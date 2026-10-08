"""
Data models and schemas for Bank Statement Processing and Classification.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class AccountDetails:
    bank_name: str = "Unknown Bank"
    account_holder: str = "Not Found"
    account_number: str = "Not Found"
    ifsc_code: Optional[str] = None
    branch: Optional[str] = None
    statement_period_start: Optional[str] = None
    statement_period_end: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    currency: str = "INR"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Transaction:
    date: str
    raw_date: str
    description: str
    debit: float = 0.0
    credit: float = 0.0
    balance: float = 0.0
    type: str = "DEBIT"  # "DEBIT" or "CREDIT"
    chq_ref_no: Optional[str] = None
    channel: Optional[str] = None  # UPI, NEFT, IMPS, RTGS, POS, ATM, ACH, CHEQUE, etc.
    merchant: Optional[str] = None
    category: str = "Miscellaneous / Others"
    sub_category: Optional[str] = None
    confidence: float = 1.0
    classification_method: str = "Heuristic Rule-Based"
    balance_verified: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractionMetadata:
    file_name: str = ""
    file_type: str = "Text-based PDF"  # "Text-based PDF" or "Image-based PDF (OCR)"
    page_count: int = 1
    total_transactions: int = 0
    total_debits: float = 0.0
    total_credits: float = 0.0
    net_cash_flow: float = 0.0
    balance_mismatches_count: int = 0
    processing_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StatementProcessingResult:
    account_details: AccountDetails = field(default_factory=AccountDetails)
    transactions: List[Transaction] = field(default_factory=list)
    metadata: ExtractionMetadata = field(default_factory=ExtractionMetadata)
    anomalies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_details": self.account_details.to_dict(),
            "transactions": [t.to_dict() for t in self.transactions],
            "metadata": self.metadata.to_dict(),
            "anomalies": self.anomalies,
        }
