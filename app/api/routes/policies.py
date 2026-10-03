from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["IAM Policies"])


@router.post("/upload", summary="Upload IAM Policies", description="Upload IAM policies in JSON or CSV format.")
async def upload_policies(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".json", ".csv")):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .json and .csv files are supported.")

    content = await file.read()
    result = PolicyService.process_and_save_policies(db, content, file.filename)
    return {
        "message": "IAM policies uploaded and parsed successfully",
        "saved_policies_count": result["saved_policies_count"]
    }
