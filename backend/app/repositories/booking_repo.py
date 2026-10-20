from datetime import date
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload
from ..models import Booking


class BookingRepository:
    """Repository handling database operations for the Booking entity."""

    @staticmethod
    def get_by_ref(db: Session, booking_ref: str) -> Optional[Booking]:
        """Fetch booking by unique booking_ref with room and tourist pre-loaded."""
        stmt = (
            select(Booking)
            .options(joinedload(Booking.room), joinedload(Booking.tourist))
            .where(Booking.booking_ref == booking_ref)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(db: Session, booking_id: int) -> Optional[Booking]:
        """Fetch booking by primary key ID."""
        stmt = (
            select(Booking)
            .options(joinedload(Booking.room), joinedload(Booking.tourist))
            .where(Booking.id == booking_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all(
        db: Session,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Booking]:
        """Fetch paginated bookings with optional status filter, ordered by creation date desc."""
        stmt = (
            select(Booking)
            .options(joinedload(Booking.room), joinedload(Booking.tourist))
            .order_by(Booking.created_at.desc())
        )
        if status:
            stmt = stmt.where(Booking.status == status.upper())

        stmt = stmt.limit(limit).offset(offset)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def check_collision(
        db: Session,
        room_id: int,
        check_in: date,
        check_out: date,
        exclude_booking_id: Optional[int] = None,
    ) -> bool:
        """
        Check if an active (CONFIRMED) booking exists for this room overlapping [check_in, check_out).
        Overlap formula:
            new_check_in < existing_check_out AND new_check_out > existing_check_in
        Optionally excludes exclude_booking_id for PATCH operations.
        Returns True if a collision exists, False if available.
        """
        filters = [
            Booking.room_id == room_id,
            Booking.status == "CONFIRMED",
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        ]

        if exclude_booking_id is not None:
            filters.append(Booking.id != exclude_booking_id)

        stmt = select(Booking.id).where(and_(*filters)).limit(1)
        result = db.execute(stmt).scalar_one_or_none()
        return result is not None

    @staticmethod
    def create(db: Session, booking: Booking) -> Booking:
        """Persist a new booking record."""
        db.add(booking)
        db.flush()
        return booking

    @staticmethod
    def delete(db: Session, booking: Booking) -> None:
        """Hard delete a booking record."""
        db.delete(booking)
        db.flush()
