# PROJECT ABSTRACT

**Project Title:** CitizenSchemeAI: An Explainable Multilingual Generative AI & Retrieval-Augmented Decision Support System for Indian Citizen Welfare Schemes  
**Domain:** Artificial Intelligence, Natural Language Processing (NLP), Civic Technology, Information Retrieval  
**Application Field:** E-Governance & Public Service Delivery  

---

### Abstract

A significant bottleneck in democratic governance and social welfare delivery in India is the information asymmetry between welfare entitlements and marginalized citizens. Despite central and state governments allocating hundreds of thousands of crores annually to direct benefit transfer (DBT), healthcare, agricultural subsidies, and educational scholarships, millions of eligible citizens—especially small farmers, unorganized laborers, women, and low-income students—remain excluded due to complex bureaucratic jargon, fragmented portals, lack of native-language assistance, and opaque eligibility criteria.

While Generative AI and Large Language Models (LLMs) present a promising paradigm for citizen interaction, naive LLM deployments in civic governance suffer from high hallucination rates, probabilistic uncertainty, latency spikes, heavy GPU compute requirements, and severe privacy risks associated with sending citizen demographic data to external APIs.

To overcome these critical limitations, this project introduces **Citizen-Scheme-AI**—a production-ready, lightweight, explainable AI system designed specifically for welfare scheme discovery, eligibility assessment, and application navigation. CitizenSchemeAI operates on a dual-engine architecture:
1. **Deterministic Rule Auditing Engine**: Evaluates citizen demographic, occupational, and economic parameters against official statutory scheme rules, generating 100% auditable decisions tagged with "Met Criteria", "Unmet Criteria", and "Conditional Document Checkpoints".
2. **Hybrid Multilingual RAG Retrieval (Vector Space & Lexical Boosting)**: Indexes official scheme gazettes, operational guidelines, FAQs, and required documentation using TF-IDF vector spaces and Devanagari Unicode tokenization. It synthesizes grounded answers with strict source citations without requiring multi-gigabyte models or paid external APIs.

The system features real-time trilingual localization (English, Hindi, and Marathi), a dynamic Citizen Eligibility Wizard, a Scheme Comparison & Cumulative Benefit Calculator, and an automated Markdown Action Roadmap generator. The architecture is hardened against prompt injection, cross-site scripting (XSS), and path traversal attacks. Experimental evaluations demonstrate sub-millisecond deterministic evaluation, zero hallucination on criteria checks, and seamless offline responsiveness on standard consumer hardware, providing an accessible, transparent, and trustworthy bridge between citizens and public welfare.
