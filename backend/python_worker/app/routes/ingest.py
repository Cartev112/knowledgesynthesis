from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from ..services.preprocess import extract_text_from_path, HARD_CODED_INPUT
from ..services.openai_extract import extract_triplets
from ..services.graph_write import write_triplets
from ..services.openai_graph_extract import extract_graph
from ..routes.process import _cleanup_mermaid_string
from ..services.graph_json import mermaid_to_json
from ..services.graph_json_write import write_graph_json
from pypdf import PdfReader
import hashlib
import io
from typing import Any, Dict, Optional


router = APIRouter()


@router.api_route("/run", methods=["GET", "POST"])
def run_ingest():
    try:
        text = extract_text_from_path(HARD_CODED_INPUT)
        result = extract_triplets(text)
        writes = write_triplets(
            triplets=result.triplets,
            document_id="sample-doc-1",
            document_title="Sample Input",
        )
        return {"triplets": len(result.triplets), "writes": writes}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class IngestTextRequest(BaseModel):
    text: str
    document_id: str = "user-doc-1"
    document_title: str = "User Submitted"


class IngestGraphJsonRequest(BaseModel):
    graph: Dict[str, Any]
    document_id: Optional[str] = None
    document_title: Optional[str] = None


@router.post("/text")
def ingest_from_text(payload: IngestTextRequest):
    try:
        # Extract Mermaid-style graph and write using JSON model
        mermaid_graph = extract_graph(payload.text, payload.document_title or payload.document_id)
        mermaid_graph = _cleanup_mermaid_string(mermaid_graph)
        graph_json = mermaid_to_json(mermaid_graph)
        stats = write_graph_json(graph_json, document_id=payload.document_id, document_title=payload.document_title)
        return {"nodes": stats["nodes"], "edges": stats["edges"], "model": "graph-json", "graph": graph_json, "document_id": payload.document_id, "title": payload.document_title}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/pdf")
async def ingest_from_pdf(file: UploadFile = File(...)):
    try:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

        pdf_bytes = await file.read()
        # Document identity by SHA-256; title by filename
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        document_id = sha256
        document_title = file.filename or sha256

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "".join([(p.extract_text() or "") for p in reader.pages])
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the PDF.")

        mermaid_graph = extract_graph(text, document_title)
        mermaid_graph = _cleanup_mermaid_string(mermaid_graph)
        graph_json = mermaid_to_json(mermaid_graph)
        stats = write_graph_json(graph_json, document_id=document_id, document_title=document_title)

        return {
            "document_id": document_id,
            "title": document_title,
            "nodes": stats["nodes"],
            "edges": stats["edges"],
            "graph": graph_json,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/graphjson")
def ingest_graphjson(payload: IngestGraphJsonRequest):
    try:
        # Generate a stable document_id if not provided
        doc_id = payload.document_id
        if not doc_id:
            try:
                doc_id = hashlib.sha256(repr(payload.graph).encode("utf-8")).hexdigest()
            except Exception:
                doc_id = "graph-" + hashlib.sha256(b"fallback").hexdigest()
        title = payload.document_title or doc_id
        stats = write_graph_json(payload.graph, document_id=doc_id, document_title=title)
        return {"document_id": doc_id, "title": title, "nodes": stats["nodes"], "edges": stats["edges"], "graph": payload.graph}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

