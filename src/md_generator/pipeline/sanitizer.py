from __future__ import annotations

"""TracebackSanitizer for partial error isolation and diagnostic logging.

Phase 0C Implementation: Redacts sensitive local user paths, credentials,
bearer tokens, and environment secrets before storage in IngestionError.
"""

import re


class TracebackSanitizer:
    """Sanitizes tracebacks to remove sensitive path and credential information."""

    # Path patterns
    _WINDOWS_USER_PATH = re.compile(r"[C-Z]:\\Users\\[^\s\\\/]+", re.IGNORECASE)
    _UNIX_USER_PATH = re.compile(r"/(?:home|Users)/[^\s/]+", re.IGNORECASE)

    # Credential & Token patterns
    _BEARER_TOKEN = re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/=]+", re.IGNORECASE)
    _KEY_VAL_CREDENTIAL = re.compile(
        r"(?i)\b(password|pass|secret|api_key|apikey|token|access_token|aws_secret_access_key|database_url)\b\s*[:=]\s*(?:['\"][^'\"]*['\"]|[^\s'\",;&]+)"
    )

    # Max length constraint
    MAX_TRACEBACK_LENGTH = 4000

    @classmethod
    def sanitize(cls, tb_text: str) -> str:
        """Return sanitized traceback text free of sensitive tokens/paths."""
        if not tb_text:
            return ""

        text = str(tb_text)

        # 1. Redact Bearer tokens
        text = cls._BEARER_TOKEN.sub("Bearer [REDACTED]", text)

        # 2. Redact credentials (key=val patterns)
        text = cls._KEY_VAL_CREDENTIAL.sub(r"\1=[REDACTED]", text)

        # 3. Redact local user home paths
        text = cls._WINDOWS_USER_PATH.sub(r"C:\\Users\\[REDACTED]", text)
        text = cls._UNIX_USER_PATH.sub(r"/home/[REDACTED]", text)

        # 4. Truncate if exceeding max length while preserving head and tail
        if len(text) > cls.MAX_TRACEBACK_LENGTH:
            half = (cls.MAX_TRACEBACK_LENGTH - 50) // 2
            text = text[:half] + "\n... [TRACEBACK TRUNCATED] ...\n" + text[-half:]

        return text
