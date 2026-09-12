"""
ChromaDB Disambiguation Client
Used strictly inline to resolve genuine same-tier conflicts against offline synthetic exemplars.
Never ingests live traffic or raw PII (PIIShield.md §3, §8, §20, §24).
"""

from typing import List, Optional
from app.detection.models import RawDetectedEntity


class ChromaDisambiguationClient:
    """Client for querying offline exemplar vectors for ambiguous entity types."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        # TODO: Initialize ChromaDB HTTP client connection

    def resolve_tie(
        self, candidate_a: RawDetectedEntity, candidate_b: RawDetectedEntity, context_text: str
    ) -> Optional[RawDetectedEntity]:
        """
        Queries nearest synthetic exemplar neighbors to break type tie between two candidates.
        Returns the winning candidate, or None if ChromaDB query fails or is unavailable.
        """
        # TODO: Query synthetic exemplar collection and return winning candidate
        raise NotImplementedError("ChromaDB disambiguation client is not yet implemented.")
