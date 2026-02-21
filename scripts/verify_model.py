#!/usr/bin/env python3
"""Verify that the sentiment model can be loaded and run a dummy prediction."""
import os
import pickle
import sys

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/sentiment_model.pkl")


def verify_model():
    model_path = os.path.abspath(MODEL_PATH)
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found at {model_path}")
        sys.exit(1)

    print(f"Loading model from {model_path} ...")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    print("Model loaded successfully.")

    dummy_texts = ["I love this!", "This is terrible."]
    predictions = model.predict(dummy_texts)
    print(f"Dummy predictions: {list(zip(dummy_texts, predictions))}")
    print("Verification complete.")


if __name__ == "__main__":
    verify_model()
