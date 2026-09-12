"""
Live Proxy Gateway Routes
Handles client chat/completion requests through the PIIShield pipeline.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ProxyChatRequest(BaseModel):
    session_id: Optional[str] = None
    messages: List[ChatMessage]
    model: Optional[str] = "default"
    stream: Optional[bool] = False


@router.post("/chat/completions")
async def chat_completions(payload: ProxyChatRequest):
    """
    Main LLM proxy endpoint.
    Pipeline: Detect -> Consolidate -> Policy -> Pseudonymize -> LLM -> Response Scan -> Classify -> De-pseudonymize.
    """
    # TODO: Implement complete fail-closed proxy flow according to PIIShield.md §24
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Proxy gateway pipeline is not yet implemented."
    )
