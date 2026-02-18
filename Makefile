# Blender GSD Makefile
# Common commands for development and execution

# Configuration
BLENDER ?= blender
TASK ?= tasks/example_artifact.yaml
PROJECT_ROOT := $(shell pwd)

# Default: show help
.PHONY: help
help:
	@echo "Blender GSD Framework"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  run       Run a task headlessly (TASK=...)"
	@echo "  inspect   Run a task and open Blender to inspect"
	@echo "  test      Run all tests"
	@echo "  clean     Remove build outputs"
	@echo "  init      Initialize a new project from template"
	@echo ""

# Run task headlessly
.PHONY: run
run:
	$(BLENDER) -b -P scripts/run_task.py -- $(TASK)

# Run task and open Blender for inspection
.PHONY: inspect
inspect:
	$(BLENDER) -P scripts/run_task.py -- $(TASK)

# Run tests
.PHONY: test
test:
	@echo "Running Python tests..."
	python3 -m pytest tests/ -v || true

# Clean build outputs
.PHONY: clean
clean:
	rm -rf build/
	rm -rf output/
	rm -rf artifacts/

# Initialize new project
.PHONY: init
init:
	@echo "Creating new project structure..."
	@read -p "Project name: " name; \
	mkdir -p $$name/{tasks,scripts,build,.planning}; \
	cp templates/project/README.md $$name/; \
	cp templates/project/Makefile $$name/ 2>/dev/null || true; \
	echo "Project $$name created. cd $$name && git init"

# Lint Python files
.PHONY: lint
lint:
	@echo "Linting Python files..."
	python3 -m ruff check lib/ scripts/ || true

# Format Python files
.PHONY: format
format:
	python3 -m ruff format lib/ scripts/

# Show current structure
.PHONY: tree
tree:
	@find . -type f -name "*.py" -o -name "*.yaml" | grep -v __pycache__ | sort

# Install Python dependencies (for development)
.PHONY: deps
deps:
	pip install pyyaml ruff pytest

# Scan asset library
.PHONY: scan-assets
scan-assets:
	@echo "Scanning /Volumes/Storage/3d ..."
	@find /Volumes/Storage/3d -name "*.blend" | wc -l | xargs echo "Blend files found:"
