from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.database import get_db
from app.schemas.envelope import ApiResponse

router = APIRouter(tags=["System"])
settings = get_settings()


@router.get(
    "/health",
    response_model=ApiResponse[dict],
    summary="Health and readiness probe",
    status_code=status.HTTP_200_OK,
)
async def health_check(db: AsyncSession = Depends(get_db)) -> ApiResponse[dict]:
    """Verify backend system status and live database connectivity."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return ApiResponse.success_response(
        {
            "status": "online" if db_status == "healthy" else "degraded",
            "environment": settings.ENVIRONMENT,
            "database": db_status,
            "version": "1.0.0",
        }
    )
