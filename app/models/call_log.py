import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    String,
    DateTime,
    Integer,
    Text,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import CallStatusEnum

if TYPE_CHECKING:
    from app.models.patient import Patient


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CallLog(Base):
    """Telephony call session metadata and transcript record."""

    __tablename__ = "call_logs"

    log_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("patients.patient_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated patient registered or referenced during call",
    )
    call_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Telephony provider unique call session ID (e.g. Vapi call ID)",
    )
    caller_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Caller ID phone number",
    )
    status: Mapped[CallStatusEnum] = mapped_column(
        SQLEnum(CallStatusEnum, name="call_status_enum", native_enum=False),
        nullable=False,
        default=CallStatusEnum.COMPLETED,
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Call duration in seconds",
    )
    recording_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="URL to listen to or download call audio recording",
    )
    transcript: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Full speech-to-text dialogue transcript",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
    )

    # Relationships
    patient: Mapped[Optional["Patient"]] = relationship(
        "Patient",
        back_populates="call_logs",
    )

    def __repr__(self) -> str:
        return f"<CallLog(id={self.log_id}, call_id={self.call_id}, caller={self.caller_phone})>"
