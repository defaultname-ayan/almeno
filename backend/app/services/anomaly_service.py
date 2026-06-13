from decimal import Decimal
from statistics import median

from app.config import settings


def annotate_anomalies(records: list[dict]) -> list[dict]:
    account_amounts: dict[str, list[float]] = {}

    for record in records:
        account_id = record["account_id"]
        account_amounts.setdefault(account_id, []).append(float(record["amount"]))

    account_medians = {
        account_id: median(amounts) if amounts else 0
        for account_id, amounts in account_amounts.items()
    }

    for record in records:
        reasons = []
        account_median = account_medians.get(record["account_id"], 0)
        amount_value = float(record["amount"])

        if account_median > 0 and amount_value > (3 * account_median):
            reasons.append(f"Amount exceeds 3x account median ({account_median:.2f})")

        if (
            record["currency"] == "USD"
            and record["merchant"].strip().upper() in settings.domestic_usd_merchants
        ):
            reasons.append("USD used for domestic-only merchant")

        if reasons:
            record["is_anomaly"] = True
            record["anomaly_reason"] = "; ".join(reasons)

    return records
