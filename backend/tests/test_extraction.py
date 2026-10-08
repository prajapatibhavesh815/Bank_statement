"""
Unit tests for text and OCR extraction pipeline on statements.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline import StatementPipeline

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")


class TestExtraction(unittest.TestCase):

    def setUp(self):
        self.pipeline = StatementPipeline()

    def test_extract_hdfc_statement(self):
        pdf_path = os.path.join(SAMPLE_DIR, "hdfc_sample_statement.pdf")
        res = self.pipeline.process(pdf_path)

        self.assertEqual(res.metadata.file_type, "Text-based PDF")
        self.assertEqual(res.account_details.bank_name, "HDFC Bank")
        self.assertEqual(res.account_details.account_holder, "RAJESH VERMA")
        self.assertEqual(res.account_details.account_number, "50100234918234")
        self.assertEqual(res.account_details.ifsc_code, "HDFC0000128")
        self.assertEqual(len(res.transactions), 16)
        self.assertEqual(res.metadata.total_debits, 82235.0)
        self.assertEqual(res.metadata.total_credits, 95285.0)
        self.assertEqual(res.metadata.balance_mismatches_count, 0)

    def test_extract_sbi_statement(self):
        pdf_path = os.path.join(SAMPLE_DIR, "sbi_sample_statement.pdf")
        res = self.pipeline.process(pdf_path)

        self.assertEqual(res.metadata.file_type, "Text-based PDF")
        self.assertEqual(res.account_details.bank_name, "State Bank of India (SBI)")
        self.assertEqual(res.account_details.account_holder, "BHAVESH PATEL")
        self.assertEqual(res.account_details.account_number, "38291029481")
        self.assertEqual(res.account_details.ifsc_code, "SBIN0001824")
        self.assertEqual(len(res.transactions), 12)
        self.assertEqual(res.metadata.total_debits, 43844.0)
        self.assertEqual(res.metadata.total_credits, 82294.0)
        self.assertEqual(res.metadata.balance_mismatches_count, 0)

    def test_extract_scanned_statement(self):
        pdf_path = os.path.join(SAMPLE_DIR, "scanned_sample_statement.pdf")
        res = self.pipeline.process(pdf_path)

        self.assertIn("OCR", res.metadata.file_type)
        self.assertEqual(res.account_details.account_holder, "ANANYASHARMA")
        self.assertEqual(res.account_details.account_number, "001901582910")
        self.assertEqual(res.account_details.ifsc_code, "ICIC0000007")
        self.assertEqual(len(res.transactions), 9)

    def test_dynamic_novel_bank_layout(self):
        """Verifies parsing of an arbitrary bank table with Single Amount + Dr/Cr Type column."""
        from src.extractors.bank_parsers.generic_parser import GenericBankParser
        novel_table = [
            ["Post Date", "Transaction Memo", "Amount", "Dr/Cr", "Available Balance"],
            ["05/09/2024", "Monthly Tech Consulting Fee", "75,000.00", "CR", "1,25,000.00"],
            ["08/09/2024", "Office Equipment Store", "12,450.00", "DR", "1,12,550.00"],
            ["12/09/2024", "Cloud Infrastructure Hosting", "3,200.00", "DR", "1,09,350.00"],
        ]
        txns = GenericBankParser.parse_table_rows(novel_table)
        self.assertEqual(len(txns), 3)
        self.assertEqual(txns[0].credit, 75000.0)
        self.assertEqual(txns[0].type, "CREDIT")
        self.assertEqual(txns[1].debit, 12450.0)
        self.assertEqual(txns[1].type, "DEBIT")
        self.assertEqual(txns[2].balance, 109350.0)

    def test_dynamic_multiline_narration_wrapping(self):
        """Verifies dynamic continuation row merging for multi-line wrapped descriptions."""
        from src.extractors.bank_parsers.generic_parser import GenericBankParser
        table_with_wraps = [
            ["Date", "Particulars", "Chq No", "Withdrawals", "Deposits", "Balance"],
            ["10/01/2024", "NEFT CR FROM ACME CORP", "UTR98765", "", "50,000.00", "50,000.00"],
            ["", "INVOICE #9821 FOR SERVICES", "", "", "", ""],
            ["12/01/2024", "Z EPTO ONLINE GROCERY", "REF12345", "1,450.00", "", "48,550.00"],
        ]
        txns = GenericBankParser.parse_table_rows(table_with_wraps)
        self.assertEqual(len(txns), 2)
        self.assertIn("INVOICE #9821", txns[0].description)
        self.assertEqual(txns[1].description, "ZEPTO ONLINE GROCERY")
        self.assertEqual(txns[1].debit, 1450.0)

    def test_section_based_and_2part_dates(self):
        """Verifies section-divided statements with 2-part dates and tabular check registers."""
        from src.extractors.bank_parsers.generic_parser import GenericBankParser
        from src.extractors.base_extractor import BaseExtractor

        sample_section_text = """
Statement Date: June 5, 2024
Deposits & Other Credits
Description    DateCredited    Amount
Salary Payroll Ref: 98123 05-15 $4,500.00
Total Deposits & Other Credits $4,500.00

ATM Withdrawals & Debits
Description    Date Paid    Amount
ATM Cash Withdrawal Downtown 05-18 $120.00
Total ATM Withdrawals $120.00

Checks Paid
Date Paid    CheckNumber    Amount    ReferenceNumber
05-20    1045    350.00    000918237
Total Checks Paid $350.00
"""
        txns = GenericBankParser.parse_raw_text_lines(sample_section_text)
        self.assertEqual(len(txns), 3)

        # Deposit
        self.assertEqual(txns[0].date, "2024-05-15")
        self.assertEqual(txns[0].credit, 4500.0)
        self.assertEqual(txns[0].debit, 0.0)
        self.assertEqual(txns[0].type, "CREDIT")

        # ATM Withdrawal
        self.assertEqual(txns[1].date, "2024-05-18")
        self.assertEqual(txns[1].debit, 120.0)
        self.assertEqual(txns[1].credit, 0.0)
        self.assertEqual(txns[1].type, "DEBIT")

        # Check
        self.assertEqual(txns[2].date, "2024-05-20")
        self.assertEqual(txns[2].debit, 350.0)
        self.assertEqual(txns[2].chq_ref_no, "1045")
        self.assertEqual(txns[2].type, "DEBIT")


if __name__ == "__main__":
    unittest.main()

