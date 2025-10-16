# Server Restart & Cache Clear Instructions

## The Problem
Your browser is serving **cached old JavaScript** from before the fixes were applied.  
The error line numbers (1839) don't match the actual file (function is at 1856).

## Solution: 3-Step Process

### Step 1: Restart the FastAPI Server

**Stop the server** (Ctrl+C in the terminal where it's running)

**Start it again:**
```bash
cd backendAndUI/python_worker
uvicorn app.main:app --reload --port 8000
```

The `--reload` flag should auto-reload, but a full restart ensures all changes are loaded.

---

### Step 2: Hard Refresh Your Browser

**Clear browser cache for localhost:**

**Chrome/Edge:**
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

**OR:**
- Windows: `Ctrl + Shift + R` or `Ctrl + F5`
- Mac: `Cmd + Shift + R`

**OR (most thorough):**
1. Open DevTools (F12)
2. Go to Application tab
3. Click "Clear storage"
4. Check "Cache storage" and "Cached images and files"
5. Click "Clear site data"

---

### Step 3: Verify the Fixes

After restart and cache clear, you should see:

1. **Documents dropdown works** - No more `docs.map is not a function` error
2. **Schema endpoint works** - Query Builder dropdowns populate with your actual node/relationship types
3. **Longer titles** - Titles can now be up to 500 characters
4. **Console logs** show the fixes:
   ```
   Schema loaded: {node_types: [...], relationship_types: [...]}
   Loaded X node types and Y relationship types
   ```

---

## Check If You're Still Seeing Old Code

**Open browser DevTools (F12) → Console**, then run:
```javascript
// Check if the fix is loaded
fetch('/query/documents').then(r => r.json()).then(data => {
  console.log('API Response:', data);
  console.log('Has documents property:', 'documents' in data);
});
```

**Expected output:**
```javascript
API Response: {documents: [...], page_number: 1}
Has documents property: true
```

If you see `documents: undefined`, the backend didn't restart.  
If you still get `docs.map is not a function`, your browser cache didn't clear.

---

## About Significance Being Null

**This is expected for OLD data!**

Your existing data shows `significance: null` because it was extracted with the **old prompt** that didn't require significance.

**To get significance values:**
1. Delete the old document from Neo4j OR
2. Re-upload the same PDF (it will re-extract with new prompt)

**New extractions will have:**
- `subject_significance`: 1-5
- `object_significance`: 1-5
- `relationship_significance`: 1-5
- Node sizes will adjust automatically
- Sidebar will show stars: ⭐⭐⭐⭐⭐

---

## Testing the Schema Endpoint Directly

**Test in browser or terminal:**
```bash
curl http://localhost:8000/api/pathway/schema
```

**Expected response:**
```json
{
  "node_types": ["Concept", "Device", "Method", "Technology", ...],
  "relationship_types": ["ENABLES", "IMPROVES", "REQUIRES", ...],
  "message": "Schema retrieved successfully: 15 node types, 20 relationship types"
}
```

If you get a 500 error, check the server logs for the detailed error message I added.

---

## Summary

✅ **All fixes are in the code**  
⚠️ **Your server needs restarting**  
⚠️ **Your browser cache needs clearing**  
ℹ️ **Old data won't have significance** (re-ingest to get it)

After restart + cache clear, everything should work!




