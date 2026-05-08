from typing import Optional, List
from pydantic import BaseModel
from app.schemas.user import User as UserSchema
from app.schemas.department import Department as DepartmentSchema

class DoctorBase(BaseModel):
    specialization: Optional[str] = None
    bio: Optional[str] = None
    experience_years: Optional[int] = 0
    consultation_fee: Optional[int] = 0
    department_id: Optional[int] = None

class DoctorCreate(DoctorBase):
    user_id: int
    specialization: str

class DoctorUpdate(DoctorBase):
    pass

class DoctorInDBBase(DoctorBase):
    id: Optional[int] = None
    user_id: int

    class Config:
        from_attributes = True

class Doctor(DoctorInDBBase):
    user: Optional[UserSchema] = None
    department: Optional[DepartmentSchema] = None

class DoctorSearch(BaseModel):
    specialization: Optional[str] = None
    department_id: Optional[int] = None
    query: Optional[str] = None
