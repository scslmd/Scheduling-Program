from __future__ import annotations

import json
from typing import Any

from app.models import SolverInput, to_iso_z


def _sorted_staff(staff):
    return sorted(staff, key=lambda item: item.id)


def _sorted_locations(locations):
    return sorted(locations, key=lambda item: item.id)


def _sorted_shift_blocks(shift_blocks):
    return sorted(
        shift_blocks,
        key=lambda item: (to_iso_z(item.start_utc), to_iso_z(item.end_utc), item.id),
    )


def _sorted_coverage(requirements):
    return sorted(requirements, key=lambda item: (item.location_id, item.shift_block_id))


def canonicalize_solver_input(data: SolverInput) -> dict[str, Any]:
    return {
        "horizon_start_utc": to_iso_z(data.horizon_start_utc),
        "horizon_end_utc": to_iso_z(data.horizon_end_utc),
        "staff": [
            {
                "id": item.id,
                "employment_type": item.employment_type.value,
                "is_eligible": item.is_eligible,
            }
            for item in _sorted_staff(data.staff)
        ],
        "locations": [{"id": item.id} for item in _sorted_locations(data.locations)],
        "shift_blocks": [
            {
                "id": item.id,
                "start_utc": to_iso_z(item.start_utc),
                "end_utc": to_iso_z(item.end_utc),
            }
            for item in _sorted_shift_blocks(data.shift_blocks)
        ],
        "coverage_requirements": [
            {
                "location_id": item.location_id,
                "shift_block_id": item.shift_block_id,
                "required_units": item.required_units,
            }
            for item in _sorted_coverage(data.coverage_requirements)
        ],
        "allow_prn": data.allow_prn,
        "prn_approval": (
            {
                "approved_by": data.prn_approval.approved_by,
                "approved_at_utc": to_iso_z(data.prn_approval.approved_at_utc),
                "expires_at_utc": to_iso_z(data.prn_approval.expires_at_utc),
            }
            if data.prn_approval
            else None
        ),
    }


def canonical_json(data: SolverInput) -> str:
    payload = canonicalize_solver_input(data)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))

