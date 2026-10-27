"""Dedicated Windows Ollama timings on fixed, unscored synthetic prompts.

No accuracy labels are read. Run only in an authorized, power-verified block.
Uses the standard library; owns and cleans up its loopback server/process tree.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import ctypes
from datetime import datetime, timezone
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
import winreg

MODELS = ("qwen2.5:1.5b", "llama3.2:1b", "qwen3:1.7b")
BEST_PERFORMANCE = "ded574b5-45a0-4f42-8737-46345c09c238"
SCHEMA = {"type": "object", "properties": {"verdict": {
    "type": "string", "enum": ["Approved", "NeedsReview"]}},
    "required": ["verdict"], "additionalProperties": False}
TEXTS = (
    ("moderation", "I enjoy reading and music. Would you like to talk about your favourite books?"),
    ("provisional_application_latency_only", "I value honesty and kindness, enjoy cooking and volunteering, and respect other people's boundaries."),
    ("moderation", "Aaj padhai ke baad thoda rest chahiye. Kal yahin baat karein?"),
    ("provisional_application_latency_only", "Mujhe kindness aur respect important lagte hain. Main saamne wale ki boundaries respect karunga."),
    ("moderation", "Aaje thodu busy chhu. Aapde kale shanti thi vaat kariye?"),
    ("provisional_application_latency_only", "Mane reading ane cooking game chhe. Hu bijana mat ane boundaries no aadar karu chhu."),
    ("moderation", "આજે હું થોડો વ્યસ્ત છું. આપણે કાલે અહીં વાત કરીએ?"),
    ("provisional_application_latency_only", "મને સંગીત અને વાંચવું ગમે છે. સંબંધમાં સન્માન અને પ્રામાણિકતા જરૂરી છે."),
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def percentile(values):
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1] if ordered else None


def valid_verdict(content):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON property.")
            result[key] = value
        return result

    try:
        value = json.loads(content, object_pairs_hook=unique_object)
    except (ValueError, TypeError):
        return False
    return (type(value) is dict and set(value) == {"verdict"}
            and value["verdict"] in ("Approved", "NeedsReview"))


def power_status():
    class Power(ctypes.Structure):
        _fields_ = [("ac", ctypes.c_ubyte), ("flag", ctypes.c_ubyte),
                    ("percent", ctypes.c_ubyte), ("reserved", ctypes.c_ubyte),
                    ("life", ctypes.c_uint32), ("full", ctypes.c_uint32)]
    status = Power()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        raise RuntimeError("Cannot verify AC power.")
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes") as key:
        overlay = winreg.QueryValueEx(key, "ActiveOverlayAcPowerScheme")[0]
    result = {"utc": utc(), "ac": status.ac, "battery_percent": status.percent,
              "ac_overlay": overlay, "base_plan": subprocess.check_output(
                  ["powercfg", "/getactivescheme"], text=True).strip()}
    if status.ac != 1 or overlay.lower() != BEST_PERFORMANCE:
        raise RuntimeError("AC power and Best Performance overlay are required.")
    sleep = subprocess.check_output(
        ["powercfg", "/query", "SCHEME_CURRENT", "SUB_SLEEP", "STANDBYIDLE"], text=True)
    result["sleep_query"] = sleep
    # This laptop's English Windows output; never assume an unparsed result passed.
    ac_lines = [line for line in sleep.splitlines() if "Current AC Power Setting Index" in line]
    if len(ac_lines) != 1 or int(ac_lines[0].split(":")[-1].strip(), 16) != 0:
        raise RuntimeError("Cannot verify disabled AC sleep.")
    return result


@contextmanager
def response_stream(path, body, *, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Request deadline reached before connection.")
    connection = http.client.HTTPConnection("127.0.0.1", 11434, timeout=remaining)
    expired = threading.Event()
    timer = None
    try:
        connection.connect()
        sock = connection.sock  # Retain it even if HTTP/1.0 transfers ownership.
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Request deadline reached during connection.")

        def expire():
            expired.set()
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()

        timer = threading.Timer(remaining, expire)
        timer.daemon = True
        timer.start()
        data = None if body is None else json.dumps(body).encode()
        connection.request("GET" if body is None else "POST", path, body=data,
                           headers={"Content-Type": "application/json"})
        with connection.getresponse() as response:
            if response.status != 200:
                raise RuntimeError(f"Local runtime returned HTTP {response.status}.")
            yield response
        if expired.is_set():
            raise TimeoutError("Absolute request deadline reached.")
    except Exception:
        if expired.is_set():
            raise TimeoutError("Absolute request deadline reached.") from None
        raise
    finally:
        if timer is not None:
            timer.cancel()
        connection.close()
        if timer is not None:
            timer.join(timeout=1)


def api(path, body=None, timeout=30, *, deadline=None):
    request_deadline = time.monotonic() + timeout
    if deadline is not None:
        request_deadline = min(request_deadline, deadline)
    with response_stream(path, body, deadline=request_deadline) as response:
        return json.load(response)


def call(model, index, backend, prompt, *, deadline):
    task, text = TEXTS[index % len(TEXTS)]
    payload = {"model": model, "stream": True, "format": SCHEMA,
               "messages": [{"role": "system", "content": prompt},
                            {"role": "user", "content": json.dumps({
                                "task": task, "text": text,
                                "synthetic_request_number": index}, ensure_ascii=False)}],
               "keep_alive": "15m", "options": {"temperature": 0, "seed": 42,
                   "num_ctx": 2048, "num_predict": 32, "num_thread": 6,
                   "num_gpu": 0 if backend == "cpu" else -1}}
    if model.startswith("qwen3:"):
        payload["think"] = False
    started = time.perf_counter()
    call_deadline = min(deadline, time.monotonic() + 30)
    sample = {"model": model, "backend": backend, "index": index, "task": task,
              "started_utc": utc(), "ok": False, "ttft_s": None,
              "content": "", "thinking_chars": 0}
    try:
        remaining = deadline - time.monotonic()
        if remaining < 2:
            raise TimeoutError("Block deadline reached.")
        final = None
        with response_stream("/api/chat", payload, deadline=call_deadline) as response:
            for raw in response:
                if time.monotonic() >= call_deadline:
                    raise TimeoutError("Experimental 30-second call deadline reached.")
                chunk = json.loads(raw)
                if "error" in chunk:
                    raise RuntimeError(chunk["error"])
                message = chunk.get("message", {})
                content = message.get("content", "")
                if content and sample["ttft_s"] is None:
                    sample["ttft_s"] = time.perf_counter() - started
                sample["content"] += content
                sample["thinking_chars"] += len(message.get("thinking", ""))
                if chunk.get("done"):
                    final = chunk
                    break
        if final is None:
            raise RuntimeError("Stream ended without completion metadata.")
        sample["metrics"] = {key: final.get(key) for key in (
            "total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration",
            "eval_count", "eval_duration", "done_reason")}
        duration = final.get("eval_duration", 0)
        sample["tokens_per_second"] = final.get("eval_count", 0) / (duration / 1e9) if duration else None
        sample["ok"] = valid_verdict(sample["content"]) and sample["thinking_chars"] == 0
        if not sample["ok"]:
            sample["error"] = "Malformed verdict or unexpected thinking."
    except Exception as error:
        sample["error"] = type(error).__name__ + ": " + str(error)
    sample["total_s"] = time.perf_counter() - started
    sample["finished_utc"] = utc()
    return sample


def summary(samples):
    good = [sample for sample in samples if sample["ok"]]
    return {"n": len(samples), "failures": len(samples) - len(good),
            "failure_rate": (len(samples) - len(good)) / len(samples) if samples else None,
            "successful_total_p95_s": percentile([s["total_s"] for s in good]),
            "all_attempt_total_p95_s": percentile([s["total_s"] for s in samples]),
            "ttft_p95_s": percentile([s["ttft_s"] for s in good if s["ttft_s"] is not None]),
            "mean_generation_tokens_per_second": (sum(s.get("tokens_per_second") or 0 for s in good) / len(good)) if good else None}


def stop_tree(process):
    # Root is the PID of the server this script created, never a name-based kill.
    try:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, timeout=15)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)


def assert_port_available():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(("127.0.0.1", 11434))
    except OSError:
        raise RuntimeError("Loopback runtime port is occupied or unavailable.") from None


def listener_owners(*, deadline=None):
    command = ("$taskOwners=@(Get-NetTCPConnection -LocalPort 11434 -State Listen "
               "-ErrorAction SilentlyContinue | Where-Object { $_.LocalAddress -eq '127.0.0.1' } "
               "| Select-Object -ExpandProperty OwningProcess); "
               "ConvertTo-Json -InputObject $taskOwners -Compress")
    remaining = 10 if deadline is None else min(10, deadline - time.monotonic())
    if remaining <= 0:
        raise TimeoutError("Block deadline reached before listener verification.")
    value = json.loads(subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", command], text=True, timeout=remaining))
    return {value} if isinstance(value, int) else set(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("cpu", "vulkan"), required=True)
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    remaining = datetime.fromisoformat(args.deadline_utc.replace("Z", "+00:00")).timestamp() - time.time()
    deadline = time.monotonic() + remaining
    if remaining < 60:
        raise RuntimeError("Insufficient time before block deadline.")
    args.output.mkdir(parents=True, exist_ok=True)
    prompt_path = Path(__file__).resolve().parents[1] / "docs/research/local-model-prompt-v1.txt"
    prompt_bytes = prompt_path.read_bytes()
    report = {"started_utc": utc(), "backend": args.backend, "accuracy_run": False,
              "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
              "prompt_revision": "v1", "fixed_runtime_texts": TEXTS,
              "power": power_status(), "experimental_settings": {
                  "parallel_slots": 2, "max_loaded_models": 1, "queue": 4,
                  "context": 2048, "max_output": 32, "threads": 6,
                  "temperature": 0, "seed": 42, "qwen3_think": False,
                  "experimental_call_deadline_s": 30}, "models": []}
    report_path = args.output / "summary.json"

    def save():
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    env = os.environ.copy()
    env.update(OLLAMA_HOST="127.0.0.1:11434", OLLAMA_NUM_PARALLEL="2",
               OLLAMA_MAX_LOADED_MODELS="1", OLLAMA_MAX_QUEUE="4",
               OLLAMA_NOPRUNE="1",
               OLLAMA_VULKAN="0" if args.backend == "cpu" else "1",
               OLLAMA_IGPU_ENABLE="0" if args.backend == "cpu" else "1",
               GGML_VK_VISIBLE_DEVICES="-1" if args.backend == "cpu" else "0")
    executable = Path(os.environ["LOCALAPPDATA"]) / "Programs/Ollama/ollama.exe"
    assert_port_available()
    if time.monotonic() >= deadline:
        raise TimeoutError("Block deadline reached before server startup.")
    with (args.output / "server.log").open("w", encoding="utf-8") as server_log:
        server = subprocess.Popen([str(executable), "serve"], env=env,
                                  stdout=server_log, stderr=server_log,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            for _ in range(60):
                if time.monotonic() >= deadline:
                    raise TimeoutError("Block deadline reached during readiness.")
                if server.poll() is not None:
                    raise RuntimeError("Owned server exited before readiness.")
                try:
                    report["runtime"] = api("/api/version", timeout=1, deadline=deadline)
                except Exception:
                    time.sleep(0.5)
                    continue
                if server.poll() is not None or listener_owners(deadline=deadline) != {server.pid}:
                    raise RuntimeError("Listener is not owned by the created server.")
                report["listener_owner_pid"] = server.pid
                break
            else:
                raise RuntimeError("Owned server did not become ready.")
            report["tags"] = api("/api/tags", deadline=deadline)
            available = {item["name"] for item in report["tags"]["models"]}
            for model in MODELS:
                if model not in available:
                    report["models"].append({"model": model, "skipped": "Authorized model not pulled."})
                    save()
                    continue
                power_status()
                item = {"model": model, "show": api("/api/show", {"model": model}, deadline=deadline)}
                report["models"].append(item)
                if deadline - time.monotonic() < 70:
                    item["incomplete"] = "Block deadline."
                    break
                api("/api/chat", {"model": model, "messages": [], "keep_alive": 0}, deadline=deadline)
                cold = call(model, 0, args.backend, prompt_bytes.decode("utf-8-sig"), deadline=deadline)
                item["cold"] = cold
                item["loaded_placement"] = api("/api/ps", deadline=deadline)
                loaded = item["loaded_placement"].get("models", [])
                if args.backend == "cpu" and any(entry.get("size_vram", 0) for entry in loaded):
                    raise RuntimeError("CPU placement verification failed.")
                if args.backend == "vulkan" and not any(entry.get("size_vram", 0) for entry in loaded):
                    item["incomplete"] = "Vulkan requested but no GPU offload measured."
                    save()
                    continue
                for concurrency in (1, 2):
                    power_status()
                    samples = []
                    with ThreadPoolExecutor(max_workers=concurrency) as pool:
                        for start in range(0, 32, concurrency):
                            if deadline - time.monotonic() < 35:
                                break
                            futures = [pool.submit(call, model, concurrency * 100 + index,
                                       args.backend, prompt_bytes.decode("utf-8-sig"), deadline=deadline)
                                       for index in range(start, start + concurrency)]
                            samples.extend(future.result() for future in futures)
                    item[f"concurrency_{concurrency}"] = {"summary": summary(samples), "samples": samples}
                    save()
                    print(model, "concurrency", concurrency, summary(samples), flush=True)
                power_status()
                sustained_start = time.monotonic()
                sustained = []
                with (args.output / (model.replace(":", "_") + "-sustained.jsonl")).open("w", encoding="utf-8") as stream:
                    while time.monotonic() - sustained_start < 600 and deadline - time.monotonic() > 35:
                        sample = call(model, 1000 + len(sustained), args.backend,
                                      prompt_bytes.decode("utf-8-sig"), deadline=deadline)
                        sample["sustained_offset_s"] = time.monotonic() - sustained_start
                        sustained.append(sample)
                        stream.write(json.dumps(sample) + "\n")
                        stream.flush()
                elapsed = time.monotonic() - sustained_start
                item["sustained"] = {"duration_s": elapsed, "completed_ten_minutes": elapsed >= 600,
                    "temperature_evidence": "No supported temperature sensor collected; slowdown is not proven thermal throttling.",
                    "summary": summary(sustained),
                    "first_minute": summary([s for s in sustained if s["sustained_offset_s"] <= 60]),
                    "last_minute": summary([s for s in sustained if s["sustained_offset_s"] >= elapsed - 60])}
                save()
                print(model, "sustained", elapsed, summary(sustained), flush=True)
                api("/api/chat", {"model": model, "messages": [], "keep_alive": 0}, deadline=deadline)
        except Exception as error:
            report["error_type"] = type(error).__name__
            report["error"] = type(error).__name__ + ": " + str(error)
            print(report["error"], flush=True)
        finally:
            stop_tree(server)
            report["finished_utc"] = utc()
            report["cleanup_server_returncode"] = server.returncode
            save()


if __name__ == "__main__":
    main()
