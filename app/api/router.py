from fastapi import APIRouter
from app.api.v1.patients import router as patients_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

# Include versioned routers
api_router.include_router(patients_router)
api_router.include_router(webhooks_router)
api_router.include_router(appointments_router)
api_router.include_router(health_router)
