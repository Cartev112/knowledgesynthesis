from fastapi import APIRouter, File, UploadFile, HTTPException
from pypdf import PdfReader
import io
import re
import os
import json
import hashlib
from ..services.openai_graph_extract import extract_graph
from ..services.graph_json import mermaid_to_json

router = APIRouter()

def _cleanup_mermaid_string(graph_string: str) -> str:
    """Applies a series of cleanup operations to the raw LLM output."""
    # Remove the word "mermaid" and any markdown fences
    graph_string = graph_string.strip()
    if graph_string.lower().startswith("mermaid"):
        graph_string = graph_string[len("mermaid"):].strip()
    if graph_string.startswith("```"):
        graph_string = graph_string.strip("```").strip("mermaid").strip()

    # Correct common node syntax errors, e.g., NodeId(Label) -> NodeId["Label"]
    lines = graph_string.split('\n')
    corrected_lines = []
    # This regex finds node IDs followed by parentheses, typical for declarations
    node_def_pattern = re.compile(r'^\s*([a-zA-Z0-9_]+)\s*\(([^)]+)\)\s*(<!--.*-->)?\s*$')

    for line in lines:
        # Strip any HTML-style comments, as they can break the parser
        line = re.sub(r'<!--.*?-->', '', line).strip()
        if '-->' not in line and '-.->' not in line and not line.strip().startswith('graph'):
            line = node_def_pattern.sub(r'\1["\2"]', line)
        corrected_lines.append(line)
    
    return '\n'.join(corrected_lines)

@router.post("/pdf-to-mermaid")
async def process_pdf_to_mermaid(file: UploadFile = File(...)):
    """
    Accepts a PDF file, extracts text, generates a Mermaid graph, and returns it.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        pdf_bytes = await file.read()

        # Disk cache keyed by SHA-256 of file bytes
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cache_dir = os.path.join(app_dir, ".cache", "graphs")
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{sha256}.json")

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                # Return cached result
                return {"graph": cached.get("graph", ""), "filename": cached.get("filename", file.filename or "uploaded_file.pdf")}
            except Exception:
                # If cache read fails, fall through to reprocess
                pass

        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the PDF.")

        # The filename is passed to the LLM for citations in the graph
        filename = file.filename or "uploaded_file.pdf"
        
        raw_graph_string = extract_graph(text, filename)
        clean_graph_string = _cleanup_mermaid_string(raw_graph_string)
        
        # Write to cache (best-effort)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"graph": clean_graph_string, "filename": filename, "sha256": sha256}, f, ensure_ascii=False)
        except Exception:
            pass
        
        return {"graph": clean_graph_string, "filename": filename}

    except HTTPException as e:
        # Re-raise HTTP exceptions to return proper error responses
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@router.post("/pdf-to-graphjson")
async def process_pdf_to_graphjson(file: UploadFile = File(...)):
    """
    Accepts a PDF file, extracts text, generates a Mermaid graph, converts to JSON graph, and returns it.
    Uses the same disk cache (keyed by file bytes) but stores JSON graph alongside Mermaid.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        pdf_bytes = await file.read()

        # Disk cache keyed by SHA-256 of file bytes
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cache_dir = os.path.join(app_dir, ".cache", "graphs")
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{sha256}.json")

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if "graph_json" in cached and cached.get("graph_json"):
                    return {"graph": cached["graph_json"], "filename": cached.get("filename", file.filename or "uploaded_file.pdf")}
            except Exception:
                pass

        # Extract text
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the PDF.")

        filename = file.filename or "uploaded_file.pdf"
        raw_graph_string = extract_graph(text, filename)
        clean_graph_string = _cleanup_mermaid_string(raw_graph_string)
        graph_json = mermaid_to_json(clean_graph_string)

        # Cache both formats
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({
                    "graph": clean_graph_string,
                    "graph_json": graph_json,
                    "filename": filename,
                    "sha256": sha256
                }, f, ensure_ascii=False)
        except Exception:
            pass

        return {"graph": graph_json, "filename": filename}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
