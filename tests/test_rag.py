"""Tests for RAG retriever and conversational citizen assistant."""

import pytest
from core.database import SchemeDatabase
from core.rag_engine import SchemeRAGRetriever, CitizenRAGAssistant


@pytest.fixture
def rag_retriever():
    db = SchemeDatabase()
    return SchemeRAGRetriever(db)


def test_rag_index_building(rag_retriever):
    assert len(rag_retriever.corpus_chunks) > 0
    assert rag_retriever.vectorizer is not None
    assert rag_retriever.tfidf_matrix is not None


def test_rag_retrieval_for_kisan(rag_retriever):
    results = rag_retriever.retrieve("farmer PM Kisan support", top_k=3)
    assert len(results) > 0
    assert any("pm-kisan" in r["scheme_id"] for r in results)


def test_rag_synonym_expansion(rag_retriever):
    # 'krishi' should expand to farmer/agriculture/pm-kisan
    results = rag_retriever.retrieve("krishi subsidy", top_k=3)
    assert len(results) > 0
    assert any("pm-kisan" in r["scheme_id"] for r in results)


def test_rag_assistant_grounded_response(rag_retriever):
    assistant = CitizenRAGAssistant(rag_retriever)
    resp = assistant.generate_response("How can I get 5 lakh health insurance?", lang="en")
    assert "Ayushman Bharat" in resp["answer"]
    assert len(resp["citations"]) > 0
    assert len(resp["relevant_schemes"]) > 0


def test_rag_assistant_hindi_response(rag_retriever):
    assistant = CitizenRAGAssistant(rag_retriever)
    resp = assistant.generate_response("किसान योजना के लाभ क्या हैं?", lang="hi")
    assert "पीएम-किसान" in resp["answer"] or "PM-KISAN" in resp["answer"]
    assert len(resp["citations"]) > 0


def test_rag_assistant_empty_query(rag_retriever):
    assistant = CitizenRAGAssistant(rag_retriever)
    resp = assistant.generate_response("", lang="en")
    assert "Please ask a question" in resp["answer"]
    assert len(resp["citations"]) == 0


def test_rag_faq_retrieval_and_direct_answer(rag_retriever):
    """Specific FAQ inquiry must retrieve Mudra and include Direct Grounded Answer."""
    assistant = CitizenRAGAssistant(rag_retriever)
    resp = assistant.generate_response("What is the maximum loan limit under Mudra?", lang="en")
    assert "Mudra" in resp["answer"]
    assert "Direct Grounded Answer" in resp["answer"] or "Official Answer" in resp["answer"]
    assert len(resp["citations"]) > 0


def test_rag_hinglish_medical_treatment_query(rag_retriever):
    """Hinglish medical query ('ilaj') must prioritize Ayushman Bharat."""
    results = rag_retriever.retrieve("ilaj ke liye 5 lakh ka card kaise banega", top_k=3)
    assert len(results) > 0
    assert results[0]["scheme_id"] == "pmjay-ayushman"


def test_rag_citation_scores_strictly_bounded(rag_retriever):
    """Relevance scores in citations must never exceed 100%."""
    assistant = CitizenRAGAssistant(rag_retriever)
    queries = [
        "What is the maximum loan limit under Mudra?",
        "Who is eligible for Ayushman Bharat?",
        "PM-KISAN installment date and land requirements",
        "sukanya samriddhi yojana girl child savings"
    ]
    for q in queries:
        resp = assistant.generate_response(q, lang="en")
        for cite in resp["citations"]:
            pct_val = float(cite["relevance_score"].replace("%", ""))
            assert 0.0 <= pct_val <= 100.0, f"Score {pct_val}% exceeded bounds!"
