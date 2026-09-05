import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import logger, setup_logging
from app.database import close_db, init_db
from app.schemas.envelope import ApiError, ApiErrorDetail, ApiResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager handling startup and shutdown hooks."""
    # Startup
    setup_logging()
    logger.info("Starting up {} in {} mode...", settings.PROJECT_NAME, settings.ENVIRONMENT)
    await init_db()
    logger.info("Application startup complete. Ready to receive calls and requests.")

    yield

    # Shutdown
    logger.info("Shutting down {}...", settings.PROJECT_NAME)
    await close_db()
    logger.info("Application shutdown complete.")


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production Voice AI Patient Registration System backend. "
        "Supports real-time telephony intake via Vapi, persistent clinical demographics, "
        "REST API CRUD with standard envelopes, and an executive companion dashboard."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS for Dashboard and third-party consumers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing and structured request logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            "{} {} - Status: {} ({:.2f}ms)",
            method,
            path,
            response.status_code,
            process_time,
        )
        return response
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        logger.exception(
            "Unhandled exception processing {} {}: {} ({:.2f}ms)",
            method,
            path,
            str(exc),
            process_time,
        )
        raise exc


# ==============================================================================
# Global Exception Handlers (Standardized Envelopes)
# ==============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Translate Pydantic validation errors into standardized API error envelope."""
    details = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        details.append(
            ApiErrorDetail(
                field=field_path,
                issue=err.get("msg", "Invalid input"),
                received=err.get("input"),
            )
        )

    error_payload = ApiResponse.error_response(
        code="VALIDATION_ERROR",
        message="One or more fields failed validation rules.",
        details=details,
    )
    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content=error_payload.model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Translate FastAPI HTTPExceptions into standardized error envelope."""
    error_payload = ApiResponse.error_response(
        code="HTTP_ERROR",
        message=str(exc.detail),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Translate unexpected internal server errors into standardized envelope."""
    logger.exception("Internal Server Error on {}: {}", request.url.path, str(exc))
    error_payload = ApiResponse.error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(),
    )


# ==============================================================================
# Router Ingestion
# ==============================================================================

# Mount routes directly at root to satisfy assessment spec (/patients, /health, /webhooks)
app.include_router(api_router)

# Also mount under /api/v1 for versioned routing
app.include_router(api_router, prefix="/api/v1")


# Ensure static directory exists
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to interactive API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/dashboard", include_in_schema=False)
async def dashboard_redirect():
    """Serve the companion Executive Dashboard."""
    return RedirectResponse(url="/static/index.html")
