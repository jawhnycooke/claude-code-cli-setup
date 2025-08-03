# Makefile for claude-code-setup Python project
# Equivalent to the npm scripts in package.json

.PHONY: help install install-dev build lint format typecheck test test-ci test-docker clean

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"  
	@echo "  build        Build the package (equivalent to npm run build)"
	@echo "  lint         Run ruff linter (equivalent to npm run lint)"
	@echo "  format       Format code with black (equivalent to npm run format)"
	@echo "  typecheck    Run mypy type checker (equivalent to npm run typecheck)"
	@echo "  test         Run tests (equivalent to npm test)"
	@echo "  test-ci      Run full CI pipeline (equivalent to npm run test:ci)"
	@echo "  test-docker  Run Docker integration tests for package installation"
	@echo "  clean        Clean build artifacts"

# Install dependencies
install:
	uv pip install -e .

install-dev: install
	uv pip install -r requirements-dev.txt

# Build the package (Python equivalent of tsup)
build:
	python -m build

# Linting (equivalent to eslint .)
lint:
	ruff check src/ tests/

# Format code (equivalent to prettier)  
format:
	black src/ tests/
	ruff check src/ tests/ --fix

# Type checking (equivalent to tsc --noEmit)
typecheck:
	mypy src/ --strict

# Run tests (equivalent to vitest run)
test:
	python -m pytest tests/ -v

# CI pipeline (equivalent to npm run test:ci)
test-ci: typecheck lint test

# Docker integration tests (tests package installation)
test-docker:
	./tests/docker/run-python-tests.sh

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete