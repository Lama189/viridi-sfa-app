from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio import RedisError
from starlette.responses import PlainTextResponse

from app.api.middlewares.rate_limit import RateLimitMiddleware
from app.application.interfaces.cache.rate_limiter import IRateLimiter
from app.infrastructure.redis.repos.rate_limiter import RedisRateLimiter


@pytest.mark.asyncio
async def test_redis_rate_limiter_limit_zero_or_negative():
    mock_client = MagicMock()
    limiter = RedisRateLimiter(client=mock_client)

    assert await limiter.allow("test-key", limit=0, window=60) is True
    assert await limiter.allow("test-key", limit=-5, window=60) is True


@pytest.mark.asyncio
async def test_redis_rate_limiter_window_invalid():
    mock_client = MagicMock()
    limiter = RedisRateLimiter(client=mock_client)

    with pytest.raises(ValueError, match="Window must be greater than zero"):
        await limiter.allow("test-key", limit=10, window=0)

    with pytest.raises(ValueError, match="Window must be greater than zero"):
        await limiter.allow("test-key", limit=10, window=-10)


@pytest.mark.asyncio
async def test_redis_rate_limiter_allowed():
    mock_client = MagicMock()
    mock_script = AsyncMock(return_value=1)
    mock_client.register_script.return_value = mock_script

    limiter = RedisRateLimiter(client=mock_client)
    result = await limiter.allow("user-1", limit=10, window=60)

    assert result is True
    mock_script.assert_called_once()
    assert mock_script.call_args.kwargs["keys"] == ["rate_limit:user-1"]


@pytest.mark.asyncio
async def test_redis_rate_limiter_rate_limited():
    mock_client = MagicMock()
    mock_script = AsyncMock(return_value=0)
    mock_client.register_script.return_value = mock_script

    limiter = RedisRateLimiter(client=mock_client)
    result = await limiter.allow("user-1", limit=10, window=60)

    assert result is False
    mock_script.assert_called_once()


@pytest.mark.asyncio
async def test_redis_rate_limiter_redis_error_fail_open():
    mock_client = MagicMock()
    mock_script = AsyncMock(side_effect=RedisError("Redis connection lost"))
    mock_client.register_script.return_value = mock_script

    limiter = RedisRateLimiter(client=mock_client)
    result = await limiter.allow("user-1", limit=10, window=60)

    assert result is True


@pytest.mark.asyncio
async def test_rate_limit_middleware_allows_request():
    mock_limiter = AsyncMock(spec=IRateLimiter)
    mock_limiter.allow.return_value = True

    async def dummy_app(scope, receive, send):
        response = PlainTextResponse("OK")
        await response(scope, receive, send)

    middleware = RateLimitMiddleware(
        app=dummy_app,
        rate_limiter=mock_limiter,
        default_limit=10,
        default_window=60,
    )

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/some-resource",
        "headers": [(b"host", b"testserver")],
        "client": ("127.0.0.1", 12345),
    }

    async def receive():
        return {"type": "http.request"}

    sent_messages = []

    async def send(msg):
        sent_messages.append(msg)

    with (
        patch("app.api.middlewares.rate_limit.sys.modules", {}),
        patch.dict("os.environ", {"TESTING": "0"}),
    ):
        await middleware(scope, receive, send)

    mock_limiter.allow.assert_called_once_with(
        "127.0.0.1:/api/v1/some-resource", limit=10, window=60
    )
    start_message = next(
        msg for msg in sent_messages if msg["type"] == "http.response.start"
    )
    assert start_message["status"] == 200


@pytest.mark.asyncio
async def test_rate_limit_middleware_blocks_when_rate_limited():
    mock_limiter = AsyncMock(spec=IRateLimiter)
    mock_limiter.allow.return_value = False

    async def dummy_app(scope, receive, send):
        response = PlainTextResponse("OK")
        await response(scope, receive, send)

    middleware = RateLimitMiddleware(
        app=dummy_app,
        rate_limiter=mock_limiter,
        default_limit=5,
        default_window=30,
        custom_rules=[("/api/v1/auth", 2, 10)],
    )

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "headers": [
            (b"host", b"testserver"),
            (b"x-forwarded-for", b"203.0.113.195, 70.41.3.18"),
        ],
        "client": ("127.0.0.1", 12345),
    }

    async def receive():
        return {"type": "http.request"}

    sent_messages = []

    async def send(msg):
        sent_messages.append(msg)

    with (
        patch("app.api.middlewares.rate_limit.sys.modules", {}),
        patch.dict("os.environ", {"TESTING": "0"}),
    ):
        await middleware(scope, receive, send)

    mock_limiter.allow.assert_called_once_with(
        "203.0.113.195:/api/v1/auth/login", limit=2, window=10
    )
    start_message = next(
        msg for msg in sent_messages if msg["type"] == "http.response.start"
    )
    assert start_message["status"] == 429
