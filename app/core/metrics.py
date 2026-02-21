from prometheus_client import Counter, Gauge, Histogram

prediction_requests_total = Counter(
    "prediction_requests_total",
    "Total number of prediction requests",
    ["sentiment"],
)

sentiment_results_total = Counter(
    "sentiment_results_total",
    "Total prediction results broken down by sentiment type",
    ["sentiment_type"],
)

prediction_latency_seconds = Histogram(
    "prediction_latency_seconds",
    "Time taken to process a prediction request in seconds",
)

model_load_status = Gauge(
    "model_load_status",
    "1 if the model loaded successfully, 0 otherwise",
)
