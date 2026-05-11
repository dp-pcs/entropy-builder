import json
import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError


@pytest.fixture(autouse=True)
def mock_s3_client(mocker):
    mock = MagicMock()
    mocker.patch("webapp.s3._client", return_value=mock)
    mocker.patch("webapp.s3.settings.s3_bucket", "test-bucket")
    return mock


def test_write_job_state(mock_s3_client):
    from webapp.s3 import write_job_state
    write_job_state("job-1", {"status": "pending"})
    mock_s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="jobs/job-1/state.json",
        Body=json.dumps({"status": "pending"}),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )


def test_read_job_state(mock_s3_client):
    from webapp.s3 import read_job_state
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: b'{"status": "pending"}')
    }
    result = read_job_state("job-1")
    assert result == {"status": "pending"}


def test_read_job_state_not_found(mock_s3_client):
    from webapp.s3 import read_job_state
    mock_s3_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
    )
    result = read_job_state("missing-job")
    assert result is None


def test_presign_upload(mock_s3_client):
    from webapp.s3 import presign_upload
    mock_s3_client.generate_presigned_url.return_value = "https://s3.example.com/upload"
    url = presign_upload("uploads/abc/file.pdf", "application/pdf")
    assert url == "https://s3.example.com/upload"
    mock_s3_client.generate_presigned_url.assert_called_once_with(
        "put_object",
        Params={"Bucket": "test-bucket", "Key": "uploads/abc/file.pdf",
                "ContentType": "application/pdf"},
        ExpiresIn=3600,
    )


def test_presign_download(mock_s3_client):
    from webapp.s3 import presign_download
    mock_s3_client.generate_presigned_url.return_value = "https://s3.example.com/dl"
    url = presign_download("jobs/job-1/entropy-vault.zip")
    assert url == "https://s3.example.com/dl"
    mock_s3_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "test-bucket", "Key": "jobs/job-1/entropy-vault.zip"},
        ExpiresIn=604800,
    )


def test_upload_vault(mock_s3_client):
    from webapp.s3 import upload_vault
    key = upload_vault("job-1", b"zipdata")
    assert key == "jobs/job-1/entropy-vault.zip"
    mock_s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="jobs/job-1/entropy-vault.zip",
        Body=b"zipdata",
        ContentType="application/zip",
        ServerSideEncryption="AES256",
    )


def test_upload_claude_settings(mock_s3_client):
    from webapp.s3 import upload_claude_settings
    key = upload_claude_settings("job-1", '{"mcpServers": {}}')
    assert key == "jobs/job-1/claude_settings.json"
    mock_s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="jobs/job-1/claude_settings.json",
        Body=b'{"mcpServers": {}}',
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
