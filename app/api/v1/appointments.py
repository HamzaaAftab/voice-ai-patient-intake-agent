from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.schemas.envelope import ApiResponse
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post(
    "",
    response_model=ApiResponse[AppointmentResponse],
    summary="Schedule an appointment for a patient",
    status_code=status.HTTP_201_CREATED,
)
async def schedule_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AppointmentResponse]:
    """Book a new clinical visit for a registered patient."""
    service = AppointmentService(db)
    appointment = await service.schedule_appointment(payload)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{payload.patient_id}' not found.",
        )
    return ApiResponse.success_response(AppointmentResponse.model_validate(appointment))


@router.get(
    "/patient/{patient_id}",
    response_model=ApiResponse[List[AppointmentResponse]],
    summary="List all appointments for a patient",
    status_code=status.HTTP_200_OK,
)
async def list_patient_appointments(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[AppointmentResponse]]:
    """Retrieve all scheduled appointments for a given patient UUID."""
    service = AppointmentService(db)
    appointments = await service.list_patient_appointments(patient_id)
    data = [AppointmentResponse.model_validate(a) for a in appointments]
    return ApiResponse.success_response(data)
