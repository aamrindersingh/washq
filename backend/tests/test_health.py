def test_health_is_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_checks_the_database(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_metrics_endpoint_is_prometheus_text(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    assert "washq_bookings_created_total" in r.text


def test_api_docs_are_under_api(client):
    # The footer links here, and only /api reaches the backend through
    # nginx and the ingress.
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/openapi.json").status_code == 200
