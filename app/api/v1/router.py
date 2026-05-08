from fastapi import APIRouter
from app.api.v1.endpoints import auth, departments, doctors

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
