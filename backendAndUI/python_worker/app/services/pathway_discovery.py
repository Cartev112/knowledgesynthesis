"""
Pathway Discovery Service
=========================

This module provides advanced graph discovery capabilities including:
- Shortest path finding between concepts
- All paths discovery
- Multi-hop relationship exploration
- Pattern-based queries

Uses Neo4j Graph Data Science library for efficient path algorithms.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging

from .neo4j_client import neo4j_client
from ..core.settings import settings


logger = logging.getLogger(__name__)


def find_shortest_path(
    source_name: str, 
    target_name: str, 
    max_hops: int = 5,
    verified_only: bool = False
) -> Dict[str, Any]:
    """
    Find the shortest path between two concepts in the knowledge graph.
    
    Args:
        source_name: Name of the source concept
        target_name: Name of the target concept
        max_hops: Maximum number of relationship hops to explore
        verified_only: Only consider verified relationships
        
    Returns:
        Dict containing path information, nodes, and relationships
    """
    status_filter = "AND r.status = 'verified'" if verified_only else ""
    
    cypher = f"""
    MATCH (source:Entity), (target:Entity)
    WHERE toLower(source.name) CONTAINS toLower($source_name)
      AND toLower(target.name) CONTAINS toLower($target_name)
    
    MATCH path = shortestPath((source)-[*1..{max_hops}]->(target))
    WHERE all(r IN relationships(path) WHERE $verified_only = false OR r.status = 'verified')
    
    WITH path, source, target, length(path) AS path_length,
         [r IN relationships(path) | {{
            id: elementId(r),
            source: coalesce(startNode(r).id, startNode(r).name, elementId(startNode(r))),
            target: coalesce(endNode(r).id, endNode(r).name, elementId(endNode(r))),
            relation: type(r),
            confidence: r.confidence,
            significance: r.significance,
            status: r.status,
            polarity: coalesce(r.polarity, 'positive')
         }}] AS path_rels,
         CASE WHEN size(nodes(path)) = 0 THEN [] ELSE range(0, size(nodes(path)) - 1) END AS idxs
    
    UNWIND idxs AS idx
    WITH path, source, target, path_length, path_rels, idx, nodes(path)[idx] AS node
    OPTIONAL MATCH (node)-[:IS_A]->(type:Concept)
    WITH source, target, path_length, path_rels, idx, node, collect(DISTINCT type.name) AS type_names
    WITH source, target, path_length, path_rels,
         collect({{
            idx: idx,
            id: coalesce(node.id, node.name, elementId(node)),
            name: node.name,
            types: CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END,
            type: CASE WHEN size(type_names) = 0 THEN 'Concept' ELSE head(type_names) END,
            significance: node.significance
         }}) AS nodes_with_idx
    WITH source, target, path_length, path_rels,
         [n IN nodes_with_idx ORDER BY n.idx | n{{.id, .name, .types, .type, .significance}}] AS path_nodes
    
    RETURN
      source.name AS source,
      target.name AS target,
      path_length,
      path_nodes,
      path_rels
    ORDER BY path_length ASC
    LIMIT 1
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                cypher, 
                source_name=source_name, 
                target_name=target_name,
                verified_only=verified_only
            )
            record = result.single()
            
            if not record:
                return {
                    "success": False,
                    "message": f"No path found between '{source_name}' and '{target_name}'",
                    "path_found": False
                }
            
            return {
                "success": True,
                "path_found": True,
                "source": record["source"],
                "target": record["target"],
                "path_length": record["path_length"],
                "nodes": record["path_nodes"],
                "relationships": record["path_rels"],
                "message": f"Found path of length {record['path_length']}"
            }
            
    except Exception as exc:
        logger.error(f"Shortest path query failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "message": "Failed to find shortest path"
        }


def find_all_paths(
    source_name: str,
    target_name: str,
    max_hops: int = 5,
    max_paths: int = 10,
    verified_only: bool = False
) -> Dict[str, Any]:
    """
    Find all paths between two concepts (up to max_paths).
    
    Args:
        source_name: Name of the source concept
        target_name: Name of the target concept
        max_hops: Maximum number of relationship hops to explore
        max_paths: Maximum number of paths to return
        verified_only: Only consider verified relationships
        
    Returns:
        Dict containing all paths found
    """
    cypher = f"""
    MATCH (source:Entity), (target:Entity)
    WHERE toLower(source.name) CONTAINS toLower($source_name)
      AND toLower(target.name) CONTAINS toLower($target_name)
    
    MATCH path = allShortestPaths((source)-[*1..{max_hops}]->(target))
    WHERE all(r IN relationships(path) WHERE $verified_only = false OR r.status = 'verified')
    
    WITH path, source, target, length(path) AS path_length,
         [r IN relationships(path) | {{
            id: elementId(r),
            source: coalesce(startNode(r).id, startNode(r).name, elementId(startNode(r))),
            target: coalesce(endNode(r).id, endNode(r).name, elementId(endNode(r))),
            relation: type(r),
            confidence: r.confidence,
            significance: r.significance,
            status: r.status,
            polarity: coalesce(r.polarity, 'positive')
         }}] AS path_rels,
         CASE WHEN size(nodes(path)) = 0 THEN [] ELSE range(0, size(nodes(path)) - 1) END AS idxs
    
    UNWIND idxs AS idx
    WITH path, source, target, path_length, path_rels, idx, nodes(path)[idx] AS node
    OPTIONAL MATCH (node)-[:IS_A]->(type:Concept)
    WITH source, target, path_length, path_rels, idx, node, collect(DISTINCT type.name) AS type_names
    WITH source, target, path_length, path_rels,
         collect({{
            idx: idx,
            id: coalesce(node.id, node.name, elementId(node)),
            name: node.name,
            types: CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END,
            type: CASE WHEN size(type_names) = 0 THEN 'Concept' ELSE head(type_names) END,
            significance: node.significance
         }}) AS nodes_with_idx
    WITH source, target, path_length, path_rels,
         [n IN nodes_with_idx ORDER BY n.idx | n{{.id, .name, .types, .type, .significance}}] AS path_nodes
    
    RETURN 
      source.name AS source,
      target.name AS target,
      path_length,
      path_nodes,
      path_rels
    ORDER BY path_length ASC
    LIMIT $max_paths
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                cypher,
                source_name=source_name,
                target_name=target_name,
                verified_only=verified_only,
                max_paths=max_paths
            )
            
            paths = []
            for record in result:
                paths.append({
                    "source": record["source"],
                    "target": record["target"],
                    "path_length": record["path_length"],
                    "nodes": record["path_nodes"],
                    "relationships": record["path_rels"]
                })
            
            if not paths:
                return {
                    "success": False,
                    "message": f"No paths found between '{source_name}' and '{target_name}'",
                    "paths_found": 0,
                    "paths": []
                }
            
            return {
                "success": True,
                "paths_found": len(paths),
                "paths": paths,
                "message": f"Found {len(paths)} path(s)"
            }
            
    except Exception as exc:
        logger.error(f"All paths query failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "message": "Failed to find paths"
        }


def find_connecting_concepts(
    source_name: str,
    target_name: str,
    max_hops: int = 3
) -> Dict[str, Any]:
    """
    Find intermediate concepts that connect two entities.
    
    This is useful for discovering "bridge" concepts that link two seemingly
    unrelated entities.
    
    Args:
        source_name: Name of the source concept
        target_name: Name of the target concept
        max_hops: Maximum hops from source to intermediate concept
        
    Returns:
        Dict containing connecting concepts and their relationships
    """
    cypher = f"""
    MATCH (source:Entity), (target:Entity)
    WHERE toLower(source.name) CONTAINS toLower($source_name)
      AND toLower(target.name) CONTAINS toLower($target_name)
    
    // Find concepts that connect both
    MATCH path1 = (source)-[*1..{max_hops}]->(connector:Entity)
    MATCH path2 = (connector)-[*1..{max_hops}]->(target)
    WHERE connector <> source AND connector <> target
    
    WITH connector, length(path1) + length(path2) AS total_hops
    ORDER BY total_hops ASC
    LIMIT 20
    
    OPTIONAL MATCH (connector)-[:EXTRACTED_FROM]->(doc:Document)
    WITH connector, total_hops, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id)}) AS sources
    OPTIONAL MATCH (connector)-[:IS_A]->(type:Concept)
    WITH connector, total_hops, sources, collect(DISTINCT type.name) AS type_names
    
    RETURN {{
      id: coalesce(connector.id, connector.name, elementId(connector)),
      name: connector.name,
      types: CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END,
      type: CASE WHEN size(type_names) = 0 THEN 'Concept' ELSE head(type_names) END,
      significance: connector.significance,
      sources: sources,
      hops: total_hops
    }} AS connector
    ORDER BY total_hops ASC
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                cypher,
                source_name=source_name,
                target_name=target_name
            )
            
            connectors = [record["connector"] for record in result]
            
            return {
                "success": True,
                "connectors_found": len(connectors),
                "connectors": connectors,
                "message": f"Found {len(connectors)} connecting concept(s)"
            }
            
    except Exception as exc:
        logger.error(f"Connecting concepts query failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "message": "Failed to find connecting concepts"
        }


def explore_multi_hop(
    concept_name: str,
    hops: int = 2,
    limit_per_hop: int = 10,
    verified_only: bool = False
) -> Dict[str, Any]:
    """
    Explore the graph starting from a concept, going N hops out.
    
    Args:
        concept_name: Starting concept name
        hops: Number of hops to explore (1-3 recommended)
        limit_per_hop: Limit results per hop level
        verified_only: Only consider verified relationships
        
    Returns:
        Dict containing multi-hop exploration results
    """
    status_filter = "AND r.status = 'verified'" if verified_only else ""
    
    cypher = f"""
    MATCH (center:Entity)
    WHERE toLower(center.name) CONTAINS toLower($concept_name)
    
    // Variable-length path
    MATCH path = (center)-[*1..{hops}]-(related:Entity)
    WHERE all(r IN relationships(path) WHERE $verified_only = false OR r.status = 'verified')
    
    WITH DISTINCT related, length(path) AS hop_distance, center
    ORDER BY hop_distance ASC, related.significance DESC
    
    WITH center, hop_distance, collect(DISTINCT related)[0..{limit_per_hop}] AS entities_at_hop
    
    UNWIND entities_at_hop AS entity
    
    OPTIONAL MATCH (entity)-[:EXTRACTED_FROM]->(doc:Document)
    
    WITH center, hop_distance, entity, collect({{id: doc.document_id, title: coalesce(doc.title, doc.document_id)}}) AS sources
    OPTIONAL MATCH (entity)-[:IS_A]->(type:Concept)
    WITH center, hop_distance, entity, sources, collect(DISTINCT type.name) AS type_names
    
    RETURN 
      center.name AS center_concept,
      hop_distance,
      collect({{
        id: coalesce(entity.id, entity.name, elementId(entity)),
        name: entity.name,
        types: CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END,
        type: CASE WHEN size(type_names) = 0 THEN 'Concept' ELSE head(type_names) END,
        significance: entity.significance,
        sources: sources
      }}) AS entities
    ORDER BY hop_distance ASC
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                cypher,
                concept_name=concept_name,
                verified_only=verified_only
            )
            
            exploration_data = []
            for record in result:
                exploration_data.append({
                    "hop_distance": record["hop_distance"],
                    "entities": record["entities"],
                    "entity_count": len(record["entities"])
                })
            
            if not exploration_data:
                return {
                    "success": False,
                    "message": f"No entities found connected to '{concept_name}'",
                    "exploration_data": []
                }
            
            return {
                "success": True,
                "center_concept": exploration_data[0]["hop_distance"] if exploration_data else concept_name,
                "exploration_data": exploration_data,
                "total_hops": len(exploration_data),
                "message": f"Explored {len(exploration_data)} hop level(s)"
            }
            
    except Exception as exc:
        logger.error(f"Multi-hop exploration failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "message": "Failed to explore multi-hop relationships"
        }


def pattern_query(
    pattern_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a pattern-based query based on configuration.
    
    Example pattern_config:
    {
        "node1_type": "Drug",
        "relationship": "TARGETS",
        "node2_type": "Gene",
        "node1_name": "Vemurafenib",
        "verified_only": true,
        "high_confidence": true,
        "limit": 50
    }
    
    Args:
        pattern_config: Dictionary describing the pattern to match
        
    Returns:
        Dict containing matching patterns
    """
    # Build dynamic Cypher query based on pattern
    try:
        node1_type = pattern_config.get("node1_type")
        node2_type = pattern_config.get("node2_type")
        rel_type = pattern_config.get("relationship")
        node1_name = pattern_config.get("node1_name")
        node2_name = pattern_config.get("node2_name")
        verified_only = pattern_config.get("verified_only", False)
        high_confidence = pattern_config.get("high_confidence", False)
        limit = pattern_config.get("limit", 50)
        
        # Build WHERE clauses
        where_clauses = []
        params = {"limit": limit}
        
        if verified_only:
            where_clauses.append("r.status = 'verified'")
        
        if high_confidence:
            where_clauses.append("r.confidence >= 0.8")
        
        if node1_name:
            where_clauses.append("toLower(n1.name) CONTAINS toLower($node1_name)")
            params["node1_name"] = node1_name
        
        if node2_name:
            where_clauses.append("toLower(n2.name) CONTAINS toLower($node2_name)")
            params["node2_name"] = node2_name
        
        # Build node patterns
        n1_pattern = "n1:Entity"
        if node1_type:
            params["node1_type"] = node1_type
            where_clauses.append(
                "(EXISTS { (n1)-[:IS_A]->(:Concept {name: $node1_type}) } OR ($node1_type = 'Concept' AND NOT EXISTS { (n1)-[:IS_A]->(:Concept) }))"
            )
    
        n2_pattern = "n2:Entity"
        if node2_type:
            params["node2_type"] = node2_type
            where_clauses.append(
                "(EXISTS { (n2)-[:IS_A]->(:Concept {name: $node2_type}) } OR ($node2_type = 'Concept' AND NOT EXISTS { (n2)-[:IS_A]->(:Concept) }))"
            )
        
        # Build relationship pattern
        if rel_type:
            rel_pattern = f"-[r:{rel_type}]->"
        else:
            rel_pattern = "-[r]->"
        
        # Build WHERE clause
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        
        cypher = f"""
        MATCH ({n1_pattern}){rel_pattern}({n2_pattern})
        {where_clause}
        
          WITH n1, n2, r
          CALL {{
            WITH n1
            OPTIONAL MATCH (n1)-[:IS_A]->(t1:Concept)
            RETURN CASE WHEN count(t1) = 0 THEN ['Concept'] ELSE collect(DISTINCT t1.name) END AS node1_types
          }}
          CALL {{
            WITH n2
            OPTIONAL MATCH (n2)-[:IS_A]->(t2:Concept)
            RETURN CASE WHEN count(t2) = 0 THEN ['Concept'] ELSE collect(DISTINCT t2.name) END AS node2_types
          }}
          
          RETURN {{
            node1: {{id: coalesce(n1.id, n1.name, elementId(n1)), name: n1.name, types: node1_types, type: head(node1_types)}},
            relationship: {{type: type(r), confidence: r.confidence, status: r.status}},
            node2: {{id: coalesce(n2.id, n2.name, elementId(n2)), name: n2.name, types: node2_types, type: head(node2_types)}}
          }} AS match
          LIMIT $limit
          """
        
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, **params)
            matches = [record["match"] for record in result]
            
            return {
                "success": True,
                "matches_found": len(matches),
                "matches": matches,
                "message": f"Found {len(matches)} matching pattern(s)"
            }
            
    except Exception as exc:
        logger.error(f"Pattern query failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "message": "Failed to execute pattern query"
        }


