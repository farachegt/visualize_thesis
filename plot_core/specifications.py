from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VariableSpecification:
    source_name: str | None = None
    input_units: str | None = None
    target_units: str | None = None
    derivation_kind: str | None = None
    derivation_options: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceSpecification:
    label: str
    latitude_name: str | None = None
    longitude_name: str | None = None
    time_name: str | None = None
    vertical_name: str | None = None
    site_latitude: float | None = None
    site_longitude: float | None = None
    site_altitude: float | None = None
    site_label: str | None = None
    variables: dict[str, VariableSpecification] = field(default_factory=dict)
