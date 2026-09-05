import asyncio
from datetime import date, datetime, timezone
from app.database import AsyncSessionLocal, init_db
from app.models.enums import SexEnum
from app.models.patient import Patient
from app.core.logging import logger


async def seed_database() -> None:
    """Populate database with realistic clinical demonstration patient records."""
    logger.info("Starting database seeding...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if records already exist
        from sqlalchemy import select
        result = await session.execute(select(Patient))
        existing = result.scalars().first()
        if existing:
            logger.info("Database already has patient records. Seeding skipped.")
            return

        seed_patients = [
            Patient(
                first_name="Jane",
                last_name="Doe",
                date_of_birth=date(1992, 5, 14),
                sex=SexEnum.FEMALE,
                phone_number="4155552671",
                address_line_1="100 California Street",
                address_line_2="Suite 400",
                city="San Francisco",
                state="CA",
                zip_code="94111",
                email="jane.doe@example.com",
                insurance_provider="Blue Cross Blue Shield",
                insurance_member_id="BCBS-987654321",
                preferred_language="English",
                emergency_contact_name="John Doe",
                emergency_contact_phone="4155559876",
            ),
            Patient(
                first_name="Michael",
                last_name="Scott",
                date_of_birth=date(1965, 3, 15),
                sex=SexEnum.MALE,
                phone_number="5705550199",
                address_line_1="1725 Slough Avenue",
                city="Scranton",
                state="PA",
                zip_code="18503",
                email="mscott@dundermifflin.com",
                insurance_provider="Aetna Healthcare",
                insurance_member_id="AETNA-44332211",
                preferred_language="English",
                emergency_contact_name="Dwight Schrute",
                emergency_contact_phone="5705550144",
            ),
            Patient(
                first_name="Carlos",
                last_name="Ramirez",
                date_of_birth=date(1988, 11, 20),
                sex=SexEnum.MALE,
                phone_number="3055558912",
                address_line_1="742 Ocean Drive",
                address_line_2="Apt 12B",
                city="Miami",
                state="FL",
                zip_code="33139",
                email="carlos.ramirez@example.com",
                insurance_provider="UnitedHealthcare",
                insurance_member_id="UHC-88776655",
                preferred_language="Spanish",
                emergency_contact_name="Maria Ramirez",
                emergency_contact_phone="3055559988",
            ),
            # Inactive / Soft-deleted record for verification
            Patient(
                first_name="Inactive",
                last_name="TestPatient",
                date_of_birth=date(1980, 1, 1),
                sex=SexEnum.OTHER,
                phone_number="2125550000",
                address_line_1="500 Broadway",
                city="New York",
                state="NY",
                zip_code="10012",
                deleted_at=datetime.now(timezone.utc),
            ),
        ]

        for p in seed_patients:
            session.add(p)

        await session.commit()
        logger.info("Successfully inserted {} demonstration patient records.", len(seed_patients))


if __name__ == "__main__":
    asyncio.run(seed_database())
