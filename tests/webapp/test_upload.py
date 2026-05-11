_VALID_UUID = "00000000-0000-0000-0000-000000000001"


def test_presign_upload_endpoint(client, mocker):
    mock_presign = mocker.patch("webapp.main.s3.presign_upload")
    mock_presign.return_value = "https://s3.example.com/put-url"

    resp = client.post("/api/upload/presign", json={
        "session_id": _VALID_UUID,
        "filename": "vault.zip",
        "content_type": "application/zip",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["upload_url"] == "https://s3.example.com/put-url"
    assert data["s3_key"].startswith(f"uploads/{_VALID_UUID}/")
    assert data["s3_key"].endswith("vault.zip")


def test_presign_upload_sanitizes_filename(client, mocker):
    mock_presign = mocker.patch("webapp.main.s3.presign_upload")
    mock_presign.return_value = "https://s3.example.com/put-url"

    resp = client.post("/api/upload/presign", json={
        "session_id": _VALID_UUID,
        "filename": "../../etc/passwd",
        "content_type": "text/plain",
    })
    assert resp.status_code == 200
    data = resp.json()
    # No path traversal in the key segment after the session prefix
    suffix = data["s3_key"].split(f"uploads/{_VALID_UUID}/")[1]
    assert ".." not in suffix
    assert "/" not in suffix


def test_presign_upload_invalid_session_id(client, mocker):
    mocker.patch("webapp.main.s3.presign_upload")
    resp = client.post("/api/upload/presign", json={
        "session_id": "not-a-uuid",
        "filename": "file.pdf",
        "content_type": "application/pdf",
    })
    assert resp.status_code == 400
