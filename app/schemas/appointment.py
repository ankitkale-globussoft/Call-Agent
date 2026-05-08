from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.models.user import AppointmentStatus
from app.schemas.user import User as UserSchema
from app.schemas.doctor import Doctor as DoctorSchema
from app.schemas.schedule import Slot as SlotSchema

class AppointmentBase(BaseModel):
    reason: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    doctor_id: int
    slot_id: int
    # patient_id will be taken from the current user

class AppointmentUpdate(AppointmentBase):
    status: Optional[AppointmentStatus] = None

class AppointmentInDBBase(AppointmentBase):
    id: int
    patient_id: int
    doctor_id: int
    slot_id: int
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Appointment(AppointmentInDBBase):
    patient: Optional[UserSchema] = None
    doctor: Optional[DoctorSchema] = None
    slot: Optional[SlotSchema] = None
