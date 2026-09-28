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
    fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        marker = re.match(r"(`{3,}|~{3,})(.*)$", stripped)
        # A fence closes only on the same character, at least as long as its opener, with
        # nothing but whitespace after it; a line like ```python inside a fence is content.
        closes = (
            marker is not None
            and bool(fence)
            and marker.group(1)[0] == fence[0]
            and len(marker.group(1)) >= len(fence)
            and not marker.group(2).strip()
        )
        if marker and (not fence or closes):
            fence = "" if fence else marker.group(1)
            continue
        if fence or stripped.startswith("|"):
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
