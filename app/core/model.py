import os
import pickle

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/sentiment_model.pkl")


def load_model():
    model_path = os.path.abspath(MODEL_PATH)
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found at {model_path}. "
            "Run scripts/download_model.sh to generate it."
        )
    with open(model_path, "rb") as f:
        return pickle.load(f)


model = load_model()
