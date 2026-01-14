from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from ortools.sat.python import cp_model

from app.models import (
    Assignment,
    CoverageRequirement,
    EmploymentType,
    InfeasibilityReport,
    SolverInput,
    SolverResult,
)


def _prn_approval_valid(data: SolverInput, now: Optional[datetime] = None) -> bool:
    if not data.allow_prn:
        return False
    if data.prn_approval is None:
        return False
    if now is None:
        now = datetime.now(timezone.utc)
    return data.prn_approval.approved_at_utc <= now <= data.prn_approval.expires_at_utc


def _eligible_staff(data: SolverInput) -> List[str]:
    return [item.id for item in data.staff if item.is_eligible]


def _eligible_staff_for_solver(data: SolverInput) -> List[str]:
    approved = _prn_approval_valid(data)
    eligible = []
    for item in data.staff:
        if not item.is_eligible:
            continue
        if item.employment_type == EmploymentType.PRN and not approved:
            continue
        eligible.append(item.id)
    return eligible


def _is_prn_not_approved(data: SolverInput) -> bool:
    has_prn = any(item.employment_type == EmploymentType.PRN for item in data.staff)
    return data.allow_prn and has_prn and not _prn_approval_valid(data)


def _coverage_requirement_map(
    requirements: Iterable[CoverageRequirement],
) -> dict[tuple[str, str], CoverageRequirement]:
    return {(req.location_id, req.shift_block_id): req for req in requirements}


def precheck_infeasibility(data: SolverInput) -> Optional[InfeasibilityReport]:
    if _is_prn_not_approved(data):
        return InfeasibilityReport(
            category="PRN_NOT_APPROVED",
            message="PRN coverage requested without valid approval window.",
        )

    eligible_ids = _eligible_staff(data)
    if not eligible_ids:
        return InfeasibilityReport(
            category="ELIGIBILITY_INFEASIBLE",
            message="No eligible staff are available.",
        )

    eligible_for_solver = _eligible_staff_for_solver(data)
    requirement_map = _coverage_requirement_map(data.coverage_requirements)

    for (location_id, shift_block_id), req in requirement_map.items():
        if req.required_units == 0:
            continue
        if not eligible_ids:
            return InfeasibilityReport(
                category="ELIGIBILITY_INFEASIBLE",
                message="No eligible staff available for coverage.",
            )
        if req.required_units > len(eligible_for_solver):
            return InfeasibilityReport(
                category="COVERAGE_INFEASIBLE_NON_PRN",
                message=(
                    "Coverage exceeds eligible non-PRN capacity without approval."
                ),
                debug={
                    "location_id": location_id,
                    "shift_block_id": shift_block_id,
                    "required_units": req.required_units,
                    "eligible_staff": len(eligible_for_solver),
                },
            )

    return None


def solve_schedule(data: SolverInput) -> SolverResult | InfeasibilityReport:
    precheck = precheck_infeasibility(data)
    if precheck:
        return precheck

    approved = _prn_approval_valid(data)
    eligible_staff = [
        staff
        for staff in data.staff
        if staff.is_eligible and not (
            staff.employment_type == EmploymentType.PRN and not approved
        )
    ]

    model = cp_model.CpModel()
    assignments = {}

    for staff in eligible_staff:
        for requirement in data.coverage_requirements:
            key = (staff.id, requirement.location_id, requirement.shift_block_id)
            assignments[key] = model.NewBoolVar("assign_{}_{}_{}".format(*key))

    for requirement in data.coverage_requirements:
        vars_for_requirement = [
            assignments[(staff.id, requirement.location_id, requirement.shift_block_id)]
            for staff in eligible_staff
        ]
        model.Add(sum(vars_for_requirement) >= requirement.required_units)

    staff_shift_block_map: dict[tuple[str, str], list[cp_model.IntVar]] = defaultdict(list)
    for (staff_id, location_id, shift_block_id), var in assignments.items():
        staff_shift_block_map[(staff_id, shift_block_id)].append(var)

    for vars_for_shift in staff_shift_block_map.values():
        model.Add(sum(vars_for_shift) <= 1)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return InfeasibilityReport(
            category="MODEL_INFEASIBLE",
            message="CP-SAT model reported infeasible coverage.",
        )

    result_assignments = []
    for (staff_id, location_id, shift_block_id), var in assignments.items():
        if solver.Value(var) == 1:
            result_assignments.append(
                Assignment(
                    staff_id=staff_id,
                    location_id=location_id,
                    shift_block_id=shift_block_id,
                )
            )

    result_assignments.sort(
        key=lambda item: (item.shift_block_id, item.location_id, item.staff_id)
    )

    return SolverResult(assignments=result_assignments, metrics={}, violations=[])

