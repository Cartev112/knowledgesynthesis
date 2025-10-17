# Node Server Frontend Reorganization

## New Directory Structure

```
node-server/
├── server.js (updated)
├── users.js (existing)
├── package.json (existing)
├── uploads/ (existing)
├── public/
│   ├── index.html
│   ├── css/
│   │   ├── base.css
│   │   ├── ingestion.css
│   │   ├── viewing.css
│   │   ├── query-builder.css
│   │   └── modals.css
│   ├── js/
│   │   ├── main.js
│   │   ├── auth.js
│   │   ├── state.js
│   │   ├── ingestion/
│   │   │   └── ingestion.js
│   │   ├── viewing/
│   │   │   ├── graph-viewer.js
│   │   │   ├── cytoscape-manager.js
│   │   │   ├── index-panel.js
│   │   │   └── modals.js
│   │   ├── query-builder/
│   │   │   └── query-builder.js
│   │   └── utils/
│   │       ├── api.js
│   │       └── helpers.js
│   └── assets/
│       └── (any images/fonts)
└── README.md
```

## Key Changes

1. **Node server serves static files** from `/public`
2. **Python backend** only provides API endpoints (no UI)
3. **All frontend code** lives in `node-server/public/`
4. **Node proxies API calls** to Python FastAPI backend