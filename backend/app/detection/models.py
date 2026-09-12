"""
Data Structures & Types for Detection
"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional


class DetectorTier(int, Enum):
    """Hierarchy defined in PIIShield.md §3."""
    TIER_1_VALIDATED_STRUCTURED = 1  # Regex + Checksum passed (e.g. Aadhaar Verhoeff, PAN)
    TIER_2_HIGH_CONF_STRUCTURED = 2  # Regex/Format matched without checksum (e.g. Phone, Email)
    TIER_3_GENERAL_RECOGNIZER = 3    # Presidio pattern recognizer above confidence threshold
    TIER_4_NER_ONLY = 4              # spaCy / Presidio statistical NER


class ValidationStatus(str, Enum):
    VALID_CHECKSUM = "VALID_CHECKSUM"
    INVALID_CHECKSUM = "INVALID_CHECKSUM"
    STRUCTURALLY_VALID = "STRUCTURALLY_VALID"
    UNVALIDATED = "UNVALIDATED"


class RawDetectedEntity(BaseModel):
    """Represents an entity detected by any detector module before consolidation."""
    entity_type: str
    start_offset: int
    end_offset: int
    text_content: str  # Kept in memory strictly for consolidation & hashing; not logged/audited
    detector_source: str
    confidence: float
    tier: DetectorTier
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
