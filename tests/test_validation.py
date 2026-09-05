from datetime import date, timedelta
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reject_future_date_of_birth(client: AsyncClient):
    """Verify server rejects future date of birth with 422 Unprocessable Entity."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "first_name": "Marty",
        "last_name": "McFly",
        "date_of_birth": tomorrow,
        "sex": "Male",
        "phone_number": "4155559999",
        "address_line_1": "9303 Lyon Drive",
        "city": "Hill Valley",
        "state": "CA",
        "zip_code": "95420",
    }
    res = await client.post("/patients", json=payload)
    assert res.status_code == 422
    json_data = res.json()
    assert json_data["data"] is None
    assert json_data["error"]["code"] == "VALIDATION_ERROR"
    # Check that error details mention date_of_birth
    issue_found = any("date_of_birth" in detail["field"] for detail in json_data["error"]["details"])
    assert issue_found


@pytest.mark.asyncio
async def test_reject_invalid_phone_number(client: AsyncClient):
    """Verify server rejects non-10-digit U.S. phone numbers."""
    payload = {
        "first_name": "Doc",
        "last_name": "Brown",
        "date_of_birth": "1950-01-01",
        "sex": "Male",
        "phone_number": "123",  # Invalid short phone
        "address_line_1": "1640 Riverside Drive",
        "city": "Hill Valley",
        "state": "CA",
        "zip_code": "95420",
    }
    res = await client.post("/patients", json=payload)
    assert res.status_code == 422
    assert "phone_number" in str(res.json()["error"]["details"])


@pytest.mark.asyncio
async def test_reject_invalid_state_code(client: AsyncClient):
    """Verify server rejects non-existent 2-letter U.S. state abbreviations."""
    payload = {
        "first_name": "Doc",
        "last_name": "Brown",
        "date_of_birth": "1950-01-01",
        "sex": "Male",
        "phone_number": "4155559999",
        "address_line_1": "1640 Riverside Drive",
        "city": "Hill Valley",
        "state": "ZZ",  # Invalid state
        "zip_code": "95420",
    }
    res = await client.post("/patients", json=payload)
    assert res.status_code == 422
    assert "state" in str(res.json()["error"]["details"])


@pytest.mark.asyncio
async def test_reject_invalid_zip_code(client: AsyncClient):
    """Verify server rejects malformed postal codes."""
    payload = {
        "first_name": "Doc",
        "last_name": "Brown",
        "date_of_birth": "1950-01-01",
        "sex": "Male",
        "phone_number": "4155559999",
        "address_line_1": "1640 Riverside Drive",
        "city": "Hill Valley",
        "state": "CA",
        "zip_code": "INVALID_ZIP",
    }
    res = await client.post("/patients", json=payload)
    assert res.status_code == 422
    assert "zip_code" in str(res.json()["error"]["details"])
