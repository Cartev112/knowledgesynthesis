# Authentication Diagnostic

## The 401 Error Explained

You're getting `401 Unauthorized` which means:
- The API endpoint exists
- The request reached the server
- **But the authentication cookie is missing or invalid**

## Possible Causes

### 1. Cookie Domain Mismatch
If your servers are on different Railway domains:
- Node server: `https://node-app.up.railway.app`
- Python backend: `https://knowledgesynthesis.up.railway.app`

Cookies set by Python backend won't be sent to Node server (different domains).

### 2. Not Logged In
You might not be logged in at all. Check:
1. Open browser DevTools → Application → Cookies
2. Look for authentication cookies for `knowledgesynthesis.up.railway.app`
3. If no cookies exist, you need to log in first

### 3. Cookie Settings
The Python backend might be setting cookies with:
- `SameSite=Strict` - Won't work across different origins
- `Secure=True` - Only works on HTTPS
- Wrong domain

## Quick Fixes

### Option 1: Check Login Status
Open browser console and run:
```javascript
fetch('/api/me', { credentials: 'include' })
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

If this returns user data → You're logged in, cookie issue
If this returns 401 → You're not logged in

### Option 2: Login First
Before accessing the workspaces tab:
1. Navigate to the login page
2. Log in with your credentials
3. Then go back to the main app
4. Try accessing workspaces tab

### Option 3: Same Domain (Recommended)
Make both servers accessible from the same domain:

**Using Railway:**
1. Set up a custom domain (e.g., `app.yourdomain.com`)
2. Use path-based routing:
   - `/` → Node server (frontend)
   - `/api/*` → Python backend (API)

This ensures cookies work perfectly.

### Option 4: Proxy Setup (If Different Domains)
If you must use different domains, set up Node server to proxy API calls:

```javascript
// In node-server/server.js
const { createProxyMiddleware } = require('http-proxy-middleware');

app.use('/api', createProxyMiddleware({
  target: 'https://knowledgesynthesis.up.railway.app',
  changeOrigin: true,
  credentials: true,
  onProxyReq: (proxyReq, req) => {
    // Forward all cookies
    if (req.headers.cookie) {
      proxyReq.setHeader('cookie', req.headers.cookie);
    }
  },
  onProxyRes: (proxyRes, req, res) => {
    // Forward set-cookie headers
    const setCookie = proxyRes.headers['set-cookie'];
    if (setCookie) {
      proxyRes.headers['set-cookie'] = setCookie.map(cookie => 
        cookie.replace(/Domain=[^;]+;?/i, '')
      );
    }
  }
}));
```

## Testing Steps

### Step 1: Verify Authentication
```javascript
// In browser console
API.get('/api/me')
  .then(user => console.log('Logged in as:', user))
  .catch(err => console.error('Not logged in:', err))
```

### Step 2: Check Cookies
```javascript
// In browser console
console.log('Cookies:', document.cookie)
```

### Step 3: Test Workspace API
```javascript
// In browser console
API.get('/api/workspaces')
  .then(workspaces => console.log('Workspaces:', workspaces))
  .catch(err => console.error('Error:', err))
```

### Step 4: Test Documents API
```javascript
// In browser console
API.get('/api/documents/available')
  .then(docs => console.log('Documents:', docs))
  .catch(err => console.error('Error:', err))
```

## Current Architecture Issue

```
Browser
  ↓
Node Server (Railway Domain A)
  ↓ API calls
Python Backend (Railway Domain B)
  ↑ Sets cookies for Domain B
  
Browser tries to send cookies from Domain B to Domain B
But request originates from Domain A
→ Cookies not sent → 401 Error
```

## Recommended Solution

**Use Railway's built-in proxy or custom domain:**

1. **Custom Domain + Path Routing:**
   ```
   app.yourdomain.com/          → Node Server
   app.yourdomain.com/api/*     → Python Backend
   ```

2. **Railway Proxy:**
   Configure Railway to route all traffic through one service

3. **Node Proxy (Quickest):**
   Add proxy middleware to Node server (code above)

## Why "Just Remove Auth" Won't Work

Removing authentication would:
- ❌ Expose all user data publicly
- ❌ Allow anyone to modify/delete workspaces
- ❌ Break permission system
- ❌ Create security vulnerabilities

The real issue is cookie/session management, not authentication itself.

## Next Steps

1. **Verify you're logged in** - Run test in console
2. **Check cookie domain** - Look in DevTools
3. **Implement proxy** - If domains are different
4. **Or use custom domain** - Best long-term solution

---

*The authentication system is working correctly. The issue is cookie delivery across domains.*
