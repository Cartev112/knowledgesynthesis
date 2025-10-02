# Unified UI with Authentication - User Guide

## 🎉 New Features

The Knowledge Synthesis platform now has a **unified, tab-based interface** with:

1. ✅ **User Authentication** - Signup/Login pages integrated with Node.js server
2. ✅ **Ingestion Tab** - Configure extraction parameters and upload documents
3. ✅ **Viewing Tab** - Visualize and explore the knowledge graph
4. ✅ **User Tracking** - All documents and reviews associated with user IDs
5. ✅ **Configurable Parameters** - Control max_concepts and max_relationships

## 🚀 Quick Start

### 1. Start Both Servers

**Terminal 1 - Python Backend:**
```bash
cd backend/python_worker
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Node.js Auth Server:**
```bash
cd node-server
npm install
node server.js
```

### 2. Access the Application

Open your browser to: **http://localhost:8000**

- You'll be redirected to the login page
- Click "Sign up" if you're a new user

## 📋 Complete Workflow

### Step 1: Create Account

1. Navigate to http://localhost:8000 (redirects to login)
2. Click **"Sign up"** link
3. Enter:
   - **Username**: At least 3 characters
   - **Password**: At least 6 characters
   - **Confirm Password**: Must match
4. Click **"Create Account"**
5. You'll be redirected to login

### Step 2: Login

1. Enter your username and password
2. Click **"Sign In"**
3. You'll be redirected to the main application

### Step 3: Ingest Documents (Ingestion Tab)

The **Ingestion Tab** is the first tab you'll see. It has two sections:

#### Section A: Upload Document

**Option 1: Upload PDF File**
1. Click **"Choose File"**
2. Select a PDF document
3. Optionally, provide a custom **Document Title**

**Option 2: Paste Text**
1. Paste your document text into the **text area**
2. Provide a **Document Title** (recommended)

#### Section B: Extraction Parameters

Configure how the AI extracts knowledge:

1. **Max Concepts** (default: 100)
   - Maximum number of entities/concepts to extract
   - Range: 10-500
   - Higher = more comprehensive, but slower

2. **Max Relationships** (default: 50)
   - Maximum number of triplets to extract
   - Range: 10-200
   - This controls the detail level

3. **Extraction Model**
   - **GPT-4o Mini**: Fast and cost-effective (recommended)
   - **GPT-4o**: Higher quality
   - **GPT-4 Turbo**: Maximum capabilities

#### Submit

1. Click **"🚀 Extract Knowledge"**
2. Wait 30-60 seconds (status will update)
3. Success message shows:
   - Number of triplets extracted
   - Document ID for reference
4. Document automatically added to Viewing tab

### Step 4: View Knowledge Graph (Viewing Tab)

Click the **"🔍 Viewing"** tab to explore your knowledge graph.

#### View Options Panel (Top Left)

**Select Documents:**
1. Multi-select documents from dropdown (Ctrl+Click)
2. Click **"Load Graph"**
3. Graph displays combined knowledge

**Search Concepts:**
1. Type a concept name (e.g., "BRAF", "cancer", "inhibitor")
2. Click **"Search"** or press Enter
3. See all relationships for that concept across ALL documents

**Filters:**
- ☑ **Show verified only**: Only display expert-reviewed relationships
- ☑ **Show negative relationships**: Include negative/inhibitory relationships

#### Interacting with the Graph

**Node (Concept):**
- Click to see details in right panel
- Shows: Name, Type, ID

**Edge (Relationship):**
- Click to see details in right panel
- Shows:
  - Relationship type (predicate)
  - Source → Target
  - **Status badge**: Unverified (yellow), Verified (green), Incorrect (red)
  - Confidence score
  - Number of source documents

**Visual Indicators:**
- **Green thick edges**: Verified by expert
- **Gray normal edges**: Unverified (needs review)
- **Red dashed edges**: Flagged as incorrect

### Step 5: Review Extractions (Review Queue Tab)

Click **"✅ Review Queue"** tab (opens in new window):

1. See dashboard with statistics
2. Browse unverified relationships
3. For each relationship:
   - **✓ Confirm**: Marks as verified (turns edge green)
   - **✎ Edit**: Update confidence or metadata
   - **⚠ Flag as Incorrect**: Marks as incorrect (turns edge red)

## 🎯 Advanced Features

### User Association

Every document you upload is associated with your user ID:
- **Documents** have `created_by` field
- **Relationships** have `created_by` field
- Future: View "My Documents" vs "All Documents"

### Extraction Parameter Tuning

**For Detailed Extraction:**
- Max Concepts: 200-500
- Max Relationships: 100-200
- Best for: Comprehensive literature reviews

**For Quick Overview:**
- Max Concepts: 50-100
- Max Relationships: 20-50
- Best for: Fast document screening

**For High-Quality Subset:**
- Max Concepts: 100
- Max Relationships: 30
- Model: GPT-4o
- Best for: Critical documents requiring accuracy

### Multi-Document Synthesis

1. Upload 3-5 related papers (same topic)
2. In Viewing tab, select all documents
3. Click "Load Graph"
4. Observe:
   - Identical concepts merged into single nodes
   - Relationships show multiple sources
   - Stronger evidence for multi-source claims

### Concept Discovery

1. Search for a broad term (e.g., "cancer therapy")
2. See all related concepts and relationships
3. Click nodes to explore connections
4. Discover unexpected links between documents

## 🔧 API Usage for Developers

All features are accessible via REST API:

### Authentication

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_pass"}'
```

**Signup:**
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "new_user", "password": "secure_pass"}'
```

### Ingestion with Parameters

**Text Ingestion:**
```bash
curl -X POST http://localhost:8000/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document text...",
    "document_title": "My Paper",
    "user_id": "your_username",
    "max_concepts": 150,
    "max_relationships": 75
  }'
```

**PDF Ingestion:**
```bash
curl -X POST http://localhost:8000/ingest/pdf \
  -F "file=@/path/to/paper.pdf" \
  -F "user_id=your_username" \
  -F "max_concepts=100" \
  -F "max_relationships=50" \
  -F "title=Research Paper Title"
```

## 🗄️ Data Model Updates

### Document Node
```cypher
(:Document {
  document_id: "sha256_hash",
  title: "Paper Title",
  created_by: "username",
  created_at: datetime(),
  updated_at: datetime()
})
```

### Relationship Properties
```cypher
()-[r:RELATIONSHIP_TYPE {
  sources: ["doc1", "doc2"],
  status: "unverified|verified|incorrect",
  confidence: 0.95,
  created_by: "username",
  created_at: datetime(),
  reviewed_by: "expert_username",
  reviewed_at: datetime()
}]->()
```

## 🎨 UI Components

### Ingestion Tab
- **Location**: First tab (📤 Ingestion)
- **Purpose**: Upload documents and configure extraction
- **Key Features**:
  - PDF upload or text paste
  - Parameter sliders
  - Model selection
  - Real-time status updates

### Viewing Tab
- **Location**: Second tab (🔍 Viewing)
- **Purpose**: Explore knowledge graph
- **Key Features**:
  - Document multi-select
  - Concept search
  - Verification filters
  - Interactive graph visualization
  - Details panel

### Review Queue Tab
- **Location**: Third tab (opens new window)
- **Purpose**: Expert curation
- **Key Features**:
  - Statistics dashboard
  - Queue filtering
  - One-click actions
  - Original text context

## 🔐 Security Features

1. **Password Hashing**: bcrypt with salt rounds
2. **Session Management**: Express session with secrets
3. **User Isolation**: Documents tagged with creator
4. **Role Support**: Admin vs User roles (framework in place)

## 📊 Use Cases

### Case 1: Research Team Collaboration

**Team Lead:**
1. Signup with team account
2. Upload 10 papers on topic X
3. Configure high-quality extraction (GPT-4o, max_relationships=100)

**Domain Expert:**
1. Signup with expert account
2. Open Review Queue
3. Verify/flag all extractions
4. Build trusted knowledge base

**Researcher:**
1. Signup with researcher account
2. Search for concepts related to hypothesis
3. Filter to "verified only"
4. Export findings

### Case 2: Individual Literature Review

1. Signup
2. Upload papers one by one
3. Use moderate parameters (max_relationships=50)
4. After all uploads, search for key concepts
5. Review and verify critical relationships
6. Use verified graph for thesis/paper

### Case 3: Continuous Knowledge Building

1. Team uploads papers weekly
2. Experts review queue weekly
3. Knowledge graph grows over time
4. Contradictions surface as multi-source edges with different statuses
5. Consensus emerges from verified relationships

## 🐛 Troubleshooting

### "Invalid credentials"
- Check username/password spelling
- Ensure account created via signup
- Try default admin account (see .env)

### Ingestion fails
- Check PDF is readable (not scanned image)
- Verify OpenAI API key in config/.env
- Try reducing max_relationships
- Check server logs for details

### Graph doesn't load
- Ensure Neo4j is running
- Check at least one document is ingested
- Try refreshing document list
- Click "Load Graph" after selection

### User ID shows "anonymous"
- Login before ingesting
- Check session hasn't expired
- Try logout/login

## 💡 Tips & Best Practices

1. **Start Small**: Upload 1-2 documents first to test parameters
2. **Tune Parameters**: Adjust based on document length and complexity
3. **Review Regularly**: Don't let unverified queue get too large
4. **Use Descriptive Titles**: Makes document selection easier
5. **Search Broadly**: Start with general terms, narrow down
6. **Verify Critical Claims**: Focus review on high-impact relationships
7. **Track Sources**: Multi-source claims are more reliable

## 🎓 Training New Users

### For Uploaders:
1. Show signup/login flow
2. Demonstrate PDF upload with parameters
3. Explain parameter meaning
4. Show status feedback

### For Reviewers:
1. Show Review Queue navigation
2. Explain status meanings
3. Demonstrate confirm/flag actions
4. Show how it affects graph viewer

### For Researchers:
1. Show document selection
2. Demonstrate concept search
3. Explain verified filter
4. Show how to trace back to sources

---

## 🚀 What's New Summary

### ✅ Completed Features

1. **Unified Tabbed UI** - Single interface for all workflows
2. **Full Authentication** - Signup, login, logout with Node.js
3. **Ingestion Parameters** - Configurable max_concepts and max_relationships
4. **User Association** - All documents and reviews track user_id
5. **Enhanced Viewing** - Status indicators, search, filters
6. **API Integration** - Python backend ↔ Node.js auth server

### 🎯 URLs

- **Main App**: http://localhost:8000/app
- **Login**: http://localhost:8000/login
- **Signup**: http://localhost:8000/signup
- **API Docs**: http://localhost:8000/docs
- **Review Queue**: http://localhost:8000/review-ui

---

**Your knowledge synthesis platform is now production-ready with full user management!** 🎉

