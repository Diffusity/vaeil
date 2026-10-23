"""Run the approved slice-2 mutations sequentially, always restoring sources."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DETECTION = ROOT / "src/vaeil/domain/identifiers.py"
PSEUDONYMS = ROOT / "src/vaeil/domain/pseudonym.py"


def main() -> None:
    mutations = [
        ("remove phone", DETECTION, "found.add(IdentifierReason.PHONE)", "pass"),
        *[(f"remove {reason.lower()}", DETECTION,
           "if reason in found)", f"if reason in found and reason is not IdentifierReason.{reason})")
          for reason in ("EMAIL", "HANDLE", "OBFUSCATED_EMAIL", "URL")],
        ("threshold 9", DETECTION, "MIN_PHONE_DIGITS = 10", "MIN_PHONE_DIGITS = 9"),
        ("threshold 11", DETECTION, "MIN_PHONE_DIGITS = 10", "MIN_PHONE_DIGITS = 11"),
        ("remove casefold", PSEUDONYMS, "key = value.casefold()", "key = value"),
        ("remove NFKC", PSEUDONYMS, 'unicodedata.normalize("NFKC", candidate).strip()', "candidate.strip()"),
        ("remove identifier check", PSEUDONYMS, "if scan_identifiers(value).is_flagged:", "if False:"),
        ("remove fixed-once guard", PSEUDONYMS, "if member_id in self._members:", "if False:"),
        ("remove reserved-name check", PSEUDONYMS, "if key in RESERVED_PSEUDONYMS:", "if False:"),
    ]
    for name, path, before, after in mutations:
        original = path.read_bytes()
        source = original.decode("utf-8")
        if source.count(before) != 1:
            raise RuntimeError(f"Mutation target changed: {name}")
        try:
            path.write_text(source.replace(before, after), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", "-m", "pytest", "-q", "--tb=no",
                 "tests/test_identifier_detection.py", "tests/test_pseudonyms.py"],
                cwd=ROOT, capture_output=True, text=True,
            )
            summary = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr
            if result.returncode != 1:
                raise RuntimeError(f"Mutation survived or errored: {name}: {summary}")
            print(f"{name}: {summary}", flush=True)
        finally:
            path.write_bytes(original)


if __name__ == "__main__":
    main()
