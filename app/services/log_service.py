import json
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.access_log import AccessLog
from app.models.user import User


class LogService:
    """
    Service for parsing, validating, and storing access logs.
    """

    @staticmethod
    def process_and_save_logs(
        db: Session,
        content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Parses JSON or CSV content, validates fields, and saves logs into database.
        """
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

        raw_items = []
        if filename.endswith(".json"):
            try:
                data = json.loads(content.decode("utf-8"))
                if isinstance(data, list):
                    raw_items = data
                elif isinstance(data, dict) and "logs" in data:
                    raw_items = data["logs"]
                else:
                    raise ValueError("JSON must contain an array of log items or a 'logs' key.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")

        elif filename.endswith(".csv"):
            try:
                df = pd.read_csv(pd.io.common.BytesIO(content))
                raw_items = df.to_dict(orient="records")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use .json or .csv.")

        saved_count = 0
        errors = []

        existing_users = {u.id for u in db.query(User).all()}

        logs_to_insert = []
        for idx, item in enumerate(raw_items):
            try:
                user_id = item.get("user_id") or item.get("user")
                service = item.get("service")
                action = item.get("action")
                resource = item.get("resource")

                if not user_id or not service or not action or not resource:
                    errors.append(f"Row {idx + 1}: Missing required fields (user_id/user, service, action, resource).")
                    continue

                if user_id not in existing_users:
                    new_user = User(
                        id=user_id,
                        name=f"User {user_id}",
                        email=f"{user_id.lower()}@example.com",
                        role="Engineer",
                        department="DevOps",
                        status="Active"
                    )
                    db.add(new_user)
                    db.flush()
                    existing_users.add(user_id)

                ts_raw = item.get("timestamp")
                timestamp_val = datetime.now(timezone.utc)
                if ts_raw:
                    try:
                        timestamp_val = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                    except Exception:
                        pass

                log_obj = AccessLog(
                    timestamp=timestamp_val,
                    user_id=str(user_id),
                    service=str(service),
                    action=str(action),
                    resource=str(resource),
                    status=str(item.get("status", "SUCCESS")),
                    source_ip=str(item.get("source_ip", "127.0.0.1")),
                    region=str(item.get("region", "us-east-1"))
                )
                logs_to_insert.append(log_obj)
                saved_count += 1
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")

        if logs_to_insert:
            db.bulk_save_objects(logs_to_insert)
            db.commit()

        return {
            "saved_count": saved_count,
            "errors_count": len(errors),
            "errors": errors[:10]
        }
