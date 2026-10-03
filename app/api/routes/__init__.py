from app.api.routes.logs import router as logs_router
from app.api.routes.policies import router as policies_router
from app.api.routes.audit import router as audit_router
from app.api.routes.findings import router as findings_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.reports import router as reports_router
from app.api.routes.simulator import router as simulator_router

__all__ = [
    "logs_router",
    "policies_router",
    "audit_router",
    "findings_router",
    "evidence_router",
    "recommendations_router",
    "reports_router",
    "simulator_router",
]
