# CitizenSchemeAI System Architecture & Technical Specifications

## 1. Overview
Citizen-Scheme-AI is designed to operate on consumer hardware with zero latency, complete explainability, and local-first data privacy.

```
                           ┌───────────────────────────────┐
                           │      Citizen Web Browser      │
                           └───────────────┬───────────────┘
                                           │ HTTP / WS
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             Streamlit Web Frontend                               │
│  - Multilingual Selector (EN, HI, MR)    - Dynamic Eligibility Form Wizard       │
│  - Instant Search & Filter Bar           - Scheme Side-by-Side Comparison Matrix │
│  - Grounded RAG Chat Interface           - Markdown Action Roadmap Export        │
└──────────────────────────────────────────┬───────────────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
                    ▼                                             ▼
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│          Security Guard              │     │         Deterministic Engine         │
│  - Prompt Injection Regex Filters    │     │  - Evaluates Age, Gender, Income,    │
│  - XSS Strip & HTML Entity Escape    │     │    Category, Landholding, BPL, etc.  │
│  - Path Traversal Disallowance       │     │  - Computes Match % & Audits Met /   │
│  - Query Length Truncation (1000 ch) │     │    Unmet / Conditional Criteria      │
└──────────────────┬───────────────────┘     └──────────────────┬───────────────────┘
                   │                                            │
                   ▼                                            │
┌──────────────────────────────────────┐                        │
│          Hybrid RAG Engine           │                        │
│  - Devanagari Unicode Tokenization   │                        │
│  - TF-IDF Vector Space (5000 feats)  │                        │
│  - Vernacular Synonym Expansion      │                        │
│  - Lexical Keyword Overlap Boost     │                        │
│  - Grounded Response Synthesizer     │                        │
└──────────────────┬───────────────────┘                        │
                   │                                            │
                   └──────────────────────┬─────────────────────┘
                                          │
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            Core Data & Scheme Store                              │
│  - Pydantic v2 Validated Schema (Scheme, CitizenProfile, EligibilityResult)      │
│  - Pre-seeded High-Impact Central & State Schemes (`data/schemes.json`)          │
│  - In-Memory Scheme Database Singleton (`core/database.py`)                     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Key Architecture Pillars

### 2.1 Deterministic Rule Engine vs. Stochastic LLM
- **The Problem:** Naive LLMs are generative and probabilistic. When a citizen asks *"Am I eligible for PM-KISAN?"*, an LLM can hallucinate qualifications, misquote income thresholds, or assume facts not in statutory guidelines.
- **The Solution:** CitizenSchemeAI decouples **Eligibility Determination** from **Natural Language Explanation**:
  - The `EligibilityEngine` performs 100% deterministic auditing on strict boolean and numerical conditions.
  - The results are tagged explicitly with `met_criteria`, `unmet_criteria`, and `conditional_criteria`.
  - Explanations are templated with dynamic localized strings, preventing hallucinations completely.

### 2.2 Offline Hybrid RAG Architecture
- **Devanagari Unicode Tokenizer:** Standard tokenizers break Hindi/Marathi combined characters (matras). CitizenSchemeAI incorporates Unicode character range `\u0900-\u097F` into the vectorizer regex pattern `r"(?u)[\w\u0900-\u097F]{2,}"`.
- **TF-IDF + Lexical Boosting:** Retains inverted index vector spaces with exact keyword overlap scoring, ensuring instant retrieval (<10ms) without model downloading or memory hogging.
- **Vernacular Synonym Expansion:** Expands terms like *kisan*, *krishi*, *aarogya*, *padhai*, *pension*, *vidyarthi*, *karz* into canonical scheme tags.

### 2.3 Security Guardrails
- **Prompt Injection Defense:** Blocks jailbreaks and prompt extraction attacks.
- **XSS Stripping:** Escapes HTML before UI rendering.
- **Path Traversal Shield:** Sanitizes filenames when ingesting scheme records.
- **Input Bounding:** Restricts queries to 1,000 characters to prevent denial-of-service memory spikes.
