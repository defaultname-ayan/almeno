import csv
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None

    formats = ["%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(value: str) -> Decimal:
    cleaned = (value or "").strip().replace("$", "").replace(",", "")
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def clean_transactions_csv(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        raw_rows = list(csv.DictReader(f))

    row_count_raw = len(raw_rows)

    seen = set()
    deduped_rows = []
    for row in raw_rows:
        key = tuple((k, (v or "").strip()) for k, v in row.items())
        if key not in seen:
            seen.add(key)
            deduped_rows.append(row)

    cleaned_records = []

    for row in deduped_rows:
        txn_id = (row.get("txn_id") or "").strip()
        if not txn_id:
            txn_id = f"GEN-{uuid.uuid4().hex[:12].upper()}"

        category = (row.get("category") or "").strip() or "Uncategorised"

        cleaned_records.append(
            {
                "txn_id": txn_id,
                "txn_date": parse_date(row.get("date", "")),
                "merchant": (row.get("merchant") or "").strip(),
                "amount": parse_amount(row.get("amount", "")),
                "currency": (row.get("currency") or "").strip().upper(),
                "status": (row.get("status") or "").strip().upper(),
                "category": category,
                "account_id": (row.get("account_id") or "").strip(),
                "notes": ((row.get("notes") or "").strip() or None),
                "is_anomaly": False,
                "anomaly_reason": None,
                "llm_category": None,
                "llm_raw_response": None,
                "llm_failed": False,
            }
        )

    return cleaned_records, row_count_raw, len(cleaned_records)
