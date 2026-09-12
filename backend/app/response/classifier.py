"""
Response PII Classification (§1 & §26.1)
Classifies detected entities in LLM responses into operational categories.
"""

from enum import Enum
from typing import List, Optional
from app.detection.models import RawDetectedEntity


class ResponsePIICategory(str, Enum):
    REFLECTED_PSEUDONYM = "reflected_pseudonym"
    REFLECTED_ORIGINAL_ALLOWED = "reflected_original_allowed"
    UNEXPECTED_ORIGINAL_REFLECTION = "unexpected_original_reflection"
    RESPONSE_GENERATED = "response_generated"
    RESPONSE_GENERATED_HALLUCINATED = "response_generated_hallucinated"
    UNRESTORABLE_TOKEN = "unrestorable_token"


def canonicalize_for_comparison(entity_type: str, value: str) -> str:
    """
    Applies type-specific canonicalization before hashing for comparison (PIIShield.md §26.1).
    Does NOT affect offsets or transformation.
    """
    # TODO: Implement type-specific canonicalization (phone digits only, email lowercase, etc.)
    raise NotImplementedError("Canonicalization for comparison is not yet implemented.")


class ResponseClassifier:
    """Classifies detected entities in LLM responses."""

    def __init__(self, session_id: str):
        self.session_id = session_id

    def classify_entity(
        self, entity: RawDetectedEntity, request_entity_hashes: List[str], active_tokens: List[str]
    ) -> ResponsePIICategory:
        """
        Classifies response entity into one of the 5 operational categories or unrestorable token.
        """
        # TODO: Implement classification decision tree
        raise NotImplementedError("Response classification is not yet implemented.")
