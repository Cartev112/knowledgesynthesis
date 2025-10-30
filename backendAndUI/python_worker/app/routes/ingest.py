from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Form
from pydantic import BaseModel

from ..services.preprocess import extract_text_from_path, HARD_CODED_INPUT
from ..services.openai_extract import extract_triplets
from ..services.graph_write import write_triplets
from ..services.workspace_service import workspace_service
# from ..services.email_service import send_upload_notification
from pypdf import PdfReader
import hashlib
import io
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def extract_title_from_text(text: str, max_length: int = 500) -> str:
    """
    Extract a meaningful title from document text.
    Looks for title-like patterns in the first few lines.
    Handles multi-line titles common in PDFs.
    """
    if not text or not text.strip():
        return "Untitled Document"
    
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    
    # Strategy 1: Combine first few lines if they look like a multi-line title
    # Common in academic PDFs where title wraps across lines
    if lines:
        title_candidate = []
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            # Stop if we hit what looks like body text
            if len(line) > 200 or line.endswith(('.', '!', '?')) or line.lower().startswith(('abstract', 'introduction', 'keywords')):
                break
            
            # Add line to title candidate
            title_candidate.append(line)
            
            # Check if combined title is complete (ends with a natural break)
            combined = ' '.join(title_candidate)
            if len(combined) >= 30:  # Minimum reasonable title length
                # Stop if next line looks like author/affiliation/abstract
                if i + 1 < len(lines):
                    next_line = lines[i + 1].lower()
                    # Comprehensive author/affiliation detection
                    author_indicators = [
                        'university', 'department', 'abstract', 'author', '@', 'email',
                        'institute', 'college', 'school', 'center', 'centre', 'laboratory', 'lab',
                        'corresponding', 'affiliation', 'address', 'received', 'accepted',
                        'doi:', 'doi ', 'http', 'www.', 'vol.', 'volume', 'issue', 'pp.',
                        'journal', 'proceedings', 'conference', 'symposium', 'workshop',
                        'et al', 'phd', 'md', 'prof', 'professor', 'dr.', 'dr ',
                        'carter', 'whitworth', 'and', '&', '1,', '2,', '3,'  # Common author patterns
                    ]
                    if any(indicator in next_line for indicator in author_indicators):
                        break
                
                # Also check current line for author indicators
                current_line_lower = line.lower()
                if any(indicator in current_line_lower for indicator in ['et al', 'phd', 'md', 'prof', 'dr.', 'dr ', 'and', '&']):
                    break
        
        if title_candidate:
            title = ' '.join(title_candidate)
            title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
            if len(title) <= max_length:
                return title
            else:
                # Truncate at last complete word
                truncated = title[:max_length].rsplit(' ', 1)[0]
                return truncated + '...'
    
    # Strategy 2: Look for a single line in ALL CAPS or Title Case
    for line in lines[:5]:
        if not line:
            continue
        
        # Skip lines that look like author names/affiliations
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in ['university', 'department', 'et al', 'phd', 'md', 'prof', 'dr.', 'dr ', 'and', '&', '@', 'email']):
            continue
        
        words = line.split()
        if len(words) >= 3 and len(line) <= max_length:
            title_case_count = sum(1 for w in words if w and w[0].isupper())
            if title_case_count >= len(words) * 0.7:  # 70% title case
                title = re.sub(r'\s+', ' ', line)
                return title
    
    # Strategy 3: Use first sentence if reasonable length
    sentences = re.split(r'[.!?]\s+', text[:1000])
    if sentences:
        first_sentence = sentences[0].strip()
        if 20 <= len(first_sentence) <= max_length:
            return first_sentence
    
    # Fallback: Use first N characters, truncate at word boundary
    truncated = text[:max_length].strip()
    truncated = re.sub(r'\s+', ' ', truncated)
    if len(truncated) >= max_length:
        truncated = truncated.rsplit(' ', 1)[0] + '...'
    return truncated


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
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None
    user_email: Optional[str] = None
    max_concepts: Optional[int] = 100
    max_relationships: Optional[int] = 50


class IngestGraphJsonRequest(BaseModel):
    # Deprecated placeholder to preserve endpoint shape if called
    document_id: Optional[str] = None
    document_title: Optional[str] = None


@router.post("/text")
async def ingest_from_text(payload: IngestTextRequest, background_tasks: BackgroundTasks):
    try:
        # Auto-extract title if not provided or generic
        document_title = payload.document_title
        if not document_title or document_title in ["User Submitted", "Text Upload"]:
            document_title = extract_title_from_text(payload.text)
            logger.info(f"Auto-extracted title from text: {document_title}")
        
        workspace_metadata = None
        if payload.workspace_id:
            if not payload.user_id:
                raise HTTPException(status_code=400, detail="workspace_id requires user_id")
            workspace_metadata = workspace_service.get_workspace_metadata(payload.workspace_id, payload.user_id)
            if not workspace_metadata:
                raise HTTPException(status_code=404, detail="Workspace not found or access denied")

        result = extract_triplets(
            payload.text,
            max_triplets=payload.max_relationships
        )
        writes = write_triplets(
            triplets=result.triplets,
            document_id=payload.document_id,
            document_title=document_title,
            user_id=payload.user_id,
            user_first_name=payload.user_first_name,
            user_last_name=payload.user_last_name,
            workspace_id=payload.workspace_id,
            workspace_metadata=workspace_metadata
        )
        
        # Send email notification in background
        # if payload.user_email:
        #     user_name = f"{payload.user_first_name or ''} {payload.user_last_name or ''}".strip() or "User"
        #     background_tasks.add_task(
        #         send_upload_notification,
        #         user_email=payload.user_email,
        #         user_name=user_name,
        #         document_title=payload.document_title,
        #         document_id=payload.document_id,
        #         triplet_count=len(result.triplets)
        #     )
        #     logger.info(f"Scheduled email notification for {payload.user_email}")
        
        return {
            "triplets": len(result.triplets),
            "writes": writes,
            "document_id": payload.document_id,
            "title": document_title,
            "user_id": payload.user_id
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/pdf")
async def ingest_from_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    user_first_name: Optional[str] = Form(None),
    user_last_name: Optional[str] = Form(None),
    user_email: Optional[str] = Form(None),
    max_concepts: int = Form(100),
    max_relationships: int = Form(50),
    extraction_context: Optional[str] = Form(None),
    workspace_id: Optional[str] = Form(None)
):
    try:
        logger.info(f"PDF ingest request received - user_id: {user_id}, user_first_name: '{user_first_name}', user_last_name: '{user_last_name}'")
        
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

        workspace_metadata = None
        if workspace_id:
            if not user_id:
                raise HTTPException(status_code=400, detail="workspace_id requires user_id")
            workspace_metadata = workspace_service.get_workspace_metadata(workspace_id, user_id)
            if not workspace_metadata:
                raise HTTPException(status_code=404, detail="Workspace not found or access denied")

        pdf_bytes = await file.read()
        # Document identity by SHA-256; title extracted from text or filename
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        document_id = sha256
        # Title will be extracted from text later

        reader = PdfReader(io.BytesIO(pdf_bytes))
        
        # Extract text per page to preserve page numbers
        pages_with_numbers = []
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages_with_numbers.append({
                    "page_number": page_num,
                    "text": page_text
                })
        
        # Combine all text for title extraction and validation
        full_text = "\n\n".join([p["text"] for p in pages_with_numbers])
        if not full_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the PDF.")
        
        # Auto-extract title from document
        extracted_title = extract_title_from_text(full_text)
        document_title = extracted_title
        logger.info(f"Auto-extracted title: {document_title}")
        
        if extraction_context:
            logger.info(f"Using extraction context: {extraction_context[:100]}...")
        
        logger.info(f"Starting AI extraction for document: {document_title} ({len(pages_with_numbers)} pages)")
        result = extract_triplets(
            full_text, 
            max_triplets=max_relationships, 
            pages=pages_with_numbers,
            extraction_context=extraction_context
        )
        logger.info(f"AI extraction complete. Found {len(result.triplets)} triplets")
        
        logger.info(f"Starting database write for {len(result.triplets)} triplets")
        writes = write_triplets(
            triplets=result.triplets,
            document_id=document_id,
            document_title=document_title,
            user_id=user_id,
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            workspace_id=workspace_id,
            workspace_metadata=workspace_metadata
        )
        logger.info(f"Database write complete. Wrote {writes.get('triplets_written', 0)} relationships")
        
        # Send email notification in background
        # if user_email:
        #     user_name = f"{user_first_name or ''} {user_last_name or ''}".strip() or "User"
        #     background_tasks.add_task(
        #         send_upload_notification,
        #         user_email=user_email,
        #         user_name=user_name,
        #         document_title=document_title,
        #         document_id=document_id,
        #         triplet_count=len(result.triplets)
        #     )
        #     logger.info(f"Scheduled email notification for {user_email}")

        # Extract counts from write results
        triplets_extracted = len(result.triplets)
        triplets_written = writes.get("triplets_written", 0)
        
        return {
            "document_id": document_id,
            "title": document_title,
            "triplets_extracted": triplets_extracted,
            "triplets_written": triplets_written,
            "triplets_merged": triplets_extracted - triplets_written,  # These already existed in DB
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
