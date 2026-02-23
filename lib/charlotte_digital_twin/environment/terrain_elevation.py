"""
Terrain Elevation System

Handles terrain elevation data:
- DEM (Digital Elevation Model) loading
- Procedural terrain generation
- Height map application
- Road profiling

Supports integration with real elevation data for Charlotte area.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math
import random
import os

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection, Image
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any
    Image = Any


class TerrainSourceType(Enum):
    """Source of terrain data."""
    DEM_FILE = "dem"          # From DEM file (GeoTIFF, etc.)
    HEIGHT_MAP = "heightmap"  # From grayscale image
    PROCEDURAL = "procedural" # Generated procedurally
    FLAT = "flat"             # No elevation


@dataclass
class TerrainConfig:
    """Configuration for terrain generation."""
    # Dimensions
    size_x: float = 1000.0  # Meters
    size_y: float = 1000.0
    base_height: float = 0.0

    # Elevation
    elevation_scale: float = 1.0  # Multiplier for height data
    min_elevation: float = 0.0
    max_elevation: float = 100.0

    # Mesh resolution
    subdivisions_x: int = 100
    subdivisions_y: int = 100

    # Smoothing
    smooth_factor: int = 1
    use_smooth_shade: bool = True

    # Procedural settings (if no DEM)
    procedural_scale: float = 100.0
    procedural_octaves: int = 4
    procedural_persistence: float = 0.5

    # Charlotte-specific
    charlotte_elevation_base: float = 228.0  # Charlotte avg elevation in meters


class TerrainSystem:
    """
    Manages terrain elevation for the Charlotte Digital Twin.

    Can load real DEM data or generate procedural terrain.
    """

    def __init__(self):
        """Initialize terrain system."""
        self._material_cache: Dict[str, Any] = {}
        self._elevation_cache: Dict[Tuple[int, int], float] = {}

    def create_terrain(
        self,
        config: Optional[TerrainConfig] = None,
        source_type: TerrainSourceType = TerrainSourceType.PROCEDURAL,
        height_map_path: Optional[str] = None,
        name: str = "Terrain",
    ) -> Optional[Object]:
        """
        Create terrain mesh.

        Args:
            config: Terrain configuration
            source_type: How to get elevation data
            height_map_path: Path to height map image (if applicable)
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or TerrainConfig()

        # Create grid mesh
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Generate vertices
        step_x = config.size_x / config.subdivisions_x
        step_y = config.size_y / config.subdivisions_y
        half_x = config.size_x / 2
        half_y = config.size_y / 2

        # Load height map if provided
        height_data = None
        if source_type == TerrainSourceType.HEIGHT_MAP and height_map_path:
            height_data = self._load_height_map(height_map_path, config)

        # Create vertices
        for j in range(config.subdivisions_y + 1):
            for i in range(config.subdivisions_x + 1):
                x = -half_x + i * step_x
                y = -half_y + j * step_y

                # Get elevation
                if source_type == TerrainSourceType.FLAT:
                    z = config.base_height
                elif height_data is not None:
                    z = self._sample_height_map(height_data, i, j, config)
                else:
                    z = self._procedural_elevation(x, y, config)

                bm.verts.new((x, y, z))

        bm.verts.ensure_lookup_table()

        # Create faces
        for j in range(config.subdivisions_y):
            for i in range(config.subdivisions_x):
                v1 = bm.verts[j * (config.subdivisions_x + 1) + i]
                v2 = bm.verts[j * (config.subdivisions_x + 1) + i + 1]
                v3 = bm.verts[(j + 1) * (config.subdivisions_x + 1) + i + 1]
                v4 = bm.verts[(j + 1) * (config.subdivisions_x + 1) + i]
                bm.faces.new([v1, v2, v3, v4])

        # Smooth if requested
        if config.smooth_factor > 0:
            bmesh.ops.smooth_vert(
                bm,
                verts=bm.verts,
                factor=0.5,
                use_axis_x=True,
                use_axis_y=True,
                use_axis_z=True,
            )

        bm.to_mesh(mesh)
        bm.free()

        # Apply smooth shading
        if config.use_smooth_shade:
            for poly in mesh.polygons:
                poly.use_smooth = True

        # Apply ground material
        mat = self._get_terrain_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def create_road_profile(
        self,
        road_points: List[Tuple[float, float, float]],
        width: float = 20.0,
        shoulder_width: float = 3.0,
        config: Optional[TerrainConfig] = None,
        name: str = "Road_Terrain",
    ) -> Optional[Object]:
        """
        Create terrain profile following a road path.

        Generates terrain that conforms to road elevation
        with proper drainage slopes.

        Args:
            road_points: Center line points (x, y, z)
            width: Road width
            shoulder_width: Shoulder width on each side
            config: Terrain configuration
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE or len(road_points) < 2:
            return None

        config = config or TerrainConfig()

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        total_width = width + shoulder_width * 2

        # Generate vertices along road
        for i, point in enumerate(road_points):
            p = Vector(point)

            # Calculate direction
            if i == 0:
                direction = (Vector(road_points[1]) - p).normalized()
            elif i == len(road_points) - 1:
                direction = (p - Vector(road_points[-2])).normalized()
            else:
                direction = (Vector(road_points[i + 1]) - Vector(road_points[i - 1])).normalized()

            perpendicular = Vector((-direction.y, direction.x, 0))

            # Create vertices across road width
            for offset in [-total_width, -width/2, width/2, total_width]:
                pos = p + perpendicular * offset

                # Add terrain slope away from road
                if abs(offset) > width / 2:
                    slope = (abs(offset) - width / 2) * 0.05  # 5% slope
                    z = point[2] - slope
                else:
                    z = point[2]

                bm.verts.new((pos.x, pos.y, z))

        bm.verts.ensure_lookup_table()

        # Create faces
        verts_per_row = 4
        for i in range(len(road_points) - 1):
            for j in range(verts_per_row - 1):
                v1 = bm.verts[i * verts_per_row + j]
                v2 = bm.verts[i * verts_per_row + j + 1]
                v3 = bm.verts[(i + 1) * verts_per_row + j + 1]
                v4 = bm.verts[(i + 1) * verts_per_row + j]
                bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_terrain_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def get_elevation_at_point(
        self,
        x: float,
        y: float,
        config: Optional[TerrainConfig] = None,
    ) -> float:
        """
        Get terrain elevation at a specific point.

        Args:
            x: X coordinate
            y: Y coordinate
            config: Terrain configuration

        Returns:
            Elevation in meters
        """
        config = config or TerrainConfig()

        # Check cache
        cache_key = (int(x), int(y))
        if cache_key in self._elevation_cache:
            return self._elevation_cache[cache_key]

        # Calculate procedural elevation
        elevation = self._procedural_elevation(x, y, config)

        # Cache result
        self._elevation_cache[cache_key] = elevation

        return elevation

    def _procedural_elevation(
        self,
        x: float,
        y: float,
        config: TerrainConfig,
    ) -> float:
        """Generate procedural elevation using layered noise."""
        if config.charlotte_elevation_base > 0:
            # Charlotte-specific: gentle rolling terrain
            base = config.charlotte_elevation_base
        else:
            base = config.base_height

        # Simple multi-octave noise approximation
        elevation = 0.0
        amplitude = 1.0
        frequency = 1.0 / config.procedural_scale
        max_value = 0.0

        for _ in range(config.procedural_octaves):
            # Simple hash-based noise
            nx = x * frequency
            ny = y * frequency

            # Pseudo-noise using sin
            noise = (
                math.sin(nx * 12.9898 + ny * 78.233) * 43758.5453
            ) % 1.0

            elevation += noise * amplitude
            max_value += amplitude

            amplitude *= config.procedural_persistence
            frequency *= 2.0

        # Normalize
        elevation = elevation / max_value

        # Scale to elevation range
        elevation = config.min_elevation + elevation * (config.max_elevation - config.min_elevation)
        elevation *= config.elevation_scale

        return base + elevation

    def _load_height_map(
        self,
        path: str,
        config: TerrainConfig,
    ) -> Optional[List[List[float]]]:
        """Load height data from image file."""
        if not BLENDER_AVAILABLE or not os.path.exists(path):
            return None

        try:
            # Load image
            img = bpy.data.images.load(path)
            width = img.size[0]
            height = img.size[1]

            # Extract grayscale values
            data = []
            pixels = list(img.pixels)

            for y in range(height):
                row = []
                for x in range(width):
                    idx = (y * width + x) * 4  # RGBA
                    gray = pixels[idx]  # Use red channel
                    row.append(gray)
                data.append(row)

            # Unload image
            bpy.data.images.remove(img)

            return data

        except Exception:
            return None

    def _sample_height_map(
        self,
        height_data: List[List[float]],
        i: int,
        j: int,
        config: TerrainConfig,
    ) -> float:
        """Sample height map at grid position."""
        if height_data is None:
            return config.base_height

        # Map grid position to height map
        height_y = int(j * len(height_data) / (config.subdivisions_y + 1))
        height_x = int(i * len(height_data[0]) / (config.subdivisions_x + 1))

        # Clamp
        height_y = min(max(0, height_y), len(height_data) - 1)
        height_x = min(max(0, height_x), len(height_data[0]) - 1)

        # Get value
        normalized = height_data[height_y][height_x]

        # Scale to elevation
        elevation = config.min_elevation + normalized * (config.max_elevation - config.min_elevation)
        elevation *= config.elevation_scale

        return config.base_height + elevation

    def _get_terrain_material(self) -> Optional[Any]:
        """Get or create terrain material."""
        if not BLENDER_AVAILABLE:
            return None

        if "terrain" in self._material_cache:
            return self._material_cache["terrain"]

        mat = bpy.data.materials.new("Terrain_Ground")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Coordinate
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-800, 0)

        # Noise for color variation
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-600, 0)
        noise.inputs["Scale"].default_value = 50.0
        noise.inputs["Detail"].default_value = 4
        links.new(tex_coord.outputs["Generated"], noise.inputs["Vector"])

        # Color ramp
        color_ramp = nodes.new("ShaderNodeValToRGB")
        color_ramp.location = (-400, 0)
        color_ramp.color_ramp.elements[0].color = (0.25, 0.35, 0.2, 1.0)  # Dark green
        color_ramp.color_ramp.elements[1].color = (0.4, 0.45, 0.3, 1.0)   # Light green
        links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])

        # BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Roughness"].default_value = 0.9
        bsdf.inputs["Metallic"].default_value = 0.0

        links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache["terrain"] = mat
        return mat


def create_charlotte_terrain(
    size: float = 2000.0,
    resolution: int = 200,
    collection: Optional[Collection] = None,
) -> Optional[Object]:
    """
    Create terrain mesh for Charlotte area.

    Uses Charlotte-specific elevation parameters.

    Args:
        size: Terrain size in meters
        resolution: Grid resolution
        collection: Collection to add to

    Returns:
        Terrain mesh object
    """
    config = TerrainConfig(
        size_x=size,
        size_y=size,
        subdivisions_x=resolution,
        subdivisions_y=resolution,
        charlotte_elevation_base=228.0,  # Charlotte avg elevation
        min_elevation=-10.0,  # Some variation below
        max_elevation=30.0,   # Some variation above
        procedural_scale=200.0,
        procedural_octaves=4,
        use_smooth_shade=True,
    )

    system = TerrainSystem()
    terrain = system.create_terrain(config, TerrainSourceType.PROCEDURAL, name="Charlotte_Terrain")

    if terrain and collection:
        collection.objects.link(terrain)

    return terrain


def apply_elevation_to_road(
    road_points: List[Tuple[float, float]],
    config: Optional[TerrainConfig] = None,
) -> List[Tuple[float, float, float]]:
    """
    Apply terrain elevation to a 2D road path.

    Args:
        road_points: 2D road points (x, y)
        config: Terrain configuration

    Returns:
        3D road points (x, y, z)
    """
    system = TerrainSystem()
    config = config or TerrainConfig()

    result = []
    for x, y in road_points:
        z = system.get_elevation_at_point(x, y, config)
        result.append((x, y, z))

    return result


__all__ = [
    "TerrainSourceType",
    "TerrainConfig",
    "TerrainSystem",
    "create_charlotte_terrain",
    "apply_elevation_to_road",
]
