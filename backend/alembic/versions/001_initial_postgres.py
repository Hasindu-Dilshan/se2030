"""Initial schema for Tourstay Portal (PostgreSQL path)

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-27 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create rooms table
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_number", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("rate_per_night", sa.Float(), nullable=False),
        sa.Column("max_capacity", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_id"), "rooms", ["id"], unique=False)
    op.create_index(op.f("ix_rooms_room_number"), "rooms", ["room_number"], unique=True)

    # 2. Create tourists table (shared, reusable guest entity)
    op.create_table(
        "tourists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("nationality", sa.String(length=50), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("passport_id", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tourists_id"), "tourists", ["id"], unique=False)
    op.create_index(op.f("ix_tourists_passport_id"), "tourists", ["passport_id"], unique=True)

    # 3. Create bookings table
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_ref", sa.String(length=30), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("tourist_id", sa.Integer(), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("total_nights", sa.Integer(), nullable=False),
        sa.Column("total_tariff", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column("manage_token", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tourist_id"], ["tourists.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_id"), "bookings", ["id"], unique=False)
    op.create_index(op.f("ix_bookings_booking_ref"), "bookings", ["booking_ref"], unique=True)
    op.create_index(op.f("ix_bookings_check_in"), "bookings", ["check_in"], unique=False)
    op.create_index(op.f("ix_bookings_check_out"), "bookings", ["check_out"], unique=False)
    op.create_index(op.f("ix_bookings_manage_token"), "bookings", ["manage_token"], unique=False)
    op.create_index("idx_booking_room_dates", "bookings", ["room_id", "check_in", "check_out", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_booking_room_dates", table_name="bookings")
    op.drop_index(op.f("ix_bookings_manage_token"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_check_out"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_check_in"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_booking_ref"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_id"), table_name="bookings")
    op.drop_table("bookings")

    op.drop_index(op.f("ix_tourists_passport_id"), table_name="tourists")
    op.drop_index(op.f("ix_tourists_id"), table_name="tourists")
    op.drop_table("tourists")

    op.drop_index(op.f("ix_rooms_room_number"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_id"), table_name="rooms")
    op.drop_table("rooms")
