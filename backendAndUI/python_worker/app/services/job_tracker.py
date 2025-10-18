"""Job tracking service using Redis for fast status updates."""
import json
import redis
from typing import Optional
from datetime import datetime
import os
from ..models.job import IngestJob, JobStatus

# Redis connection - support both REDIS_URL (Railway) and individual vars
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    # Use REDIS_URL if provided (Railway, Upstash, etc.)
    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        ssl_cert_reqs=None  # Allow self-signed certs
    )
else:
    # Fall back to individual environment variables (local development)
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
        ssl=True if os.getenv("RAILWAY_ENVIRONMENT") else False
    )


class JobTracker:
    """Track ingestion job status using Redis."""
    
    @staticmethod
    def create_job(job: IngestJob) -> None:
        """Create a new job in Redis."""
        # Store job data (excluding large binary data)
        job_data = job.dict(exclude={"pdf_bytes"})
        redis_client.setex(
            f"job:{job.job_id}",
            86400,  # 24 hours TTL
            json.dumps(job_data, default=str)
        )
    
    @staticmethod
    def get_job(job_id: str) -> Optional[IngestJob]:
        """Retrieve job by ID."""
        data = redis_client.get(f"job:{job_id}")
        if not data:
            return None
        return IngestJob(**json.loads(data))
    
    @staticmethod
    def update_status(
        job_id: str,
        status: JobStatus,
        **kwargs
    ) -> None:
        """Update job status and other fields."""
        job = JobTracker.get_job(job_id)
        if not job:
            return
        
        # Update status
        job.status = status
        
        # Update timestamp based on status
        if status == JobStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.utcnow().isoformat()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.utcnow().isoformat()
        
        # Update any additional fields
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        # Save back to Redis
        job_data = job.dict(exclude={"pdf_bytes"})
        redis_client.setex(
            f"job:{job_id}",
            86400,
            json.dumps(job_data, default=str)
        )
    
    @staticmethod
    def list_jobs(user_id: Optional[str] = None, limit: int = 50) -> list[IngestJob]:
        """List recent jobs, optionally filtered by user."""
        # This is a simple implementation; for production, you'd want to maintain
        # a sorted set by timestamp for efficient querying
        jobs = []
        for key in redis_client.scan_iter("job:*", count=100):
            data = redis_client.get(key)
            if data:
                job = IngestJob(**json.loads(data))
                if user_id is None or job.user_id == user_id:
                    jobs.append(job)
                if len(jobs) >= limit:
                    break
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

