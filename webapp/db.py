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
