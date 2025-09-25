from fastapi import APIRouter, HTTPException

from ..services.neo4j_client import neo4j_client
from ..core.settings import settings


router = APIRouter()


@router.get("/ping")
def ping_db():
    try:
        ok = neo4j_client.verify_connection()
        return {"connected": ok}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/restart_fulltext")
def restart_fulltext_index():
    drop_cypher = "DROP INDEX entity_search IF EXISTS"
    create_cypher = "CREATE FULLTEXT INDEX entity_search FOR (n:Entity|Document) ON EACH [n.name, n.title]"
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            try:
                session.run(drop_cypher)
            except Exception as e:
                # This might fail if the index is already in the process of being dropped.
                # We can ignore this, as the create command will either succeed or fail with a clear message.
                print(f"Info: could not drop index 'entity_search'. It may not have existed or was being dropped. Error: {e}")
            session.run(create_cypher)
            return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/reset")
def reset_database():
    """Wipe the database and re-initialize the schema."""
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            # Wipe all data
            session.run("MATCH (n) DETACH DELETE n")

            # Load and apply the init.cypher schema
            with open("db/neo4j/init.cypher", "r") as f:
                init_cypher = f.read()
                # Split commands and run them one by one
                for statement in init_cypher.split(';'):
                    if statement.strip():
                        session.run(statement)
            
            return {"status": "database reset successfully"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to reset database: {exc}")


@router.get("/debug/info")
def debug_info():
    import sys
    import openai
    import platform

    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "openai_version": openai.__version__,
        "sys_path": sys.path,
    }


