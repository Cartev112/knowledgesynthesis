# Deploying to Render

This guide walks you through deploying the Knowledge Synthesis backend to Render.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **Neo4j Aura Account**: Sign up at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura) (free tier available)
3. **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com)
4. **GitHub Repository**: Push your code to GitHub

## Step 1: Prepare Neo4j Database

1. Go to [Neo4j Aura Console](https://console.neo4j.io/)
2. Create a **Free** AuraDB instance
3. **Save the credentials** shown after creation:
   - Connection URI (e.g., `neo4j+s://xxxxx.databases.neo4j.io`)
   - Username (usually `neo4j`)
   - Password (auto-generated)
4. Wait for the instance to be ready (takes 1-2 minutes)

## Step 2: Push Code to GitHub

```bash
cd knowledgesynthesis
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

## Step 3: Create Python Backend Service on Render

### 3.1 Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `knowledge-synthesis-api`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend/python_worker`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r ../../requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free` (or `Starter` for better performance)

### 3.2 Add Environment Variables

Click **"Environment"** tab and add:

```
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_DRY_RUN=false
NODE_PORT=3000
NODE_SERVER=https://your-node-server.onrender.com
SESSION_SECRET=your-random-secret-here-change-this
```

**Important**: 
- Replace `NEO4J_PASSWORD` with your Neo4j Aura password
- Replace `OPENAI_API_KEY` with your OpenAI key
- Replace `SESSION_SECRET` with a random string (use `openssl rand -hex 32`)
- `NODE_SERVER` URL will be added after Step 4

### 3.3 Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete (5-10 minutes)
3. Once deployed, note your service URL: `https://knowledge-synthesis-api.onrender.com`

## Step 4: Create Node.js Server on Render

### 4.1 Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect the same GitHub repository
3. Configure:
   - **Name**: `knowledge-synthesis-node`
   - **Region**: Same as Python service
   - **Branch**: `main`
   - **Root Directory**: `node-server`
   - **Runtime**: `Node`
   - **Build Command**: `npm install`
   - **Start Command**: `node server.js`
   - **Instance Type**: `Free`

### 4.2 Add Environment Variables

```
NODE_PORT=10000
FASTAPI_BASE=https://knowledge-synthesis-api.onrender.com
SESSION_SECRET=same-secret-as-python-service
LOGIN_USER=admin
LOGIN_PASS=change-this-admin-password
```

**Important**: Use the same `SESSION_SECRET` as the Python service

### 4.3 Deploy

1. Click **"Create Web Service"**
2. Wait for deployment
3. Note your service URL: `https://knowledge-synthesis-node.onrender.com`

## Step 5: Update Environment Variables

### Update Python Backend

Go back to the Python service and update:
```
NODE_SERVER=https://knowledge-synthesis-node.onrender.com
```

This will trigger a redeploy.

## Step 6: Initialize Neo4j Database

After both services are deployed:

1. Go to your Python service URL: `https://knowledge-synthesis-api.onrender.com/health`
2. You should see: `{"status":"healthy"}`
3. Check Neo4j connection: `https://knowledge-synthesis-api.onrender.com/db/status`

If you need to run the initialization script:

```bash
# Update the script to use your Render service URL
python scripts/apply_neo4j_init.py
```

Or manually run the Cypher from `db/neo4j/init.cypher` in Neo4j Aura Browser.

## Step 7: Access Your Application

1. **Main Application**: `https://knowledge-synthesis-api.onrender.com/app`
2. **Login Page**: `https://knowledge-synthesis-api.onrender.com/login`
3. **API Docs**: `https://knowledge-synthesis-api.onrender.com/docs`
4. **Review Queue**: `https://knowledge-synthesis-api.onrender.com/review-ui`

## Step 8: Create Admin Account

1. Go to: `https://knowledge-synthesis-api.onrender.com/signup`
2. Create your account with:
   - First Name
   - Last Name
   - Email
   - Password
3. Login at: `https://knowledge-synthesis-api.onrender.com/login`

## Troubleshooting

### Service Won't Start

**Check Logs:**
1. Go to Render Dashboard
2. Click on your service
3. Click "Logs" tab
4. Look for error messages

**Common Issues:**

1. **Module not found**: Check that `requirements.txt` is in the root directory
2. **Neo4j connection failed**: Verify NEO4J_URI, USERNAME, PASSWORD
3. **Port binding error**: Render uses `$PORT` environment variable automatically

### Neo4j Connection Issues

1. **Verify credentials** in Neo4j Aura Console
2. **Check connection string** - must start with `neo4j+s://` for Aura
3. **Whitelist IPs**: Neo4j Aura free tier allows all IPs by default

### Environment Variables Not Working

1. **Restart service** after adding/updating env vars
2. **Check spelling** - env var names are case-sensitive
3. **No quotes** - Don't wrap values in quotes in Render UI

## Performance Notes

### Free Tier Limitations

- **Spin down after 15 minutes** of inactivity
- **First request after spin-down** takes 30-60 seconds
- **750 hours/month** free (shared across all free services)

### Upgrade to Starter ($7/month per service) for:
- **No spin-down**
- **Faster performance**
- **More memory and CPU**

## Monitoring

### View Logs
```
Render Dashboard → Service → Logs
```

### Health Checks
- Python API: `https://your-api.onrender.com/health`
- Neo4j Status: `https://your-api.onrender.com/db/status`

## Security Checklist

- [ ] Change `SESSION_SECRET` to a strong random value
- [ ] Change `LOGIN_PASS` from default
- [ ] Use strong Neo4j password
- [ ] Rotate OpenAI API keys periodically
- [ ] Enable HTTPS (automatic on Render)
- [ ] Review Neo4j Aura security settings

## Updating Your Deployment

To deploy updates:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render will automatically detect the push and redeploy.

## Cost Estimate

- **Neo4j Aura Free**: $0/month (limited to 200k nodes + relationships)
- **Render Free Tier**: $0/month (with limitations)
- **OpenAI API**: Pay per use (~$0.10-1.00 per document depending on size)

**Total**: Free for development/testing, ~$15-30/month for production (Starter tier + Neo4j Professional)

## Support

If you encounter issues:
1. Check Render logs
2. Check Neo4j Aura console
3. Verify all environment variables
4. Test locally first with production settings

