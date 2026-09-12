"""
Consolidation & Deterministic Precedence Logic
Implements overlap resolution according to PIIShield.md §3:
1. Higher tier wins.
2. Within tier, longer span wins.
3. Within tier and equal span, higher confidence wins.
4. Genuine same-tier type conflicts consult ChromaDB (or fallback to more restrictive policy).
"""

from typing import List
from app.detection.models import RawDetectedEntity


def consolidate_entities(entities: List[RawDetectedEntity]) -> List[RawDetectedEntity]:
    """
    Consolidates overlapping detected entities using deterministic precedence rules.
    Fails closed if consolidation fails (PIIShield.md §2).
    """
    # TODO: Implement overlap detection, tier precedence, and ChromaDB tie-breaking
    raise NotImplementedError("Entity consolidation is not yet implemented.")
