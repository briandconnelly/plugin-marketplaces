"""Parse tests/scenarios.md: the arm preamble, each scenario's prompt and criteria, scoring.

The dispatch prompt and the scorer's criteria are cut from the document, never retyped,
so what an arm and a scorer receive is exactly what the document says.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "tests" / "scenarios.md"


@dataclass(frozen=True)
class Scenario:
    number: int
    prompt: str
    criteria: str

    @property
    def has_upstream(self) -> bool:
        return "UPSTREAM" in self.prompt


def _quote(block: str) -> list[str]:
    return [line[2:] for line in block.splitlines() if line.startswith("> ")]


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    following = re.search(r"^##+ ", text[start + len(heading) :], re.M)
    end = start + len(heading) + following.start() if following else len(text)
    return text[start:end]


def preamble(text: str) -> list[str]:
    return _quote(_section(text, "### Arm preamble"))


def scoring(text: str) -> str:
    return _section(text, "## Scoring (every scenario)").strip()


def scenario(text: str, number: int) -> Scenario:
    body = _section(text, f"## Scenario {number}:")
    prompt = body[body.index("**Prompt:**") : body.index("**Success criteria:**")]
    criteria = body[
        body.index("**Success criteria:**") : body.index("**Expected baseline failure:**")
    ]
    return Scenario(number, "\n".join(_quote(prompt)), criteria.strip())


def dispatch_prompt(text: str, number: int, workdir: Path, upstream: Path | None) -> str:
    item = scenario(text, number)
    lines = [line for line in preamble(text) if item.has_upstream or "UPSTREAM" not in line]
    prompt = "\n".join(lines) + "\n\n" + item.prompt
    prompt = prompt.replace("WORKDIR", str(workdir))
    if upstream is not None:
        prompt = prompt.replace("UPSTREAM", str(upstream))
    if "UPSTREAM" in prompt:
        raise ValueError(f"scenario {number} mentions UPSTREAM but no mirror was given")
    return prompt
