# webapp/db.py
import time
import boto3
from .config import settings


def _table():
    ddb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return ddb.Table(settings.dynamodb_table)


def get_user(google_sub: str) -> dict | None:
    resp = _table().get_item(Key={"google_sub": google_sub})
    return resp.get("Item")


def upsert_user(google_sub: str, email: str, name: str) -> None:
    _table().update_item(
        Key={"google_sub": google_sub},
        UpdateExpression="SET email = :e, #n = :n, updated_at = :u",
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":e": email,
            ":n": name,
            ":u": int(time.time()),
        },
    )


def remove_job(google_sub: str, job_id: str) -> None:
    user = get_user(google_sub)
    if not user:
        return
    remaining = [j for j in user.get("jobs", []) if j.get("job_id") != job_id]
    if user.get("latest_job_id") == job_id:
        if remaining:
            newest = sorted(remaining, key=lambda j: j.get("created_at", 0), reverse=True)[0]
            _table().update_item(
                Key={"google_sub": google_sub},
                UpdateExpression="SET jobs = :jobs, latest_job_id = :new_latest",
                ExpressionAttributeValues={":jobs": remaining, ":new_latest": newest["job_id"]},
            )
        else:
            _table().update_item(
                Key={"google_sub": google_sub},
                UpdateExpression="SET jobs = :jobs REMOVE latest_job_id",
                ExpressionAttributeValues={":jobs": remaining},
            )
    else:
        _table().update_item(
            Key={"google_sub": google_sub},
            UpdateExpression="SET jobs = :jobs",
            ExpressionAttributeValues={":jobs": remaining},
        )


def record_job(google_sub: str, job_id: str) -> None:
    _table().update_item(
        Key={"google_sub": google_sub},
        UpdateExpression=(
            "SET latest_job_id = :jid, "
            "jobs = list_append(if_not_exists(jobs, :empty), :entry)"
        ),
        ExpressionAttributeValues={
            ":jid": job_id,
            ":entry": [{"job_id": job_id, "created_at": int(time.time())}],
            ":empty": [],
        },
    )
