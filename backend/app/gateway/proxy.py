"""
Gateway Proxy Orchestrator
Coordinates request/response lifecycle with fail-closed error boundaries.
Follows PIIShield_Spec_v2.md §2, §5, §6, §7.
"""

import uuid
from typing import List, Tuple
from app.detection.normalizer import normalize_text, map_span_to_original
from app.detection.structured import detect_structured_entities
from app.detection.presidio_pipeline import PresidioPipeline
from app.detection.models import RawDetectedEntity
from app.consolidation.precedence import consolidate_entities
from app.policy.engine import PolicyEngine
from app.policy.models import PolicyAction
from app.anonymization.pseudonymizer import Pseudonymizer, PIIPolicyBlockedException
from app.response.depseudonymizer import DePseudonymizer


class GatewayProxy:
    """Orchestrates end-to-end request protection and response de-pseudonymization."""

    def __init__(self):
        self.presidio = PresidioPipeline()
        self.policy_engine = PolicyEngine()

    async def process_inbound(self, session_id: str, client_id: str, prompt: str) -> str:
        """
        Executes inbound pipeline:
        Normalization -> Detection -> Span Mapping -> Consolidation -> Policy -> Pseudonymization.
        Strictly fails closed on any exception (PIIShield_Spec_v2.md §2).
        """
        if not prompt:
            return prompt

        try:
            # 1. Normalization & Offset Mapping (§5)
            norm_res = normalize_text(prompt)

            # 2. Multi-Tier Detection on Normalized Text
            structured_entities = detect_structured_entities(norm_res.normalized_text)
            presidio_entities = self.presidio.analyze(norm_res.normalized_text)
            all_raw = structured_entities + presidio_entities

            # 3. Project normalized spans back to original offsets
            mapped_entities: List[RawDetectedEntity] = []
            for entity in all_raw:
                orig_start, orig_end = map_span_to_original(
                    entity.start_offset, entity.end_offset, norm_res.offset_map
                )
                mapped_entities.append(
                    RawDetectedEntity(
                        entity_type=entity.entity_type,
                        start_offset=orig_start,
                        end_offset=orig_end,
                        text_content=prompt[orig_start:orig_end],
                        detector_source=entity.detector_source,
                        confidence=entity.confidence,
                        tier=entity.tier,
                        validation_status=entity.validation_status,
                    )
                )

            # 4. Deterministic Tier-Precedence Consolidation (§3)
            consolidated = consolidate_entities(mapped_entities)

            # 5. Policy Engine Evaluation (§2)
            entities_with_actions: List[Tuple[RawDetectedEntity, PolicyAction]] = []
            for entity in consolidated:
                action = self.policy_engine.evaluate(entity)
                entities_with_actions.append((entity, action))

            # 6. Reversible Pseudonymization & Masking (§6)
            pseudonymizer = Pseudonymizer(session_id=session_id)
            transformed_prompt = pseudonymizer.transform(prompt, entities_with_actions)

            return transformed_prompt

        except PIIPolicyBlockedException:
            # Policy blocked: re-raise for API layer to return 403 Forbidden
            raise
        except Exception as exc:
            # Fail closed on any detection or transformation failure (§2)
            raise RuntimeError(f"Gateway inbound fail-closed triggered: {str(exc)}") from exc

    async def process_outbound(self, session_id: str, client_id: str, llm_response_text: str) -> str:
        """
        Executes outbound pipeline:
        Response Scanning -> Classification -> De-pseudonymization.
        Fails closed on any exception (PIIShield_Spec_v2.md §2, §7).
        """
        if not llm_response_text:
            return llm_response_text

        try:
            # Restore verified pseudonyms using Token Integrity Rule (§1, §7)
            depseudonymizer = DePseudonymizer(session_id=session_id)
            restored_text = depseudonymizer.restore_pseudonyms(llm_response_text)
            return restored_text
        except Exception as exc:
            raise RuntimeError(f"Gateway outbound fail-closed triggered: {str(exc)}") from exc
