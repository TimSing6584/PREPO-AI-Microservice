import asyncio
import logging
from fastapi import HTTPException, Request, status
from upstash_ratelimit import Ratelimit, SlidingWindow

from .redis_client import redis
logger = logging.getLogger("rate_limit")
# Different limiters for different route sensitivity
rate_limiters = {
    "pipeline": Ratelimit(
        redis=redis,
        limiter=SlidingWindow(max_requests=10, window=60),
        prefix="rl:stt_microservice:pipeline"
    ),
    "stt": Ratelimit(
        redis=redis,
        limiter=SlidingWindow(max_requests=10, window=60),
        prefix="rl:stt_microservice:stt"
    ),
    "llm": Ratelimit(
        redis=redis,
        limiter=SlidingWindow(max_requests=10, window=60),
        prefix="rl:stt_microservice:llm"
    ),
}


class RateLimiter:
    def __init__(self, type: str):
        self.limiter = rate_limiters[type]
        self.type = type

    async def __call__(self, request: Request) -> None:
        user_id = request.state.user_id
        response = await asyncio.to_thread(self.limiter.limit, user_id)

        if not response.allowed:
            logger.warning(
                f"Rate limit exceeded: user={user_id} type={self.type} path={request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
            )