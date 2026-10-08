"""
ICICI Bank statement parser.
Handles ICICI layout with Date, Mode, Particulars, Withdrawals, Deposits, and Balance.
"""
from typing import List, Any
from .generic_parser import GenericBankParser
from ...models.schemas import Transaction


class ICICIParser(GenericBankParser):
    """
    Parser specifically tailored for ICICI bank statements.
    """

    ICICI_HEADERS = [
        "transaction date",
        "particulars",
        "cheque no",
        "withdrawals",
        "deposits",
        "balance",
    ]

    @classmethod
    def parse_icici_table(cls, table: List[List[Any]]) -> List[Transaction]:
        return cls.parse_table_rows(table)
