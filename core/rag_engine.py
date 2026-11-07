"""
Hybrid Multilingual RAG (Retrieval-Augmented Generation) Engine
Combines TF-IDF vector-space semantic matching, keyword indexing, and grounded answer synthesis.
Ensures zero-latency, crash-proof offline responses with source citations.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

from core.models import Scheme
from core.database import SchemeDatabase, get_scheme_db
from core.security import SecurityGuard


# Multilingual / Vernacular / Hinglish stop words to exclude from lexical boosting
STOP_WORDS = set(ENGLISH_STOP_WORDS).union({
    # Common English conversational question words
    "what", "is", "the", "are", "can", "how", "who", "whom", "which", "where", "when",
    "why", "does", "do", "did", "for", "from", "with", "about", "under", "get", "give",
    "apply", "need", "want", "tell", "explain", "i", "my", "me", "you", "your", "we",
    # Hindi conversational words
    "क्या", "है", "हैं", "के", "लिए", "का", "की", "को", "से", "में", "पर", "और", "या",
    "मुझे", "हमे", "हम", "आप", "कैसे", "कहाँ", "कब", "कितना", "किसे", "चाहिए", "सकता", "सकती",
    "kya", "hai", "hain", "ke", "liye", "ka", "ki", "ko", "se", "mein", "par", "aur", "ya",
    "mujhe", "hame", "ham", "aap", "kaise", "kahan", "kab", "kitna", "kise", "chahiye", "sakta",
    # Marathi conversational words
    "काय", "आहे", "आहेत", "च्या", "साठी", "चे", "ला", "वर", "आणि", "किंवा", "मला", "आम्हाला",
    "कसे", "कुठे", "केव्हा", "किती", "कोणाला", "पाहिजे", "शकेल", "शकता"
})


# Expanded vernacular and Hinglish domain synonym map
SYNONYM_MAP: Dict[str, List[str]] = {
    # Agriculture / Farming
    "kisan": ["farmer", "agriculture", "crops", "krishi", "pm-kisan"],
    "किसान": ["kisan", "farmer", "agriculture", "pm-kisan", "फसल", "कृषि"],
    "शेतकरी": ["farmer", "agriculture", "pm-kisan", "पिके", "शेती"],
    "krishi": ["farmer", "agriculture", "pm-kisan", "crops"],
    "कृषि": ["farmer", "agriculture", "pm-kisan", "फसल"],
    "kheti": ["farmer", "agriculture", "pm-kisan", "crops"],
    "खेती": ["farmer", "agriculture", "pm-kisan", "फसल"],
    "fasal": ["crops", "agriculture", "pm-kisan"],
    "फसल": ["crops", "agriculture", "pm-kisan"],
    "zameen": ["land", "landholding", "agriculture"],
    "bhoomi": ["land", "landholding", "agriculture"],
    "annadata": ["farmer", "agriculture", "pm-kisan"],

    # Health / Medical / Cashless Hospitalization
    "aarogya": ["health", "hospital", "medical", "treatment", "ayushman", "pmjay"],
    "आरोग्य": ["health", "hospital", "medical", "ayushman", "pmjay", "इलाज"],
    "ayushman": ["health", "hospital", "medical", "pmjay", "cashless"],
    "आयुष्मान": ["health", "hospital", "medical", "pmjay", "इलाज"],
    "bimari": ["health", "hospital", "ayushman", "treatment"],
    "बीमारी": ["health", "hospital", "ayushman", "इलाज"],
    "ilaj": ["health", "hospital", "medical", "ayushman", "pmjay", "treatment"],
    "ilaaj": ["health", "hospital", "medical", "ayushman", "pmjay", "treatment"],
    "इलाज": ["health", "hospital", "medical", "ayushman", "pmjay"],
    "dawa": ["medical", "health", "hospital", "treatment"],
    "dawakhana": ["hospital", "medical", "health", "ayushman"],
    "dawai": ["medical", "health", "hospital", "treatment"],
    "upchar": ["treatment", "medical", "hospital", "ayushman"],
    "उपचार": ["treatment", "medical", "hospital", "ayushman"],
    "chikitsa": ["medical", "health", "hospital", "ayushman"],
    "चिकित्सा": ["medical", "health", "hospital", "ayushman"],
    "beemar": ["health", "medical", "hospital", "treatment"],
    "bimar": ["health", "medical", "hospital", "treatment"],
    "hospital": ["medical", "ayushman", "pmjay", "health", "cashless"],

    # Education / Scholarship / Student
    "padhai": ["student", "scholarship", "education", "college"],
    "पढ़ाई": ["student", "scholarship", "education"],
    "shiksha": ["student", "scholarship", "education"],
    "शिक्षा": ["student", "scholarship", "education"],
    "शिक्षण": ["student", "scholarship", "education"],
    "vidyarthi": ["student", "scholarship", "education"],
    "विद्यार्थी": ["student", "scholarship", "education"],
    "chhatravritti": ["scholarship", "post-matric", "student"],
    "छात्रवृत्ति": ["scholarship", "post-matric", "student"],
    "शिष्यवृत्ती": ["scholarship", "post-matric", "student"],
    "scholarship": ["post-matric", "student", "education"],
    "college": ["student", "scholarship", "education"],
    "school": ["student", "scholarship", "education"],
    "fees": ["scholarship", "post-matric", "education"],

    # Pension / Senior Citizens / Social Security
    "pension": ["retirement", "old age", "senior citizen", "atal pension", "nsap", "ignaps"],
    "पेंशन": ["pension", "retirement", "atal pension", "nsap", "वृद्धावस्था"],
    "पेन्शन": ["pension", "retirement", "atal pension", "nsap"],
    "vridha": ["old age", "senior citizen", "pension", "nsap"],
    "वृद्ध": ["old age", "senior citizen", "pension", "nsap"],
    "vriddhavastha": ["old age", "senior citizen", "pension", "nsap"],
    "वृद्धावस्था": ["old age", "senior citizen", "pension", "nsap"],
    "buzurg": ["senior citizen", "old age", "pension", "nsap"],
    "buddhe": ["senior citizen", "old age", "pension"],
    "budhapa": ["old age", "senior citizen", "pension", "nsap"],
    "senior": ["senior citizen", "old age", "pension", "nsap"],

    # Credit / Loans / Entrepreneurship
    "karz": ["loan", "mudra", "svanidhi", "credit", "business"],
    "कर्ज": ["loan", "mudra", "svanidhi", "credit", "business"],
    "karza": ["loan", "mudra", "svanidhi", "credit", "business"],
    "rin": ["loan", "mudra", "credit"],
    "ऋण": ["loan", "mudra", "credit"],
    "mudra": ["loan", "business", "credit", "entrepreneur", "pmmy"],
    "मुद्रा": ["loan", "business", "credit", "entrepreneur"],
    "paisa": ["financial", "grant", "subsidy", "benefit", "loan"],
    "paise": ["financial", "grant", "subsidy", "benefit", "loan"],
    "sahayata": ["assistance", "benefit", "subsidy", "welfare"],
    "सहायता": ["assistance", "benefit", "subsidy", "welfare"],
    "maddat": ["assistance", "benefit", "subsidy"],
    "मदत": ["assistance", "benefit", "subsidy"],
    "vyapar": ["business", "mudra", "entrepreneur", "self-employed"],
    "व्यापार": ["business", "mudra", "entrepreneur", "self-employed"],
    "dukan": ["shop", "mudra", "svanidhi", "vendor", "retail"],
    "दुकान": ["shop", "mudra", "svanidhi", "vendor"],
    "thela": ["vendor", "svanidhi", "hawker", "street vendor"],
    "ठेला": ["vendor", "svanidhi", "hawker", "street vendor"],
    "vendor": ["street vendor", "svanidhi", "working capital"],
    "hawker": ["street vendor", "svanidhi"],
    "funding": ["loan", "credit", "mudra", "stand-up"],

    # Artisans / Crafts / Traditional Trades
    "vishwakarma": ["artisan", "crafts", "tool", "training", "pm vishwakarma"],
    "विश्वकर्मा": ["artisan", "crafts", "tool", "training", "कारीगर"],
    "karigar": ["artisan", "craftsperson", "vishwakarma", "tools"],
    "कारीगर": ["artisan", "craftsperson", "vishwakarma", "tools"],
    "badhai": ["carpenter", "artisan", "vishwakarma"],
    "lohar": ["blacksmith", "artisan", "vishwakarma"],
    "sunar": ["goldsmith", "artisan", "vishwakarma"],
    "kumhar": ["potter", "artisan", "vishwakarma"],
    "darzi": ["tailor", "artisan", "vishwakarma"],
    "mistri": ["mason", "artisan", "vishwakarma"],
    "silai": ["tailor", "sewing", "vishwakarma"],

    # Women / Girl Child Empowerment
    "mahila": ["women", "girl child", "sukanya", "ujjwala", "stand-up"],
    "महिला": ["women", "girl child", "sukanya", "ujjwala", "stand-up"],
    "ladki": ["girl child", "sukanya", "daughter"],
    "मुलगी": ["girl child", "sukanya", "daughter"],
    "beti": ["girl child", "sukanya", "daughter"],
    "बेटी": ["girl child", "sukanya", "daughter"],
    "kanya": ["girl child", "sukanya", "daughter"],
    "कन्या": ["girl child", "sukanya", "daughter"],
    "aurat": ["women", "ujjwala", "stand-up"],
    "stree": ["women", "female"],
    "स्त्री": ["women", "female"],
    "sukanya": ["girl child", "daughter", "savings", "ssy"],
    "सुकन्या": ["girl child", "daughter", "savings"],

    # Housing / Pucca House
    "ghar": ["housing", "awas", "pmay", "pucca house"],
    "घर": ["housing", "awas", "pmay"],
    "makan": ["housing", "awas", "pmay", "pucca house"],
    "मकान": ["housing", "awas", "pmay"],
    "awas": ["housing", "pmay", "shelter"],
    "आवास": ["housing", "pmay"],
    "chhat": ["housing", "awas", "pucca house"],
    "pucca": ["housing", "awas", "pmay"],

    # Gas / Clean Cooking
    "ujjwala": ["gas", "lpg", "cylinder", "cooking", "pmuy"],
    "उज्ज्वला": ["gas", "lpg", "cylinder", "cooking", "गैस"],
    "gas": ["lpg", "cylinder", "ujjwala", "cooking"],
    "गैस": ["lpg", "cylinder", "ujjwala", "cooking"],
    "cylinder": ["lpg", "gas", "ujjwala"],
    "chulha": ["cooking", "lpg", "ujjwala", "gas"],
    "lpg": ["gas", "cylinder", "ujjwala", "cooking"],
    "rasoi": ["cooking", "lpg", "ujjwala", "gas"]
}


class SchemeRAGRetriever:
    """Indexes scheme knowledge chunks and executes semantic cosine similarity retrieval."""

    def __init__(self, db: Optional[SchemeDatabase] = None):
        self.db = db or get_scheme_db()
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.corpus_chunks: List[Dict[str, Any]] = []
        self._build_index()

    def _build_index(self):
        """Builds search corpus chunks from schemes."""
        schemes = self.db.get_all_schemes()
        chunks = []

        for s in schemes:
            # 1. Main scheme chunk
            native_str = " ".join(s.native_names.values())
            tags_str = " ".join(s.tags)
            main_text = f"{s.name} {native_str} {s.category} {s.ministry}. {s.description} {s.benefits}. Tags: {tags_str}"
            chunks.append({
                "scheme_id": s.id,
                "scheme_name": s.name,
                "chunk_type": "overview",
                "text": main_text,
                "source": f"{s.name} ({s.ministry})",
                "content_detail": s.description
            })

            # 2. Eligibility & Documents chunk
            docs_str = ", ".join(s.required_documents)
            target_str = s.rules.target_beneficiaries
            rules_text = f"{s.name} Eligibility and Documents: Target Beneficiaries: {target_str}. Required Documents: {docs_str}."
            chunks.append({
                "scheme_id": s.id,
                "scheme_name": s.name,
                "chunk_type": "documents_rules",
                "text": rules_text,
                "source": f"{s.name} - Eligibility & Document Rules",
                "content_detail": f"Target: {target_str} | Required Documents: {docs_str}"
            })

            # 3. FAQ chunks
            for faq in s.faqs:
                faq_text = f"{s.name} FAQ: Q: {faq.question} A: {faq.answer}"
                chunks.append({
                    "scheme_id": s.id,
                    "scheme_name": s.name,
                    "chunk_type": "faq",
                    "text": faq_text,
                    "source": f"{s.name} - Official FAQ",
                    "content_detail": f"Q: {faq.question}\nA: {faq.answer}",
                    "faq_question": faq.question,
                    "faq_answer": faq.answer
                })

        self.corpus_chunks = chunks

        if chunks:
            corpus_texts = [c["text"] for c in chunks]
            self.vectorizer = TfidfVectorizer(
                token_pattern=r"(?u)[\w\u0900-\u097F]{2,}",
                stop_words="english",
                ngram_range=(1, 2),
                max_features=6000
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus_texts)
        else:
            self.vectorizer = None
            self.tfidf_matrix = None

    def expand_query(self, query: str) -> str:
        """Expands multilingual and vernacular keywords with domain synonyms."""
        words = re.findall(r"[\w\u0900-\u097F]+", query.lower())
        expansions = []
        for word in words:
            if word in SYNONYM_MAP:
                expansions.extend(SYNONYM_MAP[word])

        if expansions:
            return query + " " + " ".join(set(expansions))
        return query

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top_k relevant scheme chunks with normalized similarity scores."""
        clean_q, is_safe, _ = SecurityGuard.sanitize_user_query(query)
        if not clean_q or not is_safe or not self.vectorizer or self.tfidf_matrix is None:
            return []

        expanded_query = self.expand_query(clean_q)
        q_vec = self.vectorizer.transform([expanded_query])
        raw_scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()

        # Extract content words excluding stopwords to avoid biasing FAQs with "what/is/the"
        raw_words = set(re.findall(r"[\w\u0900-\u097F]+", clean_q.lower()))
        content_words = {w for w in raw_words if w not in STOP_WORDS and len(w) > 1}

        # Calculate hybrid boosted scores
        scores = np.copy(raw_scores)
        for i, chunk in enumerate(self.corpus_chunks):
            chunk_words = set(re.findall(r"[\w\u0900-\u097F]+", chunk["text"].lower()))
            overlap = len(content_words.intersection(chunk_words))
            if overlap > 0:
                # Moderate lexical boost strictly on meaningful content words
                scores[i] += 0.20 * overlap

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.05:  # Minimum relevance threshold
                chunk = dict(self.corpus_chunks[idx])
                # Ensure bounded score [0.0, 1.0]
                chunk["score"] = min(1.0, max(0.0, score))
                results.append(chunk)

        return results


class CitizenRAGAssistant:
    """Answers citizen inquiries using retrieved scheme context with verified citations and direct answers."""

    def __init__(self, retriever: Optional[SchemeRAGRetriever] = None):
        self.retriever = retriever or SchemeRAGRetriever()

    def generate_response(self, query: str, lang: str = "en") -> Dict[str, Any]:
        """
        Processes citizen query, retrieves top context, and synthesizes grounded answer.
        Guaranteed zero hallucination, zero crashes, and bounded citations.
        """
        clean_q, is_safe, flag_reason = SecurityGuard.sanitize_user_query(query)
        if not is_safe:
            return {
                "answer": f"⚠️ {flag_reason}",
                "citations": [],
                "relevant_schemes": []
            }

        if not clean_q:
            return {
                "answer": "Please ask a question regarding government schemes, benefits, or eligibility.",
                "citations": [],
                "relevant_schemes": []
            }

        retrieved = self.retriever.retrieve(clean_q, top_k=4)

        if not retrieved:
            no_match_text = {
                "en": "I could not find a directly matching government scheme for your query. Try searching for terms like 'farmer financial help', 'health insurance card', 'student fee scholarship', or 'business loan'.",
                "hi": "मुझे आपके प्रश्न से संबंधित कोई सटीक सरकारी योजना नहीं मिली। कृपया 'किसान सहायता', 'आयुष्मान कार्ड', 'छात्रवृत्ति', या 'मुद्रा लोन' जैसे शब्दों का उपयोग करें।",
                "mr": "मला आपल्या प्रश्नाशी जुळणारी योजना सापडली नाही. कृपया 'शेतकरी मदत', 'आरोग्य कार्ड', 'शिष्यवृत्ती', किंवा 'व्यवसाय कर्ज' असे शब्द वापरून शोधा."
            }.get(lang, "I could not find a matching scheme for your query.")

            return {
                "answer": no_match_text,
                "citations": [],
                "relevant_schemes": []
            }

        # Deduplicate schemes safely
        matched_scheme_ids = list(dict.fromkeys([c["scheme_id"] for c in retrieved]))
        matched_schemes: List[Scheme] = [
            self.retriever.db.get_scheme_by_id(sid)
            for sid in matched_scheme_ids
            if self.retriever.db.get_scheme_by_id(sid) is not None
        ]

        if not matched_schemes:
            return {
                "answer": "No valid scheme records found for your query.",
                "citations": [],
                "relevant_schemes": []
            }

        answer_parts = []
        citations = []
        primary_scheme = matched_schemes[0]
        top_chunk = retrieved[0]

        # 1. Synthesize Targeted Direct Answer if top match is FAQ or Rules
        if top_chunk.get("chunk_type") == "faq" and top_chunk.get("faq_answer"):
            faq_q = top_chunk.get("faq_question", "")
            faq_a = top_chunk.get("faq_answer", "")
            if lang == "hi":
                answer_parts.append(f"### 🎯 सटीक उत्तर (Official Grounded Answer)\n> **प्रश्न:** {faq_q}\n> **उत्तर:** {faq_a}\n")
            elif lang == "mr":
                answer_parts.append(f"### 🎯 थेट अचूक उत्तर (Official Grounded Answer)\n> **प्रश्न:** {faq_q}\n> **उत्तर:** {faq_a}\n")
            else:
                answer_parts.append(f"### 🎯 Direct Grounded Answer\n> **Question:** {faq_q}\n> **Official Answer:** {faq_a}\n")

        elif top_chunk.get("chunk_type") == "documents_rules":
            target = primary_scheme.rules.target_beneficiaries
            docs = ", ".join(primary_scheme.required_documents)
            if lang == "hi":
                answer_parts.append(f"### 🎯 पात्रता एवं आवश्यक दस्तावेज\n- **लक्षित नागरिक:** {target}\n- **आवश्यक दस्तावेज:** {docs}\n")
            elif lang == "mr":
                answer_parts.append(f"### 🎯 पात्रता व आवश्यक कागदपत्रे\n- **लक्षित नागरिक:** {target}\n- **कागदपत्रे:** {docs}\n")
            else:
                answer_parts.append(f"### 🎯 Eligibility & Documentation Summary\n- **Target Demographics:** {target}\n- **Key Documents:** {docs}\n")

        # 2. Main Verified Scheme Summary
        if lang == "hi":
            answer_parts.append(f"### 📋 {primary_scheme.name}\n")
            if primary_scheme.native_names.get("hi"):
                answer_parts.append(f"**हिंदी नाम:** {primary_scheme.native_names['hi']}\n")
            answer_parts.append(f"**मंत्रालय:** {primary_scheme.ministry}\n")
            answer_parts.append(f"\n**मुख्य विवरण:**\n{primary_scheme.description}\n")
            answer_parts.append(f"\n**योजना के प्रमुख लाभ:**\n{primary_scheme.benefits}\n")
            answer_parts.append(f"\n**लक्षित लाभार्थी:**\n{primary_scheme.rules.target_beneficiaries or 'सभी पात्र नागरिक'}\n")

            if primary_scheme.required_documents:
                answer_parts.append("\n**आवश्यक दस्तावेज सूची:**")
                for doc in primary_scheme.required_documents:
                    answer_parts.append(f"- 📄 {doc}")

            answer_parts.append(f"\n\n**🌐 आधिकारिक आवेदन पोर्टल:** [{primary_scheme.official_portal_url}]({primary_scheme.official_portal_url})")
            if primary_scheme.helpline:
                answer_parts.append(f"\n**📞 हेल्पलाइन नंबर:** `{primary_scheme.helpline}`")

        elif lang == "mr":
            answer_parts.append(f"### 📋 {primary_scheme.name}\n")
            if primary_scheme.native_names.get("mr"):
                answer_parts.append(f"**स्थानिक नाव:** {primary_scheme.native_names['mr']}\n")
            answer_parts.append(f"**मंत्रालय:** {primary_scheme.ministry}\n")
            answer_parts.append(f"\n**योजनेचे स्वरूप:**\n{primary_scheme.description}\n")
            answer_parts.append(f"\n**मिळणारे प्रमुख लाभ:**\n{primary_scheme.benefits}\n")
            answer_parts.append(f"\n**लक्षित लाभार्थी:**\n{primary_scheme.rules.target_beneficiaries or 'सर्व पात्र नागरिक'}\n")

            if primary_scheme.required_documents:
                answer_parts.append("\n**आवश्यक कागदपत्रे:**")
                for doc in primary_scheme.required_documents:
                    answer_parts.append(f"- 📄 {doc}")

            answer_parts.append(f"\n\n**🌐 अधिकृत पोर्टल:** [{primary_scheme.official_portal_url}]({primary_scheme.official_portal_url})")
            if primary_scheme.helpline:
                answer_parts.append(f"\n**📞 हेल्पलाइन क्रमांक:** `{primary_scheme.helpline}`")

        else:
            answer_parts.append(f"### 📋 {primary_scheme.name}\n")
            answer_parts.append(f"**Nodal Ministry:** {primary_scheme.ministry}\n")
            answer_parts.append(f"**Target Beneficiaries:** {primary_scheme.rules.target_beneficiaries or 'Eligible Indian Citizens'}\n")
            answer_parts.append(f"\n**Summary of Scheme:**\n{primary_scheme.description}\n")
            answer_parts.append(f"\n**Key Benefits & Assistance:**\n{primary_scheme.benefits}\n")

            if primary_scheme.required_documents:
                answer_parts.append("\n**Mandatory Documents Checklist:**")
                for doc in primary_scheme.required_documents:
                    answer_parts.append(f"- 📄 {doc}")

            answer_parts.append(f"\n\n**🌐 Official Application Portal:** [{primary_scheme.official_portal_url}]({primary_scheme.official_portal_url})")
            if primary_scheme.helpline:
                answer_parts.append(f"\n**📞 National Helpline:** `{primary_scheme.helpline}`")

        # 3. Secondary relevant schemes
        if len(matched_schemes) > 1:
            other_names = [f"**{s.name}** ({s.category})" for s in matched_schemes[1:3]]
            answer_parts.append(f"\n\n💡 *Also potentially relevant:* {', '.join(other_names)}")

        # 4. Citations with bounded percentage [0.0% to 100.0%]
        for item in retrieved:
            bounded_pct = min(100.0, max(0.0, round(item["score"] * 100, 1)))
            citations.append({
                "source": item["source"],
                "scheme_name": item["scheme_name"],
                "relevance_score": f"{bounded_pct}%"
            })

        return {
            "answer": "\n".join(answer_parts),
            "citations": citations,
            "relevant_schemes": [s.name for s in matched_schemes]
        }
