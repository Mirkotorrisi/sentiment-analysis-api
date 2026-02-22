#!/usr/bin/env bash
# Download or generate the sentiment model.
# Replace the URL below with the actual model source if available.

set -e

MODELS_DIR="$(dirname "$0")/../models"
MODEL_FILE="$MODELS_DIR/sentiment_analysis_model.pkl"

mkdir -p "$MODELS_DIR"

if [ -f "$MODEL_FILE" ]; then
  echo "Model already exists at $MODEL_FILE"
  exit 0
fi

echo "Generating a sample sentiment model..."
python3 - <<'EOF'
import pickle, os
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

texts = [
    "I love this", "fantastic product", "great experience", "very happy",
    "excellent work", "wonderful", "best ever", "highly recommend",
    "I hate this", "terrible product", "awful experience", "very unhappy",
    "worst ever", "do not recommend", "horrible", "disappointed",
]
labels = ["positive"] * 8 + ["negative"] * 8

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", LogisticRegression(max_iter=1000)),
])
pipeline.fit(texts, labels)

model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../models/sentiment_analysis_model.pkl")
with open(model_path, "wb") as f:
    pickle.dump(pipeline, f)
print(f"Model saved to {model_path}")
EOF
