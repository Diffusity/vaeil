"""Run alone: selected T2 behavioral mutations, restoring exact source bytes."""

import hashlib
import re
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/vaeil/domain/conversation.py"

# Each change preserves syntax; a kill must be a failing test, not collection error.
MUTATIONS = [
    ("active ignores Reveal", "return not self.revealed and not self.blocked", "return not self.blocked"),
    ("active ignores Block", "return not self.revealed and not self.blocked", "return not self.revealed"),
    ("Reveal closes chat", "return not self.blocked\n", "return self.active\n"),
    ("Block still allows chat", "return not self.blocked\n", "return True\n"),
    ("escalation ignores pair Reveal", "return not self.revealed\n", "return True\n"),
    ("projection context hides Reveal", "self.participant_ids, self.revealed)", "self.participant_ids, False)"),
    ("duplicate ID overwrites history", "if conversation_id in self._conversations:", "if False:"),
    ("reversed Block pair escapes exclusion", "frozenset(conversation.participant_ids) == frozenset(existing.participant_ids)", "conversation.participant_ids == existing.participant_ids"),
    ("restoring same record conflicts with itself", "if existing.conversation_id != conversation.conversation_id]", "if True]"),
    ("outsider can Block", "if actor_id not in conversation.participant_ids:", "if False:"),
    ("Block not recorded", "replace(conversation, blocked=True)", "replace(conversation, blocked=False)"),
    ("restore reverses Reveal", "or (previous.revealed and not conversation.revealed)", "or False"),
    ("restore reverses Block", "or (previous.blocked and not conversation.blocked)", "or False"),
    ("restore changes pair", "previous.participant_ids != conversation.participant_ids", "False"),
    ("open and restore ignore slots", "if conversation.active and any(", "if False and any("),
    ("open and restore ignore Block exclusion", "if any(existing.blocked and frozenset(conversation.participant_ids)", "if any(False and frozenset(conversation.participant_ids)"),
    ("same participant twice", "or pair[0] == pair[1]", "or False"),
    ("non-Boolean Reveal accepted", "or type(self.revealed) is not bool or type(self.blocked) is not bool", "or type(self.blocked) is not bool"),
    ("mutable Conversation", "@dataclass(frozen=True, slots=True)", "@dataclass(slots=True)"),
]


def write_source(content: bytes) -> None:
    for attempt in range(3):
        try:
            SOURCE.write_bytes(content)
            return
        except OSError as error:
            if error.errno != 22 or attempt == 2:
                raise
            time.sleep(0.05)


def main() -> int:
    original = SOURCE.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8").replace("\r\n", "\n")
    killed = 0
    try:
        for name, old, new in MUTATIONS:
            if text.count(old) != 1:
                raise ValueError(f"Mutation anchor is not unique: {name}")
            write_source(text.replace(old, new, 1).encode("utf-8"))
            # Ignore cached bytecode even for equal-length mutations on Windows.
            for cache in SOURCE.parent.glob("__pycache__/conversation.*.pyc"):
                cache.unlink()
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "tests/test_conversation.py", "--tb=no"],
                cwd=ROOT, capture_output=True, text=True, timeout=60,
            )
            valid_kill = (result.returncode == 1 and "failed" in result.stdout
                          and re.search(r"\b\d+ errors?\b", result.stdout) is None)
            killed += valid_kill
            print(f"{'KILLED' if valid_kill else 'SURVIVED/ERROR'} | {name}", flush=True)
            if not valid_kill:
                print(result.stdout + result.stderr)
            write_source(original)
    finally:
        write_source(original)
        for cache in SOURCE.parent.glob("__pycache__/conversation.*.pyc"):
            cache.unlink()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == digest
    print(f"{killed}/{len(MUTATIONS)} killed; restored SHA256 {digest}")
    return 0 if killed == len(MUTATIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
