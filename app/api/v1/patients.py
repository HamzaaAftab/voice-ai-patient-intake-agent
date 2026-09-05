from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.envelope import ApiErrorDetail, ApiResponse
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "",
    response_model=ApiResponse[List[PatientResponse]],
    summary="List all patients with optional query filters",
    status_code=status.HTTP_200_OK,
)
async def list_patients(
    last_name: Optional[str] = Query(None, description="Filter by last name (case-insensitive)"),
    date_of_birth: Optional[date] = Query(None, description="Filter by date of birth (YYYY-MM-DD)"),
    phone_number: Optional[str] = Query(None, description="Filter by 10-digit U.S. phone number"),
    include_deleted: bool = Query(False, description="Include soft-deleted records"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[PatientResponse]]:
    """Retrieve all patients with support for optional query parameter filtering:
    `?last_name=`, `?date_of_birth=`, `?phone_number=`.
    """
    service = PatientService(db)
    patients, _ = await service.list_patients(
        last_name=last_name,
        date_of_birth=date_of_birth,
        phone_number=phone_number,
        include_deleted=include_deleted,
        offset=offset,
        limit=limit,
    )
    data = [PatientResponse.model_validate(p) for p in patients]
    return ApiResponse.success_response(data)


@router.get(
    "/metrics/summary",
    response_model=ApiResponse[dict],
    summary="Retrieve aggregated registration metrics",
    status_code=status.HTTP_200_OK,
)
async def get_patient_metrics(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Return aggregated patient registration counts for dashboards and monitoring."""
    service = PatientService(db)
    metrics = await service.get_dashboard_metrics()
    return ApiResponse.success_response(metrics)


@router.get(
    "/{id}",
    response_model=ApiResponse[PatientResponse],
    summary="Retrieve a single patient by UUID",
    status_code=status.HTTP_200_OK,
)
async def get_patient(
    id: str,
    include_deleted: bool = Query(False, description="Allow retrieving soft-deleted record"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PatientResponse]:
    """Retrieve a single patient by `patient_id` (UUID)."""
    service = PatientService(db)
    patient = await service.get_patient_by_id(id, include_deleted=include_deleted)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{id}' not found or has been deleted.",
        )
    return ApiResponse.success_response(PatientResponse.model_validate(patient))


@router.post(
    "",
    response_model=ApiResponse[PatientResponse],
    summary="Create a new patient record",
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
    payload: PatientCreate,
    allow_duplicate: bool = Query(False, description="Bypass duplicate phone check"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PatientResponse]:
    """Create a new patient record. Validates all inputs server-side and enforces duplicate detection."""
    service = PatientService(db)
    saved_patient, existing = await service.register_patient(payload, allow_duplicate=allow_duplicate)
    if not saved_patient:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An active patient record already exists with phone number '{payload.phone_number}' "
                f"(Patient ID: {existing.patient_id}, Name: {existing.first_name} {existing.last_name}). "
                f"Use PUT /patients/{existing.patient_id} to update their record."
            ),
        )
    return ApiResponse.success_response(PatientResponse.model_validate(saved_patient))


@router.put(
    "/{id}",
    response_model=ApiResponse[PatientResponse],
    summary="Update an existing patient record",
    status_code=status.HTTP_200_OK,
)
async def update_patient(
    id: str,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PatientResponse]:
    """Update an existing patient record. Partial updates are allowed."""
    service = PatientService(db)
    updated_patient = await service.update_patient(id, payload)
    if not updated_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{id}' not found.",
        )
    return ApiResponse.success_response(PatientResponse.model_validate(updated_patient))


@router.delete(
    "/{id}",
    response_model=ApiResponse[dict],
    summary="Soft-delete a patient record",
    status_code=status.HTTP_200_OK,
)
async def delete_patient(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Soft-delete a patient record (sets `deleted_at` timestamp; does not hard-delete row)."""
    service = PatientService(db)
    success = await service.soft_delete_patient(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{id}' not found or already deleted.",
        )
    return ApiResponse.success_response(
        {
            "patient_id": id,
            "status": "soft_deleted",
            "message": "Patient record marked as inactive with timestamp.",
        }
    )
