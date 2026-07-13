import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    """Thread-safe in-memory rate limiter with sliding window."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, key: str) -> bool:
        """Returns True if the request is within rate limits."""
        now = time.time()
        with self.lock:
            # Clean up old requests
            self.requests[key] = [t for t in self.requests[key] if now - t < self.window_seconds]
            if len(self.requests[key]) >= self.max_requests:
                return False
            self.requests[key].append(now)
            return True

# Pre-configured instances:
forgot_password_email_limiter = RateLimiter(max_requests=3, window_seconds=3600)
forgot_password_ip_limiter = RateLimiter(max_requests=10, window_seconds=3600)
