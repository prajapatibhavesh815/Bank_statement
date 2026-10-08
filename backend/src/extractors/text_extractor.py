"""
High-accuracy dynamic text extractor for digital bank statement PDFs.
Leverages universal adaptive table parsing and robust fallback mechanisms.
Fully dynamic — supports statements from any financial institution.
"""
import os
import pdfplumber
from typing import List, Tuple, Dict, Any
from .base_extractor import BaseExtractor
from .bank_parsers.generic_parser import GenericBankParser
from ..models.schemas import AccountDetails, Transaction


class TextExtractor:
    """
    Extracts structured transactions and account metadata from digital text PDFs
    dynamically without hardcoded bank assumptions.
    """

    @classmethod
    def extract(cls, file_path: str, detected_bank: str = "Generic Bank") -> Tuple[AccountDetails, List[Transaction], List[str]]:
        """
        Processes a text-based bank statement PDF.
        Returns (AccountDetails, List[Transaction], List[anomalies]).
        """
        all_tables: List[List[List[Any]]] = []
        full_text = ""

        with pdfplumber.open(file_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                # Extract text
                page_text = page.extract_text(layout=False) or ""
                full_text += "\n" + page_text

                def has_viable_table(t_list):
                    if not t_list:
                        return False
                    for tbl in t_list:
                        if tbl and any(len([c for c in r if c is not None and str(c).strip()]) >= 3 for r in tbl):
                            return True
                    return False

                # 1. Try explicit grid lines strategy
                tables = page.extract_tables({
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 4,
                    "join_tolerance": 4,
                })

                # 2. Try row-lines with text-based columns if grid lines yielded no multi-column table
                if not has_viable_table(tables):
                    tables = page.extract_tables({
                        "vertical_strategy": "text",
                        "horizontal_strategy": "lines",
                        "snap_tolerance": 4,
                    })

                # 3. Try pure borderless text whitespace strategy
                if not has_viable_table(tables):
                    tables = page.extract_tables({
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_tolerance": 4,
                    })

                if tables:
                    all_tables.extend(tables)

        # 1. Extract account metadata dynamically from full text
        metadata = BaseExtractor.extract_account_metadata(full_text, detected_bank=detected_bank)

        # 2. Dynamically extract transactions across all tables without bank-specific branching
        transactions: List[Transaction] = []
        if all_tables:
            transactions = GenericBankParser.parse_all_tables(all_tables)

        # 3. If table extraction yielded nothing, fallback to adaptive raw text parsing
        if len(transactions) == 0:
            transactions = GenericBankParser.parse_raw_text_lines(full_text)

        # 4. Perform dynamic ledger balance audit
        transactions, anomalies = BaseExtractor.verify_running_balances(transactions)

        # 5. Dynamically calculate opening/closing balances if not detected earlier
        if transactions:
            if metadata.opening_balance is None and any(t.balance > 0 for t in transactions):
                first_bal = transactions[0].balance
                first_dr = transactions[0].debit
                first_cr = transactions[0].credit
                metadata.opening_balance = round(first_bal + first_dr - first_cr, 2)
            if metadata.closing_balance is None and any(t.balance > 0 for t in transactions):
                metadata.closing_balance = round(transactions[-1].balance, 2)
            elif metadata.closing_balance is None and metadata.opening_balance is not None:
                tot_cr = sum(t.credit for t in transactions)
                tot_dr = sum(t.debit for t in transactions)
                metadata.closing_balance = round(metadata.opening_balance + tot_cr - tot_dr, 2)

        return metadata, transactions, anomalies
