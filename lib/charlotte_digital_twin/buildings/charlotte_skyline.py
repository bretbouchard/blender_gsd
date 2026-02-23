"""
Charlotte Skyline Building Generator

Generates accurate 3D models of Charlotte's iconic buildings with
LED facade support. Based on research and reference photos.

Charlotte has MULTIPLE buildings with LED/illuminated facades that
participate in city-wide coordinated lighting events:

LED Buildings (10 total):
- Duke Energy Center (550 S Tryon) - 48 floors, ~2,500 LEDs (PRIMARY)
- Bank of America Corporate Center - 60 floors, crown/accent lighting
- Truist Center (Hearst Tower) - 46 floors, art-deco accent
- One Wells Fargo Center - 42 floors, "The Jukebox" rounded crown
- FNB Tower - 25 floors, modern LED (2021)
- Honeywell Tower - 23 floors, contemporary LED (2021)
- Ally Charlotte Center - 26 floors, modern illuminated
- Carillon Tower - 24 floors, neo-gothic spire
- NASCAR Hall of Fame - Curved LED ribbon (distinctive)
- 200 South Tryon - 34 floors, curtain wall accent

Reference: .planning/research/CHARLOTTE_LED_IMAGE_URLS.md

Usage:
    from lib.charlotte_digital_twin.buildings.charlotte_skyline import (
        CharlotteSkylineBuilder,
        create_duke_energy_center,
        create_charlotte_skyline,
    )

    # Create individual building
    duke = create_duke_energy_center()
    duke.set_led_color(LEDColor.PANTHERS_BLUE)

    # Create entire skyline with all LED buildings
    skyline = create_charlotte_skyline()

    # Set Panthers mode for ALL buildings
    builder = CharlotteSkylineBuilder()
    builder.set_panthers_mode()
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math

try:
    import bpy
    import mathutils
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .led_facade import (
    LEDColor,
    LEDAnimationType,
    LEDZone,
    LEDBuildingConfig,
    LEDFacadeBuilder,
    LEDMaterialBuilder,
    LEDAnimator,
)


class CharlotteBuilding(Enum):
    """Major Charlotte buildings with LED/illuminated facades."""
    DUKE_ENERGY_CENTER = "duke_energy_center"
    BOA_CORPORATE_CENTER = "boa_corporate_center"
    TRUIST_CENTER = "truist_center"
    WELLS_FARGO_ONE = "wells_fargo_one"
    CARILLON_TOWER = "carillon_tower"
    FNB_TOWER = "fnb_tower"
    HONEYWELL_TOWER = "honeywell_tower"
    ALLY_CENTER = "ally_center"
    NASCAR_HOF = "nascar_hof"
    SOUTH_TRYON_200 = "south_tryon_200"


@dataclass
class BuildingSpec:
    """Building specifications for geometry generation."""
    name: str
    address: str
    floors: int
    height_m: float
    width_m: float
    depth_m: float
    lat: float
    lon: float
    building_type: str
    has_led: bool = False
    led_count: int = 0
    crown_type: str = "flat"  # flat, granite, rounded, spire, art_deco
    window_pattern: str = "curtain_wall"  # curtain_wall, grid, ribbon


# Charlotte building specifications from research
CHARLOTTE_BUILDING_SPECS: Dict[CharlotteBuilding, BuildingSpec] = {
    CharlotteBuilding.DUKE_ENERGY_CENTER: BuildingSpec(
        name="Duke Energy Center",
        address="550 South Tryon Street",
        floors=48,
        height_m=240,
        width_m=45,
        depth_m=45,
        lat=35.2267,
        lon=-80.8467,
        building_type="office",
        has_led=True,
        led_count=2500,
        crown_type="flat",
        window_pattern="curtain_wall",
    ),
    CharlotteBuilding.BOA_CORPORATE_CENTER: BuildingSpec(
        name="Bank of America Corporate Center",
        address="100 North Tryon Street",
        floors=60,
        height_m=265,
        width_m=50,
        depth_m=50,
        lat=35.2276,
        lon=-80.8436,
        building_type="office",
        has_led=False,
        crown_type="granite",
        window_pattern="curtain_wall",
    ),
    CharlotteBuilding.TRUIST_CENTER: BuildingSpec(
        name="Truist Center",
        address="214 North Tryon Street",
        floors=46,
        height_m=201,
        width_m=40,
        depth_m=40,
        lat=35.2252,
        lon=-80.8401,
        building_type="office",
        has_led=False,
        crown_type="art_deco",
        window_pattern="grid",
    ),
    CharlotteBuilding.WELLS_FARGO_ONE: BuildingSpec(
        name="One Wells Fargo Center",
        address="301 South College Street",
        floors=42,
        height_m=176,
        width_m=38,
        depth_m=38,
        lat=35.2282,
        lon=-80.8424,
        building_type="office",
        has_led=False,
        crown_type="rounded",
        window_pattern="curtain_wall",
    ),
    CharlotteBuilding.CARILLON_TOWER: BuildingSpec(
        name="Carillon Tower",
        address="227 West Trade Street",
        floors=24,
        height_m=120,
        width_m=30,
        depth_m=30,
        lat=35.2265,
        lon=-80.8475,
        building_type="office",
        has_led=False,
        crown_type="spire",
        window_pattern="grid",
    ),
    CharlotteBuilding.FNB_TOWER: BuildingSpec(
        name="FNB Tower",
        address="401 South Graham Street",
        floors=25,
        height_m=115,
        width_m=35,
        depth_m=35,
        lat=35.2270,
        lon=-80.8510,
        building_type="mixed",
        has_led=False,
        crown_type="flat",
        window_pattern="curtain_wall",
    ),
    CharlotteBuilding.HONEYWELL_TOWER: BuildingSpec(
        name="Honeywell Tower",
        address="855 South Mint Street",
        floors=23,
        height_m=100,
        width_m=40,
        depth_m=40,
        lat=35.2210,
        lon=-80.8520,
        building_type="office",
        has_led=True,  # Modern LED lighting (2021)
        led_count=560,
        crown_type="flat",
        window_pattern="curtain_wall",
    ),
    CharlotteBuilding.ALLY_CENTER: BuildingSpec(
        name="Ally Charlotte Center",
        address="201 South Tryon Street",
        floors=26,
        height_m=122,
        width_m=38,
        depth_m=38,
        lat=35.2245,
        lon=-80.8440,
        building_type="office",
        has_led=True,  # Modern illuminated facade
        led_count=800,
        crown_type="flat",
        window_pattern="curtain_wall",
    ),
    CharlotteBuilding.NASCAR_HOF: BuildingSpec(
        name="NASCAR Hall of Fame",
        address="400 East Martin Luther King Jr Boulevard",
        floors=5,
        height_m=30,
        width_m=80,
        depth_m=60,
        lat=35.2250,
        lon=-80.8390,
        building_type="museum",
        has_led=True,  # Distinctive curved LED ribbon
        led_count=800,
        crown_type="flat",
        window_pattern="ribbon",
    ),
    CharlotteBuilding.SOUTH_TRYON_200: BuildingSpec(
        name="200 South Tryon",
        address="200 South Tryon Street",
        floors=34,
        height_m=148,
        width_m=35,
        depth_m=35,
        lat=35.2255,
        lon=-80.8450,
        building_type="office",
        has_led=True,  # Curtain wall accent lighting
        led_count=480,
        crown_type="flat",
        window_pattern="curtain_wall",
    ),
}


class CharlotteSkylineBuilder:
    """Builder for Charlotte skyline buildings."""

    def __init__(self):
        self.buildings: Dict[str, Any] = {}
        self.led_configs: Dict[str, LEDBuildingConfig] = {}
        self._led_builder = LEDFacadeBuilder()
        self._material_builder = LEDMaterialBuilder()

    def create_building(
        self,
        spec: BuildingSpec,
        location: Tuple[float, float, float] = (0, 0, 0),
    ) -> Optional[Any]:
        """
        Create a building mesh from specification.

        Args:
            spec: Building specifications
            location: World position (x, y, z)

        Returns:
            Blender object or None if Blender not available
        """
        if not BLENDER_AVAILABLE:
            return None

        # Calculate floor height
        floor_height = spec.height_m / spec.floors

        # Create building mesh
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=location,
        )
        building = bpy.context.active_object
        building.name = spec.name

        # Scale to building dimensions
        building.scale = (
            spec.width_m,
            spec.depth_m,
            spec.height_m,
        )
        building.location = (
            location[0],
            location[1],
            location[2] + spec.height_m / 2,
        )

        # Apply scale
        bpy.ops.object.transform_apply(scale=True)

        # Add crown based on type
        if spec.crown_type == "granite":
            self._add_granite_crown(building, spec)
        elif spec.crown_type == "rounded":
            self._add_rounded_crown(building, spec)
        elif spec.crown_type == "spire":
            self._add_spire(building, spec)
        elif spec.crown_type == "art_deco":
            self._add_art_deco_crown(building, spec)

        # Apply material
        if spec.has_led:
            self._apply_led_material(building, spec)
        else:
            self._apply_standard_material(building, spec)

        self.buildings[spec.name] = building
        return building

    def _add_granite_crown(self, building: Any, spec: BuildingSpec):
        """Add granite crown (Bank of America style)."""
        floor_height = spec.height_m / spec.floors
        crown_height = floor_height * 5

        bpy.ops.mesh.primitive_cube_add(size=1)
        crown = bpy.context.active_object
        crown.name = f"{spec.name}_crown"

        # Tapered crown
        crown.scale = (
            spec.width_m * 0.7,
            spec.depth_m * 0.7,
            crown_height,
        )
        crown.location = (
            building.location.x,
            building.location.y,
            building.location.z + spec.height_m / 2 + crown_height / 2,
        )

        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.join()  # Join to main building

    def _add_rounded_crown(self, building: Any, spec: BuildingSpec):
        """Add rounded crown (Wells Fargo style - 'The Jukebox')."""
        floor_height = spec.height_m / spec.floors
        crown_height = floor_height * 3
        radius = min(spec.width_m, spec.depth_m) / 2 * 0.7

        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=radius,
            location=(
                building.location.x,
                building.location.y,
                building.location.z + spec.height_m / 2 + crown_height / 2,
            ),
        )
        crown = bpy.context.active_object
        crown.name = f"{spec.name}_crown"
        crown.scale = (1, 1, 0.5)  # Flatten hemisphere

        bpy.ops.object.transform_apply(scale=True)

    def _add_spire(self, building: Any, spec: BuildingSpec):
        """Add neo-gothic spire (Carillon Tower style)."""
        floor_height = spec.height_m / spec.floors
        spire_height = spec.height_m * 0.2

        bpy.ops.mesh.primitive_cone_add(
            radius1=min(spec.width_m, spec.depth_m) / 4,
            depth=spire_height,
            location=(
                building.location.x,
                building.location.y,
                building.location.z + spec.height_m / 2 + spire_height / 2,
            ),
        )
        spire = bpy.context.active_object
        spire.name = f"{spec.name}_spire"

    def _add_art_deco_crown(self, building: Any, spec: BuildingSpec):
        """Add art-deco style crown (Truist Center style)."""
        floor_height = spec.height_m / spec.floors
        crown_height = floor_height * 4

        # Stepped pyramid
        for i, scale_factor in enumerate([0.8, 0.6, 0.4]):
            step_height = crown_height / 3
            bpy.ops.mesh.primitive_cube_add(size=1)
            step = bpy.context.active_object
            step.scale = (
                spec.width_m * scale_factor,
                spec.depth_m * scale_factor,
                step_height,
            )
            step.location = (
                building.location.x,
                building.location.y,
                building.location.z + spec.height_m / 2 + (i + 0.5) * step_height,
            )
            bpy.ops.object.transform_apply(scale=True)

    def _apply_led_material(self, building: Any, spec: BuildingSpec):
        """Apply LED facade material to building."""
        mat = self._material_builder.create_led_panel_material(
            name=f"led_{spec.name.lower().replace(' ', '_')}",
            base_color=(0.1, 0.12, 0.15),  # Dark glass base
            emission_color=LEDColor.WHITE.value,
            emission_strength=2.0,
            mix_factor=0.4,
        )

        if building.data.materials:
            building.data.materials[0] = mat
        else:
            building.data.materials.append(mat)

        # Create LED config
        led_config = self._led_builder.create_generic_led_facade(
            name=spec.name,
            floors=spec.floors,
            led_density=0.5,
        )
        self.led_configs[spec.name] = led_config

    def _apply_standard_material(self, building: Any, spec: BuildingSpec):
        """Apply standard glass/concrete material."""
        # Create glass material
        mat = bpy.data.materials.new(name=f"glass_{spec.name.lower().replace(' ', '_')}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Glass BSDF
        output = nodes.new('ShaderNodeOutputMaterial')
        glass = nodes.new('ShaderNodeBsdfGlass')

        # Configure glass
        glass.inputs['Color'].default_value = (0.6, 0.7, 0.8, 1.0)
        glass.inputs['Roughness'].default_value = 0.05
        glass.inputs['IOR'].default_value = 1.5

        links.new(glass.outputs['BSDF'], output.inputs['Surface'])

        if building.data.materials:
            building.data.materials[0] = mat
        else:
            building.data.materials.append(mat)

    def create_duke_energy_center(
        self,
        location: Tuple[float, float, float] = (0, 0, 0),
    ) -> Optional[Any]:
        """Create Duke Energy Center with LED facade."""
        spec = CHARLOTTE_BUILDING_SPECS[CharlotteBuilding.DUKE_ENERGY_CENTER]

        building = self.create_building(spec, location)

        if building:
            # Use full LED facade config
            led_config = self._led_builder.create_duke_energy_facade()
            self.led_configs[spec.name] = led_config

        return building

    def create_boa_center(
        self,
        location: Tuple[float, float, float] = (0, 0, 0),
    ) -> Optional[Any]:
        """Create Bank of America Corporate Center."""
        spec = CHARLOTTE_BUILDING_SPECS[CharlotteBuilding.BOA_CORPORATE_CENTER]
        return self.create_building(spec, location)

    def create_truist_center(
        self,
        location: Tuple[float, float, float] = (0, 0, 0),
    ) -> Optional[Any]:
        """Create Truist Center."""
        spec = CHARLOTTE_BUILDING_SPECS[CharlotteBuilding.TRUIST_CENTER]
        return self.create_building(spec, location)

    def create_full_skyline(
        self,
        center: Tuple[float, float, float] = (0, 0, 0),
        scale: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Create the full Charlotte skyline.

        Args:
            center: Center point for skyline
            scale: Scale factor for all buildings

        Returns:
            Dictionary of building name to Blender object
        """
        buildings = {}

        # Place buildings based on relative lat/lon
        for building_type, spec in CHARLOTTE_BUILDING_SPECS.items():
            # Convert lat/lon to meters (approximate)
            # Charlotte: ~35.2°N, -80.8°W
            # 1 degree lat ≈ 111km, 1 degree lon at 35°N ≈ 91km

            lat_offset = (spec.lat - 35.2271) * 111000 * scale
            lon_offset = (spec.lon - (-80.8431)) * 91000 * scale

            location = (
                center[0] + lon_offset,
                center[1] + lat_offset,
                center[2],
            )

            building = self.create_building(spec, location)
            if building:
                buildings[spec.name] = building

        return buildings

    def set_building_led_color(
        self,
        building_name: str,
        color: LEDColor,
    ):
        """Set LED color for a building."""
        if building_name in self.led_configs:
            config = self.led_configs[building_name]
            for zone in config.zones:
                zone.current_color = color.value

    def set_panthers_mode(self):
        """Set all LED buildings to Panthers blue."""
        for config in self.led_configs.values():
            LEDAnimator.apply_preset_panthers(config)


def create_duke_energy_center(
    location: Tuple[float, float, float] = (0, 0, 0),
) -> Optional[Any]:
    """
    Convenience function to create Duke Energy Center.

    Args:
        location: World position

    Returns:
        Blender building object
    """
    builder = CharlotteSkylineBuilder()
    return builder.create_duke_energy_center(location)


def create_charlotte_skyline(
    center: Tuple[float, float, float] = (0, 0, 0),
    scale: float = 1.0,
) -> Dict[str, Any]:
    """
    Convenience function to create full Charlotte skyline.

    Args:
        center: Center point for skyline
        scale: Scale factor

    Returns:
        Dictionary of building name to object
    """
    builder = CharlotteSkylineBuilder()
    return builder.create_full_skyline(center, scale)


def setup_charlotte_night_render():
    """
    Set up Charlotte night scene with LED buildings for rendering.

    Creates the skyline, configures night lighting, and sets up
    LED facades for realistic night shots.
    """
    if not BLENDER_AVAILABLE:
        return None

    # Create skyline
    builder = CharlotteSkylineBuilder()
    buildings = builder.create_full_skyline()

    # Configure night scene
    scene = bpy.context.scene

    # Set to Cycles for realistic lighting
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 256

    # Dark environment
    world = bpy.data.worlds.get("World")
    if not world:
        world = bpy.data.worlds.new("World")
    scene.world = world

    if world.use_nodes:
        nodes = world.node_tree.nodes
        bg = nodes.get("Background")
        if bg:
            bg.inputs['Color'].default_value = (0.02, 0.02, 0.05, 1.0)  # Dark blue night
            bg.inputs['Strength'].default_value = 0.3

    # Set Panthers mode for LED buildings
    builder.set_panthers_mode()

    return {
        "builder": builder,
        "buildings": buildings,
    }
