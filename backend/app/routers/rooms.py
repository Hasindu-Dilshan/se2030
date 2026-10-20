from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import RoomResponse
from ..repositories.room_repo import RoomRepository

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", response_model=List[RoomResponse])
def list_rooms(db: Session = Depends(get_db)):
    """List all available rooms in the hotel catalog."""
    return RoomRepository.get_all(db)


@router.get("/available", response_model=List[RoomResponse])
def list_available_rooms(
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    List rooms with no overlapping CONFIRMED booking in [check_in, check_out).
    Powers the Room Search & Catalog screens.
    """
    if check_out <= check_in:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="check_out must be strictly greater than check_in.",
        )
    return RoomRepository.get_available_rooms(db, check_in, check_out)


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Get room details by ID."""
    room = RoomRepository.get_by_id(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with ID {room_id} not found."
        )
    return room
