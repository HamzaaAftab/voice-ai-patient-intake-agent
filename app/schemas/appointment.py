from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import AppointmentStatusEnum


class AppointmentCreate(BaseModel):
    """Schema for scheduling a post-registration patient appointment."""
    patient_id: str = Field(..., description="UUID of registered patient")
    appointment_time: datetime = Field(..., description="Date and time of appointment (ISO format)")
    provider_name: str = Field("Dr. Sarah Smith, MD", max_length=100)
    reason: str = Field("New Patient Intake & Wellness Consultation", max_length=255)

    @field_validator("appointment_time", mode="before")
    @classmethod
    def validate_future_time(cls, v: object) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime):
            return v
        raise ValueError("Invalid appointment time.")


class AppointmentResponse(BaseModel):
    """Schema for appointment details returned to callers and API."""
    appointment_id: str
    patient_id: str
    appointment_time: datetime
    provider_name: str
    reason: str
    status: AppointmentStatusEnum
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
