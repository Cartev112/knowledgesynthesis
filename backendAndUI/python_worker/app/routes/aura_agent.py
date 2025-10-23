from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from ..core.settings import settings
from ..services.aura_agent_client import invoke_aura_agent

router = APIRouter()


class AgentInvokeRequest(BaseModel):
    input: str
    body: Optional[Dict[str, Any]] = None


@router.post("/invoke")
def agent_invoke(payload: AgentInvokeRequest):
    if not settings.aura_agent_endpoint_url:
        raise HTTPException(status_code=500, detail="AURA_AGENT_ENDPOINT_URL is not configured")
    try:
        result = invoke_aura_agent(payload.input, body=payload.body)
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Aura Agent call failed: {exc}")
