"""Job model for tracking ingestion job status."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestJob(BaseModel):
    """Model for an ingestion job."""
    job_id: str
    status: JobStatus
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    workspace_id: Optional[str] = None
    workspace_metadata: Optional[dict] = None
    user_id: Optional[str] = None
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None
    user_email: Optional[str] = None
    max_concepts: int = 100
    max_relationships: int = 50
    extraction_context: Optional[str] = None
    
    # File or text content
    pdf_bytes: Optional[bytes] = None
    text_content: Optional[str] = None
    
    # Progress tracking
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    
    # Results
    triplets_extracted: Optional[int] = None
    triplets_written: Optional[int] = None
    
    class Config:
        use_enum_values = True


