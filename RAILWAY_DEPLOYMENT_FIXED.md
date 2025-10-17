# Railway Deployment - Fixed for Missing RabbitMQ

## 🚨 The Problem
Railway doesn't offer RabbitMQ as a managed service. We need alternative solutions.

## 🎯 Solution Options

### Option 1: CloudAMQP (Recommended)
Use CloudAMQP's free tier for RabbitMQ hosting.

### Option 2: Redis Pub/Sub (Simpler)
Replace RabbitMQ with Redis pub/sub for job queuing.

### Option 3: Railway Custom Service
Deploy RabbitMQ as a custom Docker service on Railway.

---

## 🚀 Option 1: CloudAMQP (Recommended)

### Step 1: Create CloudAMQP Account
1. Go to [CloudAMQP](https://www.cloudAMQP.com)
2. Sign up for free (Little Lemur plan: 1M messages/month)
3. Create a new instance
4. Copy the connection details

### Step 2: Deploy to Railway
1. **Add Redis**: New Service → Database → Redis
2. **Deploy FastAPI**: Use existing setup
3. **Deploy Worker**: Use existing setup

### Step 3: Environment Variables
Set these in Railway for **both** FastAPI and Worker services:

```bash
# CloudAMQP RabbitMQ
RABBITMQ_HOST=your-instance.cloudamqp.com
RABBITMQ_PORT=5672
RABBITMQ_DEFAULT_USER=your-username
RABBITMQ_DEFAULT_PASS=your-password
RABBITMQ_VHOST=your-vhost

# Railway Redis
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}

# Neo4j (you provide)
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# OpenAI (you provide)
OPENAI_API_KEY=your-openai-key
```

### Step 4: Update Code for CloudAMQP
The existing code already handles SSL, so it should work with CloudAMQP out of the box.

---

## 🔄 Option 2: Redis Pub/Sub (Simpler)

This replaces RabbitMQ with Redis pub/sub, eliminating the need for external services.

### Step 1: Create Redis-based Queue System

Create `backendAndUI/python_worker/app/services/redis_queue.py`:

```python
"""Redis-based job queue system (replaces RabbitMQ)."""
import json
import time
import redis
import os
from typing import Optional

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
    ssl=True if os.getenv("RAILWAY_ENVIRONMENT") else False
)

# Queue names
INGEST_QUEUE = "ingestion_jobs"
PROCESSING_QUEUE = "processing_jobs"


class RedisQueue:
    """Redis-based job queue."""
    
    @staticmethod
    def publish_job(job_id: str, job_data: dict) -> bool:
        """Publish job to queue."""
        try:
            # Add job to queue
            redis_client.lpush(INGEST_QUEUE, json.dumps({
                'job_id': job_id,
                'data': job_data
            }))
            return True
        except Exception as e:
            print(f"Failed to publish job: {e}")
            return False
    
    @staticmethod
    def consume_job(timeout: int = 1) -> Optional[dict]:
        """Consume job from queue."""
        try:
            # Blocking pop from queue
            result = redis_client.brpop(INGEST_QUEUE, timeout=timeout)
            if result:
                _, job_json = result
                return json.loads(job_json)
            return None
        except Exception as e:
            print(f"Failed to consume job: {e}")
            return None
    
    @staticmethod
    def move_to_processing(job_id: str, job_data: dict):
        """Move job to processing queue."""
        redis_client.lpush(PROCESSING_QUEUE, json.dumps({
            'job_id': job_id,
            'data': job_data
        }))
```

### Step 2: Update Publisher

Replace `backendAndUI/python_worker/app/services/queue_publisher.py`:

```python
"""Redis-based publisher for ingestion jobs."""
import json
import logging
from .redis_queue import RedisQueue

logger = logging.getLogger(__name__)


class QueuePublisher:
    """Publisher for sending jobs to Redis queue."""
    
    def publish_job(self, job_id: str, job_data: dict) -> bool:
        """Publish an ingestion job to the queue."""
        try:
            success = RedisQueue.publish_job(job_id, job_data)
            if success:
                logger.info(f"Published job {job_id} to Redis queue")
            return success
        except Exception as e:
            logger.error(f"Failed to publish job {job_id}: {e}")
            return False


# Singleton instance
_publisher: Optional[QueuePublisher] = None


def get_publisher() -> QueuePublisher:
    """Get or create the singleton queue publisher."""
    global _publisher
    if _publisher is None:
        _publisher = QueuePublisher()
    return _publisher
```

### Step 3: Update Worker

Replace `backendAndUI/python_worker/app/worker.py`:

```python
"""Redis-based worker for processing ingestion jobs."""
import json
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.job import JobStatus
from app.services.job_tracker import JobTracker
from app.services.redis_queue import RedisQueue
from app.services.openai_extract import extract_triplets
from app.services.graph_write import write_triplets
from app.routes.ingest import extract_title_from_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IngestionWorker:
    """Worker that processes ingestion jobs from Redis queue."""
    
    def start(self):
        """Start consuming messages from the queue."""
        logger.info("Worker started. Waiting for jobs in Redis queue...")
        
        while True:
            try:
                # Get job from queue
                job_item = RedisQueue.consume_job(timeout=5)
                
                if job_item:
                    job_id = job_item['job_id']
                    job_data = job_item['data']
                    
                    logger.info(f"Processing job {job_id}")
                    
                    # Update status to processing
                    JobTracker.update_status(job_id, JobStatus.PROCESSING)
                    
                    # Process job (same logic as before)
                    try:
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
                        
                    except Exception as e:
                        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
                        JobTracker.update_status(
                            job_id,
                            JobStatus.FAILED,
                            error_message=str(e)
                        )
                
            except KeyboardInterrupt:
                logger.info("Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying
    
    # ... rest of the processing methods (same as before)


if __name__ == "__main__":
    worker = IngestionWorker()
    worker.start()
```

### Step 4: Railway Deployment (Redis Only)

1. **Add Redis**: New Service → Database → Redis
2. **Deploy FastAPI**: Use existing setup
3. **Deploy Worker**: Use existing setup

### Step 5: Environment Variables (Redis Only)

```bash
# Railway Redis
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}

# Neo4j (you provide)
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# OpenAI (you provide)
OPENAI_API_KEY=your-openai-key
```

---

## 🐳 Option 3: Custom RabbitMQ Service

Deploy RabbitMQ as a custom Docker service on Railway.

### Step 1: Create RabbitMQ Dockerfile

Create `Dockerfile.rabbitmq`:

```dockerfile
FROM rabbitmq:3.12-management

# Enable management plugin
RUN rabbitmq-plugins enable rabbitmq_management

# Set default user
ENV RABBITMQ_DEFAULT_USER=admin
ENV RABBITMQ_DEFAULT_PASS=password

# Expose ports
EXPOSE 5672 15672
```

### Step 2: Deploy RabbitMQ Service

1. New Service → GitHub Repo
2. Set **Dockerfile Path**: `Dockerfile.rabbitmq`
3. Set **Port**: `5672`

### Step 3: Environment Variables

```bash
# Custom RabbitMQ
RABBITMQ_HOST=${{RabbitMQ.RAILWAY_PRIVATE_DOMAIN}}
RABBITMQ_PORT=5672
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=password
RABBITMQ_VHOST=/

# Railway Redis
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}
```

---

## 🎯 Recommendation

**Use Option 1 (CloudAMQP)** because:
- ✅ Free tier available
- ✅ Managed service (no maintenance)
- ✅ Existing code works with minimal changes
- ✅ Reliable and scalable

**Use Option 2 (Redis Pub/Sub)** if you want:
- ✅ Simpler architecture (one less service)
- ✅ Lower cost (no external service)
- ✅ Easier deployment

**Use Option 3 (Custom RabbitMQ)** if you need:
- ✅ Full control over RabbitMQ
- ✅ Custom configurations
- ✅ No external dependencies

---

## 🚀 Quick Start (CloudAMQP)

1. **Sign up for CloudAMQP** (free tier)
2. **Create instance** and copy connection details
3. **Deploy to Railway**:
   ```bash
   railway add redis
   railway up --service fastapi
   railway up --service worker
   ```
4. **Set environment variables** in Railway dashboard
5. **Test deployment**

Which option would you prefer? I can help you implement any of these solutions!

