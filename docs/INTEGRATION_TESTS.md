# Integration Tests

This document explains how to run integration tests that require Blender.

## Overview

Integration tests verify that the GSD code works correctly with the actual Blender environment.
 These tests require:
- **Blender 4.0+** installed
- **Python 3.9+** (bundled with Blender)
- **bpy module** available

## Running Integration Tests

### Method 1: Using Blender's Python interpreter

```bash
# Run Blender with the test script
blender --background --python-expr "import pytest; pytest.main(['tests/blender_integration/', '-v'])"
``

### Method 2: Using pytest with Blender environment

```bash
# Set up environment to use Blender's Python
export BLENDER_PYTHON=/Applications/Blender.app/Contents/Resources/4.0/python/bin/python3.11

# Run pytest with bpy module available
pytest tests/blender_integration/ -v -m blender_integration
```

### Method 3: Running in Docker container

```bash
# Build and run the docker run --rm
docker build -f docker/DCP/Dockerfile.test .
docker run --rm -it --volumes-from=.:/app -v $(pwd):/app -w $(pwd) --entrypoint pytest tests/blender_integration/ -v
```

## Test Categories

### Geometry Nodes Tests
- `test_geometry_nodes.py` - Tests for Geometry Nodes creation
- Node tree creation
- Input/output nodes
- Attribute nodes
- Socket interfaces

### Cinematic System Tests
- `test_cinematic.py` - Tests for cinematic functionality
- Camera system
- Lighting system
- Render system
- Backdrop system

### Vehicle Stunts Tests
- `test_vehicle_stunts.py` - Tests for stunt system
- Ramp creation
- Course building
- Course validation

## Adding New Integration Tests

1. Create test file in `tests/blender_integration/`
2. Use `@requires_blender` decorator
3. Import from lib modules
4. Clean up Blender objects after tests

Example:
```python
import pytest
from . import requires_blender

@requires_blender
class TestMyFeature:
    def test_something(self):
        import bpy
        from lib.my_module import my_function

        result = my_function()
        assert result is not None

        # Cleanup
        bpy.data.objects.remove(result)
```

## CI Integration

Integration tests can be integrated into CI pipeline using GitHub Actions:

```yaml
# .github/workflows/integration.yml
name: Integration Tests

on: [push, workflow_dispatch]
  - ubuntu-latest

  - uses: actions/setup-blender@v1

steps:
  - name: Run Integration Tests
    run: |
      pip install pytest
      pytest tests/blender_integration/ -v --tb=short
```
