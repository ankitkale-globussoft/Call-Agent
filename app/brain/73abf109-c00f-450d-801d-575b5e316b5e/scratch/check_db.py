import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import DoctorAvailability, AppointmentSlot, DoctorLeave

async def check():
    async with SessionLocal() as db:
        print("--- Doctor Availabilities ---")
        res = await db.execute(select(DoctorAvailability))
        for a in res.scalars().all():
            print(f"ID: {a.id}, Doctor: {a.doctor_id}, DOW: {a.day_of_week}, Start: {a.start_time}, End: {a.end_time}")
            
        print("\n--- Doctor Leaves ---")
        res = await db.execute(select(DoctorLeave))
        for l in res.scalars().all():
            print(f"ID: {l.id}, Doctor: {l.doctor_id}, Date: {l.leave_date}")

        print("\n--- Appointment Slots ---")
        res = await db.execute(select(AppointmentSlot))
        for s in res.scalars().all():
            print(f"ID: {s.id}, Doctor: {s.doctor_id}, Start: {s.start_time}")

if __name__ == "__main__":
    asyncio.run(check())
