from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, List, Optional

from pydantic import BaseModel, Field, model_validator


class EmploymentType(str, Enum):
    FTD = "FTD"
    PT = "PT"
    PRN = "PRN"


class Staff(BaseModel):
    id: str
    employment_type: EmploymentType
    is_eligible: bool


class Location(BaseModel):
    id: str


class ShiftBlock(BaseModel):
    id: str
    start_utc: datetime
    end_utc: datetime

    @model_validator(mode="after")
    def validate_range(self) -> "ShiftBlock":
        if self.start_utc >= self.end_utc:
            raise ValueError("shift block start must be before end")
        return self


class CoverageRequirement(BaseModel):
    location_id: str
    shift_block_id: str
    required_units: int = Field(ge=0)


class PrnApproval(BaseModel):
    approved_by: str
    approved_at_utc: datetime
    expires_at_utc: datetime

    @model_validator(mode="after")
    def validate_window(self) -> "PrnApproval":
        if self.approved_at_utc >= self.expires_at_utc:
            raise ValueError("approval window must be valid")
        return self


class SolverInput(BaseModel):
    horizon_start_utc: datetime
    horizon_end_utc: datetime
    staff: List[Staff]
    locations: List[Location]
    shift_blocks: List[ShiftBlock]
    coverage_requirements: List[CoverageRequirement]
    allow_prn: bool
    prn_approval: Optional[PrnApproval] = None

    @model_validator(mode="after")
    def validate_horizon(self) -> "SolverInput":
        if self.horizon_start_utc >= self.horizon_end_utc:
            raise ValueError("horizon start must be before end")
        return self


class Assignment(BaseModel):
    staff_id: str
    location_id: str
    shift_block_id: str


class SolverResult(BaseModel):
    assignments: List[Assignment]
    metrics: dict[str, Any] = Field(default_factory=dict)
    violations: List[str] = Field(default_factory=list)


class InfeasibilityReport(BaseModel):
    category: str
    message: str
    debug: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt.astimezone(timezone.utc)


def ensure_utc_models(items: Iterable[BaseModel]) -> None:
    for item in items:
        for field_name, value in item.model_dump().items():
            if isinstance(value, datetime):
                ensure_utc(value)


def to_iso_z(dt: datetime) -> str:
    return ensure_utc(dt).isoformat().replace("+00:00", "Z")

