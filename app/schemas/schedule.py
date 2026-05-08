from typing import Optional, List
from pydantic import BaseModel
from datetime import date, time, datetime

# Availability
class AvailabilityBase(BaseModel):
    day_of_week: int # 0-6
    start_time: time
    end_time: time
    slot_duration: int = 30

class AvailabilityCreate(AvailabilityBase):
    doctor_id: int

class AvailabilityUpdate(BaseModel):
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration: Optional[int] = None

class Availability(AvailabilityBase):
    id: int
    doctor_id: int
    class Config:
        from_attributes = True

# Leaves
class LeaveBase(BaseModel):
    leave_date: date
    reason: Optional[str] = None

class LeaveCreate(LeaveBase):
    doctor_id: int

class LeaveUpdate(BaseModel):
    leave_date: Optional[date] = None
    reason: Optional[str] = None

class Leave(LeaveBase):
    id: int
    doctor_id: int
    class Config:
        from_attributes = True

# Slots
class SlotBase(BaseModel):
    start_time: datetime
    end_time: datetime
    is_booked: bool = False

class Slot(SlotBase):
    id: int
    doctor_id: int
    class Config:
        from_attributes = True

class SlotGenerationRequest(BaseModel):
    doctor_id: int
    start_date: date
    end_date: date
