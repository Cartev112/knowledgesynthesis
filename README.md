Knowledge Synthesis - Unified Knowledge Graph Platform

A production-ready application for building unified knowledge graphs from multiple documents using AI extraction, expert review, and cross-document synthesis.

## ✨ Key Features

- **🧠 AI-Powered Extraction**: Automatic knowledge triplet extraction using OpenAI GPT
- **🔗 Unified Knowledge Graph**: Merges concepts across documents, preventing duplicates
- **✅ Expert Review Workflow**: Beautiful UI for domain experts to verify/flag extractions
- **🔍 Advanced Search**: Cross-document concept search with relationship visualization
- **📊 Interactive Visualization**: Cytoscape.js graph viewer with status indicators
- **🎯 Quality Control**: Status tracking (unverified/verified/incorrect) with timestamps
- **📚 Multi-Document Synthesis**: Automatically aggregates evidence from multiple sources

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+ 
- Neo4j Desktop installed (see `docs/neo4j-setup-windows.md`)
- OpenAI API key (or use dry-run mode for testing)

### 2. Installation

```bash
# Create virtual environment
py -m venv .venv

# Install dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configuration

Create `config/.env` from `config/example.env`:

```env
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your_password>
NEO4J_DATABASE=neo4j

# For testing without OpenAI
OPENAI_DRY_RUN=true

# For production
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### 4. Initialize Database Schema

```bash
python scripts/apply_neo4j_init.py
```

### 5. Start the Application

```bash
.\.venv\Scripts\python.exe -m uvicorn backend.python_worker.app.main:app --reload
```

### 6. Access the UIs

- **Graph Viewer**: http://localhost:8000/viewer
- **Review Queue**: http://localhost:8000/review-ui  
- **API Documentation**: http://localhost:8000/docs

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step usage guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical details & architecture
- **[docs/neo4j-setup-windows.md](docs/neo4j-setup-windows.md)** - Neo4j setup guide

## 🎯 Core Workflows

### 1️⃣ Ingest Documents
- Upload PDFs via the Graph Viewer
- Or use API: `POST /ingest/pdf` or `POST /ingest/text`
- AI automatically extracts knowledge triplets
- Unified graph prevents duplicate concepts

### 2️⃣ Review Extractions  
- Open the Review Queue at `/review-ui`
- See unverified relationships with original context
- Confirm correct extractions ✓
- Flag incorrect ones ⚠
- Edit metadata as needed ✎

### 3️⃣ Explore Knowledge
- Search for concepts across all documents
- Filter by verification status
- Visualize relationship networks
- Trace back to source documents

## 🔌 API Endpoints

### Ingestion
- `POST /ingest/pdf` - Upload PDF file
- `POST /ingest/text` - Ingest raw text
- `GET /ingest/run` - Ingest sample file

### Query & Search
- `GET /query/documents` - List all documents
- `GET /query/graph_by_docs` - Get graph for document(s)
- `GET /query/search/concept` - Cross-document concept search ✨
- `GET /query/all` - Get entire graph

### Review & Verification
- `GET /review/queue` - Get review queue ✨
- `POST /review/{id}/confirm` - Confirm relationship ✨
- `POST /review/{id}/edit` - Edit relationship ✨
- `POST /review/{id}/flag` - Flag as incorrect ✨
- `GET /review/stats` - Get statistics ✨

### UI
- `GET /viewer` - Interactive graph viewer
- `GET /review-ui` - Review queue interface ✨

✨ = New in latest version

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI (Python)
- **Database**: Neo4j (Graph Database)
- **AI**: OpenAI GPT-4 (Structured Outputs)
- **Frontend**: Vanilla JS with Cytoscape.js
- **Validation**: Custom triplet validator

### Data Flow
1. **Ingestion**: PDF/Text → OpenAI → Triplets → Validator → Neo4j
2. **Unification**: MERGE logic prevents duplicates, aggregates sources
3. **Review**: Expert confirms/flags → Status updated in Neo4j
4. **Query**: Cypher queries → JSON API → Interactive visualization

### Neo4j Schema
- **Nodes**: `Entity` (concepts), `Document` (sources)
- **Relationships**: Dynamic types based on predicates
  - Properties: `status`, `sources`, `confidence`, `original_text`, timestamps
- **Linking**: `EXTRACTED_FROM` connects entities to documents

## 🧪 Development Status

### ✅ Completed (Production-Ready)
- Phase 1: Unified graph with MERGE logic
- Phase 2: Document ingestion and visualization  
- Phase 3: Expert review workflow
- Phase 4: Advanced cross-document search

### 🚧 Pending Enhancements
- Phase 2.1: Configurable extraction parameters (max_concepts, etc.)
- Phase 4.2: Full user authentication integration

## 🤝 Contributing

This is a research/internal tool. For questions or issues, contact the development team.

## 📝 License

Internal use only. See your organization's policies.

---

**Built with ❤️ for knowledge synthesis and research acceleration**








