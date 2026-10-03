import json
import random
from datetime import datetime, timedelta, timezone


def generate_logs():
    base_time = datetime.now(timezone.utc) - timedelta(days=30)

    # 50 logs for Alice - ONLY GetObject and PutObject
    alice_logs = []
    for i in range(50):
        action = "s3:GetObject" if i % 2 == 0 else "s3:PutObject"
        resource = f"arn:aws:s3:::production-data/report_{i % 10}.csv"
        alice_logs.append({
            "user_id": "usr-alice",
            "service": "S3",
            "action": action,
            "resource": resource,
            "status": "SUCCESS",
            "source_ip": "192.168.1.10",
            "region": "us-east-1",
            "timestamp": (base_time + timedelta(hours=i * 12)).isoformat()
        })

    # 450 logs for remaining users
    actions_map = {
        "usr-bob": ("EC2", ["ec2:DescribeInstances", "ec2:StartInstances", "ec2:StopInstances"], "arn:aws:ec2:us-east-1:123456789012:instance/i-01234567"),
        "usr-charlie": ("Lambda", ["lambda:InvokeFunction"], "arn:aws:lambda:us-east-1:123456789012:function:api-handler"),
        "usr-david": ("RDS", ["rds:DescribeDBInstances"], "arn:aws:rds:us-east-1:123456789012:db:prod-db"),
        "usr-eve": ("S3", ["s3:GetObject"], "arn:aws:s3:::frontend-assets/main.js"),
        "usr-frank": ("IAM", ["iam:GetUser"], "arn:aws:iam::123456789012:user/frank"),
        "usr-grace": ("EC2", ["ec2:StartInstances", "ec2:StopInstances"], "arn:aws:ec2:us-east-1:123456789012:instance/i-09876543"),
        "usr-heidi": ("S3", ["s3:GetObject", "s3:PutObject"], "arn:aws:s3:::qa-test-data/test1.json"),
        "usr-ivan": ("RDS", ["rds:DescribeDBInstances"], "arn:aws:rds:us-east-1:123456789012:db:analytics-db"),
        "usr-judy": ("S3", ["s3:GetObject"], "arn:aws:s3:::audit-logs-2026/trail.json"),
        "usr-mallory": ("Lambda", ["lambda:InvokeFunction"], "arn:aws:lambda:us-east-1:123456789012:function:worker"),
        "usr-oscar": ("EC2", ["ec2:DescribeInstances", "ec2:RunInstances"], "arn:aws:ec2:us-east-1:123456789012:instance/i-999999"),
        "usr-peggy": ("S3", ["s3:GetObject", "s3:PutObject"], "arn:aws:s3:::product-analytics/daily.parquet"),
        "usr-sybil": ("IAM", ["iam:GetUser"], "arn:aws:iam::123456789012:user/sybil"),
        "usr-trent": ("EC2", ["ec2:DescribeInstances"], "arn:aws:ec2:us-east-1:123456789012:instance/*"),
        "usr-victor": ("S3", ["s3:GetObject", "s3:ListBucket"], "arn:aws:s3:::logs-bucket/*"),
        "usr-walter": ("S3", ["s3:GetObject", "s3:PutObject"], "arn:aws:s3:::ml-training-data/model.pt"),
        "usr-xavier": ("Lambda", ["lambda:CreateFunction", "lambda:InvokeFunction"], "arn:aws:lambda:us-east-1:123456789012:function:deployer"),
        "usr-yvonne": ("S3", ["s3:GetObject", "s3:PutObject"], "arn:aws:s3:::user-uploads/image.png"),
        "usr-zack": ("IAM", ["iam:GetUser", "iam:ListUsers"], "arn:aws:iam::123456789012:root")
    }

    random.seed(42)
    other_logs = []
    for i in range(450):
        u = random.choice(list(actions_map.keys()))
        svc, acts, res = actions_map[u]
        act = random.choice(acts)
        ts = (base_time + timedelta(minutes=i * 90)).isoformat()
        other_logs.append({
            "user_id": u,
            "service": svc,
            "action": act,
            "resource": res,
            "status": "SUCCESS",
            "source_ip": f"10.0.{i % 255}.{i % 200}",
            "region": "us-east-1",
            "timestamp": ts
        })

    all_logs = alice_logs + other_logs
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(base_dir, "data", "access_logs.json")
    with open(target_path, "w") as f:
        json.dump(all_logs, f, indent=2)
    print(f"Successfully generated {len(all_logs)} access log events in {target_path}")


if __name__ == "__main__":
    generate_logs()

