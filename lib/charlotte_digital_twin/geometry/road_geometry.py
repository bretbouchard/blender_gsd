"""
Road Geometry Generator for Charlotte Digital Twin

Generates Blender geometry (curves and meshes) from road segments.

Usage:
    from lib.charlotte_digital_twin.geometry import RoadGeometryGenerator, RoadSegment

    generator = RoadGeometryGenerator()

    # Create curve from segment
    curve = generator.create_curve(segment)

    # Create mesh with width
    mesh = generator.create_road_mesh(segment)

    # Create all roads at once
    objects = generator.create_all_roads(segments)
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    GeometryConfig,
    RoadSegment,
    RoadType,
    WorldCoordinate,
    DetailLevel,
)
from .coordinates import CoordinateTransformer


class RoadGeometryGenerator:
    """
    Generates Blender geometry for road networks.

    Features:
    - Creates curves from road segments
    - Generates road meshes with proper width
    - Handles intersections
    - Applies materials based on road type

    Note: This module uses bpy conditionally - it will work without
    Blender for testing but actual geometry requires Blender context.
    """

    def __init__(
        self,
        config: Optional[GeometryConfig] = None,
        transformer: Optional[CoordinateTransformer] = None,
    ):
        """
        Initialize geometry generator.

        Args:
            config: Geometry configuration
            transformer: Coordinate transformer
        """
        self.config = config or GeometryConfig()
        self.transformer = transformer or CoordinateTransformer(self.config)

        # Check if Blender is available
        self._blender_available = False
        self._bpy = None
        try:
            import bpy
            self._bpy = bpy
            self._blender_available = True
        except ImportError:
            pass

    def create_curve(
        self,
        segment: RoadSegment,
        name: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Create a Blender curve from a road segment.

        Args:
            segment: RoadSegment to convert
            name: Optional name for the curve object

        Returns:
            Blender curve object or None if Blender unavailable
        """
        if not self._blender_available:
            return None

        if len(segment.coordinates) < 2:
            return None

        # Generate name
        if name is None:
            name = segment.name if segment.name else f"Road_{segment.osm_id}"

        # Create curve data
        curve_data = self._bpy.data.curves.new(name=f"{name}_curve", type="CURVE")
        curve_data.dimensions = "3D"
        curve_data.resolution_u = 2  # Low resolution for roads

        # Create spline
        spline = curve_data.splines.new("POLY")
        spline.points.add(len(segment.coordinates) - 1)

        # Set points
        for i, coord in enumerate(segment.coordinates):
            spline.points[i].co = (coord.x, coord.y, coord.z, 1.0)

        # Create object
        curve_obj = self._bpy.data.objects.new(name, curve_data)

        # Link to scene
        self._bpy.context.collection.objects.link(curve_obj)

        # Store metadata
        curve_obj["osm_id"] = segment.osm_id
        curve_obj["road_type"] = segment.road_type.value
        curve_obj["road_width"] = segment.width
        curve_obj["road_name"] = segment.name

        return curve_obj

    def create_road_mesh(
        self,
        segment: RoadSegment,
        name: Optional[str] = None,
        width_override: Optional[float] = None,
        subdivisions: int = 1,
    ) -> Optional[Any]:
        """
        Create a Blender mesh from a road segment.

        Generates a flat road surface with proper width.

        Args:
            segment: RoadSegment to convert
            name: Optional name for the mesh object
            width_override: Override road width
            subdivisions: Subdivisions for curves (1 = linear)

        Returns:
            Blender mesh object or None if Blender unavailable
        """
        if not self._blender_available:
            return None

        if len(segment.coordinates) < 2:
            return None

        # Generate name
        if name is None:
            name = segment.name if segment.name else f"Road_{segment.osm_id}"

        width = width_override or segment.width

        # Generate mesh vertices
        vertices = []
        faces = []
        uvs = []

        # Build road mesh
        for i in range(len(segment.coordinates) - 1):
            p1 = segment.coordinates[i]
            p2 = segment.coordinates[i + 1]

            # Calculate direction vector
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            length = math.sqrt(dx * dx + dy * dy)

            if length < 0.001:
                continue

            # Normalize and get perpendicular
            dx /= length
            dy /= length

            # Perpendicular vector (for road width)
            px = -dy
            py = dx

            # Half width
            hw = width / 2.0

            # Create quad vertices
            base_idx = len(vertices)

            # Four corners of road segment
            vertices.append((p1.x + px * hw, p1.y + py * hw, p1.z))
            vertices.append((p1.x - px * hw, p1.y - py * hw, p1.z))
            vertices.append((p2.x - px * hw, p2.y - py * hw, p2.z))
            vertices.append((p2.x + px * hw, p2.y + py * hw, p2.z))

            # Face indices
            faces.append((base_idx, base_idx + 1, base_idx + 2, base_idx + 3))

            # UV coordinates (along road length)
            u_start = i / (len(segment.coordinates) - 1)
            u_end = (i + 1) / (len(segment.coordinates) - 1)
            uvs.extend([
                (u_start, 0.0),
                (u_start, 1.0),
                (u_end, 1.0),
                (u_end, 0.0),
            ])

        if not vertices:
            return None

        # Create mesh
        mesh = self._bpy.data.meshes.new(name=f"{name}_mesh")
        mesh.from_pydata(vertices, [], faces)

        # Create UV layer
        if uvs:
            uv_layer = mesh.uv_layers.new(name="UVMap")
            for i, loop in enumerate(mesh.loops):
                uv_layer.data[loop.index].uv = uvs[i]

        # Create object
        mesh_obj = self._bpy.data.objects.new(name, mesh)

        # Link to scene
        self._bpy.context.collection.objects.link(mesh_obj)

        # Store metadata
        mesh_obj["osm_id"] = segment.osm_id
        mesh_obj["road_type"] = segment.road_type.value
        mesh_obj["road_width"] = segment.width
        mesh_obj["road_name"] = segment.name
        mesh_obj["road_lanes"] = segment.lanes
        mesh_obj["road_surface"] = segment.surface
        mesh_obj["is_bridge"] = segment.is_bridge
        mesh_obj["is_tunnel"] = segment.is_tunnel

        return mesh_obj

    def create_all_curves(
        self,
        segments: List[RoadSegment],
        collection_name: str = "Roads_Curves",
    ) -> List[Any]:
        """
        Create Blender curves for all road segments.

        Args:
            segments: List of RoadSegment objects
            collection_name: Name for the collection

        Returns:
            List of curve objects
        """
        if not self._blender_available:
            return []

        curves = []

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        for segment in segments:
            curve = self.create_curve(segment)
            if curve:
                # Move to collection
                self._bpy.context.collection.objects.unlink(curve)
                collection.objects.link(curve)
                curves.append(curve)

        return curves

    def create_all_meshes(
        self,
        segments: List[RoadSegment],
        collection_name: str = "Roads_Meshes",
    ) -> List[Any]:
        """
        Create Blender meshes for all road segments.

        Args:
            segments: List of RoadSegment objects
            collection_name: Name for the collection

        Returns:
            List of mesh objects
        """
        if not self._blender_available:
            return []

        meshes = []

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        for segment in segments:
            mesh = self.create_road_mesh(segment)
            if mesh:
                # Move to collection
                self._bpy.context.collection.objects.unlink(mesh)
                collection.objects.link(mesh)
                meshes.append(mesh)

        return meshes

    def create_intersection_marker(
        self,
        position: WorldCoordinate,
        radius: float = 2.0,
        name: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Create a marker at an intersection point.

        Args:
            position: World coordinate for intersection
            radius: Radius of marker
            name: Optional name

        Returns:
            Blender mesh object or None
        """
        if not self._blender_available:
            return None

        name = name or f"Intersection_{position.x:.0f}_{position.y:.0f}"

        # Create a simple circle marker
        bpy = self._bpy

        # Create mesh
        mesh = bpy.data.meshes.new(f"{name}_mesh")

        # Create circle vertices
        segments = 16
        vertices = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position.x + radius * math.cos(angle)
            y = position.y + radius * math.sin(angle)
            vertices.append((x, y, position.z))

        # Add center
        vertices.append((position.x, position.y, position.z))
        center_idx = len(vertices) - 1

        # Create faces (triangles from center to edge)
        faces = []
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append((center_idx, i, next_i))

        mesh.from_pydata(vertices, [], faces)

        # Create object
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)

        return obj

    def get_material_for_road_type(self, road_type: RoadType) -> str:
        """
        Get recommended material name for road type.

        Args:
            road_type: Type of road

        Returns:
            Material name string
        """
        material_map = {
            RoadType.MOTORWAY: "asphalt_highway",
            RoadType.MOTORWAY_LINK: "asphalt_highway",
            RoadType.TRUNK: "asphalt_main",
            RoadType.TRUNK_LINK: "asphalt_main",
            RoadType.PRIMARY: "asphalt_main",
            RoadType.PRIMARY_LINK: "asphalt_main",
            RoadType.SECONDARY: "asphalt_secondary",
            RoadType.SECONDARY_LINK: "asphalt_secondary",
            RoadType.TERTIARY: "asphalt_local",
            RoadType.TERTIARY_LINK: "asphalt_local",
            RoadType.RESIDENTIAL: "asphalt_residential",
            RoadType.SERVICE: "concrete_service",
            RoadType.UNCLASSIFIED: "gravel_road",
            RoadType.PEDESTRIAN: "concrete_pedestrian",
            RoadType.FOOTWAY: "concrete_sidewalk",
            RoadType.CYCLEWAY: "asphalt_cycle",
            RoadType.PATH: "dirt_path",
            RoadType.TRACK: "dirt_track",
            RoadType.STEPS: "concrete_steps",
        }
        return material_map.get(road_type, "asphalt_default")


__all__ = ["RoadGeometryGenerator"]
