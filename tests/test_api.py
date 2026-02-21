import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_positive():
    response = client.post("/predict", json={"text": "I love this product, it is amazing!"})
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert "confidence" in data
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_negative():
    response = client.post("/predict", json={"text": "This is terrible and I hate it."})
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert "confidence" in data
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_echoes_input_text():
    text = "Neutral statement about something."
    response = client.post("/predict", json={"text": text})
    assert response.status_code == 200
    assert response.json()["text"] == text
