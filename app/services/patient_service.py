from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.patient import Patient
from app.repositories.patient_repo import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientService:
    """Business logic and domain service for Patient registration and management."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PatientRepository(session)

    async def register_patient(
        self, payload: PatientCreate, allow_duplicate: bool = False
    ) -> Tuple[Optional[Patient], Optional[Patient]]:
        """Register a new patient.
        
        Enforces duplicate detection by phone number:
        - If an active patient already exists with this phone and allow_duplicate=False,
          returns (None, existing_patient).
        - Otherwise, persists and returns (new_patient, None).
        """
        existing = await self.repo.find_by_phone(payload.phone_number)
        if existing and not allow_duplicate:
            logger.warning(
                "Duplicate registration attempt blocked for phone={}: existing patient id={}",
                payload.phone_number,
                existing.patient_id,
            )
            return None, existing

        patient_dict = payload.model_dump()
        new_patient = Patient(**patient_dict)
        saved_patient = await self.repo.create(new_patient)

        logger.info(
            "Patient registered successfully: id={}, name='{} {}', phone={}",
            saved_patient.patient_id,
            saved_patient.first_name,
            saved_patient.last_name,
            saved_patient.phone_number,
        )
        return saved_patient, None

    async def get_patient_by_id(
        self, patient_id: str, include_deleted: bool = False
    ) -> Optional[Patient]:
        """Retrieve single patient by UUID."""
        return await self.repo.get_by_id(patient_id, include_deleted=include_deleted)

    async def find_by_phone(
        self, phone_number: str, include_deleted: bool = False
    ) -> Optional[Patient]:
        """Check for existing patient by phone number for voice duplicate detection."""
        return await self.repo.find_by_phone(phone_number, include_deleted=include_deleted)

    async def list_patients(
        self,
        last_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        phone_number: Optional[str] = None,
        include_deleted: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Patient], int]:
        """List patients matching query filters."""
        return await self.repo.list_all(
            last_name=last_name,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            include_deleted=include_deleted,
            offset=offset,
            limit=limit,
        )

    async def update_patient(
        self, patient_id: str, payload: PatientUpdate
    ) -> Optional[Patient]:
        """Apply partial update to patient demographics."""
        patient = await self.repo.get_by_id(patient_id)
        if not patient:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        updated = await self.repo.update(patient, update_data)
        logger.info("Patient updated: id={}", patient_id)
        return updated

    async def soft_delete_patient(self, patient_id: str) -> bool:
        """Soft-delete a patient record by populating deleted_at timestamp."""
        patient = await self.repo.get_by_id(patient_id)
        if not patient:
            return False

        await self.repo.soft_delete(patient)
        logger.info("Patient soft-deleted: id={}", patient_id)
        return True

    async def get_dashboard_metrics(self) -> dict:
        """Retrieve aggregated counts for companion dashboard."""
        return await self.repo.count_metrics()
