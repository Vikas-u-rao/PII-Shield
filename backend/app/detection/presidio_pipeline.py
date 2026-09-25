"""
Microsoft Presidio & spaCy NER Pipeline Wrapper
Integrates AnalyzerEngine with customized confidence thresholds and India-specific recognizers.
Follows PIIShield_Spec_v2.md §3.
"""

from typing import List
from app.detection.models import RawDetectedEntity, DetectorTier, ValidationStatus
from app.detection.india_recognizers import get_india_pattern_recognizers

try:
    from presidio_analyzer import AnalyzerEngine
    HAS_PRESIDIO = True
except ImportError:
    HAS_PRESIDIO = False
    AnalyzerEngine = None


class PresidioPipeline:
    """Wraps Presidio AnalyzerEngine with custom India pattern recognizers."""

    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold
        self.analyzer = None

        if HAS_PRESIDIO:
            self.analyzer = AnalyzerEngine()
            # Register Indian recognizers
            for recognizer in get_india_pattern_recognizers():
                self.analyzer.registry.add_recognizer(recognizer)

    def analyze(self, text: str) -> List[RawDetectedEntity]:
        """
        Runs Presidio analysis and converts findings to RawDetectedEntity instances.
        Maps recognizers to Tier 3 (Pattern recognizers) or Tier 4 (Statistical NER).
        """
        if not text:
            return []

        if not self.analyzer:
            # Graceful fallback when Presidio is not yet installed in local environment
            return []

        results = self.analyzer.analyze(
            text=text,
            language="en",
            score_threshold=self.confidence_threshold,
        )

        entities: List[RawDetectedEntity] = []
        for res in results:
            # Map detector source to appropriate Tier per PIIShield_Spec_v2.md §3
            is_ner = "spacy" in str(res.recognition_metadata.get("recognizer_name", "")).lower()
            tier = DetectorTier.TIER_4_NER_ONLY if is_ner else DetectorTier.TIER_3_GENERAL_RECOGNIZER

            entities.append(
                RawDetectedEntity(
                    entity_type=res.entity_type,
                    start_offset=res.start,
                    end_offset=res.end,
                    text_content=text[res.start:res.end],
                    detector_source=res.recognition_metadata.get("recognizer_name", "presidio"),
                    confidence=float(res.score),
                    tier=tier,
                    validation_status=ValidationStatus.UNVALIDATED,
                )
            )

        return entities
