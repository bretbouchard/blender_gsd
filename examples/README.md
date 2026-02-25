# Blender GSD Examples

This directory contains example scripts and configurations demonstrating Blender GSD capabilities.

## Example Categories

### `/basic`
Fundamental GSD patterns and workflows.

| Example | Description |
|---------|-------------|
| `hello_nodekit.py` | Create a simple node group programmatically |
| `mask_basics.py` | Zone-based mask creation and combination |
| `pipeline_stages.py` | 5-stage pipeline demonstration |

### `/control_surfaces`
Control surface design examples.

| Example | Description |
|---------|-------------|
| `neve_knob.py` | Generate Neve 1073 style knob |
| `ssl_fader.py` | SSL-style fader with LED meter |
| `moog_button.py` | Moog-style illuminated button |
| `style_morph.py` | Morph between console styles |

### `/cinematic`
Cinematic rendering examples.

| Example | Description |
|---------|-------------|
| `product_turntable.py` | 360° product turntable render |
| `three_point_lighting.py` | Classic three-point lighting setup |
| `orbit_animation.py` | Camera orbit around subject |
| `shot_from_yaml.py` | Assemble complete shot from YAML |

### `/charlotte`
Charlotte Digital Twin examples.

| Example | Description |
|---------|-------------|
| `downtown_scene.py` | Generate downtown Charlotte scene |
| `road_network.py` | Road network from OSM data |
| `building_extrusion.py` | Extrude buildings from footprints |

## Running Examples

Most examples can be run directly with Python:

```bash
# Run from Blender's Python
blender --python examples/basic/hello_nodekit.py

# Or use the Blender Python interpreter
/path/to/blender/python examples/basic/hello_nodekit.py
```

Some examples require additional setup:

```bash
# Charlotte examples need OSM data
python -c "from lib.charlotte_digital_twin import download_osm_data; download_osm_data('charlotte')"
```

## Example Structure

Each example follows this pattern:

```python
"""
Example: Brief Description

Demonstrates:
- Feature 1
- Feature 2

Usage:
    blender --python this_example.py
"""

from lib.some_module import SomeClass

def main():
    # Setup
    config = SomeClass(...)

    # Execute
    result = config.execute()

    # Verify
    assert result.success

if __name__ == "__main__":
    main()
```

## Contributing Examples

When adding new examples:

1. Keep them focused (one concept per example)
2. Include docstring with description and usage
3. Add assertions for validation
4. Update this README with the new example
