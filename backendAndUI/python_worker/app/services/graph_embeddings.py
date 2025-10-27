from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

from ..core.settings import settings
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


ENTITY_VECTOR_INDEX = "entity_embedding_idx"
DOCUMENT_VECTOR_INDEX = "document_embedding_idx"
TRIPLET_VECTOR_INDEX = "triplet_embedding_idx"


def _ensure_vector_index(session, name: str, label: str, property: str, dims: int) -> None:
    """Create a vector index if it does not already exist.
    Prefers CREATE VECTOR INDEX syntax, falls back to procedure if needed.
    """
    try:
        existing = session.run("SHOW INDEXES YIELD name WHERE name = $name RETURN name", name=name)
        if existing.single():
            return
        create_cypher = (
            "CREATE VECTOR INDEX " + name +
            f" FOR (n:{label}) ON (n.{property}) "
            "OPTIONS { indexConfig: { 'vector.dimensions': $dims, 'vector.similarity_function': 'cosine' } }"
        )
        session.run(create_cypher, dims=dims)
        logger.info(f"Created vector index {name} on :{label}({property})")
    except Exception as exc:
        try:
            # Fallback to db.index.vector procedure
            session.run(
                "CALL db.index.vector.createNodeIndex($name, $label, $prop, $dims, 'cosine')",
                name=name, label=label, prop=property, dims=dims,
            )
            logger.info(f"Created vector index via procedure {name} on :{label}({property})")
        except Exception as exc2:
            logger.warning(f"Failed to create vector index {name}: {exc2}")


def ensure_vector_indexes() -> None:
    """Ensure required vector indexes exist for Entities, Documents, and Triplets."""
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        _ensure_vector_index(session, ENTITY_VECTOR_INDEX, "Entity", "embedding", settings.openai_embedding_dim)
        _ensure_vector_index(session, DOCUMENT_VECTOR_INDEX, "Document", "embedding", settings.openai_embedding_dim)
        _ensure_vector_index(session, TRIPLET_VECTOR_INDEX, "Triplet", "embedding", settings.openai_embedding_dim)


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Call OpenAI embeddings API for a list of texts."""
    if settings.openai_dry_run or not settings.openai_api_key:
        # Deterministic vectors for dry-run environments, matching configured dimension
        dim = int(getattr(settings, "openai_embedding_dim", 1536) or 1536)
        return [[(hash(t + str(i)) % 1000) / 1000.0 for i in range(dim)] for t in texts]

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.embeddings.create(model=settings.openai_embedding_model, input=texts)
    return [d.embedding for d in resp.data]


def upsert_document_embedding(document_id: str, document_title: str | None, triplets: Iterable[object]) -> None:
    """Compute and store a document-level embedding summarizing the extracted triplets.
    The text is a compact serialization of subject-predicate-object triples.
    """
    snippets: List[str] = []
    for t in list(triplets)[:200]:  # cap for safety
        try:
            s = getattr(t, 'subject', '')
            p = getattr(t, 'predicate', '')
            o = getattr(t, 'object', '')
            otxt = getattr(t, 'original_text', None) or ''
            if otxt:
                otxt = otxt.strip().replace('\n', ' ')
            snippets.append(f"{s} {p} {o}. {otxt}".strip())
        except Exception:
            continue

    doc_text = (document_title or document_id or "") + "\n" + " \n".join(snippets[:200])
    embedding = _embed_texts([doc_text])[0]

    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        session.run(
            "MERGE (d:Document {document_id: $id}) SET d.embedding = $emb, d.embedding_model = $model, d.embedding_updated_at = datetime()",
            id=document_id, emb=embedding, model=settings.openai_embedding_model,
        )
    logger.info(f"Stored document embedding for {document_id}")


def upsert_entity_embeddings_for_document(document_id: str) -> int:
    """Compute embeddings for all Entities linked to the Document via EXTRACTED_FROM.
    Returns the number of entities updated.
    """
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        # Fetch entities for this document
        result = session.run(
            """
            MATCH (e:Entity)-[:EXTRACTED_FROM]->(d:Document {document_id: $id})
            RETURN coalesce(e.id, e.name, elementId(e)) AS eid, e.name AS name, coalesce(e.type, head(labels(e))) AS etype
            """,
            id=document_id,
        )
        rows = list(result)

    if not rows:
        return 0

    texts = [f"{r['name']} ({r['etype']})" if r['etype'] else r['name'] for r in rows]
    vectors = _embed_texts(texts)

    # Write embeddings back in batches
    updated = 0
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        for r, vec in zip(rows, vectors):
            session.run(
                """
                MATCH (e:Entity)
                WHERE coalesce(e.id, e.name, elementId(e)) = $eid
                SET e.embedding = $emb, e.embedding_model = $model, e.embedding_updated_at = datetime()
                """,
                eid=r["eid"], emb=vec, model=settings.openai_embedding_model,
            )
            updated += 1

    logger.info(f"Updated embeddings for {updated} entities from document {document_id}")
    return updated


def ensure_triplet_vector_index() -> None:
    """Create vector index for Triplet node embeddings."""
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        _ensure_vector_index(session, TRIPLET_VECTOR_INDEX, "Triplet", "embedding", settings.openai_embedding_dim)
    logger.info(f"Ensured triplet vector index: {TRIPLET_VECTOR_INDEX}")
