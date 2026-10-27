"""Windows benchmark scope guards; no Ollama or model inference required."""

import importlib.util
import json
from pathlib import Path
import socket
import sys
import time
from types import SimpleNamespace

import pytest

pytest.importorskip("winreg")


@pytest.fixture
def benchmark():
    path = Path(__file__).resolve().parents[1] / "scripts/benchmark_ollama_runtime.py"
    spec = importlib.util.spec_from_file_location("runtime_benchmark_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_with_fake_endpoint(benchmark, monkeypatch, tmp_path, *, occupied, child_exited):
    """Replace only OS/process/endpoint boundaries, never call a live model."""
    class Port:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def setsockopt(self, *args):
            pass

        def bind(self, address):
            if occupied:
                raise OSError("Address already in use")

    monkeypatch.setattr(benchmark, "socket", SimpleNamespace(
        socket=lambda *args: Port(), AF_INET=socket.AF_INET, SOCK_STREAM=socket.SOCK_STREAM,
        SOL_SOCKET=socket.SOL_SOCKET, SO_EXCLUSIVEADDRUSE=socket.SO_EXCLUSIVEADDRUSE,
    ), raising=False)
    process = SimpleNamespace(pid=987654321, returncode=23 if child_exited else None,
                              poll=lambda: 23 if child_exited else None)
    launches, requests = [], []

    def launch(*args, **kwargs):
        launches.append(True)
        return process

    def endpoint(path, body=None, **kwargs):
        requests.append(path)
        if len(requests) == 1:
            raise TimeoutError("Existing version probe did not respond")
        return {"version": "unowned-test-server"} if path == "/api/version" else {"models": []}

    monkeypatch.setattr(benchmark.subprocess, "Popen", launch)
    monkeypatch.setattr(benchmark.subprocess, "check_output", lambda *a, **k: "999999997")
    monkeypatch.setattr(benchmark, "power_status", lambda: {"ac": 1})
    monkeypatch.setattr(benchmark, "api", endpoint)
    monkeypatch.setattr(benchmark, "stop_tree", lambda process: None)
    deadline = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 600))
    monkeypatch.setattr(sys, "argv", ["benchmark", "--backend", "cpu", "--deadline-utc",
                                     deadline, "--output", str(tmp_path)])
    return launches, requests


def test_occupied_port_is_refused_even_if_version_probe_would_time_out(benchmark, monkeypatch, tmp_path):
    launches, _ = run_with_fake_endpoint(benchmark, monkeypatch, tmp_path,
                                        occupied=True, child_exited=False)
    with pytest.raises(RuntimeError):
        benchmark.main()
    assert launches == []


@pytest.mark.parametrize("child_exited", [True, False], ids=["child-exited", "other-listener-pid"])
def test_readiness_cannot_use_another_server(benchmark, monkeypatch, tmp_path, child_exited):
    _, requests = run_with_fake_endpoint(benchmark, monkeypatch, tmp_path,
                                        occupied=False, child_exited=child_exited)
    benchmark.main()
    report = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert report.get("error_type") == "RuntimeError"
    assert "/api/tags" not in requests
