"""
Unit tests for Non-LLM Transaction Classification Engines:
1. Heuristic Rule-Based Classifier
2. Traditional Machine Learning Classifier (TF-IDF + Logistic Regression)
3. Hybrid Ensemble Classifier
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.schemas import Transaction
from src.classifiers.heuristic import HeuristicClassifier
from src.classifiers.ml_classifier import MLClassifier
from src.classifiers.ensemble import TransactionClassifier, ClassificationMode


class TestClassification(unittest.TestCase):

    def setUp(self):
        self.heuristic = HeuristicClassifier()
        self.ml = MLClassifier()
        self.ml.load_or_train()
        self.ensemble = TransactionClassifier(mode=ClassificationMode.HYBRID)

    def test_heuristic_salary(self):
        txn = Transaction(
            date="2024-08-01",
            raw_date="01/08/2024",
            description="ACH CR INFOSYS LIMITED MONTHLY SALARY PAYROLL",
            credit=95000.0,
            debit=0.0,
            balance=125000.0,
            type="CREDIT",
        )
        cat, sub, conf = self.heuristic.classify(txn)
        self.assertEqual(cat, "Salary & Income")
        self.assertGreaterEqual(conf, 0.90)

    def test_heuristic_food(self):
        txn = Transaction(
            date="2024-08-03",
            raw_date="03/08/2024",
            description="UPI/421092837192/ZOMATO LIMITED/zomato@icici/DR",
            credit=0.0,
            debit=650.0,
            balance=91850.0,
            type="DEBIT",
        )
        cat, sub, conf = self.heuristic.classify(txn)
        self.assertEqual(cat, "Food & Dining")

    def test_heuristic_groceries(self):
        txn = Transaction(
            date="2024-08-05",
            raw_date="05/08/2024",
            description="UPI/421598201928/BLINKIT COMMERCE/blinkit@icici/DR",
            credit=0.0,
            debit=1240.0,
            balance=90610.0,
            type="DEBIT",
        )
        cat, sub, conf = self.heuristic.classify(txn)
        self.assertEqual(cat, "Groceries & Supermarkets")

    def test_heuristic_utilities(self):
        txn = Transaction(
            date="2024-08-08",
            raw_date="08/08/2024",
            description="BILLDESK BESCOM ELECTRICITY BILL ONLINE PAYMENT",
            credit=0.0,
            debit=2450.0,
            balance=88160.0,
            type="DEBIT",
        )
        cat, sub, conf = self.heuristic.classify(txn)
        self.assertEqual(cat, "Utilities & Bills")

    def test_ml_prediction(self):
        cat, conf = self.ml.predict("SWIGGY FOOD ORDER DELIVERY")
        self.assertEqual(cat, "Food & Dining")
        self.assertGreaterEqual(conf, 0.40)

    def test_ml_salary_prediction(self):
        cat, conf = self.ml.predict("MONTHLY PAYROLL SALARY CREDIT TECH MAHINDRA")
        self.assertEqual(cat, "Salary & Income")

    def test_hybrid_ensemble(self):
        txn = Transaction(
            date="2024-08-10",
            raw_date="10/08/2024",
            description="POS 489201 SHELL PETROL PUMP KORAMANGALA BLR",
            credit=0.0,
            debit=3500.0,
            balance=84660.0,
            type="DEBIT",
        )
        res_txn = self.ensemble.classify_transaction(txn)
        self.assertEqual(res_txn.category, "Travel & Fuel")
        self.assertIsNotNone(res_txn.channel)


if __name__ == "__main__":
    unittest.main()
