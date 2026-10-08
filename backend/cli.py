"""
Command Line Interface (CLI) for Bank Statement Processing & Classification System.
Enables headless, batch, and automated command-line execution.
"""
import argparse
import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from glob import glob
from src.pipeline import StatementPipeline
from src.classifiers.ensemble import ClassificationMode
from src.exporters import ExcelExporter, CSVExporter
from src.analytics import FinancialSummary


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def process_single_file(file_path: str, output_dir: str, mode: str, force_ocr: bool, export_format: str):
    print(f"\n=======================================================")
    print(f" Processing: {os.path.basename(file_path)}")
    print(f"=======================================================")
    
    pipeline = StatementPipeline(classification_mode=mode)
    result = pipeline.process(file_path=file_path, force_ocr=force_ocr)

    meta = result.metadata
    acc = result.account_details

    print(f"[PDF Detection]   Type: {meta.file_type} (Pages: {meta.page_count})")
    print(f"[Account Details] Bank: {acc.bank_name}")
    print(f"                  Holder: {acc.account_holder}")
    print(f"                  Account #: {acc.account_number}")
    print(f"                  IFSC: {acc.ifsc_code or 'N/A'}")
    print(f"[Ledger Summary]  Transactions: {meta.total_transactions}")
    print(f"                  Total Debits:  INR {meta.total_debits:,.2f}")
    print(f"                  Total Credits: INR {meta.total_credits:,.2f}")
    print(f"                  Net Flow:      INR {meta.net_cash_flow:,.2f}")
    print(f"                  Audit Status:  {'100% Reconciled' if meta.balance_mismatches_count == 0 else f'{meta.balance_mismatches_count} Discrepancies'}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    if export_format in ["all", "excel"]:
        xlsx_path = os.path.join(output_dir, f"{base_name}_classified.xlsx")
        ExcelExporter.export(result, xlsx_path)
        print(f"[Export] Saved Excel to: {xlsx_path}")

    if export_format in ["all", "csv"]:
        csv_path = os.path.join(output_dir, f"{base_name}_classified.csv")
        CSVExporter.export_result(result, csv_path)
        print(f"[Export] Saved CSV to:   {csv_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Bank Statement Processing & Non-LLM Classification System")
    parser.add_argument("-i", "--input", required=True, help="Path to a PDF bank statement file or folder containing PDFs")
    parser.add_argument("-o", "--output-dir", default="output", help="Directory where Excel/CSV results will be stored")
    parser.add_argument("-m", "--mode", choices=["hybrid", "heuristic", "ml"], default="hybrid", help="Classification Engine Mode")
    parser.add_argument("--force-ocr", action="store_true", help="Force OCR pipeline even on digital text PDFs")
    parser.add_argument("-f", "--format", choices=["all", "excel", "csv"], default="all", help="Output export format")

    args = parser.parse_args()

    mode_map = {
        "hybrid": ClassificationMode.HYBRID,
        "heuristic": ClassificationMode.HEURISTIC,
        "ml": ClassificationMode.ML,
    }
    selected_mode = mode_map[args.mode]

    if os.path.isfile(args.input):
        pdf_files = [args.input]
    elif os.path.isdir(args.input):
        pdf_files = glob(os.path.join(args.input, "*.pdf"))
    else:
        print(f"Error: Input path '{args.input}' does not exist.")
        sys.exit(1)

    if not pdf_files:
        print(f"No PDF files found in '{args.input}'.")
        sys.exit(0)

    print(f"Found {len(pdf_files)} statement(s) to process with mode: {selected_mode}...")
    for pdf_path in pdf_files:
        process_single_file(
            file_path=pdf_path,
            output_dir=args.output_dir,
            mode=selected_mode,
            force_ocr=args.force_ocr,
            export_format=args.format,
        )

    print("\nProcessing completed successfully!")


if __name__ == "__main__":
    main()
