import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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

