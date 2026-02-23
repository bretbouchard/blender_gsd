"""
Road Barrier Generator

Generates highway barriers and guardrails:
- Jersey barriers (concrete)
- Guardrails (metal)
- Cable barriers
- Crash cushions

Places barriers along road edges based on OSM data or manual placement.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any


class BarrierType(Enum):
    """Types of road barriers."""
    JERSEY_STANDARD = "jersey_standard"
    JERSEY_TALL = "jersey_tall"
    JERSEY_LOW = "jersey_low"
    GUARDRAIL_STANDARD = "guardrail_standard"
    GUARDRAIL_DOUBLE = "guardrail_double"
    CABLE_BARRIER = "cable"
    CRASH_CUSHION = "crash_cushion"


@dataclass
class BarrierConfig:
    """Configuration for barrier generation."""
    # Dimensions (meters)
    height: float = 0.81  # Standard Jersey barrier height
    base_width: float = 0.61
    top_width: float = 0.15

    # Segment
    segment_length: float = 3.0  # Standard precast length

    # Spacing
    gap_between_segments: float = 0.02  # Small gap for realism

    # Materials
    concrete_color: Tuple[float, float, float] = (0.45, 0.43, 0.4)
    concrete_roughness: float = 0.8
    metal_color: Tuple[float, float, float] = (0.7, 0.7, 0.7)
    metal_roughness: float = 0.3


# Standard barrier configurations
BARRIER_CONFIGS = {
    BarrierType.JERSEY_STANDARD: BarrierConfig(
        height=0.81,
        base_width=0.61,
        top_width=0.15,
        segment_length=3.0,
    ),
    BarrierType.JERSEY_TALL: BarrierConfig(
        height=1.07,
        base_width=0.76,
        top_width=0.20,
        segment_length=3.0,
    ),
    BarrierType.JERSEY_LOW: BarrierConfig(
        height=0.51,
        base_width=0.46,
        top_width=0.10,
        segment_length=3.0,
    ),
    BarrierType.GUARDRAIL_STANDARD: BarrierConfig(
        height=0.71,
        base_width=0.31,
        top_width=0.31,
        segment_length=3.8,
        metal_color=(0.6, 0.6, 0.65),
        metal_roughness=0.4,
    ),
}


class BarrierGenerator:
    """
    Generates road barrier geometry.

    Creates 3D barrier meshes that can be placed along road edges.
    """

    def __init__(self):
        """Initialize barrier generator."""
        self._material_cache: Dict[str, Any] = {}

    def create_jersey_barrier(
        self,
        config: Optional[BarrierConfig] = None,
        name: str = "Jersey_Barrier",
    ) -> Optional[Object]:
        """
        Create a single Jersey barrier segment.

        Args:
            config: Barrier configuration
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or BARRIER_CONFIGS[BarrierType.JERSEY_STANDARD]

        # Create mesh
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # Create bmesh for geometry
        bm = bmesh.new()

        # Jersey barrier profile (trapezoid with beveled base)
        h = config.height
        b = config.base_width / 2
        t = config.top_width / 2
        l = config.segment_length / 2

        # Vertices for the profile
        # Bottom corners (slightly wider at very bottom)
        v1 = bm.verts.new((-b, -l, 0))
        v2 = bm.verts.new((b, -l, 0))
        v3 = bm.verts.new((b, l, 0))
        v4 = bm.verts.new((-b, l, 0))

        # Mid-section (angled sides)
        v5 = bm.verts.new((-t, -l, h))
        v6 = bm.verts.new((t, -l, h))
        v7 = bm.verts.new((t, l, h))
        v8 = bm.verts.new((-t, l, h))

        bm.verts.ensure_lookup_table()

        # Create faces
        # Bottom
        bm.faces.new([v1, v2, v3, v4])

        # Top
        bm.faces.new([v5, v8, v7, v6])

        # Sides
        bm.faces.new([v1, v4, v8, v5])  # Left
        bm.faces.new([v2, v6, v7, v3])  # Right
        bm.faces.new([v1, v5, v6, v2])  # Front
        bm.faces.new([v4, v3, v7, v8])  # Back

        # Update mesh
        bm.to_mesh(mesh)
        bm.free()

        # Apply material
        mat = self._get_concrete_material(config)
        if mat:
            obj.data.materials.append(mat)

        return obj

    def create_guardrail(
        self,
        length: float = 3.8,
        name: str = "Guardrail",
    ) -> Optional[Object]:
        """
        Create a guardrail section.

        Args:
            length: Length of guardrail section
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create mesh
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Guardrail dimensions (W-beam profile)
        height = 0.71
        width = 0.31
        thickness = 0.003  # Sheet metal thickness
        post_height = 0.61
        post_width = 0.1

        # Create W-beam profile (simplified)
        # Main rail
        l = length / 2

        # Rail vertices (flat for simplicity)
        v1 = bm.verts.new((-width/2, -l, height - 0.15))
        v2 = bm.verts.new((width/2, -l, height - 0.15))
        v3 = bm.verts.new((width/2, l, height - 0.15))
        v4 = bm.verts.new((-width/2, l, height - 0.15))
        v5 = bm.verts.new((-width/2, -l, height))
        v6 = bm.verts.new((width/2, -l, height))
        v7 = bm.verts.new((width/2, l, height))
        v8 = bm.verts.new((-width/2, l, height))

        bm.verts.ensure_lookup_table()

        # Rail faces
        bm.faces.new([v1, v2, v3, v4])  # Bottom
        bm.faces.new([v5, v8, v7, v6])  # Top
        bm.faces.new([v1, v5, v6, v2])  # Front
        bm.faces.new([v4, v3, v7, v8])  # Back
        bm.faces.new([v1, v4, v8, v5])  # Left
        bm.faces.new([v2, v6, v7, v3])  # Right

        bm.to_mesh(mesh)
        bm.free()

        # Apply metal material
        mat = self._get_metal_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def place_barriers_along_road(
        self,
        road_points: List[Tuple[float, float, float]],
        offset: float,
        side: str = "right",
        barrier_type: BarrierType = BarrierType.JERSEY_STANDARD,
        collection: Optional[Collection] = None,
    ) -> List[Object]:
        """
        Place barriers along a road path.

        Args:
            road_points: Road center line points
            offset: Distance from road edge
            side: "left" or "right" side of road
            barrier_type: Type of barrier to place
            collection: Collection to add objects to

        Returns:
            List of created barrier objects
        """
        if not BLENDER_AVAILABLE or len(road_points) < 2:
            return []

        objects = []
        config = BARRIER_CONFIGS.get(barrier_type, BarrierConfig())

        side_mult = 1.0 if side == "right" else -1.0

        # Calculate barrier positions along road
        for i in range(len(road_points) - 1):
            p1 = Vector(road_points[i])
            p2 = Vector(road_points[i + 1])

            direction = (p2 - p1).normalized()
            perpendicular = Vector((-direction.y, direction.x, 0))

            # Barrier position
            barrier_pos = p1 + perpendicular * offset * side_mult

            # Create barrier
            if barrier_type in [BarrierType.JERSEY_STANDARD, BarrierType.JERSEY_TALL, BarrierType.JERSEY_LOW]:
                obj = self.create_jersey_barrier(config, f"Barrier_{i}")
            else:
                segment_length = (p2 - p1).length
                obj = self.create_guardrail(segment_length, f"Guardrail_{i}")

            if obj:
                # Position and rotate
                obj.location = barrier_pos

                # Rotate to align with road direction
                angle = math.atan2(direction.y, direction.x)
                obj.rotation_euler = (0, 0, angle)

                objects.append(obj)

                if collection:
                    collection.objects.link(obj)

        return objects

    def _get_concrete_material(self, config: BarrierConfig) -> Optional[Any]:
        """Get or create concrete material."""
        if not BLENDER_AVAILABLE:
            return None

        if "concrete_barrier" in self._material_cache:
            return self._material_cache["concrete_barrier"]

        mat = bpy.data.materials.new("Concrete_Barrier")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")

        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*config.concrete_color, 1.0)
            bsdf.inputs["Roughness"].default_value = config.concrete_roughness

        self._material_cache["concrete_barrier"] = mat
        return mat

    def _get_metal_material(self) -> Optional[Any]:
        """Get or create metal material."""
        if not BLENDER_AVAILABLE:
            return None

        if "metal_guardrail" in self._material_cache:
            return self._material_cache["metal_guardrail"]

        mat = bpy.data.materials.new("Metal_Guardrail")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")

        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.6, 0.6, 0.65, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.8
            bsdf.inputs["Roughness"].default_value = 0.4

        self._material_cache["metal_guardrail"] = mat
        return mat


def create_jersey_barrier(name: str = "Jersey_Barrier") -> Optional[Object]:
    """Convenience function to create a Jersey barrier."""
    generator = BarrierGenerator()
    return generator.create_jersey_barrier(name=name)


def create_guardrail(name: str = "Guardrail") -> Optional[Object]:
    """Convenience function to create a guardrail."""
    generator = BarrierGenerator()
    return generator.create_guardrail(name=name)


def place_barriers_along_road(
    road_points: List[Tuple[float, float, float]],
    offset: float,
    side: str = "right",
) -> List[Object]:
    """Convenience function to place barriers along a road."""
    generator = BarrierGenerator()
    return generator.place_barriers_along_road(road_points, offset, side)


__all__ = [
    "BarrierType",
    "BarrierConfig",
    "BARRIER_CONFIGS",
    "BarrierGenerator",
    "create_jersey_barrier",
    "create_guardrail",
    "place_barriers_along_road",
]
