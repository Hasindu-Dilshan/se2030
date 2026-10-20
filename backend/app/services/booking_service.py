import string
import secrets
from datetime import date
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models import Booking, Room, Tourist
from ..schemas import BookingCreate, BookingUpdateDates
from ..repositories.room_repo import RoomRepository
from ..repositories.tourist_repo import TouristRepository
from ..repositories.booking_repo import BookingRepository
from .pricing_strategies import PricingStrategy, PricingStrategyResolver


class BookingService:
    """
    Business logic and orchestration service for hotel reservations.
    Enforces atomic concurrency locking, dynamic tariff calculation,
    unique reference generation with collision retry, and guest deduplication.
    """

    @staticmethod
    def _acquire_room_lock(db: Session, room_id: int) -> Room:
        """
        CONCURRENCY-SAFE ROOM LOCKING:
        ------------------------------
        In a multi-user reservation portal, two concurrent requests might check room
        availability simultaneously. Without transactional serialization, both requests
        would see the room as unoccupied in the requested interval and both would proceed
        to insert CONFIRMED bookings for the exact same room and overlapping dates.
        This represents a classic check-then-act race condition causing double bookings.

        To guarantee atomicity between the overlap verification and the booking insertion:
        1. On SQLite: We promote the transaction to an exclusive write lock immediately
           via 'BEGIN IMMEDIATE'. This serializes concurrent write transactions at the database
           level, preventing any other connection from performing a check-and-insert race.
        2. On PostgreSQL: We issue 'SELECT ... FOR UPDATE' on the target Room record. This
           places an exclusive row lock on the Room, causing any competing concurrent transaction
           attempting to book the same room to wait until this transaction completes (commits or rolls back).
        """
        dialect_name = db.bind.dialect.name if db.bind else "sqlite"
        if dialect_name == "sqlite":
            try:
                db.connection().execute(text("BEGIN IMMEDIATE"))
            except Exception:
                # If transaction has already begun or connection is wrapped, proceed with row query
                pass

        stmt = select(Room).where(Room.id == room_id).with_for_update()
        room = db.execute(stmt).scalar_one_or_none()
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Room with ID {room_id} not found."
            )
        return room

    @classmethod
    def create_booking(
        cls,
        db: Session,
        payload: BookingCreate,
        pricing_strategy: Optional[PricingStrategy] = None,
    ) -> Tuple[Booking, str]:
        """
        Create a new booking with atomic concurrency collision check,
        dynamic tariff calculation (via Strategy Pattern), guest deduplication,
        and collision-resistant booking_ref generation.
        """
        # 1. Acquire transaction-level lock on the room to prevent concurrent race conditions
        room = cls._acquire_room_lock(db, payload.room_id)

        # 2. Concurrency-safe collision check:
        # Overlap condition: new_check_in < existing_check_out AND new_check_out > existing_check_in
        has_collision = BookingRepository.check_collision(
            db=db,
            room_id=payload.room_id,
            check_in=payload.check_in,
            check_out=payload.check_out,
        )
        if has_collision:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Room is not available for the selected dates. Please choose different dates or another room."
            )

        # 3. Guest profile deduplication (shared, reusable Tourist entity by passport_id)
        passport_clean = payload.passport_id.strip().upper()
        tourist = TouristRepository.get_by_passport(db, passport_clean)
        if not tourist:
            tourist = Tourist(
                full_name=payload.full_name.strip(),
                nationality=payload.nationality.strip(),
                phone=payload.phone.strip(),
                email=str(payload.email).strip().lower(),
                passport_id=passport_clean,
            )
            TouristRepository.create(db, tourist)
        else:
            # Update guest profile with latest contact details
            tourist.full_name = payload.full_name.strip()
            tourist.nationality = payload.nationality.strip()
            tourist.phone = payload.phone.strip()
            tourist.email = str(payload.email).strip().lower()
            db.flush()

        # 4. Dynamic tariff computation using Strategy Pattern (behavioral)
        strategy = pricing_strategy or PricingStrategyResolver.get_strategy()
        total_nights = (payload.check_out - payload.check_in).days
        total_tariff = strategy.calculate_tariff(room, payload.check_in, payload.check_out)

        # 5. Security management token generation (scope security token for PATCH / DELETE)
        manage_token = secrets.token_urlsafe(24)

        # 6. Reference code generation inside a retry loop against unique constraint collisions
        # Format: TRV-{current_year}-{random 5-char alphanumeric}
        max_retries = 10
        booking = None
        for attempt in range(max_retries):
            chars = string.ascii_uppercase + string.digits
            # Avoid visually ambiguous characters 0, O, 1, I
            unambiguous_chars = "".join(c for c in chars if c not in ("0", "O", "1", "I"))
            random_code = "".join(secrets.choice(unambiguous_chars) for _ in range(5))
            booking_ref = f"TRV-{payload.check_in.year}-{random_code}"

            if BookingRepository.get_by_ref(db, booking_ref) is not None:
                continue

            candidate = Booking(
                booking_ref=booking_ref,
                room_id=room.id,
                tourist_id=tourist.id,
                check_in=payload.check_in,
                check_out=payload.check_out,
                total_nights=total_nights,
                total_tariff=total_tariff,
                status="CONFIRMED",
                special_requests=payload.special_requests,
                manage_token=manage_token,
            )

            try:
                with db.begin_nested():
                    BookingRepository.create(db, candidate)
                booking = candidate
                break
            except IntegrityError:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to generate a unique booking reference after multiple attempts."
                    )
                continue

        db.commit()
        db.refresh(booking)
        return booking, manage_token

    @classmethod
    def get_booking_by_ref(cls, db: Session, booking_ref: str) -> Booking:
        """Retrieve booking itinerary by reference."""
        booking = BookingRepository.get_by_ref(db, booking_ref)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with reference '{booking_ref}' was not found."
            )
        return booking

    @classmethod
    def list_bookings(
        cls,
        db: Session,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Booking]:
        """List paginated bookings, optionally filtered by status."""
        return BookingRepository.get_all(db, status=status_filter, limit=limit, offset=offset)

    @classmethod
    def update_booking_dates(
        cls,
        db: Session,
        booking_ref: str,
        payload: BookingUpdateDates,
        token: str,
        pricing_strategy: Optional[PricingStrategy] = None,
    ) -> Booking:
        """
        Modify check_in / check_out dates for an existing booking.
        Enforces manage_token authentication, concurrency row lock, dynamic tariff
        recalculation via Strategy Pattern, and collision check excluding the booking's own ID.
        """
        booking = BookingRepository.get_by_ref(db, booking_ref)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with reference '{booking_ref}' was not found."
            )

        # Security verification
        if not secrets.compare_digest(booking.manage_token, token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid management token. You are not authorized to modify this booking."
            )

        # Lock room row
        room = cls._acquire_room_lock(db, booking.room_id)

        # Collision check excluding the current booking ID
        has_collision = BookingRepository.check_collision(
            db=db,
            room_id=booking.room_id,
            check_in=payload.check_in,
            check_out=payload.check_out,
            exclude_booking_id=booking.id,
        )
        if has_collision:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The room is not available for the updated dates requested."
            )

        # Recalculate duration and tariff using Strategy Pattern (behavioral)
        strategy = pricing_strategy or PricingStrategyResolver.get_strategy()
        new_nights = (payload.check_out - payload.check_in).days
        new_tariff = strategy.calculate_tariff(room, payload.check_in, payload.check_out)

        booking.check_in = payload.check_in
        booking.check_out = payload.check_out
        booking.total_nights = new_nights
        booking.total_tariff = new_tariff

        db.commit()
        db.refresh(booking)
        return booking

    @classmethod
    def delete_booking(
        cls,
        db: Session,
        booking_ref: str,
        token: str,
    ) -> None:
        """
        Hard-delete a booking, immediately freeing the room for those dates.
        Requires manage_token authentication.
        """
        booking = BookingRepository.get_by_ref(db, booking_ref)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with reference '{booking_ref}' was not found."
            )

        # Security verification
        if not secrets.compare_digest(booking.manage_token, token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid management token. You are not authorized to cancel this booking."
            )

        BookingRepository.delete(db, booking)
        db.commit()
