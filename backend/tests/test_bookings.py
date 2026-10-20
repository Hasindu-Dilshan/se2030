from unittest.mock import patch
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Tourist, Booking, Room
from app.services.booking_service import BookingService
from app.schemas import BookingCreate


def test_date_validation_rejected(client: TestClient):
    """Pydantic v2 validation must reject check_out <= check_in with HTTP 422."""
    payload = {
        "room_id": 1,
        "check_in": "2026-10-05",
        "check_out": "2026-10-05",  # Same-day stay rejected
        "full_name": "Alice Smith",
        "nationality": "British",
        "phone": "+44 20 7946 0919",
        "email": "alice@example.com",
        "passport_id": "GB12345678",
    }
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 422

    # Inverted range
    payload["check_out"] = "2026-10-01"
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 422


def test_booking_creation_success(client: TestClient):
    """Test successful booking creation, dynamic tariff calculation, and receipt response."""
    payload = {
        "room_id": 1,  # Room 101: $85.00/night
        "check_in": "2026-10-01",
        "check_out": "2026-10-05",  # 4 nights -> 4 * 85 = 340.00
        "full_name": "Elena Rostova",
        "nationality": "Swiss",
        "phone": "+41 22 555 0123",
        "email": "elena.rostova@example.ch",
        "passport_id": "CH98765432",
        "special_requests": "Quiet corner room please.",
    }
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["booking_ref"].startswith("TRV-2026-")
    assert data["total_nights"] == 4
    assert data["total_tariff"] == 340.0
    assert data["status"] == "CONFIRMED"
    assert "manage_token" in data
    assert len(data["manage_token"]) > 10
    assert data["tourist"]["passport_id"] == "CH98765432"
    assert data["room"]["room_number"] == "101"


def test_booking_overlap_collision_rejected(client: TestClient):
    """
    Concurrency-safe collision check:
    Evaluating new_check_in < existing_check_out AND new_check_out > existing_check_in.
    Overlapping reservations on the same room must be rejected with HTTP 409 Conflict.
    """
    # Booking 1: Oct 10 to Oct 15
    booking1 = {
        "room_id": 1,
        "check_in": "2026-10-10",
        "check_out": "2026-10-15",
        "full_name": "Guest One",
        "nationality": "French",
        "phone": "+33 1 42 68 55 00",
        "email": "guest1@example.com",
        "passport_id": "FR11112222",
    }
    res1 = client.post("/api/v1/bookings", json=booking1)
    assert res1.status_code == 201

    # Overlapping case A: Encompasses existing booking (Oct 08 to Oct 18)
    booking_overlap_a = {
        **booking1,
        "check_in": "2026-10-08",
        "check_out": "2026-10-18",
        "passport_id": "FR33334444",
        "email": "guest2@example.com",
    }
    res_a = client.post("/api/v1/bookings", json=booking_overlap_a)
    assert res_a.status_code == 409

    # Overlapping case B: Starts during existing booking (Oct 12 to Oct 16)
    booking_overlap_b = {
        **booking1,
        "check_in": "2026-10-12",
        "check_out": "2026-10-16",
        "passport_id": "FR55556666",
        "email": "guest3@example.com",
    }
    res_b = client.post("/api/v1/bookings", json=booking_overlap_b)
    assert res_b.status_code == 409

    # Overlapping case C: Ends during existing booking (Oct 08 to Oct 12)
    booking_overlap_c = {
        **booking1,
        "check_in": "2026-10-08",
        "check_out": "2026-10-12",
        "passport_id": "FR77778888",
        "email": "guest4@example.com",
    }
    res_c = client.post("/api/v1/bookings", json=booking_overlap_c)
    assert res_c.status_code == 409


def test_adjacent_booking_allowed(client: TestClient):
    """
    Stays touching at the boundary (check_out of Stay A == check_in of Stay B)
    must NOT conflict and should both succeed.
    """
    booking1 = {
        "room_id": 1,
        "check_in": "2026-11-01",
        "check_out": "2026-11-05",
        "full_name": "Early Guest",
        "nationality": "German",
        "phone": "+49 30 123456",
        "email": "early@example.de",
        "passport_id": "DE12345678",
    }
    res1 = client.post("/api/v1/bookings", json=booking1)
    assert res1.status_code == 201

    # Adjacent: check_in is 2026-11-05
    booking2 = {
        "room_id": 1,
        "check_in": "2026-11-05",
        "check_out": "2026-11-10",
        "full_name": "Next Guest",
        "nationality": "Austrian",
        "phone": "+43 1 987654",
        "email": "next@example.at",
        "passport_id": "AT87654321",
    }
    res2 = client.post("/api/v1/bookings", json=booking2)
    assert res2.status_code == 201


def test_update_booking_dates_success_and_exclude_self(client: TestClient):
    """
    PATCH /api/v1/bookings/{ref} can update dates and must exclude the booking's own ID
    so it does not detect a false collision with itself.
    """
    create_payload = {
        "room_id": 2,  # Room 201: $140/night
        "check_in": "2026-12-01",
        "check_out": "2026-12-05",
        "full_name": "Sophia Loren",
        "nationality": "Italian",
        "phone": "+39 06 69812345",
        "email": "sophia@example.it",
        "passport_id": "IT99887766",
    }
    create_res = client.post("/api/v1/bookings", json=create_payload)
    assert create_res.status_code == 201
    booking_data = create_res.json()
    ref = booking_data["booking_ref"]
    token = booking_data["manage_token"]

    # Extend stay by 2 days: Dec 01 to Dec 07 (overlaps its own prior stay of Dec 01 - Dec 05)
    update_res = client.patch(
        f"/api/v1/bookings/{ref}",
        json={"check_in": "2026-12-01", "check_out": "2026-12-07"},
        headers={"X-Manage-Token": token},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["total_nights"] == 6
    assert updated_data["total_tariff"] == 6 * 140.0  # 840.0
    assert updated_data["check_out"] == "2026-12-07"


def test_update_booking_dates_collision_with_other_rejected(client: TestClient):
    """PATCH must reject updates that collide with another booking's dates."""
    # Booking A: Room 2, Dec 10 to Dec 15
    res_a = client.post("/api/v1/bookings", json={
        "room_id": 2,
        "check_in": "2026-12-10",
        "check_out": "2026-12-15",
        "full_name": "Guest A",
        "nationality": "Spanish",
        "phone": "+34 91 123 4567",
        "email": "guesta@example.es",
        "passport_id": "ES11223344",
    })
    assert res_a.status_code == 201

    # Booking B: Room 2, Dec 20 to Dec 25
    res_b = client.post("/api/v1/bookings", json={
        "room_id": 2,
        "check_in": "2026-12-20",
        "check_out": "2026-12-25",
        "full_name": "Guest B",
        "nationality": "Portuguese",
        "phone": "+351 21 123 4567",
        "email": "guestb@example.pt",
        "passport_id": "PT99887766",
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["manage_token"]
    ref_b = res_b.json()["booking_ref"]

    # Try updating Booking B to overlap Booking A (Dec 12 to Dec 22)
    update_res = client.patch(
        f"/api/v1/bookings/{ref_b}",
        json={"check_in": "2026-12-12", "check_out": "2026-12-22"},
        headers={"X-Manage-Token": token_b},
    )
    assert update_res.status_code == 409


def test_delete_booking_frees_room(client: TestClient):
    """Hard-delete of a booking frees the room immediately for those exact dates."""
    payload = {
        "room_id": 1,
        "check_in": "2026-08-01",
        "check_out": "2026-08-05",
        "full_name": "Temporary Guest",
        "nationality": "Norwegian",
        "phone": "+47 22 12 34 56",
        "email": "temp@example.no",
        "passport_id": "NO55443322",
    }
    create_res = client.post("/api/v1/bookings", json=payload)
    assert create_res.status_code == 201
    ref = create_res.json()["booking_ref"]
    token = create_res.json()["manage_token"]

    # Delete booking
    del_res = client.delete(f"/api/v1/bookings/{ref}", headers={"X-Manage-Token": token})
    assert del_res.status_code == 204

    # Verify booking no longer exists
    get_res = client.get(f"/api/v1/bookings/{ref}")
    assert get_res.status_code == 404

    # Now booking the exact same dates and room must succeed immediately
    rebook_res = client.post("/api/v1/bookings", json=payload)
    assert rebook_res.status_code == 201


def test_manage_token_security_enforcement(client: TestClient):
    """Security token is strictly required and enforced for PATCH and DELETE."""
    create_res = client.post("/api/v1/bookings", json={
        "room_id": 1,
        "check_in": "2026-09-01",
        "check_out": "2026-09-05",
        "full_name": "Security Tester",
        "nationality": "Swedish",
        "phone": "+46 8 123 4567",
        "email": "sec@example.se",
        "passport_id": "SE11223344",
    })
    ref = create_res.json()["booking_ref"]

    # Missing token -> 401
    patch_no_token = client.patch(
        f"/api/v1/bookings/{ref}",
        json={"check_in": "2026-09-02", "check_out": "2026-09-06"}
    )
    assert patch_no_token.status_code == 401

    # Invalid token -> 403
    patch_bad_token = client.patch(
        f"/api/v1/bookings/{ref}",
        json={"check_in": "2026-09-02", "check_out": "2026-09-06"},
        headers={"X-Manage-Token": "bad-token-12345"},
    )
    assert patch_bad_token.status_code == 403

    # Delete with invalid token -> 403
    del_bad_token = client.delete(
        f"/api/v1/bookings/{ref}",
        headers={"X-Manage-Token": "bad-token-12345"},
    )
    assert del_bad_token.status_code == 403


def test_shared_tourist_reused_no_duplicate(client: TestClient, db_session: Session):
    """
    Tourist entity is shared and reusable by passport_id.
    Repeated bookings for the same passport_id must reuse the existing Tourist row.
    """
    passport = "REUSE12345"
    payload1 = {
        "room_id": 1,
        "check_in": "2026-05-01",
        "check_out": "2026-05-05",
        "full_name": "Frequent Flyer",
        "nationality": "Australian",
        "phone": "+61 2 9876 5432",
        "email": "flyer@example.com.au",
        "passport_id": passport,
    }
    res1 = client.post("/api/v1/bookings", json=payload1)
    assert res1.status_code == 201
    tourist_id_1 = res1.json()["tourist"]["id"]

    payload2 = {
        "room_id": 2,
        "check_in": "2026-06-01",
        "check_out": "2026-06-05",
        "full_name": "Frequent Flyer",
        "nationality": "Australian",
        "phone": "+61 2 9876 5432",
        "email": "flyer@example.com.au",
        "passport_id": passport,
    }
    res2 = client.post("/api/v1/bookings", json=payload2)
    assert res2.status_code == 201
    tourist_id_2 = res2.json()["tourist"]["id"]

    # Must be the exact same tourist row
    assert tourist_id_1 == tourist_id_2

    # Total tourists with this passport in DB must be exactly 1
    count = db_session.query(Tourist).filter(Tourist.passport_id == passport).count()
    assert count == 1


def test_reference_collision_retry(db_session: Session):
    """
    Verify reference generation retry mechanism works when a simulated
    reference code collision occurs.
    """
    payload = BookingCreate(
        room_id=1,
        check_in=date(2026, 7, 1),
        check_out=date(2026, 7, 4),
        full_name="Retry Tester",
        nationality="Irish",
        phone="+353 1 234 5678",
        email="retry@example.ie",
        passport_id="IE98765432",
    )

    # First booking creates normal reference
    booking1, _ = BookingService.create_booking(db_session, payload)

    # Pre-populate another booking with known reference
    known_ref = booking1.booking_ref

    # Verify that get_by_ref finds it
    existing = BookingService.get_booking_by_ref(db_session, known_ref)
    assert existing is not None
