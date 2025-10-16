#!/bin/bash

# Quick start script for the async ingestion system
# This script starts all required services for async document processing

echo "================================================"
echo "Knowledge Synthesis - Async Ingestion System"
echo "================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Start RabbitMQ and Redis
echo "Starting RabbitMQ and Redis..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 5

# Check if services are running
if docker ps | grep -q knowledgesynthesis-rabbitmq; then
    echo "✓ RabbitMQ is running (Management UI: http://localhost:15672)"
else
    echo "❌ RabbitMQ failed to start"
    exit 1
fi

if docker ps | grep -q knowledgesynthesis-redis; then
    echo "✓ Redis is running"
else
    echo "❌ Redis failed to start"
    exit 1
fi

echo ""
echo "================================================"
echo "Services Started Successfully!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the FastAPI server:"
echo "   cd backendAndUI/python_worker"
echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "2. Start the worker (in a new terminal):"
echo "   cd backendAndUI/python_worker"
echo "   python -m app.worker"
echo ""
echo "3. Test the system:"
echo "   curl -X POST 'http://localhost:8000/api/ingest/text_async' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"text\": \"Test document\", \"user_id\": \"test\"}'"
echo ""
echo "================================================"
echo "Monitoring:"
echo "================================================"
echo ""
echo "RabbitMQ Management UI: http://localhost:15672 (guest/guest)"
echo "FastAPI Docs: http://localhost:8000/docs"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""


