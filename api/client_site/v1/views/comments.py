from fastapi import APIRouter
from typing import List

from ..serializers.comments import CommentListSerializer, CommentListUserSerializer
from models import Comment

router = APIRouter()

@router.get("/", response_model=List[CommentListSerializer])
async def list_comments():
    """Return all comments for main page (read-only, no updates)."""
    comments = await Comment.all().select_related("user").order_by("-id")
    return [
        CommentListSerializer(
            id=comment.id,
            text=comment.text,
            user=CommentListUserSerializer(
                id=comment.user.id,
                first_name=comment.user.first_name,
                last_name=comment.user.last_name,
                photo=comment.user.photo,
            ),
            rate=comment.rate,
            status=comment.status,
        )
        for comment in comments
    ]