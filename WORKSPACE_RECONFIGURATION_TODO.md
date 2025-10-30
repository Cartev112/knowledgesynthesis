# Workspace Reconfiguration - Implementation TODO

## Overview
Migrate workspace management from separate page to main app tab. Documents ingested globally, workspaces become logical views with document associations.

---

## BACKEND TASKS

### 1. Database Schema Changes
- [ ] **Remove workspace_id from Document nodes** - Documents are global, not workspace-scoped
- [ ] **Create document-workspace association relationships**
  - Add `(Document)-[:IN_WORKSPACE]->(Workspace)` relationship
  - Documents can belong to multiple workspaces
  - Track when document was added to workspace (`added_at` property)
  - Track who added it (`added_by` property)

### 2. Update Workspace Service (`workspace_service.py`)
- [ ] **Add document management methods:**
  - `add_document_to_workspace(workspace_id, document_id, user_id)` - Associate existing document
  - `remove_document_from_workspace(workspace_id, document_id, user_id)` - Remove association
  - `list_workspace_documents(workspace_id, user_id)` - Get all documents in workspace
  - `list_available_documents(user_id)` - Get all documents user can add (public + their private)
  
- [ ] **Modify existing methods:**
  - `get_workspace()` - Include document list in response
  - `get_workspace_stats()` - Count documents via IN_WORKSPACE relationships
  - Remove any document ingestion logic from workspace context

### 3. Update Workspace Routes (`routes/workspaces.py`)
- [ ] **Add new endpoints:**
  - `POST /api/workspaces/{workspace_id}/documents` - Add document to workspace
    - Body: `{ document_id: string }`
    - Returns: Updated workspace or success message
  
  - `DELETE /api/workspaces/{workspace_id}/documents/{document_id}` - Remove document
    - Returns: Success message
  
  - `GET /api/workspaces/{workspace_id}/documents` - List workspace documents
    - Returns: List of documents with metadata
  
  - `GET /api/documents/available` - List documents user can add to workspaces
    - Returns: All public documents + user's private documents

### 4. Update Ingestion Routes (`routes/ingest.py`, `routes/ingest_async.py`)
- [ ] **Remove workspace_id from ingestion**
  - Documents ingested globally (no workspace context)
  - Remove workspace_id parameter from ingestion endpoints
  - Remove BELONGS_TO relationship creation during ingestion

### 5. Update Query Routes (`routes/query.py`)
- [ ] **Modify graph queries to use IN_WORKSPACE:**
  - When workspace_id provided, filter via `(d:Document)-[:IN_WORKSPACE]->(:Workspace {workspace_id: $workspace_id})`
  - Entities/relationships filtered by their source documents being in workspace
  - Global view shows all public + user's private content

### 6. Migration Script
- [ ] **Create migration endpoint/script:**
  - Convert existing `(Document)-[:BELONGS_TO]->(Workspace)` to `(Document)-[:IN_WORKSPACE]->(Workspace)`
  - Preserve all existing data
  - Add `added_at` and `added_by` properties to relationships

---

## FRONTEND TASKS

### 1. Add Workspaces Tab to Main App (`index.html`)
- [ ] **Add tab to main navigation:**
  ```html
  <div class="tab" data-tab="workspaces">Workspaces</div>
  ```
  
- [ ] **Create workspaces tab content:**
  - Migrate grid layout from `workspaces.html`
  - Include: Create card, Global View card, workspace cards
  - Use existing workspace card styles

### 2. Workspace Tab Manager (`js/workspaces/workspace-tab-manager.js`)
- [ ] **Create new manager class:**
  - Load and display workspaces in grid
  - Handle workspace creation (use existing modal)
  - Handle workspace selection (switch to workspace, open detail modal)
  - Handle workspace settings (gear icon on each card)
  
- [ ] **Integrate with existing modals:**
  - Reuse create workspace modal from `workspaces.html`
  - Reuse workspace detail modal
  - Reuse workspace settings modal

### 3. Update Workspace Detail Modal
- [ ] **Add Document Management UI to Content tab:**
  - **Documents sub-tab enhancements:**
    - Add "➕ Add Documents" button
    - Show list of current workspace documents
    - Each document has remove button (❌)
  
  - **Add Documents Modal:**
    - Show available documents (public + user's private)
    - Search/filter documents
    - Multi-select documents to add
    - "Add Selected" button
  
- [ ] **Remove entity/relationship management:**
  - Keep Documents sub-tab
  - Remove Entities sub-tab
  - Remove Relationships sub-tab
  - Entities/relationships are automatically included via their source documents

### 4. Update Workspace Switcher (`workspace-switcher.js`)
- [ ] **Remove management button:**
  - Delete "🏠 Manage" button from modal footer
  - Remove `manage-workspaces-action` event listener
  - Remove navigation to `/workspaces.html`

- [ ] **Remove settings button from footer:**
  - Delete "⚙️ Settings" button from modal footer
  - Remove `workspace-settings-action` from footer

- [ ] **Add gear icon to workspace items:**
  - Add gear icon (⚙️) to each workspace item in the list (not Global View)
  - Right-aligned within workspace item
  - Click opens workspace settings modal
  - Stop propagation so clicking gear doesn't switch workspace

### 5. Ingestion Panel Updates
- [ ] **Remove workspace context from ingestion:**
  - Documents ingested globally
  - After ingestion, optionally prompt: "Add to workspace?"
  - User can add to current workspace or skip

### 6. Add Modals to Main App
- [ ] **Copy modals from workspaces.html to index.html:**
  - Create Workspace Modal (already exists in switcher, ensure it's in main HTML)
  - Workspace Settings Modal (ensure it's in main HTML)
  - Add Documents Modal (new - create this)

### 7. Cleanup
- [ ] **Remove/deprecate workspaces.html:**
  - Keep file for reference initially
  - Eventually delete once migration confirmed working
  - Update any links pointing to `/workspaces.html`

---

## DETAILED IMPLEMENTATION NOTES

### Backend: Document-Workspace Association

**Current (to be changed):**
```cypher
// Document belongs to ONE workspace
(Document {workspace_id: "xyz"})-[:BELONGS_TO]->(Workspace)
```

**New design:**
```cypher
// Document can be in MULTIPLE workspaces
(Document)-[:IN_WORKSPACE {added_at: datetime, added_by: "user_id"}]->(Workspace)
```

**Query pattern for workspace filtering:**
```cypher
// Get entities in workspace
MATCH (e:Entity)-[:EXTRACTED_FROM]->(d:Document)-[:IN_WORKSPACE]->(w:Workspace {workspace_id: $workspace_id})
RETURN e

// Get relationships in workspace
MATCH (e1:Entity)-[r]->(e2:Entity)
WHERE EXISTS {
  (e1)-[:EXTRACTED_FROM]->(d1:Document)-[:IN_WORKSPACE]->(:Workspace {workspace_id: $workspace_id})
}
AND EXISTS {
  (e2)-[:EXTRACTED_FROM]->(d2:Document)-[:IN_WORKSPACE]->(:Workspace {workspace_id: $workspace_id})
}
RETURN r
```

### Frontend: Workspace Switcher Gear Icon

**Current structure:**
```html
<div class="ws-item" data-workspace-id="123">
  <span class="ws-item-icon">📊</span>
  <span class="ws-item-name">My Workspace</span>
</div>
```

**New structure:**
```html
<div class="ws-item" data-workspace-id="123">
  <span class="ws-item-icon">📊</span>
  <span class="ws-item-name">My Workspace</span>
  <button class="ws-item-settings" data-workspace-id="123">⚙️</button>
</div>
```

**CSS addition:**
```css
.ws-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ws-item-settings {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  opacity: 0.6;
}

.ws-item-settings:hover {
  opacity: 1;
}
```

### Frontend: Add Documents Modal Structure

```html
<div class="modal" id="add-documents-modal">
  <div class="modal-content">
    <div class="modal-header">
      <h2>Add Documents to Workspace</h2>
      <button class="modal-close">&times;</button>
    </div>
    <div class="modal-body">
      <input type="search" placeholder="Search documents..." />
      <div class="documents-list">
        <!-- Checkboxes for each available document -->
      </div>
    </div>
    <div class="modal-footer">
      <button class="button button-secondary">Cancel</button>
      <button class="button button-primary">Add Selected</button>
    </div>
  </div>
</div>
```

---

## TESTING CHECKLIST

### Backend Tests
- [ ] Create workspace → verify no workspace_id on documents
- [ ] Ingest document globally → verify accessible to all users
- [ ] Add document to workspace → verify IN_WORKSPACE relationship created
- [ ] Remove document from workspace → verify relationship deleted, document remains
- [ ] Query workspace graph → verify only documents IN_WORKSPACE are included
- [ ] Add same document to multiple workspaces → verify works correctly
- [ ] Delete workspace → verify documents remain, only relationships deleted

### Frontend Tests
- [ ] Open Workspaces tab → verify grid displays correctly
- [ ] Create workspace → verify appears in grid and switcher
- [ ] Click workspace card → verify detail modal opens
- [ ] Click gear icon on workspace in switcher → verify settings modal opens
- [ ] Click workspace name in switcher → verify switches workspace (no settings)
- [ ] Add documents to workspace → verify they appear in workspace
- [ ] Remove document from workspace → verify removed but document still exists globally
- [ ] Switch between workspaces → verify different document sets
- [ ] Global view → verify shows all public + user's private content

---

## MIGRATION STRATEGY

### Phase 1: Backend (Non-breaking)
1. Add new document management endpoints
2. Keep old BELONGS_TO relationships working
3. Add IN_WORKSPACE relationship support to queries (OR condition)

### Phase 2: Migration Script
1. Run script to convert BELONGS_TO → IN_WORKSPACE
2. Verify data integrity
3. Test queries work with new relationships

### Phase 3: Frontend
1. Add Workspaces tab to main app
2. Update workspace switcher
3. Add document management UI
4. Test thoroughly

### Phase 4: Cleanup
1. Remove old BELONGS_TO relationship code
2. Remove workspace_id from ingestion
3. Deprecate workspaces.html
4. Update documentation

---

## FILES TO MODIFY

### Backend
- `app/models/workspace.py` - Add document management models
- `app/services/workspace_service.py` - Add document management methods
- `app/routes/workspaces.py` - Add document endpoints
- `app/routes/ingest.py` - Remove workspace_id
- `app/routes/ingest_async.py` - Remove workspace_id
- `app/routes/query.py` - Update to use IN_WORKSPACE
- `app/services/graph_write.py` - Remove BELONGS_TO creation

### Frontend
- `public/index.html` - Add Workspaces tab, modals
- `public/js/workspaces/workspace-tab-manager.js` - NEW FILE
- `public/js/workspaces/workspace-switcher.js` - Update gear icon, remove buttons
- `public/css/workspaces.css` - Ensure styles work in main app context
- `public/js/main.js` or equivalent - Initialize workspace tab manager

### To Deprecate
- `public/workspaces.html` - Eventually remove

---

## PRIORITY ORDER

1. **Backend document management** (foundation)
2. **Migration script** (data transformation)
3. **Frontend Workspaces tab** (UI migration)
4. **Workspace switcher updates** (UX improvements)
5. **Document management UI** (new functionality)
6. **Testing & cleanup** (validation)

---

## NOTES

- **NO filtering UI needed** - Workspaces are document collections, not filtered views
- **Reuse existing modals** - Don't recreate what exists in workspaces.html
- **Minimal new code** - Migrate, don't rebuild
- **Documents are global** - Ingestion happens once, shared across system
- **Workspaces = Document collections** - Simple association model
