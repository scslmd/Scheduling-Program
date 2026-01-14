.PHONY: dev test lint format install

install:
	python -m pip install -r requirements-dev.txt

dev:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	python -m pytest

lint:
	python -m ruff check .

format:
	python -m ruff format .
