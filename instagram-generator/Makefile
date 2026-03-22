.PHONY: install dev test lint typecheck format docker run schedule webhook doctor clean help

# ====================================================================
# Setup
# ====================================================================

install:  ## Install production dependencies
	pip install -r requirements.txt

dev:  ## Install dev dependencies (includes test/lint tools)
	pip install -r requirements-dev.txt

# ====================================================================
# Quality
# ====================================================================

test:  ## Run all tests
	pytest -v --tb=short -m "not integration"

test-cov:  ## Run tests with coverage report
	pytest --cov=. --cov-report=term-missing --cov-report=html -m "not integration"

test-all:  ## Run all tests including integration
	pytest -v --tb=short

lint:  ## Lint code with ruff
	ruff check .

format:  ## Format code with ruff
	ruff format .

typecheck:  ## Run mypy type checker
	mypy --ignore-missing-imports .

check: lint typecheck test  ## Run all checks (lint + typecheck + test)

# ====================================================================
# Run
# ====================================================================

run:  ## Generate content (interactive)
	python main.py auto-generate -c motivational

schedule:  ## Start the automated scheduler
	python main.py schedule

webhook:  ## Start the webhook server
	python main.py webhook --port 8080

doctor:  ## Run startup diagnostics
	python main.py doctor

batch:  ## Process all queued items
	python main.py batch --from-queue

# ====================================================================
# Docker
# ====================================================================

docker:  ## Build Docker image
	docker build -t instagram-generator .

docker-up:  ## Start scheduler + webhook (production)
	docker compose up -d scheduler webhook

docker-down:  ## Stop all services
	docker compose down

docker-logs:  ## Follow scheduler logs
	docker compose logs -f scheduler

# ====================================================================
# Maintenance
# ====================================================================

clean:  ## Remove build artifacts and cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
