import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import bcrypt from 'bcryptjs'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const storePath = path.join(__dirname, 'users.json')

function readStore() {
  if (!fs.existsSync(storePath)) return { users: [] }
  try { return JSON.parse(fs.readFileSync(storePath, 'utf-8')) } catch { return { users: [] } }
}

function writeStore(data) {
  fs.writeFileSync(storePath, JSON.stringify(data, null, 2))
}

export function ensureAdminFromEnv() {
  const username = process.env.LOGIN_USER
  const password = process.env.LOGIN_PASS
  if (!username || !password) return
  const store = readStore()
  // Support legacy username-based admin or email-based
  const email = username.includes('@') ? username : `${username}@admin.local`
  if (store.users.find(u => u.email === email || u.username === username)) return
  const hash = bcrypt.hashSync(password, 10)
  store.users.push({ 
    email,
    first_name: 'Admin',
    last_name: 'User',
    password_hash: hash,
    roles: ['admin']
  })
  writeStore(store)
}

export function createUser(first_name, last_name, email, password) {
  const store = readStore()
  if (store.users.find(u => u.email === email)) throw new Error('User with this email already exists')
  const hash = bcrypt.hashSync(password, 10)
  store.users.push({ 
    first_name,
    last_name,
    email,
    password_hash: hash,
    roles: ['user']
  })
  writeStore(store)
}

export function verifyUser(email, password) {
  const store = readStore()
  const user = store.users.find(u => u.email === email)
  if (!user) return null
  const ok = bcrypt.compareSync(password, user.password_hash)
  return ok ? { 
    email: user.email,
    first_name: user.first_name,
    last_name: user.last_name,
    roles: user.roles
  } : null
}

export function getUserByEmail(email) {
  const store = readStore()
  const user = store.users.find(u => u.email === email)
  if (!user) return null
  return {
    email: user.email,
    first_name: user.first_name,
    last_name: user.last_name,
    roles: user.roles
  }
}








