import os
from pathlib import Path
from typing import List

from neo4j import GraphDatabase
from dotenv import load_dotenv


def load_environment() -> None:
    # Load from .env in project root if present
    load_dotenv(dotenv_path=Path(".env"), override=False)
    # Load from config/dev.env if present (does not override existing env)
    load_dotenv(dotenv_path=Path("config/dev.env"), override=False)


def read_cypher_statements(file_path: Path) -> List[str]:
    text = file_path.read_text(encoding="utf-8")
    # Split on semicolons while preserving statements that may span lines
    statements = [stmt.strip() for stmt in text.split(";")]
    return [s for s in statements if s]


def apply_init(uri: str, username: str, password: str, database: str, statements: List[str]) -> None:
    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        with driver.session(database=database) as session:
            def run_all(tx):
                for stmt in statements:
                    tx.run(stmt)

            session.execute_write(run_all)
    finally:
        driver.close()


def main() -> None:
    load_environment()

    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "changeme")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    init_file = Path("db/neo4j/init.cypher")
    if not init_file.exists():
        raise FileNotFoundError(f"Missing schema file: {init_file}")

    statements = read_cypher_statements(init_file)
    if not statements:
        print("No statements found to apply.")
        return

    apply_init(uri, username, password, database, statements)
    print(f"Applied {len(statements)} Cypher statements to database '{database}'.")


if __name__ == "__main__":
    main()



