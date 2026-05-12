from typing import Any

_store: dict[str, dict] = {}

def get_session(session_id: str) -> dict:
    return _store.setdefault(session_id, {})

def set_session_value(session_id: str, key: str, value: Any) -> None:
    _store.setdefault(session_id, {})[key] = value

def get_session_value(session_id: str, key: str):
    return _store.get(session_id, {}).get(key)

def get_token(session_id: str, provider: str) -> dict | None:
    return _store.get(session_id, {}).get(f"{provider}_tokens")
