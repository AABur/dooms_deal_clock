.PHONY: help init init-dev run tests test check format lint lint-all mypy deps-check clean js-lint js-format js-check docker-dev docker-build docker-logs docker-status docker-stop docker-clean
.DEFAULT_GOAL := help

# Default Python command using uv
PY := uv run python
PYTEST := uv run pytest
MYPY := uv run mypy
RUFF := uv run ruff
FLAKE8 := uv run flake8

# Help command
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

# Setup commands
init: ## Initialize project after cloning (install dependencies)
	@echo "Initializing project..."
	@echo "Checking uv installation..."
	@which uv > /dev/null || (echo "Error: uv is not installed. Please install uv first: https://github.com/astral-sh/uv" && exit 1)
	@echo "Creating virtual environment..."
	@uv venv
	@echo "Installing project dependencies..."
	@uv pip install -e .
	@echo "Creating necessary directories..."
	@mkdir -p data logs
	@echo "Creating .env file from template..."
	@if [ ! -f .env ]; then cp .env.example .env && echo ".env file created from template. Please edit it with your API credentials."; else echo ".env file already exists."; fi
	@echo "Project initialized! Edit .env file and run 'make run' to start."

init-dev: ## Initialize development environment (install dev dependencies)
	@echo "Initializing development environment..."
	@echo "Checking uv installation..."
	@which uv > /dev/null || (echo "Error: uv is not installed. Please install uv first: https://github.com/astral-sh/uv" && exit 1)
	@echo "Creating virtual environment..."
	@uv venv
	@echo "Installing project with dev dependencies..."
	@uv pip install -e ".[dev]"
	@echo "Creating necessary directories..."
	@mkdir -p data logs
	@echo "Creating .env file from template..."
	@if [ ! -f .env ]; then cp .env.example .env && echo ".env file created from template. Please edit it with your API credentials."; else echo ".env file already exists."; fi
	@echo "Development environment initialized! Edit .env file and run 'make run' to start."

# Run the application
run: ## Run the application
	$(PY) run.py

# Run all tests with coverage
tests: ## Run all tests with coverage and generate HTML report
	$(PYTEST) --cov=app --cov-report=term-missing --cov-report=html

# Run a specific test (usage: make test test_file.py::test_function)
test: ## Run specific test with coverage report (e.g., make test test_config.py or test_config.py::test_function)
	@if [ -z "$(filter-out test,$@)" ]; then \
		echo "Usage: make test <test_file.py::test_function_name>"; \
	else \
		$(PYTEST) tests/$(filter-out test,$@) --cov=app --cov-report=term-missing --cov-report=html; \
	fi

# Format code
format: ## Format code with ruff
	$(RUFF) format .

# Lint code with ruff
lint: ## Lint code with ruff
	$(RUFF) check .

# Lint code with wemake-python-styleguide
lint-wps: ## Lint code with wemake-python-styleguide
	$(FLAKE8) . --select=WPS

# Lint code with all linters
lint-all: format lint lint-wps ## Run all linting (format, ruff lint, wemake-python-styleguide)
	@echo "All linting completed"

# Type check
mypy: ## Run type checking with mypy
	$(MYPY) .

# Check dependencies installation
deps-check: ## Check if all dependencies are properly installed
	@echo "Checking uv installation..."
	@which uv > /dev/null || (echo "Error: uv is not installed" && exit 1)
	@echo "Checking Python environment..."
	@$(PY) --version
	@echo "Checking project dependencies..."
	@uv pip check || echo "Warning: Some dependencies may have issues"
	@echo "Dependencies check completed"

# Clean temporary files
clean: ## Clean temporary files and cache
	@echo "Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/ 2>/dev/null || true
	@rm -rf logs/* data/*.db* 2>/dev/null || true
	@rm -rf node_modules/ 2>/dev/null || true
	@echo "Cleanup completed"

# JavaScript/Frontend targets
js-lint: ## Lint JavaScript code
	@if [ -f package.json ]; then \
		if [ -d node_modules ]; then npm run lint; else echo "No node_modules found, skipping JS lint"; fi; \
	else echo "No package.json found, skipping JS lint"; fi

js-format: ## Format JavaScript code
	@if [ -f package.json ]; then \
		if [ -d node_modules ]; then npm run format; else echo "No node_modules found, skipping JS format"; fi; \
	else echo "No package.json found, skipping JS format"; fi

js-check: ## Check JavaScript formatting and linting
	@if [ -f package.json ]; then \
		if [ -d node_modules ]; then npm run check; else echo "No node_modules found, skipping JS check"; fi; \
	else echo "No package.json found, skipping JS check"; fi

# Run all checks (format, lint, type check)
check: format lint mypy js-check ## Run all checks (format, lint, type check, JS)
 
ui-tests: ## Run only UI (Playwright) tests
	uv run pytest -m ui tests/ui -q

# Docker targets
docker-dev: ## Start development Docker environment
	@echo "Starting development Docker environment..."
	@docker compose up -d

docker-auth: ## Run interactive Telegram auth inside container (creates data/dooms_deal_session.session)
	@docker compose run --rm dooms-deal-clock python scripts/telegram_auth.py

docker-status: ## Show Telegram authorization status
	@docker compose run --rm dooms-deal-clock python scripts/telegram_status.py

docker-build: ## Build Docker image
	@echo "Building Docker image..."
	@docker compose build

docker-logs: ## Show Docker container logs
	@docker compose logs -f

docker-status: ## Show Docker containers status
	@docker compose ps

docker-stop: ## Stop Docker containers
	@echo "Stopping Docker containers..."
	@docker compose down

docker-clean: docker-stop ## Stop containers and clean up
	@echo "Cleaning up Docker resources..."
	@docker compose down --volumes --remove-orphans
	@docker system prune -f
