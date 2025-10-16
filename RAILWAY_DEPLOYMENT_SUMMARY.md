# Railway Deployment - Complete Setup Guide

## 🎯 What You Need to Deploy

Your async ingestion system needs these services on Railway:

1. **FastAPI App** - Main API server
2. **Worker Service** - Background job processor  
3. **RabbitMQ** - Message queue (managed service)
4. **Redis** - Job status tracking (managed service)
5. **Neo4j** - Graph database (external or self-hosted)

## 🚀 Quick Start (TL;DR)

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
# or
curl -fsSL https://railway.app/install.sh | sh
```

### 2. Run Deployment Script
```bash
# Windows
.\deploy_to_railway.ps1

# Linux/Mac  
./deploy_to_railway.sh
```

### 3. Set Environment Variables
In Railway dashboard, add these variables to **both** FastAPI and Worker services:

```bash
# Neo4j (you need to provide this)
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# OpenAI (you need to provide this)
OPENAI_API_KEY=your-openai-key

# Railway will auto-set these from managed services:
# RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS
# REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
```

### 4. Test It
```bash
# Test health
curl https://your-app.railway.app/health

# Test async ingestion
curl -X POST "https://your-app.railway.app/api/ingest/text_async" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test document", "user_id": "test"}'
```

## 📋 Manual Setup (Step by Step)

### Step 1: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Create new project
3. Connect your GitHub repo

### Step 2: Add Managed Services
1. **Add RabbitMQ**: New Service → Database → RabbitMQ
2. **Add Redis**: New Service → Database → Redis

### Step 3: Deploy FastAPI Service
1. New Service → GitHub Repo
2. Set **Root Directory**: `backendAndUI/python_worker`
3. Set **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 4: Deploy Worker Service
1. New Service → GitHub Repo (same repo)
2. Set **Root Directory**: `backendAndUI/python_worker`  
3. Set **Start Command**: `python -m app.worker`
4. **Disable Health Check** (workers don't need HTTP)

### Step 5: Configure Environment Variables

**For FastAPI Service:**
```bash
PORT=8000
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
OPENAI_API_KEY=your-openai-key
RABBITMQ_HOST=${{RabbitMQ.RABBITMQ_HOST}}
RABBITMQ_PORT=${{RabbitMQ.RABBITMQ_PORT}}
RABBITMQ_USER=${{RabbitMQ.RABBITMQ_USER}}
RABBITMQ_PASS=${{RabbitMQ.RABBITMQ_PASSWORD}}
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}
```

**For Worker Service:**
```bash
# Same variables as FastAPI service
```

## 🔧 Neo4j Options

### Option A: Neo4j AuraDB (Recommended)
1. Sign up at [neo4j.com/aura](https://neo4j.com/aura)
2. Create a free database
3. Copy the connection URI
4. Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

### Option B: Self-hosted Neo4j
1. Deploy Neo4j on another cloud provider
2. Or use Railway's custom Dockerfile (see full guide)

## 💰 Cost Breakdown

**Railway Pricing:**
- **Services**: $5/month per service (FastAPI + Worker = $10/month)
- **RabbitMQ**: ~$5/month (managed service)
- **Redis**: ~$5/month (managed service)
- **Total**: ~$20/month

**Neo4j AuraDB:**
- **Free tier**: 50k nodes, 175k relationships
- **Paid**: $65/month for production

## 🐛 Troubleshooting

### Worker Not Processing Jobs
```bash
# Check worker logs
railway logs --service worker

# Check if RabbitMQ is connected
railway logs --service worker | grep "Connected to RabbitMQ"
```

### FastAPI Not Starting
```bash
# Check build logs
railway logs --service fastapi

# Check environment variables
railway variables --service fastapi
```

### Redis Connection Errors
- Verify `REDIS_PASSWORD` is set
- Check SSL settings (auto-handled by code)

## 📊 Monitoring

### Railway Dashboard
- View service status and logs
- Monitor resource usage
- Check deployment history

### Application Health
```bash
# Health check
curl https://your-app.railway.app/health

# Job status
curl https://your-app.railway.app/api/ingest/jobs
```

## 🔄 Scaling

### Add More Workers
1. Duplicate the worker service in Railway
2. Each worker connects to the same RabbitMQ queue
3. Jobs automatically distribute across workers

### Resource Limits
- Set CPU/memory limits in Railway dashboard
- Monitor usage and adjust as needed

## 🚨 Important Notes

1. **Environment Variables**: Must be set in **both** FastAPI and Worker services
2. **SSL**: Code automatically handles SSL for Railway managed services
3. **Ports**: Railway sets `$PORT` automatically
4. **Logs**: Use `railway logs --follow` for real-time monitoring
5. **Restarts**: Services auto-restart on failure

## 📚 Files Created for Railway

- `railway.json` - Railway configuration
- `Procfile` - FastAPI startup command
- `Procfile.worker` - Worker startup command
- `deploy_to_railway.ps1` - Windows deployment script
- `deploy_to_railway.sh` - Linux/Mac deployment script
- `RAILWAY_DEPLOYMENT_GUIDE.md` - Detailed guide

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ FastAPI service shows "Deployed" in Railway dashboard
2. ✅ Worker service shows "Deployed" and logs show "Connected to RabbitMQ"
3. ✅ Health endpoint returns 200: `curl https://your-app.railway.app/health`
4. ✅ Text ingestion returns job ID: `curl -X POST .../api/ingest/text_async`
5. ✅ Job status shows "completed" after processing

## 🆘 Need Help?

1. **Check logs**: `railway logs --service [service-name]`
2. **Verify variables**: `railway variables --service [service-name]`
3. **Test locally first**: Use `docker-compose up` to test locally
4. **Railway docs**: https://docs.railway.app
5. **Railway Discord**: https://discord.gg/railway

---

**Ready to deploy?** Run the deployment script and follow the prompts! 🚀

