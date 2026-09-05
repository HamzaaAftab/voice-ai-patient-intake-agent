"""Data access repositories package."""

from app.repositories.base import BaseRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.call_log_repo import CallLogRepository
from app.repositories.appointment_repo import AppointmentRepository

__all__ = [
    "BaseRepository",
    "PatientRepository",
    "CallLogRepository",
    "AppointmentRepository",
]
