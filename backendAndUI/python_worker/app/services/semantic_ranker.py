"""
Semantic Ranking Service
Uses embeddings to rank documents by relevance to a query or existing knowledge graph.
"""

import logging
from typing import List, Dict, Optional
import numpy as np
from openai import OpenAI

from ..core.settings import settings

logger = logging.getLogger(__name__)


class SemanticRanker:
    """Rank documents using semantic similarity via embeddings."""
    
    def __init__(self):
        self.client = None
        if not settings.openai_dry_run:
            self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "text-embedding-3-small"  # Cheaper, faster embedding model
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if settings.openai_dry_run:
            # Return dummy embedding for testing
            return [0.1] * 1536
        
        try:
            # Truncate text to avoid token limits (8191 tokens for embedding model)
            text = text[:8000]
            
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score between -1 and 1
        """
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    def rank_papers(
        self,
        papers: List[Dict],
        query: str,
        context: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Rank papers by semantic relevance to query and optional context.
        
        Args:
            papers: List of paper dictionaries
            query: Search query
            
        Returns:
            Papers sorted by relevance with relevance_score added
        """
        if not papers:
            return []
        
        try:
            # Prepare all texts for batch embedding
            texts = [query]  # Query first
            for paper in papers:
                paper_text = f"{paper.get('title', '')} {paper.get('abstract', '')[:500]}"  # Limit abstract length
                texts.append(paper_text)
            
            # Get all embeddings in ONE batch call (much faster!)
            if settings.openai_dry_run:
                # Dry run mode - return dummy scores
                for i, paper in enumerate(papers):
                    paper['relevance_score'] = 1.0 - (i * 0.01)  # Decreasing scores
                logger.info(f"Ranked {len(papers)} papers (dry run mode)")
                return papers
            
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            
            # Extract embeddings
            query_embedding = np.array(response.data[0].embedding)
            paper_embeddings = [np.array(response.data[i+1].embedding) for i in range(len(papers))]
            
            # Calculate similarities
            for i, paper in enumerate(papers):
                similarity = self.cosine_similarity(query_embedding, paper_embeddings[i])
                paper['relevance_score'] = float(similarity)
            
            # Sort by relevance score (highest first)
            papers.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"Ranked {len(papers)} papers by semantic relevance")
            return papers
            
        except Exception as e:
            logger.error(f"Semantic ranking failed: {e}")
            # Return unranked papers
            for paper in papers:
                paper['relevance_score'] = 0.5
            return papers
    
    def rank_by_graph_context(
        self,
        papers: List[Dict],
        entities: List[str],
        relationships: List[str],
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Rank papers by relevance to existing knowledge graph entities/relationships.
        
        Args:
            papers: List of paper dictionaries
            entities: List of entity names from graph
            relationships: List of relationship descriptions from graph
            top_k: Return only top K results
            
        Returns:
            Papers sorted by relevance to graph context
        """
        # Build context from graph
        context_parts = []
        if entities:
            context_parts.append(f"Key entities: {', '.join(entities[:20])}")
        if relationships:
            context_parts.append(f"Key relationships: {', '.join(relationships[:10])}")
        
        context = " | ".join(context_parts)
        
        # Use the context as the query
        return self.rank_papers(papers, query=context, top_k=top_k)
    
    def filter_by_threshold(
        self,
        papers: List[Dict],
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Filter papers by minimum relevance score.
        
        Args:
            papers: Papers with 'relevance_score' field
            threshold: Minimum score (0-1)
            
        Returns:
            Filtered papers
        """
        filtered = [p for p in papers if p.get('relevance_score', 0) >= threshold]
        logger.info(f"Filtered to {len(filtered)} papers with score >= {threshold}")
        return filtered
