"""RabbitMQ consumer worker for processing ingestion jobs in the background."""
import pika
import json
import os
import logging
import sys
import io
import hashlib
import requests
from pypdf import PdfReader
from typing import Optional
from pdfminer.high_level import extract_text as pdfminer_extract_text

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.job import JobStatus
from app.services.job_tracker import JobTracker
from app.services.openai_extract import extract_triplets, extract_title_with_llm
from app.services.graph_write import write_triplets
from app.services.graph_embeddings import (
    ensure_vector_indexes,
    upsert_document_embedding,
    upsert_entity_embeddings_for_document,
)
from app.services.email_service import send_upload_notification
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RabbitMQ settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT") or "5672")
RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER") or "guest"
RABBITMQ_DEFAULT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS") or "guest"
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST") or "/"
INGEST_QUEUE = "ingestion_jobs"


class IngestionWorker:
    """Worker that processes ingestion jobs from RabbitMQ."""
    
    def __init__(self):
        """Initialize worker connection."""
        self.connection = None
        self.channel = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Set up RabbitMQ connection and channel."""
        # Check if RABBITMQ_URL is provided (Railway, CloudAMQP, etc.)
        rabbitmq_url = os.getenv("RABBITMQ_URL")
        
        if rabbitmq_url:
            # Use URL-based connection (works for both Railway and local)
            parameters = pika.URLParameters(rabbitmq_url)
            logger.info("Worker connecting to RabbitMQ via URL")
        else:
            # Fall back to individual parameters (local development)
            credentials = pika.PlainCredentials(RABBITMQ_DEFAULT_USER, RABBITMQ_DEFAULT_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host=RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            logger.info(f"Worker connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declare queue (must match publisher)
        self.channel.queue_declare(queue=INGEST_QUEUE, durable=True)
        
        # Fair dispatch - don't give more than 1 job to a worker at a time
        self.channel.basic_qos(prefetch_count=1)
        
        
    
    def _process_pdf_job(self, job_data: dict) -> dict:
        """Process a PDF ingestion job."""
        job_id = job_data['job_id']
        
        # Get PDF bytes from job data (base64 encoded)
        import base64
        pdf_bytes = base64.b64decode(job_data['pdf_bytes'])
        
        # Extract text from PDF
        reader = PdfReader(io.BytesIO(pdf_bytes))
        
        pages_with_numbers = []
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages_with_numbers.append({
                    "page_number": page_num,
                    "text": page_text
                })
        
        # Combine text
        full_text = "\n\n".join([p["text"] for p in pages_with_numbers])
        if not full_text.strip():
            raise ValueError("Could not extract any text from the PDF")
        
        # Extract title using LLM
        document_title = extract_title_with_llm(full_text)
        
        # Generate document_id from hash
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        document_id = sha256
        
        logger.info(f"Job {job_id}: Processing PDF '{document_title}' ({len(pages_with_numbers)} pages)")
        
        # Extract triplets using AI
        result = extract_triplets(
            full_text,
            max_triplets=job_data.get('max_relationships', 50),
            pages=pages_with_numbers,
            extraction_context=job_data.get('extraction_context')
        )
        
        logger.info(f"Job {job_id}: Extracted {len(result.triplets)} triplets")
        
        # Write to Neo4j
        writes = write_triplets(
            triplets=result.triplets,
            document_id=document_id,
            document_title=document_title,
            user_id=job_data.get('user_id'),
            user_first_name=job_data.get('user_first_name'),
            user_last_name=job_data.get('user_last_name')
        )
        
        # Generate and store embeddings
        try:
            ensure_vector_indexes()
            upsert_document_embedding(document_id, document_title, result.triplets)
            upsert_entity_embeddings_for_document(document_id)
        except Exception as emb_exc:
            logger.warning(f"Embedding generation failed for job {job_id}: {emb_exc}")
        
        return {
            'document_id': document_id,
            'document_title': document_title,
            'triplets_extracted': len(result.triplets),
            'triplets_written': writes.get('triplets_written', 0)
        }
    
    def _process_text_job(self, job_data: dict) -> dict:
        """Process a text ingestion job."""
        job_id = job_data['job_id']
        text_content = job_data['text_content']
        
        # Extract or use provided title
        document_title = job_data.get('document_title')
        if not document_title:
            document_title = extract_title_with_llm(text_content)
        
        document_id = job_data.get('document_id', f"text-{job_id}")
        
        logger.info(f"Job {job_id}: Processing text '{document_title}'")
        
        # Extract triplets
        result = extract_triplets(
            text_content,
            max_triplets=job_data.get('max_relationships', 50),
            extraction_context=job_data.get('extraction_context')
        )
        
        logger.info(f"Job {job_id}: Extracted {len(result.triplets)} triplets")
        
        # Write to Neo4j
        writes = write_triplets(
            triplets=result.triplets,
            document_id=document_id,
            document_title=document_title,
            user_id=job_data.get('user_id'),
            user_first_name=job_data.get('user_first_name'),
            user_last_name=job_data.get('user_last_name')
        )
        
        return {
            'document_id': document_id,
            'document_title': document_title,
            'triplets_extracted': len(result.triplets),
            'triplets_written': writes.get('triplets_written', 0)
        }
    
    def _process_pdf_url_job(self, job_data: dict) -> dict:
        """Process a PDF URL ingestion job by downloading and extracting."""
        job_id = job_data['job_id']
        pdf_url = job_data['pdf_url']
        
        logger.info(f"Job {job_id}: Downloading PDF from {pdf_url}")
        
        # Download PDF from URL
        try:
            response = requests.get(
                pdf_url,
                timeout=60,
                stream=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                    "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8"
                },
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            content_disp = (response.headers.get('content-disposition') or '').lower()
            is_pdf = ('pdf' in content_type) or pdf_url.lower().endswith('.pdf') or ('.pdf' in content_disp)
            if not is_pdf:
                logger.warning(
                    f"Job {job_id}: URL may not be a PDF (content-type: {content_type}, content-disposition: {content_disp}). Aborting."
                )
                raise ValueError("Provided URL does not appear to be a PDF. Please provide a direct PDF link.")
            
            pdf_bytes = response.content
            
            # Check size (limit to 50MB)
            max_size_mb = 50
            if len(pdf_bytes) > max_size_mb * 1024 * 1024:
                raise ValueError(f"PDF too large. Maximum size is {max_size_mb}MB")
            
            logger.info(f"Job {job_id}: Downloaded {len(pdf_bytes)} bytes")
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to download PDF: {str(e)}")
        
        # Extract text from PDF
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            
            pages_with_numbers = []
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages_with_numbers.append({
                        "page_number": page_num,
                        "text": page_text
                    })
            
            # Combine text
            full_text = "\n\n".join([p["text"] for p in pages_with_numbers])
            primary_chars = len(full_text)
            logger.info(
                f"Job {job_id}: PyPDF extracted {primary_chars} chars from {len(pages_with_numbers)} pages"
            )
            
            # If extraction seems too small, try pdfminer as a fallback
            need_fallback = (primary_chars < 800 and len(pages_with_numbers) >= 1)
            if need_fallback:
                try:
                    miner_text = pdfminer_extract_text(io.BytesIO(pdf_bytes)) or ""
                    miner_pages_raw = [seg.strip() for seg in miner_text.split('\f')]
                    miner_pages = [seg for seg in miner_pages_raw if seg]
                    if miner_pages:
                        pages_with_numbers = [
                            {"page_number": i + 1, "text": t} for i, t in enumerate(miner_pages)
                        ]
                        full_text = "\n\n".join(miner_pages)
                    fallback_chars = len(full_text)
                    logger.info(
                        f"Job {job_id}: pdfminer fallback extracted {fallback_chars} chars from {len(pages_with_numbers)} pages"
                    )
                except Exception as fe:
                    logger.warning(f"Job {job_id}: pdfminer fallback failed: {fe}")
            
            if not full_text.strip():
                raise ValueError("Could not extract any text from the PDF")
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
        
        # Extract or use provided title
        document_title = job_data.get('document_title')
        if not document_title:
            document_title = extract_title_with_llm(full_text)
        
        # Generate document_id from hash
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        document_id = sha256
        
        logger.info(
            f"Job {job_id}: Processing PDF '{document_title}' with {len(pages_with_numbers)} pages and {len(full_text)} chars"
        )
        
        # Extract triplets using AI
        result = extract_triplets(
            full_text,
            max_triplets=job_data.get('max_relationships', 50),
            pages=pages_with_numbers,
            extraction_context=job_data.get('extraction_context')
        )
        
        logger.info(f"Job {job_id}: Extracted {len(result.triplets)} triplets")
        
        # Write to Neo4j
        writes = write_triplets(
            triplets=result.triplets,
            document_id=document_id,
            document_title=document_title,
            user_id=job_data.get('user_id'),
            user_first_name=job_data.get('user_first_name'),
            user_last_name=job_data.get('user_last_name')
        )
        
        return {
            'document_id': document_id,
            'document_title': document_title,
            'triplets_extracted': len(result.triplets),
            'triplets_written': writes.get('triplets_written', 0)
        }
    
    def _callback(self, ch, method, properties, body):
        """Process a message from the queue."""
        job_data = None
        job_id = None
        
        try:
            # Parse job data
            job_data = json.loads(body)
            job_id = job_data['job_id']
            
            logger.info(f"Processing job {job_id}")
            
            # Update status to processing
            JobTracker.update_status(job_id, JobStatus.PROCESSING)
            
            # Process based on job type
            if 'pdf_bytes' in job_data:
                result = self._process_pdf_job(job_data)
            elif 'pdf_url' in job_data:
                result = self._process_pdf_url_job(job_data)
            elif 'text_content' in job_data:
                result = self._process_text_job(job_data)
            else:
                raise ValueError("Job must contain 'pdf_bytes', 'pdf_url', or 'text_content'")
            
            # Update job with results
            JobTracker.update_status(
                job_id,
                JobStatus.COMPLETED,
                document_id=result['document_id'],
                document_title=result['document_title'],
                triplets_extracted=result['triplets_extracted'],
                triplets_written=result['triplets_written']
            )
            
            logger.info(f"Job {job_id} completed successfully")
            
            # Send email notification if user email is provided
            user_email = job_data.get('user_email')
            if user_email:
                try:
                    user_first_name = job_data.get('user_first_name', '')
                    user_last_name = job_data.get('user_last_name', '')
                    user_name = f"{user_first_name} {user_last_name}".strip() or "User"
                    
                    # Run async email send in sync context
                    asyncio.run(send_upload_notification(
                        user_email=user_email,
                        user_name=user_name,
                        document_title=result['document_title'],
                        document_id=result['document_id'],
                        triplet_count=result['triplets_written']
                    ))
                    logger.info(f"Email notification sent to {user_email}")
                except Exception as email_error:
                    logger.warning(f"Failed to send email notification: {email_error}")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            
            # Update job status to failed
            if job_id:
                JobTracker.update_status(
                    job_id,
                    JobStatus.FAILED,
                    error_message=str(e)
                )
            
            # Acknowledge message (don't requeue to avoid infinite loops)
            ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def start(self):
        """Start consuming messages from the queue."""
        logger.info(f"Worker started. Waiting for jobs in queue '{INGEST_QUEUE}'...")
        
        self.channel.basic_consume(
            queue=INGEST_QUEUE,
            on_message_callback=self._callback
        )
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            self.channel.stop_consuming()
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()


if __name__ == "__main__":
    worker = IngestionWorker()
    worker.start()

