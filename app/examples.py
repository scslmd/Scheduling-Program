from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import (
    CoverageRequirement,
    Location,
    ShiftBlock,
    SolverInput,
    Staff,
)


def _base_time() -> datetime:
    return datetime(2024, 1, 1, tzinfo=timezone.utc)


def feasible_example() -> SolverInput:
    start = _base_time()
    end = start + timedelta(days=1)
    shift = ShiftBlock(
        id="shift-1",
        start_utc=start,
        end_utc=start + timedelta(hours=8),
    )
    return SolverInput(
        horizon_start_utc=start,
        horizon_end_utc=end,
        staff=[
            Staff(id="staff-1", employment_type="FTD", is_eligible=True),
            Staff(id="staff-2", employment_type="PT", is_eligible=True),
        ],
        locations=[Location(id="loc-1")],
        shift_blocks=[shift],
        coverage_requirements=[
            CoverageRequirement(
                location_id="loc-1",
                shift_block_id=shift.id,
                required_units=1,
            )
        ],
        allow_prn=False,
    )


def infeasible_example() -> SolverInput:
    start = _base_time()
    end = start + timedelta(days=1)
    shift = ShiftBlock(
        id="shift-1",
        start_utc=start,
        end_utc=start + timedelta(hours=8),
    )
    return SolverInput(
        horizon_start_utc=start,
        horizon_end_utc=end,
        staff=[Staff(id="staff-1", employment_type="FTD", is_eligible=True)],
        locations=[Location(id="loc-1")],
        shift_blocks=[shift],
        coverage_requirements=[
            CoverageRequirement(
                location_id="loc-1",
                shift_block_id=shift.id,
                required_units=2,
            )
        ],
        allow_prn=False,
    )

