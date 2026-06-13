from app.services.anomaly_service import annotate_anomalies


def test_annotate_anomalies_statistical_outlier():
    records = [
        {"account_id": "acc1", "amount": 100, "currency": "INR", "merchant": "A", "is_anomaly": False, "anomaly_reason": None},
        {"account_id": "acc1", "amount": 110, "currency": "INR", "merchant": "B", "is_anomaly": False, "anomaly_reason": None},
        {"account_id": "acc1", "amount": 105, "currency": "INR", "merchant": "C", "is_anomaly": False, "anomaly_reason": None},
        # Median should be 105. 3 * 105 = 315.
        {"account_id": "acc1", "amount": 350, "currency": "INR", "merchant": "D", "is_anomaly": False, "anomaly_reason": None},
    ]

    annotated = annotate_anomalies(records)
    
    assert not annotated[0]["is_anomaly"]
    assert not annotated[1]["is_anomaly"]
    assert not annotated[2]["is_anomaly"]
    
    assert annotated[3]["is_anomaly"]
    assert "exceeds 3x account median" in annotated[3]["anomaly_reason"]


def test_annotate_anomalies_domestic_usd():
    records = [
        {"account_id": "acc1", "amount": 100, "currency": "USD", "merchant": "SWIGGY", "is_anomaly": False, "anomaly_reason": None},
        {"account_id": "acc1", "amount": 100, "currency": "INR", "merchant": "SWIGGY", "is_anomaly": False, "anomaly_reason": None},
    ]

    annotated = annotate_anomalies(records)

    assert annotated[0]["is_anomaly"]
    assert "USD used for domestic-only merchant" in annotated[0]["anomaly_reason"]
    
    assert not annotated[1]["is_anomaly"]
