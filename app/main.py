import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.api.routes import router
from app.core.metrics import prediction_latency_seconds

app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

app.include_router(router)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.middleware("http")
async def track_request_latency(request: Request, call_next):
    if request.url.path == "/predict":
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        prediction_latency_seconds.observe(elapsed)
        return response
    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred during model inference."},
    )


@app.get("/health")
def health_check():
    return {"status": "healthy"}
