import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class MachineStatus(str, enum.Enum):
    free = "free"
    out_of_order = "out_of_order"


class BookingStatus(str, enum.Enum):
    booked = "booked"
    collected = "collected"
    cancelled = "cancelled"
    no_show = "no_show"


# A booking still holds its machine while it is in one of these.
ACTIVE_BOOKING_STATES = (BookingStatus.booked, BookingStatus.collected)


def _enum_col(py_enum, name, default):
    return mapped_column(
        Enum(py_enum, name=name, values_callable=lambda e: [m.value for m in e]),
        default=default,
        index=True,
    )


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(40), unique=True)
    location: Mapped[str] = mapped_column(String(80))
    status: Mapped[MachineStatus] = _enum_col(
        MachineStatus, "machine_status", MachineStatus.free
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    bookings: Mapped[list["Booking"]] = relationship(back_populates="machine")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id", ondelete="RESTRICT"), index=True
    )
    student_name: Mapped[str] = mapped_column(String(80))
    room_number: Mapped[str] = mapped_column(String(10))
    slot_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    slot_end: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[BookingStatus] = _enum_col(
        BookingStatus, "booking_status", BookingStatus.booked
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    machine: Mapped[Machine] = relationship(back_populates="bookings")
