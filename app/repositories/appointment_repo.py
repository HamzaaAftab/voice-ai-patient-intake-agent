from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.appointment import Appointment
from app.repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    """Data access repository for clinical appointment bookings."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Appointment, session)

    async def create(self, appointment: Appointment) -> Appointment:
        self.session.add(appointment)
        await self.session.flush()
        await self.session.refresh(appointment)
        return appointment

    async def list_by_patient(self, patient_id: str) -> List[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.appointment_time.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
