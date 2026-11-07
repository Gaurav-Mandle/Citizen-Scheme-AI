"""
Security and Input Sanitization Module for Citizen-Scheme-AI
Protects against prompt injections, XSS, path traversal, URL exploits, and payload bloat.
"""

import os
import re
import html
from urllib.parse import urlparse
from typing import Tuple, Optional


class SecurityGuard:
    """Security validator and sanitizer for user inputs, URLs, and file paths."""

    # Common prompt injection signatures, jailbreak patterns, and exploit attempts
    PROMPT_INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
        r"(?i)system\s*:\s*you\s+are\s+now",
        r"(?i)act\s+as\s+(an?\s+)?unrestricted",
        r"(?i)jailbreak",
        r"(?i)dan\s+mode",
        r"(?i)developer\s+override",
        r"(?i)(what\s+is|show|tell|print|display|reveal|repeat)\s+(me\s+)?(your\s+)?(internal|secret|system)\s+(prompt|instructions)",
        r"(?i)reveal\s+(your\s+)?(secret|internal|system)\s+(prompt|instructions)",
        r"(?i)(bypass|ignore|override)\s+(the\s+)?(rules|safety|filters|guardrails)",
        r"(?i)disregard\s+(the\s+)?system",
        r"(?i)forget\s+(all\s+)?(prior|previous)\s+(instructions|context)",
        r"(?i)<\s*script[^>]*>",
        r"(?i)<\s*iframe[^>]*>",
        r"(?i)javascript\s*:",
        r"(?i)data\s*:\s*text/html",
        r"(?i)onload\s*=",
        r"(?i)onerror\s*=",
        r"(?i)\beval\s*\(",
        r"(?i)\bexec\s*\(",
        r"(?i)\bos\.system\b",
        r"(?i)\bsubprocess\b",
        r"(?i)base64\s*--decode"
    ]

    MAX_QUERY_LENGTH = 1000
    MAX_PROFILE_TEXT_LENGTH = 200

    WINDOWS_RESERVED_NAMES = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }

    @classmethod
    def sanitize_user_query(cls, text: str) -> Tuple[str, bool, Optional[str]]:
        """
        Sanitizes citizen search query or chat input.
        Returns:
            Tuple[clean_text, is_safe, flag_reason]
        """
        if not text:
            return "", True, None

        # 1. Truncate oversized input to prevent memory bloat / DOS
        if len(text) > cls.MAX_QUERY_LENGTH:
            text = text[:cls.MAX_QUERY_LENGTH]

        # 2. Check for malicious prompt injection patterns
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text):
                return (
                    html.escape(text),
                    False,
                    "Security alert: The query contains an unsupported command or injection pattern."
                )

        # 3. Strip dangerous HTML/script injection tags
        clean_text = re.sub(r"<[^>]*>", "", text)

        # 4. Normalize excessive whitespace
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        return clean_text, True, None

    @classmethod
    def escape_html(cls, text: str) -> str:
        """Escapes raw text for safe interpolation inside HTML blocks."""
        if not text:
            return ""
        return html.escape(str(text))

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitizes a filename to protect against directory traversal and reserved OS names.
        Disallows ../ or ..\\, null bytes, and Windows reserved names.
        """
        if not filename:
            return "scheme_record"

        # Remove null bytes
        filename = filename.replace("\0", "")

        # Take only the base name (strip directory components)
        filename = os.path.basename(filename.replace("\\", "/"))

        # Iteratively remove traversal sequences
        while ".." in filename:
            filename = filename.replace("..", "")

        # Keep only alphanumeric, underscores, hyphens, and dots
        safe_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)

        # Strip leading/trailing dots and underscores
        safe_name = safe_name.strip("._")

        # Check for empty or Windows reserved names
        stem = safe_name.split(".")[0].upper()
        if not safe_name or stem in cls.WINDOWS_RESERVED_NAMES:
            return f"safe_{safe_name}" if safe_name else "scheme_record"

        return safe_name

    @classmethod
    def sanitize_field(cls, field_value: str) -> str:
        """Sanitizes text fields for profiles and scheme metadata."""
        if not field_value:
            return ""
        clean = re.sub(r"<[^>]*>", "", str(field_value))
        clean = clean[:cls.MAX_PROFILE_TEXT_LENGTH]
        return clean.strip()

    @classmethod
    def validate_and_sanitize_url(cls, url: str) -> str:
        """
        Validates that a URL uses safe HTTP or HTTPS protocol and avoids XSS/javascript schemes.
        Falls back to the official National Portal of India on invalid/malicious URLs.
        """
        if not url:
            return "https://india.gov.in"

        url = url.strip()
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return "https://india.gov.in"

        if not parsed.netloc:
            return "https://india.gov.in"

        # Disallow embedded script or tag payloads
        if any(char in url for char in ("<", ">", '"', "'", "\0", "\n", "\r")):
            return "https://india.gov.in"

        return url
