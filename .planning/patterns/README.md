# Patterns — Reusable Solutions

This folder contains reusable solutions, fixes, and patterns discovered during Blender Python API development.

## Pattern Categories

### Geometry Nodes
- Node group creation patterns
- Attribute flow and data transfer
- Procedural mesh generation
- Instance management

### Camera Systems
- Follow camera implementations
- Shot preset configurations
- Anamorphic projection setups
- Camera animation workflows

### Rendering
- Eevee/Cycles render configuration
- Compositor node setups
- Render layer management
- Batch rendering patterns

### Animation
- Rigging automation
- Motion graphics workflows
- Simulation node patterns
- Driver setup and constraints

### Hair/Fur Systems
- Particle system configuration
- Grooming workflow automation
- Hair geometry node setups
- Texture-based hair control

## Pattern Format

Each pattern file should follow this structure:

```markdown
# Pattern Name

## Problem
Description of the problem this solves.

## Solution
The solution that works.

## Code Example
\`\`\`python
# Blender Python code here
import bpy
\`\`\`

## When to Use
- Condition 1
- Condition 2

## Gotchas
- Thing to watch out for
- Blender version considerations
```

## Usage

When encountering a problem:

1. Check this folder for existing patterns
2. If new solution found, create a pattern file
3. Update existing patterns with new learnings
4. Tag patterns with relevant Blender version (e.g., `blender-4.0+`)

## Naming Convention

Use descriptive names with domain prefix:
- `geo_nodes_attribute_flow.md`
- `camera_follow_smooth.md`
- `render_batch_automation.md`
- `hair_particle_control.md`
