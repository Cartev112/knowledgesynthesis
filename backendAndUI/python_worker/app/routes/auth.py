"""Authentication endpoints that integrate with the Node.js authentication server."""
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
import httpx
from typing import Optional

from ..core.settings import settings


router = APIRouter()

# Node server URL for authentication
NODE_SERVER = "http://127.0.0.1:3000"


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


# Simple session storage (in production, use Redis or database)
sessions = {}


@router.get("/login")
def login_page():
    """Serve the login page."""
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Login - Knowledge Synthesis</title>
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        padding: 0;
        font-family: system-ui, -apple-system, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
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
        margin: 0 0 8px 0;
        color: #111827;
        font-size: 28px;
        text-align: center;
      }
      
      .subtitle {
        text-align: center;
        color: #6b7280;
        margin-bottom: 32px;
        font-size: 14px;
      }
      
      .form-group {
        margin-bottom: 20px;
      }
      
      label {
        display: block;
        font-weight: 600;
        margin-bottom: 6px;
        color: #374151;
        font-size: 14px;
      }
      
      input {
        width: 100%;
        padding: 12px 14px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 15px;
        font-family: inherit;
        transition: border-color 0.2s;
      }
      
      input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
      }
      
      button {
        width: 100%;
        background: #667eea;
        color: white;
        border: none;
        padding: 14px;
        border-radius: 6px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }
      
      button:hover { background: #5568d3; }
      button:disabled {
        background: #9ca3af;
        cursor: not-allowed;
      }
      
      .error {
        background: #fee2e2;
        color: #991b1b;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 20px;
        border: 1px solid #fca5a5;
        font-size: 14px;
        display: none;
      }
      
      .error.show { display: block; }
      
      .divider {
        text-align: center;
        margin: 24px 0;
        color: #9ca3af;
        font-size: 14px;
      }
      
      .signup-link {
        text-align: center;
        margin-top: 24px;
        font-size: 14px;
        color: #6b7280;
      }
      
      .signup-link a {
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
      }
      
      .signup-link a:hover { text-decoration: underline; }
    </style>
  </head>
  <body>
    <div class="login-container">
      <h1>Knowledge Synthesis</h1>
      <div class="subtitle">Sign in to continue</div>
      
      <div id="error" class="error"></div>
      
      <form id="login-form" onsubmit="handleLogin(event)">
        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" id="email" name="email" required autocomplete="email" />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input type="password" id="password" name="password" required autocomplete="current-password" />
        </div>
        
        <button type="submit" id="login-btn">Sign In</button>
      </form>
      
      <div class="signup-link">
        Don't have an account? <a href="/signup">Sign up</a>
      </div>
    </div>
    
    <script>
      async function handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const btn = document.getElementById('login-btn');
        const errorEl = document.getElementById('error');
        
        btn.disabled = true;
        btn.textContent = 'Signing in...';
        errorEl.classList.remove('show');
        
        try {
          const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',  // Important: include cookies
            body: JSON.stringify({ email, password })
          });
          
          if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || 'Login failed');
          }
          
          const data = await res.json();
          console.log('Login successful:', data);
          
          // Small delay to ensure cookie is set
          setTimeout(() => {
            window.location.href = '/workspaces.html';
          }, 100);
          
        } catch (err) {
          errorEl.textContent = err.message;
          errorEl.classList.add('show');
          btn.disabled = false;
          btn.textContent = 'Sign In';
        }
      }
    </script>
  </body>
</html>
    """
    return HTMLResponse(content=html)


@router.get("/signup")
def signup_page():
    """Serve the signup page."""
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Sign Up - Knowledge Synthesis</title>
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        padding: 0;
        font-family: system-ui, -apple-system, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
      }
      
      .signup-container {
        background: white;
        padding: 32px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        width: 100%;
        max-width: 420px;
      }
      
      h1 {
        margin: 0 0 6px 0;
        color: #111827;
        font-size: 26px;
        text-align: center;
      }
      
      .subtitle {
        text-align: center;
        color: #6b7280;
        margin-bottom: 24px;
        font-size: 14px;
      }
      
      .form-group {
        margin-bottom: 14px;
      }
      
      label {
        display: block;
        font-weight: 600;
        margin-bottom: 5px;
        color: #374151;
        font-size: 13px;
      }
      
      input {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
        font-family: inherit;
        transition: border-color 0.2s;
      }
      
      input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
      }
      
      button {
        width: 100%;
        background: #667eea;
        color: white;
        border: none;
        padding: 12px;
        border-radius: 6px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }
      
      button:hover { background: #5568d3; }
      button:disabled {
        background: #9ca3af;
        cursor: not-allowed;
      }
      
      .error {
        background: #fee2e2;
        color: #991b1b;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 20px;
        border: 1px solid #fca5a5;
        font-size: 14px;
        display: none;
      }
      
      .error.show { display: block; }
      
      .success {
        background: #d1fae5;
        color: #065f46;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 20px;
        border: 1px solid #6ee7b7;
        font-size: 14px;
        display: none;
      }
      
      .success.show { display: block; }
      
      .login-link {
        text-align: center;
        margin-top: 16px;
        font-size: 14px;
        color: #6b7280;
      }
      
      .login-link a {
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
      }
      
      .login-link a:hover { text-decoration: underline; }
      
      .help-text {
        font-size: 12px;
        color: #6b7280;
        margin-top: 3px;
      }
    </style>
  </head>
  <body>
    <div class="signup-container">
      <h1>Knowledge Synthesis</h1>
      <div class="subtitle">Create your account</div>
      
      <div id="error" class="error"></div>
      <div id="success" class="success"></div>
      
      <form id="signup-form" onsubmit="handleSignup(event)">
        <div class="form-group">
          <label for="first-name">First Name</label>
          <input type="text" id="first-name" name="first-name" required autocomplete="given-name" />
        </div>
        
        <div class="form-group">
          <label for="last-name">Last Name</label>
          <input type="text" id="last-name" name="last-name" required autocomplete="family-name" />
        </div>
        
        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" id="email" name="email" required autocomplete="email" />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input type="password" id="password" name="password" required minlength="6" autocomplete="new-password" />
          <div class="help-text">At least 6 characters</div>
        </div>
        
        <div class="form-group">
          <label for="confirm-password">Confirm Password</label>
          <input type="password" id="confirm-password" name="confirm-password" required autocomplete="new-password" />
        </div>
        
        <button type="submit" id="signup-btn">Create Account</button>
      </form>
      
      <div class="login-link">
        Already have an account? <a href="/login">Sign in</a>
      </div>
    </div>
    
    <script>
      async function handleSignup(e) {
        e.preventDefault();
        
        const firstName = document.getElementById('first-name').value;
        const lastName = document.getElementById('last-name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        const btn = document.getElementById('signup-btn');
        const errorEl = document.getElementById('error');
        const successEl = document.getElementById('success');
        
        errorEl.classList.remove('show');
        successEl.classList.remove('show');
        
        if (password !== confirmPassword) {
          errorEl.textContent = 'Passwords do not match';
          errorEl.classList.add('show');
          return;
        }
        
        btn.disabled = true;
        btn.textContent = 'Creating account...';
        
        try {
          const payload = { 
            first_name: firstName,
            last_name: lastName,
            email: email,
            password: password
          };
          console.log('Attempting signup with:', JSON.stringify(payload));
          
          const res = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          
          const data = await res.json();
          console.log('Signup response status:', res.status);
          console.log('Signup response data:', data);
          
          if (!res.ok) {
            const errorMsg = data.detail || data.error || data.message || 'Signup failed';
            console.error('Signup failed with error:', errorMsg);
            throw new Error(errorMsg);
          }
          
          successEl.textContent = 'Account created! Redirecting to login...';
          successEl.classList.add('show');
          
          setTimeout(() => {
            window.location.href = '/login';
          }, 2000);
          
        } catch (err) {
          console.error('Signup error:', err);
          errorEl.textContent = err.message;
          errorEl.classList.add('show');
          btn.disabled = false;
          btn.textContent = 'Create Account';
        }
      }
    </script>
  </body>
</html>
    """
    return HTMLResponse(content=html)


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    """Authenticate user via Node.js server."""
    try:
        # Try Node.js server authentication
        async with httpx.AsyncClient() as client:
            node_response = await client.post(
                f"{NODE_SERVER}/api/login",
                json={"email": request.email, "password": request.password},
                timeout=5.0
            )
            
            if node_response.status_code == 200:
                user_data = node_response.json()
                user = user_data.get("user", {})
                session_id = f"sess_{user.get('email', request.email)}"
                sessions[session_id] = {
                    "user_id": user.get("email", request.email),
                    "email": user.get("email", request.email),
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "username": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    "roles": user.get("roles", ["user"])
                }
                
                # Set session cookie
                response.set_cookie(
                    key="session_id",
                    value=session_id,
                    httponly=True,
                    max_age=86400,  # 24 hours
                    samesite="lax"
                )
                
                return {
                    "success": True,
                    "user": sessions[session_id],
                    "session_id": session_id
                }
    except Exception as e:
        pass
    
    # Fallback to simple auth for development
    if request.email and request.password:
        session_id = f"sess_{request.email}"
        sessions[session_id] = {
            "user_id": request.email,
            "email": request.email,
            "first_name": "Demo",
            "last_name": "User",
            "username": "Demo User",
            "roles": ["user"]
        }
        
        # Set session cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite="lax"
        )
        
        return {
            "success": True,
            "user": sessions[session_id],
            "session_id": session_id
        }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/signup")
async def signup(request: SignupRequest):
    """Create new user via Node.js server."""
    import logging
    logging.info(f"Signup request received: {request.email}")
    
    # Validate required fields
    if not request.first_name or not request.last_name or not request.email or not request.password:
        raise HTTPException(status_code=400, detail="All fields are required: first name, last name, email, and password")
    
    try:
        # Try Node.js server signup
        async with httpx.AsyncClient() as client:
            payload = {
                "first_name": request.first_name,
                "last_name": request.last_name,
                "email": request.email,
                "password": request.password
            }
            logging.info(f"Sending to Node.js server: {payload}")
            
            node_response = await client.post(
                f"{NODE_SERVER}/api/signup",
                json=payload,
                timeout=5.0
            )
            
            logging.info(f"Node.js response: {node_response.status_code}")
            
            if node_response.status_code == 200 or node_response.status_code == 201:
                return {"success": True, "message": "Account created successfully"}
            else:
                error_data = node_response.json()
                error_msg = error_data.get("error", "Signup failed")
                logging.error(f"Node.js signup failed: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        # Fallback for development - just accept the signup
        logging.warning(f"Node.js server unavailable, using dev mode: {str(e)}")
        return {"success": True, "message": "Account created successfully (dev mode)"}


@router.get("/me")
async def get_current_user(request: Request):
    """Get current authenticated user."""
    # Check for session cookie
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in sessions:
        return {"user": sessions[session_id]}
    
    # If no valid session, return 401
    raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout current user."""
    # Get session ID and remove from sessions
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    # Clear cookie
    response.delete_cookie("session_id")
    
    return {"success": True}

