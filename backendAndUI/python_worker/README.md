Python Worker (FastAPI)

Run locally
1) Create and activate a virtual environment.
2) Install deps: `pip install -r requirements.txt`
3) Ensure `.env` or `config/dev.env` has NEO4J_* values.
4) Start server: `uvicorn backend.python_worker.app.main:app --reload`.

Endpoints
- GET `/` -> `{ "status": "ok" }`
- GET `/health` -> `{ "status": "healthy" }`
- GET `/db/ping` -> `{ "connected": true|false }`



