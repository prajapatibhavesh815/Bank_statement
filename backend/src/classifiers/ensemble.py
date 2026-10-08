"""
Hybrid Ensemble Classifier.
Orchestrates Heuristic Rule-Based and Traditional Machine Learning models
to deliver high-accuracy non-LLM transaction classification.
"""
from typing import List, Optional
from .heuristic import HeuristicClassifier
from .ml_classifier import MLClassifier
from ..models.schemas import Transaction


class ClassificationMode:
    HYBRID = "Hybrid Ensemble"
    HEURISTIC = "Heuristic Rule-Based"
    ML = "Traditional Machine Learning (TF-IDF)"


class TransactionClassifier:
    """
    Main entry point for transaction classification.
    """

    def __init__(self, mode: str = ClassificationMode.HYBRID):
        self.mode = mode
        self.heuristic = HeuristicClassifier()
        self.ml = MLClassifier()
        self.ml.load_or_train()

    def classify_transaction(self, txn: Transaction, mode: Optional[str] = None) -> Transaction:
        """
        Classifies an individual transaction based on selected mode.
        """
        active_mode = mode or self.mode

        # 1. Always extract channel and merchant
        txn.channel = self.heuristic.detect_channel(txn.description)
        txn.merchant = self.heuristic.extract_merchant(txn.description)

        # 2. Classification based on mode
        if active_mode == ClassificationMode.HEURISTIC:
            cat, sub_cat, conf = self.heuristic.classify(txn)
            txn.category = cat
            txn.sub_category = sub_cat
            txn.confidence = conf
            txn.classification_method = "Heuristic (Rule-Based)"

        elif active_mode == ClassificationMode.ML:
            cat, conf = self.ml.predict(txn.description)
            txn.category = cat
            txn.confidence = conf
            txn.classification_method = "Machine Learning (TF-IDF + LogReg)"

        else:  # HYBRID mode
            heur_cat, sub_cat, heur_conf = self.heuristic.classify(txn)
            ml_cat, ml_conf = self.ml.predict(txn.description)

            # Decision logic:
            # If heuristic matched with high confidence (>= 0.90) e.g. known merchant or salary rule
            if heur_conf >= 0.90:
                txn.category = heur_cat
                txn.sub_category = sub_cat
                txn.confidence = heur_conf
                txn.classification_method = "Heuristic Rule-Based"
            elif ml_conf >= 0.70:
                txn.category = ml_cat
                txn.confidence = ml_conf
                txn.classification_method = "Traditional ML Model"
            else:
                # Fallback to heuristic or higher of the two
                if heur_conf >= ml_conf:
                    txn.category = heur_cat
                    txn.sub_category = sub_cat
                    txn.confidence = heur_conf
                    txn.classification_method = "Heuristic Rule-Based"
                else:
                    txn.category = ml_cat
                    txn.confidence = ml_conf
                    txn.classification_method = "Traditional ML Model"

        return txn

    def classify_all(self, transactions: List[Transaction], mode: Optional[str] = None) -> List[Transaction]:
        """Classifies a list of transactions."""
        return [self.classify_transaction(t, mode=mode) for t in transactions]
