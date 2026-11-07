"""Tests for Marathi localized RAG queries and responses."""

import pytest
from core.database import SchemeDatabase
from core.rag_engine import SchemeRAGRetriever, CitizenRAGAssistant


@pytest.fixture
def assistant():
    db = SchemeDatabase()
    retriever = SchemeRAGRetriever(db)
    return CitizenRAGAssistant(retriever)


def test_marathi_farmer_query(assistant):
    resp = assistant.generate_response("शेतकरी योजना कोणती आहे?", lang="mr")
    assert "पीएम-किसान" in resp["answer"] or "PM-KISAN" in resp["answer"]
    assert len(resp["citations"]) > 0


def test_marathi_girl_child_query(assistant):
    resp = assistant.generate_response("मुलींसाठी सुकन्या समृद्धी योजना काय आहे?", lang="mr")
    assert "सुकन्या" in resp["answer"] or "Sukanya" in resp["answer"]
    assert len(resp["citations"]) > 0


def test_marathi_loan_query(assistant):
    resp = assistant.generate_response("व्यवसायासाठी कर्ज कसे मिळेल?", lang="mr")
    assert "मुद्रा" in resp["answer"] or "Mudra" in resp["answer"] or "SVANidhi" in resp["answer"]
