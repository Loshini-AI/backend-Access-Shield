import os
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models import User, Policy, Permission, AccessLog


def seed_database(db: Session = None):
    """
    Idempotent seed script to load demo users, IAM policies, and access logs into database.
    """
    close_db_on_exit = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db_on_exit = True

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        users_file = os.path.join(base_dir, "data", "users.json")
        policies_file = os.path.join(base_dir, "data", "iam_policies.json")
        logs_file = os.path.join(base_dir, "data", "access_logs.json")

        print("--- STARTING DATABASE SEED PROCESS ---")

        # 1. Seed Users
        if os.path.exists(users_file):
            with open(users_file, "r") as f:
                users_data = json.load(f)

            user_count = 0
            for u in users_data:
                user_id = u["id"]
                existing = db.query(User).filter(User.id == user_id).first()
                if not existing:
                    user_obj = User(
                        id=user_id,
                        name=u["name"],
                        email=u["email"],
                        role=u["role"],
                        department=u["department"],
                        status=u.get("status", "Active")
                    )
                    db.add(user_obj)
                    user_count += 1
            db.commit()
            print(f"Seeded {user_count} new users (Total: {len(users_data)}).")

        # 2. Seed IAM Policies
        if os.path.exists(policies_file):
            with open(policies_file, "r") as f:
                policies_data = json.load(f)

            policy_count = 0
            for p in policies_data:
                pol_id = p["id"]
                existing_pol = db.query(Policy).filter(Policy.id == pol_id).first()
                if not existing_pol:
                    pol_obj = Policy(
                        id=pol_id,
                        policy_name=p["policy_name"],
                        user_id=p["user_id"],
                        service=p["service"],
                        description=p.get("description", "")
                    )
                    db.add(pol_obj)
                    db.flush()

                    for perm in p.get("permissions", []):
                        perm_obj = Permission(
                            policy_id=pol_id,
                            effect=perm.get("effect", "Allow"),
                            action=perm["action"],
                            resource=perm["resource"]
                        )
                        db.add(perm_obj)
                    policy_count += 1
            db.commit()
            print(f"Seeded {policy_count} new policies (Total: {len(policies_data)}).")

        # 3. Seed Access Logs
        if os.path.exists(logs_file):
            with open(logs_file, "r") as f:
                logs_data = json.load(f)

            existing_log_count = db.query(AccessLog).count()
            if existing_log_count < len(logs_data):
                db.query(AccessLog).delete()
                db.flush()

                logs_to_insert = []
                for l in logs_data:
                    ts = datetime.now(timezone.utc)
                    if "timestamp" in l:
                        try:
                            ts = datetime.fromisoformat(l["timestamp"].replace("Z", "+00:00"))
                        except Exception:
                            pass

                    logs_to_insert.append(AccessLog(
                        user_id=l["user_id"],
                        service=l["service"],
                        action=l["action"],
                        resource=l["resource"],
                        status=l.get("status", "SUCCESS"),
                        source_ip=l.get("source_ip", "127.0.0.1"),
                        region=l.get("region", "us-east-1"),
                        timestamp=ts
                    ))
                db.bulk_save_objects(logs_to_insert)
                db.commit()
                print(f"Seeded {len(logs_to_insert)} access log records.")
            else:
                print(f"Access logs already present ({existing_log_count} existing records). Skipping re-seed.")

        print("--- DATABASE SEED COMPLETED SUCCESSFULLY ---")

    except Exception as e:
        db.rollback()
        print(f"Error during database seed: {str(e)}")
        raise e
    finally:
        if close_db_on_exit:
            db.close()


if __name__ == "__main__":
    seed_database()
