"""Fail when a Markdown line holds more than one sentence (see AGENTS.md)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

CODE_SPAN = re.compile(r"`[^`]*`")
LEAD = re.compile(r"^\s*(?:>\s*)?(?:#+\s*)?(?:\d+\.|[-*+])?\s*")
ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "vs.", "cf.")
BREAK = re.compile(r"[A-Za-z0-9)\]*_\"'`][.!?] +[A-Z]")


def violations(text: str) -> list[int]:
    found: list[int] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith("|"):
            continue
        prose = CODE_SPAN.sub("`code`", LEAD.sub("", line, count=1))
        for abbreviation in ABBREVIATIONS:
            prose = prose.replace(abbreviation, "ABBR")
        if BREAK.search(prose):
            found.append(number)
    return found


def main(argv: list[str]) -> int:
    status = 0
    for name in argv:
        for number in violations(Path(name).read_text(encoding="utf-8")):
            print(f"{name}:{number}: more than one sentence on this line")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
