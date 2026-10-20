from datetime import date
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Room, Booking


class RoomRepository:
    """Repository handling database operations for the Room entity."""

    @staticmethod
    def get_all(db: Session) -> List[Room]:
        """Fetch all rooms ordered by room number."""
        stmt = select(Room).order_by(Room.room_number)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_id(db: Session, room_id: int) -> Optional[Room]:
        """Fetch a single room by its primary key ID."""
        stmt = select(Room).where(Room.id == room_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_number(db: Session, room_number: str) -> Optional[Room]:
        """Fetch a room by room number."""
        stmt = select(Room).where(Room.room_number == room_number)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_available_rooms(db: Session, check_in: date, check_out: date) -> List[Room]:
        """
        List rooms that have NO overlapping CONFIRMED booking in [check_in, check_out).
        Overlap condition:
            new_check_in < existing_check_out AND new_check_out > existing_check_in
        """
        overlapping_booking_subquery = (
            select(Booking.room_id)
            .where(
                Booking.status == "CONFIRMED",
                Booking.check_in < check_out,
                Booking.check_out > check_in,
            )
            .scalar_subquery()
        )

        stmt = (
            select(Room)
            .where(~Room.id.in_(overlapping_booking_subquery))
            .order_by(Room.room_number)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def create(db: Session, room: Room) -> Room:
        """Persist a new room record."""
        db.add(room)
        db.flush()
        return room
