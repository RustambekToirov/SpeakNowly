from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from datetime import timedelta, datetime, timezone
from tortoise.expressions import Q
import random

from ...serializers.tests.top import TopUserIELTSSerializer
from models import User, TokenTransaction
from utils.ielts_score import IELTSScoreCalculator

router = APIRouter()

MOCK_IMAGES = [
    "http://dummyimage.com/163x100.png/5fa2dd/ffffff",
    "http://dummyimage.com/169x100.png/cc0000/ffffff",
    "http://dummyimage.com/212x100.png/dddddd/000000",
    "http://dummyimage.com/121x100.png/ff4444/ffffff",
    "http://dummyimage.com/238x100.png/dddddd/000000",
    "http://dummyimage.com/148x100.png/ff4444/ffffff",
    "http://dummyimage.com/206x100.png/dddddd/000000",
    "http://dummyimage.com/161x100.png/dddddd/000000",
    "http://dummyimage.com/213x100.png/ff4444/ffffff",
    "http://dummyimage.com/134x100.png/5fa2dd/ffffff",
]

MOCK_NAMES = [
    "Darcy", "Robb", "Aile", "Uriel", "Elsinore", "Christopher", "Carolann", "Louie", "Moina", "Berne",
    "Renault", "Kristofer", "Darren", "Willy", "Omar", "Karney", "Vivia", "Mabelle", "Nara", "Josiah"
]

@router.get(
    "/ielts/",
    response_model=List[TopUserIELTSSerializer],
    status_code=status.HTTP_200_OK,
    summary="Get top users by IELTS score"
)
async def get_top_users_ielts(
    period: Optional[str] = Query(None, description="Period: week, month, or all"),
    test_type: Optional[str] = Query(None, description="Test type (READING_ENG, etc.)"),
):
    """
    Get top 100 users by IELTS score for a given period and test type,
    """
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = None

    filters = Q()
    if start_date:
        filters &= Q(created_at__gte=start_date)
    if test_type:
        filters &= Q(transaction_type=test_type.upper())

    transactions = await TokenTransaction.filter(filters).select_related("user")
    user_ids = set(t.user_id for t in transactions)
    users = await User.filter(id__in=user_ids)

    user_scores = {user: await IELTSScoreCalculator.calculate(user) for user in users}
    sorted_users = sorted(user_scores.items(), key=lambda item: item[1], reverse=True)

    top_users = []
    for user, score in sorted_users[:100]:
        reg_date = None
        if hasattr(user, "created_at") and user.created_at:
            reg_date = user.created_at.strftime("%d.%m.%Y")
        top_users.append(
            TopUserIELTSSerializer(
                first_name=user.first_name,
                last_name=user.last_name,
                ielts_score=score,
                data=reg_date,
                image=getattr(user, "photo", None) if hasattr(user, "photo") else None,
            )
        )

    return top_users



@router.get(
    "/ielts/mock3/",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get mock top 3 users"
)
async def mock_top3_users_ielts():
    """
    Get mock top 3 users (for demo/testing).
    """
    return [
        {
            "id": 1,
            "full_name": "Darcy",
            "data": "14.03.2025",
            "ball": 21,
            "image": "http://dummyimage.com/163x100.png/5fa2dd/ffffff",
        },
        {
            "id": 2,
            "full_name": "Robb",
            "data": "17.11.2024",
            "ball": 53,
            "image": "http://dummyimage.com/169x100.png/cc0000/ffffff",
        },
        {
            "id": 3,
            "full_name": "Aile",
            "data": "28.01.2025",
            "ball": 9,
            "image": "http://dummyimage.com/212x100.png/dddddd/000000",
        },
    ]


@router.get(
    "/ielts/mock100/",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get mock top 100 users"
)
async def mock_top_users_ielts():
    """
    Get mock top 100 users (randomly generated).
    """
    data = []
    today = datetime.today()
    for i in range(1, 101):
        name = random.choice(MOCK_NAMES)
        full_name = name
        date = (today - timedelta(days=random.randint(0, 365))).strftime("%d.%m.%Y")
        ball = random.randint(1, 100)
        image = random.choice(MOCK_IMAGES)
        data.append({
            "id": i,
            "full_name": full_name,
            "data": date,
            "ball": ball,
            "image": image,
        })
    return data