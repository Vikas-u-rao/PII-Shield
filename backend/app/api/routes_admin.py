"""
Admin & Policy Management Routes
Protected by JWT authentication for configuration and policy updates.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()


class PolicyUpdateRequest(BaseModel):
    version_tag: str
    rules_yaml: str
    description: str


@router.get("/policies")
async def list_policies():
    """List policy versions and active configuration."""
    # TODO: Implement policy retrieval logic from policy_versions table
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Policy management is not yet implemented."
    )


@router.post("/policies")
async def create_policy_version(payload: PolicyUpdateRequest):
    """Publish a new policy version."""
    # TODO: Implement policy version creation and activation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Policy creation is not yet implemented."
    )
