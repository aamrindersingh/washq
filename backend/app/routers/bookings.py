import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import metrics, service
from app.db import get_db
from app.models import Booking, BookingStatus, Machine, MachineStatus
from app.schemas import BookingCreate, BookingPage, BookingRead, BookingUpdate

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _load(db: Session, booking_id: int) -> Booking:
    booking = db.scalars(
        select(Booking).options(selectinload(Booking.machine)).where(Booking.id == booking_id)
    ).first()
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such booking")
    return booking


@router.get("", response_model=BookingPage)
def list_bookings(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    machine_id: int | None = None,
    booking_status: BookingStatus | None = Query(None, alias="status"),
):
    query = select(Booking).options(selectinload(Booking.machine))
    count_query = select(func.count()).select_from(Booking)

    if machine_id is not None:
        query = query.where(Booking.machine_id == machine_id)
        count_query = count_query.where(Booking.machine_id == machine_id)
    if booking_status is not None:
        query = query.where(Booking.status == booking_status)
        count_query = count_query.where(Booking.status == booking_status)

    total = db.scalar(count_query) or 0
    rows = db.scalars(
        query.order_by(Booking.slot_start.desc()).offset((page - 1) * limit).limit(limit)
    ).all()

    return {
        "items": rows,
        "page": page,
        "limit": limit,
        "total_items": total,
        "total_pages": math.ceil(total / limit) if total else 0,
    }


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    return _load(db, booking_id)


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def book_slot(payload: BookingCreate, db: Session = Depends(get_db)):
    machine = db.get(Machine, payload.machine_id)
    if machine is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such machine")
    if machine.status == MachineStatus.out_of_order:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{machine.label} is out of order")

    if payload.slot_start < service.now_local():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "That slot is in the past")

    end = payload.slot_end
    clash = service.clashing_booking(db, machine.id, payload.slot_start, end)
    if clash is not None:
        # The whole point of the app. Say who has it and until when.
        metrics.double_booking_rejected.inc()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{machine.label} is taken until {clash.slot_end:%H:%M}",
        )

    booking = Booking(
        machine_id=machine.id,
        student_name=payload.student_name,
        room_number=payload.room_number,
        slot_start=payload.slot_start,
        slot_end=end,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    metrics.bookings_created.inc()
    service.refresh_gauges(db)
    return _load(db, booking.id)


@router.put("/{booking_id}", response_model=BookingRead)
def update_booking(booking_id: int, payload: BookingUpdate, db: Session = Depends(get_db)):
    booking = _load(db, booking_id)

    machine_id = payload.machine_id if payload.machine_id is not None else booking.machine_id
    start = payload.slot_start if payload.slot_start is not None else booking.slot_start
    end = service.slot_end_for(start)

    if payload.machine_id is not None and db.get(Machine, machine_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such machine")

    moving = payload.slot_start is not None or payload.machine_id is not None
    if moving:
        clash = service.clashing_booking(db, machine_id, start, end, ignore_booking_id=booking.id)
        if clash is not None:
            metrics.double_booking_rejected.inc()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"That slot is taken until {clash.slot_end:%H:%M}",
            )
        booking.machine_id = machine_id
        booking.slot_start = start
        booking.slot_end = end

    if payload.status is not None:
        if payload.status == BookingStatus.cancelled and booking.status != BookingStatus.cancelled:
            metrics.bookings_cancelled.inc()
        booking.status = payload.status

    db.commit()
    service.refresh_gauges(db)
    return _load(db, booking.id)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = _load(db, booking_id)
    if booking.status != BookingStatus.cancelled:
        booking.status = BookingStatus.cancelled
        metrics.bookings_cancelled.inc()
        db.commit()
    service.refresh_gauges(db)
