# Quetzalcoatl - Feathered Serpent Generator

A procedural creature generation system for Blender 5.x, part of the [Blender GSD](https://github.com/bretbouchard/blender_gsd) project.

## Overview

Quetzalcoatl is a procedural generator for creating feathered serpent creatures inspired by Mesoamerican mythology. The system generates complete creature geometry including body, scales, wings, tail, and head with configurable parameters.

## Features

- **Procedural Body Generation**: Parametric body with customizable length, taper, and segmentation
- **Scale System**: Configurable scale patterns with multiple shapes (round, pointed, serrated)
- **Feathered Wings**: Procedural wing generation with configurable feather types
- **Tail Variations**: Multiple tail styles (feather tuft, rattle, fan)
- **Head Configuration**: Customizable crest types and head shapes
- **Color System**: Multiple color patterns including iridescent, gradient, and spotted
- **Animation Ready**: Built-in rig generation with bone definitions
- **Export Pipeline**: FBX export for Unreal Engine 5.x integration

## Architecture

```
lib/
├── types.py           # Core data types and configurations
├── color.py           # Color system with patterns and palettes
├── body.py            # Body geometry generation
├── scales.py          # Scale system with multiple patterns
├── wings.py           # Wing and feather generation
├── tail.py            # Tail geometry and variations
├── head.py            # Head configuration and generation
├── shader.py          # Material and shader system
├── animation.py       # Rig generation and bone definitions
└── export.py          # Export pipeline and presets
```

## Usage

```python
from projects.quetzalcoatl.lib import (
    QuetzalcoatlConfig,
    WingConfig,
    ScaleConfig,
    QuetzalcoatlGenerator,
)

# Create configuration
config = QuetzalcoatlConfig(
    length=5.0,
    wings=WingConfig(wing_type=WingType.FEATHERED),
    scales=ScaleConfig(shape=ScaleShape.ROUND),
)

# Generate creature
generator = QuetzalcoatlGenerator(config)
result = generator.generate("MyQuetzalcoatl")
```

## Requirements

- Python 3.11+
- NumPy
- Blender 5.x (for full functionality)
- PyYAML (for preset loading)

## Test Coverage

446 unit tests covering all components of the system.

## Version

1.0.0 - Production Ready

## License

Private - Part of Blender GSD Project

## Related

- [Blender GSD Main Repository](https://github.com/bretbouchard/blender_gsd)
- [Tentacle System](../lib/tentacle/) - Procedural tentacle generation
