from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class VapiFunctionCall(BaseModel):
    name: str
    arguments: Union[Dict[str, Any], str]


class VapiToolCallItem(BaseModel):
    id: str
    type: str = "function"
    function: VapiFunctionCall


class VapiCustomer(BaseModel):
    number: Optional[str] = None
    name: Optional[str] = None


class VapiCallMetadata(BaseModel):
    id: Optional[str] = None
    customer: Optional[VapiCustomer] = None


class VapiMessagePayload(BaseModel):
    type: Optional[str] = None  # "tool-calls", "end-of-call-report", "status-update", etc.
    call: Optional[VapiCallMetadata] = None
    toolCalls: Optional[List[VapiToolCallItem]] = None
    # For end-of-call-report
    recordingUrl: Optional[str] = None
    transcript: Optional[str] = None
    durationSeconds: Optional[int] = 0
    endedReason: Optional[str] = None


class VapiWebhookPayload(BaseModel):
    """Payload received from Vapi server webhook."""
    message: VapiMessagePayload


class VapiToolCallResult(BaseModel):
    """Individual tool call execution result returned to Vapi assistant."""
    toolCallId: str
    result: str


class VapiToolCallResponse(BaseModel):
    """Container of results returned back to Vapi."""
    results: List[VapiToolCallResult]
