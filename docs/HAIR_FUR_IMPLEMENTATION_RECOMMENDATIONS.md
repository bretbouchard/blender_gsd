# Hair & Fur Implementation Recommendations

**Context analysis and implementation strategy for the Blender GSD codebase.**

---

## Executive Summary

After reviewing the existing codebase, knowledge base, and test infrastructure, this document provides recommendations for implementing the hair/fur techniques uncovered from tutorial analysis.

### Key Findings

1. **Solid Foundation Exists** - `lib/geometry_nodes/hair.py` already implements:
   - `HairClumpGenerator` with spiral clump creation
   - `FurSystem` with fluent API
   - `create_fur()` convenience function

2. **Gaps to Fill**:
   - Hair Curve nodes (Blender 3.3+) not yet implemented
   - Multi-layer fur system missing
   - Clump convergence not implemented
   - Material templates not integrated

3. **Test Infrastructure** - Well-established patterns in `tests/unit/geometry_nodes/`

---

## Current State Analysis

### Existing Implementation (`lib/geometry_nodes/hair.py`)

**Strengths:**
- Clean fluent API design
- Good use of NodeTreeBuilder
- Comprehensive parameter options
- Well-documented code

**Limitations:**
- Only implements spiral-based fur (CGMatter method)
- Missing Blender 3.3+ Hair Curve nodes
- No multi-layer support
- Build method creates single clump variant (not using `add_clump_variants`)
- Missing pick instance for random clump selection

### NodeTreeBuilder Capabilities

The `node_builder.py` provides:
- `add_node()` - Create nodes with inputs
- `link()` - Connect sockets
- `add_simulation_zone()` - For simulations
- `add_repeat_zone()` - For iterations
- `wrap_as_group()` - Create reusable groups

### Test Patterns

From `test_scatter.py` and similar tests:
- Enum testing pattern
- Dataclass testing pattern
- Integration testing with seeds
- Edge case coverage
- Serialization testing (to_dict)

---

## Recommended Implementation Strategy

### Phase 1: Enhance Existing Hair.py

#### 1.1 Fix FurSystem.build() to Use Clump Variants

**Current Issue:** The `build()` method creates a single clump, ignoring `_clump_variants`.

**Solution:**

```python
def build(self, location: tuple[float, float] = (0, 0)) -> Optional[Node]:
    """Build with proper clump variant support."""
    if self.builder is None:
        return None

    b = self.builder

    # Create clump variants as instances
    clumps = []
    for i in range(self._clump_variants):
        variant = self._create_clump_variant(
            seed=i * 1000,
            location=(location[0] - 800, location[1] - 300 + i * 150),
        )
        if variant:
            clumps.append(variant)

    # Join variants for pick instance
    if len(clumps) > 1:
        join = b.add_node(
            "GeometryNodeJoinGeometry",
            (location[0] - 400, location[1] - 300),
            name="JoinClumpVariants",
        )
        for i, clump in enumerate(clumps):
            b.link(clump.outputs[0], join.inputs[0])
        clump_source = join.outputs[0]
    elif clumps:
        clump_source = clumps[0].outputs[0]
    else:
        return None

    # Distribute points on surface
    # ... existing distribution code ...

    # Instance with PICK INSTANCE enabled
    instance = b.add_node(
        "GeometryNodeInstanceOnPoints",
        (location[0] + 300, location[1]),
        name="InstanceFur",
    )

    # Key: Enable pick instance for random selection
    # Note: In Blender, pick instance is automatic when instance input varies
    b.link(clump_source, instance.inputs["Instance"])

    # Random selection via index
    index = b.add_node("GeometryNodeInputIndex", (location[0] + 200, location[1] - 200))
    random_select = b.add_node(
        "FunctionNodeRandomValue",
        (location[0] + 250, location[1] - 200),
    )
    random_select.inputs["Min"].default_value = 0
    random_select.inputs["Max"].default_value = self._clump_variants - 1
    b.link(index.outputs["Index"], random_select.inputs["ID"])

    # ... rest of build
```

#### 1.2 Add Missing Methods to HairClumpGenerator

```python
@staticmethod
def with_index_variation(
    builder: NodeTreeBuilder,
    base_node: Node,
    parameter_name: str,
    min_mult: float = 0.8,
    max_mult: float = 1.2,
    location: tuple = (0, 0),
) -> Node:
    """
    Apply index-based variation to a parameter.

    This is the CGMatter "Single Random Value" pattern.
    """
    index = builder.add_node("GeometryNodeInputIndex", location)

    random = builder.add_node(
        "FunctionNodeRandomValue",
        (location[0] + 100, location[1]),
    )
    random.inputs["Min"].default_value = min_mult
    random.inputs["Max"].default_value = max_mult
    builder.link(index.outputs["Index"], random.inputs["ID"])

    return random
```

### Phase 2: Add Hair Curve Nodes Support

#### 2.1 Create HairCurvesBuilder Class

**New file: `lib/geometry_nodes/hair_curves.py`**

```python
"""
HairCurves - Blender 3.3+ Hair Curve nodes system.

Uses the new Hair Curves system for modern hair workflows.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from bpy.types import Node, Object
    from .node_builder import NodeTreeBuilder


class HairDeformationType(Enum):
    """Available hair deformation types."""
    CLUMP = "clump"
    CURL = "curl"
    FRIZZ = "frizz"
    SMOOTH = "smooth"
    NOISE = "noise"
    TRIM = "trim"
    BRAID = "braid"


@dataclass
class DeformationStep:
    """A single deformation in the chain."""
    type: HairDeformationType
    strength: float = 0.5
    frequency: float = 5.0
    shape: float = 0.0


class HairCurvesBuilder:
    """
    Build hairstyles using Blender 3.3+ Hair Curve nodes.

    Usage:
        hair = HairCurvesBuilder("LongWavyHair")
        hair.set_length(0.4)
        hair.set_density(800)
        hair.add_deformation(HairDeformationType.CLUMP, strength=0.6)
        hair.add_deformation(HairDeformationType.CURL, strength=0.3, frequency=4)
        tree = hair.build()
    """

    def __init__(self, name: str):
        self.name = name
        self._length: float = 0.3
        _density: int = 500
        _deformations: list[DeformationStep] = field(default_factory=list)
        _builder: Optional[NodeTreeBuilder] = None

    def set_length(self, length: float) -> "HairCurvesBuilder":
        self._length = max(0.01, length)
        return self

    def set_density(self, density: int) -> "HairCurvesBuilder":
        self._density = max(1, density)
        return self

    def add_deformation(
        self,
        type: HairDeformationType,
        strength: float = 0.5,
        frequency: float = 5.0,
        shape: float = 0.0,
    ) -> "HairCurvesBuilder":
        self._deformations.append(DeformationStep(type, strength, frequency, shape))
        return self

    def clump(self, factor: float = 0.5, shape: float = 0.0) -> "HairCurvesBuilder":
        return self.add_deformation(HairDeformationType.CLUMP, factor, shape=shape)

    def curl(self, radius: float = 0.02, frequency: float = 5.0) -> "HairCurvesBuilder":
        return self.add_deformation(HairDeformationType.CURL, radius, frequency)

    def frizz(self, amount: float = 0.3, frequency: float = 10.0) -> "HairCurvesBuilder":
        return self.add_deformation(HairDeformationType.FRIZZ, amount, frequency)

    def smooth(self, factor: float = 0.5) -> "HairCurvesBuilder":
        return self.add_deformation(HairDeformationType.SMOOTH, factor)

    def build(self, builder: NodeTreeBuilder, location: tuple = (0, 0)) -> Node:
        """Build the hair curves node tree."""
        # Implementation
        pass
```

### Phase 3: Multi-Layer Fur System

#### 3.1 Create MultiLayerFur Class

**Add to `hair.py`:**

```python
@dataclass
class FurLayer:
    """A single layer in multi-layer fur."""
    name: str
    length: float
    density: int
    curl: float = 0.5
    scale: float = 0.03
    selection: Optional[str] = None  # Vertex group name
    color: tuple = (0.5, 0.4, 0.3, 1.0)


class MultiLayerFur:
    """
    Build realistic multi-layer fur systems.

    Usage:
        fur = MultiLayerFur("AnimalFur", builder)
        fur.set_surface(bpy.context.active_object)

        # Undercoat
        fur.add_layer(FurLayer("undercoat", length=0.08, density=1500, curl=0.8))

        # Guard hairs
        fur.add_layer(FurLayer("guard", length=0.25, density=150, curl=0.2))

        # Whiskers
        fur.add_layer(FurLayer("whiskers", length=0.6, density=15, curl=0.0))

        fur.build()
    """

    # Preset layer configurations
    PRESETS = {
        "wolf": [
            FurLayer("undercoat", 0.08, 2000, curl=0.9, scale=0.02),
            FurLayer("guard", 0.20, 200, curl=0.3, scale=0.04),
        ],
        "cat": [
            FurLayer("undercoat", 0.03, 3000, curl=0.7, scale=0.015),
            FurLayer("guard", 0.08, 300, curl=0.2, scale=0.025),
            FurLayer("whiskers", 0.15, 20, curl=0.0, scale=0.03),
        ],
        "bunny": [
            FurLayer("undercoat", 0.04, 4000, curl=0.8, scale=0.01),
            FurLayer("guard", 0.10, 250, curl=0.3, scale=0.02),
        ],
    }

    def __init__(self, name: str, builder: NodeTreeBuilder):
        self.name = name
        self.builder = builder
        self.surface = None
        self._layers: list[FurLayer] = []

    def set_surface(self, obj: Object) -> "MultiLayerFur":
        self.surface = obj
        return self

    def add_layer(self, layer: FurLayer) -> "MultiLayerFur":
        self._layers.append(layer)
        return self

    def use_preset(self, preset_name: str) -> "MultiLayerFur":
        if preset_name in self.PRESETS:
            self._layers = list(self.PRESETS[preset_name])
        return self

    def build(self, location: tuple = (0, 0)) -> Node:
        """Build multi-layer fur system."""
        if not self._layers:
            # Default 3-layer configuration
            self._layers = [
                FurLayer("undercoat", 0.08, 1500, curl=0.8),
                FurLayer("guard", 0.25, 150, curl=0.2),
                FurLayer("top", 0.35, 50, curl=0.1),
            ]

        # Implementation builds each layer and joins
        pass
```

### Phase 4: Material Integration

#### 4.1 Create Hair Material Helper

**Add to `hair.py`:**

```python
def create_hair_material(
    name: str = "HairMaterial",
    melanin: float = 0.5,
    roughness: float = 0.3,
    radial_roughness: float = 0.4,
    coat: float = 0.0,
    base_color: tuple = None,
) -> "bpy.types.Material":
    """
    Create Principled Hair BSDF material.

    Args:
        name: Material name
        melanin: Hair darkness (0=white, 1=black)
        roughness: Fiber texture amount
        radial_roughness: Cross-section detail
        coat: Optional shine
        base_color: Override color (ignores melanin)

    Returns:
        Configured material with Principled Hair BSDF
    """
    import bpy

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output node
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    # Principled Hair BSDF
    hair = nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.location = (300, 0)

    if base_color:
        hair.inputs["Parametrization"].default_value = 'COLOR'
        hair.inputs["Color"].default_value = base_color
    else:
        hair.inputs["Parametrization"].default_value = 'MELANIN'
        hair.inputs["Melanin"].default_value = melanin

    hair.inputs["Roughness"].default_value = roughness
    hair.inputs["Radial Roughness"].default_value = radial_roughness
    hair.inputs["Coat"].default_value = coat

    links.new(hair.outputs["BSDF"], output.inputs["Surface"])

    return mat


def create_stylized_hair_material(
    name: str = "StylizedHair",
    color: tuple = (0.8, 0.6, 0.4, 1.0),
    emission_strength: float = 1.0,
) -> "bpy.types.Material":
    """Create emission-based stylized hair material."""
    import bpy

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)

    emission = nodes.new("ShaderNodeEmission")
    emission.location = (100, 0)
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = emission_strength

    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    return mat
```

---

## Test Implementation

### Create `tests/unit/geometry_nodes/test_hair.py`

Following the established test patterns:

```python
"""
Unit tests for lib/geometry_nodes/hair.py

Tests the hair/fur system including:
- HairClumpGenerator static methods
- FurSystem fluent API
- create_fur convenience function
- Multi-layer fur system
- HairCurvesBuilder (Blender 3.3+)
"""

import pytest
import math

from lib.geometry_nodes.hair import (
    HairClumpGenerator,
    FurSystem,
    MultiLayerFur,
    FurLayer,
    SIZE_CURVES,
    create_fur,
    create_hair_material,
    create_stylized_hair_material,
)


class TestSizeCurves:
    """Tests for SIZE_CURVES distribution functions."""

    def test_uniform_curve(self):
        """Test uniform distribution."""
        curve = SIZE_CURVES["uniform"]
        assert curve(0.0) == pytest.approx(0.0, abs=0.001)
        assert curve(0.5) == pytest.approx(0.5, abs=0.001)
        assert curve(1.0) == pytest.approx(1.0, abs=0.001)

    def test_bias_small_curve(self):
        """Test bias_small produces more small values."""
        curve = SIZE_CURVES["bias_small"]
        assert curve(0.5) < 0.5  # x^2 < x for 0 < x < 1

    def test_bias_large_curve(self):
        """Test bias_large produces more large values."""
        curve = SIZE_CURVES["bias_large"]
        assert curve(0.5) > 0.5  # x^0.5 > x for 0 < x < 1

    def test_all_curves_defined(self):
        """Test all expected curves exist."""
        expected = ["uniform", "bias_small", "bias_large", "bell", "exponential", "sigmoid"]
        for name in expected:
            assert name in SIZE_CURVES
            assert callable(SIZE_CURVES[name])


class TestFurLayer:
    """Tests for FurLayer dataclass."""

    def test_default_values(self):
        """Test FurLayer defaults."""
        layer = FurLayer(name="test", length=0.1, density=100)
        assert layer.curl == 0.5
        assert layer.scale == 0.03
        assert layer.selection is None

    def test_custom_values(self):
        """Test FurLayer with custom values."""
        layer = FurLayer(
            name="undercoat",
            length=0.08,
            density=1500,
            curl=0.8,
            scale=0.02,
            color=(0.5, 0.4, 0.3, 1.0),
        )
        assert layer.length == 0.08
        assert layer.density == 1500


class TestMultiLayerFur:
    """Tests for MultiLayerFur system."""

    def test_preset_exists(self):
        """Test presets are defined."""
        assert "wolf" in MultiLayerFur.PRESETS
        assert "cat" in MultiLayerFur.PRESETS
        assert "bunny" in MultiLayerFur.PRESETS

    def test_preset_layer_count(self):
        """Test presets have correct layer counts."""
        assert len(MultiLayerFur.PRESETS["wolf"]) == 2
        assert len(MultiLayerFur.PRESETS["cat"]) == 3

    def test_default_layers(self):
        """Test default layer configuration."""
        # When no layers added, build() creates default 3-layer
        pass  # Requires Blender context


class TestHairMaterial:
    """Tests for hair material creation."""

    @pytest.mark.requires_blender
    def test_create_hair_material_basic(self, blender_available):
        """Test basic hair material creation."""
        if not blender_available:
            pytest.skip("Blender not available")

        import bpy

        mat = create_hair_material("TestHair", melanin=0.5)
        assert mat is not None
        assert mat.name == "TestHair"

        # Cleanup
        bpy.data.materials.remove(mat)

    @pytest.mark.requires_blender
    def test_create_stylized_material(self, blender_available):
        """Test stylized emission material."""
        if not blender_available:
            pytest.skip("Blender not available")

        import bpy

        mat = create_stylized_hair_material(
            "TestStylized",
            color=(1.0, 0.5, 0.3, 1.0),
            emission_strength=2.0,
        )
        assert mat is not None

        # Cleanup
        bpy.data.materials.remove(mat)


class TestFurSystemFluentAPI:
    """Tests for FurSystem fluent interface."""

    def test_method_chaining(self):
        """Test all methods return self."""
        system = FurSystem()

        result = system.set_density(1000)
        assert result is system

        result = system.set_scale_range(0.5, 1.5)
        assert result is system

        result = system.add_clump_variants(5)
        assert result is system

    def test_invalid_size_curve_raises(self):
        """Test invalid size curve raises ValueError."""
        system = FurSystem()

        with pytest.raises(ValueError, match="Invalid size curve"):
            system.set_size_curve("nonexistent")

    def test_valid_size_curves(self):
        """Test all valid size curves."""
        system = FurSystem()

        for curve_name in SIZE_CURVES.keys():
            result = system.set_size_curve(curve_name)
            assert result is system


# Integration test would go here, requiring full Blender context
```

---

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| **P0** | Fix FurSystem.build() to use clump variants | 2h | High |
| **P1** | Add create_hair_material() helper | 1h | High |
| **P2** | Create HairCurvesBuilder class | 4h | Medium |
| **P3** | Create MultiLayerFur class | 4h | Medium |
| **P4** | Add unit tests | 3h | High |
| **P5** | Update documentation | 2h | Medium |

---

## File Structure After Implementation

```
lib/geometry_nodes/
├── __init__.py          # Update exports
├── hair.py              # Enhanced with fixes + MultiLayerFur
├── hair_curves.py       # NEW: HairCurvesBuilder (Blender 3.3+)
└── curl_noise.py        # Existing (reference for patterns)

tests/unit/geometry_nodes/
├── test_hair.py         # NEW: Comprehensive tests
├── test_hair_curves.py  # NEW: Hair curve tests
└── test_scatter.py      # Existing (pattern reference)

docs/
├── HAIR_FUR_KNOWLEDGE_BASE.md         # Existing
├── HAIR_FUR_IMPLEMENTATION_GUIDE.md   # Existing
└── HAIR_FUR_IMPLEMENTATION_RECOMMENDATIONS.md  # This document
```

---

## Next Steps

1. **Immediate**: Fix `FurSystem.build()` to properly use `_clump_variants`
2. **Short-term**: Add `create_hair_material()` to `hair.py`
3. **Medium-term**: Implement `HairCurvesBuilder` and `MultiLayerFur`
4. **Testing**: Create comprehensive unit tests following existing patterns
5. **Documentation**: Update `__init__.py` exports

---

*Recommendations based on codebase analysis - March 2026*
