from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from app.repositories.base import BaseRepository
from app.models.user import Doctor, User

class DoctorRepository(BaseRepository[Doctor]):
    async def get_with_details(self, db: AsyncSession, id: int) -> Optional[Doctor]:
        query = (
            select(Doctor)
            .where(Doctor.id == id)
            .options(joinedload(Doctor.user), joinedload(Doctor.department))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def search_doctors(
        self, 
        db: AsyncSession, 
        *, 
        specialization: Optional[str] = None,
        department_id: Optional[int] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Doctor]:
        query = select(Doctor).options(joinedload(Doctor.user), joinedload(Doctor.department))
        
        if specialization:
            query = query.where(Doctor.specialization.ilike(f"%{specialization}%"))
        
        if department_id:
            query = query.where(Doctor.department_id == department_id)
            
        if search_query:
            # Search in doctor specialization, bio, or user full_name
            query = query.join(Doctor.user).where(
                or_(
                    Doctor.specialization.ilike(f"%{search_query}%"),
                    Doctor.bio.ilike(f"%{search_query}%"),
                    User.full_name.ilike(f"%{search_query}%"),
                    User.email.ilike(f"%{search_query}%")
                )
            )
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

doctor_repo = DoctorRepository(Doctor)
