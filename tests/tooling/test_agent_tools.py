"""Exercise agent tooling through its command-line interfaces."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def run_tool(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name), *args],
        capture_output=True, encoding="utf-8", timeout=10,
    )


def assumptions_file(tmp_path: Path, rows: list[str]) -> str:
    path = tmp_path / "assumptions.md"
    path.write_text(
        "| ID | Date | Assumption | Why it was made | What would invalidate it | Status | Supersedes |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(rows),
        encoding="utf-8",
    )
    return str(path)


def row(identifier: str, status: str = "active", supersedes: str = "-") -> str:
    return f"| {identifier} | 2026-10-23 | Choice | Reason | Change | {status} | {supersedes} |"


def test_assumption_replacement_chain_is_valid(tmp_path: Path) -> None:
    path = assumptions_file(tmp_path, [row("A001", "superseded"), row("A002", supersedes="A001")])
    assert run_tool("check_assumptions.py", "--path", path).returncode == 0


@pytest.mark.parametrize("rows", [
    [row("A001"), row("A001")],
    [row("A001", supersedes="A999")],
    [row("A001"), row("A002", supersedes="A001")],
    [row("A001", "superseded")],
    [row("A001", "superseded", "A002"), row("A002", "superseded", "A001")],
    [row("A001", "maybe")],
], ids=["duplicate", "missing-target", "active-predecessor", "missing-replacement", "cycle", "bad-status"])
def test_invalid_assumption_relationships_fail(tmp_path: Path, rows: list[str]) -> None:
    result = run_tool("check_assumptions.py", "--path", assumptions_file(tmp_path, rows))
    assert result.returncode == 1
    assert "error:" in result.stderr.lower()


def test_invalidated_assumption_needs_no_replacement(tmp_path: Path) -> None:
    path = assumptions_file(tmp_path, [row("A001", "invalidated")])
    assert run_tool("check_assumptions.py", "--path", path).returncode == 0


def session_file(tmp_path: Path) -> str:
    path = tmp_path / "session.json"
    path.write_text(json.dumps({"messages": [
        {"type": "user", "text": "Please build the approved feature."},
        {"type": "assistant", "content": [
            {"type": "reasoning", "text": "PRIVATE_REASONING"},
            {"type": "text", "text": "Here is the plan."},
            {"type": "tool", "name": "shell", "state": {"content": [{"type": "text", "text": "TOOL_NOISE"}]}},
            {"type": "tool", "name": "question", "state": {
                "input": {"question": "Approve the seam?"},
                "content": [{"type": "text", "text": "Seam approved."}],
            }},
        ]},
    ]}), encoding="utf-8")
    return str(path)


def test_session_export_keeps_visible_dialogue_and_questions(tmp_path: Path) -> None:
    result = run_tool("read_session.py", "--input", session_file(tmp_path))
    assert result.returncode == 0
    for text in ("Please build", "Here is the plan", "Approve the seam?", "Seam approved."):
        assert text in result.stdout
    assert "PRIVATE_REASONING" not in result.stdout
    assert "TOOL_NOISE" not in result.stdout


def test_session_export_pages_without_losing_text(tmp_path: Path) -> None:
    path = session_file(tmp_path)
    first = run_tool("read_session.py", "--input", path, "--max-chars", "30")
    second = run_tool("read_session.py", "--input", path, "--start", "30", "--max-chars", "30")
    whole = run_tool("read_session.py", "--input", path)
    first_body = first.stdout.split("\n", 1)[1].removesuffix("\n")
    second_body = second.stdout.split("\n", 1)[1].removesuffix("\n")
    whole_body = whole.stdout.split("\n", 1)[1]
    assert first_body + second_body == whole_body[:60]
    assert "next --start 30" in first.stdout


def test_session_export_reports_bad_input_without_a_traceback(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("not json", encoding="utf-8")
    result = run_tool("read_session.py", "--input", str(path))
    assert result.returncode == 1
    assert "error:" in result.stderr.lower()
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("data", [
    {"messages": [None]},
    {"messages": [{"type": "assistant", "content": [None]}]},
    {"messages": [{"type": "assistant", "content": [{"type": "tool", "name": "question", "state": None}]}]},
], ids=["bad-message", "bad-part", "bad-question-state"])
def test_malformed_session_structure_reports_a_concise_error(tmp_path: Path, data: dict) -> None:
    path = tmp_path / "bad-structure.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = run_tool("read_session.py", "--input", str(path))
    assert result.returncode == 1
    assert "error:" in result.stderr.lower()
    assert "Traceback" not in result.stderr


def test_large_parameter_values_get_short_ids(tmp_path: Path) -> None:
    (tmp_path / "conftest.py").write_bytes((ROOT / "tests/conftest.py").read_bytes())
    (tmp_path / "test_sample.py").write_text(
        'import pytest\n@pytest.mark.parametrize("text", ["x" * 10000])\ndef test_sample(text): pass\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "x" * 100 not in result.stdout
    assert "text-10000-" in result.stdout
