install:
	pip install -e ".[dev]"

format:
	black src tests
	ruff check --fix src tests

lint:
	ruff check src tests
	black --check src tests

test:
	pytest

check: lint test
