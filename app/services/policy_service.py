import json
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.policy import Policy
from app.models.permission import Permission
from app.models.user import User


class PolicyService:
    """
    Service for parsing, validating, and storing IAM policies.
    """

    @staticmethod
    def process_and_save_policies(
        db: Session,
        content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Parses JSON or CSV policies file and saves policies and permissions.
        """
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

        raw_items = []
        if filename.endswith(".json"):
            try:
                data = json.loads(content.decode("utf-8"))
                if isinstance(data, list):
                    raw_items = data
                elif isinstance(data, dict) and "policies" in data:
                    raw_items = data["policies"]
                else:
                    raw_items = [data]
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

        saved_policies = 0
        existing_users = {u.id for u in db.query(User).all()}

        for idx, item in enumerate(raw_items):
            policy_id = item.get("id") or item.get("policy_id") or f"pol-up-{idx + 1}"
            policy_name = item.get("policy_name") or item.get("policy") or f"Policy-{policy_id}"
            user_id = item.get("user_id") or item.get("user")
            service = item.get("service", "s3")
            description = item.get("description", "Uploaded IAM Policy")

            if not user_id:
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

            existing_pol = db.query(Policy).filter(Policy.id == policy_id).first()
            if existing_pol:
                db.delete(existing_pol)
                db.flush()

            pol_obj = Policy(
                id=policy_id,
                policy_name=policy_name,
                user_id=user_id,
                service=service,
                description=description
            )
            db.add(pol_obj)
            db.flush()

            permissions_data = item.get("permissions", [])
            if not permissions_data and ("action" in item or "resource" in item):
                permissions_data = [{
                    "effect": item.get("effect", "Allow"),
                    "action": item.get("action", "*"),
                    "resource": item.get("resource", "*")
                }]

            for perm_item in permissions_data:
                perm_obj = Permission(
                    policy_id=policy_id,
                    effect=perm_item.get("effect", "Allow"),
                    action=perm_item.get("action", "*"),
                    resource=perm_item.get("resource", "*")
                )
                db.add(perm_obj)

            saved_policies += 1

        db.commit()

        return {
            "saved_policies_count": saved_policies,
            "status": "success"
        }
