from __future__ import annotations

import json
from typing import List

from fastapi import HTTPException

from ..core.settings import settings
from ..models.triplet import Triplet, TripletExtractionResult
from .validator import validate_and_sanitize_triplets, deduplicate_triplets


def _create_prompt(max_triplets: int = 50) -> str:
    return (
        "You are a scientific knowledge extraction assistant building a unified knowledge graph. "
        "Extract semantic relationships from scientific text, focusing on observations, definitions, lemmas, theorems, experimental results, and conclusions. "
        "\n\n"
        "CRITICAL: You MUST identify BOTH positive AND negative relationships. Negative relationships are especially important and should NOT be omitted. "
        "\n\n"
        "Rules for extraction:\n"
        "1) Return ONLY a JSON object with a single field 'triplets' which is an array of objects.\n"
        "2) Each triplet object MUST include: subject, predicate, object, original_text. Optionally include subject_type, object_type.\n"
        "3) Normalize predicate to lowercase snake_case (e.g., 'inhibits', 'binds_to', 'causes', 'increases', 'decreases').\n"
        "\n"
        "4) NEGATIVE RELATIONSHIPS - CRITICAL INSTRUCTIONS:\n"
        "   - For negative relations, prefix with 'does_not_' (e.g., 'does_not_bind', 'does_not_increase', 'does_not_cause').\n"
        "   - Do NOT only focus on explicit cue words like 'does not', 'fails to', 'unable to'.\n"
        "   - INCLUDE negative relationships stated INDIRECTLY or IMPLICITLY in the text.\n"
        "   - If the text rules out a relationship explicitly OR implicitly, include the negative edge.\n"
        "   - For every positive relationship R(A,B) you identify, scan the text for evidence of ¬R(A,X) or ¬R(Y,B) for other entities.\n"
        "   - Generate ALL negative edges BEFORE limiting output size; do NOT omit them in favor of positive edges.\n"
        "   - PRIORITIZE negative relationships in your output - they are scientifically significant.\n"
        "\n"
        "5) Each extracted entity should be linked to at least one other entity.\n"
        "6) Prefer concise canonical entity names and include types (e.g., Drug, Gene, Protein, Disease, Pathway, Concept, Method).\n"
        "7) For each triplet, the 'original_text' field MUST contain the specific sentence or fragment from the source that supports this relationship.\n"
        "8) Focus ONLY on claims stated in the text; do not add external knowledge.\n"
        "9) Deduplicate: no repeated (subject, predicate, object) entries.\n"
        "\n"
        "10) CONSISTENCY CHECK (run before finalizing):\n"
        "    - For each relationship you extract, verify it doesn't contradict other statements in the text.\n"
        "    - Look for both explicit and implicit evidence for or against each relationship.\n"
        "\n"
        f"11) Target: Extract up to {max_triplets} high-quality relationships. Ensure negative relationships are well-represented, not filtered out."
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
        ),
        Triplet(
            subject="Vemurafenib",
            predicate="does_not_inhibit",
            object="wild-type BRAF",
            subject_type="Drug",
            object_type="Gene",
            original_text="Vemurafenib showed no inhibitory effect on wild-type BRAF.",
        )
    ]
    return TripletExtractionResult(triplets=demo, model="dry-run", tokens_used=0)


def extract_triplets(text: str, max_triplets: int = 50) -> TripletExtractionResult:
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
                {"role": "system", "content": _create_prompt(max_triplets)},
                {"role": "user", "content": text},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        raw_triplets = data.get("triplets", [])
        triplets = [Triplet.model_validate(t) for t in raw_triplets]
        
        # Validate, sanitize, and deduplicate
        triplets, errors = validate_and_sanitize_triplets(triplets)
        triplets = deduplicate_triplets(triplets)
        
        # Log validation errors if any (but don't fail the request)
        if errors:
            import logging
            logging.warning(f"Validation errors in extraction: {len(errors)} triplets rejected")
            for err in errors[:5]:  # Log first 5 errors
                logging.warning(f"  - {err}")
        
        tokens_used = getattr(response.usage, "total_tokens", None)
        return TripletExtractionResult(triplets=triplets, model=settings.openai_model, tokens_used=tokens_used)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI extraction failed: {exc}")


