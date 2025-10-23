from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

from ..services.graph_rag_agent import ask_graphrag
from ..services.graph_embeddings import ensure_vector_indexes

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    k: int = 8
    scope: Literal["entity", "document", "hybrid"] = "hybrid"


@router.post("/ask")
def rag_ask(payload: AskRequest):
    try:
        ensure_vector_indexes()
    except Exception:
        # continue; queries may still work if indexes already exist
        pass
    try:
        result = ask_graphrag(payload.question, k=payload.k, scope=payload.scope)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"GraphRAG failed: {exc}")
