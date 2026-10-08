"""
Traditional Machine Learning Transaction Classifier.
Uses TF-IDF feature extraction + Logistic Regression / Naive Bayes
to classify bank statement transaction narrations without LLMs.
"""
import os
import re
from typing import Tuple, Dict, Any, Optional
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from .dataset import generate_augmented_training_data


MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
MODEL_PATH = os.path.join(MODEL_DIR, "bank_transaction_ml_model.joblib")


class MLClassifier:
    """
    Supervised Machine Learning classifier for bank transactions.
    """

    def __init__(self, model_type: str = "logistic_regression"):
        self.model_type = model_type
        self.pipeline: Optional[Pipeline] = None
        self.accuracy: float = 0.0
        self.classes_: list = []

    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        Cleans transaction narration to extract salient semantic tokens
        while removing arbitrary reference numbers and pure noise.
        """
        if not text:
            return ""
        # Lowercase
        t = str(text).lower()
        # Remove long digit reference numbers (e.g. 12-digit UTRs or account numbers)
        t = re.sub(r"\b\d{6,}\b", " ", t)
        # Replace common separators with spaces
        t = re.sub(r"[/\\:\-_#@\.]", " ", t)
        # Remove standalone single digits
        t = re.sub(r"\b\d+\b", " ", t)
        # Collapse whitespace
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def build_pipeline(self) -> Pipeline:
        """Constructs the Scikit-Learn TF-IDF + Classifier pipeline."""
        vectorizer = TfidfVectorizer(
            preprocessor=self.preprocess_text,
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
        )

        if self.model_type == "naive_bayes":
            classifier = MultinomialNB(alpha=0.1)
        else:
            classifier = LogisticRegression(
                C=2.5,
                max_iter=1000,
                class_weight="balanced",
                random_state=42,
            )

        return Pipeline([
            ("vectorizer", vectorizer),
            ("classifier", classifier),
        ])

    def train(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Trains the traditional ML model on transaction narrations.
        """
        if df is None:
            df = generate_augmented_training_data(multiplier=15)

        X = df["description"]
        y = df["category"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.pipeline = self.build_pipeline()
        self.pipeline.fit(X_train, y_train)

        y_pred = self.pipeline.predict(X_test)
        self.accuracy = float(accuracy_score(y_test, y_pred))
        self.classes_ = list(self.pipeline.classes_)

        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        # Save trained model to disk
        self.save_model()

        return {
            "accuracy": round(self.accuracy, 4),
            "total_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "report": report,
        }

    def predict(self, description: str) -> Tuple[str, float]:
        """
        Predicts category and returns (category, confidence_score).
        """
        if self.pipeline is None:
            self.load_or_train()

        # Get probability distribution
        probas = self.pipeline.predict_proba([description])[0]
        max_idx = probas.argmax()
        category = self.pipeline.classes_[max_idx]
        confidence = float(probas[max_idx])

        return category, round(confidence, 3)

    def save_model(self, file_path: str = MODEL_PATH):
        """Persists trained model using joblib."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        joblib.dump({
            "pipeline": self.pipeline,
            "accuracy": self.accuracy,
            "classes": self.classes_,
        }, file_path)

    def load_model(self, file_path: str = MODEL_PATH) -> bool:
        """Loads a saved model from disk."""
        if os.path.exists(file_path):
            data = joblib.load(file_path)
            self.pipeline = data["pipeline"]
            self.accuracy = data.get("accuracy", 0.0)
            self.classes_ = data.get("classes", [])
            return True
        return False

    def load_or_train(self):
        """Loads existing model or initiates instant training."""
        if not self.load_model():
            self.train()
