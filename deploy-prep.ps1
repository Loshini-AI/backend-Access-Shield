$utf8 = New-Object Text.UTF8Encoding($false)
$be = Get-Location
$fe = "C:\Users\lokes\Desktop\AccessShield-X-IAM-Auditor-main\AccessShield-X-IAM-Auditor-main\artifacts\accessshield-x"

$req = @'
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
alembic>=1.11.0
python-dotenv>=1.0.0
python-multipart>=0.0.6
pandas>=2.0.0
httpx>=0.24.0
email-validator
'@
[IO.File]::WriteAllText((Join-Path $be 'requirements.txt'), $req, $utf8); "WROTE requirements.txt"

$admin = @'
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
'@
[IO.File]::WriteAllText((Join-Path $be 'app\api\routes\admin.py'), $admin, $utf8); "WROTE app\api\routes\admin.py"

$mp = Join-Path $be 'app\main.py'
$m = [IO.File]::ReadAllText($mp)
if (-not $m.Contains('seed_if_empty')) {
  $marker = 'if __name__ == "__main__":'
  if ($m.Contains($marker)) {
    $m = $m.Replace($marker, "from app.api.routes.admin import seed_if_empty`nseed_if_empty()`n`n`n" + $marker)
    [IO.File]::WriteAllText($mp, $m, $utf8); "PATCHED main.py"
  } else { "MISS: main.py marker not found" }
} else { "main.py already patched" }

$ex = Join-Path $be '.env.example'
$exText = [IO.File]::ReadAllText($ex)
if (-not $exText.Contains('ADMIN_KEY')) {
  [IO.File]::AppendAllText($ex, "`nADMIN_KEY=change-me`n", $utf8); "PATCHED .env.example"
}

$apiPath = Join-Path $fe 'src\services\api.ts'
$a = [IO.File]::ReadAllText($apiPath)
$oldR = 'request<ResetResult>("/api/admin/reset-demo", { method: "POST", body: "{}" });'
$newR = 'request<ResetResult>("/api/admin/reset-demo", { method: "POST", body: "{}", headers: { "Content-Type": "application/json", "X-Admin-Key": import.meta.env.VITE_ADMIN_KEY || "" } });'
if ($a.Contains($oldR)) { [IO.File]::WriteAllText($apiPath, $a.Replace($oldR, $newR), $utf8); "PATCHED api.ts" } else { "MISS: api.ts reset call not found (already patched?)" }

$vj = '{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }'
[IO.File]::WriteAllText((Join-Path $fe 'vercel.json'), $vj, $utf8); "WROTE vercel.json"

$fex = Join-Path $fe '.env.example'
$fexText = if (Test-Path $fex) { [IO.File]::ReadAllText($fex) } else { "" }
if (-not $fexText.Contains('VITE_ADMIN_KEY')) { [IO.File]::AppendAllText($fex, "`nVITE_ADMIN_KEY=change-me`n", $utf8); "PATCHED frontend .env.example" }
"DONE"