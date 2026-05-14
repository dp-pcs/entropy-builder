import json
import boto3
from botocore.exceptions import ClientError
from .config import settings

_s3 = None


def _client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3", region_name=settings.aws_region)
    return _s3


def write_job_state(job_id: str, state: dict) -> None:
    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=f"jobs/{job_id}/state.json",
        Body=json.dumps(state),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )


def read_job_state(job_id: str) -> dict | None:
    try:
        obj = _client().get_object(
            Bucket=settings.s3_bucket, Key=f"jobs/{job_id}/state.json"
        )
        return json.loads(obj["Body"].read())
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise


def write_job_config(job_id: str, config: dict) -> None:
    """Write full job config (including credentials) to S3. Never written to state.json."""
    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=f"jobs/{job_id}/config.json",
        Body=json.dumps(config),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )


def read_job_config(job_id: str) -> dict | None:
    try:
        obj = _client().get_object(
            Bucket=settings.s3_bucket, Key=f"jobs/{job_id}/config.json"
        )
        return json.loads(obj["Body"].read())
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise


def presign_upload(s3_key: str, content_type: str, expires: int = 3600) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": s3_key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def presign_download(s3_key: str, expires: int = 604800) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": s3_key},
        ExpiresIn=expires,
    )


def upload_vault(job_id: str, zip_bytes: bytes) -> str:
    key = f"jobs/{job_id}/entropy-vault.zip"
    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=zip_bytes,
        ContentType="application/zip",
        ServerSideEncryption="AES256",
    )
    return key


def delete_job(job_id: str) -> None:
    prefix = f"jobs/{job_id}/"
    paginator = _client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=settings.s3_bucket, Prefix=prefix):
        objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
        if objects:
            _client().delete_objects(Bucket=settings.s3_bucket, Delete={"Objects": objects})


def upload_wiki_debug_artifacts(job_id: str, local_dir: str) -> list[str]:
    """Upload per-chunk wiki debug artifacts under jobs/{job_id}/wiki_debug/.

    Used by scripts/replay_wiki_parse.py to diagnose silent content loss.
    Returns the S3 keys uploaded.
    """
    from pathlib import Path
    keys: list[str] = []
    for path in sorted(Path(local_dir).glob("chunk_*.json")):
        key = f"jobs/{job_id}/wiki_debug/{path.name}"
        _client().put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=path.read_bytes(),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        keys.append(key)
    return keys


def upload_claude_settings(job_id: str, settings_json: str) -> str:
    key = f"jobs/{job_id}/claude_desktop_config.json"
    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=settings_json.encode(),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    return key
