from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from app.models.user import Appointment, AppointmentSlot, AppointmentStatus, Doctor, User
from app.repositories.base import BaseRepository

class AppointmentRepository(BaseRepository[Appointment]):
    async def create_appointment(
        self, 
        db: AsyncSession, 
        *, 
        patient_id: int, 
        doctor_id: int, 
        slot_id: int, 
        reason: Optional[str] = None
    ) -> Appointment:
        """
        Critical Booking Logic with Concurrency Handling
        """
        # 1. Lock the slot record to prevent concurrent bookings
        slot_query = (
            select(AppointmentSlot)
            .where(
                and_(
                    AppointmentSlot.id == slot_id,
                    AppointmentSlot.doctor_id == doctor_id
                )
            )
            .with_for_update() # ROW-LEVEL LOCK
        )
        
        result = await db.execute(slot_query)
        slot = result.scalar_one_or_none()
        
        if not slot:
            raise ValueError("Slot not found or does not belong to this doctor")
            
        if slot.is_booked:
            raise ValueError("This slot is already booked")
            
        # 2. Mark slot as booked
        slot.is_booked = True
        
        # 3. Create the appointment
        new_appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            slot_id=slot_id,
            reason=reason,
            status=AppointmentStatus.CONFIRMED # Auto-confirm for now, or use PENDING
        )
        
        db.add(new_appointment)
        
        # 4. Commit transaction
        try:
            await db.commit()
            await db.refresh(new_appointment)
        except Exception as e:
            await db.rollback()
            raise e
            
        return await self.get_with_details(db, id=new_appointment.id)

    async def get_with_details(self, db: AsyncSession, id: int) -> Optional[Appointment]:
        query = (
            select(Appointment)
            .where(Appointment.id == id)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor).joinedload(Doctor.user),
                joinedload(Appointment.doctor).joinedload(Doctor.department),
                joinedload(Appointment.slot)
            )
        )
        # Note: joinedload for doctor.user might need explicit import if it fails
        # but Doctor.user is defined in same models file.
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_patient_appointments(self, db: AsyncSession, patient_id: int) -> List[Appointment]:
        query = (
            select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .options(
                joinedload(Appointment.doctor).joinedload(Doctor.user),
                joinedload(Appointment.doctor).joinedload(Doctor.department),
                joinedload(Appointment.slot)
            )
            .order_by(Appointment.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_doctor_appointments(self, db: AsyncSession, doctor_id: int) -> List[Appointment]:
        query = (
            select(Appointment)
            .where(Appointment.doctor_id == doctor_id)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor).joinedload(Doctor.user),
                joinedload(Appointment.doctor).joinedload(Doctor.department),
                joinedload(Appointment.slot)
            )
            .order_by(Appointment.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

appointment_repo = AppointmentRepository(Appointment)
