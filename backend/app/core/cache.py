# backend/app/core/cache.py
# Redis Caching Utility interface supporting dashboard summaries, job analysis, & optimizations

import json
from typing import Any, Optional
from backend.app.core.config import settings

class RedisCache:
    def __init__(self):
        # In a real production setup, we would initialize redis connection pools
        # self.client = redis.from_url(settings.REDIS_URL)
        self.mock_db = {}

    def get(self, key: str) -> Optional[Any]:
        """Fetch value from cache."""
        val = self.mock_db.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        return None

    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> None:
        """Store value in cache with expiration limit."""
        try:
            self.mock_db[key] = json.dumps(value)
        except Exception:
            self.mock_db[key] = str(value)

    def delete(self, key: str) -> None:
        """Clear key from cache."""
        if key in self.mock_db:
            del self.mock_db[key]

# Global cache instance
cache = RedisCache()
