from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.patient import Patient
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    """Data access repository for clinical patient demographic records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Patient, session)

    async def create(self, patient: Patient) -> Patient:
        """Persist a new patient entity to the database."""
        self.session.add(patient)
        await self.session.flush()
        await self.session.refresh(patient)
        return patient

    async def get_by_id(
        self, patient_id: str, include_deleted: bool = False
    ) -> Optional[Patient]:
        """Fetch single patient by UUID.
        
        By default, excludes soft-deleted records unless include_deleted=True.
        """
        stmt = select(Patient).where(Patient.patient_id == patient_id)
        if not include_deleted:
            stmt = stmt.where(Patient.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_phone(
        self, phone_number: str, include_deleted: bool = False
    ) -> Optional[Patient]:
        """Find an active patient by phone number for duplicate detection."""
        stmt = select(Patient).where(Patient.phone_number == phone_number)
        if not include_deleted:
            stmt = stmt.where(Patient.deleted_at.is_(None))
        # Order by created_at desc to get most recent
        stmt = stmt.order_by(Patient.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_all(
        self,
        last_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        phone_number: Optional[str] = None,
        include_deleted: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Patient], int]:
        """Retrieve patients matching optional filter criteria with pagination.
        
        Returns tuple of (patients_list, total_count).
        """
        stmt = select(Patient)
        count_stmt = select(func.count()).select_from(Patient)

        # Base filter: soft-deleted records exclusion
        if not include_deleted:
            stmt = stmt.where(Patient.deleted_at.is_(None))
            count_stmt = count_stmt.where(Patient.deleted_at.is_(None))

        # Filter by last name (case-insensitive substring/prefix search)
        if last_name:
            clean_name = last_name.strip()
            stmt = stmt.where(Patient.last_name.ilike(f"%{clean_name}%"))
            count_stmt = count_stmt.where(Patient.last_name.ilike(f"%{clean_name}%"))

        # Filter by date of birth
        if date_of_birth:
            stmt = stmt.where(Patient.date_of_birth == date_of_birth)
            count_stmt = count_stmt.where(Patient.date_of_birth == date_of_birth)

        # Filter by phone number
        if phone_number:
            clean_phone = phone_number.strip()
            stmt = stmt.where(Patient.phone_number.like(f"%{clean_phone}%"))
            count_stmt = count_stmt.where(Patient.phone_number.like(f"%{clean_phone}%"))

        # Order by creation date descending
        stmt = stmt.order_by(Patient.created_at.desc()).offset(offset).limit(limit)

        # Execute queries
        total_count_res = await self.session.execute(count_stmt)
        total_count = total_count_res.scalar() or 0

        result = await self.session.execute(stmt)
        patients = list(result.scalars().all())

        return patients, total_count

    async def update(self, patient: Patient, update_data: dict) -> Patient:
        """Apply partial dictionary update to an existing patient entity."""
        for field, value in update_data.items():
            if hasattr(patient, field) and value is not None:
                setattr(patient, field, value)
        patient.updated_at = datetime.now(timezone.utc)
        self.session.add(patient)
        await self.session.flush()
        await self.session.refresh(patient)
        return patient

    async def soft_delete(self, patient: Patient) -> Patient:
        """Mark patient as soft-deleted by stamping deleted_at with UTC timestamp."""
        now = datetime.now(timezone.utc)
        patient.deleted_at = now
        patient.updated_at = now
        self.session.add(patient)
        await self.session.flush()
        await self.session.refresh(patient)
        return patient

    async def count_metrics(self) -> dict:
        """Return aggregated counts for the companion dashboard."""
        total_stmt = select(func.count()).select_from(Patient)
        active_stmt = select(func.count()).select_from(Patient).where(Patient.deleted_at.is_(None))
        deleted_stmt = select(func.count()).select_from(Patient).where(Patient.deleted_at.is_not(None))

        total_res = await self.session.execute(total_stmt)
        active_res = await self.session.execute(active_stmt)
        deleted_res = await self.session.execute(deleted_stmt)

        return {
            "total_patients": total_res.scalar() or 0,
            "active_patients": active_res.scalar() or 0,
            "deleted_patients": deleted_res.scalar() or 0,
        }
