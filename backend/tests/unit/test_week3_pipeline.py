"""
Unit Tests for PIIShield Core Pipeline (Weeks 1 to 3)
Covers:
- Verhoeff (Aadhaar) & Luhn (Card) algorithms
- PAN structural validation
- Normalizer & offset mapping
- Tier-precedence consolidation
- Policy engine deny-by-default
- Reversible pseudonymization & masking
- De-pseudonymization with Token Integrity Rule
"""

import pytest
from app.detection.structured import (
    is_verhoeff_valid,
    validate_verhoeff_checksum,
    validate_luhn_checksum,
    validate_pan_structure,
    detect_structured_entities,
)
from app.detection.normalizer import normalize_text, map_span_to_original
from app.detection.models import RawDetectedEntity, DetectorTier, ValidationStatus
from app.consolidation.precedence import consolidate_entities
from app.policy.engine import PolicyEngine
from app.policy.models import PolicyAction
from app.anonymization.session_store import EncryptedSessionStore
from app.anonymization.pseudonymizer import (
    Pseudonymizer,
    PIIPolicyBlockedException,
)
from app.response.depseudonymizer import DePseudonymizer


# -----------------------------------------------------------------------------
# 1. India Identifier Checksum & Format Tests (Week 2 Milestone)
# -----------------------------------------------------------------------------
def test_verhoeff_aadhaar_validation():
    # Standard Verhoeff algorithm test vector
    assert is_verhoeff_valid("2363") is True
    assert is_verhoeff_valid("2364") is False

    # 12-digit valid Aadhaar test vector
    assert validate_verhoeff_checksum("2345 6789 0124") is True
    assert validate_verhoeff_checksum("2345-6789-0124") is True
    assert validate_verhoeff_checksum("234567890124") is True
    assert validate_verhoeff_checksum("234567890125") is False  # Invalid checksum

    # Check formatting constraints (cannot start with 0 or 1, must be 12 digits)
    assert validate_verhoeff_checksum("012345678901") is False
    assert validate_verhoeff_checksum("12345") is False
    assert validate_verhoeff_checksum("abcd12345678") is False


def test_luhn_card_validation():
    # Known valid Visa test card numbers
    assert validate_luhn_checksum("49927398716") is True
    assert validate_luhn_checksum("49927398717") is False
    assert validate_luhn_checksum("1234567812345670") is True
    assert validate_luhn_checksum("1234567812345671") is False


def test_pan_structure_validation():
    # Valid PAN format: 5 letters, 4th must be [CPHFATBLJG], 4 digits, 1 letter
    assert validate_pan_structure("ABCDE1234F") is False  # 'E' is not valid 4th char
    assert validate_pan_structure("ABCPE1234F") is True   # 'P' for Individual
    assert validate_pan_structure("XYZCH5678K") is True   # 'C' for Company
    assert validate_pan_structure("abcpe1234f") is True   # Case-insensitive
    assert validate_pan_structure("1234567890") is False  # All digits invalid


def test_detect_structured_entities():
    sample_text = "Reach me at 9876543210 or user@example.com with PAN ABCPE1234F."
    entities = detect_structured_entities(sample_text)
    types = {e.entity_type for e in entities}
    assert "PHONE_NUMBER" in types
    assert "EMAIL_ADDRESS" in types
    assert "PAN" in types


# -----------------------------------------------------------------------------
# 2. Normalizer & Offset Mapping Tests (Week 3 Milestone)
# -----------------------------------------------------------------------------
def test_normalizer_and_offset_mapping():
    raw_text = "Contact   John   at   john@example.com"
    result = normalize_text(raw_text)

    # Whitespace should be collapsed
    assert result.normalized_text == "Contact John at john@example.com"

    # Find "john@example.com" in normalized text
    norm_start = result.normalized_text.index("john@example.com")
    norm_end = norm_start + len("john@example.com")

    # Map back to original text offsets
    orig_start, orig_end = map_span_to_original(norm_start, norm_end, result.offset_map)
    assert raw_text[orig_start:orig_end] == "john@example.com"


# -----------------------------------------------------------------------------
# 3. Consolidation & Tier Precedence Tests (Week 3 Milestone)
# -----------------------------------------------------------------------------
def test_consolidation_tier_precedence():
    # Overlapping span: Tier 1 (Validated Aadhaar) vs Tier 4 (Statistical NER Person)
    tier1_entity = RawDetectedEntity(
        entity_type="AADHAAR",
        start_offset=10,
        end_offset=24,
        text_content="2345 6789 0128",
        detector_source="india_structured_verhoeff",
        confidence=1.0,
        tier=DetectorTier.TIER_1_VALIDATED_STRUCTURED,
        validation_status=ValidationStatus.VALID_CHECKSUM,
    )
    tier4_entity = RawDetectedEntity(
        entity_type="PERSON",
        start_offset=15,
        end_offset=24,
        text_content="6789 0128",
        detector_source="spacy_ner",
        confidence=0.75,
        tier=DetectorTier.TIER_4_NER_ONLY,
    )

    consolidated = consolidate_entities([tier4_entity, tier1_entity])
    assert len(consolidated) == 1
    # Higher tier (Tier 1) MUST win
    assert consolidated[0].entity_type == "AADHAAR"
    assert consolidated[0].tier == DetectorTier.TIER_1_VALIDATED_STRUCTURED


def test_consolidation_longer_span_tie_break():
    # Same tier (Tier 2), overlapping: longer span must win
    short_span = RawDetectedEntity(
        entity_type="PHONE_NUMBER",
        start_offset=0,
        end_offset=10,
        text_content="9876543210",
        detector_source="regex",
        confidence=0.9,
        tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
    )
    long_span = RawDetectedEntity(
        entity_type="PHONE_NUMBER",
        start_offset=0,
        end_offset=14,
        text_content="+91 9876543210",
        detector_source="regex",
        confidence=0.9,
        tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
    )

    consolidated = consolidate_entities([short_span, long_span])
    assert len(consolidated) == 1
    assert consolidated[0].text_content == "+91 9876543210"


# -----------------------------------------------------------------------------
# 4. Policy Engine Deny-by-Default Tests (Week 3 Milestone)
# -----------------------------------------------------------------------------
def test_policy_engine_evaluation():
    engine = PolicyEngine()

    pan_entity = RawDetectedEntity(
        entity_type="PAN",
        start_offset=0,
        end_offset=10,
        text_content="ABCPE1234F",
        detector_source="pan",
        confidence=1.0,
        tier=DetectorTier.TIER_1_VALIDATED_STRUCTURED,
    )
    assert engine.evaluate(pan_entity) == PolicyAction.MASK

    passport_entity = RawDetectedEntity(
        entity_type="PASSPORT_IN",
        start_offset=0,
        end_offset=8,
        text_content="A1234567",
        detector_source="passport",
        confidence=0.95,
        tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
    )
    assert engine.evaluate(passport_entity) == PolicyAction.BLOCK

    # Unknown entity type must trigger deny-by-default (BLOCK)
    unknown_entity = RawDetectedEntity(
        entity_type="UNKNOWN_SECRET_TYPE",
        start_offset=0,
        end_offset=5,
        text_content="12345",
        detector_source="custom",
        confidence=0.5,
        tier=DetectorTier.TIER_3_GENERAL_RECOGNIZER,
    )
    assert engine.evaluate(unknown_entity) == PolicyAction.BLOCK


# -----------------------------------------------------------------------------
# 5. Pseudonymization, Masking & De-pseudonymization Tests (Week 3 Milestone)
# -----------------------------------------------------------------------------
def test_pseudonymization_and_depseudonymization():
    store = EncryptedSessionStore()
    session_id = "test_session_101"
    pseudonymizer = Pseudonymizer(session_id=session_id, session_store=store)

    text = "Hello Alice, your number is 9876543210."
    phone_entity = RawDetectedEntity(
        entity_type="PHONE_NUMBER",
        start_offset=28,
        end_offset=38,
        text_content="9876543210",
        detector_source="regex",
        confidence=0.9,
        tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
    )

    # Transform with PSEUDONYMIZE action
    sanitized_text = pseudonymizer.transform(
        text, [(phone_entity, PolicyAction.PSEUDONYMIZE)]
    )

    # Must contain reserved namespace token format ⟦PII_PHONE_NUMBER_01⟧
    assert "9876543210" not in sanitized_text
    assert "⟦PII_PHONE_NUMBER_01⟧" in sanitized_text

    # Response de-pseudonymization (Token Integrity Rule)
    depseudonymizer = DePseudonymizer(session_id=session_id, session_store=store)
    restored = depseudonymizer.restore_pseudonyms(f"AI response mentioning ⟦PII_PHONE_NUMBER_01⟧.")
    assert "9876543210" in restored

    # Fake placeholder not in session lookup must NOT be restored (Token-integrity invariant)
    fake_token_response = "AI response mentioning ⟦PII_PHONE_NUMBER_99⟧."
    restored_fake = depseudonymizer.restore_pseudonyms(fake_token_response)
    assert "⟦PII_PHONE_NUMBER_99⟧" in restored_fake  # Left unrestored


def test_policy_block_fails_closed():
    store = EncryptedSessionStore()
    pseudonymizer = Pseudonymizer(session_id="blocked_session", session_store=store)

    text = "User passport: A1234567"
    passport_entity = RawDetectedEntity(
        entity_type="PASSPORT_IN",
        start_offset=15,
        end_offset=23,
        text_content="A1234567",
        detector_source="passport",
        confidence=0.95,
        tier=DetectorTier.TIER_2_HIGH_CONF_STRUCTURED,
    )

    # Policy action BLOCK must raise exception and fail closed
    with pytest.raises(PIIPolicyBlockedException):
        pseudonymizer.transform(text, [(passport_entity, PolicyAction.BLOCK)])
