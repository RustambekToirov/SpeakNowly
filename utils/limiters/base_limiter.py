import redis.asyncio as redis
from datetime import timedelta, datetime, timezone

class AsyncLimiter:
    """
    Implements rate limiting using Redis backend.
    """

    def __init__(self, redis_client: redis.Redis, prefix: str, max_attempts: int, period: timedelta):
        self.redis = redis_client
        self.prefix = prefix
        self.max_attempts = max_attempts
        self.period = period

    def get_key(self, identifier: str) -> str:
        """
        Generates Redis key from prefix and identifier.
        """
        return f"{self.prefix}:{identifier}"

    async def is_blocked(self, identifier: str) -> bool:
        """
        Checks if identifier has exceeded attempt limit.
        """
        key = self.get_key(identifier)
        curr = await self.redis.get(key)
        if curr is not None and int(curr) >= self.max_attempts:
            return True
        return False

    async def register_attempt(self, identifier: str) -> None:
        """
        Records new attempt for identifier.
        """
        key = self.get_key(identifier)
        curr = await self.redis.get(key)
        if curr is None:
            await self.redis.setex(key, int(self.period.total_seconds()), 1)
        else:
            await self.redis.incr(key)
            await self.redis.expire(key, int(self.period.total_seconds()))

    async def reset(self, identifier: str) -> None:
        """
        Resets attempt counter for identifier.
        """
        key = self.get_key(identifier)
        await self.redis.delete(key)

class EmailUpdateLimiter:
    """
    Limits email update requests to once per period.
    """
    def __init__(self, redis_client: redis.Redis, period: timedelta = timedelta(days=7)):
        self.redis = redis_client
        self.prefix = "email_update_last"
        self.period = period

    def get_key(self, email: str) -> str:
        return f"{self.prefix}:{email}"

    async def is_blocked(self, email: str) -> bool:
        """
        Checks if email was updated within blocking period.
        """
        key = self.get_key(email)
        last_update = await self.redis.get(key)
        if last_update:
            last_dt = datetime.fromisoformat(last_update)
            if datetime.now(timezone.utc) - last_dt < self.period:
                return True
        return False

    async def register_attempt(self, email: str) -> None:
        """
        Records email update attempt timestamp.
        """
        key = self.get_key(email)
        await self.redis.set(key, datetime.now(timezone.utc).isoformat())

    async def reset(self, email: str) -> None:
        """
        Resets limiter for email.
        """
        key = self.get_key(email)
        await self.redis.delete(key)
