"""
Reversible Pseudonymization & Masking Engine
Transforms text using reserved namespace tokens (e.g. ⟦PII_PERSON_01⟧) (PIIShield_Spec_v2.md §5, §6).
Applies replacements on original text in reverse offset order.
"""

from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta, timezone
import re

from app.detection.models import RawDetectedEntity
from app.policy.models import PolicyAction
from app.anonymization.session_store import EncryptedSessionStore

# Shared default session store singleton if none injected
_GLOBAL_STORE = EncryptedSessionStore()


class PIIPolicyBlockedException(Exception):
    """Raised when an entity violates policy with a BLOCK action."""
    pass


def mask_entity_value(entity_type: str, raw_val: str) -> str:
    """
    Produces irreversible masked representation.
    Preserves last 4 digits for identifiers like Aadhaar or Cards for auditability.
    """
    clean_val = re.sub(r"[\s\-]", "", raw_val)
    if entity_type in ("AADHAAR", "CREDIT_CARD") and len(clean_val) >= 4:
        return f"XXXXXXXX{clean_val[-4:]}"
    elif entity_type == "PAN" and len(clean_val) == 10:
        return f"XXXXX{clean_val[5:9]}X"
    elif entity_type == "PHONE_NUMBER" and len(clean_val) >= 4:
        return f"XXXXXX{clean_val[-4:]}"
    elif entity_type == "EMAIL_ADDRESS" and "@" in raw_val:
        parts = raw_val.split("@")
        return f"***@{parts[1]}"
    return f"[MASKED_{entity_type}]"


class Pseudonymizer:
    """Manages reversible token substitution and irreversible masking."""

    def __init__(
        self,
        session_id: str,
        session_store: Optional[EncryptedSessionStore] = None,
        ttl_minutes: int = 60,
    ):
        self.session_id = session_id
        self.store = session_store or _GLOBAL_STORE
        self.ttl_minutes = ttl_minutes

        # In-session value to token cache for referential consistency
        self._value_to_token: Dict[Tuple[str, str], str] = {}
        self._token_counters: Dict[str, int] = {}

    def _get_or_create_token(self, entity_type: str, raw_value: str) -> str:
        """
        Maintains referential coherence: identical entities in the same session
        receive the exact same pseudonym token.
        Token format uses reserved namespace: ⟦PII_<TYPE>_<INDEX>⟧.
        """
        cache_key = (entity_type, raw_value.strip().lower())
        if cache_key in self._value_to_token:
            return self._value_to_token[cache_key]

        counter = self._token_counters.get(entity_type, 0) + 1
        self._token_counters[entity_type] = counter

        token = f"⟦PII_{entity_type}_{counter:02d}⟧"
        self._value_to_token[cache_key] = token

        # Store in encrypted session store with TTL
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.ttl_minutes)
        self.store.store_mapping(
            session_id=self.session_id,
            token=token,
            entity_type=entity_type,
            raw_value=raw_value,
            expires_at=expires_at,
        )

        return token

    def transform(
        self,
        original_text: str,
        entities_with_actions: List[Tuple[RawDetectedEntity, PolicyAction]],
    ) -> str:
        """
        Applies masking and pseudonymization in reverse offset order on original text.
        Fails closed on any error (PIIShield_Spec_v2.md §2, §5).
        """
        if not original_text or not entities_with_actions:
            return original_text

        try:
            # 1. First pass: check for any BLOCK actions (Strict Fail-Closed)
            for entity, action in entities_with_actions:
                if action == PolicyAction.BLOCK:
                    raise PIIPolicyBlockedException(
                        f"Request blocked by policy due to entity '{entity.entity_type}'."
                    )

            # 2. Sort entities by start_offset DESCENDING (reverse order)
            # Earlier offsets never shift, avoiding running delta bookkeeping.
            sorted_entries = sorted(
                entities_with_actions,
                key=lambda x: x[0].start_offset,
                reverse=True,
            )

            modified_text = original_text

            for entity, action in sorted_entries:
                if action == PolicyAction.ALLOW:
                    continue

                start = entity.start_offset
                end = entity.end_offset
                raw_val = original_text[start:end]

                if action == PolicyAction.MASK:
                    replacement = mask_entity_value(entity.entity_type, raw_val)
                elif action == PolicyAction.PSEUDONYMIZE:
                    replacement = self._get_or_create_token(entity.entity_type, raw_val)
                else:
                    # Unknown action: fail closed by blocking
                    raise PIIPolicyBlockedException(
                        f"Unknown policy action '{action}' for entity '{entity.entity_type}'."
                    )

                # Splice replacement into text
                modified_text = modified_text[:start] + replacement + modified_text[end:]

            return modified_text

        except PIIPolicyBlockedException:
            raise
        except Exception as exc:
            # Fail closed on any transformation failure (§2)
            raise RuntimeError(f"Pseudonymization transformation failed closed: {str(exc)}") from exc
