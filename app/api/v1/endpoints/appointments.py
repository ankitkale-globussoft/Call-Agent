from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.db.session import get_db
from app.repositories.appointment_repository import appointment_repo
from app.schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from app.models.user import User, AppointmentStatus

router = APIRouter()

@router.post("/", response_model=Appointment)
async def book_appointment(
    *,
    db: AsyncSession = Depends(get_db),
    appointment_in: AppointmentCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Book a new appointment.
    """
    try:
        return await appointment_repo.create_appointment(
            db,
            patient_id=current_user.id,
            doctor_id=appointment_in.doctor_id,
            slot_id=appointment_in.slot_id,
            reason=appointment_in.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")

@router.get("/my-appointments", response_model=List[Appointment])
async def get_my_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get all appointments for the current logged-in patient.
    """
    return await appointment_repo.get_patient_appointments(db, patient_id=current_user.id)

@router.get("/doctor/{doctor_id}", response_model=List[Appointment])
async def get_doctor_appointments(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.PermissionChecker(["manage_appointments"]))
) -> Any:
    """
    Get all appointments for a specific doctor (Admin/Staff only).
    """
    return await appointment_repo.get_doctor_appointments(db, doctor_id=doctor_id)

@router.get("/{id}", response_model=Appointment)
async def get_appointment(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get detailed information about a specific appointment.
    """
    appointment = await appointment_repo.get_with_details(db, id=id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Security: only patient or admin/doctor can see it
    if appointment.patient_id != current_user.id and not current_user.is_superuser:
        # Check if user is the doctor
        doctor_profile = getattr(current_user, 'doctor_profile', None)
        if not doctor_profile or doctor_profile.id != appointment.doctor_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this appointment")
            
    return appointment

@router.patch("/{id}/status", response_model=Appointment)
async def update_appointment_status(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    status_update: AppointmentUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update appointment status (Confirm, Cancel, Complete).
    """
    appointment = await appointment_repo.get(db, id=id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Logic for who can update what status
    if status_update.status == AppointmentStatus.CANCELLED:
        # Both patient and clinic can cancel
        if appointment.patient_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
            
        # Re-open the slot if cancelled
        from app.models.user import AppointmentSlot
        slot_res = await db.execute(select(AppointmentSlot).where(AppointmentSlot.id == appointment.slot_id))
        slot = slot_res.scalar_one_or_none()
        if slot:
            slot.is_booked = False
            
    elif status_update.status in [AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED]:
        # Only admin or doctor can confirm/complete
        if not current_user.is_superuser:
             # Check if current user is the doctor for this appointment
             doctor_profile = getattr(current_user, 'doctor_profile', None)
             if not doctor_profile or doctor_profile.id != appointment.doctor_id:
                 raise HTTPException(status_code=403, detail="Only staff or the doctor can update this status")

    appointment.status = status_update.status
    await db.commit()
    return await appointment_repo.get_with_details(db, id=id)
