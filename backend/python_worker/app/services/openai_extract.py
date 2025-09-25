from __future__ import annotations

import json
from typing import List

from fastapi import HTTPException

from ..core.settings import settings
from ..models.triplet import Triplet, TripletExtractionResult


PROMPT = (
    "You are an information extraction assistant. Extract factual triplets from the given text. "
    "Return ONLY a JSON object with a single field 'triplets' which is an array of objects, "
    "each with keys: subject, predicate, object, and optional subject_type, object_type, original_text."
)


def _fake_extract(text: str) -> TripletExtractionResult:
    # Deterministic placeholder for no-key environments
    demo = [
        Triplet(
            subject="Vemurafenib",
            predicate="targets",
            object="BRAF V600E",
            subject_type="Drug",
            object_type="GeneMutation",
            original_text="Vemurafenib targets the BRAF V600E mutation in melanoma.",
        )
    ]
    return TripletExtractionResult(triplets=demo, model="dry-run", tokens_used=0)


def extract_triplets(text: str) -> TripletExtractionResult:
    if settings.openai_dry_run or not settings.openai_api_key:
        return _fake_extract(text)

    try:
        # Lazy import to avoid hard dependency if not used
        import os
        import httpx
        from openai import OpenAI

        # Honor proxy environment variables without using unsupported kwargs
        proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("OPENAI_PROXY")
        http_client = None
        if proxy_url:
            http_client = httpx.Client(proxies=proxy_url, timeout=60.0)

        client = OpenAI(api_key=settings.openai_api_key, http_client=http_client) if http_client else OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        raw_triplets = data.get("triplets", [])
        triplets = [Triplet.model_validate(t) for t in raw_triplets]
        tokens_used = getattr(response.usage, "total_tokens", None)
        return TripletExtractionResult(triplets=triplets, model=settings.openai_model, tokens_used=tokens_used)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI extraction failed: {exc}")


