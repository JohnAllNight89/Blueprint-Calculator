"""
Provenance tracking (Phase 9, Step 28 of the Master Outline).

Every computed value in the pipeline is wrapped in a DataPoint and
recorded in a Ledger. This is what lets any number in the final report
be traced back, step by step, to the four raw inputs -- proving that
nothing in the blueprint is arbitrary.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Status(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    INVENTORY = "INVENTORY"
    HEURISTIC = "HEURISTIC"
    DERIVED = "DERIVED"


@dataclass
class DataPoint:
    id: str
    system: str
    phase: str
    label: str
    value: Any
    source: list[str] = field(default_factory=list)
    calculation: str = ""
    status: Status = Status.IMPLEMENTED

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class Ledger:
    """Ordered registry of every DataPoint computed during a pipeline run."""

    def __init__(self) -> None:
        self._points: dict[str, DataPoint] = {}
        self._order: list[str] = []

    def record(
        self,
        id: str,
        *,
        system: str,
        phase: str,
        label: str,
        value: Any,
        source: list[str] | None = None,
        calculation: str = "",
        status: Status = Status.IMPLEMENTED,
    ) -> DataPoint:
        if id in self._points:
            raise ValueError(f"Data point '{id}' already recorded")
        dp = DataPoint(
            id=id,
            system=system,
            phase=phase,
            label=label,
            value=value,
            source=source or [],
            calculation=calculation,
            status=status,
        )
        self._points[id] = dp
        self._order.append(id)
        return dp

    def get(self, id: str) -> DataPoint:
        return self._points[id]

    def value(self, id: str) -> Any:
        return self._points[id].value

    def __contains__(self, id: str) -> bool:
        return id in self._points

    def trace(self, id: str, _seen: set[str] | None = None) -> list[DataPoint]:
        """Return the full ancestry chain feeding into a given data point."""
        seen = _seen if _seen is not None else set()
        if id in seen or id not in self._points:
            return []
        seen.add(id)
        dp = self._points[id]
        chain: list[DataPoint] = []
        for src in dp.source:
            chain.extend(self.trace(src, seen))
        chain.append(dp)
        return chain

    def all(self) -> list[DataPoint]:
        return [self._points[i] for i in self._order]

    def to_dict(self) -> dict:
        return {i: self._points[i].to_dict() for i in self._order}
