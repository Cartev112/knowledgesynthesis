# Workspace & Multi-User UI Specification

**Version:** 1.0  
**Date:** October 23, 2025  
**Status:** Design Specification

---

## Overview

This document provides detailed UI/UX specifications for workspace management and multi-user collaboration features in the Knowledge Synthesis platform.

### Design Goals
- **Progressive disclosure:** Start simple, reveal complexity as needed
- **Context awareness:** Always show user where they are
- **Quick switching:** Minimize clicks to change context
- **Collaboration-first:** Make it easy to work with others

---

## 1. Workspace Landing Page (Post-Login)

### Layout

After login, users see a dashboard of their workspaces:

```
┌────────────────────────────────────────────────────────────────┐
│  Knowledge Synthesis            [User: Carter ▼] [Logout]     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Your Workspaces                                               │
│                                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ 📊 Immune   │  │ 🌱 Plant    │  │ ➕ Create   │           │
│  │    Cell     │  │    Biology  │  │    New      │           │
│  │ Engineering │  │  Research   │  │ Workspace   │           │
│  │             │  │             │  │             │           │
│  │ 42 docs     │  │ 18 docs     │  │             │           │
│  │ 847 entities│  │ 523 entities│  │             │           │
│  │ 2h ago      │  │ 1d ago      │  │             │           │
│  │             │  │             │  │             │           │
│  │ [Open] [⚙️] │  │ [Open] [⚙️] │  │             │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                │
│  ┌─────────────┐  ┌─────────────┐                            │
│  │ 📚 Lit      │  │ 🤝 Team     │                            │
│  │   Review    │  │   Project   │                            │
│  │             │  │  (shared)   │                            │
│  │ 8 docs      │  │ 67 docs     │                            │
│  │ 234 entities│  │ 2,103 ents  │                            │
│  │ 3d ago      │  │ 3 collabs   │                            │
│  │             │  │ 5h ago      │                            │
│  │ [Open] [⚙️] │  │ [Open] [⚙️] │                            │
│  └─────────────┘  └─────────────┘                            │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 🌐 Global View - All Workspaces                          │ │
│  │ 135 documents • 4,107 entities                           │ │
│  │ [Explore Global Graph]                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### Workspace Card Features
- **Icon & Color:** Visual identifier
- **Name:** Workspace title
- **Stats:** Document count, entity count
- **Last Activity:** Timestamp
- **Collaborators:** Badge if shared
- **Actions:** Open, Settings

### Create New Workspace Modal

```
┌─────────────────────────────────────────────────────────┐
│  Create New Workspace                          [✕]      │
├─────────────────────────────────────────────────────────┤
│  Name *                                                 │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Immune Cell Engineering                           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Description (optional)                                 │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Research on CAR-T cell engineering...             │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Icon & Color                                           │
│  🧬 🔬 🧪 💉 📊 📈 🌱 🔭 ⚗️ 🧫                          │
│  [🔴 🟠 🟡 🟢 🔵 🟣]                                    │
│                                                         │
│  Privacy                                                │
│  ● Private (only you)                                   │
│  ○ Shared (invite collaborators)                       │
│                                                         │
│                      [Cancel]  [Create Workspace]      │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Main Platform - Workspace Context

### Top Navigation Bar

```
┌────────────────────────────────────────────────────────────────┐
│ 📊 Immune Cell Engineering ▼  [Upload] [Discovery] [Query]    │
│                                              [User ▼] [Help]   │
└────────────────────────────────────────────────────────────────┘
```

**Key Element:** Workspace Switcher (top-left)

### Workspace Switcher Dropdown

Click on workspace name to open:

```
┌─────────────────────────────────────────────────────┐
│  Current Workspace                                  │
│  ┌───────────────────────────────────────────────┐ │
│  │ ✓ 📊 Immune Cell Engineering                  │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Your Workspaces                                    │
│    🌱 Plant Biology Research                        │
│    📚 Literature Review                             │
│    🤝 Team Project (shared)                         │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  🌐 Global View (All Workspaces)                    │
│  ➕ Create New Workspace                            │
│  🏠 Back to Workspace Landing                       │
│                                                     │
│  Quick Actions                                      │
│  ⚙️  Workspace Settings                             │
│  👥 Manage Collaborators                            │
└─────────────────────────────────────────────────────┘
```

**Behavior:**
- Always visible in top-left
- One-click to switch workspaces
- Quick access to settings
- Return to landing page

---

## 3. View Filter System

### Filter Panel Location

**Recommended:** Right sidebar, collapsible

**Access Methods:**
1. Button in top nav: "🔍 Filters" or "👁️ View"
2. Keyboard shortcut: `Ctrl+Shift+F`
3. Auto-opens when needed

### Filter Panel UI

```
┌─────────────────────────────────────────┐
│  View Filters                     [✕]  │
├─────────────────────────────────────────┤
│  Scope                                  │
│  ● Workspace View (all content)         │
│  ○ My Content Only                      │
│  ○ Collaborative View (select users)    │
│  ○ Global View (entire database)        │
│                                         │
│  ┌─ Collaborative View ──────────────┐ │
│  │ Select Users:                     │ │
│  │ ☑ Carter Whitworth (me)           │ │
│  │ ☑ Belinda Akpa                    │ │
│  │ ☐ Abhinav Gorantla                │ │
│  │                                   │ │
│  │ [Select All] [Clear]              │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Entity Types                           │
│  ☑ Gene  ☑ Protein  ☐ Disease          │
│  ☑ Drug  ☐ Pathway  ☑ Method           │
│                                         │
│  Date Range                             │
│  From: [2025-01-01]                     │
│  To:   [2025-12-31]                     │
│                                         │
│  Significance                           │
│  Min: [3] ═══●═════ Max: [5]            │
│                                         │
│  [Reset]  [Apply]                       │
│                                         │
│  Stats: 847 entities • 2,341 rels       │
└─────────────────────────────────────────┘
```

### Quick Collaborative View

**Alternative UI for "My Content + Belinda's Content":**

Add a **Quick Collab Button** next to workspace switcher:

```
┌────────────────────────────────────────────────────────┐
│ 📊 Workspace ▼  [👥 Collab View]  [Upload] [Discovery] │
└────────────────────────────────────────────────────────┘
```

Click "👥 Collab View" to open:

```
┌─────────────────────────────────────────┐
│  Quick Collaborative View               │
├─────────────────────────────────────────┤
│  Select users to view together:         │
│                                         │
│  ☑ Me (Carter)                          │
│  ☑ Belinda Akpa                         │
│  ☐ Abhinav Gorantla                     │
│  ☐ K. Selcuk Candan                     │
│                                         │
│  Presets:                               │
│  • Me + Belinda                         │
│  • Team (All 4)                         │
│  • [+ Save Current]                     │
│                                         │
│  [Cancel]  [Apply]                      │
└─────────────────────────────────────────┘
```

**Benefits:**
- Fast access (2 clicks)
- Save common combinations
- Visual user selection

---

## 4. Context Indicators

### Status Bar (Bottom)

```
┌────────────────────────────────────────────────────────────┐
│ 📊 Immune Cell Engineering • Collaborative View (Me +     │
│ Belinda) • 847 entities • 2,341 rels • Updated 2h ago     │
└────────────────────────────────────────────────────────────┘
```

Shows:
- Current workspace
- Active view mode
- Graph statistics
- Last update time

### Visual Indicators in Graph

**Node Colors by Creator:**
- Each user assigned a color
- Nodes colored by creator
- Legend in corner:

```
┌─────────────────┐
│ Created By:     │
│ 🔵 You (Carter) │
│ 🟢 Belinda      │
│ 🟡 Abhinav      │
└─────────────────┘
```

**Workspace Badges:**
- In Global View, show workspace origin
- Small badge on nodes: `📊` or `🌱`

---

## 5. Workspace Settings

Access via gear icon on workspace card or switcher dropdown:

```
┌─────────────────────────────────────────────────────────┐
│  Workspace Settings: Immune Cell Engineering   [✕]     │
├─────────────────────────────────────────────────────────┤
│  [General] [Collaborators] [Extraction] [Privacy]      │
│                                                         │
│  General                                                │
│  Name: [Immune Cell Engineering]                        │
│  Description: [Research on CAR-T cells...]              │
│  Icon: 🧬 [Change]  Color: 🔵 [Change]                 │
│                                                         │
│  Collaborators                                          │
│  Owner: Carter Whitworth                                │
│                                                         │
│  Members (2):                                           │
│  • Belinda Akpa - Can view, add docs [Edit] [Remove]   │
│  • Abhinav Gorantla - Can view only [Edit] [Remove]    │
│                                                         │
│  [+ Invite Collaborator]                                │
│                                                         │
│  Extraction Settings                                    │
│  Strategy: ● Balanced ○ Diversity ○ Connectedness      │
│  Max Relationships: [50]                                │
│  ☑ Auto-generate embeddings                            │
│                                                         │
│  Privacy                                                │
│  ● Private  ○ Organization  ○ Public                    │
│                                                         │
│  Danger Zone                                            │
│  [Archive Workspace]  [Delete Workspace]                │
│                                                         │
│                          [Cancel]  [Save Changes]      │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Technical Implementation

### Database Schema

```cypher
// Workspace Node
CREATE (w:Workspace {
  workspace_id: 'uuid',
  name: 'Immune Cell Engineering',
  description: 'Research...',
  icon: '🧬',
  color: '#3B82F6',
  privacy: 'private',
  created_by: 'user_id',
  created_at: datetime()
})

// User-Workspace Membership
CREATE (u:User)-[:MEMBER_OF {
  role: 'owner', // 'owner', 'editor', 'viewer'
  permissions: ['view', 'add_documents'],
  joined_at: datetime()
}]->(w:Workspace)

// Document belongs to Workspace
CREATE (d:Document)-[:BELONGS_TO]->(w:Workspace)
```

### API Endpoints

```javascript
GET    /api/workspaces              // List user's workspaces
POST   /api/workspaces              // Create workspace
GET    /api/workspaces/:id          // Get workspace
PUT    /api/workspaces/:id          // Update workspace
DELETE /api/workspaces/:id          // Delete workspace

POST   /api/workspaces/:id/invite   // Invite user
DELETE /api/workspaces/:id/members/:userId // Remove member

POST   /api/graph/filter            // Apply view filters
GET    /api/graph/stats             // Get filtered stats
```

### Frontend State

```javascript
const WorkspaceContext = {
  currentWorkspace: {
    id: 'workspace_id',
    name: 'Immune Cell Engineering',
    role: 'owner'
  },
  
  viewMode: 'collaborative', // 'my_content', 'workspace', 'collaborative', 'global'
  
  filters: {
    users: ['user_id_1', 'user_id_2'],
    entityTypes: ['Gene', 'Protein'],
    dateRange: { start: '2025-01-01', end: '2025-12-31' }
  }
}
```

---

## 7. User Flow Summary

### Typical Workflow

1. **Login** → Workspace Landing Page
2. **Select** workspace (or create new)
3. **Work** in main platform with workspace context
4. **Switch** workspace via top-left switcher (1 click)
5. **Filter** view via right sidebar or quick collab button
6. **Collaborate** by selecting multiple users
7. **Manage** workspace via settings

### Key Interaction Points

| Action | Location | Clicks |
|--------|----------|--------|
| Switch workspace | Top-left switcher | 2 |
| Create workspace | Landing page or switcher | 2 |
| Collaborative view | Quick collab button | 2 |
| Filter by user | Right sidebar | 3 |
| Workspace settings | Switcher dropdown | 2 |
| Return to landing | Switcher dropdown | 2 |

---

## 8. Recommendations

### Phase 1 (MVP)
- ✅ Workspace landing page
- ✅ Workspace switcher in top nav
- ✅ Basic filtering (my content vs workspace)
- ✅ Workspace settings

### Phase 2 (Enhanced)
- ✅ Collaborative view with user selection
- ✅ Quick collab button
- ✅ View presets
- ✅ Status bar indicators

### Phase 3 (Advanced)
- Real-time presence
- Activity feed
- Advanced permissions
- Workspace templates

---

## 9. Design Assets Needed

- Workspace icons (emoji or custom)
- Color palette for user identification
- Loading states for workspace switching
- Empty states for new workspaces
- Onboarding tutorial screens

---

**Document Status:** Ready for Implementation  
**Next Steps:** Create mockups, gather team feedback, begin frontend development
