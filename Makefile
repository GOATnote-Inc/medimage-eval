.PHONY: help venv install lint test test-integration preflight smoke clean

PY ?= python3.12
VENV := .venv

help:
	@echo "Targets:"
	@echo "  venv              create local virtualenv"
	@echo "  install           install package + dev extras into venv"
	@echo "  lint              run ruff + bandit"
	@echo "  test              hermetic unit tests"
	@echo "  test-integration  judges + network required"
	@echo "  preflight         verify judge keys before a long run"
	@echo "  smoke             single eval pass with synthetic inputs"

venv:
	$(PY) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

install: venv
	$(VENV)/bin/pip install -e .[dev,judges]

lint:
	$(VENV)/bin/ruff check src tests
	$(VENV)/bin/ruff format --check src tests
	$(VENV)/bin/bandit -q -r src

test:
	$(VENV)/bin/pytest -m "not integration" --cov=medimage_eval

test-integration:
	$(VENV)/bin/pytest -m integration

preflight:
	$(VENV)/bin/python -m medimage_eval.judges.preflight

smoke:
	$(VENV)/bin/python -m medimage_eval.cli smoke

clean:
	rm -rf $(VENV) build dist *.egg-info .pytest_cache .ruff_cache .coverage htmlcov
