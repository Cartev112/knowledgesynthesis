# Knowledge Synthesis Platform - Implementation Plan
**Based on Meeting: October 30, 2025**

---

## 🎯 HIGH PRIORITY TASKS

### 1. Workspace Architecture Redesign
**Current State:** Workspaces are document-centric - documents are ingested into specific workspaces and isolated from other workspaces.

**Required Change:** Workspaces should be **logical/declarative views** over a shared global database.

**Implementation:**
- [ ] Documents are ingested into the **global database** (not into workspaces)
- [ ] Workspaces become **filtered views** with:
  - Custom visualization settings
  - Filter criteria (by document, entity type, relationship type, etc.)
  - Layout preferences
  - Display options (show/hide IS_A relationships, etc.)
- [ ] Same document can appear in multiple workspaces without re-ingestion
- [ ] Users can add/remove existing documents/entities/relationships to workspaces
- [ ] Workspace = Visualization + Filtering + Selection criteria (NOT a separate data store)

**Rationale:** 
- Enables multidisciplinary collaboration with different perspectives on same data
- Allows users to create focused views for different use cases
- Prevents data duplication and inconsistency
- Papers/documents should only be ingested once into the system

---

### 2. Document Deduplication System
**Problem:** System doesn't recognize when the same PDF is uploaded multiple times, creating duplicate documents.

**Implementation:**
- [ ] **Metadata-based detection:**
  - Extract DOI, title, authors from PDF metadata
  - Hash PDF content for exact match detection
  - Check against existing documents before processing
  
- [ ] **User confirmation workflow:**
  - When uploading, check if document already exists
  - Show user: "We found a similar document. Is this the same paper?"
  - If yes: Link to existing document and its extracted graph
  - If no: Process as new document
  
- [ ] **DOI-centric ingestion option:**
  - Add field for users to provide DOI directly
  - Fetch metadata from DOI
  - Check if DOI already exists in system
  - Prioritize DOI matching over file matching

**Files to modify:**
- Ingestion backend (document upload handler)
- Database schema (add DOI, content hash fields)
- Frontend upload UI

---

### 3. Enhanced Filtering System
**Current State:** Basic filtering exists but needs expansion for workspace functionality.

**Required Features:**
- [ ] **Filter by Entity Type:**
  - Show/hide specific ontological types (Outcome, Metric, Process, etc.)
  - Multi-select type filtering
  
- [ ] **Filter by Relationship Type:**
  - Toggle IS_A relationships on/off
  - Filter by predicate (causes, improves, relates_to, etc.)
  - Option to make IS_A relationships lighter/grayed out
  
- [ ] **Filter by Document:**
  - Select specific documents to include in view
  - Filter by document metadata (author, date, source)
  
- [ ] **Filter by Significance:**
  - Threshold sliders for node/relationship significance
  - Show only high-confidence relationships
  
- [ ] **Save Filter Presets:**
  - Save filter combinations as workspace configurations
  - Quick toggle between filter presets

**UI Location:** Expand existing filter panel in viewing tab

---

### 4. Extraction Prompt Improvements
**Problem:** LLM extracting too many literal/trivial relationships, especially IS_A type relationships overwhelming useful semantic relationships.

**Current Issues:**
- Extracting word-for-word phrases without higher-order sense-making
- IS_A relationships dominating the extraction quota
- Not enough conceptually meaningful relationships

**Action Items:**
- [x] Made `original_text` field optional (completed)
- [x] Encouraged implicit relationship extraction (completed)
- [ ] **Share prompt with team for review** (Dr. Candan, Dr. Akpa)
- [ ] **Adjust extraction priorities:**
  - Deprioritize IS_A relationships in the extraction quota
  - Emphasize semantic/causal relationships
  - Focus on "most significant relationships" more explicitly
  
- [ ] **Test with different models:**
  - Dr. Candan to test with GPT-5 or other models
  - Compare extraction quality across models

**Files:**
- `backendAndUI/python_worker/app/services/openai_extract.py`

---

### 5. Ontological Type System Refinement
**Problem:** LLM using generic terms like "Concept" and "Entity" as types, which is confusing since everything is a concept/entity.

**Implementation:**
- [ ] **Blacklist generic terms:**
  - Add to prompt: "Do NOT use 'Concept' or 'Entity' as types"
  - Exception: If the paper is about philosophy/linguistics where "concept" has domain meaning
  
- [ ] **Improve type extraction guidance:**
  - Emphasize domain-specific, descriptive types
  - Examples: Metric, Framework, Process, Outcome, Property, Gene, Protein, etc.
  - Avoid overly generic classifications

**Note:** Some generic types (Outcome, Metric) are valuable for newcomers to a field, so keep them but make them filterable.

---

### 6. IS_A Relationship Visualization Controls
**Problem:** IS_A (ontological type) relationships overwhelm the graph visualization.

**Implementation:**
- [ ] **Toggle IS_A relationships:**
  - Checkbox to show/hide all IS_A relationships
  - Default: Hidden or grayed out
  
- [ ] **Visual styling options:**
  - Make IS_A edges lighter gray/dashed
  - Reduce opacity when shown
  - Different color scheme for ontological vs semantic relationships
  
- [ ] **Layout considerations:**
  - Hierarchical layout works well for ontological relationships
  - Force-directed layout gets cluttered with IS_A edges
  - Concentric layout shows types in center effectively

**Files:**
- `node-server/public/js/viewing/visual-config.js`
- `node-server/public/js/viewing/cytoscape-config.js`

---

### 7. User Annotation System
**Feature Request:** Allow users to add free-form annotations to nodes and relationships.

**Implementation:**
- [ ] **Node annotations:**
  - Click node → "Add annotation" button
  - Text field for user notes/definitions
  - Display annotations in node tooltip/modal
  
- [ ] **Relationship annotations:**
  - Similar annotation capability for edges
  - Explain why relationship is important
  - Add context or corrections
  
- [ ] **Annotation storage:**
  - User-specific annotations (not shared by default)
  - Option to make annotations public/workspace-specific
  
- [ ] **Annotation display:**
  - Show annotation indicator on annotated nodes/edges
  - Include in search/filter

**Database schema:**
- New table: `annotations` (user_id, node_id/edge_id, text, visibility, timestamp)

---

### 8. Documentation Requirements
**Critical Need:** Design decisions are not transparent to team members.

**Required Documentation:**
- [ ] **Architecture Documentation:**
  - System architecture diagram
  - Data model/schema documentation
  - Workspace design decisions
  - Authentication/authorization model
  
- [ ] **API Documentation:**
  - Backend endpoints
  - Request/response formats
  - Error handling
  
- [ ] **Feature Specifications:**
  - How workspaces work
  - How filtering works
  - How extraction context works
  - How deduplication works
  
- [ ] **Extraction Prompt Documentation:**
  - Current prompt text
  - Rationale for each instruction
  - Version history

**Format:** Markdown files in `/docs` directory

---

## 🔧 MEDIUM PRIORITY TASKS

### 9. Forgot Password Feature
**Status:** Multiple team members had to create new accounts due to password issues.

**Implementation:**
- [ ] Add "Forgot Password" link on login page
- [ ] Email-based password reset flow
- [ ] Temporary reset tokens (expire after 1 hour)
- [ ] Email service configuration (SendGrid or similar)

**Note:** Previous password storage issue has been fixed.

---

### 10. Email Service Configuration
**Problem:** Email service not working (SendGrid issue).

**Tasks:**
- [ ] Debug SendGrid configuration
- [ ] Test email sending for:
  - Password reset
  - Account verification
  - Workspace invitations (future feature)
  - Extraction completion notifications (optional)

---

### 11. API Key Access for Team
**Status:** Abhinav working on getting OpenAI API keys through university IT.

**Action Items:**
- [ ] Abhinav to contact Jill (IT contact) - CC Dr. Candan
- [ ] Mention NSF-funded project and Carter as visiting scholar
- [ ] Ensure Carter has immediate access to API keys
- [ ] Document API key setup process for future team members

---

## 📋 COMPLETED FEATURES (Recent)

### ✅ Context Configuration Modal
- New modal for graph context selection
- Options: Concepts, Relationships, Current Filtered View, Specific Documents
- When documents selected, automatically includes all entities/relationships from those documents

### ✅ Extraction Intent Controls
- Four intent options: Complement, Conflict, Extend, Distinct
- Guides extraction to find relationships that match user's goal

### ✅ Ontological Type System
- Changed from properties to relationships (IS_A edges)
- Enables better visualization and filtering
- Works well with hierarchical layouts

### ✅ Index Panel Improvements
- Relationships now explicitly state the actual relationship type
- Clearer display of graph structure

### ✅ Multiple Layout Options
- Force-directed (COSE, fCOSE, COLA)
- Hierarchical (Dagre)
- Concentric
- Circular
- Grid
- Breadth-first
- User can choose layout based on visualization needs

### ✅ Visual Configuration Panel
- Compact side panel
- Node color schemes (by type, user, document, degree)
- Node size schemes (significance, degree, centrality)
- Label display modes (hover, always, selected, never)
- Layout controls with spread slider

---

## 🎨 UI/UX IMPROVEMENTS NEEDED

### 12. Workspace Tab Integration
**Current:** Workspaces have separate page
**Proposed:** Workspaces should be a tab on main page

**Rationale:** Better integration with main workflow

---

### 13. Documents Tab Redesign
**Proposed Functionality:**
- Show all documents in DB (public + user's private)
- Allow adding existing documents to workspaces
- Show document metadata (DOI, authors, date, ingestion status)
- Prevent duplicate ingestion of same document

---

## 📊 TESTING & VALIDATION

### Test Cases Needed:
- [ ] Upload same PDF twice - verify deduplication works
- [ ] Create workspace with filters - verify correct data shown
- [ ] Switch between workspaces - verify views are independent
- [ ] Test all layout algorithms with ontological graphs
- [ ] Verify IS_A relationship toggle works
- [ ] Test extraction with different prompts/models
- [ ] Validate annotation system
- [ ] Test forgot password flow

---

## 🗓️ SUGGESTED TIMELINE

**Week 1-2: Core Architecture**
1. Workspace redesign (logical views)
2. Document deduplication system
3. Enhanced filtering foundation

**Week 3-4: Extraction & Visualization**
4. Prompt improvements (with team feedback)
5. IS_A relationship controls
6. Type system refinement

**Week 5-6: User Features**
7. Annotation system
8. Forgot password
9. Email service
10. Documentation

**Week 7: Testing & Polish**
- Comprehensive testing
- Bug fixes
- UI/UX refinements

---

## 📝 NOTES FROM MEETING

### Key Insights:
- **Workspaces as perspectives:** Different users (domain experts vs newcomers) need different views of same data
- **Filtering is crucial:** Generic types (Outcome, Metric) are useful for some users, overwhelming for others
- **Layout matters:** Hierarchical/concentric layouts work better for ontological relationships than force-directed
- **Quality over quantity:** Better to extract fewer, more meaningful relationships than many trivial ones
- **Documentation gap:** Team needs visibility into design decisions to provide effective feedback

### Team Feedback:
- Dr. Candan: Workspaces should be logical/declarative, not physical isolation
- Dr. Akpa: Generic types can be valuable for newcomers but need filtering
- Dr. Akpa: Recent extractions too literal, need higher-order sense-making
- Abhinav: Need forgot password feature
- All: Need to review extraction prompt

---

## 🔗 RELATED FILES

**Backend:**
- `backendAndUI/python_worker/app/services/openai_extract.py` - Extraction prompt
- `backendAndUI/python_worker/app/routes/query.py` - Query endpoints
- `backendAndUI/python_worker/app/routes/workspaces.py` - Workspace logic
- `backendAndUI/python_worker/app/services/workspace_service.py` - Workspace service

**Frontend:**
- `node-server/public/index.html` - Main UI structure
- `node-server/public/js/viewing/visual-config.js` - Visual configuration
- `node-server/public/js/viewing/graph-viewer.js` - Graph rendering
- `node-server/public/js/viewing/cytoscape-config.js` - Graph styling
- `node-server/public/css/ingestion.css` - Ingestion panel styles

**Documentation:**
- `TODO.MD` - Current task list
- `IMPLEMENTATION_PLAN.md` - This document

---

## ✅ NEXT IMMEDIATE ACTIONS

1. **Share extraction prompt with team** (email to Dr. Candan, Dr. Akpa)
2. **Start workspace architecture redesign** (highest priority)
3. **Implement document deduplication** (prevents immediate user frustration)
4. **Create architecture documentation** (enables better team feedback)
5. **Abhinav: Contact IT for API keys** (CC Dr. Candan)

---

*Last Updated: October 30, 2025*
*Meeting Participants: Dr. K. Selcuk Candan, Dr. Belinda Akpa, Carter Whitworth, Abhinav Gorantla*
