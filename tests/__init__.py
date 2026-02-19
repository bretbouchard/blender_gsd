"""
Blender GSD Cinematic System Test Suite

Test Organization:
==================

tests/
├── unit/              # Fast, isolated tests (< 1s each)
├── integration/       # Cross-module tests (< 10s each)
├── regression/        # Visual and math regression tests
└── fixtures/          # Test data and baselines

Running Tests:
==============

# Run all tests with coverage
pytest tests/ -v --cov=lib --cov-fail-under=80

# Run only fast unit tests
pytest tests/unit -v

# Run integration tests (requires Blender)
pytest tests/integration -v -m requires_blender

# Run regression tests
pytest tests/regression -v

Coverage Requirements:
======================

- Unit tests: 80%+ coverage required
- Integration tests: All phase boundaries tested
- Regression tests: All visual/math outputs have baselines
"""
