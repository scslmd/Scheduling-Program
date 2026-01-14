from __future__ import annotations

from fastapi.testclient import TestClient

from app.examples import feasible_example, infeasible_example
from app.main import app

client = TestClient(app)


def test_solve_feasible() -> None:
    response = client.post("/solve", json=feasible_example().model_dump())
    assert response.status_code == 200
    assert "assignments" in response.json()


def test_solve_infeasible() -> None:
    response = client.post("/solve", json=infeasible_example().model_dump())
    assert response.status_code == 422
    assert response.json()["category"] == "COVERAGE_INFEASIBLE_NON_PRN"


def test_validate() -> None:
    response = client.post("/validate", json=feasible_example().model_dump())
    assert response.status_code == 200
    assert response.json()["is_valid"] is True

