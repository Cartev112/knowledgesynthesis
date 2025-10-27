"""
Migration script to convert existing relationships to Triplet nodes with embeddings.
Run this after implementing triplet embedding support to backfill existing data.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backendAndUI" / "python_worker"))

from app.core.settings import settings
from app.services.neo4j_client import neo4j_client
from app.services.graph_write import write_triplet_with_embedding
from app.services.graph_embeddings import ensure_triplet_vector_index
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_existing_relationships(batch_size: int = 100, limit: int = None):
    """
    Convert existing relationships to Triplet nodes with embeddings.
    
    Args:
        batch_size: Number of relationships to process per batch
        limit: Maximum number of relationships to migrate (None for all)
    """
    logger.info("Starting migration of existing relationships to Triplet nodes")
    
    # First ensure the vector index exists
    logger.info("Ensuring triplet vector index exists...")
    ensure_triplet_vector_index()
    
    # Fetch all relationships (excluding EXTRACTED_FROM and structural ones)
    cypher = """
    MATCH (s:Entity)-[r]->(o:Entity)
    WHERE type(r) <> 'EXTRACTED_FROM' 
      AND type(r) <> 'ABOUT_SUBJECT'
      AND type(r) <> 'ABOUT_OBJECT'
      AND type(r) <> 'FROM_DOCUMENT'
    RETURN 
      s.name as subject,
      coalesce(s.type, 'Concept') as subject_type,
      type(r) as predicate,
      o.name as object,
      coalesce(o.type, 'Concept') as object_type,
      r.original_text as original_text,
      r.sources as sources,
      r.page_number as page_number,
      r.confidence as confidence,
      r.status as status,
      r.created_by as user_id
    """
    
    if limit:
        cypher += f" LIMIT {limit}"
    else:
        cypher += " LIMIT 10000"  # Safety limit
    
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        results = list(session.run(cypher))
    
    total = len(results)
    logger.info(f"Found {total} relationships to migrate")
    
    if total == 0:
        logger.info("No relationships to migrate")
        return
    
    # Process in batches
    migrated = 0
    failed = 0
    
    for i in range(0, total, batch_size):
        batch = results[i:i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1} ({i + 1}-{min(i + batch_size, total)} of {total})")
        
        for record in batch:
            try:
                # Skip if missing required fields
                if not record["subject"] or not record["object"] or not record["predicate"]:
                    logger.warning(f"Skipping relationship with missing fields: {record}")
                    failed += 1
                    continue
                
                # Handle missing sources
                sources = record["sources"] or []
                if not sources:
                    logger.warning(f"Relationship has no sources: {record['subject']} {record['predicate']} {record['object']}")
                    sources = ["unknown"]
                
                # Convert predicate from relationship type format to readable format
                predicate = record["predicate"].replace("_", " ").lower()
                
                write_triplet_with_embedding(
                    subject=record["subject"],
                    predicate=predicate,
                    object=record["object"],
                    original_text=record["original_text"] or "",
                    sources=sources,
                    page_number=record["page_number"],
                    confidence=record["confidence"] or 1.0,
                    status=record["status"] or "unverified",
                    user_id=record["user_id"],
                    subject_type=record["subject_type"],
                    object_type=record["object_type"]
                )
                
                migrated += 1
                
                if migrated % 50 == 0:
                    logger.info(f"Progress: {migrated}/{total} migrated, {failed} failed")
                    
            except Exception as e:
                logger.error(f"Failed to migrate relationship {i}: {e}")
                logger.error(f"Record: {record}")
                failed += 1
    
    logger.info(f"Migration complete: {migrated} migrated, {failed} failed")
    logger.info(f"Triplet nodes created with embeddings for semantic search")


def verify_migration():
    """Verify that triplet nodes were created successfully."""
    logger.info("Verifying migration...")
    
    cypher = """
    MATCH (t:Triplet)
    RETURN 
      count(t) as total_triplets,
      count(t.embedding) as triplets_with_embeddings,
      collect(DISTINCT t.embedding_model)[0] as embedding_model
    """
    
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        result = session.run(cypher).single()
        
        logger.info(f"Total Triplet nodes: {result['total_triplets']}")
        logger.info(f"Triplets with embeddings: {result['triplets_with_embeddings']}")
        logger.info(f"Embedding model: {result['embedding_model']}")
        
        if result['total_triplets'] == result['triplets_with_embeddings']:
            logger.info("✓ All triplets have embeddings")
        else:
            logger.warning(f"⚠ {result['total_triplets'] - result['triplets_with_embeddings']} triplets missing embeddings")
    
    # Check vector index
    index_cypher = "SHOW VECTOR INDEXES YIELD name, state WHERE name = 'triplet_embedding_idx' RETURN name, state"
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        result = session.run(index_cypher).single()
        if result:
            logger.info(f"✓ Vector index '{result['name']}' exists with state: {result['state']}")
        else:
            logger.warning("⚠ Vector index 'triplet_embedding_idx' not found")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate existing relationships to Triplet nodes with embeddings")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of relationships to migrate")
    parser.add_argument("--verify-only", action="store_true", help="Only verify migration, don't migrate")
    
    args = parser.parse_args()
    
    if args.verify_only:
        verify_migration()
    else:
        migrate_existing_relationships(batch_size=args.batch_size, limit=args.limit)
        verify_migration()
