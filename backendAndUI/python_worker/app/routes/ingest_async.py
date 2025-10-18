"""Asynchronous ingestion endpoints using RabbitMQ job queue."""
import uuid
import base64
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel

from ..models.job import IngestJob, JobStatus
from ..services.job_tracker import JobTracker
from ..services.queue_publisher import get_publisher

logger = logging.getLogger(__name__)
router = APIRouter()


class IngestTextRequest(BaseModel):
    """Request model for text ingestion."""
    text: str
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    user_id: Optional[str] = None
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None
    user_email: Optional[str] = None
    max_concepts: int = 100
    max_relationships: int = 50
    extraction_context: Optional[str] = None


@router.post("/text_async")
async def ingest_text_async(payload: IngestTextRequest):
    """
    Submit a text document for async ingestion.
    Returns immediately with a job_id for status tracking.
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job object
        job = IngestJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            document_id=payload.document_id,
            document_title=payload.document_title,
            user_id=payload.user_id,
            user_first_name=payload.user_first_name,
            user_last_name=payload.user_last_name,
            user_email=payload.user_email,
            max_concepts=payload.max_concepts,
            max_relationships=payload.max_relationships,
            extraction_context=payload.extraction_context,
            text_content=payload.text,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Store job in Redis
        JobTracker.create_job(job)
        
        # Publish to queue (without large text content in Redis)
        job_data = {
            'job_id': job_id,
            'text_content': payload.text,
            'document_id': payload.document_id,
            'document_title': payload.document_title,
            'user_id': payload.user_id,
            'user_first_name': payload.user_first_name,
            'user_last_name': payload.user_last_name,
            'max_relationships': payload.max_relationships,
            'extraction_context': payload.extraction_context
        }
        
        publisher = get_publisher()
        success = publisher.publish_job(job_id, job_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to queue job")
        
        logger.info(f"Queued text ingestion job {job_id}")
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Job queued successfully. Use /api/jobs/{job_id} to check status."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queueing text job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf_async")
async def ingest_pdf_async(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    user_first_name: Optional[str] = Form(None),
    user_last_name: Optional[str] = Form(None),
    user_email: Optional[str] = Form(None),
    max_concepts: int = Form(100),
    max_relationships: int = Form(50),
    extraction_context: Optional[str] = Form(None)
):
    """
    Submit a PDF document for async ingestion.
    Returns immediately with a job_id for status tracking.
    """
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload a PDF."
            )
        
        # Read PDF bytes
        pdf_bytes = await file.read()
        
        # Check file size (limit to 50MB to avoid RabbitMQ message size issues)
        max_size_mb = 50
        if len(pdf_bytes) > max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"PDF file too large. Maximum size is {max_size_mb}MB."
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job object (without storing PDF bytes in Redis)
        job = IngestJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            user_id=user_id,
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            user_email=user_email,
            max_concepts=max_concepts,
            max_relationships=max_relationships,
            extraction_context=extraction_context,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Store job in Redis
        JobTracker.create_job(job)
        
        # Publish to queue (with base64 encoded PDF)
        job_data = {
            'job_id': job_id,
            'pdf_bytes': base64.b64encode(pdf_bytes).decode('utf-8'),
            'user_id': user_id,
            'user_first_name': user_first_name,
            'user_last_name': user_last_name,
            'max_concepts': max_concepts,
            'max_relationships': max_relationships,
            'extraction_context': extraction_context
        }
        
        publisher = get_publisher()
        success = publisher.publish_job(job_id, job_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to queue job")
        
        logger.info(f"Queued PDF ingestion job {job_id} for file: {file.filename}")
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Job queued successfully. Use /api/jobs/{job_id} to check status.",
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queueing PDF job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of an ingestion job."""
    try:
        job = JobTracker.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "document_id": job.document_id,
            "document_title": job.document_title,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message,
            "triplets_extracted": job.triplets_extracted,
            "triplets_written": job.triplets_written
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(user_id: Optional[str] = None, limit: int = 50):
    """List recent ingestion jobs, optionally filtered by user."""
    try:
        jobs = JobTracker.list_jobs(user_id=user_id, limit=limit)
        
        return {
            "jobs": [
                {
                    "job_id": job.job_id,
                    "status": job.status,
                    "document_title": job.document_title,
                    "created_at": job.created_at,
                    "completed_at": job.completed_at,
                    "triplets_extracted": job.triplets_extracted
                }
                for job in jobs
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


