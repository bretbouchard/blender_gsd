# Eyes - Water Sphere & Swarm Effects

A procedural eye and water effect system for Blender 5.x, part of the [Blender GSD](https://github.com/bretbouchard/blender_gsd) project.

## Overview

The Eyes project focuses on procedural water sphere effects and swarm animations. It includes geometry nodes setups for creating dynamic water-based creatures and effects.

## Features

- **Water Sphere Generation**: Procedural water sphere with realistic displacement
- **Swarm Effects**: Multi-agent swarm simulation with smooth movement
- **Wave Patterns**: Configurable wave amplitude, frequency, and spread
- **Animation Support**: Frame-by-frame animation rendering
- **Material System**: Pearlescent and water-based materials

## Project Structure

```
eyes/
├── scripts/           # Python and geometry node scripts
├── configs/           # Configuration files
├── docs/              # Documentation
├── assets/            # Source assets
├── .planning/         # Project planning documents
└── *.blend            # Blender scene files
```

## Key Files

- `smooth_water_swarm.blend` - Main swarm animation scene
- `geo_nodes_swarm.blend` - Geometry nodes setup
- `water_sphere_test.blend` - Basic water sphere tests
- `simple_waves_sphere.blend` - Wave pattern experiments

## Render Outputs

The project includes various render tests:
- Swarm animations (600-10000 agents)
- Wave amplitude variations
- Spread pattern tests
- Pearlescent material tests

## Requirements

- Blender 5.x
- Python 3.11+

## Version

Experimental/Development

## License

Private - Part of Blender GSD Project

## Related

- [Blender GSD Main Repository](https://github.com/bretbouchard/blender_gsd)
