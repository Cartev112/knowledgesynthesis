# Asynchronous Ingestion with RabbitMQ - Setup Guide

This guide explains how to set up and use the new asynchronous ingestion system that uses RabbitMQ for job queuing.

## Overview

The system now supports **asynchronous document ingestion** which provides:
- ✅ **Immediate response** - API returns instantly with a job ID
- ✅ **Background processing** - Workers process documents independently
- ✅ **Scalability** - Add more workers to handle load
- ✅ **Reliability** - Jobs survive server restarts (persistent queue)
- ✅ **Progress tracking** - Monitor job status in real-time

## Architecture

```
[User Upload] → [FastAPI Endpoint] → [RabbitMQ Queue] → [Worker Process] → [Neo4j]
                       ↓                                        ↓
                   [Redis]  ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← [Job Status]
```

1. User uploads document via API
2. API creates job record in Redis and queues it in RabbitMQ
3. API returns immediately with `job_id`
4. Worker processes consume jobs from queue
5. Workers update job status in Redis as they progress
6. UI polls Redis for status updates

## Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ with pip
- Node.js (for the frontend server)

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Python dependencies
cd backendAndUI/python_worker
pip install -r ../../requirements.txt
```

### 2. Start Infrastructure Services

Start RabbitMQ and Redis using Docker Compose:

```bash
# From the project root
docker-compose up -d
```

This will start:
- **RabbitMQ** on ports 5672 (AMQP) and 15672 (Management UI)
- **Redis** on port 6379

Verify services are running:

```bash
docker-compose ps
```

### 3. Configure Environment Variables

Add these to your `.env` file or `config/example.env`:

```bash
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
RABBITMQ_VHOST=/

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 4. Start the FastAPI Server

```bash
cd backendAndUI/python_worker
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start the Worker Process(es)

In a **separate terminal**:

```bash
cd backendAndUI/python_worker
python -m app.worker
```

You should see:

```
Worker connected to RabbitMQ at localhost:5672
Worker started. Waiting for jobs in queue 'ingestion_jobs'...
```

**For production**: Run multiple workers for parallel processing:

```bash
# Terminal 1
python -m app.worker

# Terminal 2  
python -m app.worker

# Terminal 3
python -m app.worker
```

### 6. Start the Node.js Server (if using)

```bash
cd node-server
npm install
npm start
```

## API Endpoints

### Submit PDF for Async Ingestion

```bash
POST /api/ingest/pdf_async

# Example with curl
curl -X POST "http://localhost:8000/api/ingest/pdf_async" \
  -F "file=@document.pdf" \
  -F "user_id=user123" \
  -F "user_first_name=John" \
  -F "user_last_name=Doe" \
  -F "max_relationships=50"

# Response:
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "message": "Job queued successfully. Use /api/jobs/{job_id} to check status.",
  "filename": "document.pdf"
}
```

### Submit Text for Async Ingestion

```bash
POST /api/ingest/text_async

# Example with curl
curl -X POST "http://localhost:8000/api/ingest/text_async" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document text here...",
    "document_title": "My Document",
    "user_id": "user123",
    "max_relationships": 50
  }'

# Response:
{
  "job_id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
  "status": "pending",
  "message": "Job queued successfully. Use /api/jobs/{job_id} to check status."
}
```

### Check Job Status

```bash
GET /api/ingest/job/{job_id}

# Example
curl "http://localhost:8000/api/ingest/job/a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Response (pending):
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "document_id": null,
  "document_title": null,
  "created_at": "2025-01-16T10:30:00.123456",
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "triplets_extracted": null,
  "triplets_written": null
}

# Response (completed):
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "document_id": "abc123...",
  "document_title": "Extracted Title from Document",
  "created_at": "2025-01-16T10:30:00.123456",
  "started_at": "2025-01-16T10:30:05.789012",
  "completed_at": "2025-01-16T10:32:15.345678",
  "error_message": null,
  "triplets_extracted": 45,
  "triplets_written": 45
}
```

### List All Jobs

```bash
GET /api/ingest/jobs?user_id=user123&limit=50

# Response:
{
  "jobs": [
    {
      "job_id": "...",
      "status": "completed",
      "document_title": "Document 1",
      "created_at": "2025-01-16T10:30:00",
      "completed_at": "2025-01-16T10:32:15",
      "triplets_extracted": 45
    },
    ...
  ]
}
```

## Job Statuses

- **pending** - Job is queued, waiting for a worker
- **processing** - Worker is currently processing the job
- **completed** - Job finished successfully
- **failed** - Job encountered an error

## Monitoring

### RabbitMQ Management UI

Access at: `http://localhost:15672`
- Username: `guest`
- Password: `guest`

Here you can:
- View queue depth
- Monitor message rates
- See active workers (consumers)
- Inspect messages

### Redis CLI

Check job status directly:

```bash
docker exec -it knowledgesynthesis-redis redis-cli

# List all jobs
KEYS job:*

# Get specific job
GET job:a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

## Production Deployment

### Running Workers as Services

Create a systemd service file `/etc/systemd/system/ks-worker@.service`:

```ini
[Unit]
Description=Knowledge Synthesis Worker %i
After=network.target rabbitmq.service redis.service

[Service]
Type=simple
User=appuser
WorkingDirectory=/path/to/backendAndUI/python_worker
Environment=PATH=/path/to/venv/bin:/usr/bin
ExecStart=/path/to/venv/bin/python -m app.worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start multiple workers:

```bash
sudo systemctl enable ks-worker@{1..3}.service
sudo systemctl start ks-worker@{1..3}.service
```

### Scaling

**Horizontal Scaling:**
- Run multiple worker processes across multiple servers
- All workers connect to the same RabbitMQ instance
- Jobs are automatically distributed (round-robin)

**Vertical Scaling:**
- Increase worker resources (CPU, RAM)
- Adjust `max_triplets` parameter to control job size

## Troubleshooting

### Worker Not Processing Jobs

1. Check worker is running: `ps aux | grep worker`
2. Check RabbitMQ connection: View logs in worker output
3. Check queue has messages: RabbitMQ Management UI

### Jobs Stuck in Pending

1. Ensure at least one worker is running
2. Check RabbitMQ is accessible
3. View worker logs for errors

### Redis Connection Errors

1. Verify Redis is running: `docker ps | grep redis`
2. Test connection: `redis-cli ping`
3. Check environment variables

## Migration from Synchronous to Asynchronous

The old synchronous endpoints (`/ingest/pdf` and `/ingest/text`) are still available for backward compatibility. To migrate:

1. Update UI to call `/api/ingest/pdf_async` or `/api/ingest/text_async`
2. Implement polling for job status using `/api/ingest/job/{job_id}`
3. Update UI to show job progress instead of blocking

## Next Steps

- Implement UI job status polling (see `ASYNC_INGESTION_UI_UPDATE.md`)
- Set up monitoring and alerting for queue depth
- Configure auto-scaling based on queue size
- Add email notifications when jobs complete


