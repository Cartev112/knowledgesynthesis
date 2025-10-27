# Aura Agent Configuration for Knowledge Synthesis Platform

## Overview
This document provides the complete configuration for the Neo4j Aura Agent to enable detailed, relational concept elaboration with proper GraphRAG capabilities.

## Agent Purpose
The agent should:
- Elaborate on concepts in detail using both entity and relationship data
- Explain relationships between concepts with evidence from source documents
- Traverse the knowledge graph to provide comprehensive, contextual answers
- Cite sources with document titles and page numbers
- Use a combination of vector similarity and graph traversal

---

## System Prompt

```
You are a Knowledge Synthesis Agent, an expert AI assistant specialized in exploring and explaining concepts from a unified knowledge graph built from multiple research documents.

Your knowledge graph contains:
- **Entities**: Concepts, methods, findings, and other knowledge elements extracted from documents
- **Relationships**: Typed connections between entities (e.g., "inhibits", "treats", "causes") with original text evidence
- **Documents**: Source materials with titles and page numbers for citation

Your primary responsibilities:
1. **Elaborate on concepts relationally**: When asked about a concept, explain it through its relationships to other concepts
2. **Provide evidence**: Always cite the original text snippets and source documents (title + page number)
3. **Traverse the graph**: Use relationships to build comprehensive, multi-hop explanations
4. **Synthesize across sources**: When multiple documents mention the same concept, synthesize the information
5. **Be precise**: Ground all answers in the actual graph data - never hallucinate relationships

**Tool Usage Strategy**:
- Start with `entity_similarity_search` to find the most relevant concept(s)
- Use `get_entity_relationships` to retrieve all relationships for those concepts
- Use `get_entity_neighborhood` to explore connected concepts in depth
- Use `document_similarity_search` if the question is about broader document content
- Use `text2cypher_aggregation` only for counting, statistics, or queries not covered by other tools

**Response Format**:
When explaining a concept:
1. Brief definition/overview
2. Key relationships organized by type (what it inhibits, what it treats, etc.)
3. Evidence snippets with citations [Document Title, p.X]
4. Connected concepts and their significance
5. Multi-document synthesis if applicable

Be thorough but concise. Always prioritize accuracy over completeness.
```

---

## Tool Configurations

### Tool 1: Entity Similarity Search
**Type**: Similarity Search  
**Name**: `entity_similarity_search`  
**Description**:
```
Given a query about a concept, entity, or topic, find the most semantically similar entities in the knowledge graph. Use this as the FIRST step to identify relevant concepts before retrieving their relationships.
```

**Configuration**:
- **Index Name**: `entity_embedding_idx`
- **Embedding Provider**: OpenAI
- **Embedding Model**: `text-embedding-3-small` (or your configured model)
- **Top K**: 5

---

### Tool 2: Get Entity Relationships
**Type**: Cypher Template  
**Name**: `get_entity_relationships`  
**Description**:
```
Given an entity name, retrieve ALL relationships (incoming and outgoing) for that entity, including:
- Connected entities (subjects and objects)
- Relationship types (predicates)
- Original text evidence
- Source documents with page numbers
- Relationship metadata (confidence, status)

Use this tool AFTER finding entities with similarity search to get detailed relational information.
```

**Parameters**:
- **Name**: `entity_name`
- **Type**: `string`
- **Description**: `The exact name of the entity to retrieve relationships for`

**Cypher Query**:
```cypher
MATCH (e:Entity {name: $entity_name})

// Get outgoing relationships (exclude EXTRACTED_FROM which links entities to documents)
OPTIONAL MATCH (e)-[r_out]->(target:Entity)
WHERE type(r_out) <> 'EXTRACTED_FROM'
WITH e, 
     collect({
       direction: 'outgoing',
       predicate: type(r_out),
       target_entity: target.name,
       target_type: target.type,
       evidence: r_out.original_text,
       sources: r_out.sources,
       page: r_out.page_number,
       confidence: r_out.confidence,
       status: r_out.status
     }) as outgoing_rels

// Get incoming relationships (exclude EXTRACTED_FROM)
OPTIONAL MATCH (source:Entity)-[r_in]->(e)
WHERE type(r_in) <> 'EXTRACTED_FROM'
WITH e, outgoing_rels,
     collect({
       direction: 'incoming',
       predicate: type(r_in),
       source_entity: source.name,
       source_type: source.type,
       evidence: r_in.original_text,
       sources: r_in.sources,
       page: r_in.page_number,
       confidence: r_in.confidence,
       status: r_in.status
     }) as incoming_rels

// Filter out null entries (from OPTIONAL MATCH when no relationships exist)
WITH e, 
     [rel IN outgoing_rels WHERE rel.target_entity IS NOT NULL] as outgoing_filtered,
     [rel IN incoming_rels WHERE rel.source_entity IS NOT NULL] as incoming_filtered

RETURN 
  e.name as entity_name,
  coalesce(e.type, 'Entity') as entity_type,
  coalesce(e.significance, 0) as significance,
  outgoing_filtered as outgoing_rels,
  incoming_filtered as incoming_rels,
  size(outgoing_filtered) + size(incoming_filtered) as total_relationships
```

---

### Tool 3: Get Entity Neighborhood
**Type**: Cypher Template  
**Name**: `get_entity_neighborhood`  
**Description**:
```
Given an entity name, retrieve a 2-hop neighborhood showing:
- Direct neighbors (1-hop)
- Second-degree connections (2-hop)
- Relationship paths with evidence

Use this to explore broader context and discover indirect connections between concepts.
```

**Parameters**:
- **Name**: `entity_name`
- **Type**: `string`
- **Description**: `The exact name of the entity to explore neighborhood for`
- **Name**: `max_neighbors`
- **Type**: `integer`
- **Description**: `Maximum number of neighbors to return (default: 10)`

**Cypher Query**:
```cypher
MATCH (e:Entity {name: $entity_name})

// Get 1-hop neighbors (both directions, exclude EXTRACTED_FROM)
OPTIONAL MATCH (e)-[r1]-(n1:Entity)
WHERE type(r1) <> 'EXTRACTED_FROM'
WITH e, 
     collect(DISTINCT {
       entity: n1.name,
       entity_type: n1.type,
       relationship: type(r1),
       evidence: r1.original_text,
       sources: r1.sources,
       page: r1.page_number,
       confidence: r1.confidence,
       hop: 1
     }) as neighbors_1hop_raw
ORDER BY size(neighbors_1hop_raw) DESC

// Filter nulls and limit
WITH e, 
     [n IN neighbors_1hop_raw WHERE n.entity IS NOT NULL][0..coalesce($max_neighbors, 10)] as neighbors_1hop

// Get 2-hop neighbors (exclude EXTRACTED_FROM)
OPTIONAL MATCH (e)-[r1]-(n1:Entity)-[r2]-(n2:Entity)
WHERE n2 <> e AND n1 IS NOT NULL AND n2 IS NOT NULL
  AND type(r1) <> 'EXTRACTED_FROM' AND type(r2) <> 'EXTRACTED_FROM'
WITH e, neighbors_1hop,
     collect(DISTINCT {
       entity: n2.name,
       entity_type: n2.type,
       path: [type(r1), n1.name, type(r2)],
       hop: 2
     }) as neighbors_2hop_raw

// Filter nulls and limit
WITH e, neighbors_1hop,
     [n IN neighbors_2hop_raw WHERE n.entity IS NOT NULL][0..5] as neighbors_2hop

RETURN 
  e.name as entity_name,
  neighbors_1hop,
  neighbors_2hop,
  size(neighbors_1hop) as direct_neighbor_count,
  size(neighbors_2hop) as indirect_neighbor_count
```

---

### Tool 4: Document Similarity Search
**Type**: Similarity Search  
**Name**: `document_similarity_search`  
**Description**:
```
Given a query about document content or broader topics, find the most semantically similar documents. Use this when the question is about document-level information rather than specific entities.
```

**Configuration**:
- **Index Name**: `document_embedding_idx`
- **Embedding Provider**: OpenAI
- **Embedding Model**: `text-embedding-3-small`
- **Top K**: 5

---

### Tool 5: Get Document Entities
**Type**: Cypher Template  
**Name**: `get_document_entities`  
**Description**:
```
Given a document ID, retrieve all entities and relationships extracted from that document. Use this to understand what knowledge was extracted from a specific source.
```

**Parameters**:
- **Name**: `document_id`
- **Type**: `string`
- **Description**: `The document ID to retrieve entities for`

**Cypher Query**:
```cypher
MATCH (d:Document {document_id: $document_id})
OPTIONAL MATCH (s:Entity)-[r]->(o:Entity)
WHERE $document_id IN r.sources
WITH d, s, r, o,
     type(r) as rel_type,
     r.original_text as evidence,
     r.page_number as page,
     r.confidence as conf
ORDER BY page, conf DESC
RETURN 
  d.document_id as document_id,
  d.title as document_title,
  collect({
    subject: s.name,
    subject_type: s.type,
    predicate: rel_type,
    object: o.name,
    object_type: o.type,
    evidence: evidence,
    page: page,
    confidence: conf
  })[0..50] as relationships
```

---

### Tool 6: Text2Cypher for Aggregation
**Type**: Text2Cypher  
**Name**: `text2cypher_aggregation`  
**Description**:
```
Use this tool ONLY for aggregation queries, statistics, or complex questions not covered by other tools. Examples:
- "How many entities are in the graph?"
- "What are the top 10 most connected concepts?"
- "List all relationship types in the database"
- "Which documents have the most extractions?"

Do NOT use this for simple entity or relationship lookups - use the Cypher template tools instead.
```

---

## Embedding Strategy

### Current State
You currently embed:
- **Entities**: `Entity.embedding` (entity name + type)
- **Documents**: `Document.embedding` (document title + content)

### Recommended Enhancement: Triplet Embeddings

To improve retrieval, consider adding a **Relationship embedding** approach:

**Option A: Embed relationship text directly**
- Create embeddings from `relationship.original_text`
- Store as `relationship.embedding` property
- Create a relationship vector index

**Option B: Embed triplet strings**
- Embed formatted triplets: `"{subject} {predicate} {object}"`
- Store on relationship or create intermediate `Triplet` nodes
- Enables semantic search over relationship patterns

**Implementation** (if you want this):
```python
# In your extraction/ingestion code
def embed_triplet(subject: str, predicate: str, object: str, original_text: str) -> List[float]:
    """Embed a triplet for semantic search"""
    # Combine structured + unstructured
    triplet_text = f"{subject} {predicate} {object}. Context: {original_text}"
    return _embed_query(triplet_text)

# Store on relationship
relationship_props = {
    'original_text': original_text,
    'embedding': embed_triplet(s, p, o, original_text),
    # ... other props
}
```

Then add a **Tool 7: Relationship Similarity Search** to find semantically similar relationships.

---

## Example Agent Interaction

**User**: "Tell me about endovascular BCI"

**Agent Reasoning**:
1. Call `entity_similarity_search("endovascular BCI")` → finds entity "endovascular BCI"
2. Call `get_entity_relationships(entity_name="endovascular BCI")` → retrieves all relationships
3. Parse relationships to identify key connections (e.g., "is a" minimally invasive alternative, "enables" stable neural recordings)
4. Call `get_entity_neighborhood(entity_name="endovascular BCI")` → discover related concepts like "craniotomy", "neural recordings"
5. Synthesize response with evidence and citations

**Agent Response**:
```
Endovascular BCI (Brain-Computer Interface) is a minimally invasive brain-computer interface technology that offers an alternative to traditional surgical approaches.

**Key Characteristics**:
- **Type**: Minimally invasive BCI solution
- **Alternative to**: Craniotomy-based BCIs [Source: Document X, p.5]
- **Enables**: Stable neural recordings without open brain surgery [Source: Document X, p.7]

**Relationships**:
1. **Compared to traditional methods**:
   - Avoids craniotomy procedures, which require opening the skull [Document X, p.5]
   - Provides a viable BCI solution with reduced surgical risk [Document Y, p.12]

2. **Technical capabilities**:
   - Achieves stable neural recordings over extended periods [Document X, p.7]
   - Can elicit cortical activation for brain signal decoding [Document Z, p.3]

3. **Related concepts**:
   - Connected to brain_signal_decoding (enables this capability)
   - Part of broader BCI_performance research area
   - Represents advancement in minimally invasive neural interfaces

**Evidence Summary**:
The concept appears in 3 documents with 8 verified relationships, indicating it's a well-documented alternative approach to brain-computer interfaces that prioritizes patient safety through minimally invasive techniques.
```

---

## Configuration Checklist

In Neo4j Aura Agent Console:

- [ ] Set system prompt (copy from "System Prompt" section above)
- [ ] Add Tool 1: `entity_similarity_search` (Similarity Search)
- [ ] Add Tool 2: `get_entity_relationships` (Cypher Template)
- [ ] Add Tool 3: `get_entity_neighborhood` (Cypher Template)
- [ ] Add Tool 4: `document_similarity_search` (Similarity Search)
- [ ] Add Tool 5: `get_document_entities` (Cypher Template)
- [ ] Add Tool 6: `text2cypher_aggregation` (Text2Cypher)
- [ ] Test with sample queries
- [ ] Verify citations and evidence appear in responses
- [ ] Adjust Top K values based on response quality

---

## Testing Queries

After configuration, test with:

1. **Simple concept query**: "What is endovascular BCI?"
2. **Relationship query**: "How does aspirin relate to COX-2?"
3. **Multi-hop query**: "What connects BRAF mutations to drug resistance?"
4. **Document query**: "What does Document X discuss?"
5. **Aggregation query**: "What are the top 5 most connected concepts?"

Expected behavior: Agent should use 2-3 tools per query, provide detailed relational explanations with evidence.

---

## Troubleshooting

### Agent still loops on similarity search
- **Cause**: System prompt not clear enough about tool usage
- **Fix**: Emphasize in prompt: "ALWAYS follow similarity search with get_entity_relationships"

### No evidence/citations in responses
- **Cause**: Cypher queries not returning `original_text` or `sources`
- **Fix**: Verify relationship properties exist in your graph, check Cypher query results

### Responses too brief
- **Cause**: System prompt doesn't emphasize thoroughness
- **Fix**: Add to prompt: "Provide comprehensive explanations with all available relationships"

### Agent uses Text2Cypher for everything
- **Cause**: Text2Cypher description too broad
- **Fix**: Make description very restrictive, emphasize "ONLY for aggregation"

---

## Future Enhancements

1. **Conversation Memory**: Add conversation history to maintain context across queries
2. **Triplet Embeddings**: Implement relationship-level embeddings for better retrieval
3. **Multi-Document Synthesis Tool**: Dedicated Cypher template for cross-document analysis
4. **Contradiction Detection**: Tool to find conflicting relationships
5. **Temporal Analysis**: If you add timestamps, enable temporal reasoning

---

**Last Updated**: 2025-10-26  
**Version**: 1.0
