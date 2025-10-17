# Quick Start Guide - Migrated UI

## 🚀 Running the Application

### Step 1: Start Python Backend
```bash
cd backendAndUI/python_worker
uvicorn app.main:app --reload
```
Server will run on: http://127.0.0.1:8000

### Step 2: Start Node.js Frontend
```bash
cd node-server
node server.js
```
Server will run on: http://127.0.0.1:3000

### Step 3: Access the App
Open your browser to: **http://127.0.0.1:3000**

Login with default credentials:
- Username: `admin`
- Password: `admin123`

## 📁 File Structure

```
node-server/public/
├── index.html              # Main HTML file
├── css/                    # All stylesheets
│   ├── base.css           # Core styles
│   ├── ingestion.css      # Upload UI
│   ├── viewing.css        # Graph viewer
│   ├── query-builder.css  # Query UI
│   └── modals.css         # Modals & tooltips
└── js/                     # All JavaScript
    ├── main.js            # App entry point
    ├── auth.js            # Authentication
    ├── state.js           # Global state
    ├── utils/             # Utilities
    ├── ingestion/         # Upload logic ✅
    ├── viewing/           # Graph viewer (TODO)
    └── query-builder/     # Query logic (TODO)
```

## ✅ What's Working

- ✅ User authentication
- ✅ Document ingestion (PDF & text)
- ✅ Progress tracking
- ✅ Job status polling
- ✅ Graph context integration
- ✅ Tab navigation
- ✅ All styling

## ⚠️ What Needs Work

The following modules need to be completed by extracting code from the old `main_ui.py`:

1. **Graph Viewer** (`public/js/viewing/graph-viewer.js`)
   - Cytoscape initialization
   - Graph rendering
   - Node/edge interactions

2. **Query Builder** (`public/js/query-builder/query-builder.js`)
   - Pattern queries
   - Result visualization

## 🔧 Development

### Making Changes

**CSS Changes**: Edit files in `node-server/public/css/`  
**JavaScript Changes**: Edit files in `node-server/public/js/`  
**HTML Changes**: Edit `node-server/public/index.html`

Refresh browser to see changes (no rebuild needed for static files).

### Adding New Features

1. Create new module in appropriate directory
2. Import in `main.js`
3. Wire up in `AppManager` class
4. Add to `window` object if needed for inline handlers

## 📝 Key Files

- **server.js**: Node.js server, serves static files, proxies API
- **main.js**: Application coordinator, initializes all modules
- **ingestion.js**: Complete document upload implementation
- **api.js**: Centralized API communication
- **state.js**: Shared application state

## 🐛 Troubleshooting

**Can't connect to app**:
- Ensure both Python and Node servers are running
- Check ports 8000 (Python) and 3000 (Node) are available

**Login fails**:
- Check credentials (admin/admin123)
- Verify session secret is set in .env

**API errors**:
- Ensure Python backend is running
- Check console for proxy errors
- Verify FASTAPI_BASE in .env points to http://127.0.0.1:8000

**Ingestion not working**:
- Check Python backend logs
- Verify API proxy is working
- Check browser console for errors

## 📚 Next Steps

See `MIGRATION_COMPLETE.md` for:
- Detailed migration notes
- Complete file structure
- Extraction guide for remaining modules
- API endpoint documentation

## 🎯 Priority Tasks

1. Extract graph viewer from old main_ui.py
2. Extract query builder from old main_ui.py
3. Test all features end-to-end
4. Remove old HTML code from Python backend

---

**Questions?** Check `MIGRATION_COMPLETE.md` for detailed documentation.
