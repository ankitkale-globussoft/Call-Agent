import asyncio
from datetime import date
from sqlalchemy import select
from app.db.session import SessionLocal
from app.repositories.schedule_repository import schedule_repo

async def test_gen():
    async with SessionLocal() as db:
        print("Testing generation for May 9 to May 10")
        slots = await schedule_repo.generate_slots(
            db, 
            doctor_id=1, 
            start_date=date(2026, 5, 9), 
            end_date=date(2026, 5, 10)
        )
        print(f"Generated/Found {len(slots)} slots")
        for s in slots:
            print(f"Slot: {s.start_time}")

if __name__ == "__main__":
    asyncio.run(test_gen())
