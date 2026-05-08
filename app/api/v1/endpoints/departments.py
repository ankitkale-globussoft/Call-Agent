from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.db.session import get_db
from app.repositories.department_repository import department_repo
from app.schemas.department import Department, DepartmentCreate, DepartmentUpdate
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Department])
async def read_departments(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return await department_repo.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=Department)
async def create_department(
    *,
    db: AsyncSession = Depends(get_db),
    department_in: DepartmentCreate,
    current_user: User = Depends(deps.PermissionChecker(["manage_departments"]))
) -> Any:
    department = await department_repo.get_by_name(db, name=department_in.name)
    if department:
        raise HTTPException(status_code=400, detail="Department already exists")
    
    from app.models.user import Department as DepartmentModel
    data = department_in.dict() if hasattr(department_in, "dict") else department_in.model_dump()
    new_dept = DepartmentModel(**data)
    return await department_repo.create(db, obj_in=new_dept)

@router.put("/{id}", response_model=Department)
async def update_department(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    department_in: DepartmentUpdate,
    current_user: User = Depends(deps.PermissionChecker(["manage_departments"]))
) -> Any:
    # 1. Get the existing department
    department = await department_repo.get(db, id=id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # 2. Check for name uniqueness if name is provided in update
    if department_in.name is not None and department_in.name != department.name:
        existing_dept = await department_repo.get_by_name(db, name=department_in.name)
        if existing_dept:
            raise HTTPException(
                status_code=400, 
                detail="A department with this name already exists."
            )
    
    # 3. Apply updates
    data = department_in.dict(exclude_unset=True) if hasattr(department_in, "dict") else department_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(department, field, value)
    
    try:
        await db.commit()
        await db.refresh(department)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    return department

@router.delete("/{id}", response_model=Department)
async def delete_department(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.PermissionChecker(["manage_departments"]))
) -> Any:
    department = await department_repo.get(db, id=id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return await department_repo.remove(db, id=id)
