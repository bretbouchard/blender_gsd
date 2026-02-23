"""
POI Geometry Generator for Charlotte Digital Twin

Generates Blender geometry for Points of Interest (markers, labels, icons).

Usage:
    from lib.charlotte_digital_twin.geometry import POIGeometryGenerator, POIMarker

    generator = POIGeometryGenerator()

    # Create POI marker
    marker = generator.create_poi_marker(poi)

    # Create all POIs at once
    markers = generator.create_all_pois(pois)
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    POIMarker,
    POICategory,
    GeometryConfig,
    WorldCoordinate,
    DetailLevel,
)
from .coordinates import CoordinateTransformer


class POIGeometryGenerator:
    """
    Generates Blender geometry for POI markers.

    Features:
    - Creates marker geometry (cylinders, cones, spheres)
    - Category-based styling
    - Label support
    - LOD support
    """

    # Marker sizes by category (meters)
    MARKER_SIZES = {
        POICategory.RESTAURANT: 1.0,
        POICategory.CAFE: 0.8,
        POICategory.BAR: 0.8,
        POICategory.SHOP: 0.6,
        POICategory.HOTEL: 1.5,
        POICategory.ATTRACTION: 2.0,
        POICategory.MUSEUM: 1.5,
        POICategory.PARK: 1.2,
        POICategory.SCHOOL: 1.0,
        POICategory.HOSPITAL: 1.5,
        POICategory.POLICE: 1.0,
        POICategory.FIRE_STATION: 1.0,
        POICategory.PUBLIC_TRANSPORT: 0.8,
        POICategory.PARKING: 0.6,
        POICategory.FUEL: 0.8,
        POICategory.BANK: 0.8,
        POICategory.POST_OFFICE: 0.6,
        POICategory.LIBRARY: 1.0,
        POICategory.PLACE_OF_WORSHIP: 1.5,
        POICategory.SPORTS: 1.2,
        POICategory.ENTERTAINMENT: 1.0,
        POICategory.OFFICE: 0.8,
        POICategory.OTHER: 0.5,
    }

    # Marker colors by category (RGBA)
    MARKER_COLORS = {
        POICategory.RESTAURANT: (0.9, 0.3, 0.2, 1.0),      # Red
        POICategory.CAFE: (0.6, 0.4, 0.2, 1.0),           # Brown
        POICategory.BAR: (0.5, 0.2, 0.5, 1.0),            # Purple
        POICategory.SHOP: (0.2, 0.6, 0.8, 1.0),           # Blue
        POICategory.HOTEL: (0.9, 0.7, 0.2, 1.0),          # Gold
        POICategory.ATTRACTION: (0.9, 0.5, 0.1, 1.0),     # Orange
        POICategory.MUSEUM: (0.6, 0.5, 0.4, 1.0),         # Tan
        POICategory.PARK: (0.3, 0.7, 0.3, 1.0),           # Green
        POICategory.SCHOOL: (0.3, 0.5, 0.8, 1.0),         # Light blue
        POICategory.HOSPITAL: (0.9, 0.2, 0.3, 1.0),       # Red
        POICategory.POLICE: (0.2, 0.3, 0.7, 1.0),         # Dark blue
        POICategory.FIRE_STATION: (0.9, 0.3, 0.1, 1.0),   # Orange-red
        POICategory.PUBLIC_TRANSPORT: (0.3, 0.6, 0.4, 1.0), # Teal
        POICategory.PARKING: (0.5, 0.5, 0.5, 1.0),        # Gray
        POICategory.FUEL: (0.8, 0.5, 0.2, 1.0),           # Amber
        POICategory.BANK: (0.2, 0.5, 0.3, 1.0),           # Dark green
        POICategory.POST_OFFICE: (0.8, 0.3, 0.3, 1.0),    # Light red
        POICategory.LIBRARY: (0.5, 0.4, 0.6, 1.0),        # Lavender
        POICategory.PLACE_OF_WORSHIP: (0.7, 0.7, 0.7, 1.0), # Light gray
        POICategory.SPORTS: (0.4, 0.7, 0.4, 1.0),         # Light green
        POICategory.ENTERTAINMENT: (0.7, 0.3, 0.6, 1.0),  # Pink
        POICategory.OFFICE: (0.6, 0.6, 0.6, 1.0),         # Gray
        POICategory.OTHER: (0.5, 0.5, 0.5, 1.0),          # Gray
    }

    def __init__(
        self,
        config: Optional[GeometryConfig] = None,
        transformer: Optional[CoordinateTransformer] = None,
    ):
        """
        Initialize POI geometry generator.

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

    def create_poi_marker(
        self,
        poi: POIMarker,
        name: Optional[str] = None,
        style: str = "cone",
    ) -> Optional[Any]:
        """
        Create a Blender mesh for a POI marker.

        Args:
            poi: POIMarker to convert
            name: Optional name for the mesh object
            style: Marker style ("cone", "cylinder", "sphere", "pin")

        Returns:
            Blender mesh object or None if Blender unavailable
        """
        if not self._blender_available:
            return None

        # Generate name
        if name is None:
            name = poi.name if poi.name else f"POI_{poi.osm_id}"

        # Get marker size
        size = self.MARKER_SIZES.get(poi.category, 0.5)

        # Create geometry based on style
        if style == "cone":
            obj = self._create_cone_marker(poi.position, size, name)
        elif style == "cylinder":
            obj = self._create_cylinder_marker(poi.position, size, name)
        elif style == "sphere":
            obj = self._create_sphere_marker(poi.position, size, name)
        elif style == "pin":
            obj = self._create_pin_marker(poi.position, size, name)
        else:
            obj = self._create_cone_marker(poi.position, size, name)

        if obj:
            # Store metadata
            obj["osm_id"] = poi.osm_id
            obj["poi_name"] = poi.name
            obj["poi_category"] = poi.category.value
            obj["poi_importance"] = poi.importance

            # Copy tags
            for key, value in poi.tags.items():
                obj[f"osm_{key}"] = value

        return obj

    def _create_cone_marker(
        self,
        position: WorldCoordinate,
        size: float,
        name: str,
    ) -> Optional[Any]:
        """Create cone-shaped marker."""
        vertices = []
        faces = []
        segments = 8

        # Base circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position.x + size * math.cos(angle)
            y = position.y + size * math.sin(angle)
            vertices.append((x, y, position.z))

        # Center of base
        center_idx = len(vertices)
        vertices.append((position.x, position.y, position.z))

        # Apex
        apex_idx = len(vertices)
        vertices.append((position.x, position.y, position.z + size * 2))

        # Base face
        base_face = list(range(segments))
        base_face.append(base_face[0])  # Close the loop
        faces.append(tuple(base_face))

        # Side faces
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append((i, next_i, apex_idx))

        return self._create_mesh_object(name, vertices, faces)

    def _create_cylinder_marker(
        self,
        position: WorldCoordinate,
        size: float,
        name: str,
    ) -> Optional[Any]:
        """Create cylinder-shaped marker."""
        vertices = []
        faces = []
        segments = 8
        height = size * 1.5

        # Bottom circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position.x + size * 0.5 * math.cos(angle)
            y = position.y + size * 0.5 * math.sin(angle)
            vertices.append((x, y, position.z))

        # Top circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position.x + size * 0.5 * math.cos(angle)
            y = position.y + size * 0.5 * math.sin(angle)
            vertices.append((x, y, position.z + height))

        # Bottom face
        faces.append(tuple(range(segments)))

        # Top face
        faces.append(tuple(range(segments, 2 * segments)))

        # Side faces
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append((
                i,
                next_i,
                segments + next_i,
                segments + i,
            ))

        return self._create_mesh_object(name, vertices, faces)

    def _create_sphere_marker(
        self,
        position: WorldCoordinate,
        size: float,
        name: str,
    ) -> Optional[Any]:
        """Create sphere-shaped marker."""
        vertices = []
        faces = []
        segments = 8
        rings = 4
        radius = size * 0.6

        for ring in range(rings + 1):
            phi = math.pi * ring / rings
            for seg in range(segments):
                theta = 2 * math.pi * seg / segments
                x = position.x + radius * math.sin(phi) * math.cos(theta)
                y = position.y + radius * math.sin(phi) * math.sin(theta)
                z = position.z + radius * math.cos(phi) + size  # Lifted up
                vertices.append((x, y, z))

        # Generate faces
        for ring in range(rings):
            for seg in range(segments):
                next_seg = (seg + 1) % segments
                i1 = ring * segments + seg
                i2 = ring * segments + next_seg
                i3 = (ring + 1) * segments + next_seg
                i4 = (ring + 1) * segments + seg
                faces.append((i1, i2, i3, i4))

        return self._create_mesh_object(name, vertices, faces)

    def _create_pin_marker(
        self,
        position: WorldCoordinate,
        size: float,
        name: str,
    ) -> Optional[Any]:
        """Create map pin-shaped marker."""
        vertices = []
        faces = []
        segments = 8

        # Pin head (hemisphere approximation)
        head_radius = size * 0.5
        head_height = size * 1.5

        # Top of head
        vertices.append((position.x, position.y, position.z + head_height))
        top_idx = 0

        # Head ring
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position.x + head_radius * math.cos(angle)
            y = position.y + head_radius * math.sin(angle)
            vertices.append((x, y, position.z + head_height - head_radius * 0.5))

        # Head faces
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append((top_idx, i + 1, next_i + 1))

        # Pin point
        point_idx = len(vertices)
        vertices.append((position.x, position.y, position.z))

        # Point faces
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append((i + 1, point_idx, next_i + 1))

        return self._create_mesh_object(name, vertices, faces)

    def _create_mesh_object(
        self,
        name: str,
        vertices: List[Tuple[float, float, float]],
        faces: List[Tuple[int, ...]],
    ) -> Optional[Any]:
        """Create a Blender mesh object."""
        if not self._blender_available:
            return None

        # Create mesh
        mesh = self._bpy.data.meshes.new(name=f"{name}_mesh")
        mesh.from_pydata(vertices, [], faces)

        # Create object
        obj = self._bpy.data.objects.new(name, mesh)
        self._bpy.context.collection.objects.link(obj)

        return obj

    def create_all_pois(
        self,
        pois: List[POIMarker],
        collection_name: str = "POIs",
        style: str = "cone",
    ) -> List[Any]:
        """
        Create Blender meshes for all POI markers.

        Args:
            pois: List of POIMarker objects
            collection_name: Name for the collection
            style: Default marker style

        Returns:
            List of mesh objects
        """
        if not self._blender_available:
            return []

        markers = []

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        for poi in pois:
            marker = self.create_poi_marker(poi, style=style)
            if marker:
                # Move to collection
                self._bpy.context.collection.objects.unlink(marker)
                collection.objects.link(marker)
                markers.append(marker)

        return markers

    def get_marker_color(
        self,
        category: POICategory,
    ) -> Tuple[float, float, float, float]:
        """
        Get marker color for category.

        Args:
            category: POI category

        Returns:
            RGBA color tuple
        """
        return self.MARKER_COLORS.get(category, (0.5, 0.5, 0.5, 1.0))

    def get_marker_size(
        self,
        category: POICategory,
    ) -> float:
        """
        Get marker size for category.

        Args:
            category: POI category

        Returns:
            Size in meters
        """
        return self.MARKER_SIZES.get(category, 0.5)

    def filter_by_category(
        self,
        pois: List[POIMarker],
        categories: List[POICategory],
    ) -> List[POIMarker]:
        """
        Filter POIs by category.

        Args:
            pois: List of POIs
            categories: Categories to include

        Returns:
            Filtered list
        """
        return [p for p in pois if p.category in categories]

    def filter_by_importance(
        self,
        pois: List[POIMarker],
        min_importance: float = 0.0,
        max_importance: float = 1.0,
    ) -> List[POIMarker]:
        """
        Filter POIs by importance rating.

        Args:
            pois: List of POIs
            min_importance: Minimum importance
            max_importance: Maximum importance

        Returns:
            Filtered list
        """
        return [
            p for p in pois
            if min_importance <= p.importance <= max_importance
        ]


__all__ = ["POIGeometryGenerator"]
