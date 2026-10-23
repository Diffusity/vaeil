"""Read visible OpenCode dialogue in bounded pages, without storing raw exports."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def visible_dialogue(data: dict) -> str:
    entries: list[str] = []
    for message in data.get("messages", []):
        if message.get("type") == "user" and message.get("text"):
            entries.append(f"[USER]\n{message['text']}")
        elif message.get("type") == "assistant":
            for part in message.get("content", []):
                if part.get("type") == "text":
                    entries.append(f"[ASSISTANT]\n{part.get('text', '')}")
                elif part.get("type") == "tool" and part.get("name") == "question":
                    state = part.get("state", {})
                    entries.append("[QUESTION]\n" + json.dumps(state.get("input", {}), ensure_ascii=False))
                    for reply in state.get("content", []):
                        if reply.get("type") == "text":
                            entries.append(f"[ANSWER]\n{reply.get('text', '')}")
    return "\n\n".join(entries)


def main() -> int:
    # OpenCode transcripts contain Unicode even on legacy Windows code pages.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", nargs="?", help="OpenCode session ID")
    parser.add_argument("--input", type=Path, help="Read an existing JSON export instead")
    parser.add_argument("--start", type=int, default=0, help="Visible-text character offset")
    parser.add_argument("--max-chars", type=int, default=8000, help="Page size, 1-12000 characters")
    args = parser.parse_args()
    if args.start < 0 or not 1 <= args.max_chars <= 12000:
        parser.error("start must be nonnegative; max-chars must be 1-12000")
    if bool(args.session) == bool(args.input):
        parser.error("provide exactly one session ID or --input")
    try:
        if args.input:
            raw = args.input.read_text(encoding="utf-8-sig")
        else:
            executable = shutil.which("opencode")
            if not executable:
                raise ValueError("opencode is not installed or not on PATH")
            result = subprocess.run(
                [executable, "session", "export", args.session],
                capture_output=True, encoding="utf-8", timeout=60,
            )
            if result.returncode:
                raise ValueError("OpenCode export failed; inspect the session with opencode session list")
            raw = result.stdout.lstrip("\ufeff")
        data = json.loads(raw)
        if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
            raise ValueError("expected an OpenCode object containing a messages array")
        text = visible_dialogue(data)
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    end = min(args.start + args.max_chars, len(text))
    start = min(args.start, len(text))
    suffix = f"next --start {end}" if end < len(text) else "end of visible transcript"
    print(f"Visible characters {start}:{end} of {len(text)}; {suffix}")
    print(text[start:end])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
