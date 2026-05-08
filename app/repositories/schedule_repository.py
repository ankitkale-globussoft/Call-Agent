from datetime import date, datetime, time, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from app.models.user import DoctorAvailability, DoctorLeave, AppointmentSlot, Doctor
import logging

logger = logging.getLogger("app")

class ScheduleRepository:
    async def get_availability(self, db: AsyncSession, doctor_id: int) -> List[DoctorAvailability]:
        query = select(DoctorAvailability).where(DoctorAvailability.doctor_id == doctor_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def add_availability(self, db: AsyncSession, obj_in: DoctorAvailability) -> DoctorAvailability:
        db.add(obj_in)
        await db.commit()
        await db.refresh(obj_in)
        return obj_in

    async def get_leaves(self, db: AsyncSession, doctor_id: int) -> List[DoctorLeave]:
        query = select(DoctorLeave).where(DoctorLeave.doctor_id == doctor_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def add_leave(self, db: AsyncSession, obj_in: DoctorLeave) -> DoctorLeave:
        db.add(obj_in)
        await db.commit()
        await db.refresh(obj_in)
        return obj_in

    async def generate_slots(
        self, 
        db: AsyncSession, 
        doctor_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[AppointmentSlot]:
        print(f"--- START GENERATION: {start_date} to {end_date} ---")
        
        # 1. Get doctor's weekly availability
        availabilities = await self.get_availability(db, doctor_id)
        print(f"Found {len(availabilities)} availability rules")

        # 2. Get doctor's leaves in the range
        leaves_query = select(DoctorLeave).where(
            and_(
                DoctorLeave.doctor_id == doctor_id,
                DoctorLeave.leave_date >= start_date,
                DoctorLeave.leave_date <= end_date
            )
        )
        leaves_res = await db.execute(leaves_query)
        leave_dates = {l.leave_date for l in leaves_res.scalars().all()}

        current_date = start_date
        while current_date <= end_date:
            print(f"Checking date: {current_date}")
            if current_date in leave_dates:
                print(f"SKIP: {current_date} is a leave date")
                current_date += timedelta(days=1)
                continue
            
            day_of_week = current_date.weekday()
            day_availabilities = [a for a in availabilities if a.day_of_week == day_of_week]
            print(f"  Day of week: {day_of_week}, Rules found: {len(day_availabilities)}")
            
            for avail in day_availabilities:
                slot_time = datetime.combine(current_date, avail.start_time)
                end_day_time = datetime.combine(current_date, avail.end_time)
                
                print(f"    Processing rule: {avail.start_time} - {avail.end_time}")
                
                while slot_time + timedelta(minutes=avail.slot_duration) <= end_day_time:
                    slot_end = slot_time + timedelta(minutes=avail.slot_duration)
                    
                    exists_query = select(AppointmentSlot).where(
                        and_(
                            AppointmentSlot.doctor_id == doctor_id,
                            AppointmentSlot.start_time == slot_time
                        )
                    )
                    exists_res = await db.execute(exists_query)
                    exists = exists_res.scalar_one_or_none()
                    
                    if not exists:
                        print(f"      CREATE: {slot_time}")
                        new_slot = AppointmentSlot(
                            doctor_id=doctor_id,
                            start_time=slot_time,
                            end_time=slot_end,
                            is_booked=False
                        )
                        db.add(new_slot)
                    else:
                        print(f"      EXISTS: {slot_time}")
                    
                    slot_time = slot_end
            
            current_date += timedelta(days=1)
            
        await db.commit()
        return await self.get_slots_in_range(db, doctor_id, start_date, end_date)

    async def get_slots_in_range(self, db: AsyncSession, doctor_id: int, start_date: date, end_date: date) -> List[AppointmentSlot]:
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        query = select(AppointmentSlot).where(
            and_(
                AppointmentSlot.doctor_id == doctor_id,
                AppointmentSlot.start_time >= start_dt,
                AppointmentSlot.start_time <= end_dt
            )
        ).order_by(AppointmentSlot.start_time)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_slots(
        self, 
        db: AsyncSession, 
        doctor_id: int, 
        target_date: Optional[date] = None
    ) -> List[AppointmentSlot]:
        if target_date:
            return await self.get_slots_in_range(db, doctor_id, target_date, target_date)
        
        query = select(AppointmentSlot).where(AppointmentSlot.doctor_id == doctor_id).order_by(AppointmentSlot.start_time)
        result = await db.execute(query)
        return result.scalars().all()

schedule_repo = ScheduleRepository()
