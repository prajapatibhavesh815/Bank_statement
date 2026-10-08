"""
HDFC Bank statement parser.
Handles HDFC specific table column headers, multi-line narrations, and reference numbers.
"""
from typing import List, Any
from .generic_parser import GenericBankParser
from ...models.schemas import Transaction


class HDFCParser(GenericBankParser):
    """
    Parser specifically tailored for HDFC Bank statements.
    """

    HDFC_HEADERS = [
        "date",
        "narration",
        "chq./ref.no.",
        "value dt",
        "withdrawal amt.",
        "deposit amt.",
        "closing balance",
    ]

    @classmethod
    def parse_hdfc_table(cls, table: List[List[Any]]) -> List[Transaction]:
        return cls.parse_table_rows(table)
