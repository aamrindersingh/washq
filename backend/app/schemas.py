from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import HOSTEL_TZ, SLOT_MINUTES
from app.models import BookingStatus, MachineStatus


def to_hostel_clock(value: datetime) -> datetime:
    """Drop the offset and round to the minute so slots line up."""
    if value.tzinfo is not None:
        value = value.astimezone(HOSTEL_TZ).replace(tzinfo=None)
    return value.replace(second=0, microsecond=0)


class MachineCreate(BaseModel):
    label: str = Field(min_length=1, max_length=40)
    location: str = Field(min_length=2, max_length=80)


class MachineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    location: str
    status: MachineStatus


class MachineState(MachineRead):
    """A machine plus whatever is happening on it right now."""

    busy_now: bool
    free_at: datetime | None
    current_booking_id: int | None


class MachineStatusUpdate(BaseModel):
    status: MachineStatus


class BookingCreate(BaseModel):
    machine_id: int
    student_name: str = Field(min_length=2, max_length=80)
    room_number: str = Field(pattern=r"^[A-Za-z]?-?[0-9]{1,4}[A-Za-z]?$")
    slot_start: datetime

    _clock = field_validator("slot_start")(to_hostel_clock)

    @property
    def slot_end(self) -> datetime:
        return self.slot_start + timedelta(minutes=SLOT_MINUTES)


class BookingUpdate(BaseModel):
    slot_start: datetime | None = None
    status: BookingStatus | None = None
    machine_id: int | None = None

    @field_validator("slot_start")
    @classmethod
    def _clock(cls, value: datetime | None) -> datetime | None:
        return None if value is None else to_hostel_clock(value)


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    machine_id: int
    student_name: str
    room_number: str
    slot_start: datetime
    slot_end: datetime
    status: BookingStatus
    machine: MachineRead


class BookingPage(BaseModel):
    items: list[BookingRead]
    page: int
    limit: int
    total_items: int
    total_pages: int


class MachineLoad(BaseModel):
    machine_id: int
    label: str
    bookings_today: int


class Stats(BaseModel):
    machines_total: int
    machines_busy_now: int
    machines_out_of_order: int
    bookings_today: int
    bookings_upcoming: int
    by_status: dict[str, int]
    busiest_machines: list[MachineLoad]
