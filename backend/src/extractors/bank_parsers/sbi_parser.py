"""
State Bank of India (SBI) statement parser.
Handles SBI specific table formats, Txn Date / Value Date columns, and descriptions.
"""
from typing import List, Any
from .generic_parser import GenericBankParser
from ...models.schemas import Transaction


class SBIParser(GenericBankParser):
    """
    Parser specifically tailored for SBI bank statements.
    """

    SBI_HEADERS = [
        "txn date",
        "value date",
        "description",
        "ref no./cheque no.",
        "debit",
        "credit",
        "balance",
    ]

    @classmethod
    def parse_sbi_table(cls, table: List[List[Any]]) -> List[Transaction]:
        return cls.parse_table_rows(table)
