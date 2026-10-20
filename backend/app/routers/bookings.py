from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, HTTPException, status, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    BookingCreate,
    BookingUpdateDates,
    BookingResponse,
    BookingCreatedResponse,
)
from ..services.booking_service import BookingService
from ..services.pricing_strategies import PricingStrategyResolver

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def get_manage_token(
    x_manage_token: Optional[str] = Header(None, alias="X-Manage-Token"),
    manage_token: Optional[str] = Query(None, description="Booking security management token"),
) -> str:
    """Extract security token from HTTP header or query parameter."""
    token = x_manage_token or manage_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Management token is required for this operation. Supply via 'X-Manage-Token' header or 'manage_token' query parameter."
        )
    return token


@router.get("/pricing/strategies", tags=["Pricing Strategies"])
def list_pricing_strategies():
    """
    List available pricing strategies implementing the Strategy Pattern.
    Demonstrates Open/Closed Principle for academic evaluation.
    """
    return {
        "strategies": [
            {
                "key": "standard",
                "name": "Standard Pricing Strategy",
                "description": "Flat rate calculation: nights * rate_per_night.",
            },
            {
                "key": "extended_stay",
                "name": "Extended Stay Discount Strategy",
                "description": "Tiered discounts: 10% off for 5-9 nights, 15% off for 10+ nights.",
            },
            {
                "key": "weekend_surge",
                "name": "Weekend Surge Pricing Strategy",
                "description": "Dynamic pricing: 20% surcharge on Friday and Saturday nights.",
            },
        ]
    }


@router.post("", response_model=BookingCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    pricing_strategy: Optional[str] = Query(
        None,
        description="Optional pricing strategy key ('standard', 'extended_stay', 'weekend_surge')",
    ),
    db: Session = Depends(get_db),
):
    """
    Create a new hotel reservation with concurrency collision checks,
    dynamic tariff calculation via Strategy Pattern, guest profile deduplication,
    and a one-time manage_token for subsequent updates or cancellation.
    """
    strategy = PricingStrategyResolver.get_strategy(pricing_strategy) if pricing_strategy else None
    booking, manage_token = BookingService.create_booking(db, payload, pricing_strategy=strategy)
    # Construct response including manage_token
    return BookingCreatedResponse(
        id=booking.id,
        booking_ref=booking.booking_ref,
        room_id=booking.room_id,
        tourist_id=booking.tourist_id,
        check_in=booking.check_in,
        check_out=booking.check_out,
        total_nights=booking.total_nights,
        total_tariff=booking.total_tariff,
        status=booking.status,
        special_requests=booking.special_requests,
        created_at=booking.created_at,
        room=booking.room,
        tourist=booking.tourist,
        manage_token=manage_token,
    )


@router.get("", response_model=List[BookingResponse])
def list_bookings(
    status: Optional[str] = Query(None, description="Filter bookings by status (CONFIRMED, COMPLETED)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Paginated list of bookings for dashboard view.
    Note: 'Past bookings' in UI indicates completed stays where the stay dates have passed,
    not cancelled bookings (which are permanently hard-deleted).
    """
    return BookingService.list_bookings(db, status_filter=status, limit=limit, offset=offset)


@router.get("/{booking_ref}", response_model=BookingResponse)
def get_booking(booking_ref: str, db: Session = Depends(get_db)):
    """
    Fetch full itinerary details for a booking reference, including room and tourist info.
    Powers the search and printable receipt card views.
    """
    return BookingService.get_booking_by_ref(db, booking_ref)


@router.patch("/{booking_ref}", response_model=BookingResponse)
def update_booking_dates(
    booking_ref: str,
    payload: BookingUpdateDates,
    pricing_strategy: Optional[str] = Query(
        None,
        description="Optional pricing strategy key ('standard', 'extended_stay', 'weekend_surge')",
    ),
    token: str = Depends(get_manage_token),
    db: Session = Depends(get_db),
):
    """
    Modify stay dates for an active reservation.
    Re-evaluates collision checks excluding the current booking ID.
    Recalculates stay tariff via Strategy Pattern.
    Requires the booking's secret manage_token.
    """
    strategy = PricingStrategyResolver.get_strategy(pricing_strategy) if pricing_strategy else None
    return BookingService.update_booking_dates(db, booking_ref, payload, token, pricing_strategy=strategy)


@router.delete("/{booking_ref}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_ref: str,
    token: str = Depends(get_manage_token),
    db: Session = Depends(get_db),
):
    """
    Hard-delete a booking, immediately releasing the room dates for other guests.
    Requires the booking's secret manage_token.
    """
    BookingService.delete_booking(db, booking_ref, token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
