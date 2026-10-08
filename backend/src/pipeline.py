"""
End-to-End Statement Processing & Classification Pipeline.
Orchestrates PDF type detection, bank identification, text/OCR extraction,
non-LLM transaction classification, and balance reconciliation.
"""
import time
import os
from typing import Optional
from .detector import PDFDetector
from .extractors.text_extractor import TextExtractor
from .extractors.ocr_extractor import OCRExtractor
from .classifiers.ensemble import TransactionClassifier, ClassificationMode
from .models.schemas import (
    StatementProcessingResult,
    ExtractionMetadata,
    AccountDetails,
    Transaction,
)


class StatementPipeline:
    """
    Main processing pipeline for bank statements.
    """

    def __init__(self, classification_mode: str = ClassificationMode.HYBRID):
        self.classification_mode = classification_mode
        self.classifier = TransactionClassifier(mode=classification_mode)

    def process(
        self,
        file_path: str,
        force_ocr: bool = False,
        classification_mode: Optional[str] = None
    ) -> StatementProcessingResult:
        """
        Executes the end-to-end processing pipeline on a PDF bank statement.
        """
        start_time = time.time()
        file_name = os.path.basename(file_path)

        # 1. Detect PDF Type and Bank
        detection_info = PDFDetector.detect_pdf_type(file_path)

        if detection_info.get("is_encrypted"):
            metadata = ExtractionMetadata(
                file_name=file_name,
                file_type="Password-Protected PDF",
                page_count=detection_info.get("page_count", 0),
                total_transactions=0,
                total_debits=0.0,
                total_credits=0.0,
                net_cash_flow=0.0,
                balance_mismatches_count=1,
                processing_time_sec=round(time.time() - start_time, 2),
            )
            return StatementProcessingResult(
                account_details=AccountDetails(bank_name="Encrypted / Password Protected"),
                transactions=[],
                metadata=metadata,
                anomalies=["This PDF bank statement is password-protected. Please unlock or decrypt the PDF before processing."],
            )

        is_text_based = detection_info["is_text_based"] and not force_ocr
        pdf_type = "Image-based PDF (OCR)" if (force_ocr or not is_text_based) else "Text-based PDF"

        detected_bank, _ = PDFDetector.detect_bank(detection_info["sample_text"])

        # 2. Extract Data
        account_details = AccountDetails(bank_name=detected_bank)
        transactions = []
        anomalies = []

        if is_text_based and not force_ocr:
            try:
                account_details, transactions, anomalies = TextExtractor.extract(
                    file_path, detected_bank=detected_bank
                )
            except Exception as e:
                # Fallback to OCR if text extraction throws error
                anomalies.append(f"Text extraction failed ({str(e)}), fallen back to OCR.")
                account_details, transactions, anomalies_ocr = OCRExtractor.extract(
                    file_path, detected_bank=detected_bank
                )
                anomalies.extend(anomalies_ocr)
                pdf_type = "Image-based PDF (OCR) [Fallback]"

            # If text extraction found 0 transactions in text PDF, attempt OCR fallback
            if len(transactions) == 0:
                try:
                    ocr_acc, ocr_txns, ocr_anom = OCRExtractor.extract(
                        file_path, detected_bank=detected_bank
                    )
                    if len(ocr_txns) > 0:
                        account_details = ocr_acc
                        transactions = ocr_txns
                        anomalies.extend(ocr_anom)
                        pdf_type = "Image-based PDF (OCR) [Adaptive]"
                except Exception:
                    pass
        else:
            # Scanned / Image-based extraction via OCR
            account_details, transactions, anomalies = OCRExtractor.extract(
                file_path, detected_bank=detected_bank
            )

        # 3. Classify Transactions (Non-LLM)
        mode_to_use = classification_mode or self.classification_mode
        classified_transactions = self.classifier.classify_all(transactions, mode=mode_to_use)

        # 4. Compute Totals & Build Metadata
        total_debits = sum(t.debit for t in classified_transactions)
        total_credits = sum(t.credit for t in classified_transactions)
        net_cash_flow = total_credits - total_debits
        mismatches_count = len(anomalies)

        processing_time = round(time.time() - start_time, 2)

        metadata = ExtractionMetadata(
            file_name=file_name,
            file_type=pdf_type,
            page_count=detection_info["page_count"],
            total_transactions=len(classified_transactions),
            total_debits=round(total_debits, 2),
            total_credits=round(total_credits, 2),
            net_cash_flow=round(net_cash_flow, 2),
            balance_mismatches_count=mismatches_count,
            processing_time_sec=processing_time,
        )

        return StatementProcessingResult(
            account_details=account_details,
            transactions=classified_transactions,
            metadata=metadata,
            anomalies=anomalies,
        )
