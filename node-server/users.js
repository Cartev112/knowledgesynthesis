import bcrypt from 'bcryptjs'
import pool from './db.js'

export async function ensureAdminFromEnv() {
  const username = process.env.LOGIN_USER
  const password = process.env.LOGIN_PASS
  if (!username || !password) return
  
  try {
    // Support legacy username-based admin or email-based
    const email = username.includes('@') ? username : `${username}@admin.local`
    
    // Check if admin user already exists
    const result = await pool.query('SELECT id FROM users WHERE email = $1', [email])
    if (result.rows.length > 0) return
    
    // Create admin user
    const hash = bcrypt.hashSync(password, 10)
    await pool.query(
      'INSERT INTO users (email, first_name, last_name, password_hash, roles) VALUES ($1, $2, $3, $4, $5)',
      [email, 'Admin', 'User', hash, ['admin']]
    )
    console.log(`✓ Admin user created: ${email}`)
  } catch (err) {
    console.error('Error ensuring admin user:', err)
  }
}

export async function createUser(first_name, last_name, email, password) {
  try {
    // Check if user already exists
    const existing = await pool.query('SELECT id FROM users WHERE email = $1', [email])
    if (existing.rows.length > 0) {
      throw new Error('User with this email already exists')
    }
    
    // Create new user
    const hash = bcrypt.hashSync(password, 10)
    await pool.query(
      'INSERT INTO users (email, first_name, last_name, password_hash, roles) VALUES ($1, $2, $3, $4, $5)',
      [email, first_name, last_name, hash, ['user']]
    )
    console.log(`✓ User created: ${email}`)
  } catch (err) {
    console.error('Error creating user:', err)
    throw err
  }
}

export async function verifyUser(email, password) {
  try {
    const result = await pool.query(
      'SELECT email, first_name, last_name, password_hash, roles FROM users WHERE email = $1',
      [email]
    )
    
    if (result.rows.length === 0) return null
    
    const user = result.rows[0]
    const ok = bcrypt.compareSync(password, user.password_hash)
    
    return ok ? {
      user_id: user.email,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      roles: user.roles
    } : null
  } catch (err) {
    console.error('Error verifying user:', err)
    return null
  }
}

export async function getUserByEmail(email) {
  try {
    const result = await pool.query(
      'SELECT email, first_name, last_name, roles FROM users WHERE email = $1',
      [email]
    )
    
    if (result.rows.length === 0) return null
    
    const user = result.rows[0]
    return {
      user_id: user.email,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      roles: user.roles
    }
  } catch (err) {
    console.error('Error getting user by email:', err)
    return null
  }
}








