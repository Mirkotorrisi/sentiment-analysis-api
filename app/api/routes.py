from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.core.metrics import prediction_requests_total
from app.core.model import sentiment_model

router = APIRouter()

API_VERSION = "1.0.0"


class PredictRequest(BaseModel):
    review: str = Field(..., max_length=1000)

    @field_validator("review")
    @classmethod
    def review_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("review must not be empty")
        return v


class PredictResponse(BaseModel):
    sentiment: str
    confidence: float
    version: str


@router.post("/predict", response_model=PredictResponse)
def predict_sentiment(request: PredictRequest):
    result = sentiment_model.predict(request.review)
    prediction_requests_total.labels(sentiment=result["sentiment"]).inc()
    return PredictResponse(
        sentiment=result["sentiment"],
        confidence=result["confidence"],
        version=API_VERSION,
    )
