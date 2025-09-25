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
  if (store.users.find(u => u.username === username)) return
  const hash = bcrypt.hashSync(password, 10)
  store.users.push({ username, password_hash: hash, roles: ['admin'] })
  writeStore(store)
}

export function createUser(username, password) {
  const store = readStore()
  if (store.users.find(u => u.username === username)) throw new Error('User exists')
  const hash = bcrypt.hashSync(password, 10)
  store.users.push({ username, password_hash: hash, roles: ['user'] })
  writeStore(store)
}

export function verifyUser(username, password) {
  const store = readStore()
  const user = store.users.find(u => u.username === username)
  if (!user) return null
  const ok = bcrypt.compareSync(password, user.password_hash)
  return ok ? { username: user.username, roles: user.roles } : null
}







