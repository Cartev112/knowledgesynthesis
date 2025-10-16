import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def load_environment() -> None:
    # Load dev defaults first, then let .env override
    # Look for .env in the project root (4 levels up from this file: core -> app -> python_worker -> backend -> root)
    project_root = Path(__file__).parent.parent.parent.parent.parent
    load_dotenv(dotenv_path=project_root / "config/dev.env", override=True)
    load_dotenv(dotenv_path=project_root / ".env", override=True)


class Settings:
    def __init__(self) -> None:
        load_environment()
        self.neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_username: str = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password: str = os.getenv("NEO4J_PASSWORD", "changeme")
        self.neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")

        # OpenAI
        self.openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_dry_run: bool = os.getenv("OPENAI_DRY_RUN", "false").lower() == "true"


settings = Settings()


def reload_settings() -> Settings:
    global settings
    settings = Settings()
    return settings


