from fastapi import APIRouter, HTTPException

from ..services.preprocess import extract_text_from_path, HARD_CODED_INPUT


router = APIRouter()


@router.api_route("/run", methods=["GET", "POST"])
def run_preprocess():
    try:
        text = extract_text_from_path(HARD_CODED_INPUT)
        # Return small preview to avoid large payloads
        preview = text[:500]
        return {"bytes": len(text.encode("utf-8")), "preview": preview}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Missing input file: {HARD_CODED_INPUT}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


