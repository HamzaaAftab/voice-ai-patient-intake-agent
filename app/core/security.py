import hmac
from fastapi import HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader
from app.core.config import get_settings
from app.core.logging import logger

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate incoming API Key for protected REST endpoints.
    
    If no API_KEY is set or in dev mode without key, request is allowed.
    """
    settings = get_settings()
    if not settings.API_KEY or settings.ENVIRONMENT == "development":
        return "authorized_dev"

    if not api_key or not hmac.compare_digest(api_key, settings.API_KEY):
        logger.warning("Unauthorized API Key access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key


async def verify_vapi_webhook(request: Request) -> bool:
    """Verify incoming webhook request from Vapi.
    
    Checks for 'x-vapi-secret' header matching configured WEBHOOK_SECRET.
    In development mode with default secret, logs and allows.
    """
    settings = get_settings()
    provided_secret = request.headers.get("x-vapi-secret") or request.headers.get("X-Vapi-Secret")
    
    # If authorization bearer token is passed instead
    if not provided_secret:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided_secret = auth_header.split("Bearer ")[1].strip()

    if not settings.WEBHOOK_SECRET or settings.ENVIRONMENT == "development":
        # Allow in local development mode
        return True

    if not provided_secret or not hmac.compare_digest(provided_secret, settings.WEBHOOK_SECRET):
        logger.warning(
            "Vapi webhook verification failed: secret mismatch",
            client_host=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature / secret",
        )
    return True


def mask_phone_number(phone: str) -> str:
    """Mask phone number for logging compliance (e.g. +1415***2671)."""
    if not phone or len(phone) < 6:
        return "***"
    return f"{phone[:4]}***{phone[-4:]}"
