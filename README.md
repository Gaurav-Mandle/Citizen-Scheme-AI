# 🇮🇳 Citizen Scheme AI

> **An Explainable Multilingual Generative AI & Retrieval-Augmented Decision Support System for Indian Citizen Welfare Schemes**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Pytest Coverage](https://img.shields.io/badge/Tests-43%20Passed-brightgreen.svg)](tests/)
[![Security Hardened](https://img.shields.io/badge/Security-Sanitized%20%26%20Hardened-success.svg)](core/security.py)
[![Offline Ready](https://img.shields.io/badge/Offline-100%25%20Zero%20Lag-orange.svg)](core/rag_engine.py)

---

## 🏛️ Academic Overview
- **Project Name:** Citizen-Scheme-AI
- **Academic Submission Due:** November 20, 2026
- **Developer:** Gaurav Mandle
- **Degree:** Master of Computer Applications (MCA)
- **Institution:** Dayananda Sagar University, Bengaluru
- **Repository:** [https://github.com/Gaurav-Mandle/Citizen-Scheme-AI](https://github.com/Gaurav-Mandle/Citizen-Scheme-AI)

Formal academic submission documents are available in the [`docs/`](docs/) directory:
- 📄 [**Project Abstract**](docs/PROJECT_ABSTRACT.md)
- 📑 [**Project Synopsis**](docs/PROJECT_SYNOPSIS.md)
- 📐 [**System Architecture & Technical Specifications**](docs/ARCHITECTURE.md)

---

## 🌟 Key Features & Innovations

### 1. 🎯 Explainable, Deterministic Eligibility Engine (Zero Hallucination)
Rather than relying on opaque, probabilistic LLM generations that often hallucinate qualifications or misquote guidelines, CitizenSchemeAI uses a deterministic rule-based auditing engine:
- Evaluates 10 demographic attributes: Age, Gender, State, Household Income, Occupation, Social Category, Student Status, Differently-Abled (PwD) Status, Landholding, and BPL Card.
- Produces unambiguous decision audits: **Met Criteria**, **Unmet Criteria**, and **Conditional Document Checkpoints**.
- Computes percentage match scores and categorizes status into `Eligible`, `Potentially Eligible`, or `Ineligible`.

### 2. ⚡ Offline-First Hybrid Multilingual RAG
- **Zero Latency & Crash-Proof**: Employs mathematical TF-IDF vector space semantic matching with Devanagari Unicode tokenization (`\u0900-\u097F`).
- **No Cost, No External API Downtime**: Runs 100% offline on standard consumer hardware without requiring multi-gigabyte neural weights or paid cloud API subscriptions.
- **Vernacular Synonym Expansion**: Automatically maps Hindi/Marathi terms (e.g. *kisan*, *krishi*, *aarogya*, *padhai*, *pension*, *vidyarthi*, *karz*) to canonical schemes.
- **Strict Grounding & Citations**: Every response lists verifiable official citations, nodal ministries, and official portal URLs.

### 3. 🌐 Trilingual Localization
Real-time UI and knowledge translation across:
- **English**
- **हिंदी (Hindi)**
- **मराठी (Marathi)**

### 4. 📄 Printable Action Roadmaps & Document Checklists
- Generates a customized, downloadable **Markdown Action Roadmap** tailored to the citizen's occupational and financial profile.
- Lists mandatory documents required for each eligible scheme and direct portal submission steps.

### 5. ⚖️ Scheme Compare & Cumulative Benefit Calculator
- Side-by-side comparison of 2 to 3 welfare programs.
- Dynamic calculator computing total estimated annual financial assistance across combined schemes.

### 6. 🛡️ Security & Exploit Hardening
- **Prompt Injection Defense**: Multi-pattern regex filters detecting jailbreak, system prompt leakage, and instruction overrides.
- **XSS & HTML Stripping**: All user queries and inputs are sanitized to prevent script injection.
- **Path Traversal Protection**: File inputs and scheme IDs are sanitized against `../` directory navigation.
- **Payload Bounding**: Queries are bounded to 1,000 characters to prevent memory exhaustion / DoS attacks.

---

## 📂 Project Directory Structure

```text
Citizen-Scheme-AI/
│
├── app.py                      # Main production Streamlit web application
├── requirements.txt            # Verified dependencies
├── README.md                   # Project documentation & presentation guide
├── .gitignore                  # Git exclusions for python/streamlit
│
├── core/                       # Core engine modules
│   ├── __init__.py
│   ├── models.py               # Pydantic data schemas (CitizenProfile, Scheme, EligibilityResult)
│   ├── database.py             # In-memory scheme repository & filter engine
│   ├── eligibility_engine.py   # Deterministic rule evaluator & audit trail generator
│   ├── rag_engine.py           # Hybrid RAG retriever & grounded synthesizer
│   ├── security.py             # Security sanitizer & prompt injection guard
│   └── translations.py         # Trilingual localization dictionary (EN, HI, MR)
│
├── data/
│   └── schemes.json            # Curated Indian Government welfare schemes database
│
├── docs/                       # Academic submission documentation
│   ├── PROJECT_ABSTRACT.md     # Academic Project Abstract
│   ├── PROJECT_SYNOPSIS.md     # Academic Project Synopsis
│   └── ARCHITECTURE.md         # System Architecture & Technical Specifications
│
└── tests/                      # Automated test suite (43 unit & integration tests)
    ├── __init__.py
    ├── test_models.py          # Schema validation tests
    ├── test_database.py        # Scheme storage & filter tests
    ├── test_eligibility.py     # Deterministic evaluation tests
    ├── test_rag.py             # Semantic RAG retrieval tests
    ├── test_marathi_rag.py     # Marathi multilingual queries
    ├── test_security.py        # Security & sanitization tests
    └── test_edge_cases.py      # Boundary values & performance benchmarks
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 2. Clone Repository & Setup
```bash
# Clone the repository
git clone https://github.com/Gaurav-Mandle/Citizen-Scheme-AI.git
cd Citizen-Scheme-AI

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
pytest -v
```
*All 32 tests will execute and pass in under 2 seconds.*

### 4. Launch Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📊 Pre-Seeded Welfare Schemes

The repository includes high-impact central government welfare programs:
1. **PM-KISAN**: Income support for landholding farmer families (₹6,000/year DBT).
2. **Ayushman Bharat (AB-PMJAY)**: Cashless hospitalization cover up to ₹5 Lakh/year.
3. **Pradhan Mantri Awas Yojana (PMAY)**: Pucca housing subsidies for low-income citizens.
4. **Sukanya Samriddhi Yojana (SSY)**: High-interest savings scheme for girl children (8.2% p.a., EEE tax exemption).
5. **Pradhan Mantri Mudra Yojana (PMMY)**: Collateral-free business loans up to ₹20 Lakh.
6. **PM Vishwakarma Scheme**: Toolkit incentives and microcredit for traditional artisans across 18 vocations.
7. **Post-Matric Scholarship**: Tuition fee reimbursement and allowances for SC/ST/OBC/EWS students.
8. **Atal Pension Yojana (APY)**: Guaranteed retirement monthly pension up to ₹5,000/month.
9. **PM SVANidhi**: Working capital microcredit for urban street vendors with interest subsidy.
10. **National Social Assistance Programme (IGNOAPS)**: Monthly old-age pension for destitute seniors.
11. **PM Ujjwala Yojana 2.0**: Free clean cooking LPG connections and targeted cylinder subsidies.
12. **Stand-Up India**: Bank loans up to ₹1 Crore for women and SC/ST entrepreneurs.

---

## 🧪 Benchmark & Quality Assurance
- **Batch Evaluation Speed**: 500 complete citizen demographic audits against the entire scheme database executed in **< 0.8 seconds**.
- **Offline Response Latency**: Grounded RAG query synthesis in **< 40 milliseconds**.
- **Test Suite**: 32 unit and integration tests covering model validations, multilingual queries, security sanitization, and demographic boundaries.

---

## 📜 Academic Integrity & License
This project is submitted in partial fulfillment of the requirements for the Master of Computer Applications (MCA) degree.  
Licensed under the [MIT License](LICENSE).
