from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.core.security import verify_vapi_webhook
from app.database import get_db
from app.models.call_log import CallLog
from app.models.enums import CallStatusEnum
from app.repositories.call_log_repo import CallLogRepository
from app.schemas.envelope import ApiResponse
from app.schemas.webhooks import VapiToolCallResponse, VapiToolCallResult, VapiWebhookPayload
from app.services.voice_tools import VoiceToolDispatcher

router = APIRouter(prefix="/webhooks", tags=["Voice Webhooks"])


@router.post(
    "/vapi",
    summary="Primary Vapi telephony webhook endpoint for tool calls and call reports",
    status_code=status.HTTP_200_OK,
)
async def handle_vapi_webhook(
    request: Request,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _authorized: bool = Depends(verify_vapi_webhook),
) -> Any:
    """Handle all incoming Vapi telephony webhooks.
    
    Processes:
    1. 'tool-calls' (mid-call tool execution): executes register_patient, check_existing_patient, etc.
    2. 'end-of-call-report' (post-call): records call transcript and audio recording link.
    """
    message = payload.get("message", {})
    msg_type = message.get("type", "")
    call_data = message.get("call", {})
    call_id = call_data.get("id") or payload.get("callId") or "unknown_call"
    caller_phone = (
        call_data.get("customer", {}).get("number")
        or message.get("customer", {}).get("number")
        or "unknown"
    )

    logger.info(
        "Received Vapi webhook: type='{}', call_id='{}', caller='{}'",
        msg_type,
        call_id,
        caller_phone,
    )

    # 1. Mid-call Tool Calling Handler
    if msg_type == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        dispatcher = VoiceToolDispatcher(db)
        results: List[Dict[str, str]] = []

        for call_item in tool_calls:
            tool_call_id = call_item.get("id", "")
            func = call_item.get("function", {})
            name = func.get("name", "")
            arguments = func.get("arguments", {})

            result_str = await dispatcher.execute_tool(name, arguments, call_id=call_id)
            results.append({"toolCallId": tool_call_id, "result": result_str})

        return {"results": results}

    # 2. End-of-Call Report Handler (Transcript & Recording Storage)
    elif msg_type in ("end-of-call-report", "call-ended", "status-update"):
        recording_url = message.get("recordingUrl") or message.get("artifact", {}).get("recordingUrl")
        transcript = message.get("transcript") or message.get("artifact", {}).get("transcript")
        duration = int(message.get("durationSeconds") or 0)

        call_repo = CallLogRepository(db)
        from app.repositories.patient_repo import PatientRepository
        patient_repo = PatientRepository(db)
        existing_log = await call_repo.get_by_call_id(call_id)

        # Resolve patient_id from caller_phone if not already linked
        resolved_patient_id = None
        if caller_phone and caller_phone != "unknown":
            import re
            clean_phone = re.sub(r"\D", "", caller_phone)
            if len(clean_phone) == 11 and clean_phone.startswith("1"):
                clean_phone = clean_phone[1:]
            patient = await patient_repo.find_by_phone(clean_phone)
            if patient:
                resolved_patient_id = patient.patient_id

        if existing_log:
            target_pid = existing_log.patient_id or resolved_patient_id
            await call_repo.update_post_call(
                call_id=call_id,
                transcript=transcript,
                recording_url=recording_url,
                duration_seconds=duration,
                patient_id=target_pid,
            )
            logger.info("Updated existing call log for call_id='{}', linked patient_id='{}'", call_id, target_pid)
        else:
            new_log = CallLog(
                call_id=call_id,
                caller_phone=caller_phone,
                patient_id=resolved_patient_id,
                status=CallStatusEnum.COMPLETED,
                duration_seconds=duration,
                recording_url=recording_url,
                transcript=transcript,
            )
            await call_repo.create(new_log)
            logger.info("Created new call log record for call_id='{}', linked patient_id='{}'", call_id, resolved_patient_id)

        return {"status": "success", "message": "Call report processed"}

    # Default fallback
    return {"status": "acknowledged", "type": msg_type}


@router.get(
    "/call-logs",
    response_model=ApiResponse[List[dict]],
    summary="List recent call logs and transcripts",
    status_code=status.HTTP_200_OK,
)
async def list_call_logs(
    patient_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[dict]]:
    """Fetch call history including transcripts and audio recording links."""
    repo = CallLogRepository(db)
    logs = await repo.list_recent(patient_id=patient_id, limit=limit)
    data = [
        {
            "log_id": log.log_id,
            "patient_id": log.patient_id,
            "patient_name": f"{log.patient.first_name} {log.patient.last_name}" if log.patient else "Unregistered Caller",
            "call_id": log.call_id,
            "caller_phone": log.caller_phone,
            "status": log.status,
            "duration_seconds": log.duration_seconds,
            "recording_url": log.recording_url,
            "transcript": log.transcript,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
    return ApiResponse.success_response(data)
