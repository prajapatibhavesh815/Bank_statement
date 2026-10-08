"""
Standardized CSV Exporter (.csv).
Exports extracted and classified transaction records to clean, UTF-8 formatted CSV files.
"""
from typing import List
import pandas as pd
from ..models.schemas import Transaction, StatementProcessingResult


class CSVExporter:
    """
    Exports classified transactions into standardized CSV files.
    """

    @classmethod
    def export(cls, transactions: List[Transaction], file_path: str):
        """
        Saves transaction list to CSV file.
        """
        data = []
        for t in transactions:
            data.append({
                "Date": t.date,
                "Description": t.description,
                "Merchant": t.merchant or "",
                "Channel": t.channel or "",
                "Debit": t.debit,
                "Credit": t.credit,
                "Balance": t.balance,
                "Category": t.category,
                "SubCategory": t.sub_category or "",
                "Confidence": t.confidence,
                "ClassificationMethod": t.classification_method,
                "BalanceVerified": t.balance_verified if t.balance_verified is not None else True,
                "RefNo": t.chq_ref_no or "",
            })

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")

    @classmethod
    def export_result(cls, result: StatementProcessingResult, file_path: str):
        """Convenience method to export from StatementProcessingResult."""
        cls.export(result.transactions, file_path)
