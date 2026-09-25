"""
Response De-pseudonymization (Final Pipeline Step)
Restores verified session pseudonyms immediately before returning to client (PIIShield_Spec_v2.md §1, §7).
Strictly enforces token integrity: token must exist in active session lookup table.
"""

import re
from typing import Optional
from app.anonymization.session_store import EncryptedSessionStore
from app.anonymization.pseudonymizer import _GLOBAL_STORE

# Regex to detect reserved namespace placeholder tokens
TOKEN_PATTERN = re.compile(r"⟦PII_[A-Z_]+_\d{2}⟧")


class DePseudonymizer:
    """Restores reserved tokens to real values via session store lookup."""

    def __init__(self, session_id: str, session_store: Optional[EncryptedSessionStore] = None):
        self.session_id = session_id
        self.store = session_store or _GLOBAL_STORE

    def restore_pseudonyms(self, response_text: str) -> str:
        """
        Validates placeholder exact match against active session lookup table.
        Restores raw PII values.
        Fails closed on lookup read failure or expired session (PIIShield_Spec_v2.md §2, §26.3).
        """
        if not response_text:
            return response_text

        def replace_token(match: re.Match) -> str:
            token = match.group(0)
            # Token Integrity Rule (PIIShield_Spec_v2.md §1):
            # Only restore if token exists in the active session's lookup table.
            raw_value = self.store.retrieve_raw_value(self.session_id, token)
            if raw_value is not None:
                return raw_value
            # If not in session lookup, treat as newly generated text, never restore!
            return token

        try:
            return TOKEN_PATTERN.sub(replace_token, response_text)
        except Exception as exc:
            # Fail closed on any restoration failure (§2)
            raise RuntimeError(f"De-pseudonymization failed closed: {str(exc)}") from exc
