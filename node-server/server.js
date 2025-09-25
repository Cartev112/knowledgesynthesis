import express from 'express'
import multer from 'multer'
import fs from 'fs'
import path from 'path'
import axios from 'axios'
import dotenv from 'dotenv'
import session from 'express-session'
import { fileURLToPath } from 'url'
import { ensureAdminFromEnv, createUser, verifyUser } from './users.js'

dotenv.config()

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const port = process.env.NODE_PORT || 3000
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
ensureAdminFromEnv()

function requireAuth(req, res, next) {
  if (req.session && req.session.user) return next()
  res.redirect('/login')
}

app.get('/login', (req, res) => {
  res.type('html').send(`<!doctype html>
  <meta charset="utf-8" />
  <title>Login</title>
  <style>body{font-family:system-ui;margin:40px;}input{padding:8px;margin:6px 0;width:260px;}button{padding:8px 12px;}</style>
  <form method="post" action="/login">
    <div><input name="username" placeholder="Username" /></div>
    <div><input name="password" type="password" placeholder="Password" /></div>
    <button type="submit">Login</button>
  </form>`)
})

app.post('/login', (req, res) => {
  const { username, password } = req.body || {}
  const user = verifyUser(username, password) || (username === defaultUser && password === defaultPass ? { username } : null)
  if (user) { req.session.user = user; return res.redirect('/') }
  res.status(401).type('html').send('<p>Invalid credentials. <a href="/login">Try again</a></p>')
})

app.get('/signup', (req, res) => {
  res.type('html').send(`<!doctype html>
  <meta charset="utf-8" />
  <title>Sign Up</title>
  <style>body{font-family:system-ui;margin:40px;}input{padding:8px;margin:6px 0;width:260px;}button{padding:8px 12px;}</style>
  <form method="post" action="/signup">
    <div><input name="username" placeholder="Choose username" /></div>
    <div><input name="password" type="password" placeholder="Choose password" /></div>
    <button type="submit">Create account</button>
  </form>`)
})

app.post('/signup', (req, res) => {
  const { username, password } = req.body || {}
  try {
    if (!username || !password) throw new Error('Missing fields')
    createUser(username, password)
    res.redirect('/login')
  } catch (e) {
    res.status(400).type('html').send(`<p>${e.message}. <a href="/signup">Try again</a></p>`)
  }
})

app.post('/logout', (req, res) => {
  req.session?.destroy(() => res.redirect('/login'))
})

app.get('/', requireAuth, (req, res) => {
  res.type('html').send(`<!doctype html>
  <meta charset="utf-8" />
  <title>Upload Text</title>
  <form action="/upload" method="post" enctype="multipart/form-data">
    <div><input type="file" name="file" accept=".txt" /></div>
    <div><textarea name="text" rows="8" cols="80" placeholder="or paste text here..."></textarea></div>
    <button type="submit">Submit</button>
  </form>
  <form action="/logout" method="post" style="margin-top:10px"><button type="submit">Logout</button></form>`)
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


