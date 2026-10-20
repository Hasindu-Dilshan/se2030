"""
Strategy Pattern: Tariff and Pricing Calculation Module.
-------------------------------------------------------
Defines interchangeable pricing strategies for room tariff calculation,
enabling the application to adhere to the Open/Closed Principle (OCP).
"""

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Dict, Any, Optional

from ..models import Room


class PricingStrategy(ABC):
    """
    Abstract Strategy Interface for Tariff and Pricing Calculation.
    Defines the contract for calculating stay tariffs across various pricing algorithms.
    """

    @abstractmethod
    def calculate_tariff(self, room: Room, check_in: date, check_out: date) -> float:
        """
        Calculate total tariff for the given room and stay dates.
        Must return a rounded float representing the total price.
        """
        pass

    @abstractmethod
    def get_breakdown(self, room: Room, check_in: date, check_out: date) -> Dict[str, Any]:
        """
        Returns an itemized breakdown of the tariff calculation (base rate, nights, adjustments).
        """
        pass


class StandardPricingStrategy(PricingStrategy):
    """
    Standard Pricing Strategy (Default):
    Computes flat rate based on room.rate_per_night multiplied by total nights.
    Formula: nights * room.rate_per_night
    """

    def calculate_tariff(self, room: Room, check_in: date, check_out: date) -> float:
        nights = (check_out - check_in).days
        return round(nights * room.rate_per_night, 2)

    def get_breakdown(self, room: Room, check_in: date, check_out: date) -> Dict[str, Any]:
        nights = (check_out - check_in).days
        total = self.calculate_tariff(room, check_in, check_out)
        return {
            "strategy": "Standard",
            "nights": nights,
            "rate_per_night": room.rate_per_night,
            "discount_amount": 0.0,
            "surge_amount": 0.0,
            "total_tariff": total,
        }


class ExtendedStayDiscountStrategy(PricingStrategy):
    """
    Promotional / Length-of-Stay Strategy:
    Encourages longer tourist stays by offering tiered discounts:
    - 5 to 9 nights: 10% discount
    - 10+ nights: 15% discount
    """

    def __init__(
        self,
        tier_1_nights: int = 5,
        tier_1_discount: float = 0.10,
        tier_2_nights: int = 10,
        tier_2_discount: float = 0.15,
    ):
        self.tier_1_nights = tier_1_nights
        self.tier_1_discount = tier_1_discount
        self.tier_2_nights = tier_2_nights
        self.tier_2_discount = tier_2_discount

    def calculate_tariff(self, room: Room, check_in: date, check_out: date) -> float:
        nights = (check_out - check_in).days
        base_tariff = nights * room.rate_per_night

        if nights >= self.tier_2_nights:
            discount = self.tier_2_discount
        elif nights >= self.tier_1_nights:
            discount = self.tier_1_discount
        else:
            discount = 0.0

        return round(base_tariff * (1.0 - discount), 2)

    def get_breakdown(self, room: Room, check_in: date, check_out: date) -> Dict[str, Any]:
        nights = (check_out - check_in).days
        base_tariff = round(nights * room.rate_per_night, 2)
        final_tariff = self.calculate_tariff(room, check_in, check_out)
        discount_amount = round(base_tariff - final_tariff, 2)
        return {
            "strategy": "ExtendedStayDiscount",
            "nights": nights,
            "rate_per_night": room.rate_per_night,
            "base_tariff": base_tariff,
            "discount_amount": discount_amount,
            "surge_amount": 0.0,
            "total_tariff": final_tariff,
        }


class WeekendSurgePricingStrategy(PricingStrategy):
    """
    Dynamic Surge Pricing Strategy:
    Applies a surge multiplier (default 20%) on Friday and Saturday nights.
    Weekdays are charged at the standard base rate.
    """

    def __init__(self, surge_multiplier: float = 1.20):
        self.surge_multiplier = surge_multiplier

    def calculate_tariff(self, room: Room, check_in: date, check_out: date) -> float:
        current_date = check_in
        total = 0.0

        while current_date < check_out:
            # 4 is Friday, 5 is Saturday (weekday() 0-indexed where Monday is 0)
            if current_date.weekday() in (4, 5):
                total += room.rate_per_night * self.surge_multiplier
            else:
                total += room.rate_per_night
            current_date += timedelta(days=1)

        return round(total, 2)

    def get_breakdown(self, room: Room, check_in: date, check_out: date) -> Dict[str, Any]:
        nights = (check_out - check_in).days
        base_tariff = round(nights * room.rate_per_night, 2)
        final_tariff = self.calculate_tariff(room, check_in, check_out)
        surge_amount = round(final_tariff - base_tariff, 2)
        return {
            "strategy": "WeekendSurge",
            "nights": nights,
            "rate_per_night": room.rate_per_night,
            "base_tariff": base_tariff,
            "discount_amount": 0.0,
            "surge_amount": surge_amount,
            "total_tariff": final_tariff,
        }


class PricingStrategyResolver:
    """
    Strategy Resolver / Factory:
    Selects or defaults to a pricing strategy based on strategy key name.
    """

    _registry = {
        "standard": StandardPricingStrategy,
        "extended_stay": ExtendedStayDiscountStrategy,
        "weekend_surge": WeekendSurgePricingStrategy,
    }

    @classmethod
    def get_strategy(cls, strategy_name: Optional[str] = None) -> PricingStrategy:
        if not strategy_name:
            return StandardPricingStrategy()
        strategy_cls = cls._registry.get(strategy_name.lower().strip())
        if not strategy_cls:
            return StandardPricingStrategy()
        return strategy_cls()
