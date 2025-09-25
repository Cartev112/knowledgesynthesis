from __future__ import annotations

import logging

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable

from ..core.settings import settings


class Neo4jClient:
    def __init__(self) -> None:
        self._driver: Driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )

    def verify_connection(self) -> bool:
        try:
            with self._driver.session(database=settings.neo4j_database) as session:
                result = session.run("RETURN 1 AS ok")
                record = result.single()
                return bool(record and record.get("ok") == 1)
        except ServiceUnavailable as e:
            logging.error(f"Could not connect to neo4j: {e}")
            return False

    def execute_write(self, fn):
        with self._driver.session(database=settings.neo4j_database) as session:
            return session.execute_write(fn)

    def close(self) -> None:
        self._driver.close()


neo4j_client = Neo4jClient()


