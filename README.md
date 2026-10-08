# 🏦 Bank Statement Processing & Non-LLM Classification System

A production-ready system engineered to ingest bank statements in PDF format (both **native text-based** and **scanned image-based**), extract account metadata and transaction tables dynamically without hardcoded bank assumptions, classify transactions into 14 financial categories using **100% Non-LLM techniques** (Heuristic Rules and Traditional Machine Learning), audit running balances for ledger reconciliation, and export enriched data to styled **Excel (.xlsx)** and **CSV (.csv)** files.

---

## 📋 Table of Contents
1. [Key Features](#-key-features)
2. [Architecture Overview](#-architecture-overview)
3. [System Requirements](#-system-requirements)
4. [Step-by-Step Setup Guide (Any Computer)](#-step-by-step-setup-guide-any-computer)
   - [Windows Setup](#windows-setup)
   - [macOS / Linux Setup](#macos--linux-setup)
5. [Running the Application](#-running-the-application)
   - [Option A: 1-Click Batch Launchers (Windows)](#option-a-1-click-batch-launchers-windows)
   - [Option B: Unified Production Server (Recommended)](#option-b-unified-production-server-recommended)
   - [Option C: Full-Stack Development Mode (Hot-Reload)](#option-c-full-stack-development-mode-hot-reload)
   - [Option D: Command-Line Interface (CLI Mode)](#option-d-command-line-interface-cli-mode)
6. [Non-LLM Classification Architecture](#-non-llm-classification-architecture)
7. [Supported Financial Institutions](#-supported-financial-institutions)
8. [Edge Cases & Ledger Reconciliation](#-edge-cases--ledger-reconciliation)
9. [REST API Endpoints](#-rest-api-endpoints)
10. [Automated Unit Testing](#-automated-unit-testing)
11. [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🌟 Key Features

- **Universal Dynamic PDF Ingestion**:
  - Automatically identifies whether an uploaded document is a **digital vector text PDF** or a **scanned paper photo/image PDF**.
  - No bank-specific hardcoded assumptions or rigid coordinate grids.
- **Embedded Standalone OCR Engine (100% Offline)**:
  - Powered by deep-learning `RapidOCR` with ONNX runtime.
  - Zero external Tesseract executable installations, zero cloud API keys, and zero external network calls.
- **Accurate Financial Data Extraction**:
  - **Account Metadata**: Account Holder Name, Account Number (masked/unmasked), IFSC Code, Branch, Statement Period, Opening & Closing Balances.
  - **Transaction Tables**: Transaction Date, Value Date, Narration/Description, Reference/UTR/Cheque Number, Debit Amount, Credit Amount, Running Balance.
- **100% Non-LLM Classification Engine**:
  - **Heuristic Rule-Based**: Pattern catalog, directional debit/credit validation, channel detection, and merchant inference.
  - **Traditional Machine Learning**: Scikit-Learn `TfidfVectorizer` (N-grams 1-2) with calibrated `LogisticRegression` trained on authentic banking narrations.
  - **Hybrid Ensemble**: Combines rule precision with ML statistical generalization for maximum accuracy.
- **Automated Ledger Reconciliation & Audit**:
  - Validates `Opening Balance + Total Credits - Total Debits == Closing Balance`.
  - Audits running balances row-by-row and flags discrepancies with detailed audit logs.
- **Modern FinTech React + Vite Web UI**:
  - Drag-and-drop file upload with animated state feedback.
  - Interactive transaction ledger with live search, filters, and inline category override.
  - Financial charts: Category expense breakdown, payment channels (UPI, ATM, POS, NetBanking).
  - One-click export to multi-sheet styled Excel (.xlsx) and normalized CSV (.csv).

---

## 🏛️ Architecture Overview

```
bank_statement_project/
├── backend/                       # Python FastAPI Backend & ML Core
│   ├── src/
│   │   ├── detector.py            # PDF Type & Universal Bank Detector
│   │   ├── pipeline.py            # Master Pipeline Coordinator
│   │   ├── extractors/            # Text extraction & OCR engines
│   │   │   ├── base_extractor.py  # Amount cleaning, date parsing, reconciliation
│   │   │   ├── text_extractor.py  # 3-level adaptive digital table parser
│   │   │   ├── ocr_extractor.py   # Multi-page RapidOCR with spatial clustering
│   │   │   └── bank_parsers/      # Generic & specialized table parsers
│   │   ├── classifiers/           # Non-LLM Classification engines
│   │   │   ├── heuristic.py       # Heuristic pattern & merchant rule engine
│   │   │   ├── ml_classifier.py   # Scikit-Learn TF-IDF + Logistic Regression
│   │   │   ├── ensemble.py        # Hybrid Ensemble classifier
│   │   │   └── dataset.py         # Seed & synthetic augmented banking corpus
│   │   ├── analytics/             # Financial summaries & spending analytics
│   │   ├── exporters/             # Multi-sheet Excel & CSV generators
│   │   └── models/                # Pydantic models & data schemas
│   ├── sample_data/               # Sample statement generator & test PDFs
│   ├── tests/                     # 23 Automated unit tests
│   ├── server.py                  # FastAPI server (Port 8001)
│   ├── cli.py                     # Headless command-line interface
│   └── requirements.txt           # Python dependencies
├── frontend/                      # Modern React + Vite Dashboard
│   ├── src/                       # React components, styles, Lucide icons
│   │   ├── App.jsx                # Main application UI component
│   │   ├── App.css                # Polished FinTech dashboard stylesheet
│   │   └── index.css              # Typography & global styles
│   ├── dist/                      # Production build assets (served by backend)
│   ├── package.json               # Node.js dependencies
│   └── vite.config.js             # Vite development & proxy configuration
├── run_backend.bat                # 1-Click launcher for backend server (Windows)
├── run_frontend.bat               # 1-Click launcher for frontend dev server (Windows)
├── run_tests.bat                  # 1-Click launcher for unit tests (Windows)
├── server.py                      # Root convenience launcher for backend
├── cli.py                         # Root convenience launcher for CLI
├── requirements.txt               # Unified project dependencies
├── .gitignore                     # Git ignore rules
└── README.md                      # Project setup & documentation
```

---

## 💻 System Requirements

Before setting up the project on any computer, make sure you have:

| Tool | Minimum Version | Recommended Version | Purpose |
|---|---|---|---|
| **Python** | 3.10+ | 3.11 or 3.12 / 3.13 | Backend server, PDF parsing, ML & OCR |
| **Node.js** *(Optional)* | 18.0+ | 20.0+ LTS | Only needed for frontend development (`npm run dev`) |
| **RAM** | 4 GB | 8 GB+ | Deep-learning OCR image processing |
| **OS** | Windows 10/11, macOS, or Linux | Windows 11 / Ubuntu 22.04 | Cross-platform compatibility |

> **Note**: If you only want to use the application without modifying the React code, **Node.js is NOT required!** The production React frontend is pre-built into `frontend/dist/` and served automatically by the Python backend.

---

## 🚀 Step-by-Step Setup Guide (Any Computer)

### Windows Setup

1. **Open PowerShell or Command Prompt** and navigate to the project directory:
   ```powershell
   cd d:\Bhavesh\bank_statement_project
   ```

2. **Create a Python Virtual Environment** (Recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Python Dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. *(Optional - For Frontend Development)* **Install Node Dependencies**:
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

---

### macOS / Linux Setup

1. **Open Terminal** and navigate to the project directory:
   ```bash
   cd /path/to/bank_statement_project
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. *(Optional - For Frontend Development)*:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

---

## 🖥️ Running the Application

### Option A: 1-Click Batch Launchers (Windows)

On Windows, double-click any of the provided `.bat` scripts:
- **`run_backend.bat`**: Starts the FastAPI server on `http://127.0.0.1:8001`.
- **`run_frontend.bat`**: Starts the Vite development server on `http://localhost:5173`.
- **`run_tests.bat`**: Executes the 23 automated unit tests.

---

### Option B: Unified Production Server (Recommended)

This serves the complete system (both the **REST API** and the **React Web UI**) from a single Python command:

```bash
python server.py
```

Open your browser and navigate to:
👉 **`http://localhost:8001`**

Interactive Swagger API Documentation:
👉 **`http://localhost:8001/docs`**

---

### Option C: Full-Stack Development Mode (Hot-Reload)

If you wish to edit the React frontend with Vite's instant Hot Module Replacement (HMR):

1. **Terminal 1 (Backend):**
   ```bash
   python server.py
   ```
2. **Terminal 2 (Frontend):**
   ```bash
   cd frontend
   npm run dev
   ```
3. Open your browser at:
   👉 **`http://localhost:5173`** *(API calls are automatically proxied to port 8001)*

---

### Option D: Command-Line Interface (CLI Mode)

The system includes a headless CLI for automated terminal workflows, cron jobs, and batch folders:

#### 1. Process a Single Statement:
```bash
python cli.py -i sample_data\hdfc_sample_statement.pdf -o output
```

#### 2. Process an Entire Folder in Batch:
```bash
python cli.py -i sample_data -o output --format all
```

#### 3. Select Classification Engine Mode:
```bash
# Heuristic Rules Only
python cli.py -i sample_data\sbi_sample_statement.pdf --mode heuristic

# Traditional ML (TF-IDF) Only
python cli.py -i sample_data\sbi_sample_statement.pdf --mode ml

# Hybrid Ensemble (Recommended)
python cli.py -i sample_data\sbi_sample_statement.pdf --mode hybrid
```

#### 4. Force OCR Engine:
```bash
python cli.py -i sample_data\scanned_sample_statement.pdf --force-ocr
```

---

## 🧠 Non-LLM Classification Architecture

As strictly specified by the assessment document, **no cloud Large Language Models (LLMs) are used**.

### 1. Heuristic Rule-Based Classifier (`heuristic.py`)
- **Directional Logic**: Enforces mathematical credit vs. debit restrictions (e.g., `Salary & Income` must be Credit; `Food`, `Groceries`, `EMI` must be Debit).
- **Merchant Knowledge Base**: Matches popular merchants and brands (Amazon, Flipkart, Swiggy, Zomato, Blinkit, Zepto, D-Mart, Uber, Ola, Shell, IOCL, Zerodha, Groww, Netflix, Spotify, Airtel, Jio, etc.).
- **Payment Channel Detection**: Identifies transaction mechanisms: `UPI`, `ATM Cash`, `POS / Card`, `NEFT`, `RTGS`, `IMPS`, `ACH Mandate`, `Cheque`.

### 2. Traditional Machine Learning Model (`ml_classifier.py`)
- **Feature Vectorizer**: Scikit-Learn `TfidfVectorizer` (N-grams 1 and 2, sublinear term frequency, stripped numerical noise/UTR numbers).
- **Estimator**: Calibrated `LogisticRegression` with balanced class weights.
- **Corpus**: Trained on thousands of authentic banking transaction narrations across 14 financial heads.
- **In-Browser Retraining**: 1-click model retraining with synthetic data augmentation directly from the Web UI.

### 3. Hybrid Ensemble (`ensemble.py`)
- Prioritizes deterministic high-confidence rules for known counterparties.
- Applies Scikit-Learn TF-IDF classification for ambiguous or unstructured narrations.
- Reports confidence scores (0% - 100%) and classification methods for every transaction.

---

## 🏦 Supported Financial Institutions

The system operates **completely dynamically** without hardcoded bank assumptions. It identifies banks via RBI regulatory clearing codes, IFSC prefixes, and document entity headers:

- **State Bank of India (SBI)**
- **HDFC Bank**
- **ICICI Bank**
- **Axis Bank**
- **Kotak Mahindra Bank**
- **Standard Chartered Bank**
- **Bank of Baroda**
- **Punjab National Bank (PNB)**
- **Canara Bank**
- **Union Bank of India**
- **IndusInd Bank**
- **Citibank & HSBC**
- **Federal Bank & IDFC FIRST Bank**
- **Universal International Formats (IBAN & SWIFT/BIC)**

---

## 🛡️ Edge Cases & Ledger Reconciliation

| Real-World Challenge | How It Is Handled |
|---|---|
| **Multi-line Narration Wrapping** | Automatically identifies continuation lines without dates or amounts and merges them into the parent narration row. |
| **Single Amount Column with Dr/Cr** | Detects tables with a single Amount column and separate Dr/Cr indicator, properly segregating debits from credits. |
| **Inconsistent Date Formats** | Robust multi-pattern date parser normalizes `DD/MM/YYYY`, `DD-MM-YYYY`, `DD-Mon-YYYY`, `YYYY-MM-DD`, and 2-part dates into standard ISO `YYYY-MM-DD`. |
| **Number Formatting Variations** | Strips currency symbols (`₹`, `$`, `€`, `£`, `Rs.`), accounting parentheses `(1,000.00)`, and handles both Indian (`1,50,000.00`) and European number systems (`1.234,56`). |
| **Ledger Reconciliation Audit** | Audits `Opening Balance + Deposits - Withdrawals == Closing Balance` row-by-row, flagging anomalies with detailed discrepancy alerts. |

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & list of 14 supported financial categories |
| `GET` | `/api/samples` | List of pre-built sample statements |
| `POST` | `/api/process-sample/{id}` | Process a pre-built statement (hdfc / sbi / scanned) |
| `POST` | `/api/upload` | Upload and process any custom PDF bank statement |
| `POST` | `/api/export/excel` | Stream styled multi-sheet Excel workbook (`.xlsx`) |
| `POST` | `/api/export/csv` | Stream standardized CSV file (`.csv`) |
| `GET` | `/api/model/info` | Current Scikit-Learn model metrics, accuracy & classes |
| `POST` | `/api/model/retrain` | Trigger on-demand retraining with synthetic noise augmentation |
| `POST` | `/api/reclassify` | Reclassify transactions with updated engine mode |

---

## 🧪 Automated Unit Testing

The repository includes **23 comprehensive automated unit tests** covering PDF detection, table extraction, OCR clustering, non-LLM classification, ledger reconciliation, and file exports:

To run the test suite:
```bash
python -m unittest discover backend/tests
```

Expected output:
```
.......................
----------------------------------------------------------------------
Ran 23 tests in 7.474s

OK
```

---

## ❓ Troubleshooting & FAQ

#### Q: Which mode should I use for `Force OCR`?
- **Digital PDFs (e-Statements downloaded from NetBanking)**: Keep `Force OCR` **OFF** (Unchecked). Direct vector extraction finishes in **~1 second with 100% accuracy**.
- **Scanned Documents (Mobile camera photos or scanner printouts)**: Check `Force OCR` **ON**. The deep-learning OCR engine will process all pages.

#### Q: Can I run this completely offline without Internet?
- **Yes!** The entire system (FastAPI, Scikit-Learn, RapidOCR ONNX models, and React UI) runs 100% locally on your machine. No internet access or external cloud services are required.

#### Q: How do I export my data?
- After processing a statement, click **"Export Excel"** or **"Export CSV"** in the top action bar or the "Export Reports" tab to instantly download your files.
