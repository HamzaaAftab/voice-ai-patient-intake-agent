from typing import Generic, List, Optional, TypeVar, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiErrorDetail(BaseModel):
    """Detailed diagnostic item for validation and runtime errors."""
    field: Optional[str] = None
    issue: str
    received: Optional[Any] = None


class ApiError(BaseModel):
    """Structured error payload for standardized error responses."""
    code: str
    message: str
    details: Optional[List[ApiErrorDetail]] = None


class ApiResponse(BaseModel, Generic[T]):
    """Consistent envelope required by assessment specification:
    { "data": {...}, "error": null }
    """
    data: Optional[T] = None
    error: Optional[ApiError] = None

    @classmethod
    def success_response(cls, data: T) -> "ApiResponse[T]":
        """Generate success envelope."""
        return cls(data=data, error=None)

    @classmethod
    def error_response(
        cls,
        code: str,
        message: str,
        details: Optional[List[ApiErrorDetail]] = None,
    ) -> "ApiResponse[None]":
        """Generate error envelope."""
        return cls(
            data=None,
            error=ApiError(code=code, message=message, details=details),
        )
