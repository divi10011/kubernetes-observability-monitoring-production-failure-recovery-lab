import pytest
from fastapi.testclient import TestClient
from paytrack.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        app.state.payments = []
        app.state.force_not_ready = False
        yield test_client

