from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CommentListUserSerializer(BaseModel):
    """User info for comment."""
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    photo: Optional[str]

class CommentListSerializer(BaseModel):
    """List comment serializer."""
    id: int
    text: str
    user: CommentListUserSerializer
    rate: float
    status: str

class CommentDetailSerializer(BaseModel):
    """Detailed comment serializer."""
    id: int
    text: str
    user: CommentListUserSerializer
    rate: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    message: Optional[str] = None

class CommentCreateSerializer(BaseModel):
    """Create comment serializer."""
    text: str = Field(..., max_length=500)
    rate: float = Field(..., ge=1, le=5)