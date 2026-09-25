"""
Custom Presidio Pattern Recognizers for Indian PII Entities
Provides custom PatternRecognizer instances for Presidio AnalyzerEngine.
Follows PIIShield_Spec_v2.md §3 and §4.
"""

from typing import List

try:
    from presidio_analyzer import Pattern, PatternRecognizer
    HAS_PRESIDIO = True
except ImportError:
    HAS_PRESIDIO = False
    Pattern = None
    PatternRecognizer = object


def get_india_pattern_recognizers() -> List[object]:
    """
    Returns custom PatternRecognizer instances for Indian entities:
    - Aadhaar numbers
    - PAN cards
    - Indian Passport
    - Driving License
    - Voter ID (EPIC)
    - Indian Mobile Phone Numbers (+91/0 prefixes)
    """
    if not HAS_PRESIDIO:
        return []

    recognizers = []

    # 1. Aadhaar Recognizer
    aadhaar_pattern = Pattern(
        name="aadhaar_pattern",
        regex=r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b",
        score=0.85,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="AADHAAR",
            patterns=[aadhaar_pattern],
            context=["aadhaar", "uidai", "aadhaar card", "uid", "adhaar"],
        )
    )

    # 2. PAN Recognizer
    pan_pattern = Pattern(
        name="pan_pattern",
        regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        score=0.90,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="PAN",
            patterns=[pan_pattern],
            context=["pan", "pan card", "income tax", "permanent account number"],
        )
    )

    # 3. Indian Passport Recognizer
    passport_pattern = Pattern(
        name="passport_in_pattern",
        regex=r"\b[A-PR-WYa-pr-wy][1-9]\d{6}\b",
        score=0.85,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="PASSPORT_IN",
            patterns=[passport_pattern],
            context=["passport", "republic of india", "indian passport"],
        )
    )

    # 4. Voter ID (EPIC) Recognizer
    voter_pattern = Pattern(
        name="voter_id_pattern",
        regex=r"\b[A-Z]{3}[0-9]{7}\b",
        score=0.80,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="VOTER_ID",
            patterns=[voter_pattern],
            context=["voter", "epic", "election card", "voter id"],
        )
    )

    # 5. Driving License Recognizer
    dl_pattern = Pattern(
        name="dl_pattern",
        regex=r"\b[A-Z]{2}[0-9]{2}[0-9]{11}\b|\b[A-Z]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{4}[\s\-]?[0-9]{7}\b",
        score=0.80,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="DRIVING_LICENSE",
            patterns=[dl_pattern],
            context=["dl", "driving license", "driving licence", "rto"],
        )
    )

    # 6. Indian Mobile Phone Recognizer
    phone_pattern = Pattern(
        name="phone_in_pattern",
        regex=r"(?:\+91[\-\s]?|0)?[6-9]\d{9}\b",
        score=0.85,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[phone_pattern],
            context=["call", "phone", "mobile", "contact", "whatsapp"],
        )
    )

    return recognizers
