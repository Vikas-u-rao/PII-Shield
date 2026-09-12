"""
Audit Logger
Persists audit records into database fail-closed (PIIShield.md §2).
"""

from app.audit.models import AuditRecord


def log_audit_record(record: AuditRecord) -> None:
    """
    Persists decision and outcome to database.
    Fails closed: if audit cannot be persisted, request is rejected.
    """
    # TODO: Implement database insertion for audit records
    raise NotImplementedError("Audit logger is not yet implemented.")
