import json
from datetime import datetime, timezone
from typing import Any, Dict, Union
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.schemas.patient import PatientCreate, PatientUpdate
from app.schemas.appointment import AppointmentCreate
from app.services.patient_service import PatientService
from app.services.appointment_service import AppointmentService


class VoiceToolDispatcher:
    """Dispatches mid-call tool calls executed by the Voice AI Telephony Agent."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.patient_service = PatientService(session)
        self.appointment_service = AppointmentService(session)

    async def execute_tool(
        self, tool_name: str, raw_arguments: Union[Dict[str, Any], str], call_id: str = ""
    ) -> str:
        """Route tool call execution and return conversational feedback for the voice agent."""
        # Parse JSON arguments if provided as string
        if isinstance(raw_arguments, str):
            try:
                args = json.loads(raw_arguments)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse tool arguments JSON: {}", str(e))
                return "Error: Invalid JSON payload provided for tool execution."
        else:
            args = raw_arguments or {}

        logger.info(
            "Executing voice tool: '{}' for call_id='{}' with args keys: {}",
            tool_name,
            call_id,
            list(args.keys()),
        )

        handler_map = {
            "register_patient": self._handle_register_patient,
            "check_existing_patient": self._handle_check_existing_patient,
            "update_patient": self._handle_update_patient,
            "schedule_appointment": self._handle_schedule_appointment,
        }

        handler = handler_map.get(tool_name)
        if not handler:
            logger.warning("Unrecognized voice tool invoked: {}", tool_name)
            return f"Error: Tool '{tool_name}' is not recognized by the backend service."

        try:
            return await handler(args, call_id)
        except Exception as e:
            logger.exception("Unexpected error executing voice tool '{}': {}", tool_name, str(e))
            return (
                "We encountered an internal database issue while saving your information. "
                "Please apologize to the caller and ask them to call back in a few moments."
            )

    async def _link_call_to_patient(self, call_id: str, patient_id: str, phone: str = "") -> None:
        """Helper to ensure CallLog links to patient during voice tool execution."""
        if not call_id or call_id == "unknown_call":
            return
        from app.models.call_log import CallLog
        from app.models.enums import CallStatusEnum
        from app.repositories.call_log_repo import CallLogRepository

        call_repo = CallLogRepository(self.session)
        existing_log = await call_repo.get_by_call_id(call_id)
        if existing_log:
            existing_log.patient_id = patient_id
            self.session.add(existing_log)
        else:
            new_log = CallLog(
                call_id=call_id,
                caller_phone=phone or "unknown",
                patient_id=patient_id,
                status=CallStatusEnum.IN_PROGRESS,
            )
            await call_repo.create(new_log)

    async def _handle_register_patient(self, args: Dict[str, Any], call_id: str = "") -> str:
        """Process new patient registration from voice tool call."""
        try:
            payload = PatientCreate(**args)
        except ValidationError as val_err:
            errors = val_err.errors()
            first_err = errors[0] if errors else {}
            field = " -> ".join(str(loc) for loc in first_err.get("loc", []))
            msg = first_err.get("msg", "Invalid field value")
            logger.warning("Voice tool validation failed: field='{}', message='{}'", field, msg)
            return (
                f"Registration failed due to invalid data: {field}: {msg}. "
                f"Please re-prompt the caller specifically to correct their {field}."
            )

        saved_patient, existing = await self.patient_service.register_patient(payload)
        if not saved_patient:
            # Active duplicate detected!
            if existing and call_id:
                await self._link_call_to_patient(call_id, existing.patient_id, payload.phone_number)
            return (
                f"DUPLICATE_PHONE: An active record already exists for {existing.first_name} {existing.last_name} "
                f"with phone number {payload.phone_number}. "
                f"Please ask the caller: 'It looks like we already have a record for {existing.first_name} {existing.last_name}. "
                f"Would you like to update your existing record instead of registering a new patient?'"
            )

        # Link call to newly registered patient
        await self._link_call_to_patient(call_id, saved_patient.patient_id, saved_patient.phone_number)

        return (
            f"Success! Patient {saved_patient.first_name} {saved_patient.last_name} "
            f"has been successfully registered with patient ID {saved_patient.patient_id}. "
            f"You may now confirm to the caller: 'You're all set, {saved_patient.first_name}! "
            f"Your registration is complete.'"
        )

    async def _handle_check_existing_patient(self, args: Dict[str, Any], call_id: str = "") -> str:
        """Lookup existing patient by caller phone number (Bonus Feature)."""
        phone = args.get("phone_number") or ""
        if not phone:
            return "No phone number provided to check existing records."

        patient = await self.patient_service.find_by_phone(phone)
        if patient:
            await self._link_call_to_patient(call_id, patient.patient_id, phone)
            return (
                f"EXISTING_PATIENT_FOUND: We found an existing active record for "
                f"{patient.first_name} {patient.last_name} (Patient ID: {patient.patient_id}). "
                f"Ask the caller: 'It looks like we already have a record for {patient.first_name} {patient.last_name}. "
                f"Would you like to update your information instead, or register a new patient?'"
            )
        return "NO_EXISTING_PATIENT: No prior record found for this phone number. Proceed with new patient registration."

    async def _handle_update_patient(self, args: Dict[str, Any], call_id: str = "") -> str:
        """Process demographic updates for an existing patient."""
        patient_id = args.get("patient_id")
        if not patient_id:
            return "Error: patient_id is required to update a record."

        try:
            update_payload = PatientUpdate(**args)
        except ValidationError as val_err:
            return f"Update validation error: {str(val_err)}"

        updated = await self.patient_service.update_patient(patient_id, update_payload)
        if not updated:
            return f"Error: No active patient found with ID {patient_id}."

        await self._link_call_to_patient(call_id, updated.patient_id, updated.phone_number)
        return (
            f"Success! Patient record for {updated.first_name} {updated.last_name} "
            f"has been successfully updated."
        )

    async def _handle_schedule_appointment(self, args: Dict[str, Any], call_id: str = "") -> str:
        """Process first clinical appointment booking (Bonus Feature)."""
        try:
            payload = AppointmentCreate(**args)
        except ValidationError as val_err:
            return f"Appointment scheduling error: {str(val_err)}"

        appt = await self.appointment_service.schedule_appointment(payload)
        if not appt:
            return "Error: Unable to schedule appointment because the patient ID was not found."

        return (
            f"Appointment confirmed with {appt.provider_name} for "
            f"{appt.appointment_time.strftime('%A, %B %d at %I:%M %p')}. "
            f"Please inform the caller of their appointment."
        )
