import json
import time
import requests
from collections import Counter, defaultdict

from app.config import settings


def call_gemini_api(prompt: str) -> dict | list | None:
    api_key = settings.gemini_api_key
    if not api_key:
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }
    
    retries = 3
    for attempt in range(retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(2 ** attempt)
            
    return None


def classify_missing_categories_batch(records: list[dict]) -> list[dict]:
    uncategorised = [r for r in records if r["category"] == "Uncategorised"]
    if not uncategorised:
        return records

    batch = [{"txn_id": r["txn_id"], "merchant": r["merchant"], "notes": r["notes"]} for r in uncategorised]
    
    prompt = f"""
    You are a transaction classifier. Assign one of these categories:
    {', '.join(settings.allowed_categories)}
    
    Return a JSON array of objects with "txn_id" and "category".
    Transactions:
    {json.dumps(batch)}
    """
    
    try:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is missing.")
            
        results = call_gemini_api(prompt)
        
        if not isinstance(results, list):
            raise ValueError("LLM did not return a JSON array.")
            
        cat_map = {str(res.get("txn_id")): res.get("category") for res in results}
        
        for r in uncategorised:
            new_cat = cat_map.get(str(r["txn_id"]))
            if new_cat in settings.allowed_categories:
                r["category"] = new_cat
                r["llm_category"] = new_cat
            else:
                r["category"] = "Other"
                r["llm_category"] = "Other"
                
            r["llm_raw_response"] = json.dumps(results)
            r["llm_failed"] = False

    except Exception as e:
        error_msg = str(e)
        for r in uncategorised:
            r["llm_failed"] = True
            r["llm_raw_response"] = error_msg
            
    return records


def generate_narrative_summary(records: list[dict]) -> dict:
    total_spend_inr = 0.0
    total_spend_usd = 0.0
    merchant_counter = Counter()
    category_totals = defaultdict(float)
    anomaly_count = 0

    for record in records:
        amount = float(record["amount"])
        merchant_counter[record["merchant"]] += 1
        category_totals[record["category"]] += amount

        if record["currency"] == "INR":
            total_spend_inr += amount
        elif record["currency"] == "USD":
            total_spend_usd += amount

        if record["is_anomaly"]:
            anomaly_count += 1

    top_merchants = [
        {"merchant": merchant, "count": count}
        for merchant, count in merchant_counter.most_common(3)
    ]
    
    prompt = f"""
    You are a financial analyst. Given this data:
    Total INR: {total_spend_inr}
    Total USD: {total_spend_usd}
    Top Merchants: {json.dumps(top_merchants)}
    Anomaly Count: {anomaly_count}
    
    Produce a JSON object with these exact keys:
    "total_spend_inr": {total_spend_inr},
    "total_spend_usd": {total_spend_usd},
    "top_merchants": {json.dumps(top_merchants)},
    "anomaly_count": {anomaly_count},
    "narrative": "A 2-3 sentence spending narrative summarizing the activity.",
    "risk_level": "low", "medium", or "high" based on anomaly count.
    """
    
    default_narrative = (
        f"Processed {len(records)} transactions. "
        f"Found {anomaly_count} anomalies."
    )
    
    summary_result = {
        "total_spend_inr": round(total_spend_inr, 2),
        "total_spend_usd": round(total_spend_usd, 2),
        "top_merchants": top_merchants,
        "category_breakdown": {k: round(v, 2) for k, v in category_totals.items()},
        "anomaly_count": anomaly_count,
        "narrative": default_narrative,
        "risk_level": "low",
    }
    
    try:
        if settings.gemini_api_key:
            res = call_gemini_api(prompt)
            if isinstance(res, dict):
                summary_result["narrative"] = res.get("narrative", default_narrative)
                risk_level = str(res.get("risk_level", "low")).lower()
                summary_result["risk_level"] = risk_level if risk_level in ["low", "medium", "high"] else "low"
    except Exception:
        pass
        
    return summary_result
