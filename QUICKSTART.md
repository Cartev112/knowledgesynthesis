# Knowledge Synthesis - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Neo4j database running (see `docs/neo4j-setup-windows.md`)
- Python 3.8+ with dependencies installed
- OpenAI API key configured in `config/.env`

### Step 1: Start the Backend

```bash
cd backend/python_worker
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Open the Application

Open your browser to:
- **Graph Viewer**: http://localhost:8000/viewer
- **Review Queue**: http://localhost:8000/review-ui
- **API Documentation**: http://localhost:8000/docs

## 📚 Basic Workflows

### Workflow 1: Ingest Your First Document

1. Navigate to http://localhost:8000/viewer
2. Click **"Choose File"** and select a PDF document
3. Click **"Ingest PDF"**
4. Wait for processing (typically 10-30 seconds depending on document length)
5. The knowledge graph will automatically appear!

**What just happened?**
- PDF text extracted
- OpenAI GPT analyzed the text
- Triplets (subject-predicate-object) extracted
- Unified graph created in Neo4j
- All extractions marked as 'unverified'

### Workflow 2: Review and Verify Extractions

1. Navigate to http://localhost:8000/review-ui
2. See the dashboard with statistics:
   - **Red**: Unverified relationships needing review
   - **Green**: Verified relationships
   - **Orange**: Flagged incorrect relationships

3. For each relationship:
   - Read the **original text** context
   - See the **triplet** (subject → predicate → object)
   - Choose an action:
     - ✓ **Confirm**: This is correct
     - ✎ **Edit**: Adjust confidence or metadata
     - ⚠ **Flag as Incorrect**: This is wrong

4. Watch the statistics update in real-time!

### Workflow 3: Explore the Knowledge Graph

#### View Specific Documents
1. In the Graph Viewer, select one or more documents from the dropdown
2. Click **"Apply Selection"**
3. Explore the combined graph

#### Search for Concepts
1. Type a concept name in the **search box** (e.g., "cancer", "BRAF", "treatment")
2. Press **Enter**
3. See all relationships for that concept across ALL documents

#### Filter by Verification Status
1. Check the **"Verified only"** checkbox
2. Only see relationships confirmed by experts
3. Higher quality, trusted knowledge

### Workflow 4: Multi-Document Synthesis

1. Ingest multiple related documents (e.g., multiple research papers on the same topic)
2. The system automatically:
   - **Merges identical concepts** into single nodes
   - **Aggregates evidence** from multiple sources
   - **Tracks which documents** mention each relationship

3. In the graph viewer:
   - Click on any **relationship** (edge)
   - See the **Sources** count in the details panel
   - Multiple sources = stronger evidence!

## 🎯 Common Use Cases

### Use Case 1: Literature Review
**Goal**: Synthesize knowledge from multiple research papers

1. Upload 5-10 papers on your research topic
2. Search for key concepts relevant to your research question
3. Filter to "verified only" to see high-confidence knowledge
4. Identify:
   - Consensus findings (mentioned in multiple papers)
   - Novel claims (mentioned in only one paper)
   - Contradictions (different relationship statuses)

### Use Case 2: Domain Expert Curation
**Goal**: Build a trusted knowledge base

1. Research team uploads domain literature
2. Domain expert reviews extractions in Review Queue
3. Confirm correct extractions
4. Flag incorrect or ambiguous extractions
5. Over time, build a highly accurate knowledge graph
6. Export verified knowledge for downstream applications

### Use Case 3: Concept Exploration
**Goal**: Understand a specific concept deeply

1. Search for your concept of interest
2. See all relationships in a visual graph
3. Click on connected nodes to explore further
4. Discover unexpected connections across documents
5. Trace back to original text for context

## 🔧 Advanced Features

### API Usage

All functionality is available via REST API:

#### Ingest Text Programmatically
```bash
curl -X POST "http://localhost:8000/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document text here...",
    "document_id": "my-doc-1",
    "document_title": "My Document"
  }'
```

#### Search Concepts
```bash
curl "http://localhost:8000/query/search/concept?name=cancer&verified_only=true"
```

#### Get Review Queue
```bash
curl "http://localhost:8000/review/queue?status_filter=unverified&limit=20"
```

#### Confirm a Relationship
```bash
curl -X POST "http://localhost:8000/review/{relationship_id}/confirm" \
  -H "Content-Type: application/json" \
  -d '{"reviewer_id": "expert-001"}'
```

### Cytoscape Graph Viewer Controls

- **Mouse wheel**: Zoom in/out
- **Click + drag**: Pan around
- **Click node**: Highlight neighborhood
- **Click edge**: Show relationship details
- **Click background**: Clear selection

### Status Color Coding

- **Gray edges**: Unverified (needs review)
- **Green edges** (thick): Verified (confirmed by expert)
- **Red edges** (dashed): Incorrect (flagged as wrong)

## 🐛 Troubleshooting

### "Failed to fetch graph"
- Check that Neo4j is running
- Verify connection settings in `backend/python_worker/app/core/settings.py`

### "OpenAI extraction failed"
- Verify your OpenAI API key is set in `config/.env`
- Check your OpenAI account has credits
- For testing without OpenAI, set `OPENAI_DRY_RUN=true` in `.env`

### "No items in queue"
- Great! This means all relationships have been reviewed
- Change filter to "Verified Only" or "Flagged Only" to see reviewed items
- Ingest more documents to populate the queue

### Graph looks cluttered
- Use the search feature to focus on specific concepts
- Select fewer documents to visualize
- Use the "verified only" filter to reduce noise

## 📊 Understanding the Data

### What is a Triplet?
A triplet is a factual statement with three parts:
- **Subject**: The entity performing the action (e.g., "Aspirin")
- **Predicate**: The relationship type (e.g., "inhibits")
- **Object**: The entity being acted upon (e.g., "COX-2")

Example: `Aspirin → inhibits → COX-2`

### How Does Merging Work?
When the same entity appears in multiple documents:
1. Neo4j finds or creates the entity node
2. New relationships are added
3. Source document added to `sources` array
4. Evidence accumulates over time

### Why "Unverified" by Default?
AI extraction is powerful but imperfect. By marking everything as unverified:
- Experts can review critical extractions
- Quality improves over time
- Users can choose their confidence threshold
- Flagged errors help improve the system

## 🎓 Best Practices

### For Uploaders
1. Use descriptive filenames (they become document titles)
2. Upload related documents in batches
3. Include metadata when using the text API

### For Reviewers
1. Start with high-confidence items (confidence > 0.8)
2. Use the original text context to verify
3. When in doubt, flag for further investigation
4. Add detailed reasons when flagging as incorrect

### For Researchers
1. Always filter to "verified only" for critical decisions
2. Check the source count for evidence strength
3. Click through to original text when needed
4. Export findings for external analysis

## 🔗 Additional Resources

- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **API Documentation**: http://localhost:8000/docs (when server running)
- **Neo4j Browser**: http://localhost:7474
- **Project README**: See main `README.md`

## 💡 Tips & Tricks

1. **Batch Processing**: Upload multiple PDFs, then review them all at once
2. **Keyboard Shortcuts**: Press Enter in the search box to search
3. **Multi-Select**: Hold Ctrl/Cmd to select multiple documents
4. **Export Graph**: Use Neo4j Browser to export data in various formats
5. **Custom Queries**: Write Cypher queries in Neo4j Browser for advanced analysis

---

**Happy Knowledge Synthesizing! 🧠✨**

