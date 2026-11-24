"""
Citizen Scheme AI - Modern Web API Server
FastAPI backend powering the modern civic tech web portal.
Connects with core database, deterministic eligibility engine, and hybrid RAG assistant.
"""

import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.database import get_scheme_db
from core.models import CitizenProfile, Scheme, EligibilityResult
from core.eligibility_engine import EligibilityEngine
from core.rag_engine import CitizenRAGAssistant, SchemeRAGRetriever
from core.translations import TRANSLATIONS, get_text
from core.security import SecurityGuard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="Citizen Scheme AI API",
    description="Deterministic Welfare Eligibility & Hybrid Multilingual RAG Navigator",
    version="2.0.0"
)

# CORS middleware for open/local dev access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton state initialization
db = get_scheme_db()
rag_retriever = SchemeRAGRetriever(db)
rag_assistant = CitizenRAGAssistant(rag_retriever)


# -------------------------------------------------------------------------
# Request / Response Schemas
# -------------------------------------------------------------------------

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Citizen inquiry")
    lang: str = Field(default="en", description="Interface language code: en, hi, mr")


class ChatCitation(BaseModel):
    source: str
    scheme_name: str
    relevance_score: str


class ChatResponse(BaseModel):
    query: str
    answer: str
    citations: List[Dict[str, Any]]
    lang: str


class RoadmapRequest(BaseModel):
    profile: CitizenProfile
    lang: str = Field(default="en", description="Language for roadmap: en, hi, mr")


class CompareRequest(BaseModel):
    scheme_ids: List[str] = Field(..., min_length=1, description="List of scheme IDs to compare")


class SchemeCreatePayload(BaseModel):
    id: str
    name: str
    native_names: Dict[str, str] = Field(default_factory=dict)
    ministry: str
    level: str = "Central"
    category: str
    description: str
    benefits: str
    financial_benefit_amount: float = 0.0
    rules: Dict[str, Any] = Field(default_factory=dict)
    required_documents: List[str] = Field(default_factory=list)
    application_process: List[str] = Field(default_factory=list)
    official_portal_url: str
    helpline: str = ""
    faqs: List[Dict[str, str]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


# -------------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": "Citizen Scheme AI",
        "version": "2.0.0",
        "total_schemes": len(db.get_all_schemes())
    }


@app.get("/api/stats")
def get_stats():
    """Returns knowledge base statistics."""
    schemes = db.get_all_schemes()
    return {
        "total_schemes": len(schemes),
        "total_ministries": len(db.get_ministries()),
        "total_categories": len(db.get_categories()),
        "categories": db.get_categories(),
        "ministries": db.get_ministries()
    }


@app.get("/api/schemes")
def list_schemes(
    category: Optional[str] = Query(None, description="Filter by category"),
    ministry: Optional[str] = Query(None, description="Filter by ministry"),
    search: Optional[str] = Query(None, description="Search query")
):
    """Lists schemes with optional category, ministry, and text search filtering."""
    schemes = db.filter_schemes(
        category=category,
        ministry=ministry,
        search_term=search
    )
    return [s.model_dump() for s in schemes]


@app.get("/api/schemes/{scheme_id}")
def get_scheme(scheme_id: str):
    """Retrieves a specific scheme by ID."""
    clean_id = SecurityGuard.sanitize_filename(scheme_id).lower()
    scheme = db.get_scheme_by_id(clean_id)
    if not scheme:
        # Also try direct lookup in case sanitize altered hyphens
        scheme = db.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' not found."
        )
    return scheme.model_dump()


@app.get("/api/categories")
def get_categories():
    """Returns unique scheme categories."""
    return db.get_categories()


@app.get("/api/ministries")
def get_ministries():
    """Returns unique ministries."""
    return db.get_ministries()


@app.post("/api/eligibility/evaluate")
def evaluate_eligibility(
    profile: CitizenProfile,
    lang: str = Query("en", description="Language code")
):
    """
    Evaluates citizen profile against all registered welfare schemes deterministically.
    Returns sorted audit results with met, unmet, and conditional criteria.
    """
    all_schemes = db.get_all_schemes()
    results = EligibilityEngine.evaluate_all(profile, all_schemes, lang=lang)

    eligible_count = sum(1 for r in results if r.status == "Eligible")
    potential_count = sum(1 for r in results if r.status == "Potentially Eligible")
    ineligible_count = sum(1 for r in results if r.status == "Ineligible")

    return {
        "stats": {
            "total_evaluated": len(results),
            "eligible": eligible_count,
            "potentially_eligible": potential_count,
            "ineligible": ineligible_count
        },
        "results": [r.model_dump() for r in results]
    }


@app.post("/api/eligibility/roadmap")
def generate_roadmap(request: RoadmapRequest):
    """
    Generates a structured, exportable Markdown Action Roadmap for qualified schemes.
    """
    profile = request.profile
    lang = request.lang
    all_schemes = db.get_all_schemes()
    results = EligibilityEngine.evaluate_all(profile, all_schemes, lang=lang)

    roadmap_lines = [
        f"# Citizen Scheme AI - Action Roadmap",
        f"**Generated for**: Age {profile.age} | Gender: {profile.gender} | State: {profile.state}",
        f"**Economic Profile**: Annual Income ₹{profile.annual_income:,.0f} | Occupation: {profile.occupation} | BPL: {profile.has_bpl_card}\n",
        "## Qualified Welfare Schemes Summary\n"
    ]

    qualified_found = False
    for res in results:
        if res.is_eligible or res.status == "Potentially Eligible":
            qualified_found = True
            roadmap_lines.append(f"### {res.scheme_name} [{res.status}]")
            roadmap_lines.append(f"- **Estimated Benefit**: {res.estimated_benefit}")
            if res.met_criteria:
                roadmap_lines.append(f"- **Key Criteria Satisfied**: {', '.join(res.met_criteria[:3])}")
            if res.conditional_criteria:
                roadmap_lines.append(f"- **Verification Needed**: {', '.join(res.conditional_criteria[:2])}")
            if res.required_documents:
                roadmap_lines.append(f"- **Required Documents**: {', '.join(res.required_documents)}")
            roadmap_lines.append(f"- **Official Portal**: {res.official_portal_url}\n")

    if not qualified_found:
        roadmap_lines.append("No fully or potentially eligible schemes were found based on current profile details.\n")

    roadmap_lines.append("---")
    roadmap_lines.append(f"*{get_text('disclaimer_text', lang)}*")

    content = "\n".join(roadmap_lines)
    safe_occ = "".join(c for c in profile.occupation if c.isalnum() or c in ("-", "_"))
    filename = f"CitizenSchemeAI_Action_Roadmap_{safe_occ or 'Citizen'}.md"

    return {
        "filename": filename,
        "content": content
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat_assistant(req: ChatRequest):
    """
    Multilingual Grounded RAG Assistant query endpoint.
    Retrieves verified scheme documents and answers with verifiable citations.
    """
    query, is_safe, flag_reason = SecurityGuard.sanitize_user_query(req.query)
    if not is_safe:
        return ChatResponse(
            query=req.query,
            answer=f"⚠️ {flag_reason}",
            citations=[],
            lang=req.lang
        )

    response = rag_assistant.generate_response(query, lang=req.lang)
    return ChatResponse(
        query=query,
        answer=response.get("answer", ""),
        citations=response.get("citations", []),
        lang=req.lang
    )


@app.post("/api/schemes/compare")
def compare_schemes(req: CompareRequest):
    """
    Compares selected schemes side-by-side and calculates aggregated financial benefits.
    """
    all_schemes = db.get_all_schemes()
    selected_schemes = [s for s in all_schemes if s.id in req.scheme_ids or s.name in req.scheme_ids]

    total_annual_benefit = sum(s.financial_benefit_amount for s in selected_schemes)

    comparison_data = []
    for s in selected_schemes:
        comparison_data.append({
            "id": s.id,
            "name": s.name,
            "native_names": s.native_names,
            "category": s.category,
            "ministry": s.ministry,
            "financial_benefit_amount": s.financial_benefit_amount,
            "benefits": s.benefits,
            "target_beneficiaries": s.rules.target_beneficiaries or "All Eligible Citizens",
            "max_annual_income": s.rules.max_annual_income,
            "required_documents_count": len(s.required_documents),
            "required_documents": s.required_documents,
            "official_portal_url": s.official_portal_url
        })

    return {
        "total_annual_benefit": total_annual_benefit,
        "schemes": comparison_data
    }


@app.post("/api/schemes")
def register_scheme(payload: SchemeCreatePayload):
    """
    Registers a new government welfare scheme into the repository and rebuilds RAG index.
    """
    global rag_retriever, rag_assistant

    safe_id = SecurityGuard.sanitize_filename(payload.id).lower().replace(" ", "-")
    data = payload.model_dump()
    data["id"] = safe_id
    data["name"] = SecurityGuard.sanitize_field(payload.name)
    data["ministry"] = SecurityGuard.sanitize_field(payload.ministry)
    data["description"] = SecurityGuard.sanitize_field(payload.description)
    data["benefits"] = SecurityGuard.sanitize_field(payload.benefits)
    data["official_portal_url"] = SecurityGuard.validate_and_sanitize_url(payload.official_portal_url)

    ok, msg = db.add_scheme(data)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # Rebuild RAG index
    rag_retriever = SchemeRAGRetriever(db)
    rag_assistant = CitizenRAGAssistant(rag_retriever)

    return {
        "success": True,
        "message": msg,
        "scheme_id": safe_id
    }


@app.get("/api/translations")
def get_all_translations():
    """Returns the full translation dictionary for all languages."""
    return TRANSLATIONS


@app.get("/api/translations/{lang}")
def get_language_translations(lang: str):
    """Returns dictionary of translations for a specific language."""
    if lang not in TRANSLATIONS:
        return TRANSLATIONS.get("en", {})
    return TRANSLATIONS[lang]


# -------------------------------------------------------------------------
# Static Files & SPA Routing
# -------------------------------------------------------------------------

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    """Serves the modern Single Page Application."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse(
        "<h1>Citizen Scheme AI Web Portal</h1><p>Static files initializing...</p>"
    )


# Run directly via `python server.py`
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Citizen Scheme AI Modern Web Portal on http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
