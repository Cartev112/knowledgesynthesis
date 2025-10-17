# Known Issues & Fixes

## Fixed Issues ✅

### 1. Login/Signup Styling
**Issue**: Login and signup pages had minimal styling  
**Fix**: Added proper styling matching the main app design with gradient background  
**Status**: ✅ FIXED

### 2. User Details Not Saving
**Issue**: User session didn't include all user fields (first_name, last_name, email)  
**Fix**: Updated login handler to store complete user object with all fields  
**Status**: ✅ FIXED

### 3. API Proxy Routing
**Issue**: `/api/me`, `/api/login`, `/api/logout` were being proxied to Python instead of handled by Node  
**Fix**: Added route filtering to skip proxy for Node-handled endpoints  
**Status**: ✅ FIXED

## Current Issues ⚠️

### 4. Viewer Tab Not Working
**Issue**: Graph viewer shows blank/error because it's a placeholder  
**Expected**: This is intentional - the viewer module needs to be extracted from main_ui.py  
**Workaround**: None - requires completing the migration  
**Priority**: HIGH  
**Next Steps**: Extract Cytoscape code from main_ui.py lines 1900-2700

### 5. `/query/documents` Endpoint Error
**Issue**: Python backend returns 500 error on `/api/query/documents`  
**Possible Causes**:
- Database connection issue
- Missing user context in request
- Backend not fully initialized

**Debug Steps**:
1. Check Python backend logs for detailed error
2. Verify database is accessible
3. Check if endpoint expects user_id parameter

**Temporary Workaround**: Check Python logs with:
```bash
# In python_worker directory
uvicorn app.main:app --reload
```

## Testing Checklist

- [x] Login page styling
- [x] Signup page styling  
- [x] User session persistence
- [x] API proxy routing
- [x] Ingestion tab loads
- [ ] Viewer tab works (pending implementation)
- [ ] Query builder tab works (pending implementation)
- [ ] Document upload works
- [ ] Graph rendering works

## Next Actions

1. **Immediate**: Check Python backend logs for `/query/documents` error
2. **Short-term**: Extract and implement graph viewer module
3. **Medium-term**: Extract and implement query builder module
4. **Long-term**: Full end-to-end testing

## How to Report Issues

When reporting issues, include:
1. Browser console errors (F12 → Console)
2. Network tab errors (F12 → Network)
3. Python backend logs
4. Node server logs
5. Steps to reproduce
