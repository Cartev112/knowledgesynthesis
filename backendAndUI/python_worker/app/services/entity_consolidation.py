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
    // Find entities with identical names and identical type sets
    MATCH (n:Entity)
    OPTIONAL MATCH (n)-[:IS_A]->(type:Concept)
    WITH n, collect(DISTINCT type.name) AS type_names
    WITH n,
         n.name AS entity_name,
         apoc.coll.sort(CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END) AS entity_types
    WITH entity_name, entity_types, collect(n) AS nodes
    WHERE size(nodes) > 1
    
    CALL apoc.refactor.mergeNodes(nodes, {
        mergeRels: true,
        properties: {
            name: 'discard',
            significance: 'combine',
            created_at: 'combine',
            sources: 'combine'
        },
        mergeRelsConfig: {
            sources: 'combine',
            confidence: 'combine',
            significance: 'combine'
        }
    }) YIELD node
    
    RETURN count(node) AS merged_nodes, 
           collect({name: entity_name, types: entity_types}) AS entity_groups
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(consolidation_cypher)
            record = result.single()
            
            if record:
                merged_count = record["merged_nodes"] or 0
                entity_groups = record["entity_groups"] or []
                
                logger.info(f"APOC consolidation completed: {merged_count} entity groups merged")
                logger.info(f"Merged entity groups: {entity_groups}")
                
                return {
                    "success": True,
                    "merged_entity_groups": merged_count,
                    "merged_entity_names": [group.get("name") for group in entity_groups],
                    "merged_entity_details": entity_groups,
                    "message": f"Successfully consolidated {merged_count} groups of identical entities"
                }
            else:
                logger.info("No duplicate entities found for consolidation")
                return {
                    "success": True,
                    "merged_entity_groups": 0,
                    "merged_entity_names": [],
                    "merged_entity_details": [],
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
    OPTIONAL MATCH (n)-[:IS_A]->(type:Concept)
    WITH n, collect(DISTINCT type.name) AS type_names
    WITH n,
         CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END AS types
    OPTIONAL MATCH (n)-[:EXTRACTED_FROM]->(doc:Document)
    WITH n, types, collect(DISTINCT doc.document_id) AS doc_ids
    WITH n.name AS entity_name,
         apoc.coll.sort(types) AS entity_types,
         collect({
            id: elementId(n),
            name: n.name,
            types: types,
            significance: n.significance,
            created_at: n.created_at,
            sources: doc_ids
         }) AS entities
    WHERE size(entities) > 1
    RETURN entity_name, entity_types, entities
    ORDER BY entity_name, entity_types
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(find_duplicates_cypher)
            duplicates = []
            
            for record in result:
                duplicates.append({
                    "entity_name": record["entity_name"],
                    "entity_types": record["entity_types"],
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
            significance: 'combine',
            created_at: 'combine'
        },
        mergeRelsConfig: {
            sources: 'combine',
            confidence: 'combine',
            significance: 'combine'
        }
    }) YIELD node
    OPTIONAL MATCH (node)-[:IS_A]->(type:Concept)
    WITH node, collect(DISTINCT type.name) AS type_names
    RETURN node, elementId(node) AS merged_id, CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END AS merged_types
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(merge_specific_cypher, entity_ids=entity_ids)
            record = result.single()
            
            if record:
                merged_node = record["node"]
                merged_id = record["merged_id"]
                merged_types = record["merged_types"] or ["Concept"]
                
                logger.info(f"Successfully merged entities into: {merged_node['name']} ({merged_id}) with types {merged_types}")
                
                return {
                    "success": True,
                    "merged_entity_id": merged_id,
                    "merged_entity_name": merged_node["name"],
                    "merged_entity_type": merged_types[0],
                    "merged_entity_types": merged_types,
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
    
    CALL {
        MATCH (m:Entity)
        OPTIONAL MATCH (m)-[:IS_A]->(type:Concept)
        WITH m.name AS entity_name,
             apoc.coll.sort(CASE WHEN count(type) = 0 THEN ['Concept'] ELSE collect(DISTINCT type.name) END) AS entity_types,
             collect(m) AS nodes
        WHERE size(nodes) > 1
        RETURN count(*) AS duplicate_groups, sum(size(nodes)) AS entities_in_duplicates
        UNION
        RETURN 0 AS duplicate_groups, 0 AS entities_in_duplicates
        ORDER BY duplicate_groups DESC, entities_in_duplicates DESC
        LIMIT 1
    }
    
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


