from fastapi import FastAPI

from .routes.health import router as health_router
from .routes.db import router as db_router
from .routes.preprocess import router as preprocess_router
from .routes.extract import router as extract_router
from .routes.ingest import router as ingest_router
from .routes.config import router as config_router
from .routes.query import router as query_router
from .routes.ui import router as ui_router
from .routes.cytoscape_viewer import router as cytoscape_viewer_router
from .routes.review import router as review_router
from .routes.review_ui import router as review_ui_router
from .routes.auth import router as auth_router
from .routes.main_ui import router as main_ui_router


app = FastAPI(title="Knowledge Synthesis Worker", version="0.1.0")


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
app.include_router(config_router, prefix="/config", tags=["config"]) 
app.include_router(query_router, prefix="/query", tags=["query"]) 
app.include_router(ui_router, prefix="/neo4j-viewer", tags=["ui"]) 
app.include_router(cytoscape_viewer_router, prefix="/viewer", tags=["ui"])
app.include_router(review_router, prefix="/review", tags=["review"])
app.include_router(review_ui_router, prefix="/review-ui", tags=["ui"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(main_ui_router, prefix="/app", tags=["ui"]) 

