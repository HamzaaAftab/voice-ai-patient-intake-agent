from enum import Enum


class SexEnum(str, Enum):
    """Permitted biological sex values according to clinical intake standard."""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    DECLINE_TO_ANSWER = "Decline to Answer"


class LanguageEnum(str, Enum):
    """Primary communication language."""
    ENGLISH = "English"
    SPANISH = "Spanish"
    OTHER = "Other"


class CallStatusEnum(str, Enum):
    """Telephony call lifecycle status."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AppointmentStatusEnum(str, Enum):
    """Clinical appointment status."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
