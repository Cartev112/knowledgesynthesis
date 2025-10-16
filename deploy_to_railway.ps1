# Railway Deployment Script for Knowledge Synthesis
# This script helps deploy the async ingestion system to Railway

Write-Host "🚂 Railway Deployment Script for Knowledge Synthesis" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Railway CLI is installed
try {
    railway --version | Out-Null
    Write-Host "✅ Railway CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Railway CLI is not installed." -ForegroundColor Red
    Write-Host "Please install it first:" -ForegroundColor Yellow
    Write-Host "  npm install -g @railway/cli" -ForegroundColor White
    Write-Host "  or" -ForegroundColor White
    Write-Host "  curl -fsSL https://railway.app/install.sh | sh" -ForegroundColor White
    exit 1
}

# Check if user is logged in
try {
    railway whoami | Out-Null
    Write-Host "✅ Logged in to Railway" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in to Railway." -ForegroundColor Red
    Write-Host "Please log in first:" -ForegroundColor Yellow
    Write-Host "  railway login" -ForegroundColor White
    exit 1
}

# Create or select project
Write-Host ""
Write-Host "📋 Setting up Railway project..." -ForegroundColor Cyan
Write-Host "1. Create new project" -ForegroundColor White
Write-Host "2. Use existing project" -ForegroundColor White
$choice = Read-Host "Choose option (1 or 2)"

if ($choice -eq "1") {
    Write-Host "Creating new Railway project..." -ForegroundColor Yellow
    railway project new
} else {
    Write-Host "Available projects:" -ForegroundColor Yellow
    railway projects
    $project_name = Read-Host "Enter project name or ID"
    railway project select $project_name
}

Write-Host ""
Write-Host "🔧 Setting up services..." -ForegroundColor Cyan

# Add RabbitMQ service
Write-Host "Adding RabbitMQ service..." -ForegroundColor Yellow
railway add rabbitmq

# Add Redis service  
Write-Host "Adding Redis service..." -ForegroundColor Yellow
railway add redis

# Deploy FastAPI service
Write-Host ""
Write-Host "🚀 Deploying FastAPI service..." -ForegroundColor Yellow
railway up --service fastapi

# Deploy Worker service
Write-Host ""
Write-Host "👷 Deploying Worker service..." -ForegroundColor Yellow
railway up --service worker

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Set environment variables in Railway dashboard" -ForegroundColor White
Write-Host "2. Configure Neo4j connection" -ForegroundColor White
Write-Host "3. Test the deployment" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Useful commands:" -ForegroundColor Cyan
Write-Host "  railway status                    # Check service status" -ForegroundColor White
Write-Host "  railway logs --service fastapi    # View FastAPI logs" -ForegroundColor White
Write-Host "  railway logs --service worker     # View worker logs" -ForegroundColor White
Write-Host "  railway variables                 # View environment variables" -ForegroundColor White
Write-Host ""
Write-Host "📖 For detailed setup instructions, see:" -ForegroundColor Cyan
Write-Host "  RAILWAY_DEPLOYMENT_GUIDE.md" -ForegroundColor White

