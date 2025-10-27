# Aura Agent Debugging Guide

## Issue: get_entity_relationships Returns Null Records

### Symptoms
```json
{
  "keys": ["entity_name", "entity_type", "significance", "outgoing_rels", "incoming_rels", "total_relationships"],
  "records": null,
  "summary": {}
}
```

### Root Causes

1. **Entity doesn't exist** - The entity name doesn't match exactly
2. **Entity has no relationships** - Entity exists but is isolated
3. **Cypher query issue** - Query logic returns null instead of empty arrays
4. **Relationship type mismatch** - Relationships exist but query doesn't find them

---

## Diagnostic Steps

### Step 1: Verify Entity Exists

Run in **Neo4j Browser** (http://localhost:7474):

```cypher
MATCH (e:Entity {name: "endovascular BCI"})
RETURN e.name, e.type, e.significance, labels(e)
```

**Expected**: Should return 1 row with entity details  
**If empty**: Entity name doesn't match exactly - check for:
- Extra spaces
- Case sensitivity
- Special characters

**Fix**: Find actual entity name:
```cypher
MATCH (e:Entity)
WHERE e.name CONTAINS "endovascular"
RETURN e.name
```

---

### Step 2: Check for Relationships

```cypher
MATCH (e:Entity {name: "endovascular BCI"})
OPTIONAL MATCH (e)-[r]-(other:Entity)
RETURN 
  e.name as entity,
  count(r) as relationship_count,
  collect(DISTINCT type(r)) as relationship_types
```

**Expected**: `relationship_count > 0`  
**If 0**: Entity exists but has no relationships

**Possible reasons**:
- Entity was created but relationships weren't
- Relationships point to/from different entities
- Extraction failed for this entity

---

### Step 3: Test Simplified Query

```cypher
MATCH (e:Entity {name: "endovascular BCI"})
OPTIONAL MATCH (e)-[r_out]->(target:Entity)
RETURN 
  e.name,
  count(r_out) as outgoing_count,
  collect({
    predicate: type(r_out),
    target: target.name,
    evidence: r_out.original_text
  })[0..5] as sample_outgoing
```

**Expected**: Should return at least the entity name, even if counts are 0  
**If null**: Query syntax issue - check Neo4j version compatibility

---

### Step 4: Find Any Relationships in Graph

```cypher
MATCH (s:Entity)-[r]->(o:Entity)
WHERE s.name CONTAINS "BCI" OR o.name CONTAINS "BCI"
RETURN 
  s.name as subject,
  type(r) as predicate,
  o.name as object,
  r.original_text as evidence,
  r.sources as sources
LIMIT 10
```

**Expected**: Shows relationships involving BCI-related entities  
**If empty**: No BCI relationships in graph - need to ingest documents

---

### Step 5: Check Relationship Properties

```cypher
MATCH (e:Entity {name: "endovascular BCI"})-[r]-(other)
RETURN 
  type(r) as rel_type,
  keys(r) as properties,
  r.original_text as text,
  r.sources as sources,
  r.page_number as page,
  r.confidence as confidence,
  r.status as status
LIMIT 5
```

**Expected**: Shows relationship properties  
**If missing properties**: Relationships exist but lack metadata (original_text, sources, etc.)

---

## Common Issues & Fixes

### Issue 1: Entity Name Mismatch

**Problem**: Similarity search returns "endovascular BCI" but actual entity is "endovascular BCIs" (plural)

**Solution**: Update Cypher query to use fuzzy matching:

```cypher
MATCH (e:Entity)
WHERE e.name = $entity_name 
   OR e.name = $entity_name + 's'
   OR e.name = $entity_name + 'es'
   OR e.name STARTS WITH $entity_name

// Rest of query...
```

**Better solution**: Use entity ID from similarity search instead of name:

Modify `get_entity_relationships` to accept `entity_id` parameter:
```cypher
MATCH (e:Entity)
WHERE elementId(e) = $entity_id OR e.name = $entity_name

// Rest of query...
```

---

### Issue 2: No Relationships Extracted

**Problem**: Entity exists but has no relationships

**Diagnosis**:
```cypher
MATCH (e:Entity {name: "endovascular BCI"})
OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(d:Document)
RETURN e.name, collect(d.document_id) as documents
```

**If documents exist**: Entity was extracted but relationships weren't  
**If no documents**: Entity was created manually or through consolidation

**Fix**: Re-ingest the document or manually create relationships

---

### Issue 3: Relationships Exist But Query Returns Null

**Problem**: Cypher query logic issue

**Test with minimal query**:
```cypher
MATCH (e:Entity {name: "endovascular BCI"})
RETURN 
  e.name as entity_name,
  e.type as entity_type,
  [] as outgoing_rels,
  [] as incoming_rels,
  0 as total_relationships
```

**If this works**: Issue is in the OPTIONAL MATCH logic  
**If this fails**: Entity doesn't exist

**Fix**: Use the updated Cypher query from `AURA_AGENT_CONFIGURATION.md` (v2)

---

### Issue 4: EXTRACTED_FROM Relationships Interfering

**Problem**: Query matches `EXTRACTED_FROM` relationships instead of semantic relationships

**Diagnosis**:
```cypher
MATCH (e:Entity {name: "endovascular BCI"})-[r]->(other)
RETURN type(r), count(*) as count
```

**If only EXTRACTED_FROM**: No semantic relationships exist

**Fix**: Exclude EXTRACTED_FROM in query:
```cypher
OPTIONAL MATCH (e)-[r_out]->(target:Entity)
WHERE type(r_out) <> 'EXTRACTED_FROM'
// Rest of query...
```

---

## Updated Cypher Query (v2)

Use this **robust version** that handles all edge cases:

```cypher
MATCH (e:Entity {name: $entity_name})

// Get outgoing relationships (exclude EXTRACTED_FROM)
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

// Filter out null entries and ensure we always return a result
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

**Key improvements**:
1. Excludes `EXTRACTED_FROM` relationships
2. Uses `coalesce()` for null safety
3. Filters null entries from collections
4. Always returns a result (even if empty arrays)

---

## Testing Workflow

### 1. Test in Neo4j Browser First

Before updating Aura Agent, test the query:

```cypher
// Set parameter
:param entity_name => "endovascular BCI"

// Run query
MATCH (e:Entity {name: $entity_name})
OPTIONAL MATCH (e)-[r_out]->(target:Entity)
WHERE type(r_out) <> 'EXTRACTED_FROM'
WITH e, 
     collect({
       direction: 'outgoing',
       predicate: type(r_out),
       target_entity: target.name,
       evidence: r_out.original_text
     }) as outgoing_rels
OPTIONAL MATCH (source:Entity)-[r_in]->(e)
WHERE type(r_in) <> 'EXTRACTED_FROM'
WITH e, outgoing_rels,
     collect({
       direction: 'incoming',
       predicate: type(r_in),
       source_entity: source.name,
       evidence: r_in.original_text
     }) as incoming_rels
WITH e, 
     [rel IN outgoing_rels WHERE rel.target_entity IS NOT NULL] as out_filtered,
     [rel IN incoming_rels WHERE rel.source_entity IS NOT NULL] as in_filtered
RETURN 
  e.name,
  out_filtered,
  in_filtered,
  size(out_filtered) + size(in_filtered) as total
```

**Expected output**:
```
e.name: "endovascular BCI"
out_filtered: [{direction: "outgoing", predicate: "IS_A", target_entity: "minimally invasive alternative", ...}, ...]
in_filtered: [...]
total: 5
```

### 2. Update Aura Agent Tool

Once query works in Neo4j Browser:
1. Go to Aura Agent Console
2. Edit `get_entity_relationships` tool
3. Replace Cypher query with tested version
4. Save

### 3. Test Agent

Ask: "Tell me about endovascular BCI"

**Expected**: Agent should now retrieve relationships and provide detailed response

---

## Fallback: Simplified Tool

If the complex query still fails, use this **minimal version**:

**Tool Name**: `get_entity_relationships_simple`

**Cypher**:
```cypher
MATCH (e:Entity {name: $entity_name})
MATCH (e)-[r]->(target:Entity)
WHERE type(r) <> 'EXTRACTED_FROM'
RETURN 
  e.name as entity_name,
  collect({
    predicate: type(r),
    target: target.name,
    evidence: r.original_text,
    sources: r.sources
  })[0..20] as relationships
```

**Pros**: Simple, less likely to fail  
**Cons**: Only outgoing relationships, no incoming

---

## Emergency Diagnostic Script

Save as `scripts/diagnose_entity.py`:

```python
from backendAndUI.python_worker.app.services.neo4j_client import neo4j_client
from backendAndUI.python_worker.app.core.settings import settings

entity_name = "endovascular BCI"

cypher = """
MATCH (e:Entity {name: $name})
OPTIONAL MATCH (e)-[r]-(other:Entity)
RETURN 
  e.name as entity,
  e.type as type,
  count(r) as rel_count,
  collect(DISTINCT type(r))[0..10] as rel_types,
  collect(DISTINCT other.name)[0..10] as connected_entities
"""

with neo4j_client._driver.session(database=settings.neo4j_database) as session:
    result = session.run(cypher, name=entity_name)
    record = result.single()
    
    if record:
        print(f"Entity: {record['entity']}")
        print(f"Type: {record['type']}")
        print(f"Relationship count: {record['rel_count']}")
        print(f"Relationship types: {record['rel_types']}")
        print(f"Connected entities: {record['connected_entities']}")
    else:
        print(f"Entity '{entity_name}' not found")
```

Run: `python scripts/diagnose_entity.py`

---

## Next Steps

1. **Run Step 1-5 diagnostics** to identify the exact issue
2. **Update Cypher query** with the v2 version that excludes EXTRACTED_FROM
3. **Test in Neo4j Browser** before updating Aura Agent
4. **Update Aura Agent tool** with working query
5. **Test agent** with sample questions

If issues persist, share the output from the diagnostic queries for further troubleshooting.

---

**Last Updated**: 2025-10-26  
**Version**: 2.0 (Fixed EXTRACTED_FROM interference)
