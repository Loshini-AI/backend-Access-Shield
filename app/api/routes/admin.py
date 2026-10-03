import os
from pathlib import Path
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.access_log import AccessLog
from app.models.finding import Finding
from app.models.policy import Policy
from app.models.recommendation import Recommendation
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Demo Admin"])
DATA = Path(__file__).resolve().parents[3] / "data"
STATIC_TYPES = {"WILDCARD_ACTION", "WILDCARD_RESOURCE", "DESTRUCTIVE_PERMISSION"}


def require_key(x_admin_key: str = Header(default="")):
    key = os.getenv("ADMIN_KEY", "")
    if key and x_admin_key != key:
        raise HTTPException(status_code=401, detail="Admin key required")


def _post_file(client, route: str, fname: str):
    with open(DATA / fname, "rb") as fh:
        return client.post(route, files={"file": (fname, fh, "application/json")})


def seed_if_empty():
    """Load the demo policies and events when the database is empty."""
    try:
        db = next(get_db())
        try:
            has = db.query(Policy).count() > 0 or db.query(AccessLog).count() > 0
        finally:
            db.close()
        if has:
            return
        from fastapi.testclient import TestClient
        from app.main import app
        c = TestClient(app)
        _post_file(c, "/api/policies/upload", "iam_policies.json")
        _post_file(c, "/api/logs/upload", "access_logs.json")
        db = next(get_db())
        try:
            AuditService().run_audit(db)
        finally:
            db.close()
        print("Demo data loaded on startup")
    except Exception as e:
        print("Startup seed skipped:", e)


@router.post("/reset-demo", dependencies=[Depends(require_key)],
             summary="Restore the original 500 simulated events and re-audit")
def reset_demo(db: Session = Depends(get_db)):
    db.query(Recommendation).delete()
    db.query(Finding).delete()
    db.query(AccessLog).delete()
    db.commit()
    from fastapi.testclient import TestClient
    from app.main import app
    r = _post_file(TestClient(app), "/api/logs/upload", "access_logs.json")
    report = AuditService().run_audit(db)
    return {
        "reloaded_events": r.json().get("saved_count"),
        "audit_id": report.audit_id,
        "events_analyzed": report.events_analyzed,
        "least_privilege_score": report.least_privilege_score,
    }


@router.get("/metrics", summary="Comparison numbers: static scan vs log-based audit")
def metrics(db: Session = Depends(get_db)):
    f = db.query(Finding).all()
    by_type, by_sev = {}, {}
    for x in f:
        by_type[x.finding_type] = by_type.get(x.finding_type, 0) + 1
        by_sev[x.severity] = by_sev.get(x.severity, 0) + 1
    total = len(f)
    static_found = sum(v for k, v in by_type.items() if k in STATIC_TYPES)
    log_only = total - static_found
    recs = db.query(Recommendation).all()
    avg = round(sum((r.risk_reduction or 0) for r in recs) / len(recs), 1) if recs else 0.0
    return {
        "total_findings": total,
        "by_type": by_type,
        "by_severity": by_sev,
        "static_detectable": static_found,
        "log_evidence_only": log_only,
        "uplift_pct": round(100 * log_only / static_found) if static_found else None,
        "users_flagged": len({x.user_id for x in f}),
        "users_total": db.query(User).count(),
        "events": db.query(AccessLog).count(),
        "avg_risk_reduction": avg,
    }