from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FundConfig:
    code: str
    market: str
    display_name: str
    enabled: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
