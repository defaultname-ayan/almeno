import tempfile
import os
import csv
from datetime import date
from decimal import Decimal

from app.services.csv_processor import clean_transactions_csv, parse_amount, parse_date


def test_parse_date():
    assert parse_date("15-05-2024") == date(2024, 5, 15)
    assert parse_date("2024/05/15") == date(2024, 5, 15)
    assert parse_date("2024-05-15") == date(2024, 5, 15)
    assert parse_date("") is None
    assert parse_date("invalid-date") is None


def test_parse_amount():
    assert parse_amount("$100.50") == Decimal("100.50")
    assert parse_amount("1,000.00") == Decimal("1000.00")
    assert parse_amount("invalid") == Decimal("0.00")
    assert parse_amount("") == Decimal("0.00")


def test_clean_transactions_csv():
 # create csv for testing temporary
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        writer = csv.writer(tmp)
        writer.writerow(["txn_id", "date", "merchant", "amount", "currency", "status", "category", "account_id", "notes"])
        writer.writerow(["1", "15-05-2024", "Amazon", "$150.00", "usd", "success", "Shopping", "acc1", ""])
        writer.writerow(["2", "2024/05/16", "Swiggy", "500", "inr", "pending", "", "acc1", "Lunch"])
        writer.writerow(["1", "15-05-2024", "Amazon", "$150.00", "usd", "success", "Shopping", "acc1", ""]) # this is the duplcate

    try:
        records, raw_count, clean_count = clean_transactions_csv(tmp.name)
        
        assert raw_count == 3
        assert clean_count == 2
        assert len(records) == 2

        assert records[0]["txn_id"] == "1"
        assert records[0]["amount"] == Decimal("150.00")
        assert records[0]["currency"] == "USD"
        assert records[0]["status"] == "SUCCESS"

        assert records[1]["txn_id"] == "2"
        assert records[1]["category"] == "Uncategorised"
        assert records[1]["currency"] == "INR"

    finally:
        os.remove(tmp.name)
