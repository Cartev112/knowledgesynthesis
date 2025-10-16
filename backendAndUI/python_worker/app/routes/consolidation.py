from fastapi import APIRouter, HTTPException, Query as Q
from typing import List, Optional

from ..services.entity_consolidation import (
    consolidate_identical_entities,
    find_duplicate_entities,
    merge_specific_entities,
    get_consolidation_stats
)

router = APIRouter()


@router.post("/consolidate")
def consolidate_entities():
    """
    Consolidate all identical entities in the knowledge graph using APOC.
    
    This endpoint identifies entities with the same name and type, then merges them
    using APOC's mergeNodes function, consolidating all their relationships.
    """
    try:
        result = consolidate_identical_entities()
        
        if result["success"]:
            return {
                "message": result["message"],
                "merged_entity_groups": result["merged_entity_groups"],
                "merged_entity_names": result["merged_entity_names"],
                "success": True
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Consolidation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Consolidation failed: {exc}")


@router.get("/duplicates")
def get_duplicate_entities():
    """
    Find entities that have identical names and types (potential duplicates).
    
    Returns a list of entity groups that could be merged.
    """
    try:
        duplicates = find_duplicate_entities()
        
        return {
            "duplicate_groups": len(duplicates),
            "duplicates": duplicates,
            "message": f"Found {len(duplicates)} groups of duplicate entities"
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to find duplicates: {exc}")


@router.post("/merge")
def merge_entities(
    entity_ids: List[str] = Q(..., description="List of entity element IDs to merge")
):
    """
    Manually merge specific entities by their IDs using APOC.
    
    Args:
        entity_ids: List of entity element IDs to merge together
    """
    if len(entity_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 entity IDs are required for merging"
        )
    
    try:
        result = merge_specific_entities(entity_ids)
        
        if result["success"]:
            return {
                "message": result["message"],
                "merged_entity_id": result["merged_entity_id"],
                "merged_entity_name": result["merged_entity_name"],
                "merged_entity_type": result["merged_entity_type"],
                "success": True
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Merge failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Merge failed: {exc}")


@router.get("/stats")
def get_consolidation_statistics():
    """
    Get statistics about the current state of entity consolidation.
    
    Returns information about total entities, duplicate groups, and potential merges.
    """
    try:
        stats = get_consolidation_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["message"])
        
        return {
            "statistics": stats,
            "message": "Consolidation statistics retrieved successfully"
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {exc}")


@router.get("/health")
def consolidation_health():
    """
    Check if APOC consolidation functionality is available.
    
    Returns the health status of the APOC consolidation system.
    """
    try:
        # Try to get stats to verify APOC is working
        stats = get_consolidation_stats()
        
        if "error" in stats:
            return {
                "status": "unhealthy",
                "message": "APOC consolidation is not available",
                "error": stats.get("error", "Unknown error")
            }
        else:
            return {
                "status": "healthy",
                "message": "APOC consolidation is available and working",
                "apoc_available": True
            }
            
    except Exception as exc:
        return {
            "status": "unhealthy",
            "message": "APOC consolidation is not available",
            "error": str(exc),
            "apoc_available": False
        }

