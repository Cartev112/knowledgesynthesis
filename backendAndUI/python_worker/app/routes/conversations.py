from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()

# In-memory storage (replace with database in production)
conversations_db = {}


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
def list_conversations():
    """List all conversations, sorted by most recent"""
    conversations = list(conversations_db.values())
    conversations.sort(key=lambda x: x["updated_at"], reverse=True)
    
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
            for c in conversations
        ]
    }


@router.post("/conversations")
def create_conversation(payload: CreateConversationRequest):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    conversation = {
        "id": conversation_id,
        "title": payload.title,
        "created_at": now,
        "updated_at": now,
        "messages": []
    }
    
    conversations_db[conversation_id] = conversation
    return conversation


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    """Get a specific conversation with all messages"""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversations_db[conversation_id]


@router.post("/conversations/{conversation_id}/messages")
def add_message(conversation_id: str, payload: AddMessageRequest):
    """Add a message to a conversation"""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations_db[conversation_id]
    
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
def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversations_db[conversation_id]
    return {"success": True}


@router.put("/conversations/{conversation_id}/title")
def update_title(conversation_id: str, payload: dict):
    """Update conversation title"""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    title = payload.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    conversations_db[conversation_id]["title"] = title
    conversations_db[conversation_id]["updated_at"] = datetime.utcnow().isoformat()
    
    return {"success": True, "title": title}
