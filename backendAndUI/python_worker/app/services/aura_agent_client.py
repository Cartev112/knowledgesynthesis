from __future__ import annotations

import time
import logging
from typing import Any, Dict, Optional

import httpx

from ..core.settings import settings

logger = logging.getLogger(__name__)

_TOKEN_CACHE: Dict[str, Any] = {
    "token": None,
    "expires_at": 0.0,
}


def _get_bearer_token() -> str:
    """Obtain and cache a bearer token using client credentials.
    Requires env: AURA_AGENT_CLIENT_ID, AURA_AGENT_CLIENT_SECRET.
    """
    now = time.time()
    token = _TOKEN_CACHE.get("token")
    if token and now < float(_TOKEN_CACHE.get("expires_at", 0)):
        return token

    if not settings.aura_agent_client_id or not settings.aura_agent_client_secret:
        raise RuntimeError("Aura Agent credentials not configured. Set AURA_AGENT_CLIENT_ID and AURA_AGENT_CLIENT_SECRET.")

    auth = (settings.aura_agent_client_id, settings.aura_agent_client_secret)
    data = {"grant_type": "client_credentials"}

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.neo4j.io/oauth/token", auth=auth, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            resp.raise_for_status()
            payload = resp.json()
            access_token = payload.get("access_token")
            expires_in = int(payload.get("expires_in", 3600))
            if not access_token:
                raise RuntimeError(f"No access_token in response: {payload}")
            _TOKEN_CACHE["token"] = access_token
            _TOKEN_CACHE["expires_at"] = now + max(0, expires_in - 60)  # refresh 60s early
            return access_token
    except Exception as exc:
        logger.error(f"Failed to obtain Aura Agent bearer token: {exc}")
        raise


def invoke_aura_agent(input_text: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Invoke the Neo4j Aura Agent endpoint with the given input.
    By default sends {"input": input_text}. If 'body' is provided, it will be merged.
    """
    if not settings.aura_agent_endpoint_url:
        raise RuntimeError("Aura Agent endpoint not configured. Set AURA_AGENT_ENDPOINT_URL.")

    token = _get_bearer_token()
    payload: Dict[str, Any] = {"input": input_text}
    if body:
        # don't override 'input' unless explicitly provided
        payload.update({k: v for k, v in body.items() if k != "input"})

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(settings.aura_agent_endpoint_url, headers=headers, json=payload)
            
            # Log response details for debugging
            logger.info(f"Aura Agent response status: {resp.status_code}")
            
            if resp.status_code == 500:
                # Neo4j's agent API returned 500 - log details
                try:
                    error_body = resp.json()
                    logger.error(f"Aura Agent 500 error details: {error_body}")
                except:
                    logger.error(f"Aura Agent 500 error body: {resp.text[:500]}")
                raise httpx.HTTPStatusError(
                    f"Aura Agent API returned 500 Internal Server Error. This is a Neo4j service issue. "
                    f"Try again in a few moments or check Neo4j Aura console for agent status.",
                    request=resp.request,
                    response=resp
                )
            
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as http_exc:
        logger.error(f"Aura Agent HTTP error: {http_exc}")
        raise
    except Exception as exc:
        logger.error(f"Aura Agent invocation failed: {type(exc).__name__}: {exc}")
        raise
