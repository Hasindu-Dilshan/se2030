from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Room
from app.schemas import BookingCreate
from app.services.booking_service import BookingService
from app.services.pricing_strategies import (
    StandardPricingStrategy,
    ExtendedStayDiscountStrategy,
    WeekendSurgePricingStrategy,
    PricingStrategyResolver,
)


def test_standard_pricing_strategy():
    """Verify StandardPricingStrategy calculates flat rate: nights * rate_per_night."""
    room = Room(id=1, room_number="101", category="Standard", rate_per_night=100.0, max_capacity=2)
    strategy = StandardPricingStrategy()

    check_in = date(2026, 10, 1)
    check_out = date(2026, 10, 5)  # 4 nights
    tariff = strategy.calculate_tariff(room, check_in, check_out)
    assert tariff == 400.0

    breakdown = strategy.get_breakdown(room, check_in, check_out)
    assert breakdown["strategy"] == "Standard"
    assert breakdown["nights"] == 4
    assert breakdown["total_tariff"] == 400.0


def test_extended_stay_discount_strategy():
    """Verify ExtendedStayDiscountStrategy applies 10% discount for >= 5 nights and 15% for >= 10 nights."""
    room = Room(id=1, room_number="101", category="Standard", rate_per_night=100.0, max_capacity=2)
    strategy = ExtendedStayDiscountStrategy()

    # Case 1: Under 5 nights (no discount)
    tariff_4 = strategy.calculate_tariff(room, date(2026, 10, 1), date(2026, 10, 5))  # 4 nights
    assert tariff_4 == 400.0

    # Case 2: 6 nights -> 10% discount: 6 * 100 * 0.90 = 540.0
    tariff_6 = strategy.calculate_tariff(room, date(2026, 10, 1), date(2026, 10, 7))  # 6 nights
    assert tariff_6 == 540.0

    # Case 3: 10 nights -> 15% discount: 10 * 100 * 0.85 = 850.0
    tariff_10 = strategy.calculate_tariff(room, date(2026, 10, 1), date(2026, 10, 11))  # 10 nights
    assert tariff_10 == 850.0

    breakdown = strategy.get_breakdown(room, date(2026, 10, 1), date(2026, 10, 7))
    assert breakdown["discount_amount"] == 60.0
    assert breakdown["total_tariff"] == 540.0


def test_weekend_surge_pricing_strategy():
    """Verify WeekendSurgePricingStrategy adds 20% surge on Friday and Saturday nights."""
    room = Room(id=1, room_number="101", category="Standard", rate_per_night=100.0, max_capacity=2)
    strategy = WeekendSurgePricingStrategy(surge_multiplier=1.20)

    # 2026-10-15 (Thu) to 2026-10-18 (Sun):
    # Thu night: 100.0
    # Fri night: 120.0
    # Sat night: 120.0
    # Total: 340.0
    check_in = date(2026, 10, 15)   # Thursday
    check_out = date(2026, 10, 18)  # Sunday
    tariff = strategy.calculate_tariff(room, check_in, check_out)
    assert tariff == 340.0

    breakdown = strategy.get_breakdown(room, check_in, check_out)
    assert breakdown["surge_amount"] == 40.0
    assert breakdown["total_tariff"] == 340.0


def test_pricing_strategy_resolver():
    """Verify PricingStrategyResolver returns correct strategy or defaults to Standard."""
    assert isinstance(PricingStrategyResolver.get_strategy("standard"), StandardPricingStrategy)
    assert isinstance(PricingStrategyResolver.get_strategy("extended_stay"), ExtendedStayDiscountStrategy)
    assert isinstance(PricingStrategyResolver.get_strategy("weekend_surge"), WeekendSurgePricingStrategy)
    # Default fallback
    assert isinstance(PricingStrategyResolver.get_strategy(None), StandardPricingStrategy)
    assert isinstance(PricingStrategyResolver.get_strategy("unknown_strategy"), StandardPricingStrategy)


def test_booking_service_strategy_injection(db_session: Session):
    """Verify BookingService dynamically applies an injected strategy."""
    payload = BookingCreate(
        room_id=1,  # $85/night
        check_in=date(2026, 9, 1),
        check_out=date(2026, 9, 7),  # 6 nights
        full_name="Strategy Tester",
        nationality="Canadian",
        phone="+1-555-0123",
        email="strategy@example.ca",
        passport_id="CA99881122",
    )

    # With ExtendedStayDiscountStrategy (10% off for 6 nights: 6 * 85 * 0.90 = 459.0)
    discount_strategy = ExtendedStayDiscountStrategy()
    booking, _ = BookingService.create_booking(db_session, payload, pricing_strategy=discount_strategy)

    assert booking.total_nights == 6
    assert booking.total_tariff == 459.0


def test_api_pricing_strategies_endpoint(client: TestClient):
    """Verify GET /api/v1/bookings/pricing/strategies returns available strategies."""
    res = client.get("/api/v1/bookings/pricing/strategies")
    assert res.status_code == 200
    data = res.json()
    assert "strategies" in data
    keys = [s["key"] for s in data["strategies"]]
    assert "standard" in keys
    assert "extended_stay" in keys
    assert "weekend_surge" in keys


def test_api_create_booking_with_strategy_param(client: TestClient):
    """Verify POST /api/v1/bookings with pricing_strategy query param applies the strategy."""
    payload = {
        "room_id": 1,  # Room 101: $85.00/night
        "check_in": "2026-11-10",
        "check_out": "2026-11-16",  # 6 nights -> 6 * 85 = 510. With 10% off = 459.0
        "full_name": "Discount Tourist",
        "nationality": "Japanese",
        "phone": "+81 3 1234 5678",
        "email": "tourist@example.jp",
        "passport_id": "JP12345678",
    }
    res = client.post("/api/v1/bookings?pricing_strategy=extended_stay", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["total_nights"] == 6
    assert data["total_tariff"] == 459.0
