import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.patient import Patient


@pytest.mark.asyncio
async def test_soft_delete_preserves_database_row(
    client: AsyncClient, db_session: AsyncSession, sample_patient: Patient
):
    """Verify DELETE /patients/:id sets deleted_at timestamp without dropping the database row."""
    patient_id = sample_patient.patient_id

    # Execute DELETE request
    res = await client.delete(f"/patients/{patient_id}")
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "soft_deleted"

    # Default GET /patients/:id should return 404
    get_res = await client.get(f"/patients/{patient_id}")
    assert get_res.status_code == 404

    # Default GET /patients should NOT list the soft-deleted patient
    list_res = await client.get("/patients")
    assert not any(p["patient_id"] == patient_id for p in list_res.json()["data"])

    # Allowing include_deleted=true retrieves the record
    deleted_get_res = await client.get(f"/patients/{patient_id}?include_deleted=true")
    assert deleted_get_res.status_code == 200
    assert deleted_get_res.json()["data"]["deleted_at"] is not None

    # Verify directly in database session that the row STILL exists (hard delete did not happen)
    stmt = select(Patient).where(Patient.patient_id == patient_id)
    raw_record = (await db_session.execute(stmt)).scalar_one_or_none()
    assert raw_record is not None
    assert raw_record.deleted_at is not None
    assert raw_record.first_name == "Alice"
