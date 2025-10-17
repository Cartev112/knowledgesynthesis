# Railway Deployment Guide for Async Ingestion System

This guide shows how to deploy the Knowledge Synthesis system with RabbitMQ job queues on Railway.

## Overview

Railway doesn't support Docker Compose directly, so we need to:
1. Use Railway's managed services for RabbitMQ and Redis
2. Deploy the FastAPI app as a service
3. Deploy the worker as a separate service
4. Configure environment variables properly

## Architecture on Railway

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Worker App    │    │   Node.js UI    │
│   (Port 8000)   │    │   (Background)  │    │   (Port 3000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RabbitMQ      │    │     Redis       │    │     Neo4j       │
│  (Managed)      │    │   (Managed)     │    │   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Step 1: Create Railway Project

1. Go to [Railway.app](https://railway.app)
2. Create a new project
3. Connect your GitHub repository

## Step 2: Add Managed Services

### Add RabbitMQ
1. In your Railway project, click "New Service"
2. Select "Database" → "RabbitMQ"
3. Railway will provision a managed RabbitMQ instance
4. Note the connection details from the service variables

### Add Redis
1. Click "New Service" again
2. Select "Database" → "Redis"
3. Railway will provision a managed Redis instance
4. Note the connection details

## Step 3: Deploy FastAPI Application

### Create Railway Configuration

Create `railway.json` in your project root:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backendAndUI/python_worker && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Create Procfile for FastAPI

Create `Procfile` in your project root:

```
web: cd backendAndUI/python_worker && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables for FastAPI

In Railway, go to your FastAPI service → Variables and add:

```bash
# Port (Railway sets this automatically)
PORT=8000

# Neo4j Configuration
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# RabbitMQ Configuration (from Railway managed service)
RABBITMQ_HOST=${{RabbitMQ.RABBITMQ_HOST}}
RABBITMQ_PORT=${{RabbitMQ.RABBITMQ_PORT}}
RABBITMQ_DEFAULT_USER=${{RabbitMQ.RABBITMQ_DEFAULT_USER}}
RABBITMQ_DEFAULT_PASS=${{RabbitMQ.RABBITMQ_DEFAULT_PASSWORD}}
RABBITMQ_VHOST=${{RabbitMQ.RABBITMQ_VHOST}}

# Redis Configuration (from Railway managed service)
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}

# OpenAI Configuration
OPENAI_API_KEY=your-openai-key

# Other settings
PYTHONPATH=backendAndUI/python_worker
```

## Step 4: Deploy Worker Service

### Create Worker Procfile

Create `Procfile.worker` in your project root:

```
worker: cd backendAndUI/python_worker && python -m app.worker
```

### Deploy Worker as Separate Service

1. In Railway, click "New Service"
2. Select "GitHub Repo" and choose your repository
3. In the service settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backendAndUI/python_worker && python -m app.worker`
   - **Health Check**: Disable (workers don't need HTTP health checks)

### Environment Variables for Worker

Add the same environment variables as the FastAPI service:

```bash
# RabbitMQ Configuration
RABBITMQ_HOST=${{RabbitMQ.RABBITMQ_HOST}}
RABBITMQ_PORT=${{RabbitMQ.RABBITMQ_PORT}}
RABBITMQ_DEFAULT_USER=${{RabbitMQ.RABBITMQ_DEFAULT_USER}}
RABBITMQ_DEFAULT_PASS=${{RabbitMQ.RABBITMQ_DEFAULT_PASSWORD}}
RABBITMQ_VHOST=${{RabbitMQ.RABBITMQ_VHOST}}

# Redis Configuration
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}

# Neo4j Configuration
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# OpenAI Configuration
OPENAI_API_KEY=your-openai-key

# Python path
PYTHONPATH=backendAndUI/python_worker
```

## Step 5: Deploy Node.js Frontend (Optional)

If you want to deploy the Node.js server as well:

1. Create another service in Railway
2. Set the root directory to `node-server`
3. Railway will auto-detect it's a Node.js app
4. Add environment variables:

```bash
PORT=3000
FASTAPI_BASE_URL=https://your-fastapi-service.railway.app
```

## Step 6: Configure Neo4j

Since Railway doesn't offer Neo4j as a managed service, you have a few options:

### Option A: External Neo4j (Recommended)
- Use Neo4j AuraDB (cloud)
- Or deploy Neo4j on another cloud provider
- Update the `NEO4J_URI` environment variable

### Option B: Self-hosted Neo4j
- Deploy Neo4j as a separate Railway service using a custom Dockerfile
- Create `Dockerfile.neo4j`:

```dockerfile
FROM neo4j:5.12
ENV NEO4J_AUTH=neo4j/your-password
ENV NEO4J_PLUGINS='["apoc"]'
EXPOSE 7474 7687
```

## Step 7: Update Code for Production

### Update Worker Connection Logic

Modify `backendAndUI/python_worker/app/services/queue_publisher.py`:

```python
# Add SSL support for production
def _connect(self):
    """Establish connection to RabbitMQ."""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_DEFAULT_USER, RABBITMQ_DEFAULT_PASS)
        
        # Check if we're in production (Railway sets RAILWAY_ENVIRONMENT)
        if os.getenv("RAILWAY_ENVIRONMENT"):
            # Production: use SSL
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
        # ... rest of the method
```

### Update Redis Connection

Modify `backendAndUI/python_worker/app/services/job_tracker.py`:

```python
# Add password support for production Redis
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=os.getenv("REDIS_PASSWORD"),  # Railway Redis has password
    decode_responses=True,
    ssl=True if os.getenv("RAILWAY_ENVIRONMENT") else False  # SSL in production
)
```

## Step 8: Deployment Commands

### Deploy All Services

```bash
# 1. Deploy FastAPI service
railway up --service fastapi

# 2. Deploy Worker service  
railway up --service worker

# 3. Deploy Node.js service (if needed)
railway up --service frontend
```

### Monitor Deployments

```bash
# Check service status
railway status

# View logs
railway logs --service fastapi
railway logs --service worker

# Connect to services
railway connect --service fastapi
railway connect --service worker
```

## Step 9: Testing the Deployment

### Test API Endpoints

```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Test async ingestion
curl -X POST "https://your-app.railway.app/api/ingest/text_async" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test document", "user_id": "test"}'

# Check job status
curl "https://your-app.railway.app/api/ingest/job/YOUR_JOB_ID"
```

### Monitor Services

1. **RabbitMQ Management**: Railway provides a management URL
2. **Redis**: Use Railway's Redis CLI or connect via Redis client
3. **Application Logs**: Check Railway dashboard for each service

## Step 10: Scaling and Optimization

### Scale Workers

To handle more load, deploy multiple worker services:

1. Duplicate the worker service in Railway
2. Each worker will automatically connect to the same RabbitMQ queue
3. Jobs will be distributed across all workers

### Environment-Specific Configuration

Create different environment variables for different stages:

```bash
# Production
RAILWAY_ENVIRONMENT=production
LOG_LEVEL=INFO

# Staging  
RAILWAY_ENVIRONMENT=staging
LOG_LEVEL=DEBUG
```

## Troubleshooting

### Common Issues

1. **Worker not processing jobs**
   - Check worker logs: `railway logs --service worker`
   - Verify RabbitMQ connection variables
   - Ensure worker service is running

2. **Redis connection errors**
   - Check Redis password is set correctly
   - Verify SSL settings for production

3. **FastAPI not starting**
   - Check build logs for dependency issues
   - Verify PORT environment variable
   - Check Python path configuration

### Debug Commands

```bash
# Check service variables
railway variables --service fastapi
railway variables --service worker

# Connect to service shell
railway shell --service fastapi

# View real-time logs
railway logs --follow --service worker
```

## Cost Optimization

### Railway Pricing Considerations

1. **Services**: Each service (FastAPI, Worker, Node.js) counts as a separate service
2. **Database Services**: RabbitMQ and Redis are charged separately
3. **Usage**: Monitor CPU and memory usage in Railway dashboard

### Optimization Tips

1. **Combine Services**: Consider running worker and FastAPI in the same service with a process manager
2. **Resource Limits**: Set appropriate CPU/memory limits
3. **Auto-sleep**: Enable auto-sleep for development environments

## Alternative: Single Service Deployment

If you want to minimize Railway services, you can run everything in one service:

### Create `start.sh`

```bash
#!/bin/bash
# Start FastAPI in background
cd backendAndUI/python_worker
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT &

# Start worker in background
python -m app.worker &

# Wait for any process to exit
wait
```

### Update Procfile

```
web: ./start.sh
```

This approach runs both FastAPI and the worker in the same Railway service, reducing costs but potentially less reliable for scaling.

## Next Steps

1. **Monitoring**: Set up monitoring and alerting
2. **Backups**: Configure Redis and Neo4j backups
3. **CI/CD**: Set up automated deployments
4. **Security**: Configure proper authentication and HTTPS
5. **Performance**: Monitor and optimize based on usage patterns

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- This project's GitHub issues for specific problems

