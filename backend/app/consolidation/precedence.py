"""
Consolidation & Deterministic Precedence Logic
Implements overlap resolution according to PIIShield_Spec_v2.md §3:
1. Higher tier wins (Tier 1 > Tier 2 > Tier 3 > Tier 4).
2. Within tier, longer span wins.
3. Within tier and equal span, higher confidence wins.
4. Genuine same-tier type conflicts fall back to more restrictive policy action.
Strictly fails closed on any internal error (§2).
"""

from typing import List
from app.detection.models import RawDetectedEntity, DetectorTier

# Policy action restriction ordering for tie-breaking
ACTION_SEVERITY = {
    "BLOCK": 4,
    "PSEUDONYMIZE": 3,
    "MASK": 2,
    "ALLOW": 1,
}

# Conservative default severity mapping for entity types
ENTITY_DEFAULT_SEVERITY = {
    "PASSPORT_IN": 4,
    "CREDIT_CARD": 4,
    "AADHAAR": 3,
    "PAN": 3,
    "VOTER_ID": 3,
    "PHONE_NUMBER": 3,
    "EMAIL_ADDRESS": 3,
    "PERSON": 3,
    "DRIVING_LICENSE": 2,
    "IP_ADDRESS": 2,
    "LOCATION": 1,
    "ORGANIZATION": 1,
}


def overlaps(a: RawDetectedEntity, b: RawDetectedEntity) -> bool:
    """Returns True if span a and span b share any character indices."""
    return max(a.start_offset, b.start_offset) < min(a.end_offset, b.end_offset)


def entity_priority_key(entity: RawDetectedEntity):
    """
    Sorting key for precedence:
    1. Tier: Tier 1 (1) < Tier 2 (2) < Tier 3 (3) < Tier 4 (4) -> lower is higher priority
    2. Span Length: longer span wins -> negative length
    3. Confidence: higher confidence wins -> negative confidence
    4. Type Severity Fallback: higher severity wins -> negative severity
    """
    span_len = entity.end_offset - entity.start_offset
    severity = ENTITY_DEFAULT_SEVERITY.get(entity.entity_type, 2)
    return (
        int(entity.tier.value),
        -span_len,
        -float(entity.confidence),
        -severity,
    )


def consolidate_entities(entities: List[RawDetectedEntity]) -> List[RawDetectedEntity]:
    """
    Consolidates overlapping detected entities using deterministic precedence rules.
    Fails closed (raises exception) if consolidation encounters an unrecoverable error.
    Follows PIIShield_Spec_v2.md §3.
    """
    if not entities:
        return []

    try:
        # Sort all candidates by deterministic priority
        sorted_candidates = sorted(entities, key=entity_priority_key)

        accepted_entities: List[RawDetectedEntity] = []

        for candidate in sorted_candidates:
            # Check if candidate overlaps with any already accepted entity
            has_conflict = False
            for accepted in accepted_entities:
                if overlaps(candidate, accepted):
                    has_conflict = True
                    break

            if not has_conflict:
                accepted_entities.append(candidate)

        # Return consolidated entities ordered by their start offset in the text
        accepted_entities.sort(key=lambda e: (e.start_offset, e.end_offset))
        return accepted_entities

    except Exception as exc:
        # Fail closed on any consolidation error (PIIShield_Spec_v2.md §2)
        raise RuntimeError(f"Consolidation fail-closed triggered: {str(exc)}") from exc
