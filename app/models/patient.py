import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    String,
    Date,
    DateTime,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import SexEnum

if TYPE_CHECKING:
    from app.models.call_log import CallLog
    from app.models.appointment import Appointment


def get_utc_now() -> datetime:
    """Generate current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Patient(Base):
    """Clinical Patient Demographic entity."""

    __tablename__ = "patients"

    # Primary Key
    patient_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique UUID primary key identifier",
    )

    # Required Demographic Fields
    first_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Legal first name",
    )
    last_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Legal last name",
    )
    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date of birth (enforced <= current date)",
    )
    sex: Mapped[SexEnum] = mapped_column(
        SQLEnum(SexEnum, name="sex_enum", native_enum=False),
        nullable=False,
        doc="Biological sex or intake preference",
    )
    phone_number: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
        doc="Normalized 10-digit U.S. telephone number",
    )
    address_line_1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Primary street address",
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="City name",
    )
    state: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        doc="Official 2-letter U.S. state code",
    )
    zip_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="5-digit or 9-digit ZIP+4 code",
    )

    # Optional Demographic Fields
    address_line_2: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        doc="Apartment, suite, or unit number",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Contact email address",
    )
    insurance_provider: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        doc="Health insurance carrier name",
    )
    insurance_member_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        doc="Insurance policy or subscriber ID",
    )
    preferred_language: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="English",
        doc="Preferred spoken/written language",
    )
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        doc="Designated emergency contact full name",
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        default=None,
        doc="Emergency contact 10-digit phone number",
    )

    # Audit Timestamps & Soft Deletion
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        doc="Record creation timestamp in UTC",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
        doc="Record last update timestamp in UTC",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
        doc="Soft-delete timestamp; null indicates active record",
    )

    # Relationships (Bonus Features)
    call_logs: Mapped[List["CallLog"]] = relationship(
        "CallLog",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Composite & Performance Indexes
    __table_args__ = (
        Index("ix_patients_phone_deleted", "phone_number", "deleted_at"),
        Index("ix_patients_last_name_deleted", "last_name", "deleted_at"),
        Index(
            "uq_active_patients_phone",
            "phone_number",
            unique=True,
            sqlite_where=deleted_at.is_(None),
            postgresql_where=deleted_at.is_(None),
        ),
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.patient_id}, name={self.first_name} {self.last_name}, phone={self.phone_number})>"
