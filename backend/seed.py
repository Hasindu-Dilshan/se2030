"""
Database Seed Script for Tourstay Portal.
Populates initial sample rooms with realistic rates, categories, and capacities.
Can be executed multiple times idempotently.
"""

from app.database import SessionLocal, init_db
from app.models import Room


SAMPLE_ROOMS = [
    {
        "room_number": "101",
        "category": "Standard Single",
        "rate_per_night": 85.00,
        "max_capacity": 1,
    },
    {
        "room_number": "201",
        "category": "Deluxe Double",
        "rate_per_night": 140.00,
        "max_capacity": 2,
    },
    {
        "room_number": "301",
        "category": "Ocean View Suite",
        "rate_per_night": 220.00,
        "max_capacity": 3,
    },
    {
        "room_number": "401",
        "category": "Family Executive",
        "rate_per_night": 290.00,
        "max_capacity": 4,
    },
    {
        "room_number": "501",
        "category": "Presidential Penthouse",
        "rate_per_night": 550.00,
        "max_capacity": 6,
    },
]


def seed_database():
    """Initializes tables and populates sample rooms if they do not exist."""
    print("Initializing database tables...")
    init_db()

    db = SessionLocal()
    try:
        inserted_count = 0
        for room_data in SAMPLE_ROOMS:
            existing = db.query(Room).filter(Room.room_number == room_data["room_number"]).first()
            if not existing:
                room = Room(**room_data)
                db.add(room)
                inserted_count += 1
                print(f"Added room {room_data['room_number']} ({room_data['category']}) - ${room_data['rate_per_night']}/night")
            else:
                print(f"Room {room_data['room_number']} already exists, skipping.")

        db.commit()
        print(f"\nDatabase seeding completed successfully! ({inserted_count} new rooms added).")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
