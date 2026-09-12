"""
Structured Pattern Recognizers & Checksum Validation
Includes India-specific checksum validators (Verhoeff for Aadhaar, structural validation for PAN).
"""

from typing import List
from app.detection.models import RawDetectedEntity


def validate_verhoeff_checksum(aadhaar_number: str) -> bool:
    """
    Validates 12-digit Aadhaar checksum using Verhoeff algorithm.
    Does NOT verify against UIDAI issuing authorities (PIIShield.md §4).
    """
    # TODO: Implement Verhoeff checksum algorithm
    raise NotImplementedError("Verhoeff algorithm is not yet implemented.")


def validate_pan_structure(pan_number: str) -> bool:
    """
    Validates 10-character alphanumeric PAN format ([A-Z]{5}[0-9]{4}[A-Z]).
    Does NOT verify against Income Tax database.
    """
    # TODO: Implement PAN regex/structural check
    raise NotImplementedError("PAN structure validation is not yet implemented.")


def detect_structured_entities(text: str) -> List[RawDetectedEntity]:
    """Runs regex and checksum-based detection for structured identifiers."""
    # TODO: Implement Tier 1 and Tier 2 structured recognizers
    raise NotImplementedError("Structured detection is not yet implemented.")
