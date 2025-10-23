"""User data models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model."""
    user_id: str
    email: EmailStr
    first_name: str
    last_name: str
    username: Optional[str] = None
    roles: List[str] = ["user"]
    created_at: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
