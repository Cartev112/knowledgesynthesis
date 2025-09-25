from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.preprocess import extract_text_from_path, HARD_CODED_INPUT
from ..services.openai_extract import extract_triplets


router = APIRouter()


@router.api_route("/run", methods=["GET", "POST"])
def run_extract():
    try:
        text = extract_text_from_path(HARD_CODED_INPUT)
        result = extract_triplets(text)
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class ExtractTextRequest(BaseModel):
    text: str


@router.post("/text")
def extract_from_text(payload: ExtractTextRequest):
    try:
        result = extract_triplets(payload.text)
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


