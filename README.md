Knowledge Synthesis MVP

Quick start
1) Python 3.11+ and Neo4j Desktop installed
2) Create venv and install deps
   - py -m venv .venv
   - .\.venv\Scripts\python.exe -m pip install -r requirements.txt
3) Configure .env
   - NEO4J_URI=bolt://127.0.0.1:7687
   - NEO4J_USERNAME=neo4j
   - NEO4J_PASSWORD=<your_password>
   - NEO4J_DATABASE=neo4j
   - OPENAI_DRY_RUN=true
4) Initialize schema
   - python scripts/apply_neo4j_init.py
5) Run API
   - .\.venv\Scripts\python.exe -m uvicorn backend.python_worker.app.main:app --reload

Endpoints
- GET /health
- GET /db/ping
- GET /preprocess/run
- GET /extract/run
- GET /ingest/run
- GET /query?name=...
- GET /config, POST /config/reload
- GET /ui (minimal graph viewer)







