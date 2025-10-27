# Triplet Embeddings Implementation Guide

## Overview
This guide explains how to implement relationship-level embeddings (triplet embeddings) to enhance the GraphRAG agent's ability to find semantically similar relationships, not just entities.

## Why Triplet Embeddings?

### Current Limitation
Your system currently embeds:
- **Entity names**: "endovascular BCI" → embedding vector
- **Document content**: Full document text → embedding vector

**Problem**: When a user asks "What inhibits COX-2?", the agent can find the entity "COX-2" but cannot directly search for relationships of type "inhibits".

### With Triplet Embeddings
You can search for:
- Relationships by semantic meaning: "What blocks inflammation?"
- Similar relationship patterns: "Find all inhibition relationships"
- Contextual relationships: "Neural recording techniques"

## Architecture Options

### Option A: Embed on Relationships (Recommended)
Store embeddings directly on relationship properties.

**Pros**:
- Simple schema
- Direct relationship search
- No additional nodes

**Cons**:
- Relationships can't be indexed with vector indexes in Neo4j <5.18
- Workaround: Store in separate lookup structure

### Option B: Triplet Nodes
Create intermediate `Triplet` nodes that represent relationships.

**Pros**:
- Can use vector indexes (nodes are indexable)
- Easier to query
- Can add metadata to triplets

**Cons**:
- More complex schema
- Duplicate data (relationship exists twice)

**Recommended**: Use Option B for Neo4j compatibility.

## Implementation: Option B (Triplet Nodes)

### 1. Schema Design

```cypher
// New node type
(:Triplet {
  id: string,              // Unique ID
  subject: string,         // Entity name
  predicate: string,       // Relationship type
  object: string,          // Entity name
  original_text: string,   // Evidence text
  embedding: list<float>,  // Vector embedding
  sources: list<string>,   // Document IDs
  page_number: int,
  confidence: float,
  status: string,
  created_at: datetime
})

// Relationships
(:Triplet)-[:ABOUT_SUBJECT]->(:Entity)
(:Triplet)-[:ABOUT_OBJECT]->(:Entity)
(:Triplet)-[:FROM_DOCUMENT]->(:Document)
```

### 2. Modify Extraction Code

Update `backendAndUI/python_worker/app/services/graph_write.py`:

```python
def _embed_triplet(subject: str, predicate: str, object: str, original_text: str) -> List[float]:
    """
    Create embedding for a triplet combining structured and unstructured information.
    
    Format: "{subject} {predicate} {object}. Evidence: {original_text}"
    """
    if settings.openai_dry_run or not settings.openai_api_key:
        # Dry run mode
        dim = settings.openai_embedding_dim
        combined = f"{subject}{predicate}{object}{original_text}"
        return [(hash(combined + str(i)) % 1000) / 1000.0 for i in range(dim)]
    
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Combine structured triplet with contextual evidence
    triplet_text = f"{subject} {predicate} {object}. Context: {original_text[:500]}"
    
    resp = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=[triplet_text]
    )
    return resp.data[0].embedding


def write_triplet_with_embedding(
    subject: str,
    predicate: str,
    object: str,
    original_text: str,
    sources: List[str],
    page_number: Optional[int] = None,
    confidence: float = 1.0,
    status: str = "unverified"
) -> str:
    """
    Write a triplet node with embedding to Neo4j.
    Also creates the traditional relationship for backward compatibility.
    
    Returns: triplet_id
    """
    # Generate embedding
    embedding = _embed_triplet(subject, predicate, object, original_text)
    
    # Create unique ID
    import hashlib
    triplet_id = hashlib.md5(
        f"{subject}|{predicate}|{object}|{sources[0]}".encode()
    ).hexdigest()
    
    cypher = """
    // Create or merge entities (existing logic)
    MERGE (s:Entity {name: $subject})
    ON CREATE SET s.type = 'Concept', s.created_at = datetime()
    
    MERGE (o:Entity {name: $object})
    ON CREATE SET o.type = 'Concept', o.created_at = datetime()
    
    // Create traditional relationship (for backward compatibility)
    CALL apoc.merge.relationship(
        s, $predicate, {}, 
        {
            original_text: $original_text,
            sources: $sources,
            page_number: $page_number,
            confidence: $confidence,
            status: $status,
            created_at: datetime()
        },
        o
    ) YIELD rel as traditional_rel
    
    // Create Triplet node with embedding
    MERGE (t:Triplet {id: $triplet_id})
    ON CREATE SET 
        t.subject = $subject,
        t.predicate = $predicate,
        t.object = $object,
        t.original_text = $original_text,
        t.embedding = $embedding,
        t.sources = $sources,
        t.page_number = $page_number,
        t.confidence = $confidence,
        t.status = $status,
        t.created_at = datetime()
    ON MATCH SET
        t.sources = t.sources + [x IN $sources WHERE NOT x IN t.sources]
    
    // Link triplet to entities
    MERGE (t)-[:ABOUT_SUBJECT]->(s)
    MERGE (t)-[:ABOUT_OBJECT]->(o)
    
    // Link triplet to documents
    WITH t, $sources as doc_ids
    UNWIND doc_ids as doc_id
    MERGE (d:Document {document_id: doc_id})
    MERGE (t)-[:FROM_DOCUMENT]->(d)
    
    RETURN t.id as triplet_id
    """
    
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        result = session.run(
            cypher,
            subject=subject,
            predicate=predicate,
            object=object,
            original_text=original_text,
            sources=sources,
            page_number=page_number,
            confidence=confidence,
            status=status,
            embedding=embedding,
            triplet_id=triplet_id
        )
        record = result.single()
        return record["triplet_id"] if record else triplet_id
```

### 3. Create Vector Index

Add to `backendAndUI/python_worker/app/services/graph_embeddings.py`:

```python
def ensure_triplet_vector_index():
    """Create vector index for Triplet node embeddings."""
    index_name = "triplet_embedding_idx"
    
    # Check if index exists
    check_cypher = "SHOW VECTOR INDEXES YIELD name WHERE name = $name RETURN count(*) as exists"
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        result = session.run(check_cypher, name=index_name)
        exists = result.single()["exists"] > 0
        
        if exists:
            logger.info(f"Vector index '{index_name}' already exists")
            return
    
    # Create index
    create_cypher = f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (t:Triplet)
    ON t.embedding
    OPTIONS {{
        indexConfig: {{
            `vector.dimensions`: {settings.openai_embedding_dim},
            `vector.similarity_function`: 'cosine'
        }}
    }}
    """
    
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        session.run(create_cypher)
        logger.info(f"Created vector index '{index_name}'")


def ensure_vector_indexes():
    """Ensure all vector indexes exist."""
    ensure_entity_vector_index()
    ensure_document_vector_index()
    ensure_triplet_vector_index()  # Add this line
```

### 4. Update Ingestion Pipeline

Modify `backendAndUI/python_worker/app/services/openai_extract.py`:

```python
# In the function that writes triplets to Neo4j
from .graph_write import write_triplet_with_embedding

# Replace existing triplet writing logic with:
for triplet in extracted_triplets:
    triplet_id = write_triplet_with_embedding(
        subject=triplet.subject,
        predicate=triplet.predicate,
        object=triplet.object,
        original_text=triplet.original_text,
        sources=[document_id],
        page_number=triplet.page_number,
        confidence=triplet.confidence,
        status="unverified"
    )
```

### 5. Add Aura Agent Tool

In Neo4j Aura Agent Console, add:

**Tool 7: Triplet Similarity Search**
- **Type**: Similarity Search
- **Name**: `triplet_similarity_search`
- **Description**: 
```
Given a query about relationships, actions, or interactions between concepts, find the most semantically similar triplets (subject-predicate-object statements) in the knowledge graph. Use this to find relationships by their meaning, not just entity names.

Examples:
- "What inhibits inflammation?"
- "Find treatment relationships"
- "What causes drug resistance?"
```
- **Index Name**: `triplet_embedding_idx`
- **Embedding Model**: `text-embedding-3-small`
- **Top K**: 8

**Tool 8: Get Triplet Details**
- **Type**: Cypher Template
- **Name**: `get_triplet_details`
- **Description**:
```
Given a triplet ID, retrieve full details including subject, predicate, object, evidence text, sources, and connected entities.
```
- **Parameters**:
  - Name: `triplet_id`, Type: `string`, Description: "The ID of the triplet to retrieve"
- **Cypher Query**:
```cypher
MATCH (t:Triplet {id: $triplet_id})
OPTIONAL MATCH (t)-[:ABOUT_SUBJECT]->(s:Entity)
OPTIONAL MATCH (t)-[:ABOUT_OBJECT]->(o:Entity)
OPTIONAL MATCH (t)-[:FROM_DOCUMENT]->(d:Document)
RETURN 
  t.id as triplet_id,
  t.subject as subject,
  t.predicate as predicate,
  t.object as object,
  t.original_text as evidence,
  t.confidence as confidence,
  t.status as status,
  s.type as subject_type,
  o.type as object_type,
  collect(DISTINCT {
    document_id: d.document_id,
    title: d.title,
    page: t.page_number
  }) as sources
```

### 6. Update System Prompt

Add to the Aura Agent system prompt:

```
**Tool Usage for Relationship Queries**:
- If the question is about relationships, actions, or interactions (e.g., "what inhibits X?", "how does Y affect Z?"), use `triplet_similarity_search` FIRST
- Follow up with `get_triplet_details` to get full context
- Then use `get_entity_relationships` to explore further connections
```

## Migration Strategy

### For Existing Data

Create a migration script to embed existing relationships:

```python
# scripts/migrate_to_triplet_embeddings.py

from backendAndUI.python_worker.app.core.settings import settings
from backendAndUI.python_worker.app.services.neo4j_client import neo4j_client
from backendAndUI.python_worker.app.services.graph_write import _embed_triplet
import logging

logger = logging.getLogger(__name__)

def migrate_existing_relationships():
    """Convert existing relationships to Triplet nodes with embeddings."""
    
    # Fetch all relationships
    cypher = """
    MATCH (s:Entity)-[r]->(o:Entity)
    WHERE NOT type(r) = 'EXTRACTED_FROM'
    RETURN 
      s.name as subject,
      type(r) as predicate,
      o.name as object,
      r.original_text as original_text,
      r.sources as sources,
      r.page_number as page_number,
      r.confidence as confidence,
      r.status as status
    LIMIT 1000
    """
    
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        results = list(session.run(cypher))
    
    logger.info(f"Found {len(results)} relationships to migrate")
    
    # Process in batches
    from .graph_write import write_triplet_with_embedding
    
    for i, record in enumerate(results):
        try:
            write_triplet_with_embedding(
                subject=record["subject"],
                predicate=record["predicate"],
                object=record["object"],
                original_text=record["original_text"] or "",
                sources=record["sources"] or [],
                page_number=record["page_number"],
                confidence=record["confidence"] or 1.0,
                status=record["status"] or "unverified"
            )
            
            if (i + 1) % 100 == 0:
                logger.info(f"Migrated {i + 1}/{len(results)} relationships")
        except Exception as e:
            logger.error(f"Failed to migrate relationship {i}: {e}")
    
    logger.info("Migration complete")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_existing_relationships()
```

Run with:
```bash
python scripts/migrate_to_triplet_embeddings.py
```

## Testing

### 1. Verify Index Creation
```cypher
SHOW VECTOR INDEXES
// Should show triplet_embedding_idx
```

### 2. Test Triplet Search
```cypher
MATCH (t:Triplet)
CALL db.index.vector.queryNodes('triplet_embedding_idx', 5, t.embedding)
YIELD node, score
RETURN node.subject, node.predicate, node.object, score
LIMIT 5
```

### 3. Test Agent Query
Ask: "What inhibits COX-2?"

Expected: Agent uses `triplet_similarity_search` to find inhibition relationships, then provides detailed answer with evidence.

## Performance Considerations

### Embedding Cost
- Each triplet requires 1 OpenAI API call
- For 1000 triplets: ~$0.02 with text-embedding-3-small
- Consider batch processing for large migrations

### Storage
- Each embedding: 1536 floats × 4 bytes = ~6KB
- 10,000 triplets: ~60MB of embedding data
- Neo4j handles this efficiently

### Query Performance
- Vector search: O(log n) with HNSW index
- Expect <100ms for most queries
- Monitor with `PROFILE` in Neo4j Browser

## Troubleshooting

### Embeddings not created
- Check `OPENAI_API_KEY` is set
- Verify `openai_embedding_model` matches Aura Agent config
- Check logs for API errors

### Vector index not found
- Run `ensure_triplet_vector_index()` manually
- Wait for index to reach ONLINE status (check with `SHOW VECTOR INDEXES`)

### Agent doesn't use triplet search
- Update system prompt to emphasize relationship queries
- Make tool description more specific
- Test with explicit relationship questions

## Future Enhancements

1. **Hybrid Search**: Combine triplet + entity search for comprehensive results
2. **Relationship Type Embeddings**: Embed predicate types separately for filtering
3. **Multi-Modal Embeddings**: Include document context in triplet embeddings
4. **Dynamic Re-Embedding**: Update embeddings when relationships are edited

---

**Last Updated**: 2025-10-26  
**Version**: 1.0
