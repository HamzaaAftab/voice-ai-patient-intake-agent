import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import AppointmentStatusEnum

if TYPE_CHECKING:
    from app.models.patient import Patient


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Appointment(Base):
    """Clinical appointment booked for registered patient."""

    __tablename__ = "appointments"

    appointment_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Scheduled visit date and time",
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Dr. Sarah Smith, MD",
    )
    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="New Patient Intake & Wellness Consultation",
    )
    status: Mapped[AppointmentStatusEnum] = mapped_column(
        SQLEnum(AppointmentStatusEnum, name="appointment_status_enum", native_enum=False),
        nullable=False,
        default=AppointmentStatusEnum.SCHEDULED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="appointments",
    )

    def __repr__(self) -> str:
        return f"<Appointment(id={self.appointment_id}, patient_id={self.patient_id}, time={self.appointment_time})>"
