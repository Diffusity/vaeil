"""Run T11 Block and Report mutations in an isolated worktree."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("skip Block audit", "application/safety.py",
     "self._audit(unit, actor, conversation_id, AuditKind.CONVERSATION_BLOCKED, self.clock.now())",
     "pass", "tests/test_t11_http.py", "participant_blocks"),
    ("return chat history after Block", "application/messaging.py",
     "if conversation.blocked:\n                return ConversationMessagesView",
     "if not conversation.blocked:\n                return ConversationMessagesView",
     "tests/test_t11_http.py", "participant_blocks"),
    ("skip Report audit", "application/safety.py",
     "self._audit(unit, actor, report.report_id, AuditKind.REPORT_SUBMITTED, now)",
     "pass", "tests/test_t11_http.py", "participant_blocks"),
    ("allow Report decisions to change", "application/safety.py",
     'if report.decision is not None:\n                raise ReportConflictError("This Report decision is final.")',
     "if False:\n                pass",
     "tests/test_t11_http.py", "participant_blocks"),
    ("show resolved Reports in queue", "adapters/persistence.py",
     "select(reports).where(reports.c.decision.is_(None)).order_by(",
     "select(reports).order_by(", "tests/test_t11_http.py", "participant_blocks"),
    ("skip current Block at Message finalization", "application/messaging.py",
     "conversation = self._pair(unit, actor, conversation_id, sending=True)\n            if unit.review_text_exists",
     "current = self._pair(unit, actor, conversation_id)\n            conversation = type(current)(current.conversation_id, current.participant_ids, current.revealed)\n            if unit.review_text_exists",
     "tests/test_t11_http.py", "public_block_wins"),
)


def main() -> int:
    for name, relative, original, replacement, test, selector in CASES:
        path = ROOT / "src" / "vaeil" / relative
        source = path.read_bytes()
        newline = "\r\n" if b"\r\n" in source else "\n"
        needle = original.replace("\n", newline).encode()
        if needle not in source and newline != "\n":
            newline = "\n"
            needle = original.encode()
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
