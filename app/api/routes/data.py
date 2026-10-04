from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.access_log import AccessLog
from app.models.policy import Policy

router = APIRouter(prefix="/data", tags=["Data Browser"])


@router.get("/logs", summary="Browse access logs (paged, filterable)")
def list_logs(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = "",
    service: str = "",
    status: str = "",
    q: str = "",
    db: Session = Depends(get_db),
):
    qry = db.query(AccessLog)
    if user_id:
        qry = qry.filter(AccessLog.user_id == user_id)
    if service:
        qry = qry.filter(AccessLog.service == service)
    if status:
        qry = qry.filter(AccessLog.status == status)
    if q:
        like = f"%{q}%"
        qry = qry.filter(
            AccessLog.action.ilike(like) | AccessLog.resource.ilike(like) | AccessLog.user_id.ilike(like)
        )
    total = qry.count()
    rows = qry.order_by(AccessLog.timestamp.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "user_id": r.user_id,
                "service": r.service,
                "action": r.action,
                "resource": r.resource,
                "status": getattr(r, "status", None),
                "region": getattr(r, "region", None),
            }
            for r in rows
        ],
    }


@router.get("/facets", summary="Distinct values for log filters")
def facets(db: Session = Depends(get_db)):
    users = [r[0] for r in db.query(AccessLog.user_id).distinct().order_by(AccessLog.user_id).all()]
    services = [r[0] for r in db.query(AccessLog.service).distinct().order_by(AccessLog.service).all()]
    statuses = [r[0] for r in db.query(AccessLog.status).distinct().all() if r[0]]
    return {"users": users, "services": services, "statuses": statuses}


@router.get("/policies", summary="List IAM policies with their statements")
def list_policies(db: Session = Depends(get_db)):
    out = []
    for p in db.query(Policy).all():
        out.append(
            {
                "id": str(p.id),
                "policy_name": p.policy_name,
                "user_id": p.user_id,
                "service": p.service,
                "permissions": [
                    {"effect": x.effect, "action": x.action, "resource": x.resource}
                    for x in p.permissions
                ],
            }
        )
    return out