Neo4j local setup (Windows)

Prerequisites
- Install Java is not required for Neo4j Desktop. For Neo4j Server, ensure a recent Java (if prompted).

Option A: Neo4j Desktop (recommended for development)
1) Download and install Neo4j Desktop from `https://neo4j.com/download/`.
2) Create a new Project, then create a new Local DBMS.
3) Choose Neo4j 5.x, set a password (remember it), and start the DBMS.
4) Ensure Bolt is enabled on port 7687 (default). Database name is typically `neo4j`.
5) Optional: Install APOC plugin from the Plugins tab if you plan to use it later.

Option B: Neo4j Community Server (service)
1) Download Windows zip from `https://neo4j.com/download-center/#community`.
2) Extract, then edit `conf/neo4j.conf`:
   - dbms.default_listen_address=0.0.0.0
   - dbms.connector.bolt.enabled=true
   - dbms.connector.bolt.listen_address=:7687
3) Start via `bin/neo4j.bat console` and set the initial password when prompted.

Project configuration
1) Copy `config/example.env` to either `.env` (project root) or `config/dev.env`.
2) Update values to match your local DB:
   - NEO4J_URI=neo4j://localhost:7687
   - NEO4J_USERNAME=neo4j
   - NEO4J_PASSWORD=<your_password>
   - NEO4J_DATABASE=neo4j

Initialize constraints and indexes
1) Create and activate your Python environment.
2) Install dependencies:
   - `pip install -r requirements.txt`
3) Ensure your Neo4j DB is running.
4) Run the initializer:
   - `python scripts/apply_neo4j_init.py`
5) You should see confirmation that constraints/indexes were applied.

Troubleshooting
- Authentication errors: confirm username/password and that the DB is running.
- Connection refused: ensure Bolt is on 7687 and not blocked by firewall.
- Constraint syntax errors: confirm you are on Neo4j 5.x.


