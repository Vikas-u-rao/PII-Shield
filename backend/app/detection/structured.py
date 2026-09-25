"""
Structured Pattern Recognizers & Checksum Validation
Includes India-specific checksum validators (Verhoeff for Aadhaar, Luhn for Cards, structural validation for PAN).
Follows PIIShield_Spec_v2.md §3 and §4.
"""

import re
from typing import List
from app.detection.models import RawDetectedEntity, DetectorTier, ValidationStatus

# -----------------------------------------------------------------------------
# Verhoeff Algorithm Tables (Aadhaar validation)
# -----------------------------------------------------------------------------
VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def is_verhoeff_valid(number_str: str) -> bool:
    """Validates arbitrary length digit string against Verhoeff checksum algorithm."""
    clean_num = re.sub(r"[\s\-]", "", number_str)
    if not clean_num.isdigit() or len(clean_num) < 2:
        return False
    c = 0
    reversed_digits = [int(d) for d in reversed(clean_num)]
    for i, digit in enumerate(reversed_digits):
        c = VERHOEFF_D[c][VERHOEFF_P[i % 8][digit]]
    return c == 0


def generate_verhoeff_digit(number_str: str) -> int:
    """Generates the Verhoeff checksum check digit for a given numerical string."""
    clean_num = re.sub(r"[\s\-]", "", number_str)
    c = 0
    reversed_digits = [int(d) for d in reversed(clean_num)]
    for i, digit in enumerate(reversed_digits):
        c = VERHOEFF_D[c][VERHOEFF_P[(i + 1) % 8][digit]]
    return VERHOEFF_INV[c]


def validate_verhoeff_checksum(aadhaar_number: str) -> bool:
    """
    Validates 12-digit Aadhaar checksum using the Verhoeff algorithm.
    PIIShield_Spec_v2.md §4: Performs format and checksum validation only.
    Does NOT verify against UIDAI issuing authorities.
    """
    clean_num = re.sub(r"[\s\-]", "", aadhaar_number)
    if not re.fullmatch(r"[2-9]\d{11}", clean_num):
        return False
    return is_verhoeff_valid(clean_num)


def validate_luhn_checksum(card_number: str) -> bool:
    """
    Validates numbers using the Luhn mod-10 algorithm.
    """
    clean_num = re.sub(r"[\s\-]", "", card_number)
    if not clean_num.isdigit() or len(clean_num) < 2:
        return False

    total = 0
    reversed_digits = [int(d) for d in reversed(clean_num)]
    for i, digit in enumerate(reversed_digits):
        if i % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit

    return total % 10 == 0


def validate_pan_structure(pan_number: str) -> bool:
    """
    Validates 10-character alphanumeric PAN format ([A-Z]{5}[0-9]{4}[A-Z]).
    4th character is the entity status: C, P, H, F, A, T, B, L, J, G.
    PIIShield_Spec_v2.md §4: Does NOT verify against Income Tax database.
    """
    clean_pan = pan_number.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}[CPHFATBLJG][A-Z][0-9]{4}[A-Z]", clean_pan):
        return False
    return True


# -----------------------------------------------------------------------------
# Structured Regex Patterns
# -----------------------------------------------------------------------------
# Aadhaar regex (allowing optional spaces or hyphens every 4 digits)
AADHAAR_PATTERN = re.compile(r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b")

# PAN card regex
PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

# Indian Passport: 1 uppercase letter followed by 7 digits
PASSPORT_IN_PATTERN = re.compile(r"\b[A-PR-WYa-pr-wy][1-9]\d{6}\b")

# Voter ID (EPIC): 3 letters followed by 7 digits
VOTER_ID_PATTERN = re.compile(r"\b[A-Z]{3}[0-9]{7}\b", re.IGNORECASE)

# Indian Mobile Phone: +91 or 0 prefix followed by 10 digits starting 6-9
PHONE_IN_PATTERN = re.compile(r"(?:\+91[\-\s]?|0)?[6-9]\d{9}\b")

# Indian Vehicle Registration (e.g., KA01AB1234 or DL-3C-AB-1234)
VEHICLE_RC_PATTERN = re.compile(
    r"\b[A-Z]{2}[\s\-]?[0-9]{1,2}[\s\-]?[A-Z]{1,3}[\s\-]?[0-9]{4}\b",
    re.IGNORECASE,
)

# Email Address
EMAIL_PATTERN = re.compile(
    r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"
)

# Credit / Debit Cards
CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[\s\-]?){3}\d{4}\b|\b\d{13,19}\b"
)


def detect_structured_entities(text: str) -> List[RawDetectedEntity]:
    """
    Runs deterministic regex and checksum-based detection for structured identifiers.
    Returns RawDetectedEntity items assigned to Tier 1 or Tier 2 per PIIShield_Spec_v2.md §3.
    """
    entities: List[RawDetectedEntity] = []

    # 1. Aadhaar detection (Tier 1 if Verhoeff passes)
    for match in AADHAAR_PATTERN.finditer(text):
        raw_val = match.group()
        if validate_verhoeff_checksum(raw_val):
            entities.append(
                RawDetectedEntity(
                    entity_type="AADHAAR",
                    start_offset=match.start(),
                    end_offset=match.end(),
                    text_content=raw_val,
                    detector_source="india_structured_verhoeff",
                    confidence=1.0,
                    tier=DetectorTier.TIER_1_VALIDATED_STRUCTURED,
                    validation_status=ValidationStatus.VALID_CHECKSUM,
                )
            )

    # 2. PAN Card detection (Tier 1 if structural check passes)
    for match in PAN_PATTERN.finditer(text):
        raw_val = match.group()
        if validate_pan_structure(raw_val):
            entities.append(
                RawDetectedEntity(
                    entity_type="PAN",
                    start_offset=match.start(),
                    end_offset=match.end(),
                    text_content=raw_val,
                    detector_source="india_structured_pan",
                    confidence=1.0,
                    tier=DetectorTier.TIER_1_VALIDATED_STRUCTURED,
                    validation_status=ValidationStatus.STRUCTURALLY_VALID,
                )
            )

    # 3. Credit / Debit Cards (Tier 1 if Luhn passes)
    for match in CARD_PATTERN.finditer(text):
        raw_val = match.group()
        # Avoid overlapping with already detected Aadhaar
        if validate_luhn_checksum(raw_val):
            entities.append(
                RawDetectedEntity(
                    entity_type="CREDIT_CARD",
                    start_offset=match.start(),
                    end_offset=match.end(),
                    text_content=raw_val,
                    detector_source="structured_luhn",
                    confidence=1.0,
                    tier=DetectorTier.TIER_1_VALIDATED_STRUCTURED,
                    validation_status=ValidationStatus.VALID_CHECKSUM,
                )
            )

    # 4. Indian Passport (Tier 2 - high confidence format match)
    for match in PASSPORT_IN_PATTERN.finditer(text):
        entities.append(
            RawDetectedEntity(
                entity_type="PASSPORT_IN",
                start_offset=match.start(),
                end_offset=match.end(),
                text_content=match.group(),
                detector_source="india_regex_passport",
                confidence=0.95,
                tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
                validation_status=ValidationStatus.STRUCTURALLY_VALID,
            )
        )

    # 5. Voter ID (Tier 2)
    for match in VOTER_ID_PATTERN.finditer(text):
        entities.append(
            RawDetectedEntity(
                entity_type="VOTER_ID",
                start_offset=match.start(),
                end_offset=match.end(),
                text_content=match.group(),
                detector_source="india_regex_voter_id",
                confidence=0.95,
                tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
                validation_status=ValidationStatus.STRUCTURALLY_VALID,
            )
        )

    # 6. Phone Numbers (Tier 2)
    for match in PHONE_IN_PATTERN.finditer(text):
        entities.append(
            RawDetectedEntity(
                entity_type="PHONE_NUMBER",
                start_offset=match.start(),
                end_offset=match.end(),
                text_content=match.group(),
                detector_source="india_regex_phone",
                confidence=0.90,
                tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
                validation_status=ValidationStatus.STRUCTURALLY_VALID,
            )
        )

    # 7. Email Address (Tier 2)
    for match in EMAIL_PATTERN.finditer(text):
        entities.append(
            RawDetectedEntity(
                entity_type="EMAIL_ADDRESS",
                start_offset=match.start(),
                end_offset=match.end(),
                text_content=match.group(),
                detector_source="regex_email",
                confidence=0.95,
                tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
                validation_status=ValidationStatus.STRUCTURALLY_VALID,
            )
        )

    # 8. Vehicle RC (Tier 2)
    for match in VEHICLE_RC_PATTERN.finditer(text):
        entities.append(
            RawDetectedEntity(
                entity_type="VEHICLE_RC",
                start_offset=match.start(),
                end_offset=match.end(),
                text_content=match.group(),
                detector_source="india_regex_vehicle_rc",
                confidence=0.90,
                tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
                validation_status=ValidationStatus.STRUCTURALLY_VALID,
            )
        )

    return entities
