from fastapi import APIRouter
from .views import (
    users_router,
    auth_router,
    tariffs_router,
    notifications_router,
    tests_router,
    transactions_router,
    analyses_router,
    comments_router,
    payments_router,
)

router = APIRouter()

# Users group router (CRUD, profile, email update)
router.include_router(users_router, prefix="/users", tags=["Users"])

# Auth (login, logout, register, resend, forget password, verification)
router.include_router(auth_router, prefix="/auth", tags=["Auth"])

# Tariffs
router.include_router(tariffs_router, prefix="/tariffs", tags=["Tariffs"])

# Tests
router.include_router(tests_router, prefix="/tests")

# Analyses
router.include_router(analyses_router, prefix="/analyses", tags=["Analyses"])

# Notifications
router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])

# Comments
router.include_router(comments_router, prefix="/comments", tags=["Comments"])

# Transactions
router.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])

# Payments
router.include_router(payments_router, prefix="/payments", tags=["Payments"])