from __future__ import annotations

import random

from app.canonical import canonical_json
from app.examples import feasible_example, infeasible_example
from app.models import InfeasibilityReport, SolverInput
from app.solver import solve_schedule


def test_solver_feasible_meets_coverage() -> None:
    data = feasible_example()
    result = solve_schedule(data)
    assert not isinstance(result, InfeasibilityReport)
    assert len(result.assignments) == 1


def test_solver_infeasible_category() -> None:
    data = infeasible_example()
    result = solve_schedule(data)
    assert isinstance(result, InfeasibilityReport)
    assert result.category == "COVERAGE_INFEASIBLE_NON_PRN"


def test_solver_prn_governance() -> None:
    data = feasible_example()
    data.allow_prn = True
    data.staff.append(
        data.staff[0].model_copy(update={"id": "staff-prn", "employment_type": "PRN"})
    )
    result = solve_schedule(data)
    assert isinstance(result, InfeasibilityReport)
    assert result.category == "PRN_NOT_APPROVED"


def test_deterministic_canonicalization() -> None:
    data = feasible_example()
    shuffled = SolverInput.model_validate(data.model_dump())
    random.shuffle(shuffled.staff)
    random.shuffle(shuffled.locations)
    random.shuffle(shuffled.shift_blocks)
    random.shuffle(shuffled.coverage_requirements)

    assert canonical_json(data) == canonical_json(shuffled)

