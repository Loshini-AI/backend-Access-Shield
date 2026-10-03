from app.api.routes.admin import router as admin_router
from fastapi import APIRouter
from app.api.routes import (
    logs_router,
    policies_router,
    audit_router,
    findings_router,
    evidence_router,
    recommendations_router,
    reports_router,
    simulator_router,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(logs_router)
api_router.include_router(policies_router)
api_router.include_router(audit_router)
api_router.include_router(findings_router)
api_router.include_router(evidence_router)
api_router.include_router(recommendations_router)
api_router.include_router(reports_router)
api_router.include_router(simulator_router)
api_router.include_router(admin_router)
