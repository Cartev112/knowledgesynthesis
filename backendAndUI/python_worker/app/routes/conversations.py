from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage (replace with database in production)
conversations_db = {}

# Import sessions from auth module
from .auth import sessions


def get_current_user_from_request(request: Request) -> str:
    """Get current user from session cookie."""
    session_id = request.cookies.get("session_id")
    
    logger.info(f"Session ID from cookie: {session_id}")
    logger.info(f"Available sessions: {list(sessions.keys())}")
    
    if not session_id or session_id not in sessions:
        # For development: allow anonymous access
        logger.warning("No valid session found, using 'anonymous' user")
        return "anonymous"
        # For production: uncomment this line
        # raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_data = sessions[session_id]
    username = user_data.get("username", "anonymous")
    logger.info(f"Authenticated user: {username}")
    return username


class Message(BaseModel):
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = {}


class Conversation(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Message]


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"


class AddMessageRequest(BaseModel):
    role: str
    content: str
    metadata: Optional[dict] = {}


@router.get("/conversations")
def list_conversations(request: Request):
    """List all conversations for current user, sorted by most recent"""
    username = get_current_user_from_request(request)
    
    # Filter conversations by user
    user_conversations = [c for c in conversations_db.values() if c.get("user_id") == username]
    user_conversations.sort(key=lambda x: x["updated_at"], reverse=True)
    
    # Return summary without full messages
    return {
        "conversations": [
            {
                "id": c["id"],
                "title": c["title"],
                "created_at": c["created_at"],
                "updated_at": c["updated_at"],
                "message_count": len(c["messages"])
            }
            for c in user_conversations
        ]
    }


@router.post("/conversations")
def create_conversation(request: Request, payload: CreateConversationRequest):
    """Create a new conversation for current user"""
    username = get_current_user_from_request(request)
    
    conversation_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    conversation = {
        "id": conversation_id,
        "user_id": username,
        "title": payload.title,
        "created_at": now,
        "updated_at": now,
        "messages": []
    }
    
    conversations_db[conversation_id] = conversation
    return conversation


@router.get("/conversations/{conversation_id}")
def get_conversation(request: Request, conversation_id: str):
    """Get a specific conversation with all messages"""
    username = get_current_user_from_request(request)
    
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations_db[conversation_id]
    
    # Verify user owns this conversation
    if conversation.get("user_id") != username:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return conversation


@router.post("/conversations/{conversation_id}/messages")
def add_message(request: Request, conversation_id: str, payload: AddMessageRequest):
    """Add a message to a conversation"""
    username = get_current_user_from_request(request)
    
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations_db[conversation_id]
    
    # Verify user owns this conversation
    if conversation.get("user_id") != username:
        raise HTTPException(status_code=403, detail="Access denied")
    
    message = {
        "role": payload.role,
        "content": payload.content,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": payload.metadata or {}
    }
    
    conversation["messages"].append(message)
    conversation["updated_at"] = datetime.utcnow().isoformat()
    
    # Auto-generate title from first user message if still "New Conversation"
    if conversation["title"] == "New Conversation" and payload.role == "user":
        # Use first 50 chars of message as title
        conversation["title"] = payload.content[:50] + ("..." if len(payload.content) > 50 else "")
    
    return message


@router.delete("/conversations/{conversation_id}")
def delete_conversation(request: Request, conversation_id: str):
    """Delete a conversation"""
    username = get_current_user_from_request(request)
    
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations_db[conversation_id]
    
    # Verify user owns this conversation
    if conversation.get("user_id") != username:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del conversations_db[conversation_id]
    return {"success": True}


@router.put("/conversations/{conversation_id}/title")
def update_title(request: Request, conversation_id: str, payload: dict):
    """Update conversation title"""
    username = get_current_user_from_request(request)
    
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations_db[conversation_id]
    
    # Verify user owns this conversation
    if conversation.get("user_id") != username:
        raise HTTPException(status_code=403, detail="Access denied")
    
    title = payload.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    conversation["title"] = title
    conversation["updated_at"] = datetime.utcnow().isoformat()
    
    return {"success": True, "title": title}
