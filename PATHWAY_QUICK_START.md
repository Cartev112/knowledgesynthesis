# Pathway Discovery - Quick Start Guide

## 🚀 Getting Started in 2 Minutes

### Via User Interface

1. **Open the app**: Navigate to `http://localhost:8000/app`
2. **Go to Viewing tab**: Click the **🔍 Viewing** tab
3. **Find the Pathway Discovery panel**: Scroll down on the right sidebar to **🔗 Pathway Discovery**
4. **Enter concepts**:
   - Source: `aspirin`
   - Target: `pain`
5. **Click**: **🔍 Find Shortest Path**
6. **View**: The graph automatically displays the connection path!

### Via API

```bash
# Find shortest path
curl "http://localhost:8000/api/pathway/shortest-path?source=aspirin&target=pain"

# Find all paths (up to 5)
curl "http://localhost:8000/api/pathway/all-paths?source=aspirin&target=pain&max_paths=5"

# Find connecting concepts
curl "http://localhost:8000/api/pathway/connectors?source=aspirin&target=pain"

# Explore neighborhood
curl "http://localhost:8000/api/pathway/explore?concept=aspirin&hops=2"
```

---

## 📚 Common Use Cases

### 1. Drug-Disease Connection Discovery
**Goal:** Find how a drug affects a disease

```bash
curl "http://localhost:8000/api/pathway/shortest-path?source=metformin&target=diabetes"
```

**What you'll discover:** Drug → Protein/Gene → Pathway → Disease

---

### 2. Literature Gap Identification
**Goal:** Check if two concepts are connected in your knowledge base

```bash
curl "http://localhost:8000/api/pathway/shortest-path?source=concept1&target=concept2"
```

**If `path_found: false`:** You've found a knowledge gap to explore!

---

### 3. Concept Neighborhood Exploration
**Goal:** See everything related to a concept within N hops

```bash
curl "http://localhost:8000/api/pathway/explore?concept=CRISPR&hops=2&limit_per_hop=15"
```

**What you'll get:** All entities 1-hop and 2-hops away from CRISPR

---

### 4. Bridge Concept Discovery
**Goal:** Find what connects two distant concepts

```bash
curl "http://localhost:8000/api/pathway/connectors?source=exercise&target=longevity"
```

**What you'll discover:** Intermediate proteins, pathways, or processes that bridge them

---

### 5. Pattern Matching
**Goal:** Find all instances of a specific relationship pattern

```bash
curl -X POST "http://localhost:8000/api/pathway/pattern" \
  -H "Content-Type: application/json" \
  -d '{
    "node1_type": "Drug",
    "relationship": "TARGETS",
    "node2_type": "Gene"
  }'
```

**What you'll get:** All Drug→Gene targeting relationships

---

## 🎨 UI Features

### Visual Feedback

**Shortest Path:**
- Path highlighted in **purple** (#8b5cf6)
- Thick edges (width: 4)
- All path nodes emphasized

**All Paths:**
- Paths highlighted in **indigo** (#6366f1)
- Medium edges (width: 3)
- Shows alternative routes

### Interactive Controls

**Filters that affect pathway search:**
- ✅ **Show verified only**: Only uses verified relationships in paths
- ℹ️ This checkbox affects both shortest and all-paths searches

---

## 🔧 API Parameters Reference

### `/api/pathway/shortest-path`
- `source` *(required)*: Source concept name (partial match OK)
- `target` *(required)*: Target concept name (partial match OK)
- `max_hops` *(optional)*: Max hops (1-10, default: 5)
- `verified_only` *(optional)*: Boolean (default: false)

### `/api/pathway/all-paths`
- Same as above, plus:
- `max_paths` *(optional)*: Max paths to return (1-50, default: 10)

### `/api/pathway/connectors`
- `source` *(required)*: Source concept
- `target` *(required)*: Target concept
- `max_hops` *(optional)*: Max hops to connector (1-5, default: 3)

### `/api/pathway/explore`
- `concept` *(required)*: Starting concept
- `hops` *(optional)*: Number of hops (1-3, default: 2)
- `limit_per_hop` *(optional)*: Results per hop (1-50, default: 10)
- `verified_only` *(optional)*: Boolean (default: false)

### `/api/pathway/stats`
- No parameters
- Returns: node count, relationship count, graph density

---

## 💡 Pro Tips

### 1. Start Small
Begin with **2-3 hops** for exploration, then increase if needed.

### 2. Use Verified Mode
For production analysis, add `verified_only=true` to focus on curated data.

### 3. Check Stats First
Run `/api/pathway/stats` to understand your graph size before complex queries.

### 4. Partial Matching Works
You don't need exact concept names - `"insul"` will match `"insulin"`.

### 5. Combine with Search
Use the autocomplete search first to find exact concept names, then use in pathways.

### 6. Export Paths
After finding a path in the UI, use the **Export** feature to save it!

---

## 🐛 Troubleshooting

### "No path found"
✅ **Normal!** This means concepts aren't connected in your data.
- Try increasing `max_hops`
- Check if both concepts exist (use search)
- Consider if connection is expected

### "Pathway search failed"
- Check that server is running
- Verify Neo4j connection
- Check API endpoint URL

### Empty results
- Try broader concept names
- Reduce hop count
- Check if `verified_only` is too restrictive

### Slow queries
- Reduce `max_hops` (use 3-5 max)
- Limit `max_paths` to 5-10
- Use `verified_only=true` for faster results

---

## 🎯 Examples by Domain

### Biomedical Research
```bash
# Find drug mechanism
curl "http://localhost:8000/api/pathway/shortest-path?source=imatinib&target=leukemia"

# Explore gene context
curl "http://localhost:8000/api/pathway/explore?concept=BRCA1&hops=2"
```

### General Knowledge
```bash
# Find concept connections
curl "http://localhost:8000/api/pathway/shortest-path?source=climate&target=migration"

# Explore topic
curl "http://localhost:8000/api/pathway/explore?concept=artificial_intelligence&hops=2"
```

### Literature Review
```bash
# Find connecting research
curl "http://localhost:8000/api/pathway/connectors?source=microbiome&target=depression"

# Explore all paths
curl "http://localhost:8000/api/pathway/all-paths?source=stress&target=immunity"
```

---

## 📖 Next Steps

1. ✅ Try the examples above with your data
2. ✅ Explore the interactive API docs: `http://localhost:8000/docs`
3. ✅ Read the full documentation: `PHASE_6_PATHWAY_DISCOVERY.md`
4. ✅ Consider implementing Graph Data Science algorithms (see Phase 6 docs)

---

## 🎉 You're Ready!

Start discovering hidden connections in your knowledge graph! 🔍





