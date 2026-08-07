# BlueStocks Financial Intelligence Platform Makefile

PYTHON = python
PYTEST = pytest
SRC_DIR = src
TESTS_DIR = tests

.PHONY: help install test test-cov lint format clean run-api run-dashboard run-status

help:
	@echo "Available commands:"
	@echo "  make test          - Run full pytest test suite"
	@echo "  make test-cov      - Run pytest with code coverage report"
	@echo "  make lint          - Check code formatting and linting"
	@echo "  make format        - Format code using Black and isort"
	@echo "  make run-status    - Display database diagnostics via CLI"
	@echo "  make run-api       - Start embedded dashboard REST API server"
	@echo "  make run-dashboard - Start Streamlit interactive web dashboard"
	@echo "  make clean         - Remove bytecode cache and temporary files"

test:
	$(PYTHON) -m $(PYTEST) -v

test-cov:
	$(PYTHON) -m $(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing

lint:
	$(PYTHON) -m flake8 $(SRC_DIR) $(TESTS_DIR) --max-line-length=120 --ignore=E501,W503

format:
	$(PYTHON) -m black $(SRC_DIR) $(TESTS_DIR)
	$(PYTHON) -m isort $(SRC_DIR) $(TESTS_DIR)

run-status:
	$(PYTHON) -m src.cli status

run-api:
	$(PYTHON) -m src.api_server

run-dashboard:
	streamlit run src/dashboard/app.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
