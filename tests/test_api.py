import os
import pickle
import tempfile
import unittest.mock

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Existing unit tests
# ---------------------------------------------------------------------------

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_predict_positive():
    response = client.post("/predict", json={"review": "I love this product, it is amazing!"})
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert "confidence" in data
    assert "version" in data
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_negative():
    response = client.post("/predict", json={"review": "This is terrible and I hate it."})
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert "confidence" in data
    assert "version" in data
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_empty_review_returns_422():
    response = client.post("/predict", json={"review": ""})
    assert response.status_code == 422


def test_predict_missing_review_returns_422():
    response = client.post("/predict", json={})
    assert response.status_code == 422


def test_predict_version_field():
    response = client.post("/predict", json={"review": "Neutral statement about something."})
    assert response.status_code == 200
    assert response.json()["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------

def test_predict_special_characters():
    """Special characters should not cause a 500 error."""
    response = client.post("/predict", json={"review": "!@#$%^&*()_+-=[]{}|;':\",./<>?"})
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_whitespace_only_returns_422():
    """Whitespace-only strings should fail validation."""
    response = client.post("/predict", json={"review": "   "})
    assert response.status_code == 422


def test_predict_too_long_review_returns_422():
    """Reviews longer than 1000 characters should be rejected (DoS prevention)."""
    long_text = "a" * 1001
    response = client.post("/predict", json={"review": long_text})
    assert response.status_code == 422


def test_predict_exactly_1000_chars_is_accepted():
    """A review of exactly 1000 characters should be accepted."""
    text = "great " * 166 + "grea"  # 996 + 4 = 1000 chars
    assert len(text) == 1000
    response = client.post("/predict", json={"review": text})
    assert response.status_code == 200


def test_predict_unicode_characters():
    """Unicode characters (e.g. emoji, accented letters) should be handled gracefully."""
    response = client.post("/predict", json={"review": "Très bien! 😊 Ótimo produto."})
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data


# ---------------------------------------------------------------------------
# Model-file error tests
# ---------------------------------------------------------------------------

def test_predict_model_inference_error_returns_500():
    """If the model's predict method raises an unexpected exception, the API
    should return 500 with a structured error message (not an unhandled crash)."""
    from app.core import model as model_module
    from fastapi.testclient import TestClient as _TestClient

    original_predict = model_module.sentiment_model.predict

    def broken_predict(text):
        raise RuntimeError("Simulated model failure")

    model_module.sentiment_model.predict = broken_predict
    try:
        safe_client = _TestClient(app, raise_server_exceptions=False)
        response = safe_client.post("/predict", json={"review": "test"})
        assert response.status_code == 500
        assert "detail" in response.json()
    finally:
        model_module.sentiment_model.predict = original_predict


def test_load_corrupt_model_raises():
    """Loading a corrupted .pkl file should raise an exception."""
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        f.write(b"this is not a valid pickle file")
        corrupt_path = f.name

    try:
        with open(corrupt_path, "rb") as fh:
            with pytest.raises(Exception):
                pickle.load(fh)
    finally:
        os.unlink(corrupt_path)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

def test_predict_increments_metrics_counter():
    """Calling /predict should increment the prediction_requests_total counter."""
    from app.core.metrics import prediction_requests_total

    # Capture current count across all label combinations
    before = sum(
        sample.value
        for metric in prediction_requests_total.collect()
        for sample in metric.samples
        if sample.name == "prediction_requests_total"
    )

    client.post("/predict", json={"review": "I love this!"})

    after = sum(
        sample.value
        for metric in prediction_requests_total.collect()
        for sample in metric.samples
        if sample.name == "prediction_requests_total"
    )

    assert after == before + 1, "Counter should increase by 1 after a /predict call"


def test_predict_records_positive_latency():
    """The latency histogram should record a positive observation after /predict."""
    from app.core.metrics import prediction_latency_seconds

    before_count = sum(
        sample.value
        for metric in prediction_latency_seconds.collect()
        for sample in metric.samples
        if sample.name == "prediction_latency_seconds_count"
    )

    client.post("/predict", json={"review": "Latency test review."})

    after_count = sum(
        sample.value
        for metric in prediction_latency_seconds.collect()
        for sample in metric.samples
        if sample.name == "prediction_latency_seconds_count"
    )

    assert after_count == before_count + 1, "Latency histogram count should increase by 1"

    # Verify the recorded sum is positive (latency > 0)
    latency_sum = sum(
        sample.value
        for metric in prediction_latency_seconds.collect()
        for sample in metric.samples
        if sample.name == "prediction_latency_seconds_sum"
    )
    assert latency_sum > 0, "Recorded latency should be a positive number"

