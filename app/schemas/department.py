from typing import Optional
from pydantic import BaseModel

class DepartmentBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True

class DepartmentCreate(DepartmentBase):
    name: str

class DepartmentUpdate(DepartmentBase):
    pass

class DepartmentInDBBase(DepartmentBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class Department(DepartmentInDBBase):
    pass
