from app.repositories.base import BaseRepository
from app.models.user import Department
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

class DepartmentRepository(BaseRepository[Department]):
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Department]:
        query = select(Department).where(Department.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

department_repo = DepartmentRepository(Department)
