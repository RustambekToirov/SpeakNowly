import json
from redis.asyncio import Redis
from config import REDIS_URL
from datetime import timedelta, datetime, timezone

class CacheService:
    """
    Provides Redis-based caching for application data with serialization
    and automatic expiration support.
    """

    def __init__(self, redis_url=REDIS_URL):
        """
        Initialize cache service:
        1. Create Redis client with provided URL.
        2. Configure client for automatic JSON decoding.
        """
        self.redis = Redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str):
        """
        Get object from cache:
        1. Retrieve data from Redis by key.
        2. Deserialize from JSON if found.
        3. Return deserialized object or None.
        """
        # 1-3. Get, deserialize, and return
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value, expire: int = 3600):
        """
        Save object to cache:
        1. Handle ORM objects by converting to dict if needed.
        2. Handle collections by converting items to dict.
        3. Serialize to JSON with datetime handling.
        4. Store in Redis with expiration time.
        """
        # 1-2. Handle ORM objects and collections
        if hasattr(value, "__iter__") and not isinstance(value, str):
            value = [v.dict() if hasattr(v, "dict") else v for v in value]
        elif hasattr(value, "dict"):
            value = value.dict()
            
        # 3-4. Serialize and store
        await self.redis.set(key, json.dumps(value, default=str), ex=expire)

    async def check_email_resend_limit(self, email: str, verification_type: str) -> dict:
        """
        Check and enforce email resend rate limit:
        1. Generate unique key for email/type combination.
        2. Check if key exists (user is blocked).
        3. Calculate remaining block time if blocked.
        4. Set blocking key with expiration if not blocked.
        5. Return status with block information.
        """
        # 1. Generate key
        key = f"resend_block_{email}_{verification_type}".replace(" ", "").lower()
        
        # 2-3. Check if blocked
        blocked_until = await self.redis.get(key)
        if blocked_until:
            remaining = (datetime.fromisoformat(blocked_until) - datetime.now(timezone.utc)).total_seconds()
            if remaining > 0:
                return {
                    "blocked": True,
                    "remaining_time": {"seconds": int(remaining)},
                    "message": f"Please wait {int(remaining)} seconds before resending the code.",
                }

        # 4. Set block
        block_duration = 60
        await self.redis.set(
            key,
            (datetime.now(timezone.utc) + timedelta(seconds=block_duration)).isoformat(),
            ex=block_duration
        )
        
        # 5. Return not blocked
        return {"blocked": False}

# Singleton instance for import
cache = CacheService()