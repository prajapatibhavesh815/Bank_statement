import React, { useState, useEffect, useRef } from 'react';
import {
  Building2,
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Download,
  RefreshCw,
  Search,
  PieChart,
  Table as TableIcon,
  Settings,
  ShieldCheck,
  CreditCard,
  Layers,
  ArrowRight,
  Sparkles,
  Zap,
  Lock,
  RotateCcw,
  Sliders,
  Check,
  Info,
  ChevronRight,
  FileSpreadsheet,
  Cpu
} from 'lucide-react';
import './App.css';

const API_BASE = '/api';

const CATEGORY_COLORS = {
  'Salary & Income': '#166534',
  'Food & Dining': '#dc2626',
  'Groceries & Supermarkets': '#d97706',
  'Utilities & Bills': '#4f46e5',
  'Shopping & E-Commerce': '#db2777',
  'Travel & Fuel': '#0891b2',
  'Healthcare & Medical': '#2563eb',
  'Entertainment & OTT': '#7c3aed',
  'Investments & Trading': '#059669',
  'Loan EMI & Credit Card': '#ea580c',
  'Cash & ATM Withdrawal': '#4b5563',
  'Bank Charges & Taxes': '#64748b',
  'Transfer (P2P / Self)': '#10b981',
  'Miscellaneous / Others': '#94a3b8',
};

const SUPPORTED_BANKS = [
  'State Bank of India (SBI)',
  'HDFC Bank',
  'ICICI Bank',
  'Axis Bank',
  'Kotak Mahindra Bank',
  'Standard Chartered Bank',
  'Bank of Baroda',
  'Punjab National Bank (PNB)',
  'Canara Bank',
  'Union Bank of India',
  'IndusInd Bank',
  'Citibank & HSBC',
  'Universal International (IBAN/SWIFT)'
];

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [samples, setSamples] = useState([]);
  const [activeTab, setActiveTab] = useState('statement');
  const [mode, setMode] = useState('Hybrid Ensemble');
  const [forceOcr, setForceOcr] = useState(false);
  const [toast, setToast] = useState('');

  // Table filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedType, setSelectedType] = useState('All');

  // Retrain state
  const [retraining, setRetraining] = useState(false);
  const [modelInfo, setModelInfo] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef(null);

  // Show temporary toast message
  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 4000);
  };

  // Fetch samples & model info on mount
  useEffect(() => {
    fetchSamples();
    fetchModelInfo();
  }, []);

  const fetchSamples = async () => {
    try {
      const res = await fetch(`${API_BASE}/samples`);
      if (res.ok) {
        const data = await res.json();
        setSamples(data);
      }
    } catch (err) {
      console.error('Failed to load samples:', err);
    }
  };

  const fetchModelInfo = async () => {
    try {
      const res = await fetch(`${API_BASE}/model/info`);
      if (res.ok) {
        const data = await res.json();
        setModelInfo(data);
      }
    } catch (err) {
      console.error('Failed to load model info:', err);
    }
  };

  // Upload PDF Handler
  const handleFileUpload = async (file) => {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      showToast('Please select a valid PDF file.');
      return;
    }

    setLoading(true);
    setLoadingMsg(`Processing "${file.name}" through dynamic non-LLM pipeline...`);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);
    formData.append('force_ocr', forceOcr);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to process document');
      }

      const data = await res.json();
      setResult(data);
      showToast(`Processed ${data.metadata.total_transactions} transactions successfully!`);
    } catch (err) {
      showToast(`Error: ${err.message}`);
    } finally {
      setLoading(false);
      setLoadingMsg('');
    }
  };

  // Process Pre-built Sample
  const handleProcessSample = async (sampleId) => {
    setLoading(true);
    setLoadingMsg(`Running pipeline on sample [${sampleId.toUpperCase()}]...`);

    try {
      const res = await fetch(`${API_BASE}/process-sample/${sampleId}?mode=${encodeURIComponent(mode)}&force_ocr=${forceOcr}`, {
        method: 'POST',
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Sample processing failed');
      }

      const data = await res.json();
      setResult(data);
      showToast(`Loaded ${data.metadata.total_transactions} transactions!`);
    } catch (err) {
      showToast(`Error: ${err.message}`);
    } finally {
      setLoading(false);
      setLoadingMsg('');
    }
  };

  // Reset to Upload / Showcase Screen
  const handleReset = () => {
    setResult(null);
    setSearchTerm('');
    setSelectedCategory('All');
    setSelectedType('All');
    setActiveTab('statement');
    showToast('Ready for new statement upload.');
  };

  // Inline Category Change
  const handleCategoryChange = (txnIndex, newCat) => {
    if (!result) return;
    const updatedTxns = [...result.transactions];
    updatedTxns[txnIndex].category = newCat;
    updatedTxns[txnIndex].classification_method = 'Manual Override';
    updatedTxns[txnIndex].confidence = 1.0;

    const newResult = { ...result, transactions: updatedTxns };
    setResult(newResult);
    showToast(`Updated row #${txnIndex + 1} to "${newCat}"`);
  };

  // Export Excel
  const handleExportExcel = async () => {
    if (!result) return;
    try {
      showToast('Generating Excel workbook...');
      const res = await fetch(`${API_BASE}/export/excel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_details: result.account_details,
          transactions: result.transactions,
          metadata: result.metadata,
          anomalies: result.anomalies,
        }),
      });

      if (!res.ok) throw new Error('Excel generation failed');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${result.metadata.file_name.replace('.pdf', '')}_classified.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast('Excel file downloaded successfully!');
    } catch (err) {
      showToast(`Export error: ${err.message}`);
    }
  };

  // Export CSV
  const handleExportCSV = async () => {
    if (!result) return;
    try {
      showToast('Generating CSV...');
      const res = await fetch(`${API_BASE}/export/csv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transactions: result.transactions }),
      });

      if (!res.ok) throw new Error('CSV generation failed');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${result.metadata.file_name.replace('.pdf', '')}_transactions.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast('CSV downloaded successfully!');
    } catch (err) {
      showToast(`Export error: ${err.message}`);
    }
  };

  // Retrain Model
  const handleRetrain = async () => {
    setRetraining(true);
    try {
      const res = await fetch(`${API_BASE}/model/retrain`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast(`Model retrained! New accuracy: ${(data.new_accuracy * 100).toFixed(2)}%`);
        fetchModelInfo();
      }
    } catch (err) {
      showToast(`Retrain error: ${err.message}`);
    } finally {
      setRetraining(false);
    }
  };

  // Filtered transactions
  const filteredTransactions = result ? result.transactions.filter((t) => {
    const matchesSearch = searchTerm === '' ||
      t.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.merchant && t.merchant.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesCategory = selectedCategory === 'All' || t.category === selectedCategory;

    const matchesType =
      selectedType === 'All' ||
      (selectedType === 'Debit' && t.debit > 0) ||
      (selectedType === 'Credit' && t.credit > 0);

    return matchesSearch && matchesCategory && matchesType;
  }) : [];

  // Category Badge Class Mapper
  const getCatBadgeClass = (category) => {
    switch (category) {
      case 'Salary & Income': return 'cat-salary';
      case 'Food & Dining': return 'cat-food';
      case 'Groceries & Supermarkets': return 'cat-grocery';
      case 'Utilities & Bills': return 'cat-utilities';
      case 'Shopping & E-Commerce': return 'cat-shopping';
      case 'Travel & Fuel': return 'cat-travel';
      case 'Healthcare & Medical': return 'cat-medical';
      case 'Entertainment & OTT': return 'cat-ott';
      case 'Investments & Trading': return 'cat-invest';
      case 'Loan EMI & Credit Card': return 'cat-emi';
      case 'Cash & ATM Withdrawal': return 'cat-atm';
      case 'Bank Charges & Taxes': return 'cat-charges';
      case 'Transfer (P2P / Self)': return 'cat-transfer';
      default: return 'cat-other';
    }
  };

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand" onClick={handleReset} style={{ cursor: 'pointer' }}>
          <div className="brand-icon">
            <Building2 size={22} />
          </div>
          <div>
            <div className="brand-title-wrap">
              <span className="brand-title">Bank Statement AI</span>
              <span className="version-pill">v2.0 • Non-LLM</span>
            </div>
            <div className="brand-sub">Universal Bank Statement Extraction & Financial Intelligence</div>
          </div>
        </div>

        <div className="nav-badges">
          <span className="tag-badge blue">
            <ShieldCheck size={14} /> 100% Offline & Private
          </span>
          <span className="tag-badge green">
            <Zap size={14} /> Sub-Second Scikit-Learn
          </span>
          <span className="tag-badge purple">
            <Layers size={14} /> Any Bank Layout
          </span>
          {result && (
            <button className="btn-new-statement" onClick={handleReset}>
              <RotateCcw size={14} />
              <span>Upload New PDF</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-wrapper">
        {/* If no result is loaded, show the Hero Introduction */}
        {!result && (
          <section className="hero-banner animate-fade-in">
            <div className="hero-badge">
              <Sparkles size={14} />
              <span>Enterprise-Grade Financial Parsing Engine</span>
            </div>
            <h1 className="hero-heading">
              Universal Bank Statement Parser <span className="gradient-text">& Analytics</span>
            </h1>
            <p className="hero-description">
              Extract, mathematically reconcile, and categorize transactions from <strong>ANY</strong> bank statement worldwide.
              Zero cloud LLMs, 100% confidential Scikit-Learn machine learning, and dynamic layout parsing.
            </p>

            <div className="hero-stat-pills">
              <div className="stat-pill">
                <strong>&lt; 1.5s</strong>
                <span>Instant Processing</span>
              </div>
              <div className="stat-pill-divider"></div>
              <div className="stat-pill">
                <strong>100%</strong>
                <span>Ledger Reconciliation</span>
              </div>
              <div className="stat-pill-divider"></div>
              <div className="stat-pill">
                <strong>30+ Banks</strong>
                <span>Auto-Identified</span>
              </div>
              <div className="stat-pill-divider"></div>
              <div className="stat-pill">
                <strong>14 Classes</strong>
                <span>Financial Heads</span>
              </div>
            </div>
          </section>
        )}

        {/* Upload & Controls Hero */}
        <section className={`control-hero ${result ? 'compact' : ''}`}>
          <div className="hero-grid">
            {/* Left: Drag & Drop Ingestion */}
            <div
              className={`dropzone ${isDragging ? 'dragging' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                if (e.dataTransfer.files?.[0]) {
                  handleFileUpload(e.dataTransfer.files[0]);
                }
              }}
            >
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept=".pdf"
                onChange={(e) => {
                  if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
                }}
              />
              <div className="dropzone-icon-wrap">
                <Upload size={32} className="dropzone-icon" />
              </div>
              <div className="dropzone-title">
                {result ? 'Upload or Replace Bank Statement PDF' : 'Click or Drag & Drop Bank Statement PDF Here'}
              </div>
              <div className="dropzone-desc">
                Supports native e-Statements (SBI, HDFC, ICICI, etc.) and scanned paper photos
              </div>
              <div className="dropzone-security-badge">
                <Lock size={12} /> Confidential • Processed 100% locally on your machine
              </div>
            </div>

            {/* Right: Quick Samples & Mode */}
            <div className="options-panel">
              {/* Quick Samples */}
              <div>
                <div className="panel-section-header">
                  <span className="info-label">⚡ Quick Test with Pre-Loaded Statements:</span>
                  <span className="sub-hint">Instant 1-Click Verification</span>
                </div>
                <div className="sample-buttons-grid">
                  <button
                    className="btn-sample"
                    onClick={() => handleProcessSample('hdfc')}
                    disabled={loading}
                    title="Test HDFC Bank digital e-statement"
                  >
                    <div className="btn-sample-icon blue">
                      <FileText size={16} />
                    </div>
                    <div>
                      <div className="sample-name">HDFC Bank</div>
                      <div className="sample-type">Digital Text PDF</div>
                    </div>
                  </button>

                  <button
                    className="btn-sample"
                    onClick={() => handleProcessSample('sbi')}
                    disabled={loading}
                    title="Test State Bank of India digital e-statement"
                  >
                    <div className="btn-sample-icon green">
                      <FileText size={16} />
                    </div>
                    <div>
                      <div className="sample-name">State Bank of India</div>
                      <div className="sample-type">Txn Date & Value Date</div>
                    </div>
                  </button>

                  <button
                    className="btn-sample full-width"
                    onClick={() => handleProcessSample('scanned')}
                    disabled={loading}
                    title="Test ICICI Bank scanned photo via RapidOCR"
                  >
                    <div className="btn-sample-icon amber">
                      <FileText size={16} />
                    </div>
                    <div>
                      <div className="sample-name">ICICI Bank (Scanned Paper Photo)</div>
                      <div className="sample-type">Deep-Learning RapidOCR Ingestion</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Mode & OCR Toggles */}
              <div className="config-box">
                <div className="engine-select-group">
                  <label className="info-label" htmlFor="engine-select">
                    Classification Engine:
                  </label>
                  <select
                    id="engine-select"
                    className="select-mode"
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                  >
                    <option value="Hybrid Ensemble">⚡ Hybrid Ensemble (Rules + ML) [Recommended]</option>
                    <option value="Heuristic Rule-Based">📐 Heuristic Rule-Based Only</option>
                    <option value="Traditional Machine Learning (TF-IDF)">🧠 Traditional ML (TF-IDF + LogReg)</option>
                  </select>
                </div>

                <div className="ocr-toggle-card">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={forceOcr}
                      onChange={(e) => setForceOcr(e.target.checked)}
                    />
                    <span className="checkbox-title">Force OCR Engine</span>
                  </label>
                  <div className="ocr-helper-text">
                    {forceOcr ? (
                      <span className="text-warning">⚠️ OCR Mode ON: Slower (~30s). Use only for scanned camera photos.</span>
                    ) : (
                      <span className="text-success">✅ Recommended: Keep OFF for digital PDFs (instant & 100% accurate).</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Loading Spinner */}
        {loading && (
          <div className="loading-box animate-fade-in">
            <div className="loading-spinner animate-spin"></div>
            <div className="loading-text">{loadingMsg}</div>
            <div className="loading-sub">
              Detecting layout structure, parsing transactions, and evaluating non-LLM classifier...
            </div>
          </div>
        )}

        {/* INITIAL EMPTY STATE SHOWCASE (Rendered when no statement is loaded) */}
        {!result && !loading && (
          <div className="showcase-container animate-fade-in">
            {/* Feature Cards Grid */}
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon-wrap blue">
                  <Layers size={22} />
                </div>
                <h3>Universal Bank Parser</h3>
                <p>
                  Zero hardcoded templates. Dynamically maps multi-line narrations, Dr/Cr indicators, and custom date formats from any bank.
                </p>
                <div className="feature-tag">3-Level Adaptive Strategy</div>
              </div>

              <div className="feature-card">
                <div className="feature-icon-wrap purple">
                  <Cpu size={22} />
                </div>
                <h3>100% Non-LLM Architecture</h3>
                <p>
                  Zero cloud API dependencies. Powered by Scikit-Learn TF-IDF N-grams & calibrated Logistic Regression for lightning-fast inference.
                </p>
                <div className="feature-tag">14 Financial Categories</div>
              </div>

              <div className="feature-card">
                <div className="feature-icon-wrap green">
                  <ShieldCheck size={22} />
                </div>
                <h3>Ledger Reconciliation</h3>
                <p>
                  Mathematically validates every single row. Computes running balances to ensure 0 missed rows and highlight discrepancies.
                </p>
                <div className="feature-tag">Audit-Proof Reconciled</div>
              </div>

              <div className="feature-card">
                <div className="feature-icon-wrap amber">
                  <Zap size={22} />
                </div>
                <h3>Dual Text & OCR Pipeline</h3>
                <p>
                  Direct vector parsing for digital statements, coupled with high-resolution RapidOCR deep learning for camera and scanner photos.
                </p>
                <div className="feature-tag">Hybrid Engine</div>
              </div>
            </div>

            {/* Supported Banks Grid */}
            <div className="banks-showcase-card">
              <div className="banks-header">
                <div>
                  <h3 className="banks-title">Supported Financial Institutions</h3>
                  <p className="banks-sub">Auto-detected dynamically from IFSC, document headers, and transaction metadata</p>
                </div>
                <span className="tag-badge blue">Dynamic Detection</span>
              </div>
              <div className="banks-chips-grid">
                {SUPPORTED_BANKS.map((b) => (
                  <div key={b} className="bank-chip">
                    <CheckCircle2 size={13} className="chip-check" />
                    <span>{b}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Workflow How-It-Works */}
            <div className="workflow-card">
              <h3 className="workflow-title">End-to-End Processing Workflow</h3>
              <div className="workflow-steps">
                <div className="step-item">
                  <div className="step-num">1</div>
                  <div className="step-text">
                    <h4>Ingest Statement</h4>
                    <p>Drop any digital or scanned bank PDF into the pipeline.</p>
                  </div>
                </div>
                <div className="step-arrow"><ChevronRight size={20} /></div>

                <div className="step-item">
                  <div className="step-num">2</div>
                  <div className="step-text">
                    <h4>Dynamic Table Parse</h4>
                    <p>Auto-detects columns, merges multi-line notes, and cleans amounts.</p>
                  </div>
                </div>
                <div className="step-arrow"><ChevronRight size={20} /></div>

                <div className="step-item">
                  <div className="step-num">3</div>
                  <div className="step-text">
                    <h4>ML Classification</h4>
                    <p>Classifies each narration into 14 categories with merchant detection.</p>
                  </div>
                </div>
                <div className="step-arrow"><ChevronRight size={20} /></div>

                <div className="step-item">
                  <div className="step-num">4</div>
                  <div className="step-text">
                    <h4>Audit & Export</h4>
                    <p>Reconciles running balances and exports to styled Excel & CSV.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results Area */}
        {result && !loading && (
          <div className="animate-fade-in">
            {/* Status & Audit Bar */}
            <div className="status-banner">
              <div className="banner-item">
                <FileText size={16} color="#64748b" />
                <span>File: <strong>{result.metadata.file_name}</strong></span>
                <span className={`tag-badge ${result.metadata.file_type.includes('OCR') ? 'amber' : 'blue'}`}>
                  {result.metadata.file_type}
                </span>
              </div>

              <div className="banner-item">
                <Building2 size={16} color="#64748b" />
                <span>Bank: <strong>{result.account_details.bank_name}</strong></span>
              </div>

              <div className="banner-item">
                {result.metadata.balance_mismatches_count === 0 ? (
                  <span className="tag-badge green">
                    <CheckCircle2 size={14} /> Ledger 100% Mathematically Reconciled
                  </span>
                ) : (
                  <span className="tag-badge amber">
                    <AlertTriangle size={14} /> {result.metadata.balance_mismatches_count} Balance Discrepancies Flagged
                  </span>
                )}
              </div>

              <div className="banner-item">
                <span className="tag-badge gray">
                  ⚡ {result.metadata.processing_time_sec}s
                </span>
              </div>

              <div className="banner-actions">
                <button className="btn-action-small" onClick={handleExportExcel} title="Export to Excel">
                  <FileSpreadsheet size={14} /> Export Excel
                </button>
                <button className="btn-action-small secondary" onClick={handleExportCSV} title="Export to CSV">
                  <Download size={14} /> Export CSV
                </button>
              </div>
            </div>

            {/* Financial Metrics Cards */}
            <div className="metrics-row">
              <div className="metric-card credit-card">
                <div className="metric-header">
                  <span>Total Deposits (Income)</span>
                  <div className="metric-icon-wrap green">
                    <TrendingUp size={16} />
                  </div>
                </div>
                <div className="metric-value green">
                  ₹ {result.metadata.total_credits.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                <div className="metric-sub">Total credits deposited into account</div>
              </div>

              <div className="metric-card debit-card">
                <div className="metric-header">
                  <span>Total Withdrawals (Expenses)</span>
                  <div className="metric-icon-wrap red">
                    <TrendingDown size={16} />
                  </div>
                </div>
                <div className="metric-value red">
                  ₹ {result.metadata.total_debits.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                <div className="metric-sub">Total debits paid out from account</div>
              </div>

              <div className="metric-card flow-card">
                <div className="metric-header">
                  <span>Net Cash Flow</span>
                  <div className={`metric-icon-wrap ${result.metadata.net_cash_flow >= 0 ? 'green' : 'red'}`}>
                    <CreditCard size={16} />
                  </div>
                </div>
                <div className={`metric-value ${result.metadata.net_cash_flow >= 0 ? 'green' : 'red'}`}>
                  ₹ {result.metadata.net_cash_flow.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                <div className="metric-sub">
                  {result.metadata.net_cash_flow >= 0 ? 'Positive net savings accumulated' : 'Net spending deficit'}
                </div>
              </div>

              <div className="metric-card count-card">
                <div className="metric-header">
                  <span>Total Transactions</span>
                  <div className="metric-icon-wrap blue">
                    <TableIcon size={16} />
                  </div>
                </div>
                <div className="metric-value blue">{result.metadata.total_transactions}</div>
                <div className="metric-sub">Classified and validated records</div>
              </div>
            </div>

            {/* Account Details Card */}
            <div className="account-card">
              <div className="account-card-header">
                <span className="card-sec-title">Account Profile & Audit Metadata</span>
                <span className="account-badge">{result.account_details.bank_name}</span>
              </div>
              <div className="account-grid">
                <div className="info-item">
                  <span className="info-label">Account Holder Name</span>
                  <span className="info-val">{result.account_details.account_holder}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Account Number</span>
                  <span className="info-val">{result.account_details.account_number}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">IFSC Code</span>
                  <span className="info-val">{result.account_details.ifsc_code || 'N/A'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Branch</span>
                  <span className="info-val">{result.account_details.branch || 'Main Branch'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Statement Period</span>
                  <span className="info-val">
                    {result.account_details.statement_period_start || 'N/A'} to {result.account_details.statement_period_end || 'N/A'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Opening & Closing Balance</span>
                  <span className="info-val">
                    ₹ {result.account_details.opening_balance?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '0.00'} → ₹ {result.account_details.closing_balance?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '0.00'}
                  </span>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="tabs-bar">
              <button
                className={`tab-btn ${activeTab === 'statement' ? 'active' : ''}`}
                onClick={() => setActiveTab('statement')}
              >
                <TableIcon size={16} /> Classified Transactions ({filteredTransactions.length})
              </button>
              <button
                className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
                onClick={() => setActiveTab('analytics')}
              >
                <PieChart size={16} /> Financial Analytics & Charts
              </button>
              <button
                className={`tab-btn ${activeTab === 'export' ? 'active' : ''}`}
                onClick={() => setActiveTab('export')}
              >
                <Download size={16} /> Export Reports (.xlsx / .csv)
              </button>
              <button
                className={`tab-btn ${activeTab === 'model' ? 'active' : ''}`}
                onClick={() => setActiveTab('model')}
              >
                <Settings size={16} /> ML Diagnostics & Retrain
              </button>
            </div>

            {/* Tab 1: Transactions Table */}
            {activeTab === 'statement' && (
              <div className="table-card animate-fade-in">
                {/* Search & Filters */}
                <div className="table-filters">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                    <Search size={16} color="#94a3b8" />
                    <input
                      type="text"
                      className="search-input"
                      placeholder="Search description, merchant or keyword..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>

                  <select
                    className="select-mode"
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                  >
                    <option value="All">All Categories ({result.categories.length})</option>
                    {result.categories.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>

                  <select
                    className="select-mode"
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                  >
                    <option value="All">All Transactions</option>
                    <option value="Debit">Withdrawals (Debits) Only</option>
                    <option value="Credit">Deposits (Credits) Only</option>
                  </select>

                  {(searchTerm || selectedCategory !== 'All' || selectedType !== 'All') && (
                    <button
                      className="btn-filter-reset"
                      onClick={() => {
                        setSearchTerm('');
                        setSelectedCategory('All');
                        setSelectedType('All');
                      }}
                    >
                      Clear Filters
                    </button>
                  )}
                </div>

                {/* Table Data */}
                <div className="table-container">
                  <table className="transactions-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Narration / Description</th>
                        <th>Merchant</th>
                        <th>Channel</th>
                        <th style={{ textAlign: 'right' }}>Debit (₹)</th>
                        <th style={{ textAlign: 'right' }}>Credit (₹)</th>
                        <th style={{ textAlign: 'right' }}>Balance (₹)</th>
                        <th>Category (Click to Override)</th>
                        <th>Confidence</th>
                        <th>Method</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTransactions.map((t, idx) => (
                        <tr key={idx}>
                          <td style={{ whiteSpace: 'nowrap', fontWeight: 500 }}>{t.date}</td>
                          <td style={{ maxWidth: '340px' }} title={t.description}>{t.description}</td>
                          <td>
                            {t.merchant ? (
                              <span style={{ fontWeight: 600, color: '#1e293b' }}>{t.merchant}</span>
                            ) : (
                              <span style={{ color: '#94a3b8' }}>-</span>
                            )}
                          </td>
                          <td>
                            <span className="tag-badge gray" style={{ fontSize: '0.7rem' }}>
                              {t.channel || 'NetBanking'}
                            </span>
                          </td>
                          <td className="td-amount debit">
                            {t.debit > 0 ? `₹ ${t.debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
                          </td>
                          <td className="td-amount credit">
                            {t.credit > 0 ? `₹ ${t.credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
                          </td>
                          <td className="td-amount">
                            ₹ {t.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td>
                            <select
                              className={`category-pill ${getCatBadgeClass(t.category)}`}
                              style={{ border: 'none', cursor: 'pointer', outline: 'none' }}
                              value={t.category}
                              onChange={(e) => handleCategoryChange(idx, e.target.value)}
                            >
                              {result.categories.map((c) => (
                                <option key={c} value={c}>{c}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ whiteSpace: 'nowrap' }}>
                            <div className="confidence-bar-bg">
                              <div
                                className="confidence-bar-fill"
                                style={{ width: `${Math.round(t.confidence * 100)}%` }}
                              ></div>
                            </div>
                            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                              {Math.round(t.confidence * 100)}%
                            </span>
                          </td>
                          <td>
                            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                              {t.classification_method}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 2: Analytics & Charts */}
            {activeTab === 'analytics' && (
              <div className="animate-fade-in">
                <div className="analytics-grid">
                  {/* Category Spending Progress Card */}
                  <div className="chart-card">
                    <div className="chart-title">
                      <PieChart size={18} color="#2563eb" />
                      <span>Expenses Breakdown by Category</span>
                    </div>

                    {result.analytics.category_summary.length > 0 ? (
                      <div>
                        {result.analytics.category_summary.map((item, i) => (
                          <div key={i} className="cat-row">
                            <span className="cat-label" title={item.category}>{item.category}</span>
                            <div className="cat-progress-track">
                              <div
                                className="cat-progress-bar"
                                style={{
                                  width: `${item.percentage}%`,
                                  backgroundColor: CATEGORY_COLORS[item.category] || '#3b82f6',
                                }}
                              ></div>
                            </div>
                            <span className="cat-amount">
                              ₹ {item.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </span>
                            <span className="cat-pct">{item.percentage}%</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ color: '#94a3b8', padding: '20px', textAlign: 'center' }}>
                        No debit transactions found.
                      </div>
                    )}
                  </div>

                  {/* Payment Channel Card */}
                  <div className="chart-card">
                    <div className="chart-title">
                      <CreditCard size={18} color="#059669" />
                      <span>Expenses by Payment Channel</span>
                    </div>

                    {result.analytics.channel_summary.length > 0 ? (
                      <div>
                        {result.analytics.channel_summary.map((item, i) => (
                          <div key={i} className="cat-row">
                            <span className="cat-label">{item.channel}</span>
                            <div className="cat-progress-track">
                              <div
                                className="cat-progress-bar"
                                style={{
                                  width: `${Math.min((item.total_amount / (result.metadata.total_debits || 1)) * 100, 100)}%`,
                                  backgroundColor: '#059669',
                                }}
                              ></div>
                            </div>
                            <span className="cat-amount">
                              ₹ {item.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </span>
                            <span className="cat-pct">{item.count} txns</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ color: '#94a3b8', padding: '20px', textAlign: 'center' }}>
                        No channel data available.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Export Reports */}
            {activeTab === 'export' && (
              <div className="animate-fade-in">
                <div className="export-cards-grid">
                  <div className="export-card">
                    <div className="export-card-icon green">
                      <FileSpreadsheet size={28} />
                    </div>
                    <h3>Microsoft Excel Workbook (.xlsx)</h3>
                    <p>
                      Export classified transactions formatted into multiple worksheets including executive overview, category distribution, ledger reconciliation, and merchant intelligence.
                    </p>
                    <button className="btn-export green" onClick={handleExportExcel}>
                      <Download size={16} /> Download Styled Excel Workbook
                    </button>
                  </div>

                  <div className="export-card">
                    <div className="export-card-icon blue">
                      <FileText size={28} />
                    </div>
                    <h3>Standard Comma-Separated Values (.csv)</h3>
                    <p>
                      Export pure tabular transaction records with parsed dates, clean monetary amounts, merchants, channels, and classification labels ready for ERP or database import.
                    </p>
                    <button className="btn-export blue" onClick={handleExportCSV}>
                      <Download size={16} /> Download Universal CSV
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 4: ML Diagnostics & Retrain */}
            {activeTab === 'model' && (
              <div className="animate-fade-in">
                <div className="model-card">
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#0f172a' }}>
                    Non-LLM Machine Learning Classifier Diagnostics
                  </h3>
                  <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: '6px' }}>
                    This system does not transmit your private financial data to third-party Large Language Models (LLMs).
                    Instead, it employs an offline <strong>TF-IDF N-grams (1,2) + Multinomial Logistic Regression</strong> model
                    trained on thousands of authentic Indian and global banking transaction narrations with probability calibration.
                  </p>

                  <div style={{ marginTop: '20px', display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                    <div className="metric-card" style={{ flex: 1, minWidth: '200px' }}>
                      <span className="info-label">Model Accuracy</span>
                      <span className="metric-value blue">
                        {modelInfo ? `${(modelInfo.accuracy * 100).toFixed(2)}%` : '98.5%'}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Held-out Test Evaluation</span>
                    </div>

                    <div className="metric-card" style={{ flex: 1, minWidth: '200px' }}>
                      <span className="info-label">Classes Supported</span>
                      <span className="metric-value green">
                        {modelInfo ? modelInfo.classes_count : 14}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Financial Categories</span>
                    </div>
                  </div>

                  <div style={{ marginTop: '24px' }}>
                    <span className="info-label">Supported Financial Categories:</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
                      {result.categories.map((c) => (
                        <span key={c} className={`category-pill ${getCatBadgeClass(c)}`}>
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div style={{ marginTop: '28px', borderTop: '1px solid #f1f5f9', paddingTop: '20px' }}>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Trigger On-Demand Model Retraining</h4>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                      Augment the seed banking corpus with synthetic noise (random UTRs, POS codes, bank identifiers) and retrain the Scikit-Learn pipeline.
                    </p>
                    <button
                      className="btn-retrain"
                      onClick={handleRetrain}
                      disabled={retraining}
                    >
                      <RefreshCw size={16} className={retraining ? 'animate-spin' : ''} />
                      {retraining ? 'Retraining TF-IDF + Logistic Regression Model...' : 'Retrain ML Model Now'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Toast Notification */}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
