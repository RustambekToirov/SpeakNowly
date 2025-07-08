from fastapi import APIRouter
from .history import router as history_router
from .top import router as top_router
from .listening import router as listening_router
from .reading import router as reading_router
from .speaking import router as speaking_router
from .writing import router as writing_router

router = APIRouter()
router.include_router(history_router, prefix="/history", tags=["Test History"])
router.include_router(top_router, prefix="/top", tags=["Top Tests"])
router.include_router(listening_router, prefix="/listening", tags=["Listening Tests"])
router.include_router(reading_router, prefix="/reading", tags=["Reading Tests"])
router.include_router(speaking_router, prefix="/speaking", tags=["Speaking Tests"])
router.include_router(writing_router, prefix="/writing", tags=["Writing Tests"])
