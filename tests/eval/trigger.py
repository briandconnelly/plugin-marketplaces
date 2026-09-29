"""Trigger-case runs: from a list of skill descriptions, does a fresh agent pick this skill?

Usage:
  uv run python tests/eval/trigger.py prepare OUT [--reps 3]
  uv run python tests/eval/trigger.py record OUT TASKS tests/runs/DATE-trigger.md

`prepare` writes OUT/<case>-r<k>/prompt.txt for every case in tests/trigger_cases.md; each
prompt lists this skill's frontmatter description beside the distractors in
tests/fixtures/trigger/distractors.json, in an order fixed per repetition. Dispatch each
prompt, exactly, to a fresh subagent. `record` finds each reply by its prompt and writes the
results table.
"""

from __future__ import annotations

import argparse
import datetime
import json
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from scenario_doc import ROOT
from transcript import find, load

CASES = ROOT / "tests" / "trigger_cases.md"
DISTRACTORS = ROOT / "tests" / "fixtures" / "trigger" / "distractors.json"
SKILL = ROOT / "skills" / "plugin-marketplaces" / "SKILL.md"
SKILL_NAME = "plugin-marketplaces"
ROW = re.compile(r'^\| "(.+)" \| .+ \|$')


@dataclass(frozen=True)
class Case:
    id: str
    prompt: str
    expected: str  # SKILL_NAME, or "none" for a case that must not load it


def cases(text: str) -> list[Case]:
    found: list[Case] = []
    for heading, prefix, expected in (
        ("## Positive cases", "p", SKILL_NAME),
        ("## Negative cases", "n", "none"),
    ):
        start = text.index(heading)
        end = text.find("\n## ", start + 1)
        block = text[start : end if end != -1 else len(text)]
        prompts = [m.group(1) for m in map(ROW.match, block.splitlines()) if m]
        found += [Case(f"{prefix}{i}", p, expected) for i, p in enumerate(prompts, start=1)]
    return found


def description() -> str:
    front = SKILL.read_text(encoding="utf-8").split("---\n")[1]
    return " ".join(yaml.safe_load(front)["description"].split())


def catalog(rep: int) -> list[tuple[str, str]]:
    skills = json.loads(DISTRACTORS.read_text(encoding="utf-8"))["skills"]
    entries = [(s["name"], s["description"]) for s in skills] + [(SKILL_NAME, description())]
    random.Random(rep).shuffle(entries)
    return entries


def render(case: Case, entries: list[tuple[str, str]]) -> str:
    listing = "\n".join(f"- `{name}`: {text}" for name, text in entries)
    return (
        f"Available skills:\n\n{listing}\n\n"
        f"A user sends this request:\n\n> {case.prompt}\n\n"
        "Which one skill from the list above, if any, should be loaded before answering it? "
        "Do not use any tools. "
        "Reply with the skill's name, or `none`, alone on the first line, then one sentence "
        "explaining the choice."
    )


def prepare(out: Path, reps: int = 3) -> list[Path]:
    made = []
    for case in cases(CASES.read_text(encoding="utf-8")):
        for rep in range(1, reps + 1):
            run = out / f"{case.id}-r{rep}"
            run.mkdir(parents=True)  # never reuse a run directory
            (run / "prompt.txt").write_text(render(case, catalog(rep)), encoding="utf-8")
            (run / "case.json").write_text(
                json.dumps(
                    {"id": case.id, "rep": rep, "prompt": case.prompt, "expected": case.expected}
                )
                + "\n",
                encoding="utf-8",
            )
            made.append(run)
    return made


def verdict(reply: str) -> str:
    first = next((line for line in reply.splitlines() if line.strip()), "")
    word = re.split(r"\s+[—–-]\s+|\s", first.strip())[0]
    return word.strip("`*_.,:;\"'").lower()


def offered(prompt: str) -> set[str]:
    """The skill names a rendered prompt lists."""
    return set(re.findall(r"^- `([^`]+)`:", prompt, re.M))


def passed(expected: str, chosen: str, names: set[str]) -> bool:
    if expected == SKILL_NAME:
        return chosen == SKILL_NAME
    # a negative case needs a real answer: `none` or another offered skill, never an empty reply
    return chosen != SKILL_NAME and (chosen == "none" or chosen in names)


def record(out: Path, tasks: Path, dest: Path) -> Path:
    rows = [
        "| Case | Rep | Expected | Chosen | Result | Reply |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    totals = {"p": [0, 0], "n": [0, 0]}
    models: set[str] = set()
    for run in sorted(out.glob("*-r*"), key=lambda p: (p.name[0] != "p", p.name)):
        case = json.loads((run / "case.json").read_text(encoding="utf-8"))
        prompt = (run / "prompt.txt").read_text(encoding="utf-8")
        t = load(find(tasks, prompt))
        models.update(t.models)
        chosen = verdict(t.report)
        ok = passed(case["expected"], chosen, offered(prompt))
        totals[case["id"][0]][0] += ok
        totals[case["id"][0]][1] += 1
        reply = " ".join(t.report.split()).replace("|", "\\|")
        rows.append(
            f"| {case['id']} | {case['rep']} | {case['expected']} | {chosen} | {'pass' if ok else 'FAIL'} | {reply} |"
        )
    doc = f"""# Trigger runs

Date: {datetime.date.today().isoformat()}.
Cases: `tests/trigger_cases.md`; distractors: `tests/fixtures/trigger/distractors.json`; description: `skills/plugin-marketplaces/SKILL.md` frontmatter at this commit.
Each prompt was dispatched, exactly as `tests/eval/trigger.py prepare` wrote it, to a fresh subagent (model: {", ".join(sorted(models))}).
A positive case passes when the reply chooses `{SKILL_NAME}`; a negative case passes when it chooses `none` or another offered skill.

Positive: {totals["p"][0]} of {totals["p"][1]} passed.
Negative: {totals["n"][0]} of {totals["n"][1]} passed.

{chr(10).join(rows)}
"""
    dest.write_text(doc, encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trigger-case runs.")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("out", type=Path)
    prep.add_argument("--reps", type=int, default=3)
    rec = sub.add_parser("record")
    rec.add_argument("out", type=Path)
    rec.add_argument("tasks", type=Path)
    rec.add_argument("dest", type=Path)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        for run in prepare(args.out.resolve(), args.reps):
            print(run)
    else:
        print(record(args.out.resolve(), args.tasks.resolve(), args.dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
