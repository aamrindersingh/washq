from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import service
from app.db import get_db
from app.models import Machine
from app.schemas import MachineCreate, MachineRead, MachineState, MachineStatusUpdate

router = APIRouter(prefix="/api/machines", tags=["machines"])


@router.get("", response_model=list[MachineState])
def list_machines(db: Session = Depends(get_db)):
    service.refresh_gauges(db)
    return service.machine_states(db)


@router.post("", response_model=MachineRead, status_code=status.HTTP_201_CREATED)
def add_machine(payload: MachineCreate, db: Session = Depends(get_db)):
    machine = Machine(label=payload.label, location=payload.location)
    db.add(machine)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"Machine {payload.label} already exists")
    db.refresh(machine)
    service.refresh_gauges(db)
    return machine


@router.put("/{machine_id}/status", response_model=MachineRead)
def set_machine_status(
    machine_id: int, payload: MachineStatusUpdate, db: Session = Depends(get_db)
):
    machine = db.get(Machine, machine_id)
    if machine is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such machine")
    machine.status = payload.status
    db.commit()
    db.refresh(machine)
    service.refresh_gauges(db)
    return machine


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.get(Machine, machine_id)
    if machine is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such machine")
    if machine.bookings:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Machine has bookings against it, cancel those first",
        )
    db.delete(machine)
    db.commit()
    service.refresh_gauges(db)
