def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_list(client):
    r = client.post("/api/v1/targets", json={"url": "test1.example.com"})
    assert r.status_code == 201, r.text
    target = r.json()
    assert target["url"] == "test1.example.com"
    assert target["status"] == "queued"

    r = client.get("/api/v1/targets")
    assert r.status_code == 200
    assert any(t["url"] == "test1.example.com" for t in r.json()["items"])


def test_invalid_domain(client):
    r = client.post("/api/v1/targets", json={"url": "not a domain"})
    assert r.status_code == 422


def test_duplicate_queued_conflict(client):
    client.post("/api/v1/targets", json={"url": "dup.example.com"})
    r = client.post("/api/v1/targets", json={"url": "dup.example.com"})
    assert r.status_code == 409


def test_auth_required_for_writes(unauth_client):
    r = unauth_client.post("/api/v1/targets", json={"url": "auth.example.com"})
    assert r.status_code == 401

    # reads should still work
    r = unauth_client.get("/api/v1/targets")
    assert r.status_code == 200


def test_bulk_create(client):
    r = client.post(
        "/api/v1/targets/bulk",
        json={
            "urls": ["bulk-a.example.com", "bulk-b.example.com", "not a domain"],
            "tags": ["scope:test"],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["created"]) == 2
    assert "not a domain" in body["errors"]


def test_cancel_queued(client):
    r = client.post("/api/v1/targets", json={"url": "cancel.example.com"})
    tid = r.json()["id"]
    r = client.post(f"/api/v1/targets/{tid}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_rescan_creates_new_target(client):
    r = client.post("/api/v1/targets", json={"url": "rescan.example.com", "tags": ["x"]})
    tid = r.json()["id"]
    r = client.post(f"/api/v1/targets/{tid}/rescan")
    assert r.status_code == 201
    new = r.json()
    assert new["id"] != tid
    assert new["url"] == "rescan.example.com"
    assert new["tags"] == ["x"]


def test_stats(client):
    r = client.get("/api/v1/targets/stats")
    assert r.status_code == 200
    body = r.json()
    for k in ("queued", "running", "completed", "failed", "cancelled", "total"):
        assert k in body


def test_export_csv(client):
    r = client.get("/api/v1/targets/export?format=csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert b"id,url,status" in r.content


def test_modules(client):
    r = client.get("/api/v1/modules")
    assert r.status_code == 200
    items = r.json()
    assert any(m["name"] == "subdomains" for m in items)


def test_system_info(client):
    r = client.get("/api/v1/system/info")
    assert r.status_code == 200
    body = r.json()
    assert body["auth_required"] is True
