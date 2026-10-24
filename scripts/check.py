"""Run the same non-mutating checks locally and in CI."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    commands = [
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "scripts/check_assumptions.py"],
        [sys.executable, "-m", "pytest", "-q"],
    ]
    for command in commands:
        print("Running: " + " ".join(command[1:]), flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
