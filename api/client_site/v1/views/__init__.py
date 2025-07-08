from .tests import router as tests_router
from .users import users_group_router as users_router
from .users import auth_group_router as auth_router
from .analyses import router as analyses_router
from .comments import router as comments_router
from .notifications import router as notifications_router
from .payments import router as payments_router
from .tariffs import router as tariffs_router
from .transactions import router as transactions_router

__all__ = [
    "users_router",
    "auth_router",
    "tests_router",
    "analyses_router",
    "comments_router",
    "notifications_router",
    "payments_router",
    "tariffs_router",
    "transactions_router",
]
