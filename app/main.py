from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from app.canonical import canonical_json
from app.examples import feasible_example, infeasible_example
from app.logging import configure_logging
from app.models import InfeasibilityReport, SolverInput, ValidationResult
from app.solver import precheck_infeasibility, solve_schedule

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI()


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    logger.info(
        "request.start",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
        },
    )
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    logger.info(
        "request.end",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/solve")
async def solve(payload: SolverInput, x_correlation_id: str | None = Header(None)):
    _ = x_correlation_id
    result = solve_schedule(payload)
    if isinstance(result, InfeasibilityReport):
        return JSONResponse(status_code=422, content=result.model_dump())
    return result


@app.post("/examples/feasible")
async def example_feasible() -> SolverInput:
    return feasible_example()


@app.post("/examples/infeasible")
async def example_infeasible() -> SolverInput:
    return infeasible_example()


@app.post("/validate")
async def validate(payload: SolverInput) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    precheck = precheck_infeasibility(payload)
    if precheck:
        errors.append(precheck.category)

    try:
        canonical_json(payload)
    except ValueError as exc:
        errors.append(str(exc))

    return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)
