# UV Pass-Through Migration Guide

How to migrate from implicit UV handling to the explicit Store Named Attribute pattern for reliable Geometry Nodes → Shader UV transfer.

---

## Overview

**The Problem:**
UVs generated or modified in Geometry Nodes don't automatically appear in shaders.

**The Solution:**
Use **Store Named Attribute** node with **CORNER (Face Corner)** domain to explicitly pass UVs to shaders via the Attribute node.

---

## Quick Reference

| Component | Setting | Value |
|-----------|---------|-------|
| **Store Named Attribute** | Domain | `CORNER` (Face Corner) |
| | Data Type | `FLOAT_VECTOR` |
| | Name | Your UV name (e.g., "UV", "WaveUV") |
| **Attribute Node (Shader)** | Attribute Name | Same as Store node |

---

## Migration Patterns

### Pattern 1: Basic UV Pass-Through

**Before (Implicit - Doesn't Work):**
```
UV Map node → [expect shaders to see it]
```

**After (Explicit - Works):**
```
# Geometry Nodes
UV Map node → Store Named Attribute (CORNER, "UV")

# Shader
Attribute node ("UV") → Texture Vector input
```

**Implementation:**
```python
from lib.geometry_nodes.fields import FieldOperations

# Store UVs for shader access
store_node = FieldOperations.store_uv_for_shader(
    geometry=input_geometry,
    uv_data=uv_map_output,
    uv_name="UV",
    builder=node_builder,
    location=(400, 0)
)
```

---

### Pattern 2: Generate UV from Position

**Before (Manual Setup):**
```
Position → Separate XYZ → [math] → Combine XYZ → UV
# No shader access!
```

**After (With Storage):**
```python
from lib.geometry_nodes.fields import FieldOperations

# Create and store UVs from position in one step
result = FieldOperations.create_uv_from_position(
    geometry=input_geometry,
    plane="XZ",  # Use X and Z for UV (ground plane)
    scale=(1.0, 1.0),
    offset=(0.0, 0.0),
    uv_name="GroundUV",
    builder=node_builder,
    location=(200, -200)
)
```

**In Shader:**
```
Attribute ("GroundUV") → Image Texture Vector
```

---

### Pattern 3: Wave Texture UV (Ducky 3D Style)

**For animated wave textures on instances:**

```python
# 1. Get UV from instance geometry
uv_map = builder.add_node("GeometryNodeInputNamedAttribute", location=(0, -200))
uv_map.inputs["Name"].default_value = "UVMap"  # Original UV
uv_map.data_type = 'FLOAT_VECTOR'

# 2. Store for shader access
FieldOperations.store_uv_for_shader(
    geometry=geometry_socket,
    uv_data=uv_map.outputs["Attribute"],
    uv_name="WaveUV",
    builder=builder,
    location=(200, -200)
)
```

**Shader Setup:**
```
Attribute ("WaveUV") → Wave Texture Vector
Scene Time → Math (Multiply, 20*pi) → Wave Texture Phase Offset
Wave Texture → Color Ramp → Emission Strength
```

---

## Migration Checklist

For each Geometry Nodes setup that generates or modifies UVs:

- [ ] **Identify UV source** - Where do UVs come from? (UV Map, Position, Generated)
- [ ] **Add Store Named Attribute** - Before output
- [ ] **Set CORNER domain** - Critical for UV interpolation
- [ ] **Set FLOAT_VECTOR data type** - Required for 3D UV coordinates
- [ ] **Name consistently** - Use descriptive name (e.g., "GroundUV", "WaveUV")
- [ ] **Update shader** - Add Attribute node with matching name
- [ ] **Connect Attribute.Vector** - To texture vector input
- [ ] **Test** - Verify textures appear correctly

---

## Common Pitfalls

### Wrong Domain
```
❌ Domain: POINT
   → UVs interpolate incorrectly, seams visible

✅ Domain: CORNER (Face Corner)
   → Proper UV interpolation per-vertex-per-face
```

### Wrong Data Type
```
❌ Data Type: FLOAT_COLOR
   → Won't work as UV coordinates

✅ Data Type: FLOAT_VECTOR
   → Standard for UV coordinates
```

### Name Mismatch
```
❌ GN: Store Named Attribute ("uv")
   Shader: Attribute ("UV")
   → Case-sensitive, won't work!

✅ GN: Store Named Attribute ("GroundUV")
   Shader: Attribute ("GroundUV")
   → Exact match required
```

### Forgetting to Connect
```
❌ Store Named Attribute created but not connected to output
   → UVs never stored!

✅ Chain: Input → [Processing] → Store UV → Output
```

---

## Using Validation

The `gn_integration.py` module provides validation for UV storage:

```python
from lib.materials.ground_textures.gn_integration import (
    UVStorageSpec,
    validate_uv_storage,
)

# Define UV requirements
spec = UVStorageSpec(
    uv_attribute_name="GroundUV",
    domain='CORNER',
    data_type='FLOAT_VECTOR',
)

# Validate GN output
errors = validate_uv_storage(gn_output, node_tree)
if errors:
    print("UV storage issues:", errors)
```

---

## Code Examples

### Complete GN + Shader Setup

```python
from lib.geometry_nodes.fields import FieldOperations
from lib.geometry_nodes.builder import NodeBuilder

def create_ground_texture_setup(builder: NodeBuilder):
    """Create ground geometry with UV pass-through."""

    # Input
    input_node = builder.add_node("NodeGroupInput", location=(-800, 0))

    # Create ground plane
    grid = builder.add_node("GeometryNodeMeshGrid", location=(-600, 0))
    grid.inputs["Size X"].default_value = 10.0
    grid.inputs["Size Y"].default_value = 10.0

    # Generate UVs from position (XZ plane)
    result = FieldOperations.create_uv_from_position(
        geometry=grid.outputs["Mesh"],
        plane="XZ",
        scale=(1.0, 1.0),
        offset=(0.0, 0.0),
        uv_name="GroundUV",
        builder=builder,
        location=(-200, 0)
    )

    # Output
    output_node = builder.add_node("NodeGroupOutput", location=(400, 0))
    builder.links.new(result["geometry"], output_node.inputs["Geometry"])

    return result
```

### Shader Side

```python
def create_ground_material():
    """Create material that reads GN-stored UVs."""

    return {
        "nodes": [
            {
                "type": "ShaderNodeAttribute",
                "name": "get_uv",
                "location": (-800, 0),
                "attribute_name": "GroundUV",
            },
            {
                "type": "ShaderNodeTexImage",
                "name": "ground_texture",
                "location": (-600, 0),
                # Connect Attribute.Vector to Vector input
            },
            {
                "type": "ShaderNodeBsdfPrincipled",
                "name": "bsdf",
                "location": (-200, 0),
            },
            {
                "type": "ShaderNodeOutputMaterial",
                "name": "output",
                "location": (0, 0),
            },
        ],
        "links": [
            ("get_uv", "Vector", "ground_texture", "Vector"),
            ("ground_texture", "Color", "bsdf", "Base Color"),
            ("bsdf", "BSDF", "output", "Surface"),
        ],
    }
```

---

## Related Documentation

- `docs/NODE_TOOL_PATTERNS.md` - Reusable node patterns
- `docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md` - Tutorial knowledge base
- `lib/geometry_nodes/fields.py` - FieldOperations with UV helpers
- `lib/materials/shader_raycast.py` - Shader Raycast implementation

---

## Summary

| What | Why | How |
|------|-----|-----|
| Store Named Attribute | Pass UVs from GN to shader | Domain: CORNER, Type: FLOAT_VECTOR |
| Attribute Node | Read stored UVs in shader | Exact name match required |
| Validation | Catch issues early | UVStorageSpec + validate_uv_storage() |

**Key Insight:** The CORNER (Face Corner) domain is critical because UVs are per-vertex-per-face, not per-vertex. This allows proper interpolation across face boundaries and correct handling of UV seams.

---

*Migration Guide for UV Pass-Through Pattern - February 2026*
