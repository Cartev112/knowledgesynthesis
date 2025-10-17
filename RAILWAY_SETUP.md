# Railway Deployment Guide - Knowledge Synthesis Platform

## Architecture Overview

The platform consists of **TWO separate services** on Railway:

1. **Python Backend** (FastAPI) - Handles knowledge extraction, Neo4j queries
2. **Node Frontend** (Express) - Serves UI, handles authentication, proxies API requests

## Step 1: Deploy Python Backend Service

### 1.1 Create Python Service
1. Go to Railway dashboard
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect it as a Python project

### 1.2 Configure Python Service
Set these environment variables in Railway:

```bash
# Neo4j Aura Connection
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-aura-password
NEO4J_DATABASE=neo4j

# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Service Config
PORT=8000
```

### 1.3 Set Root Directory
In Railway settings:
- **Root Directory**: Leave empty (uses repository root)
- **Start Command**: `cd backendAndUI/python_worker && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 1.4 Get Python Service URL
After deployment, Railway will give you a URL like:
- `https://your-python-service.up.railway.app`
- **Save this URL** - you'll need it for the Node service

---

## Step 2: Deploy Node Frontend Service

### 2.1 Create Node Service
1. In the **same Railway project**, click "New Service"
2. Select "GitHub Repo" again (same repository)
3. Railway will create a second service

### 2.2 Configure Node Service
Set these environment variables:

```bash
# Backend Connection (CRITICAL!)
FASTAPI_BASE=https://your-python-service.up.railway.app

# Node Server Config
NODE_PORT=3000
PORT=3000

# Session Security
SESSION_SECRET=your-random-secret-here-change-me

# Default Admin Account
LOGIN_USER=admin
LOGIN_PASS=your-admin-password
```

**IMPORTANT**: Replace `https://your-python-service.up.railway.app` with the actual URL from Step 1.4!

### 2.3 Set Root Directory
In Railway settings:
- **Root Directory**: `node-server`
- **Start Command**: `node server.js`

### 2.4 Get Node Service URL
After deployment, Railway will give you a URL like:
- `https://your-node-service.up.railway.app`
- **This is your application URL** - share this with users

---

## Step 3: Verify Deployment

### 3.1 Check Python Backend
Visit: `https://your-python-service.up.railway.app/health`

Should return:
```json
{"status": "healthy"}
```

### 3.2 Check Node Frontend
Visit: `https://your-node-service.up.railway.app/login`

Should show the login page.

### 3.3 Test Full Stack
1. Login with your admin credentials
2. Go to "Viewing" tab
3. Graph should load from Neo4j
4. Try uploading a document in "Ingestion" tab

---

## Common Issues & Solutions

### Issue 1: "ECONNREFUSED 127.0.0.1:8000"
**Problem**: Node service is trying to connect to localhost instead of the Python service.

**Solution**: 
- Check that `FASTAPI_BASE` environment variable is set in Node service
- Make sure it points to the **Railway URL** of the Python service, not localhost
- Format: `https://your-python-service.up.railway.app` (no trailing slash)

### Issue 2: "Neo4j Authentication Failed"
**Problem**: Can't connect to Neo4j Aura.

**Solution**:
- Verify `NEO4J_URI` uses `neo4j+s://` protocol (not `bolt://`)
- Check password is correct (from Aura credentials file)
- Ensure Aura instance is running

### Issue 3: "Module not found" errors
**Problem**: Missing dependencies.

**Solution**:
- Ensure `package.json` is in `node-server/` directory
- Ensure `requirements.txt` is in repository root
- Check Railway build logs for errors

### Issue 4: Services can't communicate
**Problem**: Node can't reach Python service.

**Solution**:
- Both services must be in the **same Railway project**
- Use the **public Railway URL** for `FASTAPI_BASE`, not internal networking
- Railway doesn't support private networking on free tier

---

## Environment Variables Summary

### Python Backend Service
```bash
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
PORT=8000
```

### Node Frontend Service
```bash
FASTAPI_BASE=https://your-python-service.up.railway.app
NODE_PORT=3000
PORT=3000
SESSION_SECRET=random-secret-string
LOGIN_USER=admin
LOGIN_PASS=admin-password
```

---

## Deployment Checklist

- [ ] Neo4j Aura instance created and running
- [ ] Neo4j credentials saved
- [ ] OpenAI API key obtained
- [ ] Python backend service deployed on Railway
- [ ] Python service environment variables set
- [ ] Python service health check passing
- [ ] Python service URL saved
- [ ] Node frontend service deployed on Railway
- [ ] Node service environment variables set (especially `FASTAPI_BASE`)
- [ ] Node service root directory set to `node-server`
- [ ] Node service health check passing
- [ ] Login page accessible
- [ ] Graph loads successfully
- [ ] Document ingestion works

---

## Monitoring & Logs

### View Logs
In Railway dashboard:
1. Click on a service
2. Go to "Deployments" tab
3. Click on latest deployment
4. View build and runtime logs

### Check Service Health
- Python: `https://your-python-service.up.railway.app/health`
- Node: `https://your-node-service.up.railway.app/` (should show login)

### Debug Connection Issues
Check Node service logs for:
```
Proxying GET /query/documents to http://...
```

The URL should be your Railway Python service URL, NOT `127.0.0.1:8000`!

---

## Cost Optimization

Railway free tier includes:
- $5 credit per month
- Sleeps after 30 min of inactivity

To optimize:
1. Use Neo4j Aura free tier (shared instance)
2. Use `gpt-4o-mini` model (cheaper than GPT-4)
3. Set reasonable limits on extraction (max 100 concepts)
4. Services will auto-sleep when not in use

---

## Next Steps After Deployment

1. **Create your first user**: Use signup page or set `LOGIN_USER`/`LOGIN_PASS` env vars
2. **Upload test document**: Try the ingestion tab
3. **Explore the graph**: Use the viewing tab
4. **Share the URL**: Give users the Node service URL

---

## Support

If you encounter issues:
1. Check Railway logs for both services
2. Verify all environment variables are set correctly
3. Test each service independently (health endpoints)
4. Ensure Neo4j Aura is accessible
5. Check that `FASTAPI_BASE` points to the correct Railway URL

**The most common issue is forgetting to set `FASTAPI_BASE` in the Node service!**
