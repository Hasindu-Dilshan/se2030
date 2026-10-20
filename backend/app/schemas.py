import re
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


# =====================================================================
# Room Schemas
# =====================================================================

class RoomBase(BaseModel):
    room_number: str = Field(..., examples=["201"])
    category: str = Field(..., examples=["Deluxe Double"])
    rate_per_night: float = Field(..., gt=0, examples=[140.0])
    max_capacity: int = Field(..., gt=0, examples=[2])


class RoomResponse(RoomBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# Tourist Schemas
# =====================================================================

class TouristBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, examples=["Alex Mercer"])
    nationality: str = Field(..., min_length=2, max_length=50, examples=["Canadian"])
    phone: str = Field(..., examples=["+1-555-0199"])
    email: EmailStr = Field(..., examples=["alex.mercer@example.com"])
    passport_id: str = Field(..., min_length=5, max_length=30, examples=["P12345678"])

    @field_validator("passport_id")
    @classmethod
    def validate_passport_id(cls, v: str) -> str:
        cleaned = v.strip().upper()
        # Non-empty, alphanumeric allowing hyphens
        if not re.match(r"^[A-Z0-9\-]+$", cleaned):
            raise ValueError("Passport / National ID must contain only alphanumeric characters and hyphens.")
        if len(cleaned) < 5:
            raise ValueError("Passport / National ID must be at least 5 characters long.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        # E.164-ish permissive international regex
        if not re.match(r"^\+?[0-9\s\-()]{7,25}$", cleaned):
            raise ValueError("Phone number must be a valid international phone number format (e.g. +1-555-0199).")
        return cleaned


class TouristCreate(TouristBase):
    pass


class TouristResponse(TouristBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# Booking Schemas
# =====================================================================

class BookingDatesValidatorMixin:
    """Validator mixin to guarantee check_out strictly greater than check_in."""

    @model_validator(mode="after")
    def validate_dates(self) -> "BookingDatesValidatorMixin":
        check_in = getattr(self, "check_in", None)
        check_out = getattr(self, "check_out", None)
        if check_in and check_out:
            if check_out <= check_in:
                raise ValueError("check_out must be strictly greater than check_in (same-day or inverted stays are rejected).")
        return self


class BookingCreate(BaseModel, BookingDatesValidatorMixin):
    room_id: int = Field(..., gt=0, examples=[1])
    check_in: date = Field(..., examples=["2026-10-01"])
    check_out: date = Field(..., examples=["2026-10-05"])

    # Tourist intake credentials
    full_name: str = Field(..., min_length=2, max_length=100, examples=["Alex Mercer"])
    nationality: str = Field(..., min_length=2, max_length=50, examples=["Canadian"])
    phone: str = Field(..., examples=["+1-555-0199"])
    email: EmailStr = Field(..., examples=["alex.mercer@example.com"])
    passport_id: str = Field(..., min_length=5, max_length=30, examples=["P12345678"])

    special_requests: Optional[str] = Field(None, max_length=500, examples=["High floor, quiet room away from elevators."])

    @field_validator("passport_id")
    @classmethod
    def validate_passport_id(cls, v: str) -> str:
        return TouristBase.validate_passport_id(v)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return TouristBase.validate_phone(v)


class BookingUpdateDates(BaseModel, BookingDatesValidatorMixin):
    check_in: date = Field(..., examples=["2026-10-02"])
    check_out: date = Field(..., examples=["2026-10-07"])


class BookingResponse(BaseModel):
    id: int
    booking_ref: str
    room_id: int
    tourist_id: int
    check_in: date
    check_out: date
    total_nights: int
    total_tariff: float
    status: str
    special_requests: Optional[str] = None
    created_at: datetime
    room: RoomResponse
    tourist: TouristResponse

    model_config = ConfigDict(from_attributes=True)


class BookingCreatedResponse(BookingResponse):
    """Returned only upon booking creation, providing the one-time manage_token."""
    manage_token: str
