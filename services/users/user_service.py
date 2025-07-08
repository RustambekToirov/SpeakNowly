from fastapi import HTTPException, status
from typing import Optional, Any
from tortoise.transactions import in_transaction
from pydantic import validate_email as pydantic_validate_email, ValidationError
import asyncio

from models import Tariff, TokenTransaction, TransactionType, User

ALLOWED_UPDATE_FIELDS = {
    "email", "first_name", "last_name", "age", "photo", "last_login",
    "is_active", "is_verified"
}
ADMIN_ALLOWED_UPDATE_FIELDS = ALLOWED_UPDATE_FIELDS | {"is_staff", "is_superuser"}


def validate_email(email: str, t: dict):
    """
    Validate email format:
    1. Check email format using pydantic validator.
    2. Raise HTTPException if invalid.
    """
    try:
        pydantic_validate_email(email)
    except ValidationError:
        raise HTTPException(status_code=400, detail=t.get("invalid_email_format", "Invalid email format"))


def validate_password(password: str, t: dict):
    """
    Validate password strength:
    1. Check minimum length (8 characters).
    2. Ensure password contains both letters and numbers.
    3. Raise HTTPException if invalid.
    """
    if len(password) < 8:
        raise HTTPException(status_code=400, detail=t.get("password_too_weak", "Password must be at least 8 characters"))
    if password.isdigit() or password.isalpha():
        raise HTTPException(status_code=400, detail=t.get("password_too_weak", "Password must contain both letters and numbers"))


class UserService:
    """
    Provides user management operations including authentication, registration,
    and profile management with permission control.
    """

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        """
        Get user by email:
        1. Query database for user with matching email.
        2. Return user or None if not found.
        """
        return await User.get_or_none(email=email)

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        """
        Get user by ID:
        1. Query database for user with matching ID.
        2. Return user or None if not found.
        """
        return await User.get_or_none(id=user_id)

    @staticmethod
    async def register(email: str, password: str, t: dict, **extra_fields) -> User:
        """
        Register a new user:
        1. Validate email format.
        2. Check if email already registered.
        3. Validate password strength.
        4. Create user with hashed password.
        5. Assign default tariff and tokens.
        6. Create initial token transaction record.
        7. Return created user.
        """
        # 1. Validate email
        validate_email(email, t)
        
        # 2. Check if email already registered
        existing = await UserService.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t.get("user_already_registered", "Email already registered"))

        # 3. Validate password
        validate_password(password, t)

        # 4-6. Create user and assign default tariff/tokens atomically
        async with in_transaction():
            user = User(email=email, **extra_fields)
            user.set_password(password)
            await user.save()

            default_tariff = await Tariff.get_default_tariff()
            if default_tariff:
                user.tariff = default_tariff
                user.tokens = default_tariff.tokens
                await user.save()

                await TokenTransaction.create(
                    user=user,
                    transaction_type=TransactionType.DAILY_BONUS,
                    amount=default_tariff.tokens,
                    balance_after_transaction=user.tokens,
                    description=f"Daily bonus for {default_tariff.name}",
                )

        # 7. Return created user
        return user

    @staticmethod
    async def authenticate(email: str, password: str, t: dict) -> User:
        """
        Authenticate user:
        1. Get user by email.
        2. Check if user is active.
        3. Verify password in executor to avoid blocking event loop.
        4. Verify email confirmation status.
        5. Return authenticated user.
        """
        # 1. Get user by email
        user = await UserService.get_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail=t.get("invalid_credentials", "Invalid email or password"))

        # 2. Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=403, detail=t.get("inactive_user", "User account is inactive"))

        # 3. Check password
        loop = asyncio.get_event_loop()
        valid = await loop.run_in_executor(None, user.check_password, password)
        if not valid:
            raise HTTPException(status_code=400, detail=t.get("invalid_credentials", "Invalid email or password"))

        # 4. Check if email is verified
        if not user.is_verified:
            raise HTTPException(status_code=403, detail=t.get("email_not_verified", "Email address not verified"))

        # 5. Return authenticated user
        return user

    @staticmethod
    async def update_user(user_id: int, t: dict, **fields) -> User:
        """
        Update user profile (non-admin):
        1. Get user by ID.
        2. Validate email format if changing email.
        3. Check if new email is already in use.
        4. Check for invalid fields.
        5. Update allowed fields.
        6. Save and return updated user.
        """
        # 1. Get user
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=t.get("user_not_found", "User not found"))

        # 2-3. Validate email if changed
        if "email" in fields and fields["email"]:
            validate_email(fields["email"], t)
            existing = await UserService.get_by_email(fields["email"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail=t.get("email_already_in_use", "Email address already in use"))

        # 4. Check for invalid fields
        invalid = set(fields) - ALLOWED_UPDATE_FIELDS
        if invalid:
            raise HTTPException(status_code=400, detail=t.get("invalid_fields", f"Invalid fields: {', '.join(invalid)}"))

        # 5. Update allowed fields
        for attr, value in fields.items():
            if attr in ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(user, attr, value)
                
        # 6. Save and return updated user
        await user.save()
        return user

    @staticmethod
    async def admin_update_user(user_id: int, t: dict, **fields) -> User:
        """
        Update user profile (admin):
        1. Get user by ID.
        2. Check for invalid fields.
        3. Validate email format if changing email.
        4. Check if new email is already in use.
        5. Update allowed fields including staff/superuser.
        6. Save and return updated user.
        """
        # 1. Get user
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=t.get("user_not_found", "User not found"))

        # 2. Check for invalid fields
        invalid = set(fields) - ADMIN_ALLOWED_UPDATE_FIELDS
        if invalid:
            raise HTTPException(status_code=400, detail=t.get("invalid_fields", f"Invalid fields: {', '.join(invalid)}"))

        # 3-4. Validate email if changed
        if "email" in fields and fields["email"]:
            validate_email(fields["email"], t)
            existing = await UserService.get_by_email(fields["email"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail=t.get("email_already_in_use", "Email address already in use"))

        # 5. Update allowed fields
        for attr, value in fields.items():
            if attr in ADMIN_ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(user, attr, value)
                
        # 6. Save and return updated user
        await user.save()
        return user

    @staticmethod
    async def change_password(user_id: int, new_password: str, t: dict) -> None:
        """
        Change user password:
        1. Get user by ID.
        2. Validate new password strength.
        3. Hash and set new password.
        4. Save user.
        """
        # 1. Get user
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=t.get("user_not_found", "User not found"))

        # 2. Validate password
        validate_password(new_password, t)

        # 3. Set new password
        user.set_password(new_password)
        
        # 4. Save user
        await user.save()

    @staticmethod
    async def delete_user(user_id: int, t: dict) -> None:
        """
        Delete user:
        1. Get user by ID.
        2. Delete user and related data.
        """
        # 1. Get user
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=t.get("user_not_found", "User not found"))

        # 2. Delete user
        await user.delete()

    @staticmethod
    async def list_users(is_active: Optional[bool] = None) -> list[User]:
        """
        List users:
        1. Apply active filter if specified.
        2. Return matching users.
        """
        # 1-2. Apply filter and return users
        if is_active is None:
            return await User.all()
        return await User.filter(is_active=is_active)

    @staticmethod
    async def create_user(
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        age: Optional[int] = None,
        photo: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> User:
        """
        Create user (admin only):
        1. Create user with provided attributes.
        2. Set hashed password.
        3. Save and return created user.
        """
        # 1. Create user with provided attributes
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            age=age,
            photo=photo,
            is_active=is_active,
            is_verified=is_verified,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        
        # 2. Set hashed password
        user.set_password(password)
        
        # 3. Save and return created user
        await user.save()
        return user

    @staticmethod
    async def assign_default_tariff(user: User):
        """
        Assign default tariff and tokens to a user if not already assigned.
        """
        if not user.tariff_id:
            default_tariff = await Tariff.get_default_tariff()
            if default_tariff:
                user.tariff = default_tariff
                user.tokens = default_tariff.tokens
                await user.save()
                await TokenTransaction.create(
                    user=user,
                    transaction_type=TransactionType.DAILY_BONUS,
                    amount=default_tariff.tokens,
                    balance_after_transaction=user.tokens,
                    description=f"Daily bonus for {default_tariff.name}",
                )
