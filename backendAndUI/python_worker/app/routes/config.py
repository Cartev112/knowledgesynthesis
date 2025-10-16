from fastapi import APIRouter

from ..core.settings import settings, reload_settings


router = APIRouter()


@router.get("")
def read_config():
    return {
        "neo4j_uri": settings.neo4j_uri,
        "neo4j_username": settings.neo4j_username,
        "neo4j_database": settings.neo4j_database,
        "openai_model": settings.openai_model,
        "openai_dry_run": settings.openai_dry_run,
    }


@router.post("/reload")
def reload_config():
    new_settings = reload_settings()
    return {
        "neo4j_uri": new_settings.neo4j_uri,
        "neo4j_username": new_settings.neo4j_username,
        "neo4j_database": new_settings.neo4j_database,
        "openai_model": new_settings.openai_model,
        "openai_dry_run": new_settings.openai_dry_run,
    }


