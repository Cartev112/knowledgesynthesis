from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from ..services.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/relationships", tags=["comments"])


class CommentCreate(BaseModel):
    text: str
    author: str


class Comment(BaseModel):
    id: str
    text: str
    author: str
    created_at: datetime


@router.post("/{relationship_id}/comments", response_model=Comment)
async def add_comment(relationship_id: str, comment: CommentCreate):
    """Add a comment to a relationship"""
    try:
        def work(tx):
            # Store relationship reference on the comment node (relationships cannot connect to relationships)
            query = """
            MATCH ()-[r]->()
            WHERE elementId(r) = $rel_id
            CREATE (c:Comment {
                text: $text,
                author: $author,
                created_at: datetime(),
                rel_id: $rel_id
            })
            RETURN elementId(c) as id, c.text as text, c.author as author, c.created_at as created_at
            """
            result = tx.run(query, rel_id=relationship_id, text=comment.text, author=comment.author)
            return result.single()
        
        record = neo4j_client.execute_write(work)
        
        if not record:
            raise HTTPException(status_code=404, detail="Relationship not found")
        
        return Comment(
            id=record["id"],
            text=record["text"],
            author=record["author"],
            created_at=record["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{relationship_id}/comments", response_model=List[Comment])
async def get_comments(relationship_id: str, skip: int = 0, limit: int = 10):
    """Get comments for a relationship with pagination"""
    try:
        def work(tx):
            # Fetch comments by stored rel_id property
            query = """
            MATCH (c:Comment)
            WHERE c.rel_id = $rel_id
            RETURN elementId(c) as id, c.text as text, c.author as author, c.created_at as created_at
            ORDER BY c.created_at DESC
            SKIP $skip
            LIMIT $limit
            """
            result = tx.run(query, rel_id=relationship_id, skip=skip, limit=limit)
            return list(result)
        
        records = neo4j_client.execute_write(work)
        
        comments = []
        for record in records:
            comments.append(Comment(
                id=record["id"],
                text=record["text"],
                author=record["author"],
                created_at=record["created_at"]
            ))
        
        return comments
        
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{relationship_id}/comments/{comment_id}")
async def delete_comment(relationship_id: str, comment_id: str):
    """Delete a comment"""
    try:
        def work(tx):
            query = """
            MATCH (c:Comment)
            WHERE elementId(c) = $comment_id
            DETACH DELETE c
            RETURN count(c) as deleted
            """
            result = tx.run(query, comment_id=comment_id)
            return result.single()
        
        record = neo4j_client.execute_write(work)
        
        if not record or record["deleted"] == 0:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        return {"message": "Comment deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
