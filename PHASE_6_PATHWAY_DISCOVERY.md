# Phase 6: Advanced Discovery - Pathway & Complex Queries

## Overview

Phase 6 introduces advanced graph exploration capabilities that allow users to discover hidden connections, find paths between concepts, and execute complex pattern-based queries. This transforms the knowledge graph from a simple storage system into an intelligent discovery engine.

## Features Implemented

### 1. **Shortest Path Finding** 🔍

Find the most direct connection between any two concepts in your knowledge graph.

**Use Cases:**
- Discover how a drug connects to a disease through molecular pathways
- Find the relationship between two seemingly unrelated research findings
- Identify knowledge gaps by finding where paths don't exist

**API Endpoint:** `GET /api/pathway/shortest-path`

**Parameters:**
- `source`: Source concept name (partial match supported)
- `target`: Target concept name (partial match supported)
- `max_hops`: Maximum relationship hops to explore (1-10, default: 5)
- `verified_only`: Only consider verified relationships (boolean)

**Example:**
```bash
curl "http://localhost:8000/api/pathway/shortest-path?source=vemurafenib&target=melanoma&max_hops=5"
```

**Response:**
```json
{
  "success": true,
  "path_found": true,
  "source": "Vemurafenib",
  "target": "Melanoma",
  "path_length": 2,
  "nodes": [
    {"id": "...", "name": "Vemurafenib", "type": "Drug"},
    {"id": "...", "name": "BRAF", "type": "Gene"},
    {"id": "...", "name": "Melanoma", "type": "Disease"}
  ],
  "relationships": [
    {"relation": "TARGETS", "confidence": 0.95, "status": "verified"},
    {"relation": "IMPLICATED_IN", "confidence": 0.92, "status": "verified"}
  ],
  "message": "Found path of length 2"
}
```

---

### 2. **All Paths Discovery** 📊

Find all possible paths between two concepts to discover alternative relationship routes.

**Use Cases:**
- Identify multiple mechanisms by which a drug affects a disease
- Discover redundant pathways that provide robustness
- Compare different knowledge pathways from various sources

**API Endpoint:** `GET /api/pathway/all-paths`

**Parameters:**
- `source`: Source concept name
- `target`: Target concept name
- `max_hops`: Maximum hops to explore (1-10, default: 5)
- `max_paths`: Maximum paths to return (1-50, default: 10)
- `verified_only`: Only verified relationships (boolean)

**Example:**
```bash
curl "http://localhost:8000/api/pathway/all-paths?source=aspirin&target=inflammation&max_paths=5"
```

---

### 3. **Connecting Concepts Discovery** 🌉

Find intermediate "bridge" concepts that connect two entities.

**Use Cases:**
- Discover what proteins link a drug to its therapeutic effect
- Find common genes between two diseases
- Identify key concepts that bridge different knowledge domains

**API Endpoint:** `GET /api/pathway/connectors`

**Parameters:**
- `source`: Source concept name
- `target`: Target concept name
- `max_hops`: Maximum hops from source to connector (1-5, default: 3)

**Example:**
```bash
curl "http://localhost:8000/api/pathway/connectors?source=metformin&target=aging&max_hops=3"
```

**Response:**
```json
{
  "success": true,
  "connectors_found": 5,
  "connectors": [
    {
      "id": "AMPK",
      "name": "AMPK",
      "type": "Protein",
      "significance": 0.89,
      "sources": [{"id": "doc1", "title": "AMPK and longevity"}],
      "hops": 2
    }
  ],
  "message": "Found 5 connecting concept(s)"
}
```

---

### 4. **Multi-Hop Exploration** 🕸️

Explore the neighborhood around a concept, discovering entities at different distances (hops).

**Use Cases:**
- Understand the complete context around a key concept
- Discover related concepts you didn't know existed
- Explore the "ripple effect" of knowledge from a starting point

**API Endpoint:** `GET /api/pathway/explore`

**Parameters:**
- `concept`: Starting concept name
- `hops`: Number of hops to explore (1-3, default: 2)
- `limit_per_hop`: Limit results per hop level (1-50, default: 10)
- `verified_only`: Only verified relationships (boolean)

**Example:**
```bash
curl "http://localhost:8000/api/pathway/explore?concept=p53&hops=2&limit_per_hop=15"
```

**Response:**
```json
{
  "success": true,
  "center_concept": "p53",
  "exploration_data": [
    {
      "hop_distance": 1,
      "entity_count": 15,
      "entities": [
        {"id": "...", "name": "MDM2", "type": "Protein", "significance": 0.92}
      ]
    },
    {
      "hop_distance": 2,
      "entity_count": 15,
      "entities": [...]
    }
  ],
  "total_hops": 2,
  "message": "Explored 2 hop level(s)"
}
```

---

### 5. **Pattern-Based Queries** 🔎

Execute complex graph patterns to find specific relationship structures.

**Use Cases:**
- Find all "Drug → Gene → Disease" patterns
- Discover "Protein → Protein → Pathway" interactions
- Query custom relationship chains

**API Endpoint:** `POST /api/pathway/pattern`

**Request Body:**
```json
{
  "node1_type": "Drug",
  "relationship": "TARGETS",
  "node2_type": "Gene",
  "limit": 50
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/pathway/pattern" \
  -H "Content-Type: application/json" \
  -d '{
    "node1_type": "Drug",
    "relationship": "TARGETS", 
    "node2_type": "Gene",
    "limit": 30
  }'
```

---

### 6. **Graph Statistics** 📈

Get structural statistics about your knowledge graph.

**API Endpoint:** `GET /api/pathway/stats`

**Response:**
```json
{
  "node_count": 1547,
  "relationship_count": 3891,
  "density": 0.0032,
  "message": "Graph statistics retrieved successfully"
}
```

---

## User Interface Integration

### Pathway Discovery Panel

A new **Pathway Discovery** section has been added to the main viewing interface:

**Location:** Main UI → Viewing Tab → Right Sidebar

**Features:**
1. **Source & Target Input Fields**: Enter concept names for pathway finding
2. **Find Shortest Path Button**: Discovers the most direct connection
3. **Find All Paths Button**: Discovers multiple connection routes

**Usage:**
1. Switch to the **Viewing** tab
2. Scroll to the **🔗 Pathway Discovery** section
3. Enter a source concept (e.g., "aspirin")
4. Enter a target concept (e.g., "pain")
5. Click **🔍 Find Shortest Path** or **📊 Find All Paths**
6. The graph will automatically display and highlight the discovered path(s)

**Visual Feedback:**
- Shortest paths are highlighted in purple (`#8b5cf6`)
- All paths are highlighted in indigo (`#6366f1`)
- Path nodes are emphasized with special styling
- Relationship strength is shown via edge thickness

---

## Technical Implementation

### Backend Services

**File:** `backendAndUI/python_worker/app/services/pathway_discovery.py`

Contains all pathway discovery logic:
- `find_shortest_path()`: Uses Neo4j's `shortestPath()` algorithm
- `find_all_paths()`: Uses `allShortestPaths()` for multiple routes
- `find_connecting_concepts()`: Finds intermediate bridge nodes
- `explore_multi_hop()`: Variable-length path exploration
- `pattern_query()`: Dynamic Cypher query construction

**Key Technologies:**
- Neo4j Cypher path algorithms
- Variable-length relationship patterns
- Dynamic query building
- Graph Data Science library support (ready for future enhancements)

### API Routes

**File:** `backendAndUI/python_worker/app/routes/pathway.py`

FastAPI endpoints with:
- Input validation using Pydantic
- Query parameter constraints
- Comprehensive error handling
- Helpful API documentation

### Frontend Integration

**File:** `backendAndUI/python_worker/app/routes/main_ui.py`

JavaScript functions:
- `findShortestPath()`: Client-side pathway search trigger
- `findAllPaths()`: Multiple path discovery
- Path visualization using Cytoscape.js
- Dynamic graph highlighting and styling

---

## Advanced Use Cases

### 1. **Drug Repurposing Discovery**

Find if an existing drug could treat a new disease:

```bash
# Find path from drug to disease
curl "http://localhost:8000/api/pathway/shortest-path?source=metformin&target=alzheimers"

# Find connecting proteins/pathways
curl "http://localhost:8000/api/pathway/connectors?source=metformin&target=alzheimers"
```

### 2. **Knowledge Gap Identification**

Discover where knowledge is missing:

```bash
# If no path exists between two concepts, it indicates a knowledge gap
curl "http://localhost:8000/api/pathway/shortest-path?source=NewDrug&target=RareDisease"
# Returns: path_found: false
```

### 3. **Literature Review Assistance**

Explore all concepts within N hops of your research topic:

```bash
# Discover all related concepts within 2 hops
curl "http://localhost:8000/api/pathway/explore?concept=CRISPR&hops=2&limit_per_hop=20"
```

### 4. **Cross-Domain Discovery**

Find unexpected connections across different knowledge domains:

```bash
# Find how a biological concept connects to a clinical outcome
curl "http://localhost:8000/api/pathway/all-paths?source=mitochondria&target=fatigue&max_paths=10"
```

---

## Performance Considerations

### Optimizations
- **Max hops limited to 10**: Prevents expensive queries on large graphs
- **Path result limits**: Default 10 paths max, configurable up to 50
- **Verified-only mode**: Faster queries when focusing on curated data
- **Indexed node names**: Fast concept lookup with `toLower()` matching

### Best Practices
1. **Start with shortest path** before exploring all paths
2. **Use verified_only=true** for production analysis
3. **Limit hops to 3-5** for most practical use cases
4. **Use connectors endpoint** for focused bridge discovery

---

## Future Enhancements (Ready for Implementation)

Since you have **Neo4j Graph Data Science** library installed, these are ready to implement:

### 1. **PageRank for Concept Importance**
Identify the most "central" or important concepts in your knowledge graph.

### 2. **Community Detection**
Automatically group related concepts into knowledge clusters.

### 3. **Node Similarity**
Find concepts that are structurally similar based on their relationship patterns.

### 4. **Weighted Shortest Path**
Use confidence scores to find the "most reliable" path, not just the shortest.

### 5. **Link Prediction**
Suggest missing relationships that should probably exist based on graph structure.

---

## API Documentation

All pathway endpoints are documented in the interactive API docs:

**Visit:** `http://localhost:8000/docs#/pathway`

Features:
- Interactive endpoint testing
- Parameter descriptions
- Example responses
- Schema definitions

---

## Testing the Implementation

### Quick Test Sequence

1. **Start the server:**
   ```bash
   cd backendAndUI/python_worker
   uvicorn app.main:app --reload --port 8000
   ```

2. **Test shortest path:**
   ```bash
   curl "http://localhost:8000/api/pathway/shortest-path?source=test&target=concept"
   ```

3. **Test UI integration:**
   - Open `http://localhost:8000/app`
   - Go to **Viewing** tab
   - Use the **🔗 Pathway Discovery** panel

### Example Test Data

If you have biomedical data:
```bash
# Drug to disease pathway
curl "http://localhost:8000/api/pathway/shortest-path?source=aspirin&target=inflammation"

# Multi-hop exploration
curl "http://localhost:8000/api/pathway/explore?concept=insulin&hops=2"
```

---

## Summary

✅ **Implemented:**
- Shortest path finding
- All paths discovery  
- Connecting concepts identification
- Multi-hop exploration
- Pattern-based queries
- Graph statistics
- UI integration with visual feedback

✅ **Benefits:**
- Discover hidden knowledge connections
- Identify knowledge gaps
- Support literature review and research
- Enable drug repurposing discovery
- Cross-domain knowledge synthesis

✅ **Next Steps:**
- Test pathway discovery with your data
- Explore multi-hop neighborhoods  
- Use pattern queries for specific research questions
- Consider implementing GDS algorithms for advanced analytics

**Phase 6 Complete!** 🎉 Your knowledge synthesis platform now has advanced discovery capabilities that transform it into an intelligent research assistant.





