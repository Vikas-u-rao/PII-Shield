"""
Reversible Pseudonymization & Masking
Transforms text using reserved namespace tokens (e.g. ⟦PII_PERSON_01⟧) (PIIShield.md §6).
"""

from typing import List, Tuple
from app.detection.models import RawDetectedEntity
from app.policy.models import PolicyAction


class Pseudonymizer:
    """Manages reversible token substitution and irreversible masking."""

    def __init__(self, session_id: str):
        self.session_id = session_id

    def transform(
        self,
        original_text: str,
        entities_with_actions: List[Tuple[RawDetectedEntity, PolicyAction]]
    ) -> str:
        """
        Applies masking and pseudonymization in reverse offset order on original text.
        Persists encrypted mapping to session lookup table.
        Fails closed on any transformation failure.
        """
        # TODO: Implement token assignment and text replacement
        raise NotImplementedError("Pseudonymization transformation is not yet implemented.")
