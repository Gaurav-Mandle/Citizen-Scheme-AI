"""
Database and Scheme Repository Module for Citizen-Scheme-AI
Loads, caches, validates, queries, and filters government scheme data.
"""

import json
import os
from typing import List, Optional, Dict, Any, Tuple
from core.models import Scheme, SchemeRule, SchemeFAQ
from core.security import SecurityGuard


DEFAULT_SCHEMES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "schemes.json"
)


class SchemeDatabase:
    """In-memory loaded and validated scheme repository."""

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or DEFAULT_SCHEMES_FILE
        self._schemes: Dict[str, Scheme] = {}
        self.load_schemes()

    def load_schemes(self) -> int:
        """Loads schemes from the JSON storage and validates them via Pydantic."""
        if not os.path.exists(self.data_path):
            self._schemes = {}
            return 0

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            loaded = {}
            for item in raw_data:
                try:
                    scheme = Scheme(**item)
                    loaded[scheme.id] = scheme
                except Exception as ex:
                    # Log or skip malformed scheme safely
                    print(f"Warning: Skipping invalid scheme record {item.get('id', 'unknown')}: {ex}")

            self._schemes = loaded
            return len(self._schemes)
        except Exception as ex:
            print(f"Error loading scheme database from {self.data_path}: {ex}")
            self._schemes = {}
            return 0

    def get_all_schemes(self) -> List[Scheme]:
        """Returns all registered schemes."""
        return list(self._schemes.values())

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Scheme]:
        """Fetches a scheme by exact ID."""
        return self._schemes.get(scheme_id)

    def get_categories(self) -> List[str]:
        """Returns a sorted list of unique categories."""
        cats = {s.category for s in self._schemes.values() if s.category}
        return sorted(list(cats))

    def get_ministries(self) -> List[str]:
        """Returns a sorted list of unique ministries."""
        mins = {s.ministry for s in self._schemes.values() if s.ministry}
        return sorted(list(mins))

    def filter_schemes(
        self,
        category: Optional[str] = None,
        ministry: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[Scheme]:
        """Filters schemes based on category, ministry, or search keywords."""
        results = list(self._schemes.values())

        if category and category.lower() not in ("all", "all categories"):
            results = [s for s in results if s.category.lower() == category.lower()]

        if ministry and ministry.lower() not in ("all", "all ministries"):
            results = [s for s in results if s.ministry.lower() == ministry.lower()]

        if search_term:
            clean_term, is_safe, _ = SecurityGuard.sanitize_user_query(search_term)
            if clean_term and is_safe:
                term = clean_term.lower()
                results = [
                    s for s in results
                    if term in s.name.lower()
                    or term in s.description.lower()
                    or term in s.category.lower()
                    or any(term in tag.lower() for tag in s.tags)
                    or any(term in val.lower() for val in s.native_names.values())
                ]

        return results

    def add_scheme(self, scheme_dict: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates and appends a new scheme to the repository and atomically saves to JSON.
        """
        try:
            # Validate and sanitize URL if present
            if "official_portal_url" in scheme_dict:
                scheme_dict["official_portal_url"] = SecurityGuard.validate_and_sanitize_url(
                    scheme_dict["official_portal_url"]
                )

            new_scheme = Scheme(**scheme_dict)
            if new_scheme.id in self._schemes:
                return False, f"Scheme with ID '{new_scheme.id}' already exists."

            self._schemes[new_scheme.id] = new_scheme

            # Save back to disk safely using atomic write
            all_data = [s.model_dump() for s in self._schemes.values()]
            temp_path = f"{self.data_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.data_path)

            return True, f"Successfully registered scheme '{new_scheme.name}'."
        except Exception as ex:
            return False, f"Validation failure: {str(ex)}"


# Global shared instance
_global_db: Optional[SchemeDatabase] = None


def get_scheme_db() -> SchemeDatabase:
    """Singleton getter for scheme database."""
    global _global_db
    if _global_db is None:
        _global_db = SchemeDatabase()
    return _global_db
