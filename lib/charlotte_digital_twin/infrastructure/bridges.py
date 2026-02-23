"""
Bridge and Overpass Generator

Generates bridge structures:
- Support columns
- Bridge decks
- Abutments
- Overpass geometry
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


class BridgeType(Enum):
    """Types of bridge structures."""
    HIGHWAY_OVERPASS = "highway_overpass"
    PEDESTRIAN_BRIDGE = "pedestrian"
    RAIL_OVERPASS = "rail"
    INTERCHANGE = "interchange"


@dataclass
class BridgeSupportConfig:
    """Configuration for bridge support generation."""
    # Column dimensions
    column_width: float = 1.5
    column_depth: float = 1.5
    column_height: float = 10.0  # Will be adjusted based on bridge elevation

    # Spacing
    support_spacing: float = 20.0  # Meters between supports

    # Cap beam
    cap_beam_height: float = 1.0
    cap_beam_width: float = 2.5
    cap_beam_depth: float = 1.5

    # Materials
    concrete_color: Tuple[float, float, float] = (0.5, 0.48, 0.45)
    concrete_roughness: float = 0.75


class BridgeGenerator:
    """
    Generates bridge and overpass geometry.

    Creates support columns, cap beams, and bridge deck elements.
    """

    def __init__(self):
        """Initialize bridge generator."""
        self._material_cache: Dict[str, Any] = {}

    def create_support_column(
        self,
        height: float = 10.0,
        width: float = 1.5,
        depth: float = 1.5,
        name: str = "Bridge_Support",
    ) -> Optional[Object]:
        """
        Create a bridge support column.

        Args:
            height: Column height
            width: Column width
            depth: Column depth
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Simple rectangular column
        hw, hd = width / 2, depth / 2

        # Vertices
        v1 = bm.verts.new((-hw, -hd, 0))
        v2 = bm.verts.new((hw, -hd, 0))
        v3 = bm.verts.new((hw, hd, 0))
        v4 = bm.verts.new((-hw, hd, 0))
        v5 = bm.verts.new((-hw, -hd, height))
        v6 = bm.verts.new((hw, -hd, height))
        v7 = bm.verts.new((hw, hd, height))
        v8 = bm.verts.new((-hw, hd, height))

        bm.verts.ensure_lookup_table()

        # Faces
        bm.faces.new([v1, v2, v3, v4])  # Bottom
        bm.faces.new([v5, v8, v7, v6])  # Top
        bm.faces.new([v1, v5, v6, v2])  # Front
        bm.faces.new([v2, v6, v7, v3])  # Right
        bm.faces.new([v3, v7, v8, v4])  # Back
        bm.faces.new([v4, v8, v5, v1])  # Left

        bm.to_mesh(mesh)
        bm.free()

        # Apply material
        mat = self._get_concrete_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def create_cap_beam(
        self,
        length: float = 15.0,
        height: float = 1.0,
        width: float = 2.5,
        name: str = "Cap_Beam",
    ) -> Optional[Object]:
        """
        Create a bridge cap beam.

        Args:
            length: Beam length
            height: Beam height
            width: Beam width
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        hl, hw, hh = length / 2, width / 2, height / 2

        v1 = bm.verts.new((-hl, -hw, -hh))
        v2 = bm.verts.new((hl, -hw, -hh))
        v3 = bm.verts.new((hl, hw, -hh))
        v4 = bm.verts.new((-hl, hw, -hh))
        v5 = bm.verts.new((-hl, -hw, hh))
        v6 = bm.verts.new((hl, -hw, hh))
        v7 = bm.verts.new((hl, hw, hh))
        v8 = bm.verts.new((-hl, hw, hh))

        bm.verts.ensure_lookup_table()

        bm.faces.new([v1, v2, v3, v4])
        bm.faces.new([v5, v8, v7, v6])
        bm.faces.new([v1, v5, v6, v2])
        bm.faces.new([v2, v6, v7, v3])
        bm.faces.new([v3, v7, v8, v4])
        bm.faces.new([v4, v8, v5, v1])

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_concrete_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def generate_bridge_supports(
        self,
        bridge_points: List[Tuple[float, float, float]],
        bridge_height: float,
        support_spacing: float = 20.0,
        collection: Optional[Collection] = None,
    ) -> List[Object]:
        """
        Generate support columns along a bridge path.

        Args:
            bridge_points: Bridge center line points
            bridge_height: Height of bridge deck
            support_spacing: Distance between supports
            collection: Collection to add to

        Returns:
            List of created objects
        """
        if not BLENDER_AVAILABLE or len(bridge_points) < 2:
            return []

        objects = []

        # Calculate total length and place supports
        total_length = 0.0
        segments = []

        for i in range(len(bridge_points) - 1):
            p1 = Vector(bridge_points[i])
            p2 = Vector(bridge_points[i + 1])
            seg_length = (p2 - p1).length
            segments.append((p1, p2, seg_length))
            total_length += seg_length

        # Place supports at regular intervals
        current_distance = support_spacing / 2  # Start offset

        while current_distance < total_length - support_spacing / 2:
            # Find position along path
            accumulated = 0.0

            for p1, p2, seg_length in segments:
                if accumulated + seg_length >= current_distance:
                    # Interpolate position
                    t = (current_distance - accumulated) / seg_length
                    pos = p1.lerp(p2, t)

                    # Ground height (assume 0 for now, should use terrain)
                    ground_height = 0
                    column_height = pos.z - ground_height

                    if column_height > 0.5:  # Only create if elevated
                        # Create column
                        column = self.create_support_column(
                            height=column_height,
                            name=f"Bridge_Support_{len(objects)}",
                        )
                        if column:
                            column.location = (pos.x, pos.y, ground_height)
                            objects.append(column)

                            if collection:
                                collection.objects.link(column)

                            # Create cap beam on top
                            direction = (p2 - p1).normalized()
                            angle = math.atan2(direction.y, direction.x)
                            cap = self.create_cap_beam(name=f"Cap_Beam_{len(objects)}")
                            if cap:
                                cap.location = (pos.x, pos.y, pos.z - 0.5)
                                cap.rotation_euler = (0, 0, angle)
                                objects.append(cap)

                                if collection:
                                    collection.objects.link(cap)

                    break

                accumulated += seg_length

            current_distance += support_spacing

        return objects

    def _get_concrete_material(self) -> Optional[Any]:
        """Get or create concrete material."""
        if not BLENDER_AVAILABLE:
            return None

        if "bridge_concrete" in self._material_cache:
            return self._material_cache["bridge_concrete"]

        mat = bpy.data.materials.new("Bridge_Concrete")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.5, 0.48, 0.45, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.75

        self._material_cache["bridge_concrete"] = mat
        return mat


def create_support_column(height: float = 10.0) -> Optional[Object]:
    """Convenience function to create a support column."""
    generator = BridgeGenerator()
    return generator.create_support_column(height=height)


def generate_bridge_geometry(
    bridge_points: List[Tuple[float, float, float]],
    height: float,
) -> List[Object]:
    """Convenience function to generate bridge supports."""
    generator = BridgeGenerator()
    return generator.generate_bridge_supports(bridge_points, height)


__all__ = [
    "BridgeType",
    "BridgeSupportConfig",
    "BridgeGenerator",
    "create_support_column",
    "generate_bridge_geometry",
]
