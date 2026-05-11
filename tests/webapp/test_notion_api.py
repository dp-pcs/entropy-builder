def test_get_account_managers(client, mocker):
    from webapp.session import set_session_value
    set_session_value("sess-1", "notion_tokens", {"access_token": "n-tok"})

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

    resp = client.get("/api/notion/account-managers?session_id=sess-1")
    assert resp.status_code == 200
    data = resp.json()
    assert sorted(data["managers"]) == ["Jay Khalife", "Sebastian Suarez"]


def test_get_account_managers_no_token(client):
    resp = client.get("/api/notion/account-managers?session_id=no-such-session")
    assert resp.status_code == 401


def test_get_account_managers_notion_api_error(client, mocker):
    from webapp.session import set_session_value
    import requests as req_lib
    set_session_value("sess-err", "notion_tokens", {"access_token": "tok"})
    mock_post = mocker.patch("webapp.main.requests.post")
    err_resp = mocker.MagicMock()
    err_resp.status_code = 401
    mock_post.return_value.raise_for_status.side_effect = req_lib.HTTPError(
        response=err_resp
    )
    mocker.patch("webapp.main.settings.notion_database_id", "db-id")
    resp = client.get("/api/notion/account-managers?session_id=sess-err")
    assert resp.status_code == 401
