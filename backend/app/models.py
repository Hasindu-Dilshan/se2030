from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from .database import Base


class Room(Base):
    """
    Room entity representing hotel accommodations.
    Rooms are read-only in the tourist booking flow.
    """
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(20), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)  # e.g., 'Standard', 'Deluxe', 'Suite'
    rate_per_night = Column(Float, nullable=False)
    max_capacity = Column(Integer, nullable=False)

    # Relationships: Deleting a Room must NEVER cascade-delete its bookings.
    bookings = relationship(
        "Booking",
        back_populates="room",
        cascade="",  # Explicitly no cascade-delete
    )


class Tourist(Base):
    """
    Tourist entity representing a shared, reusable guest profile.
    Guests are uniquely identified by passport/national ID so repeat guests
    do not create redundant records.
    """
    __tablename__ = "tourists"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    nationality = Column(String(50), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(100), nullable=False)
    passport_id = Column(String(50), unique=True, nullable=False, index=True)

    # Relationships: Deleting a Tourist must NEVER cascade-delete booking history.
    bookings = relationship(
        "Booking",
        back_populates="tourist",
        cascade="",  # Explicitly no cascade-delete
    )


class Booking(Base):
    """
    Booking entity linking a Tourist to a Room across a specific date range.
    Ownership:
      - Booking references Room and Tourist via foreign keys with RESTRICT semantics.
      - Deleting a booking is a hard delete that frees the room for the dates.
      - Deleting a booking only cascades to booking-owned dependents, never to Room or Tourist.
    """
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_ref = Column(String(30), unique=True, nullable=False, index=True)  # TRV-{year}-{code}
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False)
    tourist_id = Column(Integer, ForeignKey("tourists.id", ondelete="RESTRICT"), nullable=False)
    check_in = Column(Date, nullable=False, index=True)
    check_out = Column(Date, nullable=False, index=True)
    total_nights = Column(Integer, nullable=False)
    total_tariff = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="CONFIRMED")  # CONFIRMED / COMPLETED
    special_requests = Column(Text, nullable=True)
    manage_token = Column(String(64), nullable=False, index=True)  # Security token for PATCH/DELETE
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    room = relationship("Room", back_populates="bookings")
    tourist = relationship("Tourist", back_populates="bookings")

    __table_args__ = (
        Index("idx_booking_room_dates", "room_id", "check_in", "check_out", "status"),
    )
