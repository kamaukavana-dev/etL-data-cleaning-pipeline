.PHONY: install install-dev run test lint typecheck format security audit ci

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	python -m src.main

test:
	pytest

lint:
	ruff check src tests

typecheck:
	mypy src tests

format:
	black src tests

security:
	bandit -r src -x tests

audit:
	pip-audit -r requirements.txt

ci: lint typecheck test security audit
