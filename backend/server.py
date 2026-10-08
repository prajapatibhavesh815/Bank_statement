"""
FastAPI Backend Server for Bank Statement Processing & Classification System.
Powers the modern React + Vite frontend with RESTful APIs.
"""
import os
import io
import tempfile
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from src.pipeline import StatementPipeline
from src.classifiers.ensemble import ClassificationMode
from src.classifiers.heuristic import CATEGORIES
from src.exporters import ExcelExporter, CSVExporter
from src.analytics import FinancialSummary
from src.models.schemas import StatementProcessingResult, AccountDetails, Transaction, ExtractionMetadata


app = FastAPI(
    title="Bank Statement Processing API",
    description="Backend API for statement ingestion, text/OCR parsing, and non-LLM transaction classification",
    version="1.0.0",
)

# Enable CORS for Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
pipeline = StatementPipeline(classification_mode=ClassificationMode.HYBRID)


class ExportExcelRequest(BaseModel):
    account_details: Dict[str, Any]
    transactions: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    anomalies: Optional[List[str]] = []


class ExportCSVRequest(BaseModel):
    transactions: List[Dict[str, Any]]


class ReclassifyRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    mode: str = ClassificationMode.HYBRID


@app.on_event("startup")
def ensure_samples_on_startup():
    """Ensure pre-built sample statement PDFs exist on server startup."""
    try:
        from sample_data.generate_samples import (
            generate_hdfc_statement,
            generate_sbi_statement,
            generate_scanned_statement
        )
        for s_name, gen_fn in [
            ("hdfc_sample_statement.pdf", generate_hdfc_statement),
            ("sbi_sample_statement.pdf", generate_sbi_statement),
            ("scanned_sample_statement.pdf", generate_scanned_statement),
        ]:
            if not os.path.exists(os.path.join(SAMPLE_DIR, s_name)):
                gen_fn()
    except Exception:
        pass


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "Bank Statement Processing & Classification API",
        "version": "1.0.0",
        "supported_categories": CATEGORIES,
    }


@app.get("/api/samples")
def get_sample_statements():
    """Returns list of pre-generated sample statements."""
    return [
        {
            "id": "hdfc",
            "name": "HDFC Bank Statement",
            "type": "Text-based PDF",
            "description": "Multi-page digital PDF with salaries, bills, EMIs, and multi-line narrations",
            "file": "hdfc_sample_statement.pdf",
        },
        {
            "id": "sbi",
            "name": "State Bank of India (SBI)",
            "type": "Text-based PDF",
            "description": "Digital PDF with Txn Date, Value Date, Ref numbers, and UPI transfers",
            "file": "sbi_sample_statement.pdf",
        },
        {
            "id": "scanned",
            "name": "ICICI Bank (Scanned Image PDF)",
            "type": "Image-based PDF (OCR)",
            "description": "Scanned document photo parsed via offline RapidOCR deep learning engine",
            "file": "scanned_sample_statement.pdf",
        },
    ]


@app.post("/api/upload")
async def process_uploaded_pdf(
    file: UploadFile = File(...),
    mode: str = Form(ClassificationMode.HYBRID),
    force_ocr: bool = Form(False),
):
    """
    Accepts an uploaded PDF bank statement and processes it end-to-end.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        current_pipeline = StatementPipeline(classification_mode=mode)
        result = current_pipeline.process(file_path=tmp_path, force_ocr=force_ocr)
        result.metadata.file_name = file.filename

        analytics = FinancialSummary.analyze(result.transactions, result.account_details)

        return {
            "success": True,
            "account_details": result.account_details.to_dict(),
            "transactions": [t.to_dict() for t in result.transactions],
            "metadata": result.metadata.to_dict(),
            "analytics": analytics,
            "anomalies": result.anomalies,
            "categories": CATEGORIES,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@app.post("/api/process-sample/{sample_id}")
def process_sample(
    sample_id: str,
    mode: str = Query(ClassificationMode.HYBRID),
    force_ocr: bool = Query(False),
):
    """
    Processes one of the pre-built sample statements.
    """
    sample_map = {
        "hdfc": "hdfc_sample_statement.pdf",
        "sbi": "sbi_sample_statement.pdf",
        "scanned": "scanned_sample_statement.pdf",
    }

    if sample_id not in sample_map:
        raise HTTPException(status_code=404, detail="Sample ID not found.")

    file_path = os.path.join(SAMPLE_DIR, sample_map[sample_id])
    if not os.path.exists(file_path):
        try:
            from sample_data.generate_samples import (
                generate_hdfc_statement,
                generate_sbi_statement,
                generate_scanned_statement
            )
            if sample_id == "hdfc":
                generate_hdfc_statement()
            elif sample_id == "sbi":
                generate_sbi_statement()
            elif sample_id == "scanned":
                generate_scanned_statement()
        except Exception:
            pass

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample file missing on server.")

    current_pipeline = StatementPipeline(classification_mode=mode)
    result = current_pipeline.process(file_path=file_path, force_ocr=force_ocr)
    result.metadata.file_name = sample_map[sample_id]

    analytics = FinancialSummary.analyze(result.transactions, result.account_details)

    return {
        "success": True,
        "account_details": result.account_details.to_dict(),
        "transactions": [t.to_dict() for t in result.transactions],
        "metadata": result.metadata.to_dict(),
        "analytics": analytics,
        "anomalies": result.anomalies,
        "categories": CATEGORIES,
    }


@app.post("/api/export/excel")
def export_excel(payload: ExportExcelRequest):
    """
    Generates and streams styled multi-sheet Excel file (.xlsx).
    """
    acc = AccountDetails(**payload.account_details)
    meta = ExtractionMetadata(**payload.metadata)
    txns = [Transaction(**t) for t in payload.transactions]

    result = StatementProcessingResult(
        account_details=acc,
        transactions=txns,
        metadata=meta,
        anomalies=payload.anomalies or [],
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp_path = tmp.name

    try:
        ExcelExporter.export(result, tmp_path)
        with open(tmp_path, "rb") as f:
            data = f.read()

        file_name = f"{os.path.splitext(meta.file_name or 'statement')[0]}_classified.xlsx"
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@app.post("/api/export/csv")
def export_csv(payload: ExportCSVRequest):
    """
    Generates and streams standardized CSV file (.csv).
    """
    txns = [Transaction(**t) for t in payload.transactions]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp_path = tmp.name

    try:
        CSVExporter.export(txns, tmp_path)
        with open(tmp_path, "rb") as f:
            data = f.read()

        file_name = "transactions_classified.csv"
        return StreamingResponse(
            io.BytesIO(data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@app.get("/api/model/info")
def get_model_info():
    """Returns Machine Learning model information and diagnostics."""
    ml_classifier = pipeline.classifier.ml
    return {
        "model_type": "TF-IDF N-grams (1, 2) + Logistic Regression (Scikit-Learn)",
        "accuracy": round(ml_classifier.accuracy, 4),
        "classes_count": len(ml_classifier.classes_),
        "classes": ml_classifier.classes_,
        "categories": CATEGORIES,
    }


@app.post("/api/model/retrain")
def retrain_model():
    """Triggers ML model re-training on augmented banking dataset."""
    ml_classifier = pipeline.classifier.ml
    stats = ml_classifier.train()
    return {
        "success": True,
        "message": "Model retrained successfully",
        "new_accuracy": stats["accuracy"],
        "total_samples": stats["total_samples"],
        "train_samples": stats["train_samples"],
        "test_samples": stats["test_samples"],
    }


@app.post("/api/reclassify")
def reclassify_transactions(payload: ReclassifyRequest):
    """Reclassifies an existing list of transactions with a specified engine mode."""
    txns = [Transaction(**t) for t in payload.transactions]
    classified = pipeline.classifier.classify_all(txns, mode=payload.mode)
    return {
        "success": True,
        "transactions": [t.to_dict() for t in classified],
    }


# Mount frontend production build if present
from fastapi.staticfiles import StaticFiles

dist_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist"))
if not os.path.exists(dist_dir):
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting Bank Statement Processing API server on http://127.0.0.1:{port}...")
    uvicorn.run("server:app", host="127.0.0.1", port=port, reload=True)
