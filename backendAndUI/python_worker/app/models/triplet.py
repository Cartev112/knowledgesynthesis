from __future__ import annotations

from typing import Optional, List, Union

from pydantic import BaseModel, Field, model_validator


def _normalize_types(values: Optional[Union[List[str], str]]) -> List[str]:
    """
    Normalize a subject/object type field into a list of unique, trimmed strings.
    Accepts either a legacy string or a list of strings.
    """
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    normalized: List[str] = []
    for value in values:
        if not value:
            continue
        cleaned = value.strip()
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


class Triplet(BaseModel):
    subject: str = Field(..., min_length=1)
    predicate: str = Field(..., min_length=1)
    object: str = Field(..., min_length=1)
    subject_types: List[str] = Field(default_factory=list, description="List of types for the subject concept")
    object_types: List[str] = Field(default_factory=list, description="List of types for the object concept")
    # Legacy scalar fields retained for backward compatibility
    subject_type: Optional[str] = Field(default=None, description="Deprecated - prefer subject_types list")
    object_type: Optional[str] = Field(default=None, description="Deprecated - prefer object_types list")
    source_document_id: Optional[str] = None
    extracted_by: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    original_text: Optional[str] = None
    # Significance scores (1-5 scale, 5 being most significant)
    relationship_significance: Optional[int] = Field(None, ge=1, le=5)
    subject_significance: Optional[int] = Field(None, ge=1, le=5)
    object_significance: Optional[int] = Field(None, ge=1, le=5)
    # Page number where this relationship was found
    page_number: Optional[int] = Field(None, ge=1)

    @model_validator(mode="after")
    def normalize_types(cls, values: "Triplet") -> "Triplet":
        """
        Ensure subject/object types are represented as lists and populate
        the legacy scalar fields for consumers that still expect them.
        """
        subject_types = _normalize_types(values.subject_types or values.subject_type)
        object_types = _normalize_types(values.object_types or values.object_type)

        if not subject_types:
            subject_types = ["Concept"]
        if not object_types:
            object_types = ["Concept"]

        values.subject_types = subject_types
        values.object_types = object_types
        values.subject_type = subject_types[0] if subject_types else None
        values.object_type = object_types[0] if object_types else None
        return values


class TripletExtractionResult(BaseModel):
    triplets: List[Triplet]
    model: str
    tokens_used: Optional[int] = None











