from datetime import timedelta
from .base_limiter import AsyncLimiter, EmailUpdateLimiter

def get_login_limiter(redis_client):
    """
    Creates login limiter: 5 attempts per 15 minutes.
    """
    return AsyncLimiter(redis_client, prefix="login", max_attempts=5, period=timedelta(minutes=15))

def get_register_limiter(redis_client):
    """
    Creates registration limiter: 5 attempts per 10 minutes.
    """
    return AsyncLimiter(redis_client, prefix="register", max_attempts=5, period=timedelta(minutes=10))

def get_resend_limiter(redis_client):
    """
    Creates OTP resend limiter: 5 attempts per 5 minutes.
    """
    return AsyncLimiter(redis_client, prefix="resend", max_attempts=5, period=timedelta(minutes=5))

def get_forget_password_limiter(redis_client):
    """
    Creates password reset limiter: 5 attempts per 15 minutes.
    """
    return AsyncLimiter(redis_client, prefix="forget_password", max_attempts=5, period=timedelta(minutes=15))