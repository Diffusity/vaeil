"""Run T10 ranking and authorization mutations in an isolated worktree."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("reverse tie-break", "domain/matching.py",
     "(-pair.score, pair.participant_ids)", "(-pair.score, pair.participant_ids[::-1])",
     "tests/test_t10_matching.py", "rank_pairs"),
    ("rank scores lowest first", "domain/matching.py",
     "(-pair.score, pair.participant_ids)", "(pair.score, pair.participant_ids)",
     "tests/test_t10_matching.py", "descending_score"),
    ("allow active Members", "application/matching.py",
     "if pair.active for member_id", "if pair.blocked for member_id",
     "tests/test_t10_http.py", "both_must_accept"),
    ("ignore Blocked pair history", "application/matching.py",
     "(*conversations, *matches)", "(*(item for item in conversations if not item.blocked), *matches)",
     "tests/test_t10_http.py", "declined_pair"),
    ("ignore declined pair history", "application/matching.py",
     "(*conversations, *matches)", "(*conversations, *(item for item in matches if item.state != 'declined'))",
     "tests/test_t10_http.py", "declined_pair"),
    ("open after one acceptance", "application/matching.py",
     "if match.decisions == (MatchDecision.ACCEPT, MatchDecision.ACCEPT):",
     "if MatchDecision.ACCEPT in match.decisions:",
     "tests/test_t10_http.py", "both_must_accept"),
    ("broaden partner view", "http_matching.py",
     "partner=serialize_member_view(view.partner)", "partner=serialize_member_view(view.partner) | {'email': 'private'}",
     "tests/test_t10_http.py", "both_must_accept"),
    ("rank incomplete Members", "application/matching.py",
     "conversations = unit.list_conversations()",
     "profiles['00-draft'] = next(iter(profiles.values()))\n            conversations = unit.list_conversations()",
     "tests/test_t10_http.py", "declined_pair"),
)


def main() -> int:
    for name, relative, original, replacement, test, selector in CASES:
        path = ROOT / "src" / "vaeil" / relative
        source = path.read_bytes()
        newline = "\r\n" if b"\r\n" in source else "\n"
        needle = original.replace("\n", newline).encode()
        assert source.count(needle) == 1, name
        try:
            path.write_bytes(source.replace(needle, replacement.replace("\n", newline).encode()))
            run = subprocess.run([sys.executable, "-m", "pytest", "-q", test, "-k", selector],
                                 cwd=ROOT, text=True, capture_output=True, timeout=60)
            failures = [line for line in run.stdout.splitlines() if line.startswith(f"FAILED {test}::")]
            if run.returncode != 1 or not failures:
                print(f"{name}: no verified failure\n{run.stdout}\n{run.stderr}")
                return 1
            print(f"{name}: detected ({len(failures)} failing variants)", flush=True)
        finally:
            path.write_bytes(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
