# Triplet Embeddings - Usage Guide

## Quick Start

### 1. Enable Triplet Embeddings

Run the setup script:
```bash
python scripts/enable_triplet_embeddings.py
```

This creates the `triplet_embedding_idx` vector index in Neo4j.

### 2. Migrate Existing Data (Optional)

To add embeddings to existing relationships:
```bash
# Migrate all relationships
python scripts/migrate_to_triplet_embeddings.py

# Migrate with limit (for testing)
python scripts/migrate_to_triplet_embeddings.py --limit 100

# Verify migration only
python scripts/migrate_to_triplet_embeddings.py --verify-only
```

### 3. Use in New Ingestions

Triplet embeddings are now automatically created for new ingestions. The existing `write_triplets()` function continues to work, but you can also use the new function directly:

```python
from app.services.graph_write import write_triplet_with_embedding

# Write a single triplet with embedding
triplet_id = write_triplet_with_embedding(
    subject="aspirin",
    predicate="inhibits",
    object="COX-2",
    original_text="Aspirin inhibits COX-2 enzyme activity in vitro.",
    sources=["document_123"],
    page_number=5,
    confidence=0.95,
    status="unverified"
)
```

## What Gets Created

For each triplet, the system creates:

1. **Traditional relationship** (backward compatible):
   ```cypher
   (Entity)-[INHIBITS]->(Entity)
   ```

2. **Triplet node** (new):
   ```cypher
   (:Triplet {
     id: "abc123...",
     subject: "aspirin",
     predicate: "inhibits",
     object: "COX-2",
     original_text: "...",
     embedding: [0.123, 0.456, ...],
     sources: ["document_123"],
     ...
   })
   ```

3. **Linking relationships**:
   ```cypher
   (Triplet)-[:ABOUT_SUBJECT]->(Entity)
   (Triplet)-[:ABOUT_OBJECT]->(Entity)
   (Triplet)-[:FROM_DOCUMENT]->(Document)
   ```

## Aura Agent Integration

### Add Similarity Search Tool

**Tool Name**: `triplet_similarity_search`  
**Type**: Similarity Search  
**Description**:
```
Given a query about relationships, actions, or interactions between concepts, find the most semantically similar triplets (subject-predicate-object statements) in the knowledge graph. Use this to find relationships by their meaning, not just entity names.
```
**Index**: `triplet_embedding_idx`  
**Embedding Model**: `text-embedding-3-small`  
**Top K**: 8

### Add Cypher Template Tool

**Tool Name**: `get_triplet_details`  
**Type**: Cypher Template  
**Description**:
```
Given a triplet ID, retrieve full details including subject, predicate, object, evidence text, sources, and connected entities.
```

**Parameters**:
- Name: `triplet_id`, Type: `string`, Description: "The ID of the triplet to retrieve"

**Cypher Query**:
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

### Update System Prompt

Add to your Aura Agent system prompt:

```
**Tool Usage for Relationship Queries**:
- If the question is about relationships, actions, or interactions (e.g., "what inhibits X?", "how does Y affect Z?"), use `triplet_similarity_search` FIRST
- Follow up with `get_triplet_details` to get full context
- Then use `get_entity_relationships` to explore further connections
```

## Testing

### Test Triplet Creation

```python
from app.services.graph_write import write_triplet_with_embedding

triplet_id = write_triplet_with_embedding(
    subject="test_subject",
    predicate="test_predicate",
    object="test_object",
    original_text="This is a test triplet.",
    sources=["test_doc"]
)
print(f"Created triplet: {triplet_id}")
```

### Test Vector Search

In Neo4j Browser:
```cypher
// Find triplets similar to a query
MATCH (t:Triplet)
WHERE t.embedding IS NOT NULL
WITH t LIMIT 1
CALL db.index.vector.queryNodes('triplet_embedding_idx', 5, t.embedding)
YIELD node, score
RETURN node.subject, node.predicate, node.object, score
LIMIT 5
```

### Test Agent Query

Ask the agent: **"What inhibits COX-2?"**

Expected behavior:
1. Agent calls `triplet_similarity_search("what inhibits COX-2")`
2. Finds triplets with "inhibits" relationships
3. Returns detailed answer with evidence

## Performance

### Embedding Cost
- Each triplet: 1 OpenAI API call
- Cost: ~$0.00002 per triplet with text-embedding-3-small
- 1000 triplets: ~$0.02

### Storage
- Each embedding: ~6KB (1536 floats × 4 bytes)
- 10,000 triplets: ~60MB

### Query Speed
- Vector search: <100ms for most queries
- HNSW index provides O(log n) performance

## Troubleshooting

### Embeddings not created
- Check `OPENAI_API_KEY` is set
- Verify `openai_embedding_model` in settings
- Check logs for API errors

### Vector index not found
- Run `python scripts/enable_triplet_embeddings.py`
- Wait for index to reach ONLINE status
- Check with: `SHOW VECTOR INDEXES`

### Migration fails
- Check Neo4j connection
- Verify relationships exist in graph
- Run with `--limit 10` to test small batch

## Files Modified

- ✅ `app/services/graph_write.py` - Added `_embed_triplet()` and `write_triplet_with_embedding()`
- ✅ `app/services/graph_embeddings.py` - Added `TRIPLET_VECTOR_INDEX` and `ensure_triplet_vector_index()`
- ✅ `scripts/migrate_to_triplet_embeddings.py` - Migration script for existing data
- ✅ `scripts/enable_triplet_embeddings.py` - Setup script

## Next Steps

1. ✅ Enable triplet embeddings (run setup script)
2. ✅ Migrate existing data (optional)
3. ⏳ Add Aura Agent tools (triplet_similarity_search, get_triplet_details)
4. ⏳ Update system prompt
5. ⏳ Test with relationship queries

---

**Status**: Implementation complete, ready for testing  
**Version**: 1.0
