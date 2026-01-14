# Scheduling-Program

Thin-slice scheduling prototype using FastAPI and OR-Tools CP-SAT.

## Requirements

- Python 3.12
- pip

## Install (pip-tools lockfiles)

```bash
python -m pip install -r requirements-dev.txt
```

## Run

```bash
make dev
```

## Test

```bash
make test
```

## Lint & Format

```bash
make lint
make format
```

## Solve Example

```bash
curl -X POST http://localhost:8000/solve \
  -H 'Content-Type: application/json' \
  -d '{
    "horizon_start_utc": "2024-01-01T00:00:00Z",
    "horizon_end_utc": "2024-01-02T00:00:00Z",
    "staff": [
      {"id": "staff-1", "employment_type": "FTD", "is_eligible": true}
    ],
    "locations": [{"id": "loc-1"}],
    "shift_blocks": [
      {"id": "shift-1", "start_utc": "2024-01-01T00:00:00Z", "end_utc": "2024-01-01T08:00:00Z"}
    ],
    "coverage_requirements": [
      {"location_id": "loc-1", "shift_block_id": "shift-1", "required_units": 1}
    ],
    "allow_prn": false,
    "prn_approval": null
  }'
```

## Infeasibility Categories

- `PRN_NOT_APPROVED`: PRN coverage requested without a valid approval window.
- `COVERAGE_INFEASIBLE_NON_PRN`: Coverage exceeds eligible capacity when PRN is not approved.
- `ELIGIBILITY_INFEASIBLE`: No eligible staff available.
- `MODEL_INFEASIBLE`: CP-SAT model infeasible.

## PRN Approval Payload Example

```json
{
  "allow_prn": true,
  "prn_approval": {
    "approved_by": "scheduler@example.com",
    "approved_at_utc": "2024-01-01T00:00:00Z",
    "expires_at_utc": "2024-01-02T00:00:00Z"
  }
}
```
