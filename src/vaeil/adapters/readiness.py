"""Isolate blocking libpq/DNS work under a process deadline, outside the domain."""

import hashlib
import os
import subprocess
import sys
import sysconfig
import threading
import time

PROBE_TIMEOUT_SECONDS = 3
PROBE_CACHE_SECONDS = 30
_lock = threading.Lock()
_cached_key = None
_cached_until = 0.0
_cached_result = False


def _worker_command() -> list[str]:
    if sys.platform == "win32":
        # A venv exe redirects to another process. Launch the actual interpreter
        # directly and load this venv's packages, so timeout reaps the real worker.
        return [getattr(sys, "_base_executable", sys.executable), "-I", "-S", "-c",
                "import runpy,site,sys;site.addsitedir(sys.argv[1]);"
                "runpy.run_module('vaeil.adapters.database_probe',run_name='__main__')",
                sysconfig.get_path("purelib")]
    return [sys.executable, "-m", "vaeil.adapters.database_probe"]


def check_database_ready() -> bool:
    """One worker maximum; repeated/busy requests never queue more DB traffic."""
    global _cached_key, _cached_until, _cached_result
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        return False
    key = hashlib.sha256(dsn.encode()).digest()
    if not _lock.acquire(blocking=False):
        return False
    try:
        if key == _cached_key and time.monotonic() < _cached_until:
            return _cached_result
        environment = {name: value for name, value in os.environ.items()
                       if name.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
        environment["DATABASE_URL"] = dsn
        try:
            result = subprocess.run(
                _worker_command(),
                env=environment, timeout=PROBE_TIMEOUT_SECONDS,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            available = result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            available = False
        _cached_key, _cached_result = key, available
        _cached_until = time.monotonic() + PROBE_CACHE_SECONDS
        return available
    finally:
        _lock.release()
