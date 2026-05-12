import time
import uuid
from typing import Optional

from .config import settings

_TOKEN_TTL = 30 * 86400  # 30 days
_TOKEN_PREFIX = "auth_"


def _table():
    import boto3
    ddb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return ddb.Table(settings.sessions_table)


def create_auth_token(google_sub: str, email: str, name: str) -> str:
    token = _TOKEN_PREFIX + uuid.uuid4().hex
    _table().put_item(Item={
        "session_id": token,
        "item_type": "auth_token",
        "google_sub": google_sub,
        "email": email,
        "name": name,
        "ttl": int(time.time()) + _TOKEN_TTL,
    })
    return token


def get_auth_user(token: str) -> Optional[dict]:
    if not token or not token.startswith(_TOKEN_PREFIX):
        return None
    try:
        resp = _table().get_item(Key={"session_id": token})
        item = resp.get("Item")
        if not item or item.get("item_type") != "auth_token":
            return None
        return {
            "google_sub": item["google_sub"],
            "email": item.get("email", ""),
            "name": item.get("name", ""),
        }
    except Exception:
        return None


def delete_auth_token(token: str) -> None:
    if not token:
        return
    try:
        _table().delete_item(Key={"session_id": token})
    except Exception:
        pass
