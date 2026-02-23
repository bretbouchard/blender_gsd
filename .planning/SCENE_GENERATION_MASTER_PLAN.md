# Scene Generation System - Master Plan

**Version:** 2.0
**Created:** 2026-02-21
**Updated:** 2026-02-21
**Status:** Revised After Council of Ricks Review

---

## Executive Summary

This plan outlines a comprehensive system for automatic scene generation in Blender, enabling users to go from a high-level outline to a fully populated, lit, and rendered scene. The system integrates with existing assets (KitBash3D, Vitaly Bulgarov, 321 personal blend files), provides photoshoot-style lighting presets, and uses a hybrid Python + Geometry Nodes architecture.

**Key Architecture Decision (Council of Ricks):**
- **BSP Floor Plans** → Python pre-processing (`bsp_solver.py`)
- **L-System Roads** → Python pre-processing (`l_system.py`)
- **Geometry Nodes** → Consumes JSON from Python, generates final geometry

This hybrid approach avoids impossible pure-GN implementations while maintaining procedural generation benefits.

---

## Current State Assessment

### Existing Codebase (Strong Foundation)

| Module | Files | Status | Notes |
|--------|-------|--------|-------|
| `lib/cinematic/` | 45+ | ✅ Production Ready | Light rigs, backdrops, cameras, tracking |
| `lib/geometry_nodes/` | 13 | ✅ New | Node builder, curl noise, erosion, volumes |
| `lib/art/` | 4 | ✅ Foundation | Room builder, set types, props |
| `lib/animation/vehicle/` | 21 | ✅ Production Ready | Launch Control, car physics, damage |
| `lib/animation/city/` | 13 | ✅ Foundation | Road networks, OSM import, traffic |
| `lib/production/` | 11 | ✅ Production Ready | Config validation, execution engine |
| `lib/retro/` | 37 | ✅ Complete | CRT effects, pixel art, isometric |
| `lib/blender5x/` | 24 | ✅ New | ACES 2.0, SDF modeling, thin film |
| `lib/materials/sanctus/` | 8 | ✅ New | Shader tools, damage, weathering |

### External Asset Inventory

| Location | Assets | Type |
|----------|--------|------|
| `/Volumes/Storage/3d/kitbash/` | 23+ packs | KitBash3D environments, vehicles, sci-fi |
| `/Volumes/Storage/3d/animation/` | 200+ FX | VFX assets, Vitaly Bulgarov mechs |
| `/Volumes/Storage/3d/my 3d designs/` | 321 .blend | Personal work, bikes, cars, buildings |
| `/Volumes/Storage/3d/kitbash/kpacks/` | 70+ kits | DM-, KB-, Just Panels, Hexes |

### Configured in `asset_library.yaml`

- **KitBash3D Packs**: CyberPunk, Art Deco, Brutalist, Americana, Aftermath, Savage, Atompunk, Dieselpunk
- **Formats**: FBX, OBJ, BLEND
- **Categories**: kitbash, animation, printing, designs, reference

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SCENE GENERATION ORCHESTRATOR                    │
│                  "From Outline to Render in Minutes"                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  ASSET VAULT  │       │  SCENE BUILDER │       │ STUDIO SYSTEM │
│               │       │               │       │               │
│ • Indexing    │       │ • Layout Gen  │       │ • Photoshoots │
│ • Search      │       │ • Placement   │       │ • Lighting    │
│ • Scale Norm  │       │ • Roads       │       │ • Cameras     │
│ • Auto-Load   │       │ • Interiors   │       │ • Backdrops   │
└───────────────┘       └───────────────┘       └───────────────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    GEOMETRY NODES CORE    │
                    │  • NodeTreeBuilder        │
                    │  • InstanceController     │
                    │  • SimulationBuilder      │
                    │  • VolumeTools            │
                    └───────────────────────────┘
```

---

## Phase Breakdown

---

### PHASE 0: Testing Infrastructure (NEW - Council Required)
**Goal:** Establish testing foundation before any implementation

**Requirements:**
- REQ-TE-01: Unit Test Framework (80%+ coverage target)
- REQ-TE-02: Integration Test Suite (end-to-end scene generation)
- REQ-TE-03: Visual Regression Testing (screenshot comparison)
- REQ-TE-04: Performance Benchmarks (<100ms search, <5min scene gen)
- REQ-TE-05: Oracle Integration for deterministic validation

**Test Structure:**
```
tests/
├── unit/
│   ├── test_asset_vault.py
│   ├── test_bsp_solver.py        # NEW
│   ├── test_l_system.py          # NEW
│   └── test_scale_normalizer.py
├── integration/
│   ├── test_scene_generation.py
│   └── test_photoshoot_presets.py
└── visual/
    └── test_render_comparison.py
```

**Oracle Example:**
```python
from lib.oracle import Oracle

def test_bsp_generates_valid_floor_plan():
    solver = BSPSolver(seed=42)
    plan = solver.generate(width=10, height=8, room_count=5)
    Oracle.assert_equal(len(plan.rooms), 5)
    Oracle.assert_true(plan.is_connected())
```

**Estimated Time:** 3-4 days

---

### PHASE 1: Asset Vault System (Foundation)
**Goal:** Complete asset indexing, search, and auto-loading with security hardening

**Requirements:**
- REQ-AV-01: Asset Library Indexer (blend, fbx, obj, glb)
- REQ-AV-02: Metadata Extraction (dimensions, materials, textures)
- REQ-AV-03: Scale Normalization System (reference-based)
- REQ-AV-04: Category/Tag Management (YAML-driven)
- REQ-AV-05: Search API (text, tag, visual similarity)
- REQ-AV-06: Auto-Loader (context-based requirement resolution)
- REQ-AV-07: Thumbnail Generation System
- REQ-AV-08: Path Sanitization & Security (NEW - Council)
- REQ-AV-09: Audit Logging (NEW - Council)

**Key Files:**
- `lib/asset_vault/__init__.py`
- `lib/asset_vault/indexer.py`
- `lib/asset_vault/scanner.py`
- `lib/asset_vault/scale_normalizer.py`
- `lib/asset_vault/search.py`
- `lib/asset_vault/loader.py`
- `lib/asset_vault/thumbnails.py`
- `lib/asset_vault/types.py`
- `lib/asset_vault/security.py` (NEW - Council)

**Security Hardening (NEW):**
```python
# Path sanitization
def sanitize_path(path: str) -> Path:
    """Block path traversal, resolve symlinks, whitelist directories."""
    resolved = Path(path).resolve()
    if ".." in str(resolved):
        raise SecurityError("Path traversal blocked")
    if not any(resolved.is_relative_to(p) for p in ALLOWED_PATHS):
        raise SecurityError("Path outside allowed directories")
    return resolved
```

**Integration:**
- Extends `config/asset_library.yaml`
- Uses `bpy.data.libraries` for loading
- Creates `asset_index.db` (SQLite) for fast queries

**Estimated Time:** 5-7 days

---

### PHASE 2: Studio & Photoshoot System
**Goal:** Complete photoshoot lighting and backdrop presets with material library

**Requirements:**
- REQ-PH-01: Portrait Lighting Presets (12 patterns)
- REQ-PH-02: Product Photography Presets (8 categories)
- REQ-PH-03: Equipment Simulation (15+ types)
- REQ-PH-04: Camera Presets (8 focal lengths)
- REQ-PH-05: Backdrop System (7 types)
- REQ-PH-06: Photoshoot Orchestrator (combine all above)
- REQ-PH-07: Atmospherics (fog, haze, god rays)
- REQ-PH-08: Material Library System (NEW - Council)
- REQ-PH-09: Sanctus Integration (NEW - Council)
- REQ-PH-10: Material Variation System (NEW - Council)

**Key Files:**
- `lib/cinematic/photoshoot.py` (NEW)
- `lib/cinematic/equipment.py` (NEW)
- `lib/cinematic/atmospherics.py` (NEW)
- `lib/cinematic/preset_loader.py` (EXTEND)
- `lib/cinematic/material_library.py` (NEW - Council)
- `configs/cinematic/photoshoot_presets.yaml` (NEW)

**Material System (NEW):**
```python
# Material library with variation
class MaterialLibrary:
    def get_material(self, category: str, style: str) -> Material:
        """Get material with optional weathering variation."""
        base = self._load_base(category, style)
        return self._apply_variation(base, weathering=0.3)
```

**Extends Existing:**
- `lib/cinematic/lighting.py` → Add equipment mapping
- `lib/cinematic/light_rigs.py` → Add portrait patterns
- `lib/cinematic/backdrops.py` → Add backdrop types
- `lib/materials/sanctus/` → Full integration

**Estimated Time:** 5-6 days

---

### PHASE 3: Interior Layout System
**Goal:** Procedural room and interior generation using hybrid Python + GN architecture

**CRITICAL ARCHITECTURE CHANGE (Council of Ricks):**
BSP algorithm runs in **Python**, not pure Geometry Nodes. GN consumes JSON output.

**Requirements:**
- REQ-IL-01: Floor Plan Generator (BSP algorithm - PYTHON)
- REQ-IL-02: Wall System (with openings - GN from JSON)
- REQ-IL-03: Door/Window Library
- REQ-IL-04: Flooring Generator (patterns)
- REQ-IL-05: Ceiling System (with fixtures)
- REQ-IL-06: Staircase Generator
- REQ-IL-07: Furniture Placement Engine
- REQ-IL-08: Interior Detail System (moldings, wainscoting)

**Key Files:**
- `lib/interiors/__init__.py` (NEW)
- `lib/interiors/bsp_solver.py` (NEW - Python pre-processing)
- `lib/interiors/floor_plan.py`
- `lib/interiors/walls.py`
- `lib/interiors/flooring.py`
- `lib/interiors/furniture.py`
- `lib/interiors/details.py`
- `lib/interiors/room_types.py`

**BSP Architecture (NEW):**
```python
# lib/interiors/bsp_solver.py
class BSPSolver:
    """Binary Space Partitioning for floor plan generation.

    Runs in Python (not GN) because:
    - Requires recursive subdivision
    - Needs arbitrary depth iteration
    - GN has no loops/recursion

    Output: JSON floor plan consumed by GN Wall Builder
    """

    def generate(self, width: float, height: float, room_count: int, seed: int = None) -> FloorPlan:
        """Generate floor plan with connected rooms."""
        root = self._subdivide(Rect(0, 0, width, height), room_count)
        rooms = self._leaf_nodes(root)
        self._connect_rooms(rooms)
        return FloorPlan(rooms=rooms, connections=self.connections)

    def to_json(self) -> dict:
        """Export for GN consumption."""
        return {
            "version": "1.0",
            "rooms": [r.to_dict() for r in self.rooms],
            "connections": [c.to_dict() for c in self.connections]
        }
```

**JSON Interchange Format:**
```json
{
  "version": "1.0",
  "dimensions": {"width": 10.0, "height": 8.0},
  "rooms": [
    {
      "id": "room_0",
      "type": "living_room",
      "polygon": [[0,0], [5,0], [5,4], [0,4]],
      "doors": [{"wall": 1, "position": 0.5, "width": 0.9}],
      "windows": [{"wall": 0, "position": 0.3, "width": 1.2}]
    }
  ]
}
```

**Extends Existing:**
- `lib/art/room_builder.py` → JSON-based GN consumption
- `lib/art/set_types.py` → Room configuration types

**Estimated Time:** 8-11 days (increased for Python implementation)

---

### PHASE 4: Road & Urban Infrastructure
**Goal:** Complete road network and street element system using hybrid Python + GN

**CRITICAL ARCHITECTURE CHANGE (Council of Ricks):**
L-system road generation runs in **Python**, not pure Geometry Nodes. GN consumes JSON output.

**Requirements:**
- REQ-UR-01: Road Network Generator (L-system - PYTHON)
- REQ-UR-02: Road Geometry (lanes, markings, curbs - GN from JSON)
- REQ-UR-03: Intersection System (4-way, 3-way, roundabout)
- REQ-UR-04: Street Sign Library (MUTCD standards)
- REQ-UR-05: Street Lighting System
- REQ-UR-06: Urban Furniture (benches, bollards, etc.)
- REQ-UR-07: Pavement Materials
- REQ-UR-08: Crosswalk & Marking System

**Key Files:**
- `lib/urban/__init__.py` (NEW)
- `lib/urban/l_system.py` (NEW - Python pre-processing)
- `lib/urban/road_network.py`
- `lib/urban/road_geometry.py`
- `lib/urban/intersections.py`
- `lib/urban/signage.py`
- `lib/urban/lighting.py`
- `lib/urban/furniture.py`
- `lib/urban/markings.py`

**L-System Architecture (NEW):**
```python
# lib/urban/l_system.py
class LSystemRoads:
    """L-system road network generation.

    Runs in Python (not GN) because:
    - Requires string rewriting rules
    - Needs context-sensitive rule evaluation
    - GN has no string manipulation

    Output: JSON road network consumed by GN Road Builder
    """

    RULES = {
        "road": "road+road",           # Split
        "+": "turn[road]turn",         # Branch
        "turn": "turn-turn",           # Intersection
    }

    def generate(self, axiom: str, iterations: int, seed: int = None) -> RoadNetwork:
        """Generate road network from axiom."""
        result = axiom
        for _ in range(iterations):
            result = self._apply_rules(result)
        return self._parse_to_network(result)

    def to_json(self) -> dict:
        """Export for GN consumption."""
        return {
            "version": "1.0",
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges]
        }
```

**JSON Interchange Format:**
```json
{
  "version": "1.0",
  "nodes": [
    {"id": "node_0", "position": [0, 0], "type": "intersection_4way"},
    {"id": "node_1", "position": [50, 0], "type": "intersection_3way"}
  ],
  "edges": [
    {
      "id": "edge_0",
      "from": "node_0",
      "to": "node_1",
      "curve": [[0,0], [25,0], [50,0]],
      "lanes": 2,
      "width": 7.0
    }
  ]
}
```

**Extends Existing:**
- `lib/animation/city/road_network.py` → JSON-based GN consumption
- `lib/animation/city/street_elements.py` → Sign library

**Estimated Time:** 7-9 days (increased for Python implementation)

---

### PHASE 5: Scene Orchestrator
**Goal:** High-level scene generation from outline with progressive UX and CLI support

**Requirements:**
- REQ-SO-01: Scene Outline Parser (YAML/JSON)
- REQ-SO-02: Requirement Resolver (what assets needed)
- REQ-SO-03: Asset Selection Engine (best match)
- REQ-SO-04: Placement Orchestrator (coordinate all systems)
- REQ-SO-05: Scale Coordinator (maintain proportions)
- REQ-SO-06: Style Consistency (realistic vs stylized)
- REQ-SO-07: Review/Approval Workflow
- REQ-SO-08: Variation Generator (multiple takes)
- REQ-SO-09: UX Tiers (NEW - Council)
- REQ-SO-10: CLI Interface (NEW - Council)
- REQ-SO-11: Headless Execution (NEW - Council)
- REQ-SO-12: Checkpoint/Resume (NEW - Council)

**Key Files:**
- `lib/orchestrator/__init__.py` (NEW)
- `lib/orchestrator/outline_parser.py`
- `lib/orchestrator/requirement_resolver.py`
- `lib/orchestrator/asset_selector.py`
- `lib/orchestrator/placement.py`
- `lib/orchestrator/style_manager.py`
- `lib/orchestrator/review.py`
- `lib/orchestrator/variation.py`
- `lib/orchestrator/ux_tiers.py` (NEW - Council)
- `lib/orchestrator/cli.py` (NEW - Council)
- `lib/orchestrator/checkpoint.py` (NEW - Council)

**UX Tiers (NEW - Council):**
```
Tier 1: Templates (One-click, pre-built scenes)
├── Portrait Studio
├── Product Shot
├── Interior Scene
├── Street Scene
└── Full Environment

Tier 2: Wizard (Guided Q&A customization)
├── What type of scene?
├── What's the mood?
├── What assets to include?
└── Preview → Generate

Tier 3: YAML (Full configuration)
├── scene:
│     type: interior
│     rooms: 5
│     style: modern
│     ...

Tier 4: Python API (Programmatic)
├── from blender_gsd import SceneBuilder
├── scene = SceneBuilder().room(5).style("modern")
```

**CLI Specification (NEW - Council):**
```bash
# Template-based generation
blender-gsd scene-generate --template "Portrait Studio" --preset "rembrandt" --output scene.blend

# Asset indexing
blender-gsd asset-index --path /Volumes/Storage/3d/ --update

# Validation
blender-gsd validate --scene scene.blend --check scale,materials,lighting

# Headless execution
blender-gsd render --scene scene.blend --frames 1-120 --background --json-output
```

**Checkpoint System (NEW):**
```python
class Checkpoint:
    """Save/restore state at each pipeline stage."""

    def save(self, stage: str, data: dict):
        """Save checkpoint file for stage."""
        path = f".checkpoints/{stage}.json"
        with open(path, 'w') as f:
            json.dump(data, f)

    def resume(self, stage: str) -> dict:
        """Resume from checkpoint if exists."""
        path = f".checkpoints/{stage}.json"
        if os.path.exists(path):
            return json.load(open(path))
        return None
```

**Estimated Time:** 10-12 days (increased for CLI/UX)

---

### PHASE 6: Geometry Nodes Extensions
**Goal:** Fill gaps in GN capabilities with LOD and culling systems

**Requirements:**
- REQ-GN-01: Room Builder Node Group
- REQ-GN-02: Road Builder Node Group
- REQ-GN-03: Furniture Scatter System
- REQ-GN-04: Asset Instance Library
- REQ-GN-05: Scale Normalization Node
- REQ-GN-06: Style Transfer Nodes
- REQ-GN-07: LOD System (NEW - Council)
- REQ-GN-08: Culling Strategy (NEW - Council)

**Key Files:**
- `lib/geometry_nodes/room_builder.py` (NEW)
- `lib/geometry_nodes/road_builder.py` (NEW)
- `lib/geometry_nodes/scatter.py` (NEW)
- `lib/geometry_nodes/asset_instances.py` (NEW)
- `lib/geometry_nodes/lod_system.py` (NEW - Council)
- `lib/geometry_nodes/culling.py` (NEW - Council)
- `assets/node_groups/room_builder.blend` (NEW)
- `assets/node_groups/road_builder.blend` (NEW)

**LOD System (NEW - Council):**
```
LOD0: Full detail (<100 instances, <10m distance)
├── Full geometry
├── All materials
└── High-res textures

LOD1: Reduced polys (100-1000 instances, 10-50m)
├── Decimated geometry (25% polys)
├── Simplified materials
└── Medium textures

LOD2: Billboard/impostor (1000+ instances, >50m)
├── Camera-facing quad
├── Baked texture
└── Minimal shader
```

**Memory Budget (NEW):**
- Texture pool: 4GB max
- Geometry pool: 2GB max
- Instance buffer: 1GB max

**Estimated Time:** 6-8 days (increased for LOD/culling)

---

### PHASE 7: Character & Verticals
**Goal:** Organize and make accessible all character/mecha assets

**Requirements:**
- REQ-CH-01: Character Asset Index (all humanoid assets)
- REQ-CH-02: Rig Library (biped, quadruped, custom)
- REQ-CH-03: Costume/Wardrobe System (extend existing)
- REQ-CH-04: Mecha/Robot Parts Library (Vitaly Bulgarov)
- REQ-CH-05: Vehicle Parts Library (Launch Control, custom)
- REQ-CH-06: Assembly System (combine parts)

**Key Files:**
- `lib/characters/__init__.py` (NEW)
- `lib/characters/index.py`
- `lib/characters/rig_library.py`
- `lib/mecha/__init__.py` (NEW)
- `lib/mecha/parts_library.py`
- `lib/mecha/assembly.py`

**Extends Existing:**
- `lib/character/wardrobe_types.py` → Full wardrobe system
- `lib/animation/vehicle/` → Parts library

**Estimated Time:** 5-6 days

---

### PHASE 8: Quality & Review System
**Goal:** Automated review, approval workflow, and professional compositing pipeline

**Requirements:**
- REQ-QA-01: Automated Validation (scale, materials, lighting)
- REQ-QA-02: Visual Comparison (before/after, reference)
- REQ-QA-03: Checklist System (completion verification)
- REQ-QA-04: Report Generation (HTML, PDF)
- REQ-QA-05: Approval Workflow (pending, approved, revision)
- REQ-QA-06: Version History
- REQ-CP-01: Cryptomatte Pass System (NEW - Council)
- REQ-CP-02: Multi-Pass Render Pipeline (NEW - Council)
- REQ-CP-03: EXR Output Strategy (NEW - Council)
- REQ-CP-04: Post-Processing Chain (NEW - Council)

**Key Files:**
- `lib/review/__init__.py` (NEW)
- `lib/review/validation.py`
- `lib/review/comparison.py`
- `lib/review/checklists.py`
- `lib/review/reports.py`
- `lib/review/workflow.py`
- `lib/compositing/__init__.py` (NEW - Council)
- `lib/compositing/cryptomatte.py` (NEW - Council)
- `lib/compositing/multi_pass.py` (NEW - Council)
- `lib/compositing/post_process.py` (NEW - Council)

**Cryptomatte System (NEW - Council):**
```python
class CryptomatteConfig:
    """Cryptomatte pass configuration for object isolation."""

    def __init__(self):
        self.object_id_layers = [
            "characters",    # Isolate all characters
            "vehicles",      # Isolate all vehicles
            "environment",   # Isolate environment
            "props",         # Isolate props
        ]
        self.material_id_layers = [
            "metals",        # Selective color grading
            "glass",         # Refraction adjustments
            "fabric",        # Texture adjustments
        ]
```

**Multi-Pass Pipeline (NEW - Council):**
```
View Layer Configuration:
├── Beauty Pass (Combined)
├── Diffuse (Direct + Indirect)
├── Specular (Direct + Indirect)
├── Shadow Catch Pass
├── Ambient Occlusion
├── Volume (Fog/God rays)
├── Cryptomatte (Object + Material)
└── Emission

EXR Output:
├── 16-bit half-float (Preview)
├── 32-bit float (Production)
└── Layer naming: {scene}_{pass}_{frame}.exr
```

**Post-Processing Chain (NEW):**
```python
class PostProcessingChain:
    """Post-processing effects for final output."""

    def apply(self, beauty_pass: Image, passes: dict) -> Image:
        result = beauty_pass

        # Color grading
        result = self.apply_lut(result, "cinematic_film")

        # Film grain
        result = self.add_film_grain(result, intensity=0.15)

        # Lens effects
        result = self.add_chromatic_aberration(result, strength=0.5)
        result = self.add_lens_distortion(result, distortion=0.02)

        return result
```

**Hardware Specifications (NEW - Council):**
```
Minimum (Preview tier):
├── M1 MacBook Pro, 16GB RAM
├── Render time: <30s per frame
└── Max instances: 1,000

Recommended (Standard tier):
├── M2 Pro, 32GB RAM
├── Render time: <5min per frame
└── Max instances: 10,000

Production tier:
├── M2 Ultra, 64GB RAM OR Multi-GPU render farm
├── Render time: <30min per frame
└── Max instances: 100,000+
```

**Estimated Time:** 6-8 days (increased for compositing)

---

## Integration Points

### With Existing Modules

| New Module | Integrates With | Method |
|------------|-----------------|--------|
| Asset Vault | `config/asset_library.yaml` | Extends config |
| Photoshoot | `lib/cinematic/` | Adds presets |
| Interiors | `lib/art/room_builder.py` | BSP algorithm |
| Urban | `lib/animation/city/` | L-system roads |
| Orchestrator | All modules | Central coordinator |
| Review | `lib/production/` | Validation |

### Geometry Nodes Architecture

```
NodeGroup: Scene_Orchestrator
├── Input: Scene Outline (JSON)
├── Sub-Tree: Layout_Generator
│   ├── BSP_Floor_Plan
│   ├── Wall_Builder
│   └── Opening_Placer
├── Sub-Tree: Asset_Scatter
│   ├── Furniture_Pool
│   ├── Prop_Pool
│   └── Scale_Normalizer
├── Sub-Tree: Road_System
│   ├── Network_Generator
│   ├── Geometry_Builder
│   └── Furniture_Scatter
└── Output: Complete_Scene
```

---

## File Structure

```
lib/
├── asset_vault/           # NEW - Phase 1
│   ├── __init__.py
│   ├── indexer.py
│   ├── scanner.py
│   ├── scale_normalizer.py
│   ├── search.py
│   ├── loader.py
│   ├── thumbnails.py
│   └── types.py
├── cinematic/
│   ├── photoshoot.py      # NEW - Phase 2
│   ├── equipment.py       # NEW - Phase 2
│   └── atmospherics.py    # NEW - Phase 2
├── interiors/             # NEW - Phase 3
│   ├── __init__.py
│   ├── floor_plan.py
│   ├── walls.py
│   ├── flooring.py
│   ├── furniture.py
│   ├── details.py
│   └── room_types.py
├── urban/                 # NEW - Phase 4
│   ├── __init__.py
│   ├── road_network.py
│   ├── road_geometry.py
│   ├── intersections.py
│   ├── signage.py
│   ├── lighting.py
│   ├── furniture.py
│   └── markings.py
├── orchestrator/          # NEW - Phase 5
│   ├── __init__.py
│   ├── outline_parser.py
│   ├── requirement_resolver.py
│   ├── asset_selector.py
│   ├── placement.py
│   ├── style_manager.py
│   ├── review.py
│   └── variation.py
├── characters/            # NEW - Phase 7
│   ├── __init__.py
│   ├── index.py
│   └── rig_library.py
├── mecha/                 # NEW - Phase 7
│   ├── __init__.py
│   ├── parts_library.py
│   └── assembly.py
├── review/                # NEW - Phase 8
│   ├── __init__.py
│   ├── validation.py
│   ├── comparison.py
│   ├── checklists.py
│   ├── reports.py
│   └── workflow.py
└── geometry_nodes/
    ├── room_builder.py    # NEW - Phase 6
    ├── road_builder.py    # NEW - Phase 6
    ├── scatter.py         # NEW - Phase 6
    └── asset_instances.py # NEW - Phase 6

configs/
├── asset_library.yaml     # EXTEND
├── photoshoot_presets.yaml # NEW
├── room_types.yaml        # NEW
├── urban_standards.yaml   # NEW
└── scene_templates.yaml   # NEW

assets/
├── node_groups/           # NEW
│   ├── room_builder.blend
│   ├── road_builder.blend
│   └── scatter_system.blend
└── thumbnails/            # NEW (generated)
```

---

## Success Criteria

### Phase 1: Asset Vault
- [ ] 321 blend files indexed with metadata
- [ ] Search returns results in <100ms
- [ ] Auto-loading places assets at correct scale

### Phase 2: Photoshoot
- [ ] All 12 portrait patterns produce correct lighting
- [ ] 8 product presets render photorealistic
- [ ] Atmospherics integrate with existing backdrop system

### Phase 3: Interiors
- [ ] BSP generates valid floor plans with room adjacency
- [ ] All door/window openings cut correctly
- [ ] Furniture placement follows ergonomic rules

### Phase 4: Urban
- [ ] L-system generates connected road networks
- [ ] Intersections handle 3-way and 4-way correctly
- [ ] All signage follows MUTCD dimensions

### Phase 5: Orchestrator
- [ ] Scene outline → populated scene in <5 minutes
- [ ] Style consistency maintained across assets
- [ ] Review workflow tracks all changes

### Phase 6: GN Extensions
- [ ] Node groups work in Blender 5.x
- [ ] Performance acceptable with 10,000+ instances
- [ ] Scale normalization works across asset sources

### Phase 7: Characters
- [ ] All Vitaly Bulgarov parts indexed and searchable
- [ ] Assembly system combines parts correctly
- [ ] Rig library covers standard biped

### Phase 8: Review
- [ ] Validation catches 95% of common issues
- [ ] Reports generated automatically
- [ ] Approval workflow integrates with Beads

---

## Timeline (Revised v2.0)

| Phase | Duration | Parallel | Notes |
|-------|----------|----------|-------|
| 0. Testing Infrastructure | 3-4 days | - | Foundation |
| 1. Asset Vault | 5-7 days | Parallel with 0 | + Security |
| 2. Photoshoot | 5-6 days | Parallel with 1 | + Materials |
| 3. Interiors | 8-11 days | Sequential | + Python BSP |
| 4. Urban | 7-9 days | Parallel with 3 | + Python L-System |
| 5. Orchestrator | 10-12 days | Sequential | + CLI/UX |
| 6. GN Extensions | 6-8 days | Parallel with 5 | + LOD/Culling |
| 7. Characters | 5-6 days | Parallel with 5 | No change |
| 8. Review + Compositing | 6-8 days | Sequential | + Cryptomatte |

**Total Estimated:** 55-71 days (with parallelization: ~45-55 days)

**Changes from v1.0:**
- Added Phase 0 for testing foundation
- Increased times for Python implementations (BSP, L-System)
- Added time for CLI/UX/compositing requirements

---

## Dependencies (Revised v2.0)

```
Phase 0 (Testing) ─────────────────────────────────► ALL PHASES

Phase 1 ─────┬──► Phase 3 ─────► Phase 5 ─────► Phase 8
             │                  │
             │                  └──► Phase 6
             │
             └──► Phase 4 ──────► Phase 5

Phase 2 ───────────────────────► Phase 5

Phase 7 ───────────────────────► Phase 5

Python Pre-Processing:
├── bsp_solver.py (Phase 3) ──► GN Wall Builder
└── l_system.py (Phase 4) ────► GN Road Builder
```

---

## Risk Assessment (Revised v2.0)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Asset scale inconsistency | HIGH | MEDIUM | Reference-based normalization |
| GN performance with large scenes | MEDIUM | HIGH | LOD systems, culling |
| KitBash3D licensing | LOW | HIGH | Internal use only, no redistribution |
| Blender 5.x API changes | MEDIUM | MEDIUM | Test on beta, version guards |
| Complex intersection geometry | MEDIUM | MEDIUM | Start with 4-way only |
| **Python BSP complexity** (NEW) | MEDIUM | HIGH | Use proven algorithms, extensive testing |
| **L-System rule explosion** (NEW) | MEDIUM | MEDIUM | Limit iterations, validate output |
| **Testing coverage gaps** (NEW) | LOW | HIGH | 80%+ target, visual regression |
| **Security vulnerabilities** (NEW) | LOW | HIGH | Path sanitization, audit logging |

---

## Council of Ricks Review Summary

**Review Date:** 2026-02-21
**Decision:** CONDITIONAL APPROVE
**Mode:** All Hands on Deck (9 Specialists)

### Critical Issues (Fixed in v2.0)

| Issue | Resolution |
|-------|------------|
| BSP/L-system not feasible in pure GN | Moved to Python pre-processing |
| No testing strategy | Added Phase 0 with 80%+ coverage target |
| No Cryptomatte integration | Added multi-pass compositing pipeline |

### High Priority (Addressed)

| Issue | Resolution |
|-------|------------|
| No UX tiers | Added 4-tier system (Template/Wizard/YAML/API) |
| No CLI specification | Added CLI with headless support |
| No material library | Added Sanctus integration |

### Detailed Report
See `.planning/COUNCIL_REVIEW_REPORT.md` for full specialist reviews.

---

## Next Steps

1. **Phase 0 Planning** - Create detailed PLAN.md for Testing Infrastructure
2. **Begin Phase 0 & 1 in parallel** - Testing foundation + Asset indexing
3. **Create Python architecture** - BSP solver and L-system specifications
4. **Define JSON formats** - Interchange between Python and GN
5. **Iterate based on implementation learnings**

---

## Appendix A: Asset Pack Inventory

### KitBash3D Packs (23+)
- CyberPunk, Art Deco, Brutalist, Americana, Aftermath, Savage
- Atompunk, Dieselpunk, Brooklyn, Edo Japan, LA Downtown
- Sci-Fi Industrial, Veh Supercars, Age of Egypt, Aristocracy
- Elysium, EveryCity, Favelas, Future Slums, Future Warfare
- Goliath, Heavy Metal, Lunar Base, Middle East, Minerva
- Neo San Francisco, Neo Shanghai

### Kpacks (70+ kits)
- DM-Arrays, DM-Cables, DM-Decals, DM-Gui, DM-Solids, DM-Vents-Ribs
- KB 01-07 (Box Cores, Rectangular Cores, Circular Cores, Frames, Hydraulic, Panel Boxes, Swivels)
- Just Panels (2D1, 2D2, 2D3, 3D1, 3D2, Basic, Screw Heads)
- HEXES Mini Pack 04 (3D Mesh Inserts, Decals)
- Arch-2050, Arch-Panels
- Dosch-2.1, Dots, Dots-Custom, Dots-Materials
- Ft_Metal_Mats, IH-steam, Dune

### Vitaly Bulgarov (12 packs)
- ULTRABORG SUBD Armor Pack
- ULTRABORG SUBD Cyber Muscles Pack
- ULTRABORG SUBD Pistons Caps
- ULTRABORG SUBD Robo Guts
- ULTRABORG SUBD Wires Cables
- Black Widow Pack
- Black Phoenix
- Crates
- Floor Panels
- Megastructure
- Props
- Sci-Fi Crates, Sci-Fi Props

### VFX Assets
- 200 FX Alpha library
- AAA Clouds, Fog Planes, Gobos Light Textures

### Personal Designs (321 .blend files)
- Bikes, cars, armor, backrooms, buildings, bots, etc.

---

## Appendix B: Research Documents

- `.planning/research/PHOTOSHOOT_STYLES_RESEARCH.md`
- `.planning/research/LAYOUT_GENERATION_RESEARCH.md`
- `.planning/research/ROAD_SYSTEMS_RESEARCH.md`
- `.planning/research/ASSET_MANAGEMENT_RESEARCH.md`
