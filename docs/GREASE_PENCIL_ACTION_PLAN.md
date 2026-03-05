# Grease Pencil Action Plan

## Making Tutorial Insights Actionable

This document outlines how to transform the Grease Pencil tutorial insights into actionable modules and utilities for our codebase.

---

## Node-Centric Philosophy

**Key Principle:** "Structure lives in nodes" - Grease Pencil workflows should leverage node-based systems where possible:

| Aspect | Node-Based Approach | Python Role |
|--------|---------------------|-------------|
| **Stroke Effects** | **GP Modifiers** (NOT Geometry Nodes) | Configure modifier stack |
| **Materials** | Shader Node groups | Create/configure node trees |
| **Animation** | Drivers + NLA system | Setup automation |
| **Compositing** | Compositor nodes | Pipeline integration |

**Why GP Modifiers (Not Geometry Nodes)?**
- **Geometry Nodes cannot process Grease Pencil data** - Geo Nodes operate on `bpy.types.Mesh`, `bpy.types.Curve`, `bpy.types.PointCloud`. `bpy.types.GreasePencil` is a distinct data type.
- **GP has its own modifier stack**: `GP_BUILD`, `GP_NOISE`, `GP_SMOOTH`, `GP_OPACITY`, `GP_COLOR`, `GP_ARMATURE`, etc.
- Non-destructive workflow
- Real-time preview
- Export-friendly (FBX, USD)
- Reusable presets
- GPU-accelerated performance

**Python's Role:**
- Configure GP modifiers from config
- Generate shader node graphs
- Setup drivers and constraints
- Automate tedious workflows
- Bridge between GSD intent and Blender execution

---

## Current State

- **Existing:** `lib/cinematic/composition.py` uses annotations (Grease Pencil-like) for composition guides
- **Existing:** `lib/animation/` has comprehensive rigging, IK/FK, pose library, face rig, shape keys
- **Existing:** `lib/geometry_nodes/` has NodeTreeBuilder for generating node graphs
- **Gap:** No dedicated Grease Pencil module for 2D animation workflows

---

## GSD Integration

These 4 phases integrate into the ROADMAP as **Milestone v0.18 - Grease Pencil System**:

| Phase | ROADMAP ID | Priority | Est. Days |
|-------|-----------|----------|-----------|
| Core GP Module | 21.0 | P1 | 3-4 |
| Animation Integration | 21.1 | P1 | 2-3 |
| 2D/3D Hybrid | 21.2 | P2 | 2-3 |
| Style Presets | 21.3 | P2 | 1-2 |

**Total:** 8-12 days

---

## Action Items

### Phase 21.0: Core Grease Pencil Module (`lib/grease_pencil/`)

**Priority: P1** | **Effort: 3-4 days** | **Impact: High**

Create a dedicated module for Grease Pencil workflows with node-centric architecture:

```
lib/grease_pencil/
├── __init__.py          # Main exports
├── types.py            # Dataclasses (GPStrokeConfig, GPMaterialConfig, GPAnimationConfig)
├── stroke_utils.py     # Stroke creation and manipulation
├── materials.py        # GP-specific shader node groups (stroke/fill)
├── rigging.py          # Bone rigging for GP strokes
├── animation.py        # Frame-by-frame, cut-out animation helpers
├── modifiers.py        # GP modifier presets (Build, Opacity, Mirror, etc.)
├── rotoscope.py        # Video reference tracing
├── node_effects.py     # Geometry Nodes effects for GP (NEW - node-centric!)
└── presets/
    ├── stroke_presets.yaml
    ├── material_presets.yaml
    └── animation_presets.yaml
```

**Node-Centric Features:**
- `node_effects.py` - Generate Geometry Nodes graphs for GP effects
- `materials.py` - Create shader node groups for NPR styles
- Modifier presets that configure GP modifiers via Python

### Phase 21.1: Integration with Existing Animation System

**Priority: P1** | **Effort: 2-3 days** | **Impact: Medium**

Connect GP module to existing `lib/animation/`:

- **Weight painting for GP strokes** - Extend `weight_painter.py` to support GP objects
- **Bone rigging integration** - Connect to `rig_builder.py` for GP armatures
- **Pose library extension** - Add GP pose capture to `pose_library.py`
- **Onion skinning** - Extend `onion_skin.py` for GP-specific display

### Phase 21.2: 2D/3D Hybrid Workflow Utilities

**Priority: P2** | **Effort: 2-3 days** | **Impact: High**

Create utilities for hybrid workflows:

```python
# lib/grease_pencil/hybrid.py

def draw_on_mesh_surface(mesh, stroke_config):
    """Draw GP strokes on 3D mesh UV space."""
    pass

def project_3d_to_2d(camera, gp_object):
    """Project 3D GP strokes to 2D plane for compositing."""
    pass

def convert_to_cutout_character(gp_object):
    """Convert frame-by-frame GP to cut-out rigged character."""
    pass
```

**Node-Centric Approach:**
- Use Geometry Nodes for surface projection effects
- Compositor nodes for 2D/3D layering
- Shader nodes for NPR-to-3D material blending

### Phase 21.3: NPR/Anime Style Presets

**Priority: P2** | **Effort: 1-2 days** | **Impact: Medium**

Create style presets for anime/NPR rendering using shader node groups:

```yaml
# lib/grease_pencil/presets/style_presets.yaml

anime_cel:
  stroke_style: "cel_shaded"
  fill_style: "flat_color"
  line_width: 2.0
  antialiasing: minimal
  shader_node_group: "NPR_AnimeCel"  # Reference to node group

ghibli_style:
  stroke_style: "pencil"
  fill_style: "watercolor"
  line_width: 1.5
  texture_overlay: true
  shader_node_group: "NPR_Ghibli"

90s_anime:
  stroke_style: "hard_edge"
  fill_style: "flat"
  limited_palette: true
  film_grain: 0.3
  shader_node_group: "NPR_90sAnime"
```

**Node Groups to Create:**
- `NPR_AnimeCel` - Clean cel shading with posterization
- `NPR_Ghibli` - Watercolor/soft gradient look
- `NPR_90sAnime` - Limited palette with film grain

---

## Implementation Order (Node-Centric)

| Order | Item | Effort | Dependencies | Node Focus |
|-------|------|--------|--------------|------------|
| 1 | Core GP module types | 2h | None | - |
| 2 | Stroke utilities | 4h | Types | - |
| 3 | Material node groups | 3h | Types | **Shader Nodes** |
| 4 | Basic animation | 4h | Types, Stroke utils | **Drivers** |
| 5 | Modifier presets | 2h | Types | GP Modifiers |
| 6 | Node effects (Geo Nodes) | 4h | Types | **Geometry Nodes** |
| 7 | Rigging integration | 4h | Animation, lib/animation | Bone constraints |
| 8 | Hybrid workflows | 4h | Stroke utils, lib/cinematic | **Compositor Nodes** |
| 9 | Style presets | 2h | Materials | **Shader Node Groups** |

**Total Estimated Effort: ~29 hours (8-12 days)**

---

## ROADMAP Integration

Add to `.planning/ROADMAP.md` as **Milestone v0.18**:

```markdown
## Milestone: v0.18 - Grease Pencil System
**Target**: TBD
**Requirements**: `.planning/REQUIREMENTS_GREASE_PENCIL.md`

### Phase 21.0: Core GP Module (REQ-GP-01)
**Priority**: P1 | **Est. Effort**: 3-4 days

**Goal**: Create lib/grease_pencil/ module with node-centric architecture.

**Features**:
- Stroke creation and manipulation utilities
- Material shader node groups for NPR styles
- Modifier presets (Build, Opacity, Mirror)
- Geometry Nodes effects for GP

### Phase 21.1: Animation Integration (REQ-GP-02)
**Priority**: P1 | **Est. Effort**: 2-3 days

**Goal**: Integrate with existing lib/animation/ system.

**Features**:
- Weight painting for GP strokes
- Bone rigging for GP objects
- Pose library for GP frames
- Onion skinning extension

### Phase 21.2: 2D/3D Hybrid (REQ-GP-03)
**Priority**: P2 | **Est. Effort**: 2-3 days

**Goal**: Utilities for hybrid 2D/3D workflows.

**Features**:
- Draw on mesh surface (UV space)
- 3D to 2D projection for compositing
- Cut-out character conversion

### Phase 21.3: Style Presets (REQ-GP-04)
**Priority**: P2 | **Est. Effort**: 1-2 days

**Goal**: NPR/Anime style presets with shader node groups.

**Presets**:
- Anime cel shading
- Ghibli watercolor
- 90s anime aesthetic
```

---

## Quick Wins (Can do now)

1. **Extend `composition.py`** - Already uses GP-like annotations, extend for full GP support
2. **Add GP weight painting** - Extend `weight_painter.py` with `paint_gp_stroke()` function
3. **Create GP pose capture** - Add to `pose_library.py` for GP frame poses
4. **Create shader node groups** - Use `lib/geometry_nodes/node_tree_builder.py` pattern for NPR shaders

---

## Python Workflow Update for Node-Centric GP

**Question:** "Does the Python workflow need to be updated for node-based GP?"

**Answer:** Yes, but minimally. The key change is **Python generates nodes, Python doesn't manipulate GP directly**.

### Current Pattern (Direct Python):
```python
# Old approach - direct manipulation
stroke = create_gp_stroke(points=[...])
stroke.line_width = 2.0
stroke.material = material
```

### Node-Centric Pattern (Python Generates Nodes):
```python
# New approach - generate node graph
from lib.grease_pencil import GPMaterialBuilder, GPNodeEffects

# Create shader node group for NPR style
material_builder = GPMaterialBuilder()
node_group = material_builder.create_npr_material("anime_cel")
# node_group is a ShaderNodeTree with proper connections

# Create Geometry Nodes effect
effects = GPNodeEffects()
geo_node_group = effects.create_build_effect("stroke_reveal")
# geo_node_group controls GP modifier via nodes
```

### What Changes:
| File | Change |
|------|--------|
| `materials.py` | Create ShaderNodeTree instead of GP materials directly |
| `node_effects.py` | NEW - Generate Geometry Nodes for GP effects |
| `modifiers.py` | Configure GP modifiers via Python (unchanged) |
| `stroke_utils.py` | Create strokes (unchanged) |

### What Stays the Same:
- Stroke creation (`stroke_utils.py`)
- Bone rigging (`rigging.py`)
- Animation helpers (`animation.py`)
- YAML presets structure

**Key Insight:** Use the existing `NodeTreeBuilder` pattern from `lib/geometry_nodes/` as a template for GP node generation.

---

## Knowledge Base Updates

Update `docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md` to add:

- Section 39: Grease Pencil Fundamentals (from tutorial 1.2)
- Section 40: Cut-Out Animation Rigging (from tutorial 2.3)
- Section 41: 2D/3D Hybrid Workflows (from tutorial 4.1)
- Section 42: NPR/Anime Styles (from tutorial 3.3)

---

## Success Metrics

- [ ] Can create GP stroke from Python
- [ ] Can assign GP material via shader node group
- [ ] Can rig GP strokes to armature
- [ ] Can animate GP frame-by-frame
- [ ] Can apply GP modifiers programmatically
- [ ] Can generate Geometry Nodes effects for GP
- [ ] Can convert 3D mesh to GP strokes
- [ ] Can achieve anime/NPR look with node-based presets
- [ ] 80%+ test coverage for GP module
