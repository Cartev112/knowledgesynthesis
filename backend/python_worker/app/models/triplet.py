from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field


class Triplet(BaseModel):
    subject: str = Field(..., min_length=1)
    predicate: str = Field(..., min_length=1)
    object: str = Field(..., min_length=1)
    subject_type: Optional[str] = None
    object_type: Optional[str] = None
    source_document_id: Optional[str] = None
    extracted_by: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    original_text: Optional[str] = None


class TripletExtractionResult(BaseModel):
    triplets: List[Triplet]
    model: str
    tokens_used: Optional[int] = None







