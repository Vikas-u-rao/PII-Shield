"""
Policy Engine
Evaluates policy actions per detected entity under versioned rules with deny-by-default behavior.
Follows PIIShield_Spec_v2.md §2.
"""

import os
import yaml
from typing import Dict, Optional
from app.detection.models import RawDetectedEntity
from app.policy.models import PolicyConfig, PolicyAction


class PolicyEngine:
    """Evaluates privacy policy decisions against consolidated entities."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to rules.yaml in current package directory
            base_dir = os.path.dirname(__file__)
            config_path = os.path.join(base_dir, "rules.yaml")

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> PolicyConfig:
        """Loads and parses policy rules. Falls back to strict deny-all on failure."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return PolicyConfig(**data)
        except Exception:
            pass

        # Strict deny-by-default fallback config
        return PolicyConfig(
            version_tag="fallback-deny-all",
            description="Emergency deny-by-default policy",
            default_action=PolicyAction.BLOCK,
            entity_rules={},
        )

    def evaluate(self, entity: RawDetectedEntity) -> PolicyAction:
        """
        Determines policy action (BLOCK, MASK, PSEUDONYMIZE, ALLOW) for an entity.
        Fails closed (BLOCK) if rule is missing or policy evaluation errors (PIIShield_Spec_v2.md §2).
        """
        try:
            action = self.config.entity_rules.get(
                entity.entity_type, self.config.default_action
            )
            if isinstance(action, str):
                return PolicyAction(action)
            return action
        except Exception:
            # Strict fail closed
            return PolicyAction.BLOCK
