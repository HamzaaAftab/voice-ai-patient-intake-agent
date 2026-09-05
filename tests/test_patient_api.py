import pytest
from httpx import AsyncClient
from app.models.patient import Patient


@pytest.mark.asyncio
async def test_list_patients_empty(client: AsyncClient):
    """Verify listing patients when database is empty returns empty data array."""
    res = await client.get("/patients")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["error"] is None
    assert json_data["data"] == []


@pytest.mark.asyncio
async def test_create_patient_success(client: AsyncClient):
    """Verify creating a valid patient returns 201 with generated UUID and valid envelope."""
    payload = {
        "first_name": "Gregory",
        "last_name": "House",
        "date_of_birth": "1959-06-11",
        "sex": "Male",
        "phone_number": "6095550143",
        "address_line_1": "221B Baker Street",
        "city": "Princeton",
        "state": "NJ",
        "zip_code": "08540",
        "email": "drhouse@princetonplainsboro.com",
    }
    res = await client.post("/patients", json=payload)
    assert res.status_code == 201
    json_data = res.json()
    assert json_data["error"] is None
    data = json_data["data"]
    assert data["first_name"] == "Gregory"
    assert data["last_name"] == "House"
    assert data["state"] == "NJ"
    assert "patient_id" in data
    assert data["patient_id"] is not None


@pytest.mark.asyncio
async def test_get_patient_by_id(client: AsyncClient, sample_patient: Patient):
    """Verify retrieving an existing patient by UUID."""
    res = await client.get(f"/patients/{sample_patient.patient_id}")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["error"] is None
    assert json_data["data"]["patient_id"] == sample_patient.patient_id
    assert json_data["data"]["first_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_patient_not_found(client: AsyncClient):
    """Verify non-existent UUID returns 404 with error envelope."""
    res = await client.get("/patients/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404
    json_data = res.json()
    assert json_data["data"] is None
    assert json_data["error"] is not None
    assert json_data["error"]["code"] == "HTTP_ERROR"


@pytest.mark.asyncio
async def test_update_patient_partial(client: AsyncClient, sample_patient: Patient):
    """Verify partial updates modifying only selected fields."""
    update_payload = {
        "city": "Oakland",
        "zip_code": "94601",
    }
    res = await client.put(f"/patients/{sample_patient.patient_id}", json=update_payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["city"] == "Oakland"
    assert data["zip_code"] == "94601"
    assert data["first_name"] == "Alice"  # Unchanged field remains intact


@pytest.mark.asyncio
async def test_filter_patients_by_query_params(client: AsyncClient, sample_patient: Patient):
    """Verify query filtering by last_name and phone_number."""
    # Match
    res = await client.get(f"/patients?last_name=Johnson")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1

    # Non-match
    res_none = await client.get(f"/patients?last_name=NonExistent")
    assert res_none.status_code == 200
    assert len(res_none.json()["data"]) == 0


@pytest.mark.asyncio
async def test_reject_duplicate_phone_number(client: AsyncClient, sample_patient: Patient):
    """Verify POST /patients rejects duplicate phone number with 409 Conflict when active record exists."""
    payload = {
        "first_name": "Bob",
        "last_name": "Smith",
        "date_of_birth": "1988-02-14",
        "sex": "Male",
        "phone_number": sample_patient.phone_number,  # Duplicate phone of active patient!
        "address_line_1": "100 Pine Street",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94111",
    }
    # 1. Active duplicate rejection
    res = await client.post("/patients", json=payload)
    assert res.status_code == 409
    json_data = res.json()
    assert json_data["data"] is None
    assert json_data["error"]["code"] == "HTTP_ERROR"
    assert "already exists" in json_data["error"]["message"]

    # 2. Soft-delete the original patient
    del_res = await client.delete(f"/patients/{sample_patient.patient_id}")
    assert del_res.status_code == 200

    # 3. Now the phone number can be registered again because the old record is soft-deleted
    res_reused = await client.post("/patients", json=payload)
    assert res_reused.status_code == 201
    assert res_reused.json()["data"]["first_name"] == "Bob"

