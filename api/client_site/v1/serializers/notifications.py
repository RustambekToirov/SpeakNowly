from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageListSerializer(BaseModel):
    """Notification list serializer."""
    id: int
    title: str
    description: Optional[str]
    created_at: datetime
    is_read: bool

class MessageDetailSerializer(BaseModel):
    """Notification detail serializer."""
    id: int
    title: str
    description: Optional[str]
    content: Optional[str]
    created_at: datetime