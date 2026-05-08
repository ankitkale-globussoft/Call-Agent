from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.db.session import get_db
from app.repositories.doctor_repository import doctor_repo
from app.repositories.department_repository import department_repo
from app.schemas.doctor import Doctor, DoctorCreate, DoctorUpdate
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Doctor])
async def search_doctors(
    db: AsyncSession = Depends(get_db),
    specialization: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, description="Search by name, bio, or specialization"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Search and filter doctors.
    """
    return await doctor_repo.search_doctors(
        db, 
        specialization=specialization,
        department_id=department_id,
        search_query=q,
        skip=skip,
        limit=limit
    )

@router.get("/{id}", response_model=Doctor)
async def read_doctor(
    id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get doctor by ID.
    """
    doctor = await doctor_repo.get_with_details(db, id=id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.post("/", response_model=Doctor)
async def create_doctor(
    *,
    db: AsyncSession = Depends(get_db),
    doctor_in: DoctorCreate,
    current_user: User = Depends(deps.PermissionChecker(["manage_doctors"]))
) -> Any:
    """
    Create new doctor profile (Admin only).
    """
    from app.models.user import Doctor as DoctorModel
    from sqlalchemy import select
    
    # 1. Check if department exists if provided
    if doctor_in.department_id:
        dept = await department_repo.get(db, id=doctor_in.department_id)
        if not dept:
            raise HTTPException(status_code=400, detail="Invalid department_id. Department not found.")

    # 2. Check if user already has a doctor profile
    res = await db.execute(select(DoctorModel).where(DoctorModel.user_id == doctor_in.user_id))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This user already has a doctor profile.")
    
    # 3. Create the doctor
    new_doctor = DoctorModel(**doctor_in.model_dump())
    db.add(new_doctor)
    await db.commit()
    
    return await doctor_repo.get_with_details(db, id=new_doctor.id)

@router.put("/{id}", response_model=Doctor)
async def update_doctor(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    doctor_in: DoctorUpdate,
    current_user: User = Depends(deps.PermissionChecker(["manage_doctors"]))
) -> Any:
    """
    Update doctor profile (Admin only).
    """
    doctor = await doctor_repo.get(db, id=id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    if doctor_in.department_id:
        dept = await department_repo.get(db, id=doctor_in.department_id)
        if not dept:
            raise HTTPException(status_code=400, detail="Invalid department_id. Department not found.")

    update_data = doctor_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)
    
    await db.commit()
    return await doctor_repo.get_with_details(db, id=id)

@router.delete("/{id}")
async def delete_doctor(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.PermissionChecker(["manage_doctors"]))
) -> Any:
    """
    Delete doctor profile (Admin only).
    """
    # 1. Fetch with details before deletion if we want to return it, 
    # but it's simpler to just return a success message to avoid MissingGreenlet.
    doctor = await doctor_repo.get(db, id=id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    await doctor_repo.remove(db, id=id)
    return {"status": "success", "message": f"Doctor with id {id} deleted successfully"}
