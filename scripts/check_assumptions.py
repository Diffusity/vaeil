"""Validate assumption IDs and explicit supersession relationships."""

import argparse
from datetime import date
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["ID", "Date", "Assumption", "Why it was made", "What would invalidate it", "Status", "Supersedes"]


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    entries: dict[str, tuple[str, list[str]]] = {}
    header_seen = False
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells == COLUMNS:
            header_seen = True
            continue
        if all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
            continue
        if len(cells) != len(COLUMNS):
            errors.append(f"line {number}: expected {len(COLUMNS)} columns")
            continue
        identifier, recorded, statement, reason, invalidation, status, supersedes = cells
        if not re.fullmatch(r"A\d{3,}", identifier):
            errors.append(f"line {number}: invalid assumption ID {identifier!r}")
        if identifier in entries:
            errors.append(f"line {number}: duplicate ID {identifier}")
        try:
            date.fromisoformat(recorded)
        except ValueError:
            errors.append(f"{identifier}: invalid date")
        if not all((statement, reason, invalidation)):
            errors.append(f"{identifier}: statement, reason and invalidation must be present")
        if status not in {"active", "superseded", "invalidated"}:
            errors.append(f"{identifier}: invalid status {status!r}")
        targets = [] if supersedes == "-" else [target.strip() for target in supersedes.split(",")]
        entries[identifier] = status, targets
    if not header_seen or not entries:
        errors.append("missing assumption table or entries")

    replacements: dict[str, list[str]] = {}
    for identifier, (_, targets) in entries.items():
        for target in targets:
            if target not in entries:
                errors.append(f"{identifier}: unknown predecessor {target}")
                continue
            replacements.setdefault(target, []).append(identifier)
            if entries[target][0] != "superseded":
                errors.append(f"{target}: replaced by {identifier} but not marked superseded")
    for identifier, (status, _) in entries.items():
        if status == "superseded" and identifier not in replacements:
            errors.append(f"{identifier}: superseded without a replacement link")

    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            errors.append(f"{identifier}: supersession cycle")
            return
        if identifier in visited or identifier not in entries:
            return
        visiting.add(identifier)
        for target in entries[identifier][1]:
            visit(target)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in entries:
        visit(identifier)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=ROOT / "docs/logs/assumptions.md")
    args = parser.parse_args()
    try:
        errors = validate(args.path)
    except (OSError, UnicodeError) as error:
        errors = [str(error)]
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if not errors:
        print("Assumption IDs and supersession links are consistent.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
