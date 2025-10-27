# Aura Agent Quick Fix Guide

## Problem Summary
Your agent is stuck in a loop calling `entity_similarity_search` repeatedly because it has no tools to retrieve relationship data after finding entities.

## Root Causes
1. ❌ **Only similarity search tools** - no way to get relationships
2. ❌ **No Cypher templates** - can't traverse the graph
3. ❌ **Empty system prompt** - no guidance on tool usage
4. ❌ **Entity embeddings only** - can't search for relationships semantically

## Quick Fix (30 minutes)

### Step 1: Configure System Prompt (5 min)
In Neo4j Aura Agent Console → Your Agent → Edit:

Copy the **System Prompt** from `docs/AURA_AGENT_CONFIGURATION.md` (lines 17-52)

**Key points**:
- Tells agent to elaborate on concepts relationally
- Defines tool usage strategy
- Specifies response format with citations

### Step 2: Add Cypher Template Tools (15 min)

**Tool 1: get_entity_relationships**
- Type: Cypher Template
- Copy configuration from `docs/AURA_AGENT_CONFIGURATION.md` (lines 77-139)
- **Critical**: This retrieves all relationships for an entity with evidence
- **Important**: Query excludes `EXTRACTED_FROM` relationships (which link entities to documents, not semantic relationships)

**Tool 2: get_entity_neighborhood**
- Type: Cypher Template  
- Copy configuration from `docs/AURA_AGENT_CONFIGURATION.md` (lines 144-210)
- Explores 2-hop connections

**Tool 3: get_document_entities**
- Type: Cypher Template
- Copy configuration from `docs/AURA_AGENT_CONFIGURATION.md` (lines 242-287)
- Gets entities from specific documents

### Step 3: Restrict Text2Cypher (5 min)

If you have a Text2Cypher tool, update its description to:
```
Use this tool ONLY for aggregation queries, statistics, or complex questions not covered by other tools. Do NOT use for entity or relationship lookups.
```

### Step 4: Test (5 min)

Ask: **"Tell me about endovascular BCI"**

**Expected behavior**:
1. Agent calls `entity_similarity_search("endovascular BCI")`
2. Agent calls `get_entity_relationships(entity_name="endovascular BCI")`
3. Agent synthesizes response with relationships and evidence
4. Response includes citations like [Document Title, p.5]

**Expected response structure**:
- Definition/overview
- Key relationships organized by type
- Evidence with citations
- Connected concepts

## Complete Fix (2-3 hours)

### Add Triplet Embeddings

For semantic search over relationships (e.g., "what inhibits X?"):

1. **Implement triplet nodes** - Follow `docs/TRIPLET_EMBEDDINGS_IMPLEMENTATION.md`
2. **Create vector index** - `triplet_embedding_idx`
3. **Add similarity search tool** - `triplet_similarity_search`
4. **Migrate existing data** - Run migration script

**Benefits**:
- Search for relationships by meaning, not just entity names
- Better handling of "what inhibits/treats/causes" queries
- More comprehensive RAG retrieval

## Verification Checklist

After configuration:

- [ ] System prompt is set (not blank)
- [ ] `entity_similarity_search` tool exists (Similarity Search)
- [ ] `get_entity_relationships` tool exists (Cypher Template)
- [ ] `get_entity_neighborhood` tool exists (Cypher Template)
- [ ] Text2Cypher is restricted to aggregation only
- [ ] Test query returns detailed relational response
- [ ] Response includes evidence citations
- [ ] Agent uses 2-3 tools per query (not just similarity search)

## Common Issues

### Agent still loops
**Fix**: Make system prompt more explicit:
```
CRITICAL: After using entity_similarity_search, you MUST use get_entity_relationships to retrieve the actual relationship data. Never respond with just entity metadata.
```

### No citations in response
**Fix**: Check Cypher queries return `original_text` and `sources` fields. Verify these properties exist in your graph.

### Responses too brief
**Fix**: Add to system prompt:
```
Provide comprehensive explanations. For each entity, describe ALL its relationships with evidence. Aim for 3-5 paragraphs minimum.
```

### Wrong tool selection
**Fix**: Make tool descriptions more specific. Use examples in descriptions.

## Tool Usage Patterns

### For "Tell me about X"
1. `entity_similarity_search(X)` → find entity
2. `get_entity_relationships(X)` → get all relationships
3. `get_entity_neighborhood(X)` → explore connections
4. Synthesize comprehensive response

### For "How does X relate to Y?"
1. `entity_similarity_search(X)` → find X
2. `entity_similarity_search(Y)` → find Y
3. `get_entity_relationships(X)` → check X's relationships
4. `get_entity_neighborhood(X)` → look for Y in neighborhood
5. Explain connection path

### For "What documents discuss X?"
1. `entity_similarity_search(X)` → find entity
2. `get_entity_relationships(X)` → get relationships with sources
3. Extract unique document IDs from sources
4. List documents with page numbers

## Next Steps

1. **Immediate**: Apply Quick Fix (30 min)
2. **Short-term**: Test with various queries, tune tool descriptions
3. **Medium-term**: Implement triplet embeddings (2-3 hours)
4. **Long-term**: Add conversation memory, contradiction detection

## Resources

- **Full Configuration**: `docs/AURA_AGENT_CONFIGURATION.md`
- **Triplet Embeddings**: `docs/TRIPLET_EMBEDDINGS_IMPLEMENTATION.md`
- **Neo4j Aura Agent Docs**: See `agent context/context.txt`

---

**Priority**: HIGH - Agent is currently non-functional  
**Effort**: 30 min (Quick Fix) or 3 hours (Complete Fix)  
**Impact**: Transforms agent from looping to comprehensive relational responses
