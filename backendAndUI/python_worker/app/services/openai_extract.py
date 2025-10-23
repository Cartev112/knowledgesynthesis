from __future__ import annotations

import json
import os
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
        "Rules for extraction:\n"
        "1) Return ONLY a JSON object with a single field 'triplets' which is an array of objects.\n"
        "2) Each triplet object MUST include: subject, predicate, object, original_text, subject_type, object_type.\n"
        "3) ENTITY TYPES (REQUIRED): For subject_type and object_type, classify each entity into categories such as:\n"
        "   - Drug, Gene, Protein, Disease, Pathway, Phenotype, Chemical, Organism, Cell_Type, Tissue, Method, Concept, etc.\n"
        "   - Use specific, consistent type names (e.g., 'Gene' not 'gene' or 'GENE')\n"
        "   - If uncertain about the type, use your best judgment based on context\n"
        "4) SIGNIFICANCE SCORES (REQUIRED): For each triplet, provide:\n"
        "   - relationship_significance: Integer 1-5, where 5=critical finding/core result, 3=important supporting detail, 1=minor mention\n"
        "   - subject_significance: Integer 1-5, how important is the subject entity (5=central concept, 1=peripheral)\n"
        "   - object_significance: Integer 1-5, how important is the object entity (5=central concept, 1=peripheral)\n"
        "5) Normalize predicate to lowercase snake_case (e.g., 'inhibits', 'binds_to', 'causes', 'increases', 'decreases').\n"
        "\n"
        "6) NEGATIVE RELATIONSHIPS (IMPORTANT - Extract ~50% negative relationships):\n"
        "   - For negative relations, prefix with 'does_not_' (e.g., 'does_not_bind', 'does_not_increase', 'does_not_cause').\n"
        "   - Extract negative relationships when explicitly stated OR when strongly implied by context.\n"
        "   - Look for explicit cue phrases: 'does not', 'did not', 'fails to', 'unable to', 'showed no', 'no effect on', 'no difference', 'not associated with', 'lacks', 'absence of', 'failed to'.\n"
        "   - Also extract when text contrasts with expectations: 'unlike', 'in contrast to', 'however', 'but', 'although'.\n"
        "   - Include negative findings from experiments, studies, or comparisons.\n"
        "   - Include when something is explicitly stated as 'not working', 'not effective', 'not found'.\n"
        "   - BALANCE: Aim for approximately 50% positive and 50% negative relationships when both types are present in the text.\n"
        "   - If the text contains many negative findings, extract them - they are scientifically valuable.\n"
        "\n"
        "7) Each extracted entity should be linked to at least one other entity.\n"
        "8) Prefer concise canonical entity names.\n"
        "9) For each triplet, the 'original_text' field MUST contain the specific sentence or fragment from the source that supports this relationship.\n"
        "10) Focus ONLY on claims stated in the text; do not add external knowledge.\n"
        "11) Deduplicate: no repeated (subject, predicate, object) entries.\n"
        "\n"
        "12) CONSISTENCY CHECK (run before finalizing):\n"
        "    - For each relationship you extract, verify it doesn't contradict other statements in the text.\n"
        "    - Look for both explicit and implicit evidence for or against each relationship.\n"
        "\n"
        f"13) EXAMPLES of negative relationships to extract:\n"
        "   - 'Drug X does_not_inhibit protein Y' (from 'Drug X failed to inhibit protein Y')\n"
        "   - 'Treatment does_not_reduce symptoms' (from 'Treatment showed no reduction in symptoms')\n"
        "   - 'Gene does_not_express protein' (from 'Gene expression was not detected')\n"
        "   - 'Method does_not_improve outcomes' (from 'Unlike traditional methods, this approach did not improve patient outcomes')\n"
        "\n"
        f"14) Target: Extract up to {max_triplets} high-quality relationships, aiming for ~50% negative relationships."
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
            relationship_significance=5,
            subject_significance=4,
            object_significance=5,
            page_number=3
        ),
        Triplet(
            subject="Vemurafenib",
            predicate="does_not_inhibit",
            object="wild-type BRAF",
            subject_type="Drug",
            object_type="Gene",
            original_text="Vemurafenib showed no inhibitory effect on wild-type BRAF.",
            relationship_significance=4,
            subject_significance=4,
            object_significance=3,
            page_number=5
        ),
        Triplet(
            subject="Combination therapy",
            predicate="does_not_improve",
            object="overall survival",
            subject_type="Treatment",
            object_type="Outcome",
            original_text="The combination therapy failed to demonstrate improved overall survival compared to monotherapy.",
            relationship_significance=3,
            subject_significance=3,
            object_significance=4,
            page_number=7
        )
    ]
    return TripletExtractionResult(triplets=demo, model="dry-run", tokens_used=0)


def extract_triplets(text: str, max_triplets: int = 50, pages: list = None, extraction_context: str = None) -> TripletExtractionResult:
    if settings.openai_dry_run or not settings.openai_api_key:
        return _fake_extract(text)

    try:
        # Lazy import to avoid hard dependency if not used
        import httpx
        from openai import OpenAI
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Starting OpenAI extraction for {len(text)} characters of text...")
        
        # Build page-aware text if page information is provided
        page_map = {}  # Map to store which text chunks belong to which pages
        if pages and isinstance(pages, list) and len(pages) > 0:
            # Format text with clear page markers for the AI
            page_marked_text = ""
            for page_info in pages:
                page_num = page_info.get("page_number", "?")
                page_text = page_info.get("text", "")
                page_marked_text += f"\n\n[PAGE {page_num} START]\n{page_text}\n[PAGE {page_num} END]"
                # Store text snippets for post-processing page detection
                page_map[page_num] = page_text
            text_to_send = page_marked_text
            logger.info(f"Using page-aware extraction with {len(pages)} pages")
        else:
            text_to_send = text
            logger.info("Using standard extraction (no page info)")

        # Honor proxy environment variables without using unsupported kwargs
        proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("OPENAI_PROXY")
        
        # Set reasonable timeout (10 minutes for large documents)
        # Can be overridden with OPENAI_TIMEOUT_SECONDS environment variable
        timeout_seconds = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "600"))
        
        http_client = None
        if proxy_url:
            http_client = httpx.Client(proxies=proxy_url, timeout=timeout_seconds)
            logger.info(f"Using proxy: {proxy_url} with {timeout_seconds}s timeout")

        # Create client with timeout
        if http_client:
            client = OpenAI(api_key=settings.openai_api_key, http_client=http_client, timeout=timeout_seconds)
        else:
            client = OpenAI(api_key=settings.openai_api_key, timeout=timeout_seconds)
        
        # Build system prompt with optional extraction context
        system_prompt = _create_prompt(max_triplets)
        if extraction_context:
            # Check if this contains graph context
            if "=== EXISTING KNOWLEDGE GRAPH CONTEXT ===" in extraction_context:
                logger.info("Detected graph context in extraction context")
                # Add context-aware instructions
                context_prefix = (
                    f"\n\n{extraction_context}\n"
                    f"CONTEXT-AWARE EXTRACTION INSTRUCTIONS:\n"
                    f"Analyze the new document to find relationships that:\n"
                    f"1. AGREE WITH existing knowledge - support or confirm what is in the graph\n"
                    f"2. DISAGREE WITH existing knowledge - contradict existing relationships\n"
                    f"3. ADD NEW knowledge - new entities or connections\n\n"
                    f"Prioritize relationships involving entities from the existing graph.\n"
                    f"Extract both positive and negative relationships.\n\n"
                )
                system_prompt = context_prefix + system_prompt
                logger.info("Added context-aware extraction prompt")
            else:
                # Regular user context only
                context_prefix = (
                    f"\n\n=== USER'S EXTRACTION FOCUS ===\n"
                    f"{extraction_context}\n"
                    f"=== END FOCUS ===\n\n"
                    f"Please prioritize extracting relationships that align with the user's stated interests above. "
                    f"However, still extract other significant relationships found in the text.\n\n"
                )
                system_prompt = context_prefix + system_prompt
                logger.info("Added user extraction context to prompt")
        
        logger.info(f"Calling OpenAI model: {settings.openai_model} (timeout: {timeout_seconds}s)")
        logger.info(f"Request size: {len(text_to_send)} characters")
        
        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_to_send},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            logger.info("OpenAI API call completed successfully")
        except Exception as api_error:
            logger.error(f"OpenAI API call failed: {type(api_error).__name__}: {api_error}")
            raise
        content = response.choices[0].message.content
        data = json.loads(content)
        raw_triplets = data.get("triplets", [])
        triplets = [Triplet.model_validate(t) for t in raw_triplets]
        
        # Post-process: Infer page numbers from original_text
        if page_map:
            inferred_count = 0
            failed_triplets = []
            
            for triplet in triplets:
                if triplet.original_text:
                    # Normalize: remove extra whitespace, lowercase for comparison
                    original_normalized = ' '.join(triplet.original_text.strip().split()).lower()
                    
                    best_match_page = None
                    best_match_score = 0
                    
                    # Try to find the best matching page
                    for page_num, page_text in page_map.items():
                        page_normalized = ' '.join(page_text.split()).lower()
                        
                        # Strategy 1: Direct substring match (most reliable)
                        if original_normalized in page_normalized:
                            triplet.page_number = page_num
                            inferred_count += 1
                            logger.debug(f"Page {page_num} (exact): {triplet.subject}->{triplet.object}")
                            break
                        
                        # Strategy 2: Check if multiple words from original appear in page
                        original_words = set(original_normalized.split())
                        if len(original_words) >= 5:  # Only for substantial text
                            page_words = set(page_normalized.split())
                            common_words = original_words & page_words
                            match_ratio = len(common_words) / len(original_words)
                            
                            if match_ratio > best_match_score:
                                best_match_score = match_ratio
                                best_match_page = page_num
                    
                    # If no exact match but good word overlap (>70%), use best match
                    if triplet.page_number is None and best_match_score > 0.7:
                        triplet.page_number = best_match_page
                        inferred_count += 1
                        logger.debug(f"Page {best_match_page} (fuzzy {best_match_score:.0%}): {triplet.subject}->{triplet.object}")
                    
                    # Track failures for debugging
                    if triplet.page_number is None:
                        failed_triplets.append({
                            "triplet": f"{triplet.subject}->{triplet.object}",
                            "original_text_length": len(original_normalized),
                            "best_score": best_match_score
                        })
            
            # Log detailed statistics
            with_pages = sum(1 for t in triplets if t.page_number is not None)
            logger.info(f"Page number inference: {inferred_count} inferred, {with_pages}/{len(triplets)} total ({with_pages*100//len(triplets)}% coverage)")
            
            if failed_triplets and len(failed_triplets) <= 5:
                logger.warning(f"Failed to infer page for {len(failed_triplets)} triplets:")
                for fail in failed_triplets[:3]:
                    logger.warning(f"  - {fail['triplet']} (text_len={fail['original_text_length']}, best_score={fail['best_score']:.2f})")
        
        # Validate, sanitize, and deduplicate
        logger.info(f"Validating {len(triplets)} raw triplets from OpenAI...")
        triplets, errors = validate_and_sanitize_triplets(triplets)
        logger.info(f"After validation: {len(triplets)} valid triplets")
        
        # Log sample triplets to check original_text
        if triplets:
            sample = triplets[0]
            logger.info(f"Sample triplet original_text: '{sample.original_text}' (type: {type(sample.original_text)}, length: {len(sample.original_text) if sample.original_text else 0})")
            triplets_with_text = [t for t in triplets if t.original_text and t.original_text.strip()]
            logger.info(f"Triplets with original_text: {len(triplets_with_text)}/{len(triplets)}")
        
        original_count = len(triplets)
        triplets = deduplicate_triplets(triplets)
        if len(triplets) < original_count:
            logger.info(f"Deduplication removed {original_count - len(triplets)} duplicate triplets")
        
        # Log validation errors if any (but don't fail the request)
        if errors:
            logger.warning(f"⚠️  Validation rejected {len(errors)} triplets:")
            for err in errors[:10]:  # Log first 10 errors with details
                logger.warning(f"  - Triplet {err.get('triplet_index', '?')}: {err.get('error', 'Unknown error')}")
                if 'triplet' in err:
                    triplet_data = err['triplet']
                    logger.warning(f"    Subject: {triplet_data.get('subject', '?')}, Predicate: {triplet_data.get('predicate', '?')}, Object: {triplet_data.get('object', '?')}")
        
        tokens_used = getattr(response.usage, "total_tokens", None)
        return TripletExtractionResult(triplets=triplets, model=settings.openai_model, tokens_used=tokens_used)
    except json.JSONDecodeError as exc:
        import logging
        logging.error(f"Failed to parse OpenAI response as JSON: {content[:500]}")
        raise HTTPException(status_code=502, detail=f"OpenAI returned invalid JSON: {exc}")
    except httpx.TimeoutException as exc:
        import logging
        logging.error(f"OpenAI API call timed out after 5 minutes: {exc}")
        raise HTTPException(status_code=504, detail=f"OpenAI request timed out. Try with a shorter document or increase timeout settings.")
    except Exception as exc:
        import logging
        import traceback
        logging.error(f"OpenAI extraction failed: {exc}")
        logging.error(f"Exception type: {type(exc).__name__}")
        logging.error(traceback.format_exc())
        
        # Check if it's a timeout-related error
        if "timeout" in str(exc).lower() or "timed out" in str(exc).lower():
            raise HTTPException(status_code=504, detail=f"Request timed out: {exc}. Try with a shorter document.")
        
        raise HTTPException(status_code=502, detail=f"OpenAI extraction failed: {exc}")


def extract_title_with_llm(text: str) -> str:
    """
    Extract document title using LLM.
    Uses first 1500 characters to keep cost low.
    
    Args:
        text: Full document text
        
    Returns:
        Extracted title string
    """
    import logging
    import openai
    
    logger = logging.getLogger(__name__)
    
    # Take first 1500 characters for title extraction
    sample = text[:200].strip()
    
    if not sample:
        return "Untitled Document"
    
    try:
        # Use OpenAI to extract title with timeout
        timeout_seconds = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "600"))
        client = openai.OpenAI(api_key=settings.openai_api_key, timeout=timeout_seconds)
        
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{
                "role": "user",
                "content": (
                    "Extract the document title from the beginning of this text. "
                    "Return ONLY the title, nothing else. "
                    "Do not include author names, affiliations, or other metadata. "
                    "If there is no clear title, return 'Untitled Document'.\n\n"
                    f"{sample}"
                )
            }],
            temperature=0,
            max_tokens=100
        )
        
        title = response.choices[0].message.content.strip()
        
        # Clean up common issues
        title = title.strip('"\'')  # Remove quotes
        title = title.replace('\n', ' ')  # Remove newlines
        
        # Limit length
        if len(title) > 200:
            title = title[:197] + "..."
        
        # Fallback if extraction failed
        if not title or title.lower() == "untitled document":
            logger.warning("LLM title extraction returned empty or default, using fallback")
            return _fallback_title_extraction(text)
        
        logger.info(f"Extracted title with LLM: {title}")
        return title
        
    except Exception as e:
        logger.error(f"LLM title extraction failed: {e}, using fallback")
        return _fallback_title_extraction(text)


def _fallback_title_extraction(text: str) -> str:
    """Simple fallback title extraction using first non-empty line."""
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    if lines:
        title = lines[0]
        if len(title) > 200:
            title = title[:197] + "..."
        return title
    return "Untitled Document"


