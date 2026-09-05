from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.appointment import Appointment
from app.repositories.appointment_repo import AppointmentRepository
from app.repositories.patient_repo import PatientRepository
from app.schemas.appointment import AppointmentCreate


class AppointmentService:
    """Service for managing clinical appointments."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AppointmentRepository(session)
        self.patient_repo = PatientRepository(session)

    async def schedule_appointment(
        self, payload: AppointmentCreate
    ) -> Optional[Appointment]:
        """Schedule a new appointment for a registered patient."""
        patient = await self.patient_repo.get_by_id(payload.patient_id)
        if not patient:
            logger.warning("Attempted to schedule appointment for non-existent patient: {}", payload.patient_id)
            return None

        appointment = Appointment(**payload.model_dump())
        created = await self.repo.create(appointment)
        logger.info(
            "Appointment scheduled: id={}, patient_id={}, time={}",
            created.appointment_id,
            created.patient_id,
            created.appointment_time,
        )
        return created

    async def list_patient_appointments(
        self, patient_id: str
    ) -> List[Appointment]:
        return await self.repo.list_by_patient(patient_id)
