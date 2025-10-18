"""RabbitMQ publisher for ingestion jobs."""
import pika
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# RabbitMQ connection settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER", "guest")
RABBITMQ_DEFAULT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

# Queue names
INGEST_QUEUE = "ingestion_jobs"


class QueuePublisher:
    """Publisher for sending jobs to RabbitMQ."""
    
    def __init__(self):
        """Initialize connection to RabbitMQ."""
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ."""
        try:
            # Check if RABBITMQ_URL is provided (Railway, CloudAMQP, etc.)
            rabbitmq_url = os.getenv("RABBITMQ_URL")
            
            if rabbitmq_url:
                # Use URL-based connection (works for both Railway and local)
                parameters = pika.URLParameters(rabbitmq_url)
                logger.info("Publisher connecting to RabbitMQ via URL")
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
                logger.info(f"Publisher connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queue (idempotent)
            self.channel.queue_declare(
                queue=INGEST_QUEUE,
                durable=True  # Survive broker restarts
            )
            
            logger.info(f"Connected to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def publish_job(self, job_id: str, job_data: dict) -> bool:
        """
        Publish an ingestion job to the queue.
        
        Args:
            job_id: Unique job identifier
            job_data: Job payload as dictionary
        
        Returns:
            bool: True if published successfully
        """
        try:
            # Ensure connection is alive
            if self.connection is None or self.connection.is_closed:
                self._connect()
            
            # Publish message
            self.channel.basic_publish(
                exchange='',
                routing_key=INGEST_QUEUE,
                body=json.dumps(job_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json',
                    message_id=job_id
                )
            )
            
            logger.info(f"Published job {job_id} to queue {INGEST_QUEUE}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish job {job_id}: {e}")
            return False
    
    def close(self):
        """Close RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Closed RabbitMQ connection")


# Singleton instance
_publisher: Optional[QueuePublisher] = None


def get_publisher() -> QueuePublisher:
    """Get or create the singleton queue publisher."""
    global _publisher
    if _publisher is None:
        _publisher = QueuePublisher()
    return _publisher

