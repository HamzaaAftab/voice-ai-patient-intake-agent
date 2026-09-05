import pytest
from httpx import AsyncClient
from app.models.patient import Patient


@pytest.mark.asyncio
async def test_vapi_register_patient_tool_call(client: AsyncClient):
    """Verify telephony agent successfully executes register_patient tool call."""
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "vapi_call_unit_test", "customer": {"number": "+14155553322"}},
            "toolCalls": [
                {
                    "id": "tc_001",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {
                            "first_name": "Tony",
                            "last_name": "Stark",
                            "date_of_birth": "1970-05-29",
                            "sex": "Male",
                            "phone_number": "4155553322",
                            "address_line_1": "10880 Malibu Point",
                            "city": "Malibu",
                            "state": "CA",
                            "zip_code": "90265",
                        },
                    },
                }
            ],
        }
    }

    res = await client.post("/webhooks/vapi", json=payload)
    assert res.status_code == 200
    results = res.json().get("results", [])
    assert len(results) == 1
    assert "Success! Patient Tony Stark" in results[0]["result"]

    # Verify patient now exists in REST API
    list_res = await client.get("/patients?last_name=Stark")
    assert len(list_res.json()["data"]) == 1


@pytest.mark.asyncio
async def test_vapi_duplicate_caller_detection(client: AsyncClient, sample_patient: Patient):
    """Verify duplicate detection by phone number (Bonus Feature)."""
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "vapi_call_dup_test"},
            "toolCalls": [
                {
                    "id": "tc_dup",
                    "type": "function",
                    "function": {
                        "name": "check_existing_patient",
                        "arguments": {"phone_number": sample_patient.phone_number},
                    },
                }
            ],
        }
    }

    res = await client.post("/webhooks/vapi", json=payload)
    assert res.status_code == 200
    result_text = res.json()["results"][0]["result"]
    assert "EXISTING_PATIENT_FOUND" in result_text
    assert "Alice Johnson" in result_text


@pytest.mark.asyncio
async def test_vapi_tool_call_invalid_dob_recovery(client: AsyncClient):
    """Verify agent receives re-prompt instruction when caller provides invalid future DOB."""
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "vapi_call_err_test"},
            "toolCalls": [
                {
                    "id": "tc_err",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {
                            "first_name": "Peter",
                            "last_name": "Parker",
                            "date_of_birth": "2035-01-01",  # Future date!
                            "sex": "Male",
                            "phone_number": "7185550199",
                            "address_line_1": "20 Ingram Street",
                            "city": "Forest Hills",
                            "state": "NY",
                            "zip_code": "11375",
                        },
                    },
                }
            ],
        }
    }

    res = await client.post("/webhooks/vapi", json=payload)
    assert res.status_code == 200
    result_text = res.json()["results"][0]["result"]
    assert "Registration failed due to invalid data" in result_text
    assert "date_of_birth" in result_text


@pytest.mark.asyncio
async def test_vapi_call_ended_transcript_storage(client: AsyncClient):
    """Verify post-call end-of-call-report stores full transcript and recording link."""
    payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {"id": "call_session_rec_123", "customer": {"number": "+14155559988"}},
            "recordingUrl": "https://api.vapi.ai/recordings/call_123.wav",
            "transcript": "Sarah: Hello, what is your name? Caller: Peter Parker.",
            "durationSeconds": 45,
        }
    }

    res = await client.post("/webhooks/vapi", json=payload)
    assert res.status_code == 200

    # Verify call log is accessible via GET /webhooks/call-logs
    logs_res = await client.get("/webhooks/call-logs")
    assert logs_res.status_code == 200
    logs = logs_res.json()["data"]
    matched = [l for l in logs if l["call_id"] == "call_session_rec_123"]
    assert len(matched) == 1


@pytest.mark.asyncio
async def test_vapi_call_ended_links_patient_from_caller_phone(
    client: AsyncClient, sample_patient: Patient
):
    """Verify post-call report automatically resolves and links patient_id from caller phone."""
    payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {"id": "call_linked_test_99", "customer": {"number": f"+1{sample_patient.phone_number}"}},
            "recordingUrl": "https://api.vapi.ai/recordings/call_99.wav",
            "transcript": "Caller: Hello I am Alice. Sarah: Welcome Alice.",
            "durationSeconds": 60,
        }
    }
    res = await client.post("/webhooks/vapi", json=payload)
    assert res.status_code == 200

    logs_res = await client.get("/webhooks/call-logs")
    assert logs_res.status_code == 200
    matched = [l for l in logs_res.json()["data"] if l["call_id"] == "call_linked_test_99"]
    assert len(matched) == 1
    assert matched[0]["patient_id"] == sample_patient.patient_id
    assert matched[0]["patient_name"] == f"{sample_patient.first_name} {sample_patient.last_name}"


@pytest.mark.asyncio
async def test_vapi_register_patient_duplicate_phone_tool_response(
    client: AsyncClient, sample_patient: Patient
):
    """Verify voice tool returns DUPLICATE_PHONE message when caller tries to register with existing phone."""
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "vapi_call_dup_tool_test"},
            "toolCalls": [
                {
                    "id": "tc_dup_tool",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {
                            "first_name": "Clone",
                            "last_name": "Alice",
                            "date_of_birth": "1995-08-24",
                            "sex": "Female",
                            "phone_number": sample_patient.phone_number,  # Existing phone!
                            "address_line_1": "123 Another St",
                            "city": "San Francisco",
                            "state": "CA",
                            "zip_code": "94102",
                        },
                    },
                }
            ],
        }
    }
    res = await client.post("/webhooks/vapi", json=payload)
    assert res.status_code == 200
    result_text = res.json()["results"][0]["result"]
    assert "DUPLICATE_PHONE" in result_text
    assert "Alice Johnson" in result_text

