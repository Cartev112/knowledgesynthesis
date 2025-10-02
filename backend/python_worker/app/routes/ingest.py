from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from ..services.preprocess import extract_text_from_path, HARD_CODED_INPUT
from ..services.openai_extract import extract_triplets
from ..services.graph_write import write_triplets
from pypdf import PdfReader
import hashlib
import io
from typing import Optional


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
    user_id: Optional[str] = None
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None
    max_concepts: Optional[int] = 100
    max_relationships: Optional[int] = 50


class IngestGraphJsonRequest(BaseModel):
    # Deprecated placeholder to preserve endpoint shape if called
    document_id: Optional[str] = None
    document_title: Optional[str] = None


@router.post("/text")
def ingest_from_text(payload: IngestTextRequest):
    try:
        result = extract_triplets(
            payload.text,
            max_triplets=payload.max_relationships
        )
        writes = write_triplets(
            triplets=result.triplets,
            document_id=payload.document_id,
            document_title=payload.document_title,
            user_id=payload.user_id,
            user_first_name=payload.user_first_name,
            user_last_name=payload.user_last_name
        )
        return {
            "triplets": len(result.triplets),
            "writes": writes,
            "document_id": payload.document_id,
            "title": payload.document_title,
            "user_id": payload.user_id
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/pdf")
async def ingest_from_pdf(
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    user_first_name: Optional[str] = None,
    user_last_name: Optional[str] = None,
    max_concepts: int = 100,
    max_relationships: int = 50,
    title: Optional[str] = None
):
    try:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

        pdf_bytes = await file.read()
        # Document identity by SHA-256; title by filename or provided title
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        document_id = sha256
        document_title = title or file.filename or sha256

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "".join([(p.extract_text() or "") for p in reader.pages])
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the PDF.")

        result = extract_triplets(text, max_triplets=max_relationships)
        writes = write_triplets(
            triplets=result.triplets,
            document_id=document_id,
            document_title=document_title,
            user_id=user_id,
            user_first_name=user_first_name,
            user_last_name=user_last_name
        )

        return {
            "document_id": document_id,
            "title": document_title,
            "triplets": len(result.triplets),
            "writes": writes,
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/graphjson")
def ingest_graphjson(payload: IngestGraphJsonRequest):
    raise HTTPException(status_code=410, detail="/ingest/graphjson removed. Use /ingest/text or /ingest/pdf.")

