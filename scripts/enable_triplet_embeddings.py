"""
Enable triplet embeddings for new ingestions.
This script creates the vector index and provides instructions for updating the ingestion pipeline.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backendAndUI" / "python_worker"))

from app.services.graph_embeddings import ensure_triplet_vector_index
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def enable_triplet_embeddings():
    """Create the triplet vector index to enable triplet embeddings."""
    logger.info("Enabling triplet embeddings...")
    
    try:
        ensure_triplet_vector_index()
        logger.info("✓ Triplet vector index created successfully")
        logger.info("✓ Triplet embeddings are now enabled")
        
        print("\n" + "="*60)
        print("TRIPLET EMBEDDINGS ENABLED")
        print("="*60)
        print("\nNext steps:")
        print("1. The triplet_embedding_idx vector index has been created")
        print("2. New triplets will automatically get embeddings when ingested")
        print("3. To migrate existing data, run:")
        print("   python scripts/migrate_to_triplet_embeddings.py")
        print("\n4. Add Aura Agent tools (see docs/AURA_AGENT_CONFIGURATION.md):")
        print("   - triplet_similarity_search (Similarity Search)")
        print("   - get_triplet_details (Cypher Template)")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to enable triplet embeddings: {e}")
        raise


if __name__ == "__main__":
    enable_triplet_embeddings()
