"""Public smoke CLI survives a transient reset while the container starts."""
import importlib.util
from pathlib import Path
import sys


def test_smoke_retries_startup_connection_reset(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "smoke_deployment", Path(__file__).parents[1] / "scripts/smoke_deployment.py"
    )
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    responses = iter([
        ConnectionResetError("container starting"),
        (200, '{"status":"ok"}'),
        (200, '<div id="root"><script src="/assets/app.js"></script>'),
        (200, "script"),
        (200, '{"pseudonym":"Comet","values_profile":{}}'),
        (503, '{"status":"unavailable"}'),
        (200, '{"status":"ok"}'),
    ])
    urls = []

    def read(url):
        urls.append(url)
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(smoke, "read", read)
    monkeypatch.setattr(smoke.time, "sleep", lambda _: None)
    monkeypatch.setattr(sys, "argv", ["smoke_deployment.py", "http://127.0.0.1:8766", "--expect-database-unavailable"])
    smoke.main()
    assert urls[:2] == ["http://127.0.0.1:8766/api/health"] * 2
    assert len(urls) == 7
