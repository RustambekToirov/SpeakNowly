from fastapi import APIRouter
from .users import router as users_router
from .profile import router as profile_router
from .email_update import router as email_update_router
from .auth import router as auth_router
from .login import router as login_router
from .logout import router as logout_router
from .register import router as register_router
from .resend import router as resend_router
from .forget_password import router as forget_password_router
from .verification_codes import router as verification_codes_router

# Users group router (CRUD, profile, email update)
users_group_router = APIRouter()
users_group_router.include_router(users_router, prefix="", tags=["Users"])
users_group_router.include_router(profile_router, prefix="/profile", tags=["Users"])
users_group_router.include_router(email_update_router, prefix="", tags=["Users"])

# Auth group router (login, logout, register, resend, forget password, verification)
auth_group_router = APIRouter()
auth_group_router.include_router(auth_router, prefix="", tags=["Auth"])
auth_group_router.include_router(login_router, prefix="", tags=["Auth"])
auth_group_router.include_router(logout_router, prefix="", tags=["Auth"])
auth_group_router.include_router(register_router, prefix="", tags=["Auth"])
auth_group_router.include_router(resend_router, prefix="", tags=["Auth"])
auth_group_router.include_router(forget_password_router, prefix="", tags=["Auth"])
auth_group_router.include_router(verification_codes_router, prefix="", tags=["Auth"])
