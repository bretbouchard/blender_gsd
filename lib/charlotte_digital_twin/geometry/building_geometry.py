"""
Building Geometry Generator for Charlotte Digital Twin

Generates Blender geometry (meshes) from building footprints.

Usage:
    from lib.charlotte_digital_twin.geometry import BuildingGeometryGenerator, BuildingFootprint

    generator = BuildingGeometryGenerator()

    # Create building from footprint
    building = generator.create_building(footprint)

    # Create all buildings at once
    buildings = generator.create_all_buildings(footprints)
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    BuildingFootprint,
    BuildingType,
    GeometryConfig,
    WorldCoordinate,
    DetailLevel,
)
from .coordinates import CoordinateTransformer
from .scale import CHARLOTTE_BUILDING_HEIGHTS


class BuildingGeometryGenerator:
    """
    Generates Blender geometry for buildings.

    Features:
    - Creates extruded building meshes from footprints
    - Handles height data from OSM
    - Applies materials based on building type
    - LOD support (detail levels)
    """

    # Default heights by building type (meters)
    DEFAULT_HEIGHTS = {
        BuildingType.APARTMENTS: 15.0,
        BuildingType.COMMERCIAL: 12.0,
        BuildingType.HOUSE: 8.0,
        BuildingType.RETAIL: 6.0,
        BuildingType.OFFICE: 20.0,
        BuildingType.HOTEL: 25.0,
        BuildingType.SCHOOL: 10.0,
        BuildingType.HOSPITAL: 15.0,
        BuildingType.CHURCH: 15.0,
        BuildingType.INDUSTRIAL: 10.0,
        BuildingType.WAREHOUSE: 8.0,
        BuildingType.PARKING: 6.0,
        BuildingType.STADIUM: 40.0,
        BuildingType.CIVIC: 12.0,
        BuildingType.GOVERNMENT: 15.0,
        BuildingType.UNIVERSITY: 15.0,
        BuildingType.COLLEGE: 12.0,
    }

    def __init__(
        self,
        config: Optional[GeometryConfig] = None,
        transformer: Optional[CoordinateTransformer] = None,
    ):
        """
        Initialize building geometry generator.

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

    def create_building(
        self,
        footprint: BuildingFootprint,
        name: Optional[str] = None,
        detail_level: Optional[DetailLevel] = None,
    ) -> Optional[Any]:
        """
        Create a Blender mesh from a building footprint.

        Args:
            footprint: BuildingFootprint to convert
            name: Optional name for the mesh object
            detail_level: Override detail level

        Returns:
            Blender mesh object or None if Blender unavailable
        """
        if not self._blender_available:
            return None

        if len(footprint.coordinates) < 3:
            return None

        # Generate name
        if name is None:
            name = footprint.name if footprint.name else f"Building_{footprint.osm_id}"

        detail = detail_level or self.config.detail_level

        # Determine height
        height = self._get_building_height(footprint)

        # Create mesh based on detail level
        if detail == DetailLevel.MINIMAL:
            return self._create_minimal_building(footprint, name, height)
        elif detail == DetailLevel.STANDARD:
            return self._create_standard_building(footprint, name, height)
        elif detail == DetailLevel.HIGH:
            return self._create_high_detail_building(footprint, name, height)
        else:  # ULTRA
            return self._create_ultra_detail_building(footprint, name, height)

    def _get_building_height(self, footprint: BuildingFootprint) -> float:
        """Determine building height from data or defaults."""
        if footprint.height and footprint.height > 0:
            return footprint.height

        # Check if it's a known Charlotte building
        if footprint.name:
            for landmark, height in CHARLOTTE_BUILDING_HEIGHTS.items():
                if landmark.replace("_", " ").lower() in footprint.name.lower():
                    return height

        # Use type default
        return self.DEFAULT_HEIGHTS.get(footprint.building_type, self.config.default_building_height)

    def _create_minimal_building(
        self,
        footprint: BuildingFootprint,
        name: str,
        height: float,
    ) -> Optional[Any]:
        """Create minimal detail building (simple box)."""
        return self._create_box_building(footprint, name, height)

    def _create_standard_building(
        self,
        footprint: BuildingFootprint,
        name: str,
        height: float,
    ) -> Optional[Any]:
        """Create standard detail building (extruded footprint)."""
        return self._create_extruded_building(footprint, name, height)

    def _create_high_detail_building(
        self,
        footprint: BuildingFootprint,
        name: str,
        height: float,
    ) -> Optional[Any]:
        """Create high detail building (with roof form)."""
        building = self._create_extruded_building(footprint, name, height)
        if building:
            # Add roof shape based on building type
            self._add_roof_detail(building, footprint, height)
        return building

    def _create_ultra_detail_building(
        self,
        footprint: BuildingFootprint,
        name: str,
        height: float,
    ) -> Optional[Any]:
        """Create ultra detail building (with windows, details)."""
        building = self._create_high_detail_building(footprint, name, height)
        if building:
            # Store additional metadata for later detail pass
            building["detail_level"] = "ultra"
            building["needs_windows"] = True
        return building

    def _create_box_building(
        self,
        footprint: BuildingFootprint,
        name: str,
        height: float,
    ) -> Optional[Any]:
        """Create simple bounding box building."""
        # Get bounding box
        min_x = min(c.x for c in footprint.coordinates)
        max_x = max(c.x for c in footprint.coordinates)
        min_y = min(c.y for c in footprint.coordinates)
        max_y = max(c.y for c in footprint.coordinates)
        z = footprint.coordinates[0].z

        vertices = [
            (min_x, min_y, z),  # Bottom
            (max_x, min_y, z),
            (max_x, max_y, z),
            (min_x, max_y, z),
            (min_x, min_y, z + height),  # Top
            (max_x, min_y, z + height),
            (max_x, max_y, z + height),
            (min_x, max_y, z + height),
        ]

        faces = [
            (0, 1, 2, 3),  # Bottom
            (4, 7, 6, 5),  # Top
            (0, 4, 5, 1),  # Front
            (1, 5, 6, 2),  # Right
            (2, 6, 7, 3),  # Back
            (3, 7, 4, 0),  # Left
        ]

        return self._create_mesh_object(name, vertices, faces, footprint)

    def _create_extruded_building(
        self,
        footprint: BuildingFootprint,
        name: str,
        height: float,
    ) -> Optional[Any]:
        """Create building by extruding footprint polygon."""
        coords = footprint.coordinates
        n = len(coords)

        if n < 3:
            return None

        vertices = []
        faces = []

        z_base = coords[0].z

        # Bottom vertices
        for c in coords:
            vertices.append((c.x, c.y, z_base))

        # Top vertices
        z_top = z_base + height
        for c in coords:
            vertices.append((c.x, c.y, z_top))

        # Bottom face (need to ensure correct winding)
        bottom_face = tuple(range(n))
        # Reverse for bottom face
        faces.append(tuple(reversed(bottom_face)))

        # Top face
        faces.append(tuple(range(n, 2 * n)))

        # Side faces
        for i in range(n):
            next_i = (i + 1) % n
            faces.append((
                i,
                next_i,
                n + next_i,
                n + i,
            ))

        return self._create_mesh_object(name, vertices, faces, footprint)

    def _add_roof_detail(
        self,
        building_obj: Any,
        footprint: BuildingFootprint,
        height: float,
    ) -> None:
        """Add roof detail to building."""
        # Store roof type metadata for materials
        building_obj["roof_type"] = self._get_roof_type(footprint)
        building_obj["roof_height"] = height

    def _get_roof_type(self, footprint: BuildingFootprint) -> str:
        """Determine roof type from building type and tags."""
        # Check tags
        roof_shape = footprint.tags.get("roof:shape", "")
        if roof_shape:
            return roof_shape

        # Infer from building type
        if footprint.building_type == BuildingType.CHURCH:
            return "spire"
        elif footprint.building_type in [BuildingType.HOUSE, BuildingType.APARTMENTS]:
            return "gabled"
        elif footprint.building_type in [BuildingType.COMMERCIAL, BuildingType.OFFICE, BuildingType.RETAIL]:
            return "flat"
        else:
            return "flat"

    def _create_mesh_object(
        self,
        name: str,
        vertices: List[Tuple[float, float, float]],
        faces: List[Tuple[int, ...]],
        footprint: BuildingFootprint,
    ) -> Optional[Any]:
        """Create a Blender mesh object."""
        if not self._blender_available:
            return None

        # Create mesh
        mesh = self._bpy.data.meshes.new(name=f"{name}_mesh")
        mesh.from_pydata(vertices, [], faces)

        # Recalculate normals
        mesh.update()

        # Create object
        obj = self._bpy.data.objects.new(name, mesh)
        self._bpy.context.collection.objects.link(obj)

        # Store metadata
        obj["osm_id"] = footprint.osm_id
        obj["building_type"] = footprint.building_type.value
        obj["building_name"] = footprint.name
        obj["building_height"] = self._get_building_height(footprint)
        obj["building_levels"] = footprint.levels

        # Copy all tags
        for key, value in footprint.tags.items():
            obj[f"osm_{key}"] = value

        return obj

    def create_all_buildings(
        self,
        footprints: List[BuildingFootprint],
        collection_name: str = "Buildings",
    ) -> List[Any]:
        """
        Create Blender meshes for all building footprints.

        Args:
            footprints: List of BuildingFootprint objects
            collection_name: Name for the collection

        Returns:
            List of mesh objects
        """
        if not self._blender_available:
            return []

        buildings = []

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        for footprint in footprints:
            building = self.create_building(footprint)
            if building:
                # Move to collection
                self._bpy.context.collection.objects.unlink(building)
                collection.objects.link(building)
                buildings.append(building)

        return buildings

    def get_material_for_building_type(
        self,
        building_type: BuildingType,
    ) -> str:
        """
        Get recommended material name for building type.

        Args:
            building_type: Type of building

        Returns:
            Material name string
        """
        material_map = {
            BuildingType.APARTMENTS: "concrete_residential",
            BuildingType.COMMERCIAL: "glass_commercial",
            BuildingType.HOUSE: "brick_residential",
            BuildingType.RETAIL: "glass_retail",
            BuildingType.OFFICE: "glass_office",
            BuildingType.HOTEL: "glass_hotel",
            BuildingType.SCHOOL: "brick_institutional",
            BuildingType.HOSPITAL: "concrete_institutional",
            BuildingType.CHURCH: "stone_historical",
            BuildingType.INDUSTRIAL: "metal_industrial",
            BuildingType.WAREHOUSE: "metal_warehouse",
            BuildingType.PARKING: "concrete_parking",
            BuildingType.STADIUM: "concrete_stadium",
            BuildingType.CIVIC: "stone_civic",
            BuildingType.GOVERNMENT: "stone_government",
            BuildingType.UNIVERSITY: "brick_academic",
            BuildingType.COLLEGE: "brick_academic",
        }
        return material_map.get(building_type, "concrete_default")

    def estimate_levels(self, height: float) -> int:
        """
        Estimate number of levels from building height.

        Args:
            height: Building height in meters

        Returns:
            Estimated number of levels
        """
        # Average floor height is ~3.5m
        return max(1, int(height / 3.5))

    def filter_by_height(
        self,
        footprints: List[BuildingFootprint],
        min_height: float,
        max_height: float,
    ) -> List[BuildingFootprint]:
        """
        Filter building footprints by height range.

        Args:
            footprints: List of footprints
            min_height: Minimum height
            max_height: Maximum height

        Returns:
            Filtered list
        """
        filtered = []
        for fp in footprints:
            height = self._get_building_height(fp)
            if min_height <= height <= max_height:
                filtered.append(fp)
        return filtered

    def get_tall_buildings(
        self,
        footprints: List[BuildingFootprint],
        threshold: float = 50.0,
    ) -> List[BuildingFootprint]:
        """
        Get buildings above a height threshold.

        Args:
            footprints: List of footprints
            threshold: Height threshold in meters

        Returns:
            List of tall buildings
        """
        return self.filter_by_height(footprints, threshold, 1000.0)


__all__ = ["BuildingGeometryGenerator"]
