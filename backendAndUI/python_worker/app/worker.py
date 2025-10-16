"""RabbitMQ consumer worker for processing ingestion jobs in the background."""
import pika
import json
import os
import logging
import sys
import io
import hashlib
from pypdf import PdfReader
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.job import JobStatus
from app.services.job_tracker import JobTracker
from app.services.openai_extract import extract_triplets
from app.services.graph_write import write_triplets
from app.routes.ingest import extract_title_from_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RabbitMQ settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")
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
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        
        # Check if we're in production (Railway sets RAILWAY_ENVIRONMENT)
        if os.getenv("RAILWAY_ENVIRONMENT"):
            # Production: use SSL for Railway managed services
            import ssl
            ssl_options = pika.SSLOptions(ssl.create_default_context())
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host=RABBITMQ_VHOST,
                credentials=credentials,
                ssl_options=ssl_options,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        else:
            # Development: no SSL
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host=RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declare queue (must match publisher)
        self.channel.queue_declare(queue=INGEST_QUEUE, durable=True)
        
        # Fair dispatch - don't give more than 1 job to a worker at a time
        self.channel.basic_qos(prefetch_count=1)
        
        logger.info(f"Worker connected to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    
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
        
        # Extract title
        document_title = extract_title_from_text(full_text)
        
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
            document_title = extract_title_from_text(text_content)
        
        document_id = job_data.get('document_id', f"text-{job_id}")
        
        logger.info(f"Job {job_id}: Processing text '{document_title}'")
        
        # Extract triplets
        result = extract_triplets(
            text_content,
            max_triplets=job_data.get('max_relationships', 50)
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
            elif 'text_content' in job_data:
                result = self._process_text_job(job_data)
            else:
                raise ValueError("Job must contain either 'pdf_bytes' or 'text_content'")
            
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

