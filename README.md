# Knowledge Synthesis Platform

A research-grade application for constructing unified knowledge graphs from multiple documents through AI-powered extraction, expert validation, and cross-document synthesis.

## Overview

The Knowledge Synthesis Platform enables researchers to automatically extract, validate, and explore knowledge from scientific literature. The system combines large language models, graph databases, and interactive visualization to create a unified knowledge representation across multiple documents.

## Key Features

### Core Capabilities

- **AI-Powered Extraction**: Automatic knowledge triplet extraction using OpenAI GPT-4 with structured outputs
- **Unified Knowledge Graph**: Entity resolution and deduplication across documents using Neo4j MERGE operations
- **Expert Review Workflow**: Web-based interface for domain experts to verify, edit, or flag extracted relationships
- **Cross-Document Search**: Semantic search across entities and relationships with source attribution
- **Interactive Visualization**: Graph visualization with Cytoscape.js including status indicators and filtering
- **Quality Control**: Comprehensive status tracking (unverified/verified/incorrect) with timestamps and provenance
- **Multi-Document Synthesis**: Automatic aggregation of evidence from multiple sources with citation tracking

### Advanced Features

- **GraphRAG Agent**: Neo4j Aura-integrated AI agent for natural language querying with graph traversal and semantic search
- **Pathway Discovery**: Shortest path, all paths, and multi-hop exploration between concepts
- **Pattern Query Builder**: No-code interface for constructing complex graph patterns
- **Document Discovery**: Automated PubMed and ArXiv search with AI-powered relevance ranking
- **Conversation Management**: Persistent chat history for AI query sessions
- **Asynchronous Processing**: RabbitMQ-based task queue for scalable document ingestion

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Neo4j Desktop or Neo4j Aura instance (see `docs/neo4j-setup-windows.md`)
- OpenAI API key (or use dry-run mode for testing)
- Node.js 16+ (for optional authentication server)

### Installation

```bash
# Create virtual environment
py -m venv .venv

# Activate virtual environment (Windows)
.\.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Configuration

Create `config/.env` from `config/example.env`:

```env
# Neo4j Configuration
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your_password>
NEO4J_DATABASE=neo4j

# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Optional: Dry-run mode for testing without API calls
OPENAI_DRY_RUN=false

# Optional: Email notifications
SENDGRID_API_KEY=<your_key>
SENDGRID_FROM_EMAIL=<sender_email>

# Optional: Message queue
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
```

### Database Initialization

```bash
# Apply Neo4j schema and constraints
python scripts/apply_neo4j_init.py
```

### Starting the Application

```bash
# Start FastAPI backend
uvicorn backendAndUI.python_worker.app.main:app --reload --host 0.0.0.0 --port 8000

# Optional: Start Node.js authentication server
cd node-server
npm install
npm start
```

### Access Points

- **Graph Viewer**: http://localhost:8000/viewer
- **AI Query Interface**: http://localhost:8000/ai-query
- **Review Queue**: http://localhost:8000/review-ui
- **Document Discovery**: http://localhost:8000/discovery-ui
- **Query Builder**: http://localhost:8000/viewer (Query Builder tab)
- **API Documentation**: http://localhost:8000/docs

## Documentation

### Getting Started
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Step-by-step usage guide
- **[docs/neo4j-setup-windows.md](docs/neo4j-setup-windows.md)** - Neo4j installation and configuration
- **[docs/RESTART_INSTRUCTIONS.md](docs/RESTART_INSTRUCTIONS.md)** - Server restart procedures

### Architecture and Implementation
- **[docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)** - Technical architecture and design decisions
- **[docs/PHASE_6_COMPLETE_SUMMARY.md](docs/PHASE_6_COMPLETE_SUMMARY.md)** - Pathway discovery and query builder implementation
- **[docs/ASYNC_INGESTION_SETUP.md](docs/ASYNC_INGESTION_SETUP.md)** - RabbitMQ integration for asynchronous processing

### Feature Documentation
- **[docs/AURA_AGENT_CONFIGURATION.md](docs/AURA_AGENT_CONFIGURATION.md)** - GraphRAG agent setup and configuration
- **[docs/DOCUMENT_DISCOVERY_FEATURE.md](docs/DOCUMENT_DISCOVERY_FEATURE.md)** - Automated literature search
- **[docs/CONVERSATIONS_FEATURE.md](docs/CONVERSATIONS_FEATURE.md)** - Chat history persistence
- **[docs/AI_QUERY_IMPLEMENTATION.md](docs/AI_QUERY_IMPLEMENTATION.md)** - Natural language query interface

### Deployment
- **[docs/RAILWAY_DEPLOYMENT_GUIDE.md](docs/RAILWAY_DEPLOYMENT_GUIDE.md)** - Railway.app deployment
- **[docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md)** - Render.com deployment
- **[docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)** - Production deployment checklist

## Core Workflows

### Document Ingestion

1. **Upload Documents**: Use the Graph Viewer interface to upload PDF files or submit text via API
2. **AI Extraction**: OpenAI GPT-4 analyzes content and extracts knowledge triplets (subject-predicate-object)
3. **Entity Resolution**: System merges duplicate entities across documents using fuzzy matching
4. **Graph Construction**: Triplets are written to Neo4j with source attribution and metadata
5. **Status Assignment**: All extractions initially marked as "unverified" pending expert review

**API Endpoints**:
- `POST /ingest/pdf` - Upload PDF file with multipart/form-data
- `POST /ingest/text` - Submit raw text with document metadata
- `GET /ingest/run` - Process sample document for testing

### Expert Review

1. **Access Review Queue**: Navigate to `/review-ui` to see pending extractions
2. **Review Context**: Examine relationships with original text snippets and source citations
3. **Verify Accuracy**: Confirm correct extractions, flag errors, or edit metadata
4. **Track Progress**: Monitor statistics dashboard showing verification rates

**Review Actions**:
- **Confirm**: Mark relationship as verified (status: verified)
- **Flag**: Mark as incorrect with optional reason (status: incorrect)
- **Edit**: Modify confidence scores or metadata while verifying

### Knowledge Exploration

**Graph Viewer** (`/viewer`):
- Interactive visualization of knowledge graph using Cytoscape.js
- Multi-document selection and filtering
- Verification status indicators (green: verified, gray: unverified, red: incorrect)
- Node and edge detail panels with source attribution
- Concept search across entire graph

**Pathway Discovery**:
- Find shortest path between two concepts
- Discover all paths connecting entities
- Identify bridge concepts linking disparate areas
- Multi-hop neighborhood exploration

**Query Builder**:
- No-code interface for pattern-based queries
- Dynamic schema loading (entity types, relationship types)
- Quality filters (verified only, high confidence)
- Result visualization in graph viewer

### AI-Powered Querying

**GraphRAG Agent** (`/ai-query`):
- Natural language queries over knowledge graph
- Combines vector similarity search with graph traversal
- Multi-tool reasoning (entity search, relationship retrieval, neighborhood exploration)
- Source citation with document titles and page numbers
- Conversation history persistence

**Example Queries**:
- "What is endovascular BCI and how does it relate to neural recordings?"
- "Find all drugs that inhibit COX-2"
- "What connects BRAF mutations to drug resistance?"
- "Summarize findings about aspirin from all documents"

### Document Discovery

**Automated Literature Search** (`/discovery-ui`):
1. Enter research query or select graph nodes for context
2. System searches PubMed and ArXiv simultaneously
3. AI ranks results by semantic relevance using embeddings
4. Review paper metadata (title, authors, abstract, relevance score)
5. Select papers for ingestion into knowledge graph

**Features**:
- Multi-source search (PubMed, ArXiv)
- Semantic ranking with OpenAI embeddings
- Graph-context aware search
- Deduplication across sources

## API Reference

### Ingestion Endpoints

- `POST /ingest/pdf` - Upload and process PDF document
  - Request: multipart/form-data with file
  - Response: Document ID and extraction summary
  
- `POST /ingest/text` - Ingest raw text content
  - Request: JSON with text and document metadata
  - Response: Document ID and triplet count
  
- `GET /ingest/run` - Process sample document (testing)

### Query and Search Endpoints

- `GET /query/documents` - List all ingested documents
- `GET /query/graph_by_docs` - Retrieve graph for specific documents
  - Parameters: `doc_ids` (comma-separated), `verified_only` (boolean)
  
- `GET /query/search/concept` - Cross-document concept search
  - Parameters: `query` (string), `limit` (integer)
  
- `GET /query/all` - Retrieve entire knowledge graph
- `GET /query/entity/{name}` - Get specific entity with relationships

### Review and Verification Endpoints

- `GET /review/queue` - Retrieve review queue
  - Parameters: `limit` (integer), `status_filter` (string)
  
- `POST /review/{relationship_id}/confirm` - Mark relationship as verified
  - Request: Optional reviewer metadata
  
- `POST /review/{relationship_id}/edit` - Update relationship properties
  - Request: JSON with updated fields
  
- `POST /review/{relationship_id}/flag` - Flag relationship as incorrect
  - Request: Optional flag reason
  
- `GET /review/stats` - Get verification statistics

### Pathway Discovery Endpoints

- `GET /api/pathway/shortest-path` - Find shortest path between entities
  - Parameters: `source` (string), `target` (string)
  
- `GET /api/pathway/all-paths` - Find all paths between entities
  - Parameters: `source` (string), `target` (string), `max_length` (integer)
  
- `GET /api/pathway/connectors` - Find bridge concepts
  - Parameters: `source` (string), `target` (string)
  
- `GET /api/pathway/explore` - Multi-hop neighborhood exploration
  - Parameters: `entity` (string), `hops` (integer)
  
- `POST /api/pathway/pattern` - Pattern-based query
  - Request: JSON with pattern specification
  
- `GET /api/pathway/schema` - Get database schema (entity types, relationship types)
- `GET /api/pathway/stats` - Get graph statistics

### Document Discovery Endpoints

- `POST /api/discovery/search` - Search external databases
  - Request: JSON with query and parameters
  - Response: Ranked list of papers with metadata
  
- `POST /api/discovery/search-by-context` - Context-aware search
  - Request: JSON with selected graph nodes
  
- `GET /api/discovery/sources` - List available search sources

### Conversation Management Endpoints

- `GET /api/conversations` - List all conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/{id}` - Get conversation with messages
- `POST /api/conversations/{id}/messages` - Add message to conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `PUT /api/conversations/{id}/title` - Update conversation title

### User Interface Endpoints

- `GET /viewer` - Interactive graph viewer
- `GET /review-ui` - Expert review interface
- `GET /ai-query` - AI query interface with GraphRAG agent
- `GET /discovery-ui` - Document discovery interface
- `GET /docs` - OpenAPI documentation (Swagger UI)

## Architecture

### Technology Stack

**Backend**:
- FastAPI (Python 3.11+) - REST API and web server
- Neo4j 5.x - Graph database for knowledge storage
- OpenAI GPT-4 - Knowledge extraction and embeddings
- RabbitMQ - Asynchronous task queue (optional)
- Redis - Caching and session management (optional)

**Frontend**:
- Vanilla JavaScript - No framework dependencies
- Cytoscape.js - Graph visualization
- Modern CSS with responsive design

**AI Components**:
- OpenAI Structured Outputs - Reliable triplet extraction
- text-embedding-3-small - Semantic search and ranking
- Neo4j Aura Agent - GraphRAG with tool orchestration

**External Integrations**:
- NCBI E-utilities API - PubMed search
- ArXiv API - Preprint search
- SendGrid - Email notifications (optional)

### System Architecture

```
┌─────────────────┐
│   Web Browser   │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────────────────────────┐
│       FastAPI Application           │
│  ┌──────────┐  ┌────────────────┐  │
│  │   API    │  │  UI Endpoints  │  │
│  │ Endpoints│  │  (HTML/JS)     │  │
│  └──────────┘  └────────────────┘  │
└────────┬────────────────────────────┘
         │
    ┌────┴────┬────────────┬──────────┐
    ▼         ▼            ▼          ▼
┌────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐
│ Neo4j  │ │ OpenAI  │ │PubMed/ │ │ RabbitMQ │
│  DB    │ │   API   │ │ ArXiv  │ │  Queue   │
└────────┘ └─────────┘ └────────┘ └──────────┘
```

### Data Flow

**Ingestion Pipeline**:
1. Document Upload → PDF parsing (pypdf/pdfminer)
2. Text Chunking → Context-aware segmentation
3. OpenAI Extraction → Structured triplet generation
4. Validation → Triplet normalization and deduplication
5. Graph Writing → Neo4j MERGE operations with source tracking
6. Embedding Generation → Vector embeddings for entities and relationships

**Query Pipeline**:
1. User Query → Natural language or structured pattern
2. Query Processing → Intent classification and parameter extraction
3. Graph Traversal → Cypher query execution
4. Result Ranking → Semantic similarity scoring
5. Response Generation → Formatted results with citations

**GraphRAG Agent Flow**:
1. User Question → Embedding generation
2. Similarity Search → Find relevant entities/documents
3. Tool Selection → Agent chooses appropriate tools
4. Graph Traversal → Retrieve relationships and neighborhoods
5. Synthesis → Generate comprehensive answer with evidence
6. Citation → Link to source documents and page numbers

### Neo4j Schema

**Node Types**:
- `Entity` - Extracted concepts with properties:
  - `name` (string, unique) - Entity identifier
  - `type` (string) - Entity classification (Drug, Gene, Disease, etc.)
  - `embedding` (vector) - Semantic embedding for similarity search
  - `significance` (float) - Importance score
  - `created_at` (datetime)
  
- `Document` - Source documents with properties:
  - `document_id` (string, unique) - SHA-256 hash or custom ID
  - `title` (string) - Document title
  - `content` (string) - Full text content
  - `embedding` (vector) - Document-level embedding
  - `metadata` (map) - Authors, publication date, etc.
  - `ingested_at` (datetime)

**Relationship Types**:
- Dynamic types based on extracted predicates (e.g., `INHIBITS`, `TREATS`, `CAUSES`)
- All relationships include:
  - `status` (string) - "unverified", "verified", or "incorrect"
  - `sources` (list) - Array of document IDs
  - `confidence` (float) - Extraction confidence (0-1)
  - `original_text` (string) - Source text snippet
  - `page_number` (integer) - Page reference
  - `created_at` (datetime)
  - `updated_at` (datetime)
  - `reviewed_by` (string) - Reviewer identifier (optional)
  - `reviewed_at` (datetime) - Review timestamp (optional)
  - `flag_reason` (string) - Reason for flagging (optional)

**Special Relationships**:
- `EXTRACTED_FROM` - Links entities to source documents

**Indexes**:
- Vector index on `Entity.embedding` - Semantic entity search
- Vector index on `Document.embedding` - Document similarity search
- Unique constraint on `Entity.name`
- Unique constraint on `Document.document_id`

## GraphRAG Agent Configuration

The platform includes a Neo4j Aura-integrated AI agent that provides natural language querying capabilities with graph-aware reasoning.

### Agent Capabilities

**Core Functions**:
- Entity similarity search using vector embeddings
- Relationship retrieval with evidence and citations
- Multi-hop neighborhood exploration
- Document-level semantic search
- Aggregation queries and statistics

**Tool Orchestration**:
The agent uses multiple specialized tools:
1. `entity_similarity_search` - Find semantically similar entities
2. `get_entity_relationships` - Retrieve all relationships for an entity
3. `get_entity_neighborhood` - Explore 1-hop and 2-hop neighbors
4. `document_similarity_search` - Find relevant documents
5. `get_document_entities` - Extract entities from specific documents
6. `text2cypher_aggregation` - Execute complex Cypher queries

### Configuration

Detailed agent configuration is documented in `docs/AURA_AGENT_CONFIGURATION.md`, including:
- System prompt design for relational reasoning
- Tool definitions with Cypher templates
- Embedding strategy and vector indexes
- Example interactions and testing queries
- Troubleshooting common issues

### Usage Example

```python
# Query the agent via API
response = requests.post(
    "http://localhost:8000/ai-query",
    json={
        "query": "What is endovascular BCI and how does it relate to neural recordings?",
        "conversation_id": "optional-conversation-id"
    }
)

# Agent response includes:
# - Comprehensive answer with relational context
# - Evidence snippets from source documents
# - Citations with document titles and page numbers
# - Connected concepts and their significance
```

## Development Status

### Completed Features

**Phase 1: Foundation**
- Unified graph construction with entity resolution
- MERGE logic for cross-document deduplication
- Status tracking and provenance
- Robust triplet validation and normalization

**Phase 2: Core Experience**
- PDF and text ingestion with OpenAI extraction
- Document-specific graph visualization
- Multi-document selection and filtering
- Interactive Cytoscape.js viewer

**Phase 3: Expert Review**
- Review queue with filtering and pagination
- Confirm/flag/edit workflow
- Statistics dashboard
- Original text context display

**Phase 4: Advanced Search**
- Cross-document concept search
- Verification status filtering
- Relationship visualization
- Source attribution

**Phase 5: AI Integration**
- GraphRAG agent with Neo4j Aura
- Natural language query interface
- Conversation history persistence
- Multi-tool reasoning with citations

**Phase 6: Discovery and Exploration**
- Pathway discovery (shortest path, all paths, connectors)
- Pattern query builder with dynamic schema
- Document discovery (PubMed, ArXiv)
- Semantic ranking with AI embeddings

### Planned Enhancements

- User authentication and authorization
- Workspace isolation for multi-tenant deployments
- Batch document processing with progress tracking
- Advanced entity type ontologies
- Contradiction detection across sources
- Temporal reasoning for time-series data
- Export capabilities (GraphML, JSON, CSV)
- Collaborative review with user roles

## Deployment

The platform supports multiple deployment options:

**Local Development**:
- Neo4j Desktop for database
- Python virtual environment for backend
- Direct file serving for frontend

**Cloud Deployment**:
- Railway.app (documented in `docs/RAILWAY_DEPLOYMENT_GUIDE.md`)
- Render.com (documented in `docs/RENDER_DEPLOYMENT.md`)
- Neo4j Aura for managed database
- Docker containerization (coming soon)

**Production Considerations**:
- Enable RabbitMQ for asynchronous processing
- Configure Redis for session management
- Set up SendGrid for email notifications
- Implement proper authentication
- Configure CORS and security headers
- Set up monitoring and logging

## Contributing

This is a research tool developed for academic and scientific use. For questions, issues, or collaboration inquiries, please contact the development team.

## License

Internal research use. Please consult your organization's policies regarding usage and distribution.

## Citation

If you use this platform in your research, please cite:

```
Knowledge Synthesis Platform
Version 1.0
https://github.com/[repository]
```

## Acknowledgments

Built with modern AI and graph database technologies to accelerate scientific knowledge synthesis and research discovery.








