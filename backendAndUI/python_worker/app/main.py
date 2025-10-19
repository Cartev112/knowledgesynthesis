from fastapi import FastAPI
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting Knowledge Synthesis Worker...")

from .routes.health import router as health_router
from .routes.db import router as db_router
from .routes.preprocess import router as preprocess_router
from .routes.extract import router as extract_router
from .routes.ingest import router as ingest_router
from .routes.ingest_async import router as ingest_async_router
from .routes.config import router as config_router
from .routes.query import router as query_router
from .routes.ui import router as ui_router
from .routes.cytoscape_viewer import router as cytoscape_viewer_router
from .routes.review import router as review_router
from .routes.review_ui import router as review_ui_router
from .routes.auth import router as auth_router
from .routes.main_ui import router as main_ui_router
from .routes.export import router as export_router
from .routes.manual import router as manual_router
from .routes.pathway import router as pathway_router
from .routes.comments import router as comments_router
from .routes.discovery import router as discovery_router
from .routes.discovery_ui import router as discovery_ui_router


app = FastAPI(title="Knowledge Synthesis Worker", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Knowledge Synthesis Worker - Application Starting")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 60)
    logger.info("Knowledge Synthesis Worker - Application Shutting Down")
    logger.info("=" * 60)


# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    import time
    start_time = time.time()
    
    logger.info(f"→ {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"← {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}s)")
    
    return response


@app.get("/")
def root():
    """Redirect to login page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")


@app.get("/login")
def login_redirect():
    """Redirect to auth login."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/auth/login")


@app.get("/signup")
def signup_redirect():
    """Redirect to auth signup."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/auth/signup")


app.include_router(health_router, prefix="/health", tags=["health"]) 
app.include_router(db_router, prefix="/db", tags=["db"]) 
app.include_router(preprocess_router, prefix="/preprocess", tags=["preprocess"]) 
app.include_router(extract_router, prefix="/extract", tags=["extract"]) 
app.include_router(ingest_router, prefix="/ingest", tags=["ingest"]) 
app.include_router(ingest_async_router, prefix="/api/ingest", tags=["ingest-async"])
app.include_router(config_router, prefix="/config", tags=["config"]) 
app.include_router(query_router, prefix="/query", tags=["query"]) 
app.include_router(ui_router, prefix="/neo4j-viewer", tags=["ui"]) 
app.include_router(cytoscape_viewer_router, prefix="/viewer", tags=["ui"])
app.include_router(review_router, prefix="/review", tags=["review"])
app.include_router(review_ui_router, prefix="/review-ui", tags=["ui"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(main_ui_router, prefix="/app", tags=["ui"])
app.include_router(export_router, prefix="/api/export", tags=["export"])
app.include_router(manual_router, prefix="/api/manual", tags=["manual"])
app.include_router(pathway_router, prefix="/api/pathway", tags=["pathway"]) 
app.include_router(comments_router, tags=["comments"])
app.include_router(discovery_router, prefix="/api/discovery", tags=["discovery"])
app.include_router(discovery_ui_router, tags=["ui"])
