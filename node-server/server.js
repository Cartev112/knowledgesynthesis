import express from 'express'
import multer from 'multer'
import fs from 'fs'
import path from 'path'
import axios from 'axios'
import dotenv from 'dotenv'
import session from 'express-session'
import FormData from 'form-data'
import { fileURLToPath } from 'url'
import { ensureAdminFromEnv, createUser, verifyUser, getUserByEmail } from './users.js'
import { initializeDatabase } from './db.js'

dotenv.config()

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const port = process.env.PORT || 3000
const fastapiBase = process.env.FASTAPI_BASE || 'http://127.0.0.1:8000'
const sessionSecret = process.env.SESSION_SECRET || 'dev-secret-change-me'
const defaultUser = process.env.LOGIN_USER || 'admin'
const defaultPass = process.env.LOGIN_PASS || 'admin123'

// ensure uploads directory exists
const uploadsDir = path.join(__dirname, 'uploads')
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir, { recursive: true })

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => {
    const safe = Date.now() + '-' + (file.originalname || 'upload.txt')
    cb(null, safe)
  }
})
const upload = multer({ storage })

app.use(express.urlencoded({ extended: true }))
app.use(express.json())
app.use(session({ secret: sessionSecret, resave: false, saveUninitialized: false }))

// Initialize database and admin user
await initializeDatabase()
await ensureAdminFromEnv()

function requireAuth(req, res, next) {
  if (req.session && req.session.user) return next()
  res.redirect('/login')
}

app.get('/login', (req, res) => {
  res.type('html').send(`<!doctype html>
  <html>
  <head>
    <meta charset="utf-8" />
    <title>Login - Knowledge Synthesis Platform</title>
    <style>
      * { box-sizing: border-box; }
      body {
        font-family: system-ui, -apple-system, sans-serif;
        margin: 0;
        padding: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .login-container {
        background: white;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        width: 100%;
        max-width: 400px;
      }
      h1 {
        margin: 0 0 30px 0;
        color: #1f2937;
        font-size: 28px;
        text-align: center;
      }
      form {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      input {
        padding: 12px 16px;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        font-size: 15px;
        transition: border-color 0.2s;
      }
      input:focus {
        outline: none;
        border-color: #667eea;
      }
      button {
        padding: 12px 16px;
        background: #667eea;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }
      button:hover { background: #5568d3; }
      .link {
        margin-top: 20px;
        text-align: center;
        color: #6b7280;
        font-size: 14px;
      }
      .link a {
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
      }
      .link a:hover { text-decoration: underline; }
    </style>
  </head>
  <body>
    <div class="login-container">
      <h1>Knowledge Synthesis</h1>
      <form method="post" action="/login" autocomplete="on">
        <input name="email" type="email" placeholder="Email" required autocomplete="email" />
        <input name="password" type="password" placeholder="Password" required autocomplete="current-password" />
        <button type="submit">Login</button>
      </form>
      <div class="link">Don't have an account? <a href="/signup">Sign up</a></div>
    </div>
  </body>
  </html>`)
})

app.post('/login', async (req, res) => {
  const { email, password } = req.body || {}
  let user = await verifyUser(email, password)
  
  // Fallback to default credentials (support both email and legacy username)
  if (!user && (email === defaultUser || email === `${defaultUser}@admin.local`) && password === defaultPass) {
    user = {
      user_id: 'admin',
      email: email.includes('@') ? email : `${email}@admin.local`,
      first_name: 'Admin',
      last_name: 'User',
      roles: ['admin']
    }
  }
  
  if (user) {
    req.session.user = user
    return res.redirect('/workspaces.html')
  }
  
  res.status(401).type('html').send(`<!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>Login Failed</title>
      <style>
        body { font-family: system-ui; margin: 40px; text-align: center; }
        a { color: #667eea; text-decoration: none; }
        a:hover { text-decoration: underline; }
      </style>
    </head>
    <body>
      <h2>❌ Invalid credentials</h2>
      <p><a href="/login">← Try again</a></p>
    </body>
    </html>`)
})

app.get('/signup', (req, res) => {
  res.type('html').send(`<!doctype html>
  <html>
  <head>
    <meta charset="utf-8" />
    <title>Sign Up - Knowledge Synthesis Platform</title>
    <style>
      * { box-sizing: border-box; }
      body {
        font-family: system-ui, -apple-system, sans-serif;
        margin: 0;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }
      .signup-container {
        background: white;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        width: 100%;
        max-width: 400px;
      }
      h1 {
        margin: 0 0 24px 0;
        font-size: 24px;
        color: #111827;
        text-align: center;
      }
      input {
        width: 100%;
        padding: 12px;
        margin: 8px 0;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
      }
      button {
        width: 100%;
        padding: 12px;
        margin-top: 16px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
      }
      button:hover { opacity: 0.9; }
      .link { text-align: center; margin-top: 16px; font-size: 14px; }
      .link a { color: #667eea; text-decoration: none; }
      .link a:hover { text-decoration: underline; }
    </style>
  </head>
  <body>
    <div class="signup-container">
      <h1>🔬 Create Account</h1>
      <form method="post" action="/signup" autocomplete="on">
        <input name="first_name" placeholder="First Name" required autocomplete="given-name" />
        <input name="last_name" placeholder="Last Name" required autocomplete="family-name" />
        <input name="email" type="email" placeholder="Email" required autocomplete="email" />
        <input name="password" type="password" placeholder="Password" required autocomplete="new-password" />
        <button type="submit">Create Account</button>
      </form>
      <div class="link">Already have an account? <a href="/login">Login</a></div>
    </div>
  </body>
  </html>`)
})

app.post('/signup', async (req, res) => {
  const { first_name, last_name, email, password, username } = req.body || {}
  try {
    // Support both old (username) and new (email) formats
    if (email && first_name && last_name && password) {
      await createUser(first_name, last_name, email, password)
      res.redirect('/login')
    } else if (username && password) {
      // Legacy support
      await createUser('User', 'Name', username, password)
      res.redirect('/login')
    } else {
      throw new Error('Missing required fields')
    }
  } catch (e) {
    res.status(400).type('html').send(`<p>${e.message}. <a href="/signup">Try again</a></p>`)
  }
})

app.post('/logout', (req, res) => {
  req.session?.destroy(() => res.redirect('/login'))
})

// API endpoints for Python backend integration
app.post('/api/login', async (req, res) => {
  const { email, password } = req.body || {}
  const user = await verifyUser(email, password)
  if (user) {
    req.session.user = user
    return res.json({ success: true, user })
  }
  res.status(401).json({ error: 'Invalid credentials' })
})

app.post('/api/signup', async (req, res) => {
  const { first_name, last_name, email, password } = req.body || {}
  try {
    if (!first_name || !last_name || !email || !password) throw new Error('Missing required fields')
    await createUser(first_name, last_name, email, password)
    res.status(201).json({ success: true, message: 'Account created' })
  } catch (e) {
    res.status(400).json({ error: e.message })
  }
})

app.get('/api/me', requireAuth, (req, res) => {
  res.json({ user: req.session.user })
})

app.post('/api/logout', (req, res) => {
  req.session?.destroy(() => res.json({ success: true }))
})

// Serve static files from public directory
app.use('/static', express.static(path.join(__dirname, 'public')))

// Also serve CSS, JS, and other assets directly (for workspaces page)
app.use('/css', express.static(path.join(__dirname, 'public', 'css')))
app.use('/js', express.static(path.join(__dirname, 'public', 'js')))

// Proxy /query requests to Python backend (no /api prefix)
app.use('/query', (req, res, next) => {
  const url = `${fastapiBase}/query${req.url}`
  console.log(`Proxying ${req.method} /query${req.url} to ${url}`)
  
  axios({
    method: req.method,
    url,
    data: req.body,
    headers: {
      'Content-Type': req.headers['content-type'] || 'application/json'
    }
  })
  .then(response => {
    res.status(response.status).json(response.data)
  })
  .catch(err => {
    console.error(`Proxy error for /query${req.url}:`, err.message)
    const status = err.response?.status || 500
    const data = err.response?.data || { detail: err.message }
    res.status(status).json(data)
  })
})

// Special handler for PDF upload with file forwarding
app.post('/api/ingest/pdf_async', requireAuth, upload.single('file'), async (req, res) => {
  try {
    const form = new FormData()
    
    // Add the file
    if (req.file) {
      form.append('file', fs.createReadStream(req.file.path), {
        filename: req.file.originalname,
        contentType: 'application/pdf'
      })
    }
    
    // Add all other form fields
    Object.keys(req.body).forEach(key => {
      form.append(key, req.body[key])
    })
    
    const url = `${fastapiBase}/api/ingest/pdf_async`
    console.log(`Forwarding PDF upload to ${url}`)
    
    const response = await axios.post(url, form, {
      headers: form.getHeaders()
    })
    
    // Clean up uploaded file
    if (req.file) {
      fs.unlinkSync(req.file.path)
    }
    
    res.status(response.status).json(response.data)
  } catch (err) {
    console.error('PDF upload proxy error:', err.message)
    console.error('Error details:', err.response?.data)
    
    // Clean up uploaded file on error
    if (req.file) {
      try { fs.unlinkSync(req.file.path) } catch {}
    }
    
    const status = err.response?.status || 500
    const data = err.response?.data || { detail: err.message }
    res.status(status).json(data)
  }
})

// Discovery UI route (MUST be before proxies to avoid conflict)
app.get('/discovery-ui', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'discovery.html'))
})

// Review UI route (MUST be before /review proxy to avoid conflict)
app.get('/review-ui', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'review.html'))
})

// Proxy review API endpoints to Python backend (NO /api prefix!)
app.use('/review', (req, res) => {
  const url = `${fastapiBase}/review${req.url}`
  console.log(`Proxying ${req.method} /review${req.url} to ${url}`)
  
  axios({
    method: req.method,
    url,
    data: req.body,
    headers: {
      'Content-Type': req.headers['content-type'] || 'application/json'
    }
  })
  .then(response => {
    res.status(response.status).json(response.data)
  })
  .catch(err => {
    console.error(`Proxy error for /review${req.url}:`, err.message)
    const status = err.response?.status || 500
    const data = err.response?.data || { detail: err.message }
    res.status(status).json(data)
  })
})

// Workspace API endpoints (handled by Node.js, wrapping Python backend)
app.get('/api/workspaces', requireAuth, async (req, res) => {
  try {
    const user = req.session.user
    console.log('Session user data:', JSON.stringify(user, null, 2))
    const response = await axios.get(`${fastapiBase}/api/workspaces`, {
      headers: { 
        'X-User-ID': user.user_id || user.email,
        'X-User-Email': user.email,
        'X-User-First-Name': user.first_name || '',
        'X-User-Last-Name': user.last_name || '',
        'X-User-Roles': (user.roles || ['user']).join(',')
      }
    })
    res.json(response.data)
  } catch (err) {
    console.error('Workspace list error:', err.message)
    res.status(err.response?.status || 500).json(err.response?.data || { detail: err.message })
  }
})

app.get('/api/workspaces/:id', requireAuth, async (req, res) => {
  try {
    const user = req.session.user
    const response = await axios.get(`${fastapiBase}/api/workspaces/${req.params.id}`, {
      headers: { 
        'X-User-ID': user.user_id || user.email,
        'X-User-Email': user.email,
        'X-User-First-Name': user.first_name || '',
        'X-User-Last-Name': user.last_name || '',
        'X-User-Roles': (user.roles || ['user']).join(',')
      }
    })
    res.json(response.data)
  } catch (err) {
    console.error('Workspace get error:', err.message)
    res.status(err.response?.status || 500).json(err.response?.data || { detail: err.message })
  }
})

app.post('/api/workspaces', requireAuth, async (req, res) => {
  try {
    const user = req.session.user
    const response = await axios.post(`${fastapiBase}/api/workspaces`, req.body, {
      headers: { 
        'Content-Type': 'application/json',
        'X-User-ID': user.user_id || user.email,
        'X-User-Email': user.email,
        'X-User-First-Name': user.first_name || '',
        'X-User-Last-Name': user.last_name || '',
        'X-User-Roles': (user.roles || ['user']).join(',')
      }
    })
    res.status(201).json(response.data)
  } catch (err) {
    console.error('Workspace create error:', err.message)
    res.status(err.response?.status || 500).json(err.response?.data || { detail: err.message })
  }
})

app.put('/api/workspaces/:id', requireAuth, async (req, res) => {
  try {
    const user = req.session.user
    const response = await axios.put(`${fastapiBase}/api/workspaces/${req.params.id}`, req.body, {
      headers: { 
        'Content-Type': 'application/json',
        'X-User-ID': user.user_id || user.email,
        'X-User-Email': user.email,
        'X-User-First-Name': user.first_name || '',
        'X-User-Last-Name': user.last_name || '',
        'X-User-Roles': (user.roles || ['user']).join(',')
      }
    })
    res.json(response.data)
  } catch (err) {
    console.error('Workspace update error:', err.message)
    res.status(err.response?.status || 500).json(err.response?.data || { detail: err.message })
  }
})

app.get('/api/workspaces/:id/documents', requireAuth, async (req, res) => {
  try {
    const user = req.session.user
    const response = await axios.get(`${fastapiBase}/api/workspaces/${req.params.id}/documents`, {
      headers: { 
        'X-User-ID': user.user_id || user.email,
        'X-User-Email': user.email,
        'X-User-First-Name': user.first_name || '',
        'X-User-Last-Name': user.last_name || '',
        'X-User-Roles': (user.roles || ['user']).join(',')
      }
    })
    res.json(response.data)
  } catch (err) {
    console.error('Workspace documents error:', err.message)
    res.status(err.response?.status || 500).json(err.response?.data || { detail: err.message })
  }
})

app.get('/api/workspaces/:id/entities', requireAuth, async (req, res) => {
  try {
    const user = req.session.user
    const response = await axios.get(`${fastapiBase}/api/workspaces/${req.params.id}/entities`, {
      headers: { 
        'X-User-ID': user.user_id || user.email,
        'X-User-Email': user.email,
        'X-User-First-Name': user.first_name || '',
        'X-User-Last-Name': user.last_name || '',
        'X-User-Roles': (user.roles || ['user']).join(',')
      }
    })
    res.json(response.data)
  } catch (err) {
    console.error('Workspace entities error:', err.message)
    res.status(err.response?.status || 500).json(err.response?.data || { detail: err.message })
  }
})

app.get('/api/workspaces/:id/relationships', requireAuth, async (req, res) => {
  try {
    const user = req.session.user
    const response = await axios.get(`${fastapiBase}/api/workspaces/${req.params.id}/relationships`, {
      headers: { 
        'X-User-ID': user.user_id || user.email,
        'X-User-Email': user.email,
        'X-User-First-Name': user.first_name || '',
        'X-User-Last-Name': user.last_name || '',
        'X-User-Roles': (user.roles || ['user']).join(',')
      }
    })
    res.json(response.data)
  } catch (err) {
    console.error('Workspace relationships error:', err.message)
    res.status(err.response?.status || 500).json(err.response?.data || { detail: err.message })
  }
})

app.post('/api/sync-user', requireAuth, async (req, res) => {
  try {
    const user = req.session.user
    const response = await axios.post(`${fastapiBase}/api/sync-user`, {}, {
      headers: { 
        'X-User-ID': user.user_id || user.email,
        'X-User-Email': user.email,
        'X-User-First-Name': user.first_name || '',
        'X-User-Last-Name': user.last_name || '',
        'X-User-Roles': (user.roles || ['user']).join(',')
      }
    })
    res.json(response.data)
  } catch (err) {
    console.error('User sync error:', err.message)
    res.status(err.response?.status || 500).json(err.response?.data || { detail: err.message })
  }
})

// Proxy API requests to Python FastAPI backend (but NOT /api/me, /api/login, /api/logout, /api/ingest/pdf_async, /api/workspaces)
app.use('/api', (req, res, next) => {
  // Skip proxy for Node-handled endpoints
  if (req.path === '/me' || req.path === '/login' || req.path === '/logout' || req.path === '/ingest/pdf_async' || req.path.startsWith('/workspaces')) {
    return next()
  }
  
  // Proxy to Python backend - keep /api prefix in the URL
  const url = `${fastapiBase}/api${req.url}`
  console.log(`Proxying ${req.method} /api${req.url} to ${url}`)
  
  axios({
    method: req.method,
    url,
    data: req.body,
    headers: {
      'Content-Type': req.headers['content-type'] || 'application/json'
    }
  })
  .then(response => {
    res.status(response.status).json(response.data)
  })
  .catch(err => {
    console.error(`Proxy error for /api${req.url}:`, err.message)
    console.error('Error details:', err.response?.data)
    const status = err.response?.status || 500
    const data = err.response?.data || { detail: err.message }
    res.status(status).json(data)
  })
})

// Workspaces landing page
app.get('/workspaces.html', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'workspaces.html'))
})

// Main app route - serve index.html
app.get('/', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'))
})

app.get('/app', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'))
})

app.post('/upload', requireAuth, upload.single('file'), async (req, res) => {
  try {
    let text = (req.body && req.body.text) || ''
    if (!text && req.file) {
      text = fs.readFileSync(req.file.path, 'utf-8')
    }
    if (!text) return res.status(400).json({ error: 'No text provided' })

    const response = await axios.post(`${fastapiBase}/ingest/text`, {
      text,
      document_id: `node-${Date.now()}`,
      document_title: req.file ? req.file.originalname : 'Node Upload'
    })
    res.json(response.data)
  } catch (err) {
    res.status(500).json({ error: err?.response?.data || err.message })
  }
})

app.listen(port, () => {
  console.log(`Node server listening on http://127.0.0.1:${port}`)
})


