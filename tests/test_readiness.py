"""Readiness through HTTP and its owned external database-probe seam."""

from fastapi.testclient import TestClient
import pytest


@pytest.mark.parametrize("ready,status,payload", [
    (True, 200, {"status": "ready"}),
    (False, 503, {"status": "unavailable"}),
])
def test_readiness_is_bounded_database_state_not_process_health(ready, status, payload):
    from vaeil.web import create_app
    from vaeil.adapters.readiness import check_database_ready

    async def probe():
        return ready

    app = create_app()
    app.dependency_overrides[check_database_ready] = probe
    with TestClient(app) as client:
        response = client.get("/api/ready")
        assert response.status_code == status
        assert response.json() == payload
        assert response.headers["cache-control"] == "no-store"
        assert client.get("/api/health").json() == {"status": "ok"}
        assert client.get("/api/demo/member").status_code == 200
