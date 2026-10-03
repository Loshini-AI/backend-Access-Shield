from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.log_service import LogService

router = APIRouter(prefix="/logs", tags=["Access Logs"])


@router.post("/upload", summary="Upload Access Logs", description="Upload access log data in JSON or CSV format for IAM audit processing.")
async def upload_logs(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".json", ".csv")):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .json and .csv files are supported.")

    content = await file.read()
    result = LogService.process_and_save_logs(db, content, file.filename)
    return {
        "message": "Access logs processed successfully",
        "saved_count": result["saved_count"],
        "errors_count": result["errors_count"],
        "errors": result["errors"]
    }
