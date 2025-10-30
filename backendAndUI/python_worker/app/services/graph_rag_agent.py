from __future__ import annotations

import logging
from typing import List, Literal, Tuple

from ..core.settings import settings
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

Scope = Literal["entity", "document", "hybrid"]


def _embed_query(text: str) -> List[float]:
    if settings.openai_dry_run or not settings.openai_api_key:
        dim = int(getattr(settings, "openai_embedding_dim", 1536) or 1536)
        return [(hash(text + str(i)) % 1000) / 1000.0 for i in range(dim)]
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.embeddings.create(model=settings.openai_embedding_model, input=[text])
    return resp.data[0].embedding


def _vector_query_entities(qvec: List[float], k: int) -> List[dict]:
    cypher = (
        "CALL db.index.vector.queryNodes('entity_embedding_idx', $vec, $k) YIELD node, score\n"
        "OPTIONAL MATCH (node)-[:IS_A]->(type:Type)\n"
        "WITH node, score, collect(DISTINCT type.name) AS type_names\n"
        "WITH node, score, CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END AS types\n"
        "RETURN {id: coalesce(node.id, node.name, elementId(node)), name: coalesce(node.name, node.id), types: types, type: types[0], score: score} AS item\n"
        "ORDER BY score DESC LIMIT $k"
    )
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        return [r["item"] for r in session.run(cypher, vec=qvec, k=k)]


def _vector_query_documents(qvec: List[float], k: int) -> List[dict]:
    cypher = (
        "CALL db.index.vector.queryNodes('document_embedding_idx', $vec, $k) YIELD node, score\n"
        "RETURN {id: node.document_id, title: coalesce(node.title, node.document_id), score: score} AS item\n"
        "ORDER BY score DESC LIMIT $k"
    )
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        return [r["item"] for r in session.run(cypher, vec=qvec, k=k)]


def _fetch_context_for_entities(entity_ids: List[str], per_entity_limit: int = 20) -> Tuple[str, List[dict]]:
    """Return textual context and sources for a set of entity ids."""
    if not entity_ids:
        return "", []
    cypher = (
        "MATCH (e:Entity) WHERE coalesce(e.id, e.name, elementId(e)) IN $ids\n"
        "OPTIONAL MATCH (e)-[r]-(n:Entity)\n"
        "OPTIONAL MATCH (doc:Document) WHERE doc.document_id IN r.sources\n"
        "WITH e, r, n, collect(DISTINCT {id: doc.document_id, title: coalesce(doc.title, doc.document_id), page: r.page_number})[0..3] AS docs\n"
        "OPTIONAL MATCH (e)-[:IS_A]->(type:Type)\n"
        "WITH e, r, docs, collect(DISTINCT type.name) AS type_names\n"
        "RETURN coalesce(e.id, e.name, elementId(e)) AS eid,\n"
        "       e.name AS ename,\n"
        "       CASE WHEN size(type_names) = 0 THEN ['Concept'] ELSE type_names END AS types,\n"
        "       collect(DISTINCT {s: coalesce(startNode(r).name, ''), p: toLower(type(r)), o: coalesce(endNode(r).name, ''), text: r.original_text, docs: docs})[0..$lim] AS triples"
    )
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        data = list(session.run(cypher, ids=entity_ids, lim=per_entity_limit))
    lines: List[str] = []
    sources: List[dict] = []
    for row in data:
        ename = row["ename"]
        types = row.get("types") or []
        type_label = ", ".join(types) if types else "Concept"
        lines.append(f"[ENTITY] {ename} ({type_label})")
        for t in row["triples"]:
            s = t.get("s") or ""
            o = t.get("o") or ""
            p = t.get("p") or "relates_to"
            text = (t.get("text") or "").strip().replace("\n", " ")
            citation = ""
            ds = t.get("docs") or []
            if ds:
                d0 = ds[0]
                citation = f" [source: {d0.get('title')} p.{d0.get('page')}]"
                # track for response payload
                for d in ds:
                    sources.append({"document_id": d.get("id"), "title": d.get("title"), "page": d.get("page")})
            if text:
                lines.append(f"- {s} {p} {o}. Evidence: {text}.{citation}")
            else:
                lines.append(f"- {s} {p} {o}.{citation}")
        lines.append("")
    return "\n".join(lines), sources


def _fetch_context_for_documents(doc_ids: List[str], per_doc_limit: int = 50) -> Tuple[str, List[dict]]:
    if not doc_ids:
        return "", []
    cypher = (
        "MATCH (d:Document) WHERE d.document_id IN $ids\n"
        "OPTIONAL MATCH (s:Entity)-[r]->(o:Entity) WHERE d.document_id IN r.sources\n"
        "WITH d, collect({s: s.name, p: toLower(type(r)), o: o.name, text: r.original_text, page: r.page_number})[0..$lim] AS triples\n"
        "RETURN d.document_id AS id, coalesce(d.title, d.document_id) AS title, triples"
    )
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        data = list(session.run(cypher, ids=doc_ids, lim=per_doc_limit))
    lines: List[str] = []
    sources: List[dict] = []
    for row in data:
        title = row["title"]
        lines.append(f"[DOCUMENT] {title}")
        for t in row["triples"]:
            s = t.get("s") or ""
            p = t.get("p") or "relates_to"
            o = t.get("o") or ""
            page = t.get("page")
            text = (t.get("text") or "").strip().replace("\n", " ")
            cite = f" [p.{page}]" if page else ""
            if text:
                lines.append(f"- {s} {p} {o}. Evidence: {text}.{cite}")
            else:
                lines.append(f"- {s} {p} {o}.{cite}")
            sources.append({"document_id": row["id"], "title": title, "page": page})
        lines.append("")
    return "\n".join(lines), sources


def _llm_answer(question: str, context: str) -> str:
    if settings.openai_dry_run or not settings.openai_api_key:
        return "[DRY RUN] This is a placeholder answer generated without calling OpenAI."
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    system = (
        "You are a GraphRAG agent. Answer the user's question using ONLY the provided graph context. "
        "Cite evidence by referencing document titles and page numbers in square brackets. "
        "If the context is insufficient, say so and suggest what would help. Keep the answer concise."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Question: {question}\n\nGraph Context:\n{context}"},
    ]
    resp = client.chat.completions.create(model=settings.openai_model, messages=messages, temperature=0.1)
    return resp.choices[0].message.content.strip()


def ask_graphrag(question: str, k: int = 8, scope: Scope = "hybrid") -> dict:
    """Run a GraphRAG query over Neo4j embeddings and answer with LLM.
    Returns answer, retrieved entities/documents, and raw context summary.
    """
    qvec = _embed_query(question)

    entities: List[dict] = []
    documents: List[dict] = []

    if scope in ("entity", "hybrid"):
        try:
            entities = _vector_query_entities(qvec, k)
        except Exception as exc:
            logger.warning(f"Entity vector query failed: {exc}")
            entities = []
    if scope in ("document", "hybrid"):
        try:
            documents = _vector_query_documents(qvec, k)
        except Exception as exc:
            logger.warning(f"Document vector query failed: {exc}")
            documents = []

    context_parts: List[str] = []
    sources: List[dict] = []

    if entities:
        eid_list = [e["id"] for e in entities]
        ctx, src = _fetch_context_for_entities(eid_list, per_entity_limit=20)
        context_parts.append(ctx)
        sources.extend(src)

    if documents:
        did_list = [d["id"] for d in documents]
        ctx, src = _fetch_context_for_documents(did_list, per_doc_limit=60)
        context_parts.append(ctx)
        sources.extend(src)

    context_text = "\n\n".join([c for c in context_parts if c.strip()])
    answer = _llm_answer(question, context_text) if context_text.strip() else "No relevant context found to answer the question."

    return {
        "question": question,
        "scope": scope,
        "k": k,
        "entities": entities,
        "documents": documents,
        "sources": sources[:50],
        "context_chars": len(context_text),
        "answer": answer,
    }
