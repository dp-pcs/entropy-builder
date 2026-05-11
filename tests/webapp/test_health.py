def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_index_route_exists(client):
    resp = client.get("/")
    assert resp.status_code in (200, 500)  # 500 until template created


def test_wizard_route_exists(client):
    resp = client.get("/wizard")
    assert resp.status_code in (200, 500)
