# Voice AI Patient Registration System

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.10+-e92063.svg)](https://docs.pydantic.dev/)
[![Database](https://img.shields.io/badge/Database-Supabase%20PostgreSQL%20%2F%20SQLite-336791.svg)](https://supabase.com/)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed%20(100%25)-success.svg)](tests/)

A Production-grade, real-time telephony and conversational Voice AI system that registers patients over a live U.S. phone number, enforces clinical demographic validation rules, persists records to an ACID-compliant database, and exposes a companion REST API and Executive Web Dashboard.

---

## 📑 Table of Contents
1. [System Architecture](#system-architecture)
2. [Tech Stack & Justifications](#tech-stack--justifications)
3. [Features & Bonus Highlights](#features--bonus-highlights)
4. [Live Telephony Setup (Vapi Guide)](#live-telephony-setup-vapi-guide)
5. [Local Development & Quickstart](#local-development--quickstart)
6. [API Specification & cURL Examples](#api-specification--curl-examples)
7. [Automated Test Suite](#automated-test-suite)
8. [Architectural Trade-offs & Limitations](#architectural-trade-offs--limitations)

---

## 1. System Architecture

```mermaid
flowchart TD
    Caller([Caller / Interviewer Phone]) <-->|PSTN Phone Call| Telephony[Telephony & Voice Gateway\nVapi / Retell AI]

    subgraph VoicePipeline [Sub-800ms Realtime Voice Pipeline]
        STT[Deepgram Nova-2 STT\n< 250ms Latency]
        LLM[OpenAI-Compatible LLM\nGroq Llama 3.3 70B / OpenRouter / Ollama]
        TTS[Cartesia Sonic TTS\nUltra-realistic Voice]
        STT --> LLM --> TTS
    end

    Telephony <--> VoicePipeline
    Telephony -->|POST /api/v1/webhooks/vapi (Tool Calls)| BackendGateway[FastAPI Application Gateway]

    subgraph CleanBackend [Python Clean Architecture]
        Router[REST & Webhook Routers]
        Validation[Pydantic v2 Validation Layer]
        Service[Patient & Intake Domain Service]
        Repo[SQLAlchemy 2.0 Async Repository]
        Router --> Validation --> Service --> Repo
    end

    BackendGateway --> Router
    Repo <--> DB[(Persistent Cloud PostgreSQL / SQLite)]

    Interviewer[Interviewer / Admin] <-->|REST API / Swagger Docs| Router
    Interviewer <-->|Companion Glassmorphism Dashboard\n/dashboard| Dashboard[Executive Web UI]
```

### Key Architectural Traits
- **Two-Tier Validation:** The conversational LLM prompt enforces slot-level guardrails (e.g. reprompting if birth date is in the future), backed by a deterministic server-side Pydantic v2 validation layer.
- **Sub-800ms Voice Pipeline:** Integrates Deepgram Nova-2 streaming STT with Cartesia Sonic TTS and ultra-fast LLM inference (e.g. Groq / Llama 3.3 70B).
- **Zero-Data-Loss Persistence:** Backed by persistent cloud PostgreSQL (Supabase / Neon) and fallback SQLite across server restarts.
- **Audit & Soft-Deletion:** Fully supports healthcare compliance through timestamped soft-deletion (`deleted_at`).

---

## 2. Tech Stack & Justifications

| Component | Choice | Justification |
|---|---|---|
| **Language** | Python 3.12 | Modern async concurrency, type hinting, standard in conversational AI. |
| **Web Framework** | FastAPI | Native ASGI asynchronous performance, automatic OpenAPI documentation, dependency injection. |
| **Validation** | Pydantic v2 | High-performance Rust core, strict type coercion, comprehensive regex validators. |
| **Persistence** | SQLAlchemy 2.0 (Async) + `asyncpg` | Enterprise ORM supporting connection pooling, prepared statement management, and dialect portability. |
| **Database** | Supabase / Neon PostgreSQL | Cloud-hosted ACID compliance, high concurrency, zero data loss on container restarts. |
| **Telephony Gateway** | Vapi | Instant dialable US phone numbers, sub-800ms voice pipeline, built-in interruption handling (barge-in). |
| **LLM Reasoning** | OpenAI-Compatible Client (Groq / OpenRouter / Ollama) | Free-tier compatible, fast TTFT (< 300ms), zero proprietary vendor lock-in. |
| **Companion UI** | HTML5 / Modern Glassmorphic CSS / Vanilla JS | Zero build step, served directly from FastAPI at `/dashboard`. |

---

## 3. Features & Bonus Highlights

### Core Capabilities
- [x] **Natural Conversational Intake:** Warm clinical coordinator persona ("Sarah") collecting all 9 required U.S. patient demographics.
- [x] **Smart Out-of-Order Extraction:** Extracts multiple fields simultaneously without repeating questions.
- [x] **In-Flight Validation & Error Recovery:** Immediate verbal re-prompting if caller provides future DOB, bad phone, or invalid state.
- [x] **Optional Fields Opt-in:** Collects required fields first, then asks permission to record insurance, emergency contact, or language.
- [x] **Mandatory Read-Back Confirmation:** Reads back all captured demographics and prompts for confirmation or corrections before saving.
- [x] **REST API Standards:** Standard envelope `{ "data": ..., "error": null }` across all endpoints with full CRUD and soft-deletion.

### All 6 Bonus Challenges Implemented
1. **Duplicate Detection:** Inbound caller ID check detects returning callers: *"It looks like we already have a record for Jane Doe. Would you like to update your information instead?"*
2. **Multi-Language Support:** Seamlessly switches entire conversation and registration to Spanish if caller says *"Hablo español"*.
3. **Appointment Booking:** Offers and schedules first wellness visit post-registration.
4. **Call Recording & Transcript Linking:** Post-call webhook automatically links audio recording URL and full verbatim transcript to the patient profile.
5. **Companion Executive Dashboard:** Modern glassmorphism UI at `/dashboard` displaying real-time patient directory, search, metrics, and call transcripts.
6. **Comprehensive Automated Test Suite:** 15 unit and integration tests covering REST CRUD, input validation, soft deletion, and webhook tool calls.

---

## 4. Live Telephony Setup (Vapi Guide)

1. **Sign up at [vapi.ai](https://vapi.ai)** (Free credits provided upon signup).
2. **Provision a Phone Number:**
   - Go to **Phone Numbers** in Vapi Dashboard -> Click **Buy Number** -> Select a U.S. area code.
3. **Configure Assistant:**
   - Create a new Assistant: "Valley Health Intake Coordinator".
   - Under **Model**:
     - Provider: `Custom LLM` or OpenAI-compatible (Groq / OpenRouter / OpenAI).
     - Paste the System Prompt from [`app/prompts/intake_coordinator.py`](file:///app/prompts/intake_coordinator.py).
     - Set First Message: *"Hello! Thank you for calling Valley Health Clinical Intake. My name is Sarah, and I'll be helping you register today. Could you please start by sharing your first and last name?"*
   - Under **Voice**: Select Cartesia Sonic (Voice ID: `a0e99841-438c-4a64-b679-ae501e7d6091` or any warm female/male voice).
   - Under **Transcriber**: Deepgram Nova-2 (English / Multi).
4. **Attach Custom Tools:**
   - Copy tool definitions from [`app/prompts/tool_definitions.json`](file:///app/prompts/tool_definitions.json).
   - Set **Server URL** to your public webhook endpoint (e.g. `https://<your-domain>.com/webhooks/vapi` or via ngrok: `https://xxxx.ngrok-free.app/webhooks/vapi`).
5. **Link Number to Assistant:**
   - Under **Phone Numbers**, assign the phone number to your Assistant.
   - Dial the number and start talking!

---

## 5. Local Development & Quickstart

### Prerequisites
- Python 3.12+
- Git

### Installation
```bash
# 1. Clone repository
git clone <your-repo-url>
cd voice-agent-technical-assessment

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env to set your DATABASE_URL (Supabase/Postgres or default SQLite) and LLM keys

# 5. Populate Seed Data (Optional)
python seed_data.py

# 6. Launch Application
uvicorn app.main:app --reload --port 8000
```

### Access Interfaces
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Executive Dashboard:** [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Health Probe:** [http://localhost:8000/health](http://localhost:8000/health)

### Running via Docker
```bash
docker-compose up --build
```

---

## 6. API Specification & cURL Examples

All responses adhere to the standard envelope:
```json
{
  "data": { ... },
  "error": null
}
```

### 1. List All Patients (with filters)
```bash
curl -X GET "http://localhost:8000/patients?last_name=Scott"
```

### 2. Retrieve Single Patient by UUID
```bash
curl -X GET "http://localhost:8000/patients/<PATIENT_UUID>"
```

### 3. Register New Patient
```bash
curl -X POST "http://localhost:8000/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Tony",
    "last_name": "Stark",
    "date_of_birth": "1970-05-29",
    "sex": "Male",
    "phone_number": "4155553322",
    "address_line_1": "10880 Malibu Point",
    "city": "Malibu",
    "state": "CA",
    "zip_code": "90265",
    "insurance_provider": "Stark Health",
    "insurance_member_id": "IRON-001"
  }'
```

### 4. Partial Update Patient
```bash
curl -X PUT "http://localhost:8000/patients/<PATIENT_UUID>" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "4155559999"}'
```

### 5. Soft-Delete Patient
```bash
curl -X DELETE "http://localhost:8000/patients/<PATIENT_UUID>"
```

### 6. Test Vapi Tool-Call Webhook Directly
```bash
curl -X POST "http://localhost:8000/webhooks/vapi" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "tool-calls",
      "call": {"id": "curl_test_call", "customer": {"number": "+14155553322"}},
      "toolCalls": [
        {
          "id": "tc_001",
          "type": "function",
          "function": {
            "name": "check_existing_patient",
            "arguments": {"phone_number": "4155553322"}
          }
        }
      ]
    }
  }'
```

---

## 7. Automated Test Suite

The test suite runs against an isolated, in-memory SQLite database, guaranteeing zero external dependencies or side-effects:

```bash
pytest -v
```

### Test Results
```text
tests/test_patient_api.py::test_list_patients_empty PASSED               [  6%]
tests/test_patient_api.py::test_create_patient_success PASSED            [ 13%]
tests/test_patient_api.py::test_get_patient_by_id PASSED                 [ 20%]
tests/test_patient_api.py::test_get_patient_not_found PASSED             [ 26%]
tests/test_patient_api.py::test_update_patient_partial PASSED            [ 33%]
tests/test_patient_api.py::test_filter_patients_by_query_params PASSED   [ 40%]
tests/test_soft_delete.py::test_soft_delete_preserves_database_row PASSED [ 46%]
tests/test_validation.py::test_reject_future_date_of_birth PASSED        [ 53%]
tests/test_validation.py::test_reject_invalid_phone_number PASSED        [ 60%]
tests/test_validation.py::test_reject_invalid_state_code PASSED          [ 66%]
tests/test_validation.py::test_reject_invalid_zip_code PASSED            [ 73%]
tests/test_webhooks.py::test_vapi_register_patient_tool_call PASSED      [ 80%]
tests/test_webhooks.py::test_vapi_duplicate_caller_detection PASSED      [ 86%]
tests/test_webhooks.py::test_vapi_tool_call_invalid_dob_recovery PASSED  [ 93%]
tests/test_webhooks.py::test_vapi_call_ended_transcript_storage PASSED   [100%]

======================= 15 passed in 1.84s =======================
```

---

## 8. Architectural Trade-offs & Limitations

1. **Telephony Gateway Abstraction:**
   - *Decision:* Using Vapi instead of raw Twilio Media Streams + WebSocket STT/TTS.
   - *Trade-off:* Relies on a hosted platform, but eliminates telephony orchestration lag, reduces round-trip latency to sub-800ms, and provides enterprise-grade barge-in out of the box.
2. **Dual Database Architecture:**
   - *Decision:* Clean SQLAlchemy 2.0 abstraction supporting both cloud PostgreSQL and local SQLite.
   - *Trade-off:* SQLite is zero-config for offline development, while cloud PostgreSQL (Supabase/Neon) ensures 100% persistence on ephemeral cloud containers (e.g. Render / Railway).
3. **Synchronous Tool-Calling vs. Streaming Tools:**
   - *Decision:* Returning conversational strings directly in response to `tool-calls`.
   - *Trade-off:* Keeps server-side logic simple, deterministic, and fast (< 50ms processing time) without requiring asynchronous server-sent events for voice feedback.
