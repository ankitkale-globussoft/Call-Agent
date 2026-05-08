from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from app.api import deps
from app.db.session import get_db
from app.repositories.schedule_repository import schedule_repo
from app.repositories.doctor_repository import doctor_repo
from app.schemas.schedule import (
    Availability, AvailabilityCreate, AvailabilityUpdate,
    Leave, LeaveCreate, LeaveUpdate,
    Slot, SlotGenerationRequest
)
from app.models.user import User, DoctorAvailability, DoctorLeave

router = APIRouter()

# --- Availability ---

@router.get("/availability/{doctor_id}", response_model=List[Availability])
async def get_doctor_availability(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await schedule_repo.get_availability(db, doctor_id=doctor_id)

@router.post("/availability", response_model=Availability)
async def add_doctor_availability(
    *,
    db: AsyncSession = Depends(get_db),
    availability_in: AvailabilityCreate,
    current_user: User = Depends(deps.PermissionChecker(["manage_schedule"]))
) -> Any:
    doctor = await doctor_repo.get(db, id=availability_in.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    new_avail = DoctorAvailability(**availability_in.model_dump())
    return await schedule_repo.add_availability(db, obj_in=new_avail)

@router.put("/availability/{id}", response_model=Availability)
async def update_doctor_availability(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    availability_in: AvailabilityUpdate,
    current_user: User = Depends(deps.PermissionChecker(["manage_schedule"]))
) -> Any:
    res = await db.execute(select(DoctorAvailability).where(DoctorAvailability.id == id))
    availability = res.scalar_one_or_none()
    if not availability:
        raise HTTPException(status_code=404, detail="Availability entry not found")
    
    update_data = availability_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(availability, field, value)
    
    await db.commit()
    await db.refresh(availability)
    return availability

@router.delete("/availability/{id}")
async def delete_doctor_availability(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.PermissionChecker(["manage_schedule"]))
) -> Any:
    res = await db.execute(select(DoctorAvailability).where(DoctorAvailability.id == id))
    availability = res.scalar_one_or_none()
    if not availability:
        raise HTTPException(status_code=404, detail="Availability entry not found")
    
    await db.delete(availability)
    await db.commit()
    return {"status": "success", "message": "Availability entry deleted"}

# --- Leaves ---

@router.get("/leaves/{doctor_id}", response_model=List[Leave])
async def get_doctor_leaves(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await schedule_repo.get_leaves(db, doctor_id=doctor_id)

@router.post("/leaves", response_model=Leave)
async def add_doctor_leave(
    *,
    db: AsyncSession = Depends(get_db),
    leave_in: LeaveCreate,
    current_user: User = Depends(deps.PermissionChecker(["manage_schedule"]))
) -> Any:
    doctor = await doctor_repo.get(db, id=leave_in.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    new_leave = DoctorLeave(**leave_in.model_dump())
    return await schedule_repo.add_leave(db, obj_in=new_leave)

@router.put("/leaves/{id}", response_model=Leave)
async def update_doctor_leave(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    leave_in: LeaveUpdate,
    current_user: User = Depends(deps.PermissionChecker(["manage_schedule"]))
) -> Any:
    res = await db.execute(select(DoctorLeave).where(DoctorLeave.id == id))
    leave = res.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave entry not found")
    
    update_data = leave_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(leave, field, value)
    
    await db.commit()
    await db.refresh(leave)
    return leave

@router.delete("/leaves/{id}")
async def delete_doctor_leave(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.PermissionChecker(["manage_schedule"]))
) -> Any:
    res = await db.execute(select(DoctorLeave).where(DoctorLeave.id == id))
    leave = res.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave entry not found")
    
    await db.delete(leave)
    await db.commit()
    return {"status": "success", "message": "Leave entry deleted"}

# --- Slots ---

@router.post("/generate-slots", response_model=List[Slot])
async def generate_slots(
    *,
    db: AsyncSession = Depends(get_db),
    req: SlotGenerationRequest,
    current_user: User = Depends(deps.PermissionChecker(["manage_schedule"]))
) -> Any:
    return await schedule_repo.generate_slots(
        db, 
        doctor_id=req.doctor_id, 
        start_date=req.start_date, 
        end_date=req.end_date
    )

@router.get("/slots/{doctor_id}", response_model=List[Slot])
async def get_slots(
    doctor_id: int,
    target_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await schedule_repo.get_slots(db, doctor_id=doctor_id, target_date=target_date)
