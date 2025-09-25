from fastapi import APIRouter, Body
from pydantic import BaseModel
from ..services.openai_graph_extract import extract_graph

router = APIRouter()

class GraphExtractRequest(BaseModel):
    text: str
    filename: str = "source.pdf"

@router.post("")
def extract_mermaid_graph(req: GraphExtractRequest = Body(...)):
    """Extract a Mermaid graph from a given text using a detailed prompt."""
    graph_string = extract_graph(req.text, req.filename)
    return {"graph": graph_string}


