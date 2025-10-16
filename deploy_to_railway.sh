#!/bin/bash

# Railway Deployment Script for Knowledge Synthesis
# This script helps deploy the async ingestion system to Railway

echo "🚂 Railway Deployment Script for Knowledge Synthesis"
echo "=================================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed."
    echo "Please install it first:"
    echo "  npm install -g @railway/cli"
    echo "  or"
    echo "  curl -fsSL https://railway.app/install.sh | sh"
    exit 1
fi

echo "✅ Railway CLI found"

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway."
    echo "Please log in first:"
    echo "  railway login"
    exit 1
fi

echo "✅ Logged in to Railway"

# Create or select project
echo ""
echo "📋 Setting up Railway project..."
echo "1. Create new project"
echo "2. Use existing project"
read -p "Choose option (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo "Creating new Railway project..."
    railway project new
else
    echo "Available projects:"
    railway projects
    read -p "Enter project name or ID: " project_name
    railway project select "$project_name"
fi

echo ""
echo "🔧 Setting up services..."

# Add RabbitMQ service
echo "Adding RabbitMQ service..."
railway add rabbitmq

# Add Redis service  
echo "Adding Redis service..."
railway add redis

# Deploy FastAPI service
echo ""
echo "🚀 Deploying FastAPI service..."
railway up --service fastapi

# Deploy Worker service
echo ""
echo "👷 Deploying Worker service..."
railway up --service worker

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set environment variables in Railway dashboard"
echo "2. Configure Neo4j connection"
echo "3. Test the deployment"
echo ""
echo "🔗 Useful commands:"
echo "  railway status                    # Check service status"
echo "  railway logs --service fastapi    # View FastAPI logs"
echo "  railway logs --service worker     # View worker logs"
echo "  railway variables                 # View environment variables"
echo ""
echo "📖 For detailed setup instructions, see:"
echo "  RAILWAY_DEPLOYMENT_GUIDE.md"

