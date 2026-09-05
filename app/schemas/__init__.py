"""Pydantic validation schemas and API response envelopes."""

from app.schemas.envelope import ApiResponse, ApiError, ApiErrorDetail
from app.schemas.patient import PatientBase, PatientCreate, PatientUpdate, PatientResponse
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.schemas.webhooks import VapiWebhookPayload, VapiToolCallResult

__all__ = [
    "ApiResponse",
    "ApiError",
    "ApiErrorDetail",
    "PatientBase",
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "AppointmentCreate",
    "AppointmentResponse",
    "VapiWebhookPayload",
    "VapiToolCallResult",
]
