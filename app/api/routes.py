from fastapi import APIRouter
from pydantic import BaseModel
from app.core.model import model

router = APIRouter()


class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float


@router.post("/predict", response_model=SentimentResponse)
def predict_sentiment(request: SentimentRequest):
    probabilities = model.predict_proba([request.text])[0]
    classes = model.classes_
    top_index = int(probabilities.argmax())
    prediction = classes[top_index]
    confidence = float(probabilities[top_index])
    return SentimentResponse(
        text=request.text,
        sentiment=str(prediction),
        confidence=confidence,
    )
