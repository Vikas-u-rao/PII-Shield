"""
Audit Data Transfer Objects
"""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Tuple


class AuditRecord(BaseModel):
    request_id: str
    session_id: str
    client_id: str
    timestamp: datetime
    direction: str
    entity_type: str
    detector_source: str
    confidence: float
    validation_status: str
    offset_range: Tuple[int, int]
    policy_action: str
    policy_version: str
    response_classification: Optional[str] = None
    latency_ms: Optional[float] = None
    outcome: str
    # STRICT INVARIANT: No raw PII string fields permitted here
