def test_get_account_managers(client, mocker):
    mock_post = mocker.patch("webapp.main.requests.post")
    mock_post.return_value.raise_for_status = lambda: None
    mock_post.return_value.json.return_value = {
        "results": [
            {"properties": {"Account Manager": {"rich_text": [{"plain_text": "Jay Khalife"}]}}},
            {"properties": {"Account Manager": {"rich_text": [{"plain_text": "Sebastian Suarez"}]}}},
            {"properties": {"Account Manager": {"rich_text": [{"plain_text": "Jay Khalife"}]}}},
        ],
        "has_more": False,
    }
    mocker.patch("webapp.main.settings.notion_database_id", "db-id")
    mocker.patch("webapp.main.settings.notion_token", "shared-n-tok")

    resp = client.get("/api/notion/account-managers")
    assert resp.status_code == 200
    data = resp.json()
    assert sorted(data["managers"]) == ["Jay Khalife", "Sebastian Suarez"]

    # Verify the shared token was used in the Authorization header
    call_headers = mock_post.call_args[1]["headers"]
    assert call_headers["Authorization"] == "Bearer shared-n-tok"


def test_get_account_managers_no_token(client, mocker):
    mocker.patch("webapp.main.settings.notion_token", "")
    resp = client.get("/api/notion/account-managers")
    assert resp.status_code == 503


def test_get_account_managers_notion_api_error(client, mocker):
    import requests as req_lib
    mocker.patch("webapp.main.settings.notion_token", "shared-tok")
    mock_post = mocker.patch("webapp.main.requests.post")
    err_resp = mocker.MagicMock()
    err_resp.status_code = 401
    mock_post.return_value.raise_for_status.side_effect = req_lib.HTTPError(
        response=err_resp
    )
    mocker.patch("webapp.main.settings.notion_database_id", "db-id")
    resp = client.get("/api/notion/account-managers")
    assert resp.status_code == 401
