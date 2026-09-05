import re
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.enums import SexEnum

# 50 US States + DC + Territories
VALID_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP"
}

NAME_REGEX = re.compile(r"^[A-Za-z\s'\-]+$")
ZIP_REGEX = re.compile(r"^\d{5}(-\d{4})?$")


def clean_and_validate_us_phone(v: Optional[str], field_name: str = "phone_number") -> Optional[str]:
    """Clean phone number and validate standard 10-digit U.S. NANP format."""
    if v is None:
        return None
    # Strip all non-numeric characters
    digits = re.sub(r"\D", "", str(v))
    # Strip leading country code 1 if 11 digits
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError(
            f"{field_name} must be a valid 10-digit U.S. phone number. Received {len(digits)} digits."
        )
    # North American Numbering Plan: area code cannot start with 0 or 1
    if digits[0] in ("0", "1"):
        raise ValueError(
            f"{field_name} has an invalid area code (cannot start with {digits[0]})."
        )
    return digits


class PatientBase(BaseModel):
    """Base demographic fields."""
    first_name: str = Field(..., min_length=1, max_length=50, description="Legal first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Legal last name")
    date_of_birth: date = Field(..., description="Date of birth (YYYY-MM-DD or MM/DD/YYYY)")
    sex: SexEnum = Field(..., description="Sex: Male, Female, Other, Decline to Answer")
    phone_number: str = Field(..., description="Valid 10-digit U.S. phone number")
    address_line_1: str = Field(..., min_length=1, max_length=255, description="Street address")
    address_line_2: Optional[str] = Field(None, max_length=100, description="Apt, Suite, Unit")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(..., min_length=2, max_length=2, description="2-letter U.S. state abbreviation")
    zip_code: str = Field(..., description="5-digit or ZIP+4 postal code")
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    insurance_provider: Optional[str] = Field(None, max_length=100, description="Health insurance provider name")
    insurance_member_id: Optional[str] = Field(None, max_length=100, description="Insurance subscriber ID")
    preferred_language: str = Field("English", max_length=50, description="Preferred language")
    emergency_contact_name: Optional[str] = Field(None, max_length=100, description="Emergency contact full name")
    emergency_contact_phone: Optional[str] = Field(None, description="Emergency contact 10-digit phone")

    @field_validator("first_name", "last_name", mode="after")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not NAME_REGEX.match(v):
            raise ValueError("Name must contain only alphabetic characters, spaces, hyphens, and apostrophes.")
        return v.title()

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def parse_and_validate_dob(cls, v: object) -> date:
        if isinstance(v, str):
            # Support MM/DD/YYYY as well as YYYY-MM-DD
            v = v.strip()
            if "/" in v:
                try:
                    parts = v.split("/")
                    if len(parts) == 3:
                        # MM/DD/YYYY
                        return date(int(parts[2]), int(parts[0]), int(parts[1]))
                except Exception:
                    pass
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid date format. Expected YYYY-MM-DD or MM/DD/YYYY.")

        if isinstance(v, date):
            today = date.today()
            if v > today:
                raise ValueError(f"Date of birth cannot be in the future. Received {v}, today is {today}.")
            return v
        raise ValueError("Invalid date of birth.")

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        res = clean_and_validate_us_phone(v, "phone_number")
        if not res:
            raise ValueError("phone_number is required.")
        return res

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        return clean_and_validate_us_phone(v, "emergency_contact_phone")

    @field_validator("state", mode="after")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in VALID_US_STATES:
            raise ValueError(
                f"'{v}' is not a valid 2-letter U.S. state abbreviation."
            )
        return v_upper

    @field_validator("zip_code", mode="after")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        v_clean = v.strip()
        if not ZIP_REGEX.match(v_clean):
            raise ValueError(
                f"'{v}' is not a valid U.S. ZIP code. Expected 5 digits (e.g. 90210) or ZIP+4 (e.g. 90210-1234)."
            )
        return v_clean


class PatientCreate(PatientBase):
    """Schema for registering a new patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for partial update of an existing patient (all fields optional)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    sex: Optional[SexEnum] = None
    phone_number: Optional[str] = None
    address_line_1: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    zip_code: Optional[str] = None
    email: Optional[EmailStr] = None
    insurance_provider: Optional[str] = Field(None, max_length=100)
    insurance_member_id: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, max_length=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name", mode="after")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not NAME_REGEX.match(v):
            raise ValueError("Name must contain only alphabetic characters, spaces, hyphens, and apostrophes.")
        return v.title()

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def parse_and_validate_dob(cls, v: object) -> Optional[date]:
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if "/" in v:
                try:
                    parts = v.split("/")
                    if len(parts) == 3:
                        return date(int(parts[2]), int(parts[0]), int(parts[1]))
                except Exception:
                    pass
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid date format. Expected YYYY-MM-DD or MM/DD/YYYY.")
        if isinstance(v, date):
            today = date.today()
            if v > today:
                raise ValueError(f"Date of birth cannot be in the future. Received {v}, today is {today}.")
            return v
        return None

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return clean_and_validate_us_phone(v, "phone_number")

    @field_validator("state", mode="after")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_upper = v.strip().upper()
        if v_upper not in VALID_US_STATES:
            raise ValueError(f"'{v}' is not a valid 2-letter U.S. state abbreviation.")
        return v_upper

    @field_validator("zip_code", mode="after")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip()
        if not ZIP_REGEX.match(v_clean):
            raise ValueError(f"'{v}' is not a valid U.S. ZIP code.")
        return v_clean


class PatientResponse(PatientBase):
    """Schema returned by API endpoints representing persisted patient record."""
    patient_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
