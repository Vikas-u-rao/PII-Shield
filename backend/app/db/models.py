"""
SQLAlchemy ORM Model Definitions for PIIShield
Maps to database schema defined in PIIShield.md §23.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Client(Base):
    """Registered API clients / tenants."""
    __tablename__ = "clients"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    api_key_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    """Client sessions with TTL tracking."""
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, index=True)
    client_id = Column(String(64), ForeignKey("clients.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_expired = Column(Boolean, default=False)


class Request(Base):
    """Audit record of incoming and outgoing requests (sanitized metadata only)."""
    __tablename__ = "requests"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    client_id = Column(String(64), ForeignKey("clients.id"), nullable=False)
    direction = Column(String(16), nullable=False)  # "inbound" or "outbound"
    timestamp = Column(DateTime, default=datetime.utcnow)
    latency_ms = Column(Float, nullable=True)
    outcome = Column(String(32), nullable=False)  # "FORWARDED", "BLOCKED", "ERROR"


class DetectedEntity(Base):
    """Detected entity metadata. Contains NO raw PII values."""
    __tablename__ = "detected_entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), ForeignKey("requests.id"), nullable=False)
    entity_type = Column(String(64), nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    detector_source = Column(String(64), nullable=False)  # e.g., "india_regex_aadhaar", "presidio_ner_person"
    confidence = Column(Float, nullable=False)
    validation_status = Column(String(32), nullable=False)  # e.g., "VALID_CHECKSUM", "UNVALIDATED"
    value_hash = Column(String(128), nullable=False)  # Salted canonicalized hash


class PolicyVersion(Base):
    """Versioned policy configurations."""
    __tablename__ = "policy_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_tag = Column(String(32), unique=True, nullable=False)
    rules_yaml = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)


class PolicyDecision(Base):
    """Policy action recorded per entity decision."""
    __tablename__ = "policy_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), ForeignKey("requests.id"), nullable=False)
    detected_entity_id = Column(Integer, ForeignKey("detected_entities.id"), nullable=False)
    policy_version_id = Column(Integer, ForeignKey("policy_versions.id"), nullable=False)
    policy_action = Column(String(32), nullable=False)  # "BLOCK", "MASK", "PSEUDONYMIZE", "ALLOW"
    decided_at = Column(DateTime, default=datetime.utcnow)


class Transformation(Base):
    """Tracks transformation from entity instance to pseudonym ID. Contains NO raw value."""
    __tablename__ = "transformations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), ForeignKey("requests.id"), nullable=False)
    pseudonym_token = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PseudonymLookup(Base):
    """
    CRITICAL SECURITY TABLE: Sole persistent storage holding encrypted raw PII.
    Must be isolated in database schema and access controls.
    """
    __tablename__ = "pseudonym_lookup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)  # e.g. "⟦PII_PERSON_01⟧"
    entity_type = Column(String(64), nullable=False)
    encrypted_value = Column(Text, nullable=False)  # Encrypted ciphertext
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class LLMRequest(Base):
    """Sanitized payload sent to third-party LLM."""
    __tablename__ = "llm_requests"

    id = Column(String(64), primary_key=True)
    request_id = Column(String(64), ForeignKey("requests.id"), nullable=False)
    sanitized_prompt = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)


class LLMResponse(Base):
    """Raw response received from third-party LLM before de-pseudonymization."""
    __tablename__ = "llm_responses"

    id = Column(String(64), primary_key=True)
    request_id = Column(String(64), ForeignKey("requests.id"), nullable=False)
    raw_response_text = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)


class SecurityEvent(Base):
    """Security audit logs for violations, unexpected reflections, and leak attempts."""
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), ForeignKey("requests.id"), nullable=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=True)
    event_type = Column(String(64), nullable=False)  # e.g. "unexpected_original_reflection", "unrestorable_token"
    severity = Column(String(16), nullable=False)  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    details_json = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class RiskScore(Base):
    """Optional offline post-session linkage risk analysis results from NetworkX."""
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    co_occurrence_score = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    details_json = Column(Text, nullable=True)
