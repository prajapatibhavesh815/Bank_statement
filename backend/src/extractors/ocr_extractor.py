"""
OCR extractor for image-based (scanned) bank statement PDFs.
Uses pypdfium2 for high-resolution page rendering and RapidOCR
for line grouping and text extraction.
"""
import os
from typing import List, Tuple, Any, Dict
import numpy as np
import pypdfium2 as pdfium
from rapidocr_onnxruntime import RapidOCR
from .base_extractor import BaseExtractor
from .bank_parsers.generic_parser import GenericBankParser
from ..models.schemas import AccountDetails, Transaction


class OCRExtractor:
    """
    Extracts text and tables from scanned image-based bank statement PDFs using OCR.
    """

    _ocr_engine = None

    @classmethod
    def get_ocr_engine(cls) -> RapidOCR:
        if cls._ocr_engine is None:
            cls._ocr_engine = RapidOCR()
        return cls._ocr_engine

    @classmethod
    def extract(cls, file_path: str, detected_bank: str = "Generic Bank") -> Tuple[AccountDetails, List[Transaction], List[str]]:
        """
        Renders PDF pages to images, runs OCR with spatial line-grouping,
        and parses account details & transactions.
        """
        ocr = cls.get_ocr_engine()
        pdf = pdfium.PdfDocument(file_path)
        all_reconstructed_text: List[str] = []

        try:
            for page_idx, page in enumerate(pdf):
                # Render page at 2.0x scale (~144-200 DPI)
                pil_image = page.render(scale=2.0).to_pil()
                img_np = np.array(pil_image)

                # Perform OCR
                result, _ = ocr(img_np)
                if not result:
                    continue

                # result format: [[box, text, score_str], ...]
                text_blocks = []
                for item in result:
                    box, text, score_val = item[0], item[1], item[2]
                    try:
                        num_score = float(score_val)
                    except (ValueError, TypeError):
                        num_score = 1.0

                    if num_score < 0.3:
                        continue
                    # Calculate center Y and min X
                    y_center = sum(pt[1] for pt in box) / 4.0
                    x_min = min(pt[0] for pt in box)
                    box_height = max(pt[1] for pt in box) - min(pt[1] for pt in box)
                    text_blocks.append({
                        "text": text.strip(),
                        "x": x_min,
                        "y": y_center,
                        "height": max(box_height, 10),
                    })

                # Sort blocks primarily by Y coordinate
                text_blocks.sort(key=lambda b: b["y"])

                # Group into lines within vertical threshold
                lines: List[List[Dict[str, Any]]] = []
                for block in text_blocks:
                    placed = False
                    for line in lines:
                        avg_y = sum(b["y"] for b in line) / len(line)
                        avg_h = sum(b["height"] for b in line) / len(line)
                        threshold = max(avg_h * 0.6, 12.0)
                        if abs(block["y"] - avg_y) <= threshold:
                            line.append(block)
                            placed = True
                            break
                    if not placed:
                        lines.append([block])

                # Sort items in each line by X coordinate
                page_lines = []
                for line in lines:
                    line.sort(key=lambda b: b["x"])
                    line_str = "    ".join(b["text"] for b in line)
                    page_lines.append(line_str)

                all_reconstructed_text.append("\n".join(page_lines))
        finally:
            pdf.close()

        full_text = "\n\n".join(all_reconstructed_text)

        # 1. Dynamically re-detect bank from OCR reconstructed text if initially generic
        if detected_bank in ["Generic Bank", "Generic / Other Bank", "Universal Bank / Financial Institution"]:
            from ..detector import PDFDetector
            ocr_detected_bank, _ = PDFDetector.detect_bank(full_text)
            if ocr_detected_bank not in ["Generic Bank", "Generic / Other Bank", "Universal Bank / Financial Institution"]:
                detected_bank = ocr_detected_bank

        metadata = BaseExtractor.extract_account_metadata(full_text, detected_bank=detected_bank)

        # 2. Extract transactions using adaptive line parser
        transactions = GenericBankParser.parse_raw_text_lines(full_text)

        # 3. Balance verification
        transactions, anomalies = BaseExtractor.verify_running_balances(transactions)

        # Balances
        if transactions:
            if metadata.opening_balance is None and any(t.balance > 0 for t in transactions):
                first_bal = transactions[0].balance
                metadata.opening_balance = round(first_bal + transactions[0].debit - transactions[0].credit, 2)
            if metadata.closing_balance is None and any(t.balance > 0 for t in transactions):
                metadata.closing_balance = round(transactions[-1].balance, 2)
            elif metadata.closing_balance is None and metadata.opening_balance is not None:
                tot_cr = sum(t.credit for t in transactions)
                tot_dr = sum(t.debit for t in transactions)
                metadata.closing_balance = round(metadata.opening_balance + tot_cr - tot_dr, 2)

        return metadata, transactions, anomalies
