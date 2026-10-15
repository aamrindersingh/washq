from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import HOSTEL_TZ, SLOT_MINUTES
from app.models import ACTIVE_BOOKING_STATES, Booking, BookingStatus, Machine, MachineStatus


def now_local() -> datetime:
    """Wall clock in the hostel, with the offset stripped to match stored slots."""
    return datetime.now(HOSTEL_TZ).replace(tzinfo=None, second=0, microsecond=0)


def slot_end_for(start: datetime) -> datetime:
    return start + timedelta(minutes=SLOT_MINUTES)


def clashing_booking(
    db: Session,
    machine_id: int,
    start: datetime,
    end: datetime,
    ignore_booking_id: int | None = None,
) -> Booking | None:
    """The booking that already owns this machine for part of this window.

    Two windows overlap when each starts before the other ends. Touching
    at the edges is fine, so 10:00-10:45 and 10:45-11:30 both fit.
    """
    query = select(Booking).where(
        Booking.machine_id == machine_id,
        Booking.status.in_(ACTIVE_BOOKING_STATES),
        Booking.slot_start < end,
        Booking.slot_end > start,
    )
    if ignore_booking_id is not None:
        query = query.where(Booking.id != ignore_booking_id)
    return db.scalars(query).first()


def current_booking(db: Session, machine_id: int, at: datetime | None = None) -> Booking | None:
    at = at or now_local()
    return db.scalars(
        select(Booking).where(
            Booking.machine_id == machine_id,
            Booking.status.in_(ACTIVE_BOOKING_STATES),
            Booking.slot_start <= at,
            Booking.slot_end > at,
        )
    ).first()


def machine_states(db: Session) -> list[dict]:
    at = now_local()
    out = []
    for machine in db.scalars(select(Machine).order_by(Machine.id)).all():
        running = current_booking(db, machine.id, at)
        out.append(
            {
                "id": machine.id,
                "label": machine.label,
                "location": machine.location,
                "status": machine.status,
                "busy_now": running is not None,
                "free_at": running.slot_end if running else None,
                "current_booking_id": running.id if running else None,
            }
        )
    return out


def refresh_gauges(db: Session) -> None:
    """Keep the two gauges in step with the database."""
    from app.metrics import machines_busy, machines_out_of_order

    states = machine_states(db)
    machines_busy.set(sum(1 for m in states if m["busy_now"]))
    machines_out_of_order.set(
        sum(1 for m in states if m["status"] == MachineStatus.out_of_order)
    )


def build_stats(db: Session) -> dict:
    at = now_local()
    day_start = at.replace(hour=0, minute=0)
    day_end = day_start + timedelta(days=1)
    states = machine_states(db)

    by_status = {s.value: 0 for s in BookingStatus}
    for status, count in db.execute(
        select(Booking.status, func.count()).group_by(Booking.status)
    ).all():
        by_status[status.value if hasattr(status, "value") else str(status)] = count

    bookings_today = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(Booking.slot_start >= day_start, Booking.slot_start < day_end)
    )
    upcoming = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(Booking.slot_start > at, Booking.status == BookingStatus.booked)
    )

    busiest = [
        {"machine_id": mid, "label": label, "bookings_today": count}
        for mid, label, count in db.execute(
            select(Machine.id, Machine.label, func.count(Booking.id))
            .join(Booking, Booking.machine_id == Machine.id)
            .where(Booking.slot_start >= day_start, Booking.slot_start < day_end)
            .group_by(Machine.id, Machine.label)
            .order_by(func.count(Booking.id).desc())
            .limit(5)
        ).all()
    ]

    return {
        "machines_total": len(states),
        "machines_busy_now": sum(1 for m in states if m["busy_now"]),
        "machines_out_of_order": sum(
            1 for m in states if m["status"] == MachineStatus.out_of_order
        ),
        "bookings_today": bookings_today or 0,
        "bookings_upcoming": upcoming or 0,
        "by_status": by_status,
        "busiest_machines": busiest,
    }
