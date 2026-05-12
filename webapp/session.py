import json
import time
from typing import Any

from .config import settings

_TTL_SECONDS = 86400  # 24h

_fallback: dict[str, dict] = {}


def _table():
    import boto3
    ddb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return ddb.Table(settings.sessions_table)


def get_session(session_id: str) -> dict:
    if not settings.sessions_table:
        return _fallback.setdefault(session_id, {})
    try:
        resp = _table().get_item(Key={"session_id": session_id})
        item = resp.get("Item")
        if not item:
            return {}
        raw = item.get("session_data", "{}")
        return json.loads(raw) if isinstance(raw, str) else {}
    except Exception:
        return _fallback.get(session_id, {})


def set_session_value(session_id: str, key: str, value: Any) -> None:
    if not settings.sessions_table:
        _fallback.setdefault(session_id, {})[key] = value
        return
    try:
        session = get_session(session_id)
        session[key] = value
        _table().put_item(Item={
            "session_id": session_id,
            "session_data": json.dumps(session),
            "ttl": int(time.time()) + _TTL_SECONDS,
        })
    except Exception:
        _fallback.setdefault(session_id, {})[key] = value


def get_session_value(session_id: str, key: str) -> Any:
    return get_session(session_id).get(key)


def get_token(session_id: str, provider: str) -> dict | None:
    return get_session_value(session_id, f"{provider}_tokens")
