"""Readiness through HTTP and its owned external database-probe seam."""

from fastapi.testclient import TestClient
import pytest
import subprocess
import asyncio
import inspect


def probe_result(probe):
    result = probe()
    return asyncio.run(result) if inspect.isawaitable(result) else result


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


def test_real_probe_uses_a_deadline_and_caches_repeated_checks(monkeypatch):
    from vaeil.adapters import readiness

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:PrivateSecretOne@db.invalid/demo")
    calls = []

    def worker(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", worker)
    assert probe_result(readiness.check_database_ready) is True
    assert probe_result(readiness.check_database_ready) is True
    assert len(calls) == 1
    command, options = calls[0]
    assert "PrivateSecretOne" not in repr(command)
    assert options["timeout"] <= 3
    assert options["stdout"] == subprocess.DEVNULL
    assert options["stderr"] == subprocess.DEVNULL
    assert options["env"]["DATABASE_URL"].endswith("@db.invalid/demo")


@pytest.mark.parametrize("failure", ["exit", "timeout", "spawn"])
def test_probe_failures_do_not_leak_secrets_into_http_or_logs(failure, monkeypatch, caplog, capsys):
    from vaeil.adapters import readiness
    from vaeil.web import create_app

    secret = "PrivateReadinessCanary" + failure
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:" + secret + "@db.invalid/demo")

    def worker(command, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 3, output=secret, stderr=secret)
        if failure == "spawn":
            raise OSError(secret)
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(subprocess, "run", worker)
    with TestClient(create_app()) as client:
        response = client.get("/api/ready")
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/demo/member").status_code == 200
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    captured = capsys.readouterr()
    assert secret not in response.text + repr(dict(response.headers)) + caplog.text + captured.out + captured.err


def test_missing_database_configuration_never_launches_a_worker(monkeypatch):
    from vaeil.adapters import readiness

    monkeypatch.delenv("DATABASE_URL", raising=False)

    def forbidden(*args, **kwargs):
        pytest.fail("Missing configuration must not create a process or network request")

    monkeypatch.setattr(subprocess, "run", forbidden)
    assert probe_result(readiness.check_database_ready) is False
