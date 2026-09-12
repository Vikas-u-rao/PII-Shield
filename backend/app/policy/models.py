"""
Policy Data Models & Enumerations
"""

from enum import Enum
from pydantic import BaseModel
from typing import Dict, Optional


class PolicyAction(str, Enum):
    BLOCK = "BLOCK"
    MASK = "MASK"
    PSEUDONYMIZE = "PSEUDONYMIZE"
    ALLOW = "ALLOW"


class PolicyConfig(BaseModel):
    version_tag: str
    description: str
    default_action: PolicyAction = PolicyAction.BLOCK  # Deny-by-default (PIIShield.md §2)
    entity_rules: Dict[str, PolicyAction]
