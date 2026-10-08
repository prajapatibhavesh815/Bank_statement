# ⚙️ Bank Statement Backend Engine & REST API

FastAPI, Machine Learning, and Optical Character Recognition (OCR) backend service for ingesting, parsing, classifying, and exporting bank statements without using Large Language Models (LLMs).

---

## 📁 Backend Directory Structure

```
backend/
├── src/
│   ├── detector.py             # PDF Type (Text vs Scanned OCR) & Bank Auto-detector
│   ├── pipeline.py             # Master Pipeline Coordinator
│   ├── extractors/
│   │   ├── base_extractor.py   # Date & amount parsing, metadata regex, ledger audit
│   │   ├── text_extractor.py   # Vector digital PDF table parser
│   │   ├── ocr_extractor.py    # Offline RapidOCR engine with vertical clustering
│   │   └── bank_parsers/       # Specialized bank layout parsers (HDFC, SBI, ICICI, Generic)
│   ├── classifiers/
│   │   ├── heuristic.py        # Rule-based heuristic pattern matcher & merchant catalog
│   │   ├── ml_classifier.py    # Traditional ML classifier (TF-IDF + Logistic Regression)
│   │   ├── ensemble.py         # Hybrid Ensemble classifier
│   │   ├── dataset.py          # Synthetic augmented banking dataset
│   │   └── saved_models/       # Pre-trained ML model binaries (.joblib)
│   ├── analytics/
│   │   └── financial_summary.py# Spending analytics, category breakdown, cash flow stats
│   ├── exporters/
│   │   ├── excel_exporter.py   # Styled multi-sheet Excel generator
│   │   └── csv_exporter.py     # Clean standardized CSV exporter
│   └── models/
│       └── schemas.py          # Data models (Pydantic / Dataclasses)
├── sample_data/                # Sample test statements and PDF generator
│   ├── generate_samples.py
│   ├── hdfc_sample_statement.pdf
│   ├── sbi_sample_statement.pdf
│   └── scanned_sample_statement.pdf
├── tests/                      # Automated unit test suite
│   ├── test_detection.py
│   ├── test_extraction.py
│   ├── test_classification.py
│   └── test_export.py
├── server.py                   # FastAPI REST API server (port 8001)
├── cli.py                      # Terminal Command-Line Interface
├── requirements.txt            # Python dependencies
└── README.md                   # Backend documentation
```

---

## 🚀 Quick Start

### 1. Install Dependencies
From the `backend` directory:
```bash
pip install -r requirements.txt
```

### 2. Start the FastAPI Server
```bash
python server.py
```
The REST API server will run at: **`http://127.0.0.1:8001`**
Interactive Swagger API documentation is available at: **`http://127.0.0.1:8001/docs`**

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health status and supported financial categories |
| `GET` | `/api/samples` | List of pre-configured sample statement files |
| `GET` | `/api/sample/:id` | Process and return analysis for a sample statement |
| `POST` | `/api/upload` | Upload and process any PDF bank statement |
| `POST` | `/api/export/excel` | Download enriched multi-sheet Excel `.xlsx` |
| `POST` | `/api/export/csv` | Download normalized `.csv` file |
| `GET` | `/api/model/info` | Get current ML model training metrics & accuracy |
| `POST` | `/api/model/retrain` | Retrain TF-IDF model on banking corpus |
| `POST` | `/api/reclassify` | Reclassify transactions with updated engine mode |

---

## 💻 CLI Usage

Process a statement directly from the command line:
```bash
python cli.py -i sample_data/hdfc_sample_statement.pdf -o output
```

Batch process a folder:
```bash
python cli.py -i sample_data/ -o output --format all
```

Select classification mode:
```bash
python cli.py -i sample_data/sbi_sample_statement.pdf --mode hybrid
```

---

## 🧪 Running Unit Tests

Run all 17 automated unit tests from the `backend` directory:
```bash
python -m unittest discover tests
```
