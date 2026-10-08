"""
Tests for PDF type detection and bank identification.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.detector import PDFDetector

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")


class TestPDFDetection(unittest.TestCase):

    def test_text_pdf_detection_hdfc(self):
        pdf_path = os.path.join(SAMPLE_DIR, "hdfc_sample_statement.pdf")
        info = PDFDetector.detect_pdf_type(pdf_path)
        self.assertTrue(info["is_text_based"])
        self.assertEqual(info["pdf_type"], "Text-based PDF")

    def test_text_pdf_detection_sbi(self):
        pdf_path = os.path.join(SAMPLE_DIR, "sbi_sample_statement.pdf")
        info = PDFDetector.detect_pdf_type(pdf_path)
        self.assertTrue(info["is_text_based"])
        self.assertEqual(info["pdf_type"], "Text-based PDF")

    def test_scanned_pdf_detection(self):
        pdf_path = os.path.join(SAMPLE_DIR, "scanned_sample_statement.pdf")
        info = PDFDetector.detect_pdf_type(pdf_path)
        self.assertFalse(info["is_text_based"])
        self.assertEqual(info["pdf_type"], "Image-based PDF (OCR)")

    def test_bank_detection_hdfc(self):
        text = "Welcome to HDFC BANK LIMITED Koramangala branch Bangalore"
        bank, conf = PDFDetector.detect_bank(text)
        self.assertEqual(bank, "HDFC Bank")
        self.assertGreaterEqual(conf, 0.9)

    def test_bank_detection_sbi(self):
        text = "STATE BANK OF INDIA Satellite Road Ahmedabad IFSC: SBIN0001824"
        bank, conf = PDFDetector.detect_bank(text)
        self.assertEqual(bank, "State Bank of India (SBI)")
    def test_dynamic_bank_detection_ifsc_prefix(self):
        text = "Statement of Account IFSC: FDRL0001234 Customer Name: Suresh Nair"
        bank, conf = PDFDetector.detect_bank(text)
        self.assertEqual(bank, "Federal Bank")
        self.assertGreaterEqual(conf, 0.9)

    def test_dynamic_bank_detection_entity_name(self):
        text = "SARASWAT CO-OPERATIVE BANK LIMITED\nVile Parle Branch, Mumbai - 400057"
        bank, conf = PDFDetector.detect_bank(text)
        self.assertIn("Saraswat", bank)
        self.assertGreaterEqual(conf, 0.85)

    def test_dynamic_bank_detection_foreign_bank(self):
        text = "BARCLAYS BANK PLC\n1 Churchill Place London E14 5HP"
        bank, conf = PDFDetector.detect_bank(text)
        self.assertEqual(bank, "Barclays Bank")
        self.assertGreaterEqual(conf, 0.85)


if __name__ == "__main__":
    unittest.main()
