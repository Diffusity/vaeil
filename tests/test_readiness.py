"""Readiness through HTTP and its owned external database-probe seam."""

from fastapi.testclient import TestClient
import pytest
import subprocess
import asyncio
import inspect
import runpy
import sys
import time
from contextlib import contextmanager
import threading
import json


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


@pytest.mark.parametrize("row,expected", [((1,), 0), ((0,), 1), (None, 1)])
def test_worker_cli_only_probes_read_only_verified_tls_and_closes_resources(row, expected, monkeypatch):
    import psycopg

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:WorkerPrivateCanary@db.invalid/demo?sslmode=disable")
    observed = []

    class Cursor:
        def execute(self, sql):
            observed.append(sql)

        def fetchone(self):
            return row

    class Connection:
        @contextmanager
        def cursor(self):
            try:
                yield Cursor()
            finally:
                observed.append("cursor closed")

    @contextmanager
    def connect(dsn, **options):
        assert options["sslmode"] == "verify-full"
        assert options["sslrootcert"]
        assert options["connect_timeout"] <= 2
        assert "statement_timeout=2000" in options["options"]
        assert "default_transaction_read_only=on" in options["options"]
        try:
            yield Connection()
        finally:
            observed.append("connection closed")

    monkeypatch.setattr(psycopg, "connect", connect)
    with pytest.raises(SystemExit) as exit_result:
        runpy.run_module("vaeil.adapters.database_probe", run_name="__main__")
    assert exit_result.value.code == expected
    assert observed == ["SELECT 1", "cursor closed", "connection closed"]


def test_worker_exception_text_is_never_printed(monkeypatch, capsys):
    import psycopg

    monkeypatch.setenv("DATABASE_URL", "WorkerPrivateCanary")

    def unavailable(*args, **kwargs):
        raise RuntimeError("WorkerPrivateCanary")

    monkeypatch.setattr(psycopg, "connect", unavailable)
    with pytest.raises(SystemExit) as result:
        runpy.run_module("vaeil.adapters.database_probe", run_name="__main__")
    assert result.value.code == 1
    output = capsys.readouterr()
    assert "WorkerPrivateCanary" not in output.out + output.err


def test_real_worker_timeout_kills_and_reaps_a_stalled_child(monkeypatch, tmp_path):
    from vaeil.adapters import readiness

    monkeypatch.setenv("DATABASE_URL", "postgresql://TimeoutChildCanary@db.invalid/demo")
    real_run = subprocess.run
    children = []
    real_popen = subprocess.Popen
    pid_file = tmp_path / "actual-worker-pid"

    def track_child(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    def stalled_worker(command, **kwargs):
        code = "import os,time;from pathlib import Path;Path(" + repr(str(pid_file)) + ").write_text(str(os.getpid()));time.sleep(30)"
        return real_run([command[0], "-c", code], **kwargs)

    monkeypatch.setattr(subprocess, "Popen", track_child)
    monkeypatch.setattr(subprocess, "run", stalled_worker)
    started = time.monotonic()
    assert probe_result(readiness.check_database_ready) is False
    assert time.monotonic() - started < 6  # OS launch/kill overhead, not a3-second performance claim
    assert len(children) == 1
    assert int(pid_file.read_text()) == children[0].pid  # actual interpreter, not a venv redirector
    assert children[0].poll() is not None


def test_packaged_app_uses_explicit_frontend_directory(monkeypatch, tmp_path):
    import os

    monkeypatch.setenv("VAEIL_FRONTEND_DIR", str(tmp_path))
    result = subprocess.run(
        [sys.executable, "-c", "import json;from vaeil.web import FRONTEND_DIST;print(json.dumps(str(FRONTEND_DIST)))"],
        env=dict(os.environ), capture_output=True, text=True, timeout=10, check=True,
    )
    assert json.loads(result.stdout) == str(tmp_path)


def test_probe_cache_expires_without_being_extended_by_cache_hits(monkeypatch):
    from vaeil.adapters import readiness

    monkeypatch.setenv("DATABASE_URL", "postgresql://CacheExpiryCanary@db.invalid/demo")
    now = [100.0]
    calls = []
    monkeypatch.setattr(time, "monotonic", lambda: now[0])

    def worker(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0 if len(calls) == 1 else 1)

    monkeypatch.setattr(subprocess, "run", worker)
    assert probe_result(readiness.check_database_ready) is True
    now[0] = 129
    assert probe_result(readiness.check_database_ready) is True
    now[0] = 131
    assert probe_result(readiness.check_database_ready) is False
    assert len(calls) == 2


def test_concurrent_probe_does_not_queue_more_database_workers(monkeypatch):
    from vaeil.adapters import readiness

    monkeypatch.setenv("DATABASE_URL", "postgresql://ConcurrentCanary@db.invalid/demo")
    started, release = threading.Event(), threading.Event()
    calls, results = [], []

    def worker(command, **kwargs):
        calls.append(command)
        started.set()
        assert release.wait(2)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", worker)
    thread = threading.Thread(target=lambda: results.append(probe_result(readiness.check_database_ready)))
    thread.start()
    try:
        assert started.wait(1)
        assert probe_result(readiness.check_database_ready) is False
    finally:
        release.set()
        thread.join(3)
    assert not thread.is_alive()
    assert len(calls) == 1 and results == [True]
