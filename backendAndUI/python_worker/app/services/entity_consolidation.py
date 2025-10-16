from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

from .neo4j_client import neo4j_client
from ..core.settings import settings


logger = logging.getLogger(__name__)


def consolidate_identical_entities() -> Dict[str, Any]:
    """
    Use APOC to consolidate identical entities in the knowledge graph.
    
    This function identifies entities with the same name and type, then merges them
    using APOC's mergeNodes function, consolidating all their relationships.
    
    Returns:
        Dict containing consolidation statistics
    """
    consolidation_cypher = """
    // Find entities with identical names and types that should be merged
    MATCH (n:Entity)
    WITH n.name AS entity_name, n.type AS entity_type, collect(n) AS nodes
    WHERE size(nodes) > 1
    
    // For each group of identical entities, merge them using APOC
    CALL apoc.refactor.mergeNodes(nodes, {
        mergeRels: true,
        properties: {
            name: 'discard',
            type: 'discard',
            // Keep the highest significance score
            significance: 'combine',
            // Keep the most recent creation date
            created_at: 'combine',
            // Merge arrays of source documents
            sources: 'combine'
        },
        mergeRelsConfig: {
            // Merge relationship properties
            sources: 'combine',
            confidence: 'combine',
            significance: 'combine'
        }
    }) YIELD node
    
    RETURN count(node) AS merged_nodes, 
           collect(entity_name) AS entity_names
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(consolidation_cypher)
            record = result.single()
            
            if record:
                merged_count = record["merged_nodes"] or 0
                entity_names = record["entity_names"] or []
                
                logger.info(f"APOC consolidation completed: {merged_count} entity groups merged")
                logger.info(f"Merged entity names: {entity_names}")
                
                return {
                    "success": True,
                    "merged_entity_groups": merged_count,
                    "merged_entity_names": entity_names,
                    "message": f"Successfully consolidated {merged_count} groups of identical entities"
                }
            else:
                logger.info("No duplicate entities found for consolidation")
                return {
                    "success": True,
                    "merged_entity_groups": 0,
                    "merged_entity_names": [],
                    "message": "No duplicate entities found"
                }
                
    except Exception as exc:
        logger.error(f"APOC consolidation failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "message": "Failed to consolidate entities"
        }


def find_duplicate_entities() -> List[Dict[str, Any]]:
    """
    Find entities that have identical names and types (potential duplicates).
    
    Returns:
        List of dictionaries containing duplicate entity information
    """
    find_duplicates_cypher = """
    MATCH (n:Entity)
    WITH n.name AS entity_name, n.type AS entity_type, collect({
        id: elementId(n),
        name: n.name,
        type: n.type,
        significance: n.significance,
        created_at: n.created_at,
        sources: [doc IN [(n)-[:EXTRACTED_FROM]->(doc:Document) | doc.document_id]
    }) AS entities
    WHERE size(entities) > 1
    RETURN entity_name, entity_type, entities
    ORDER BY entity_name, entity_type
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(find_duplicates_cypher)
            duplicates = []
            
            for record in result:
                duplicates.append({
                    "entity_name": record["entity_name"],
                    "entity_type": record["entity_type"],
                    "entities": record["entities"],
                    "duplicate_count": len(record["entities"])
                })
            
            return duplicates
            
    except Exception as exc:
        logger.error(f"Failed to find duplicate entities: {exc}")
        return []


def merge_specific_entities(entity_ids: List[str]) -> Dict[str, Any]:
    """
    Manually merge specific entities by their IDs using APOC.
    
    Args:
        entity_ids: List of entity element IDs to merge
        
    Returns:
        Dict containing merge results
    """
    if len(entity_ids) < 2:
        return {
            "success": False,
            "error": "At least 2 entity IDs are required for merging",
            "message": "Cannot merge fewer than 2 entities"
        }
    
    merge_specific_cypher = """
    MATCH (n:Entity)
    WHERE elementId(n) IN $entity_ids
    WITH collect(n) AS nodes
    WHERE size(nodes) > 1
    
    CALL apoc.refactor.mergeNodes(nodes, {
        mergeRels: true,
        properties: {
            name: 'discard',
            type: 'discard',
            significance: 'combine',
            created_at: 'combine'
        },
        mergeRelsConfig: {
            sources: 'combine',
            confidence: 'combine',
            significance: 'combine'
        }
    }) YIELD node
    
    RETURN node, elementId(node) AS merged_id
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(merge_specific_cypher, entity_ids=entity_ids)
            record = result.single()
            
            if record:
                merged_node = record["node"]
                merged_id = record["merged_id"]
                
                logger.info(f"Successfully merged entities into: {merged_node['name']} ({merged_id})")
                
                return {
                    "success": True,
                    "merged_entity_id": merged_id,
                    "merged_entity_name": merged_node["name"],
                    "merged_entity_type": merged_node["type"],
                    "message": f"Successfully merged {len(entity_ids)} entities into {merged_node['name']}"
                }
            else:
                return {
                    "success": False,
                    "error": "No entities found with provided IDs",
                    "message": "Could not find entities to merge"
                }
                
    except Exception as exc:
        logger.error(f"Failed to merge specific entities: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "message": "Failed to merge entities"
        }


def get_consolidation_stats() -> Dict[str, Any]:
    """
    Get statistics about the current state of entity consolidation.
    
    Returns:
        Dict containing consolidation statistics
    """
    stats_cypher = """
    // Total entities
    MATCH (n:Entity)
    WITH count(n) AS total_entities
    
    // Duplicate groups
    MATCH (n:Entity)
    WITH total_entities, n.name AS entity_name, n.type AS entity_type, collect(n) AS nodes
    WHERE size(nodes) > 1
    WITH total_entities, count(*) AS duplicate_groups, sum(size(nodes)) AS entities_in_duplicates
    
    // Total relationships
    MATCH ()-[r]->()
    WITH total_entities, duplicate_groups, entities_in_duplicates, count(r) AS total_relationships
    
    RETURN total_entities, duplicate_groups, entities_in_duplicates, total_relationships,
           CASE WHEN duplicate_groups > 0 THEN entities_in_duplicates - duplicate_groups ELSE 0 END AS potential_merges
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(stats_cypher)
            record = result.single()
            
            if record:
                return {
                    "total_entities": record["total_entities"],
                    "duplicate_groups": record["duplicate_groups"],
                    "entities_in_duplicates": record["entities_in_duplicates"],
                    "total_relationships": record["total_relationships"],
                    "potential_merges": record["potential_merges"]
                }
            else:
                return {
                    "total_entities": 0,
                    "duplicate_groups": 0,
                    "entities_in_duplicates": 0,
                    "total_relationships": 0,
                    "potential_merges": 0
                }
                
    except Exception as exc:
        logger.error(f"Failed to get consolidation stats: {exc}")
        return {
            "error": str(exc),
            "message": "Failed to retrieve consolidation statistics"
        }

