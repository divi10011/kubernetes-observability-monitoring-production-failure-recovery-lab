from paytrack.main import app


def test_root_health_and_ready_endpoints(client):
    assert client.get("/").json()["service"] == "paytrack"
    assert client.get("/health").json() == {"status": "healthy"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_creates_and_lists_simulated_payments(client):
    created = client.post(
        "/payments",
        json={"amount": 42.50, "currency": "usd", "reference": "demo-order-001"},
    )

    assert created.status_code == 201
    assert created.json()["status"] == "accepted"
    assert created.json()["currency"] == "USD"

    listed = client.get("/payments")
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    assert listed.json()["items"][0]["id"] == created.json()["id"]


def test_rejects_invalid_payment_input(client):
    response = client.post("/payments", json={"amount": 0, "currency": "US1"})

    assert response.status_code == 422


def test_readiness_failure_mode_returns_503(client):
    app.state.force_not_ready = True

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "not ready"


def test_metrics_include_application_instrumentation(client):
    client.get("/health")
    client.post("/payments", json={"amount": 1, "currency": "INR"})

    metrics = client.get("/metrics")

    assert metrics.status_code == 200
    assert "paytrack_http_requests_total" in metrics.text
    assert "paytrack_http_errors_total" in metrics.text
    assert "paytrack_http_request_duration_seconds" in metrics.text
    assert "paytrack_payment_transactions_total" in metrics.text
