# Sentiment Analysis API

A production-ready REST API for real-time sentiment analysis built with **FastAPI**, **scikit-learn**, **Prometheus** and **Grafana**, deployed via **Docker Compose** and automated with a **Jenkins** CI/CD pipeline.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Docker Network                          │
│                                                                  │
│  ┌──────────────┐    scrape     ┌──────────────┐                │
│  │  FastAPI     │◄──────────────│  Prometheus  │                │
│  │  :8000       │  /metrics     │  :9090       │                │
│  │              │               └──────┬───────┘                │
│  │  /predict    │                      │ datasource             │
│  │  /health     │               ┌──────▼───────┐                │
│  │  /metrics    │               │   Grafana    │                │
│  └──────┬───────┘               │   :3000      │                │
│         │                       └──────────────┘                │
│         │ inference                                             │
│  ┌──────▼───────┐                                               │
│  │  sklearn     │                                               │
│  │  Pipeline    │  (TF-IDF + Logistic Regression)              │
│  │  (.pkl)      │                                               │
│  └──────────────┘                                               │
│                                                                  │
│           Jenkins CI/CD                                          │
│  Checkout → Test → Build image → docker-compose deploy          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start (< 5 minutes)

### Prerequisites
- Docker ≥ 20.10 and Docker Compose ≥ 1.29
- Python 3.9+ (for local development only)

### 1. Clone and start the full stack

```bash
git clone https://github.com/Mirkotorrisi/sentiment-analysis-api.git
cd sentiment-analysis-api

# (Optional) copy and customise environment variables
cp .env.example .env

docker-compose up --build
```

### 2. Explore the API

| Service    | URL                                  |
|------------|--------------------------------------|
| Swagger UI | http://localhost:8000/docs           |
| Health     | http://localhost:8000/health         |
| Metrics    | http://localhost:8000/metrics        |
| Prometheus | http://localhost:9090                |
| Grafana    | http://localhost:3000 (admin/admin)  |

### 3. Tear down

```bash
docker-compose down
```

---

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable               | Default   | Description                              |
|------------------------|-----------|------------------------------------------|
| `IMAGE_NAME`           | `sentiment-analysis-api` | Docker image name          |
| `IMAGE_TAG`            | `latest`  | Docker image tag                         |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana admin password                   |

> **Security note:** Never commit a `.env` file with real credentials to version control.

---

## API Reference

### `POST /predict`

Predict the sentiment of a review.

**Request body**

```json
{
  "review": "string (1–1000 characters)"
}
```

**Response** `200 OK`

```json
{
  "sentiment": "positive",
  "confidence": 0.87,
  "version": "1.0.0"
}
```

**Error responses**

| Code | Reason                                        |
|------|-----------------------------------------------|
| 422  | Missing/empty review or review > 1000 chars   |
| 500  | Unexpected model inference error              |

**curl example**

```bash
# Positive review
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"review": "I love this product, it is amazing!"}' | python -m json.tool

# Negative review
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"review": "Terrible experience, would not recommend."}' | python -m json.tool

# Too-long review (triggers 422)
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d "{\"review\": \"$(python -c 'print("a"*1001)')\"}"
```

### `GET /health`

Liveness probe.

```bash
curl http://localhost:8000/health
# {"status":"healthy"}
```

### `GET /metrics`

Prometheus-format metrics endpoint (scraped automatically by Prometheus).

---

## Monitoring Guide

### Custom Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `prediction_requests_total` | Counter | `sentiment` | Total prediction calls, broken down by sentiment label |
| `prediction_latency_seconds` | Histogram | — | End-to-end request latency for `/predict` |
| `model_load_status` | Gauge | — | `1` if the model loaded successfully, `0` otherwise |

### Grafana Dashboard

The pre-provisioned dashboard (`grafana/dashboards/sentiment-dashboard.json`) includes:

- **Request rate** – predictions per minute
- **Sentiment distribution** – positive vs. negative ratio
- **Latency (p50 / p95 / p99)** – percentile breakdown
- **Model load status** – alert when model is unavailable

Open Grafana at http://localhost:3000, sign in with `admin / admin` (or your custom password), and navigate to **Dashboards → Sentiment Analysis**.

---

## Running Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing
```

Expected output: **15 tests, ≥ 93% coverage**.

### Test categories

| Category | What is tested |
|----------|---------------|
| Unit | Health check, positive/negative predictions, field validation |
| Edge cases | Empty input, whitespace-only, special characters, Unicode, 1001-char input |
| Error handling | Missing model file (corrupt pickle), model inference exception → 500 |
| Integration | `/predict` increments `prediction_requests_total` counter by 1; latency histogram sum is positive |

---

## CI/CD – Jenkins Pipeline

```
Checkout → Lint & Unit Tests → Build Docker Image → docker-compose Deploy
```

The `Jenkinsfile` at the repository root defines the full pipeline.  
Set `IMAGE_NAME` and `IMAGE_TAG` as Jenkins environment variables to control the image registry and tag.

---

## Security

- The container runs as a **non-root user** (`appuser`) — see `Dockerfile`.
- The `review` field is limited to **1,000 characters** via Pydantic validation to prevent DoS attacks from unbounded inputs.
- Docker Compose `healthcheck` on the API service restarts the container automatically if `/health` stops responding.
- No passwords or ports are hardcoded; all sensitive values come from environment variables (`.env`).

---

## Project Structure

```
sentiment-analysis-api/
├── app/
│   ├── api/
│   │   └── routes.py          # /predict endpoint + Pydantic models
│   ├── core/
│   │   ├── metrics.py         # Prometheus metrics definitions
│   │   └── model.py           # Singleton model loader
│   └── main.py                # FastAPI app, middleware, exception handler
├── grafana/
│   ├── dashboards/            # Pre-built Grafana dashboard JSON
│   └── provisioning/          # Auto-provisioned datasource & dashboard
├── models/
│   └── sentiment_model.pkl    # Trained scikit-learn pipeline
├── scripts/
│   ├── download_model.sh      # Generate/download the model artifact
│   └── verify_model.py        # Smoke-test the model file
├── tests/
│   └── test_api.py            # Full test suite (unit + edge + integration)
├── Dockerfile                 # Multi-stage, non-root image
├── docker-compose.yml         # API + Prometheus + Grafana stack
├── Jenkinsfile                # CI/CD pipeline definition
├── prometheus.yml             # Prometheus scrape config
└── requirements.txt           # Python dependencies
```
