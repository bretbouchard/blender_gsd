"""
Building Generator - Procedural Skyscrapers and Structures

Creates procedural buildings with varied architectural styles.
Supports downtown cores, residential neighborhoods, and mixed-use areas.

Usage:
    from lib.animation.city.buildings import BuildingGenerator, generate_downtown

    # Generate a single building
    gen = BuildingGenerator()
    building = gen.create_building(
        footprint=[(0,0), (10,0), (10,10), (0,10)],
        height=150.0,
        style="glass_tower"
    )

    # Generate a downtown area
    downtown = generate_downtown(
        area_bounds=(-200, -200, 200, 200),
        building_count=50,
        height_range=(80, 300),
        style="mixed"
    )
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from pathlib import Path
import math
import random

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    Matrix = None
    BLENDER_AVAILABLE = False


@dataclass
class BuildingStyle:
    """Architectural style configuration."""
    name: str
    window_style: str = "modern"  # modern, classical, industrial
    window_width: float = 1.5
    window_height: float = 2.0
    window_spacing: float = 2.0
    floor_height: float = 4.0
    base_color: Tuple[float, float, float] = (0.7, 0.7, 0.75)
    accent_color: Tuple[float, float, float] = (0.5, 0.55, 0.6)
    window_color: Tuple[float, float, float, float] = (0.3, 0.5, 0.7, 0.8)
    has_roof_features: bool = True
    has_entrance: bool = True
    has_setback: bool = False
    detail_level: str = "medium"  # low, medium, high


@dataclass
class BuildingConfig:
    """Configuration for a single building."""
    name: str
    footprint: List[Tuple[float, float]]
    height: float
    floors: int = 0
    style: str = "modern"
    has_parking: bool = False
    parking_levels: int = 0
    rooftop_features: List[str] = field(default_factory=list)
    material: str = "glass"


@dataclass
class SkyscraperConfig:
    """Configuration for skyscraper generation."""
    min_height: float = 80.0
    max_height: float = 400.0
    min_floors: int = 20
    max_floors: int = 100
    footprint_style: str = "rectangular"  # rectangular, L_shaped, T_shaped, circular
    taper_style: str = "straight"  # straight, setback, tapered, stepped
    antenna_chance: float = 0.3
    helipad_chance: float = 0.1
    sky_lobby_chance: float = 0.2


# Building style presets
BUILDING_PRESETS = {
    "glass_tower": BuildingStyle(
        name="Glass Tower",
        window_style="modern",
        window_width=2.0,
        window_height=2.5,
        floor_height=4.0,
        base_color=(0.6, 0.7, 0.8),
        accent_color=(0.4, 0.5, 0.6),
        window_color=(0.2, 0.4, 0.6, 0.7),
        has_roof_features=True,
    ),
    "modern_office": BuildingStyle(
        name="Modern Office",
        window_style="modern",
        window_width=1.8,
        window_height=2.2,
        floor_height=3.8,
        base_color=(0.7, 0.72, 0.75),
        accent_color=(0.5, 0.55, 0.6),
        window_color=(0.3, 0.45, 0.55, 0.8),
    ),
    "classical": BuildingStyle(
        name="Classical",
        window_style="classical",
        window_width=1.2,
        window_height=1.8,
        window_spacing=1.5,
        floor_height=4.5,
        base_color=(0.85, 0.82, 0.78),
        accent_color=(0.6, 0.55, 0.5),
        window_color=(0.3, 0.35, 0.4, 0.9),
        has_setback=True,
    ),
    "industrial": BuildingStyle(
        name="Industrial",
        window_style="industrial",
        window_width=2.5,
        window_height=3.0,
        floor_height=5.0,
        base_color=(0.5, 0.5, 0.52),
        accent_color=(0.4, 0.4, 0.42),
        window_color=(0.3, 0.35, 0.4, 0.6),
    ),
    "residential": BuildingStyle(
        name="Residential",
        window_style="modern",
        window_width=1.4,
        window_height=1.6,
        window_spacing=1.2,
        floor_height=3.2,
        base_color=(0.9, 0.88, 0.85),
        accent_color=(0.7, 0.65, 0.6),
        window_color=(0.2, 0.3, 0.5, 0.7),
        has_balconies=True,
    ),
    "art_deco": BuildingStyle(
        name="Art Deco",
        window_style="classical",
        window_width=1.0,
        window_height=2.0,
        window_spacing=2.0,
        floor_height=4.0,
        base_color=(0.75, 0.75, 0.7),
        accent_color=(0.9, 0.85, 0.6),
        window_color=(0.2, 0.25, 0.3, 0.8),
        has_setback=True,
    ),
    "brutalist": BuildingStyle(
        name="Brutalist",
        window_style="industrial",
        window_width=1.5,
        window_height=1.5,
        floor_height=3.5,
        base_color=(0.6, 0.58, 0.55),
        accent_color=(0.5, 0.48, 0.45),
        window_color=(0.15, 0.2, 0.25, 0.9),
    ),
    "contemporary": BuildingStyle(
        name="Contemporary",
        window_style="modern",
        window_width=2.2,
        window_height=2.8,
        floor_height=4.2,
        base_color=(0.8, 0.82, 0.85),
        accent_color=(0.6, 0.65, 0.7),
        window_color=(0.25, 0.4, 0.55, 0.75),
        has_roof_features=True,
    ),
}


class BuildingGenerator:
    """
    Procedural building generator.

    Creates buildings from footprints with architectural details
    including windows, entrances, and rooftop features.
    """

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def create_building(
        self,
        footprint: List[Tuple[float, float]],
        height: float,
        style: str = "modern",
        name: str = "Building",
        floors: Optional[int] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        Create a building from footprint.

        Args:
            footprint: List of (x, y) corner points
            height: Building height in meters
            style: Style preset name
            name: Building object name
            floors: Number of floors (auto-calculated if None)

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE or len(footprint) < 3:
            return None

        import bmesh

        # Get style config
        style_config = BUILDING_PRESETS.get(style, BUILDING_PRESETS["modern"])

        # Calculate floors
        if floors is None:
            floors = int(height / style_config.floor_height)

        # Create mesh
        bm = bmesh.new()
        mesh = bpy.data.meshes.new(name)

        # Create base footprint vertices
        base_verts = []
        for x, y in footprint:
            vert = bm.verts.new((x, y, 0.0))
            base_verts.append(vert)

        bm.verts.ensure_lookup_table()

        # Create top vertices
        top_verts = []
        for x, y in footprint:
            vert = bm.verts.new((x, y, height))
            top_verts.append(vert)

        bm.verts.ensure_lookup_table()

        n = len(base_verts)

        # Create wall faces
        for i in range(n):
            v1 = base_verts[i]
            v2 = base_verts[(i + 1) % n]
            v3 = top_verts[(i + 1) % n]
            v4 = top_verts[i]

            try:
                face = bm.faces.new([v1, v2, v3, v4])
            except:
                pass

        # Create top face (roof)
        try:
            roof_face = bm.faces.new(top_verts)
        except:
            pass

        # Create bottom face
        try:
            bottom_face = bm.faces.new(base_verts)
            bottom_face.normal_flip()
        except:
            pass

        bm.to_mesh(mesh)
        bm.free()

        # Create object
        obj = bpy.data.objects.new(name, mesh)

        # Apply building material
        self._apply_building_material(obj, style_config)

        # Add window details (if high detail)
        if style_config.detail_level == "high":
            self._add_window_details(obj, style_config, floors)

        return obj

    def create_skyscraper(
        self,
        position: Tuple[float, float, float],
        config: Optional[SkyscraperConfig] = None,
        style: str = "glass_tower",
        name: str = "Skyscraper"
    ) -> Optional[Any]:
        """
        Create a procedural skyscraper.

        Args:
            position: Building center position
            config: Skyscraper configuration
            style: Style preset
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or SkyscraperConfig()

        # Random height within range
        height = random.uniform(config.min_height, config.max_height)
        floors = random.randint(config.min_floors, config.max_floors)

        # Generate footprint based on style
        footprint = self._generate_footprint(
            config.footprint_style,
            min_width=20.0,
            max_width=40.0
        )

        # Apply taper/setback
        if config.taper_style != "straight":
            footprint = self._apply_taper(
                footprint,
                height,
                config.taper_style,
                floors
            )

        # Offset to position
        footprint = [
            (x + position[0], y + position[1])
            for x, y in footprint
        ]

        # Create building
        obj = self.create_building(
            footprint=footprint,
            height=height,
            style=style,
            name=name,
            floors=floors
        )

        if obj:
            obj.location[2] = position[2]

            # Add rooftop features
            if random.random() < config.antenna_chance:
                self._add_antenna(obj, height)

            if random.random() < config.helipad_chance:
                self._add_helipad(obj, height)

            if random.random() < config.sky_lobby_chance:
                self._add_sky_lobby(obj, height, floors)

        return obj

    def _generate_footprint(
        self,
        style: str,
        min_width: float = 20.0,
        max_width: float = 40.0
    ) -> List[Tuple[float, float]]:
        """Generate building footprint based on style."""
        width = random.uniform(min_width, max_width)
        depth = random.uniform(min_width * 0.6, max_width * 0.8)

        if style == "rectangular":
            return [
                (-width/2, -depth/2),
                (width/2, -depth/2),
                (width/2, depth/2),
                (-width/2, depth/2),
            ]

        elif style == "L_shaped":
            wing_width = width * 0.4
            return [
                (-width/2, -depth/2),
                (width/2, -depth/2),
                (width/2, depth/2 - wing_width),
                (width/2 - wing_width, depth/2 - wing_width),
                (width/2 - wing_width, depth/2),
                (-width/2, depth/2),
            ]

        elif style == "T_shaped":
            wing_width = width * 0.3
            return [
                (-width/2, -depth/2),
                (width/2, -depth/2),
                (width/2, -depth/2 + wing_width),
                (wing_width, -depth/2 + wing_width),
                (wing_width, depth/2),
                (-wing_width, depth/2),
                (-wing_width, -depth/2 + wing_width),
                (-width/2, -depth/2 + wing_width),
            ]

        elif style == "circular":
            # Approximate circle with 12 segments
            points = []
            radius = width / 2
            for i in range(12):
                angle = i * (2 * math.pi / 12)
                points.append((
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                ))
            return points

        # Default to rectangular
        return [
            (-width/2, -depth/2),
            (width/2, -depth/2),
            (width/2, depth/2),
            (-width/2, depth/2),
        ]

    def _apply_taper(
        self,
        footprint: List[Tuple[float, float]],
        height: float,
        taper_style: str,
        floors: int
    ) -> List[Tuple[float, float]]:
        """Apply tapering to footprint (for setback buildings)."""
        # For now, return original footprint
        # Full implementation would modify based on taper style
        return footprint

    def _apply_building_material(
        self,
        obj: Any,
        style: BuildingStyle
    ) -> None:
        """Apply procedural material to building."""
        if not BLENDER_AVAILABLE:
            return

        mat = bpy.data.materials.new(f"BuildingMat_{obj.name}")
        mat.use_nodes = True

        # Clear default nodes
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Create node setup
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (400, 0)

        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        bsdf.inputs["Base Color"].default_value = (*style.base_color, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.4
        bsdf.inputs["Metallic"].default_value = 0.1

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    def _add_window_details(
        self,
        obj: Any,
        style: BuildingStyle,
        floors: int
    ) -> None:
        """Add window geometry details."""
        # Would use Geometry Nodes or boolean operations
        # For now, skip this for performance
        pass

    def _add_antenna(self, obj: Any, height: float) -> None:
        """Add antenna to building top."""
        if not BLENDER_AVAILABLE:
            return

        antenna_height = random.uniform(5, 15)

        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.3,
            depth=antenna_height,
            location=(0, 0, height + antenna_height/2)
        )
        antenna = bpy.context.active_object
        antenna.name = f"{obj.name}_Antenna"
        antenna.parent = obj

    def _add_helipad(self, obj: Any, height: float) -> None:
        """Add helipad to building top."""
        if not BLENDER_AVAILABLE:
            return

        bpy.ops.mesh.primitive_circle_add(
            radius=8.0,
            fill_type='NGON',
            location=(0, 0, height + 0.1)
        )
        helipad = bpy.context.active_object
        helipad.name = f"{obj.name}_Helipad"
        helipad.parent = obj

    def _add_sky_lobby(
        self,
        obj: Any,
        height: float,
        floors: int
    ) -> None:
        """Add sky lobby observation deck."""
        # Would add glass-enclosed observation deck
        pass


def create_building(
    footprint: List[Tuple[float, float]],
    height: float,
    style: str = "modern",
    **kwargs
) -> Optional[Any]:
    """Convenience function to create a building."""
    gen = BuildingGenerator()
    return gen.create_building(footprint, height, style, **kwargs)


def generate_downtown(
    area_bounds: Tuple[float, float, float, float] = (-200, -200, 200, 200),
    building_count: int = 50,
    height_range: Tuple[float, float] = (80, 300),
    density: float = 0.7,
    style: str = "mixed",
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a downtown city core.

    Args:
        area_bounds: (min_x, min_y, max_x, max_y) area to fill
        building_count: Target number of buildings
        height_range: (min, max) building heights
        density: Building density 0.0-1.0
        style: Style preset or "mixed" for variety
        seed: Random seed for reproducibility

    Returns:
        Dictionary with generated buildings
    """
    if not BLENDER_AVAILABLE:
        return {"buildings": []}

    if seed is not None:
        random.seed(seed)

    gen = BuildingGenerator()

    # Create collection
    collection = bpy.data.collections.new("Downtown")
    bpy.context.collection.children.link(collection)

    buildings = []
    min_x, min_y, max_x, max_y = area_bounds

    # Calculate grid positions
    grid_spacing = 50.0  # meters between buildings
    grid_x = int((max_x - min_x) / grid_spacing)
    grid_y = int((max_y - min_y) / grid_spacing)

    # Randomly place buildings
    positions = []
    for i in range(grid_x):
        for j in range(grid_y):
            if random.random() < density:
                x = min_x + i * grid_spacing + random.uniform(-10, 10)
                y = min_y + j * grid_spacing + random.uniform(-10, 10)
                positions.append((x, y))

    # Limit to building count
    if len(positions) > building_count:
        positions = random.sample(positions, building_count)

    # Generate buildings
    styles = list(BUILDING_PRESETS.keys())

    for i, (x, y) in enumerate(positions):
        # Height based on distance from center (taller in center)
        dist_from_center = math.sqrt(
            ((x - (min_x + max_x)/2) / (max_x - min_x)) ** 2 +
            ((y - (min_y + max_y)/2) / (max_y - min_y)) ** 2
        )
        height_factor = 1.0 - dist_from_center * 0.5

        height = random.uniform(*height_range) * height_factor
        height = max(height_range[0] * 0.5, height)

        # Choose style
        building_style = style if style != "mixed" else random.choice(styles)

        # Generate skyscraper
        skyscraper_config = SkyscraperConfig(
            min_height=height * 0.8,
            max_height=height * 1.2,
            footprint_style=random.choice(["rectangular", "L_shaped", "T_shaped"]),
            taper_style=random.choice(["straight", "setback", "tapered"]),
        )

        building = gen.create_skyscraper(
            position=(x, y, 0),
            config=skyscraper_config,
            style=building_style,
            name=f"Downtown_Building_{i:03d}"
        )

        if building:
            collection.objects.link(building)
            buildings.append(building)

    return {
        "buildings": buildings,
        "collection": collection,
        "count": len(buildings),
    }


def generate_neighborhood(
    area_bounds: Tuple[float, float, float, float],
    building_count: int = 100,
    style: str = "residential",
    max_height: float = 30.0,
    min_height: float = 8.0,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a residential or commercial neighborhood.

    Args:
        area_bounds: Area to fill
        building_count: Target building count
        style: Neighborhood style
        max_height: Maximum building height
        min_height: Minimum building height
        seed: Random seed

    Returns:
        Dictionary with generated buildings
    """
    if not BLENDER_AVAILABLE:
        return {"buildings": []}

    if seed is not None:
        random.seed(seed)

    gen = BuildingGenerator()

    collection = bpy.data.collections.new(f"Neighborhood_{style}")
    bpy.context.collection.children.link(collection)

    buildings = []
    min_x, min_y, max_x, max_y = area_bounds

    for i in range(building_count):
        # Random position
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)

        # Random footprint size
        width = random.uniform(10, 20)
        depth = random.uniform(10, 20)

        footprint = [
            (x - width/2, y - depth/2),
            (x + width/2, y - depth/2),
            (x + width/2, y + depth/2),
            (x - width/2, y + depth/2),
        ]

        height = random.uniform(min_height, max_height)
        floors = int(height / 3.5)

        building = gen.create_building(
            footprint=footprint,
            height=height,
            style=style,
            name=f"Building_{i:03d}",
            floors=floors
        )

        if building:
            collection.objects.link(building)
            buildings.append(building)

    return {
        "buildings": buildings,
        "collection": collection,
        "count": len(buildings),
    }
