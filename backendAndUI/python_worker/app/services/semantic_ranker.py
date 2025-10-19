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
            papers: List of paper dictionaries with 'title' and 'abstract'
            query: User's search query
            context: Optional context from knowledge graph
            top_k: Return only top K results (None = return all)
            
        Returns:
            Papers sorted by relevance with 'relevance_score' added
        """
        if not papers:
            return []
        
        # Combine query and context for reference embedding
        reference_text = query
        if context:
            reference_text = f"{query}\n\nContext: {context}"
        
        # Get reference embedding
        reference_embedding = self.get_embedding(reference_text)
        if reference_embedding is None:
            logger.warning("Failed to get reference embedding, returning unranked papers")
            return papers
        
        # Calculate similarity for each paper
        ranked_papers = []
        for paper in papers:
            # Combine title and abstract for paper embedding
            paper_text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
            
            paper_embedding = self.get_embedding(paper_text)
            if paper_embedding is None:
                # If embedding fails, assign low score
                similarity = 0.0
            else:
                similarity = self.cosine_similarity(reference_embedding, paper_embedding)
            
            # Add relevance score to paper
            paper_with_score = paper.copy()
            paper_with_score['relevance_score'] = round(similarity, 4)
            ranked_papers.append(paper_with_score)
        
        # Sort by relevance (highest first)
        ranked_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top K if specified
        if top_k is not None:
            ranked_papers = ranked_papers[:top_k]
        
        logger.info(f"Ranked {len(ranked_papers)} papers by semantic relevance")
        return ranked_papers
    
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
