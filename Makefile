.PHONY: setup install format lint test clean

VENV_BIN = venv/Scripts

setup:
	@echo "Creating directories..."
	mkdir -p data/raw data/processed src tests logs
	@echo "Initializing virtual environment..."
	python -m venv venv

install:
	@echo "Installing dependencies..."
	$(VENV_BIN)/pip install -r requirements.txt

format:
	@echo "Formatting code with black and isort..."
	$(VENV_BIN)/black src tests
	$(VENV_BIN)/isort src tests

lint:
	@echo "Linting with flake8 and mypy..."
	$(VENV_BIN)/flake8 src tests
	$(VENV_BIN)/mypy src

test:
	@echo "Running unit tests with pytest..."
	$(VENV_BIN)/pytest tests/ --cov=src --cov-report=term-missing

clean:
	@echo "Cleaning cache files..."
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
