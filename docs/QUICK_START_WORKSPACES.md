# Quick Start Guide - Workspaces Feature

**Date:** October 23, 2025

---

## 🚀 What's Been Implemented

### ✅ Backend (Ready to Use)
- Complete workspace API
- Authentication system
- Worker integration
- Database schema

### ✅ Frontend (Ready to Use)
- Workspace landing page
- Workspace switcher component
- View filter component
- All UI components and styles

---

## 📁 Files Created

### Backend (Python)
```
app/models/
  ├── user.py                    # User model
  └── workspace.py               # Workspace models

app/core/
  └── auth.py                    # Auth dependencies

app/services/
  └── workspace_service.py       # Workspace CRUD service

app/routes/
  └── workspaces.py              # API endpoints
```

### Frontend (JavaScript/HTML/CSS)
```
public/
  ├── workspaces.html            # Landing page
  ├── css/
  │   ├── workspaces.css         # Landing page styles
  │   ├── workspace-switcher.css # Switcher component styles
  │   └── view-filter.css        # Filter panel styles
  └── js/workspaces/
      ├── workspaces.js          # Landing page logic
      ├── workspace-switcher.js  # Switcher component
      └── view-filter.js         # Filter component
```

---

## 🔧 Integration Steps

### Step 1: Test Backend APIs

**Start the backend:**
```bash
cd backendAndUI/python_worker
python -m app.main
```

**Test workspace creation:**
```bash
# Login first to get session cookie
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  -c cookies.txt

# Create workspace
curl -X POST http://localhost:8000/api/workspaces \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Test Workspace",
    "description": "My first workspace",
    "icon": "🧪",
    "color": "#3B82F6",
    "privacy": "private"
  }'

# List workspaces
curl http://localhost:8000/api/workspaces -b cookies.txt
```

### Step 2: Add Workspace Switcher to Main App

**In your main app HTML (e.g., `index.html` or `app.html`):**

```html
<head>
  <!-- Add CSS -->
  <link rel="stylesheet" href="css/workspace-switcher.css">
  <link rel="stylesheet" href="css/view-filter.css">
</head>

<body>
  <!-- Add switcher container in navigation -->
  <nav>
    <div id="workspace-switcher-container"></div>
    <!-- Other nav items -->
  </nav>

  <!-- Add filter panel container (sidebar) -->
  <aside id="view-filter-container" style="display: none;">
    <!-- Filter panel will be rendered here -->
  </aside>

  <!-- Your main content -->
  <main>
    <!-- Graph visualization, etc. -->
  </main>

  <!-- Add scripts -->
  <script type="module">
    import WorkspaceSwitcher from './js/workspaces/workspace-switcher.js';
    import ViewFilter from './js/workspaces/view-filter.js';

    // Initialize components
    const switcher = new WorkspaceSwitcher('workspace-switcher-container');
    const filter = new ViewFilter('view-filter-container');

    // Add button to toggle filter panel
    const filterButton = document.createElement('button');
    filterButton.textContent = '🔍 Filters';
    filterButton.onclick = () => filter.toggle();
    document.querySelector('nav').appendChild(filterButton);

    // Listen for workspace changes
    window.addEventListener('workspaceChanged', (e) => {
      console.log('Workspace changed:', e.detail);
      // Reload your graph with workspace filter
      loadGraph(e.detail.workspaceId);
    });

    // Listen for filter changes
    window.addEventListener('filtersChanged', (e) => {
      console.log('Filters changed:', e.detail);
      // Apply filters to your graph
      applyFilters(e.detail.filters);
    });
  </script>
</body>
```

### Step 3: Update Document Upload to Include Workspace

**When uploading documents, include workspace_id:**

```javascript
// In your upload/ingestion code
const currentWorkspaceId = sessionStorage.getItem('currentWorkspaceId');

const jobData = {
  pdf_bytes: base64Pdf,
  user_id: currentUser.user_id,
  user_email: currentUser.email,
  user_first_name: currentUser.first_name,
  user_last_name: currentUser.last_name,
  workspace_id: currentWorkspaceId,  // Add this!
  max_relationships: 50
};

// Send to ingestion API
await API.post('/api/ingest/pdf', jobData);
```

### Step 4: Filter Graph Queries by Workspace

**Update your graph queries to filter by workspace:**

```cypher
// Example: Get entities in current workspace
MATCH (d:Document)-[:BELONGS_TO]->(w:Workspace {workspace_id: $workspace_id})
MATCH (d)<-[:EXTRACTED_FROM]-(e:Entity)
RETURN DISTINCT e

// Example: Get relationships in workspace
MATCH (d:Document)-[:BELONGS_TO]->(w:Workspace {workspace_id: $workspace_id})
MATCH (d)<-[:EXTRACTED_FROM]-(s:Entity)-[r]->(o:Entity)
RETURN s, r, o
```

---

## 🎨 UI Integration Examples

### Example 1: Simple Navigation Bar

```html
<nav class="main-nav">
  <div class="nav-left">
    <h1>Knowledge Synthesis</h1>
    <div id="workspace-switcher-container"></div>
  </div>
  <div class="nav-right">
    <button onclick="showFilters()">🔍 Filters</button>
    <button onclick="uploadDocument()">📤 Upload</button>
  </div>
</nav>
```

### Example 2: Sidebar with Filter Panel

```html
<div class="app-layout">
  <aside class="sidebar">
    <div id="view-filter-container"></div>
  </aside>
  <main class="main-content">
    <!-- Your graph visualization -->
  </main>
</div>
```

### Example 3: Redirect to Workspaces on Login

```javascript
// After successful login
async function handleLogin() {
  const response = await API.post('/api/auth/login', credentials);
  
  if (response.success) {
    // Redirect to workspaces landing page
    window.location.href = '/workspaces.html';
  }
}
```

---

## 🧪 Testing Checklist

### Backend Tests
- [ ] Create workspace via API
- [ ] List workspaces for user
- [ ] Update workspace details
- [ ] Invite member to workspace
- [ ] Remove member from workspace
- [ ] Delete workspace
- [ ] Upload document with workspace_id
- [ ] Verify document has BELONGS_TO relationship

### Frontend Tests
- [ ] Access workspaces landing page
- [ ] Create new workspace via UI
- [ ] View workspace cards with stats
- [ ] Click "Open" to enter workspace
- [ ] Switch between workspaces using switcher
- [ ] Toggle view filter panel
- [ ] Select collaborative view with multiple users
- [ ] Apply filters and verify graph updates
- [ ] Return to workspaces landing page

### Integration Tests
- [ ] Login → Redirects to workspaces
- [ ] Select workspace → Graph shows only workspace content
- [ ] Upload document → Associates with current workspace
- [ ] Switch workspace → Graph updates
- [ ] Global view → Shows all content
- [ ] Collaborative view → Shows selected users' content

---

## 🐛 Troubleshooting

### Issue: "Not authenticated" error
**Solution:** Make sure you're logged in. Session cookies must be present.

### Issue: Workspaces not loading
**Solution:** Check browser console for errors. Verify backend is running and `/api/workspaces` endpoint is accessible.

### Issue: Documents not appearing in workspace
**Solution:** Verify `workspace_id` is being passed in ingestion job data. Check Neo4j for `BELONGS_TO` relationships.

### Issue: Switcher not showing current workspace
**Solution:** Ensure `currentWorkspaceId` is set in sessionStorage when opening a workspace.

### Issue: Filter panel not appearing
**Solution:** Make sure container element exists and ViewFilter is initialized. Check CSS is loaded.

---

## 📊 Database Queries for Debugging

```cypher
// Check workspaces
MATCH (w:Workspace)
RETURN w

// Check workspace members
MATCH (u:User)-[m:MEMBER_OF]->(w:Workspace)
RETURN u.email, w.name, m.role

// Check documents in workspace
MATCH (d:Document)-[:BELONGS_TO]->(w:Workspace)
RETURN w.name, count(d) as doc_count

// Check entities in workspace
MATCH (d:Document)-[:BELONGS_TO]->(w:Workspace)
MATCH (d)<-[:EXTRACTED_FROM]-(e:Entity)
RETURN w.name, count(DISTINCT e) as entity_count
```

---

## 🚀 Next Steps

1. **Test the backend APIs** using curl or Postman
2. **Access the workspaces landing page** at `/workspaces.html`
3. **Create a test workspace** and verify it appears
4. **Integrate workspace switcher** into your main app
5. **Update document upload** to include workspace_id
6. **Test workspace filtering** in graph queries
7. **Add filter panel** for collaborative views

---

## 📝 Configuration

### Environment Variables (Optional)

```bash
# If you want to customize workspace defaults
WORKSPACE_DEFAULT_ICON=📊
WORKSPACE_DEFAULT_COLOR=#3B82F6
MAX_WORKSPACES_PER_USER=50
```

### Session Storage Keys

```javascript
// Current workspace ID
sessionStorage.getItem('currentWorkspaceId')

// Set workspace
sessionStorage.setItem('currentWorkspaceId', 'workspace-uuid')

// Clear workspace (global view)
sessionStorage.removeItem('currentWorkspaceId')
```

---

## ✨ Features Summary

**What Users Can Do:**
- ✅ Create personal workspaces
- ✅ Organize documents by topic/project
- ✅ Invite collaborators to workspaces
- ✅ Control permissions (Owner, Editor, Viewer)
- ✅ Switch between workspaces quickly
- ✅ View only their own content
- ✅ View combined content from selected users
- ✅ Access global view of all content
- ✅ Filter by entity types, dates, significance
- ✅ See workspace statistics

**What's Automatic:**
- ✅ Documents associate with current workspace
- ✅ Entities inherit workspace from documents
- ✅ Permission checking on all operations
- ✅ Statistics calculation
- ✅ Session management

---

## 📞 Support

If you encounter issues:
1. Check browser console for JavaScript errors
2. Check backend logs for API errors
3. Verify Neo4j database schema
4. Review this guide's troubleshooting section
5. Check the detailed specification docs

---

**Implementation Status:** ✅ Ready for Testing  
**Estimated Setup Time:** 30 minutes  
**Documentation:** Complete
