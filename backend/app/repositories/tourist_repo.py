from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Tourist


class TouristRepository:
    """Repository handling database operations for the shared, reusable Tourist entity."""

    @staticmethod
    def get_by_passport(db: Session, passport_id: str) -> Optional[Tourist]:
        """Look up existing tourist profile by unique passport/national ID."""
        cleaned_id = passport_id.strip().upper()
        stmt = select(Tourist).where(Tourist.passport_id == cleaned_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(db: Session, tourist_id: int) -> Optional[Tourist]:
        """Look up tourist by primary key ID."""
        stmt = select(Tourist).where(Tourist.id == tourist_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(db: Session, tourist: Tourist) -> Tourist:
        """Persist a new tourist record."""
        db.add(tourist)
        db.flush()
        return tourist
