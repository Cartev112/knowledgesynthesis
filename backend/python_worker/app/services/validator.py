"""Validation and sanitization for extracted triplets."""
from __future__ import annotations

import re
from typing import List

from ..models.triplet import Triplet


def normalize_predicate(predicate: str) -> str:
    """
    Normalize a predicate to lowercase snake_case.
    
    Examples:
        "binds to" -> "binds_to"
        "Does Not Bind" -> "does_not_bind"
        "INHIBITS" -> "inhibits"
    """
    normalized = predicate.strip().lower()
    # Replace spaces and hyphens with underscores
    normalized = re.sub(r'[\s\-]+', '_', normalized)
    # Remove any non-alphanumeric characters except underscores
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    # Remove duplicate underscores
    normalized = re.sub(r'_+', '_', normalized)
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    return normalized if normalized else "related_to"


def normalize_entity_name(name: str) -> str:
    """
    Normalize an entity name by trimming whitespace and removing excessive descriptors.
    """
    return name.strip()


def validate_triplet(triplet: Triplet) -> tuple[bool, str]:
    """
    Validate a single triplet for completeness and quality.
    
    Returns:
        (is_valid, error_message)
    """
    # Check required fields
    if not triplet.subject or len(triplet.subject.strip()) == 0:
        return False, "Subject is empty"
    
    if not triplet.predicate or len(triplet.predicate.strip()) == 0:
        return False, "Predicate is empty"
    
    if not triplet.object or len(triplet.object.strip()) == 0:
        return False, "Object is empty"
    
    # Check for overly long entities (likely errors)
    if len(triplet.subject) > 200:
        return False, f"Subject too long ({len(triplet.subject)} chars)"
    
    if len(triplet.object) > 200:
        return False, f"Object too long ({len(triplet.object)} chars)"
    
    if len(triplet.predicate) > 100:
        return False, f"Predicate too long ({len(triplet.predicate)} chars)"
    
    # Check for suspiciously short entities
    if len(triplet.subject.strip()) < 2:
        return False, "Subject too short"
    
    if len(triplet.object.strip()) < 2:
        return False, "Object too short"
    
    # Check confidence score range
    if triplet.confidence_score is not None:
        if not 0.0 <= triplet.confidence_score <= 1.0:
            return False, f"Confidence score out of range: {triplet.confidence_score}"
    
    return True, ""


def sanitize_triplet(triplet: Triplet) -> Triplet:
    """
    Clean and normalize a triplet's fields.
    """
    return Triplet(
        subject=normalize_entity_name(triplet.subject),
        predicate=normalize_predicate(triplet.predicate),
        object=normalize_entity_name(triplet.object),
        subject_type=triplet.subject_type.strip() if triplet.subject_type else None,
        object_type=triplet.object_type.strip() if triplet.object_type else None,
        source_document_id=triplet.source_document_id,
        extracted_by=triplet.extracted_by,
        confidence_score=triplet.confidence_score,
        original_text=triplet.original_text.strip() if triplet.original_text else None,
    )


def validate_and_sanitize_triplets(triplets: List[Triplet]) -> tuple[List[Triplet], List[dict]]:
    """
    Validate and sanitize a list of triplets.
    
    Returns:
        (valid_triplets, errors)
        
    Where errors is a list of dicts with 'triplet_index' and 'error' keys.
    """
    valid_triplets = []
    errors = []
    
    for idx, triplet in enumerate(triplets):
        # First sanitize
        try:
            sanitized = sanitize_triplet(triplet)
        except Exception as e:
            errors.append({
                "triplet_index": idx,
                "error": f"Sanitization failed: {str(e)}",
                "triplet": triplet.model_dump() if hasattr(triplet, 'model_dump') else str(triplet)
            })
            continue
        
        # Then validate
        is_valid, error_msg = validate_triplet(sanitized)
        if not is_valid:
            errors.append({
                "triplet_index": idx,
                "error": error_msg,
                "triplet": sanitized.model_dump()
            })
        else:
            valid_triplets.append(sanitized)
    
    return valid_triplets, errors


def deduplicate_triplets(triplets: List[Triplet]) -> List[Triplet]:
    """
    Remove duplicate triplets based on (subject, predicate, object) tuples.
    Keeps the first occurrence of each unique triplet.
    """
    seen = set()
    unique_triplets = []
    
    for triplet in triplets:
        key = (
            triplet.subject.lower(),
            triplet.predicate.lower(),
            triplet.object.lower()
        )
        
        if key not in seen:
            seen.add(key)
            unique_triplets.append(triplet)
    
    return unique_triplets

