"""Export endpoints for graph and review queue data."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel


router = APIRouter()


class GraphExportRequest(BaseModel):
    """Request to export graph data."""
    format: str  # json, csv, graphml
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class ReviewExportRequest(BaseModel):
    """Request to export review queue data."""
    format: str  # json, csv
    items: List[Dict[str, Any]]


def generate_json_export(data: Dict[str, Any]) -> str:
    """Generate JSON export with pretty formatting."""
    return json.dumps(data, indent=2, default=str)


def generate_csv_relationships(edges: List[Dict[str, Any]]) -> str:
    """Generate CSV export for relationships."""
    output = io.StringIO()
    
    if not edges:
        return "No relationships to export"
    
    # Define CSV columns
    fieldnames = [
        'source', 'relation', 'target', 'status', 'polarity', 
        'confidence', 'significance', 'source_count'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for edge in edges:
        sources = edge.get('sources', [])
        source_count = len(sources) if isinstance(sources, list) else 0
        
        writer.writerow({
            'source': edge.get('source', ''),
            'relation': edge.get('relation', ''),
            'target': edge.get('target', ''),
            'status': edge.get('status', 'unverified'),
            'polarity': edge.get('polarity', 'positive'),
            'confidence': edge.get('confidence', ''),
            'significance': edge.get('significance', ''),
            'source_count': source_count
        })
    
    return output.getvalue()


def generate_graphml(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """Generate GraphML format for Cytoscape and other tools."""
    graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
    graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns"')
    graphml.append('         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    graphml.append('         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns')
    graphml.append('         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">')
    
    # Define keys (attributes)
    graphml.append('  <key id="label" for="node" attr.name="label" attr.type="string"/>')
    graphml.append('  <key id="type" for="node" attr.name="type" attr.type="string"/>')
    graphml.append('  <key id="significance" for="node" attr.name="significance" attr.type="int"/>')
    graphml.append('  <key id="relation" for="edge" attr.name="relation" attr.type="string"/>')
    graphml.append('  <key id="status" for="edge" attr.name="status" attr.type="string"/>')
    graphml.append('  <key id="polarity" for="edge" attr.name="polarity" attr.type="string"/>')
    graphml.append('  <key id="confidence" for="edge" attr.name="confidence" attr.type="double"/>')
    graphml.append('  <key id="significance_edge" for="edge" attr.name="significance" attr.type="int"/>')
    
    graphml.append('  <graph id="KnowledgeGraph" edgedefault="directed">')
    
    # Add nodes
    for node in nodes:
        node_id = str(node.get('id', '')).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        graphml.append(f'    <node id="{node_id}">')
        
        label = str(node.get('label', '')).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        graphml.append(f'      <data key="label">{label}</data>')
        
        node_type_value = node.get('type')
        if not node_type_value:
            types_list = node.get('types')
            if isinstance(types_list, list) and types_list:
                node_type_value = ", ".join(types_list)
        if node_type_value:
            node_type = str(node_type_value).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            graphml.append(f'      <data key="type">{node_type}</data>')
        
        if node.get('significance'):
            graphml.append(f'      <data key="significance">{node["significance"]}</data>')
        
        graphml.append('    </node>')
    
    # Add edges
    for i, edge in enumerate(edges):
        source = str(edge.get('source', '')).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        target = str(edge.get('target', '')).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        edge_id = f"e{i}"
        
        graphml.append(f'    <edge id="{edge_id}" source="{source}" target="{target}">')
        
        relation = str(edge.get('relation', '')).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        graphml.append(f'      <data key="relation">{relation}</data>')
        
        if edge.get('status'):
            status = str(edge['status']).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            graphml.append(f'      <data key="status">{status}</data>')
        
        if edge.get('polarity'):
            polarity = str(edge['polarity']).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            graphml.append(f'      <data key="polarity">{polarity}</data>')
        
        if edge.get('confidence') is not None:
            graphml.append(f'      <data key="confidence">{edge["confidence"]}</data>')
        
        if edge.get('significance'):
            graphml.append(f'      <data key="significance_edge">{edge["significance"]}</data>')
        
        graphml.append('    </edge>')
    
    graphml.append('  </graph>')
    graphml.append('</graphml>')
    
    return '\n'.join(graphml)


def generate_review_csv(items: List[Dict[str, Any]]) -> str:
    """Generate CSV export for review queue."""
    output = io.StringIO()
    
    if not items:
        return "No items to export"
    
    # Define CSV columns
    fieldnames = [
        'subject', 'subject_type', 'predicate', 'object', 'object_type',
        'status', 'confidence', 'original_text', 'document_count'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for item in items:
        documents = item.get('documents', [])
        doc_count = len(documents) if isinstance(documents, list) else 0
        
        subject_type_value = item.get('subject_type')
        if not subject_type_value:
            subject_types = item.get('subject_types')
            if isinstance(subject_types, list) and subject_types:
                subject_type_value = "; ".join(subject_types)
            else:
                subject_type_value = ''
        
        object_type_value = item.get('object_type')
        if not object_type_value:
            object_types = item.get('object_types')
            if isinstance(object_types, list) and object_types:
                object_type_value = "; ".join(object_types)
            else:
                object_type_value = ''
        
        writer.writerow({
            'subject': item.get('subject', ''),
            'subject_type': subject_type_value,
            'predicate': item.get('predicate', ''),
            'object': item.get('object', ''),
            'object_type': object_type_value,
            'status': item.get('status', 'unverified'),
            'confidence': item.get('confidence', ''),
            'original_text': item.get('original_text', ''),
            'document_count': doc_count
        })
    
    return output.getvalue()


@router.post("/graph")
async def export_graph(request: GraphExportRequest):
    """
    Export graph data in various formats.
    
    Supports:
    - JSON: Full graph data with all properties
    - CSV: Relationships in tabular format
    - GraphML: Standard graph format for Cytoscape, Gephi, etc.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if request.format == "json":
            data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "node_count": len(request.nodes),
                    "edge_count": len(request.edges)
                },
                "nodes": request.nodes,
                "edges": request.edges
            }
            content = generate_json_export(data)
            filename = f"knowledge_graph_{timestamp}.json"
            media_type = "application/json"
            
        elif request.format == "csv":
            content = generate_csv_relationships(request.edges)
            filename = f"knowledge_graph_relationships_{timestamp}.csv"
            media_type = "text/csv"
            
        elif request.format == "graphml":
            content = generate_graphml(request.nodes, request.edges)
            filename = f"knowledge_graph_{timestamp}.graphml"
            media_type = "application/xml"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")


@router.post("/review")
async def export_review_queue(request: ReviewExportRequest):
    """
    Export review queue data in various formats.
    
    Supports:
    - JSON: Full review data with all properties
    - CSV: Review items in tabular format
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if request.format == "json":
            data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "item_count": len(request.items)
                },
                "items": request.items
            }
            content = generate_json_export(data)
            filename = f"review_queue_{timestamp}.json"
            media_type = "application/json"
            
        elif request.format == "csv":
            content = generate_review_csv(request.items)
            filename = f"review_queue_{timestamp}.csv"
            media_type = "text/csv"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")
