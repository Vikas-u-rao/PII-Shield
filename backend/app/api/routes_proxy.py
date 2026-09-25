"""
Live Proxy Gateway Routes
Handles client chat/completion requests through the PIIShield pipeline.
Follows PIIShield_Spec_v2.md §24.
"""

import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.gateway.proxy import GatewayProxy
from app.anonymization.pseudonymizer import PIIPolicyBlockedException

router = APIRouter()
gateway = GatewayProxy()


class ChatMessage(BaseModel):
    role: str
    content: str


class ProxyChatRequest(BaseModel):
    session_id: Optional[str] = None
    client_id: Optional[str] = "default_client"
    messages: List[ChatMessage]
    model: Optional[str] = "default"
    stream: Optional[bool] = False


class ProxyChatResponse(BaseModel):
    session_id: str
    sanitized_messages: List[ChatMessage]
    simulated_response: Optional[str] = None
    outcome: str = "FORWARDED"


@router.post("/chat/completions", response_model=ProxyChatResponse)
async def chat_completions(payload: ProxyChatRequest):
    """
    Main LLM proxy endpoint.
    Pipeline: Normalization -> Multi-tier Detection -> Precedence Consolidation -> Policy -> Pseudonymization.
    """
    session_id = payload.session_id or str(uuid.uuid4())
    client_id = payload.client_id or "default_client"

    sanitized_messages: List[ChatMessage] = []

    try:
        for msg in payload.messages:
            if msg.role == "user":
                sanitized_content = await gateway.process_inbound(
                    session_id=session_id,
                    client_id=client_id,
                    prompt=msg.content,
                )
                sanitized_messages.append(ChatMessage(role=msg.role, content=sanitized_content))
            else:
                sanitized_messages.append(msg)

        # In this milestone, return sanitized messages ready for LLM forwarding
        return ProxyChatResponse(
            session_id=session_id,
            sanitized_messages=sanitized_messages,
            simulated_response="[PIIShield] Prompt sanitized and forwarded successfully.",
            outcome="FORWARDED",
        )

    except PIIPolicyBlockedException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Privacy violation: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway pipeline error: {str(exc)}",
        )
