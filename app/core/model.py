import os
import pickle

from app.core.metrics import model_load_status

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/sentiment_model.pkl")


class SentimentModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pipeline = None
            cls._instance._load()
        return cls._instance

    def _load(self):
        model_path = os.path.abspath(MODEL_PATH)
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"Model file not found at {model_path}. "
                    "Run scripts/download_model.sh to generate it."
                )
            with open(model_path, "rb") as f:
                self._pipeline = pickle.load(f)
            model_load_status.set(1)
        except Exception:
            model_load_status.set(0)
            raise

    def predict(self, text: str) -> dict:
        if not isinstance(text, str):
            raise ValueError("Input must be a string.")
        probabilities = self._pipeline.predict_proba([text])[0]
        classes = self._pipeline.classes_
        top_index = int(probabilities.argmax())
        sentiment = str(classes[top_index])
        confidence = float(probabilities[top_index])
        return {"sentiment": sentiment, "confidence": confidence}

sentiment_model = SentimentModel()
