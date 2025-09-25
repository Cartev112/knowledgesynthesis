from fastapi import FastAPI

from .routes.health import router as health_router
from .routes.db import router as db_router
from .routes.preprocess import router as preprocess_router
from .routes.extract import router as extract_router
from .routes.extract_graph import router as extract_graph_router
from .routes.ingest import router as ingest_router
from .routes.config import router as config_router
from .routes.query import router as query_router
from .routes.ui import router as ui_router
from .routes.process import router as process_router
from .routes.mermaid_viewer import router as mermaid_viewer_router
from .routes.cytoscape_viewer import router as cytoscape_viewer_router


app = FastAPI(title="Knowledge Synthesis Worker", version="0.1.0")


@app.get("/")
def root():
    return {"status": "ok"}


app.include_router(health_router, prefix="/health", tags=["health"]) 
app.include_router(db_router, prefix="/db", tags=["db"]) 
app.include_router(process_router, prefix="/process", tags=["process"])
app.include_router(preprocess_router, prefix="/preprocess", tags=["preprocess"]) 
app.include_router(extract_router, prefix="/extract", tags=["extract"]) 
app.include_router(extract_graph_router, prefix="/extract/graph", tags=["extract"])
app.include_router(ingest_router, prefix="/ingest", tags=["ingest"]) 
app.include_router(config_router, prefix="/config", tags=["config"]) 
app.include_router(query_router, prefix="/query", tags=["query"]) 
app.include_router(ui_router, prefix="/neo4j-viewer", tags=["ui"]) 
app.include_router(mermaid_viewer_router, prefix="/mermaid", tags=["ui"])
app.include_router(cytoscape_viewer_router, prefix="/viewer", tags=["ui"]) 

