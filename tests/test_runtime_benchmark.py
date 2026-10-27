"""Windows benchmark scope guards; no Ollama or model inference required."""

import importlib.util
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import sys
import threading
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


@pytest.fixture
def trickling_endpoint(monkeypatch):
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.respond()

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.respond()

        def respond(self):
            body = (json.dumps({"message": {"content": '{"verdict":"Approved"}'},
                                "done": True, "eval_count": 8,
                                "eval_duration": 100000000}) + "\n").encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                for value in body:
                    self.wfile.write(bytes([value]))
                    self.wfile.flush()
                    time.sleep(0.06)  # Keeps idle reads alive while exceeding total budget.
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                done.set()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    connection = http.client.HTTPConnection
    class RoutedConnection(connection):
        def __init__(self, host, port=None, **kwargs):
            super().__init__("127.0.0.1", server.server_port, **kwargs)

    monkeypatch.setattr(http.client, "HTTPConnection", RoutedConnection)
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
        assert done.wait(timeout=1)
        assert not thread.is_alive()


def test_stream_trickle_cannot_exceed_the_absolute_block_deadline(benchmark, trickling_endpoint):
    sample = benchmark.call("qwen2.5:1.5b", 0, "cpu", "Fixed synthetic instruction.",
                            deadline=time.monotonic() + 2.5)
    assert sample["total_s"] < 4
    assert sample["ok"] is False
    assert sample["error"].startswith("TimeoutError:")


def test_auxiliary_json_call_has_a_total_not_idle_timeout(benchmark, trickling_endpoint):
    started = time.perf_counter()
    with pytest.raises(TimeoutError):
        benchmark.api("/synthetic-test-only", timeout=0.15)
    assert time.perf_counter() - started < 1
