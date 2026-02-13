from __future__ import annotations

import math
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

CANONICAL_COLUMNS = ["run_id", "timestamp", "voltage", "current", "temperature", "cycle"]


class CanonicalSample(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: str
    timestamp: float
    voltage: float
    current: float
    temperature: Optional[float] = None
    cycle: Optional[int] = None

    @field_validator("timestamp", "voltage", "current", "temperature")
    @classmethod
    def _reject_nan(cls, value: float | None) -> float | None:
        if value is not None and math.isnan(value):
            raise ValueError("NaN is not allowed")
        return value
