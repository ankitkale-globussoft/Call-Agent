from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, Text, Date, Time, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base

# Association tables for Many-to-Many
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    users = relationship("User", back_populates="department")
    doctors = relationship("Doctor", back_populates="department")

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    specialization = Column(String, index=True, nullable=False)
    bio = Column(Text, nullable=True)
    experience_years = Column(Integer, default=0)
    consultation_fee = Column(Integer, default=0)
    
    user = relationship("User", back_populates="doctor_profile")
    department = relationship("Department", back_populates="doctors")
    availabilities = relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    leaves = relationship("DoctorLeave", back_populates="doctor", cascade="all, delete-orphan")
    slots = relationship("AppointmentSlot", back_populates="doctor", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)

# --- New Models for Schedule & Availability ---

class DoctorAvailability(Base):
    __tablename__ = "doctor_availabilities"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0-6 (Mon-Sun)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration = Column(Integer, default=30) # in minutes
    
    doctor = relationship("Doctor", back_populates="availabilities")

class DoctorLeave(Base):
    __tablename__ = "doctor_leaves"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    leave_date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    
    doctor = relationship("Doctor", back_populates="leaves")

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)
    
    doctor = relationship("Doctor", back_populates="slots")
