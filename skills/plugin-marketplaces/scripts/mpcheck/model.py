"""Finding and status types shared by every check."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Status(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    INCONCLUSIVE = "inconclusive"
    UNPROVEN = "unproven"


@dataclass(frozen=True)
class Finding:
    check: str
    severity: Severity
    file: str
    message: str
    rule: str | None = None
    pointer: str = ""
    source: str = ""

    @property
    def level(self) -> str:
        return self.check.split(".")[0]

    @property
    def group(self) -> str:
        parts = self.check.split(".")
        return ".".join(parts[:2]) if parts[0] == "schema" else parts[0]

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = asdict(self)
        data["level"] = self.level
        data["group"] = self.group
        return data
