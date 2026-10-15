"""machines and bookings

Revision ID: 0001
Revises:
Create Date: 2026-10-16
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

machine_status = sa.Enum("free", "out_of_order", name="machine_status")
booking_status = sa.Enum("booked", "collected", "cancelled", "no_show", name="booking_status")


def upgrade() -> None:
    # create_table emits CREATE TYPE for these itself, so they are not
    # created separately here. Doing both is what raises DuplicateObject.
    op.create_table(
        "machines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(length=40), nullable=False, unique=True),
        sa.Column("location", sa.String(length=80), nullable=False),
        sa.Column("status", machine_status, nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_machines_status", "machines", ["status"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "machine_id",
            sa.Integer(),
            sa.ForeignKey("machines.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("student_name", sa.String(length=80), nullable=False),
        sa.Column("room_number", sa.String(length=10), nullable=False),
        sa.Column("slot_start", sa.DateTime(), nullable=False),
        sa.Column("slot_end", sa.DateTime(), nullable=False),
        sa.Column("status", booking_status, nullable=False, server_default="booked"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bookings_machine_id", "bookings", ["machine_id"])
    op.create_index("ix_bookings_slot_start", "bookings", ["slot_start"])
    op.create_index("ix_bookings_status", "bookings", ["status"])

    # Stops the same machine being handed out twice for an overlapping window.
    # The app checks this too, but the database is the last word.
    op.create_index(
        "ix_bookings_machine_slot",
        "bookings",
        ["machine_id", "slot_start", "slot_end"],
    )


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("machines")
    bind = op.get_bind()
    booking_status.drop(bind, checkfirst=True)
    machine_status.drop(bind, checkfirst=True)
