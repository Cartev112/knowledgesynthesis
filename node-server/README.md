Node server (Phase 2 MVP)

Setup
1) cd node-server
2) npm install
3) Copy .env.example to .env and adjust FASTAPI_BASE if needed
4) npm run dev

Usage
- Open http://127.0.0.1:3000 and upload a .txt file or paste text.
- Server forwards text to FastAPI /ingest/text and returns the result.

Auth
- Default credentials (override in .env):
  - LOGIN_USER=admin
  - LOGIN_PASS=admin123
  - SESSION_SECRET=change-this
- Login at /login, logout via POST /logout.
- Signup at /signup (file-based users.json with bcrypt hashes).


