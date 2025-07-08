from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.analyses import (
    ListeningAnalyse,
    ReadingAnalyse,
    SpeakingAnalyse,
    WritingAnalyse,
)
from models.tests import Reading, Writing, Speaking
from ..serializers.analyses import (
    ListeningAnalyseSerializer,
    ReadingAnalyseSerializer,
    SpeakingAnalyseSerializer,
    WritingAnalyseSerializer,
)
from utils.auth import active_user

def timedelta_to_str(td):
    if td is None:
        return None
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

router = APIRouter()

@router.get("/listening/{session_id}/", response_model=ListeningAnalyseSerializer)
async def get_listening_analysis(session_id: int, user=Depends(active_user)):
    try:
        session_id = int(session_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="session_id must be an integer")
    analyse = await ListeningAnalyse.get_or_none(session_id=session_id, user_id=user.id)
    if not analyse:
        raise HTTPException(status_code=404, detail="Listening analysis not found")
    data = analyse.__dict__.copy()
    data["duration"] = timedelta_to_str(data.get("duration"))
    return data

@router.get("/reading/{session_id}/", response_model=List[ReadingAnalyseSerializer])
async def get_reading_analysis(session_id: int, user=Depends(active_user)):
    try:
        session_id = int(session_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="session_id must be an integer")
    reading = await Reading.get_or_none(id=session_id)
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    passages = await reading.passages.all()
    passage_ids = [p.id for p in passages]
    analyses = await ReadingAnalyse.filter(passage_id__in=passage_ids, user_id=user.id).all()
    if not analyses:
        raise HTTPException(status_code=404, detail="No analyses found for this reading session")
    result = []
    for analyse in analyses:
        data = analyse.__dict__.copy()
        data["duration"] = timedelta_to_str(data.get("duration"))
        result.append(data)
    return result

@router.get("/speaking/{session_id}/", response_model=SpeakingAnalyseSerializer)
async def get_speaking_analysis(session_id: int, user=Depends(active_user)):
    try:
        session_id = int(session_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="session_id must be an integer")
    analyse = await SpeakingAnalyse.get_or_none(speaking_id=session_id)
    if not analyse:
        raise HTTPException(status_code=404, detail="Speaking analysis not found")
    data = analyse.__dict__.copy()
    data["duration"] = timedelta_to_str(data.get("duration"))
    return data

@router.get("/writing/{session_id}/", response_model=WritingAnalyseSerializer)
async def get_writing_analysis(session_id: int, user=Depends(active_user)):
    try:
        session_id = int(session_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="session_id must be an integer")
    analyse = await WritingAnalyse.get_or_none(writing_id=session_id)
    if not analyse:
        raise HTTPException(status_code=404, detail="Writing analysis not found")
    data = analyse.__dict__.copy()
    data["duration"] = timedelta_to_str(data.get("duration"))
    return data