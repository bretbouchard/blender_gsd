"""
Charlotte Building LED Facade System

Implements programmable LED facade systems based on real Charlotte buildings:
- Duke Energy Center: ~2,500 programmable LEDs, 48 floors
- Bank of America Corporate Center: Granite crown with accent lighting
- Truist Center: Art-deco design with accent lighting

Based on research in:
- .planning/research/CHARLOTTE_LED_IMAGE_URLS.md
- .planning/research/DUKE_ENERGY_CENTER_LED_FACADE.md

Usage:
    from lib.charlotte_digital_twin.buildings.led_facade import (
        LEDFacadeBuilder,
        LEDZone,
        LEDAnimationType,
        create_duke_energy_center_leds,
    )

    # Create Duke Energy Center with LED facade
    builder = LEDFacadeBuilder()
    led_facade = builder.create_duke_energy_facade()
    led_facade.set_panthers_mode()  # Panthers blue
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import math
import random

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


class LEDColor(Enum):
    """Predefined LED colors for Charlotte buildings."""
    # Duke Energy Center standard colors
    WHITE = (1.0, 1.0, 0.95)  # Warm white (~3000K)
    PANTHERS_BLUE = (0.0, 0.52, 0.79)  # #0085CA - Process Blue
    PANTHERS_BLACK = (0.1, 0.1, 0.1)  # For contrast
    CHRISTMAS_RED = (1.0, 0.0, 0.0)
    CHRISTMAS_GREEN = (0.0, 1.0, 0.0)
    VALENTINES_RED = (0.9, 0.1, 0.2)
    HALLOWEEN_ORANGE = (1.0, 0.5, 0.0)
    HALLOWEEN_PURPLE = (0.5, 0.0, 0.5)

    # Additional common colors
    INDEPENDENCE_BLUE = (0.2, 0.3, 0.7)
    MEMORIAL_DAY_RED = (0.8, 0.2, 0.2)
    GOLD = (1.0, 0.84, 0.0)

    # Off state
    OFF = (0.02, 0.02, 0.02)


class LEDAnimationType(Enum):
    """LED animation patterns."""
    STATIC = "static"  # Solid color
    PULSE = "pulse"  # Gentle brightness pulse
    WAVE = "wave"  # Wave pattern across zones
    CHASE = "chase"  # Sequential zone lighting
    RAINBOW = "rainbow"  # Rainbow gradient
    SPARKLE = "sparkle"  # Random twinkling
    BREATHE = "breathe"  # Breathing effect
    CASCADE = "cascade"  # Waterfall cascade


@dataclass
class LEDZone:
    """Represents a single LED zone on a building facade."""
    name: str
    floor_start: int
    floor_end: int
    position: str  # "north", "south", "east", "west", "crown", "spire"
    led_count: int
    current_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    brightness: float = 1.0
    animation: LEDAnimationType = LEDAnimationType.STATIC
    animation_speed: float = 1.0


@dataclass
class LEDBuildingConfig:
    """Configuration for a building's LED system."""
    building_name: str
    building_type: str  # "duke_energy", "boa_center", "truist", "generic"
    total_leds: int
    floors: int
    zones: List[LEDZone] = field(default_factory=list)
    default_color: Tuple[float, float, float] = (1.0, 1.0, 0.95)
    has_crown_lighting: bool = False
    has_spire_lighting: bool = False
    schedule_enabled: bool = True


class LEDFacadeBuilder:
    """Builder for creating LED facade systems for Charlotte buildings."""

    # Duke Energy Center specifications (from research)
    DUKE_ENERGY_SPEC = {
        "name": "Duke Energy Center",
        "address": "550 South Tryon Street",
        "floors": 48,
        "height_ft": 786.5,
        "height_m": 240,
        "led_count": 2500,  # Programmable LEDs
        "led_cost_per_night": 2.0,  # <$2/night
        "show_hours": "sundown to midnight",
        "designer": "Gabler-Youngston Architectural Lighting Design",
        "year_installed": 2009,
    }

    # Bank of America Corporate Center specifications
    BOA_CENTER_SPEC = {
        "name": "Bank of America Corporate Center",
        "floors": 60,
        "height_ft": 871,
        "height_m": 265,
        "feature": "Granite crown with accent lighting",
    }

    # Truist Center specifications
    TRUIST_CENTER_SPEC = {
        "name": "Truist Center (Hearst Tower)",
        "floors": 46,
        "height_ft": 659,
        "height_m": 201,
        "feature": "Art-deco design with architectural lighting",
    }

    # One Wells Fargo Center specifications
    WELLS_FARGO_ONE_SPEC = {
        "name": "One Wells Fargo Center",
        "floors": 42,
        "height_ft": 588,
        "height_m": 179,
        "feature": "Rounded crown 'The Jukebox' with accent lighting",
    }

    # FNB Tower specifications (new construction)
    FNB_TOWER_SPEC = {
        "name": "FNB Tower",
        "floors": 25,
        "height_ft": 377,
        "height_m": 115,
        "feature": "Modern LED facade (completed 2021)",
    }

    # Honeywell Tower specifications
    HONEYWELL_TOWER_SPEC = {
        "name": "Honeywell Tower",
        "floors": 23,
        "height_ft": 328,
        "height_m": 100,
        "feature": "Contemporary LED lighting (completed 2021)",
    }

    # Ally Charlotte Center specifications
    ALLY_CENTER_SPEC = {
        "name": "Ally Charlotte Center",
        "floors": 26,
        "height_ft": 400,
        "height_m": 122,
        "feature": "Modern illuminated facade",
    }

    # Carillon Tower specifications
    CARILLON_TOWER_SPEC = {
        "name": "Carillon Tower",
        "floors": 24,
        "height_ft": 394,
        "height_m": 120,
        "feature": "Neo-gothic spire with accent lighting",
    }

    # NASCAR Hall of Fame specifications
    NASCAR_HOF_SPEC = {
        "name": "NASCAR Hall of Fame",
        "floors": 5,
        "height_ft": 100,
        "height_m": 30,
        "feature": "Distinctive curved illuminated ribbon",
    }

    # 200 South Tryon specifications
    SOUTH_TRYON_200_SPEC = {
        "name": "200 South Tryon",
        "floors": 34,
        "height_ft": 485,
        "height_m": 148,
        "feature": "Glass curtain wall with accent lighting",
    }

    def __init__(self):
        self.buildings: Dict[str, LEDBuildingConfig] = {}

    def create_duke_energy_facade(self) -> LEDBuildingConfig:
        """
        Create the Duke Energy Center LED facade.

        The Duke Energy Center has programmable LED lighting on its
        glass curtain wall facade. The LEDs are arranged in vertical
        zones that can display various colors and patterns.

        Returns:
            LEDBuildingConfig for Duke Energy Center
        """
        zones = []

        # Create zones for each facade direction
        directions = ["north", "south", "east", "west"]

        for direction in directions:
            # Each direction has zones per 8-floor section
            for floor_section in range(6):  # 6 sections of 8 floors
                floor_start = floor_section * 8
                floor_end = min((floor_section + 1) * 8 - 1, 47)

                zone = LEDZone(
                    name=f"{direction}_floors_{floor_start}_{floor_end}",
                    floor_start=floor_start,
                    floor_end=floor_end,
                    position=direction,
                    led_count=100,  # ~100 LEDs per zone
                    current_color=LEDColor.WHITE.value,
                    brightness=1.0,
                )
                zones.append(zone)

        # Crown zone (top architectural feature)
        zones.append(LEDZone(
            name="crown",
            floor_start=47,
            floor_end=48,
            position="crown",
            led_count=200,
            current_color=LEDColor.WHITE.value,
            brightness=1.2,  # Slightly brighter
        ))

        config = LEDBuildingConfig(
            building_name=self.DUKE_ENERGY_SPEC["name"],
            building_type="duke_energy",
            total_leds=self.DUKE_ENERGY_SPEC["led_count"],
            floors=self.DUKE_ENERGY_SPEC["floors"],
            zones=zones,
            has_crown_lighting=True,
        )

        self.buildings["duke_energy_center"] = config
        return config

    def create_boa_center_facade(self) -> LEDBuildingConfig:
        """
        Create Bank of America Corporate Center lighting.

        The BOA Center features a distinctive granite crown with
        accent lighting rather than full LED facade.

        Returns:
            LEDBuildingConfig for Bank of America Corporate Center
        """
        zones = []

        # Crown lighting (main feature)
        zones.append(LEDZone(
            name="crown",
            floor_start=55,
            floor_end=60,
            position="crown",
            led_count=150,
            current_color=LEDColor.WHITE.value,
            brightness=0.8,
        ))

        # Accent lighting on corners
        for direction in ["north", "south", "east", "west"]:
            zones.append(LEDZone(
                name=f"corner_{direction}",
                floor_start=0,
                floor_end=60,
                position=direction,
                led_count=50,
                current_color=LEDColor.WHITE.value,
                brightness=0.6,
            ))

        config = LEDBuildingConfig(
            building_name=self.BOA_CENTER_SPEC["name"],
            building_type="boa_center",
            total_leds=350,
            floors=self.BOA_CENTER_SPEC["floors"],
            zones=zones,
            has_crown_lighting=True,
        )

        self.buildings["boa_center"] = config
        return config

    def create_truist_center_facade(self) -> LEDBuildingConfig:
        """
        Create Truist Center (Hearst Tower) lighting.

        Art-deco design with architectural accent lighting.

        Returns:
            LEDBuildingConfig for Truist Center
        """
        zones = []

        # Art-deco style accent zones
        for floor_section in range(4):
            floor_start = floor_section * 12
            floor_end = min((floor_section + 1) * 12 - 1, 45)

            for direction in ["north", "south"]:
                zone = LEDZone(
                    name=f"{direction}_floors_{floor_start}_{floor_end}",
                    floor_start=floor_start,
                    floor_end=floor_end,
                    position=direction,
                    led_count=60,
                    current_color=LEDColor.WHITE.value,
                    brightness=0.7,
                )
                zones.append(zone)

        config = LEDBuildingConfig(
            building_name=self.TRUIST_CENTER_SPEC["name"],
            building_type="truist",
            total_leds=500,
            floors=self.TRUIST_CENTER_SPEC["floors"],
            zones=zones,
        )

        self.buildings["truist_center"] = config
        return config

    def create_wells_fargo_one_facade(self) -> LEDBuildingConfig:
        """
        Create One Wells Fargo Center lighting ("The Jukebox").

        Features distinctive rounded crown and participates in
        city-wide lighting events.

        Returns:
            LEDBuildingConfig for One Wells Fargo Center
        """
        zones = []

        # Rounded crown lighting (signature feature)
        zones.append(LEDZone(
            name="rounded_crown",
            floor_start=38,
            floor_end=42,
            position="crown",
            led_count=200,
            current_color=LEDColor.WHITE.value,
            brightness=1.0,
        ))

        # Vertical accent strips
        for direction in ["north", "south", "east", "west"]:
            zones.append(LEDZone(
                name=f"accent_{direction}",
                floor_start=0,
                floor_end=42,
                position=direction,
                led_count=80,
                current_color=LEDColor.WHITE.value,
                brightness=0.7,
            ))

        config = LEDBuildingConfig(
            building_name=self.WELLS_FARGO_ONE_SPEC["name"],
            building_type="wells_fargo_one",
            total_leds=520,
            floors=self.WELLS_FARGO_ONE_SPEC["floors"],
            zones=zones,
            has_crown_lighting=True,
        )

        self.buildings["wells_fargo_one"] = config
        return config

    def create_fnb_tower_facade(self) -> LEDBuildingConfig:
        """
        Create FNB Tower LED facade.

        Modern tower completed 2021 with contemporary LED lighting.

        Returns:
            LEDBuildingConfig for FNB Tower
        """
        zones = []

        # Full facade LED system (modern building)
        for direction in ["north", "south", "east", "west"]:
            for floor_section in range(5):  # 5 sections of 5 floors
                floor_start = floor_section * 5
                floor_end = min((floor_section + 1) * 5 - 1, 24)

                zone = LEDZone(
                    name=f"{direction}_floors_{floor_start}_{floor_end}",
                    floor_start=floor_start,
                    floor_end=floor_end,
                    position=direction,
                    led_count=60,
                    current_color=LEDColor.WHITE.value,
                    brightness=0.9,
                )
                zones.append(zone)

        # Crown accent
        zones.append(LEDZone(
            name="crown",
            floor_start=23,
            floor_end=25,
            position="crown",
            led_count=100,
            current_color=LEDColor.WHITE.value,
            brightness=1.1,
        ))

        config = LEDBuildingConfig(
            building_name=self.FNB_TOWER_SPEC["name"],
            building_type="fnb_tower",
            total_leds=1300,
            floors=self.FNB_TOWER_SPEC["floors"],
            zones=zones,
            has_crown_lighting=True,
        )

        self.buildings["fnb_tower"] = config
        return config

    def create_honeywell_tower_facade(self) -> LEDBuildingConfig:
        """
        Create Honeywell Tower LED facade.

        Headquarters building completed 2021 with modern LED lighting.

        Returns:
            LEDBuildingConfig for Honeywell Tower
        """
        zones = []

        # Contemporary LED strips
        for direction in ["north", "south", "east", "west"]:
            zones.append(LEDZone(
                name=f"{direction}_full",
                floor_start=0,
                floor_end=22,
                position=direction,
                led_count=120,
                current_color=LEDColor.WHITE.value,
                brightness=0.85,
            ))

        # Rooftop accent
        zones.append(LEDZone(
            name="rooftop",
            floor_start=21,
            floor_end=23,
            position="crown",
            led_count=80,
            current_color=LEDColor.WHITE.value,
            brightness=1.0,
        ))

        config = LEDBuildingConfig(
            building_name=self.HONEYWELL_TOWER_SPEC["name"],
            building_type="honeywell_tower",
            total_leds=560,
            floors=self.HONEYWELL_TOWER_SPEC["floors"],
            zones=zones,
            has_crown_lighting=True,
        )

        self.buildings["honeywell_tower"] = config
        return config

    def create_ally_center_facade(self) -> LEDBuildingConfig:
        """
        Create Ally Charlotte Center LED facade.

        Modern illuminated facade building.

        Returns:
            LEDBuildingConfig for Ally Charlotte Center
        """
        zones = []

        # Modern grid LED system
        for direction in ["north", "south", "east", "west"]:
            for floor_section in range(4):
                floor_start = floor_section * 7
                floor_end = min((floor_section + 1) * 7 - 1, 25)

                zone = LEDZone(
                    name=f"{direction}_floors_{floor_start}_{floor_end}",
                    floor_start=floor_start,
                    floor_end=floor_end,
                    position=direction,
                    led_count=50,
                    current_color=LEDColor.WHITE.value,
                    brightness=0.8,
                )
                zones.append(zone)

        config = LEDBuildingConfig(
            building_name=self.ALLY_CENTER_SPEC["name"],
            building_type="ally_center",
            total_leds=800,
            floors=self.ALLY_CENTER_SPEC["floors"],
            zones=zones,
        )

        self.buildings["ally_center"] = config
        return config

    def create_carillon_tower_facade(self) -> LEDBuildingConfig:
        """
        Create Carillon Tower LED lighting.

        Neo-gothic bell tower with spire accent lighting.

        Returns:
            LEDBuildingConfig for Carillon Tower
        """
        zones = []

        # Spire lighting (main feature)
        zones.append(LEDZone(
            name="spire",
            floor_start=20,
            floor_end=24,
            position="spire",
            led_count=150,
            current_color=LEDColor.WHITE.value,
            brightness=1.2,
        ))

        # Corner accent lighting
        for direction in ["north", "south", "east", "west"]:
            zones.append(LEDZone(
                name=f"corner_{direction}",
                floor_start=0,
                floor_end=24,
                position=direction,
                led_count=40,
                current_color=LEDColor.WHITE.value,
                brightness=0.6,
            ))

        config = LEDBuildingConfig(
            building_name=self.CARILLON_TOWER_SPEC["name"],
            building_type="carillon_tower",
            total_leds=310,
            floors=self.CARILLON_TOWER_SPEC["floors"],
            zones=zones,
            has_spire_lighting=True,
        )

        self.buildings["carillon_tower"] = config
        return config

    def create_nascar_hof_facade(self) -> LEDBuildingConfig:
        """
        Create NASCAR Hall of Fame LED facade.

        Distinctive curved illuminated ribbon design.

        Returns:
            LEDBuildingConfig for NASCAR Hall of Fame
        """
        zones = []

        # Curved ribbon LED (signature feature)
        zones.append(LEDZone(
            name="ribbon_curved",
            floor_start=0,
            floor_end=5,
            position="north",
            led_count=500,  # Long curved LED strip
            current_color=LEDColor.WHITE.value,
            brightness=1.5,
            animation=LEDAnimationType.CHASE,
        ))

        # Building accent
        for direction in ["south", "east", "west"]:
            zones.append(LEDZone(
                name=f"accent_{direction}",
                floor_start=0,
                floor_end=5,
                position=direction,
                led_count=100,
                current_color=LEDColor.WHITE.value,
                brightness=0.8,
            ))

        config = LEDBuildingConfig(
            building_name=self.NASCAR_HOF_SPEC["name"],
            building_type="nascar_hof",
            total_leds=800,
            floors=self.NASCAR_HOF_SPEC["floors"],
            zones=zones,
        )

        self.buildings["nascar_hof"] = config
        return config

    def create_south_tryon_200_facade(self) -> LEDBuildingConfig:
        """
        Create 200 South Tryon LED facade.

        Glass curtain wall with accent lighting.

        Returns:
            LEDBuildingConfig for 200 South Tryon
        """
        zones = []

        # Curtain wall accent
        for direction in ["north", "south", "east", "west"]:
            zones.append(LEDZone(
                name=f"{direction}_full",
                floor_start=0,
                floor_end=33,
                position=direction,
                led_count=100,
                current_color=LEDColor.WHITE.value,
                brightness=0.75,
            ))

        # Crown lighting
        zones.append(LEDZone(
            name="crown",
            floor_start=30,
            floor_end=34,
            position="crown",
            led_count=80,
            current_color=LEDColor.WHITE.value,
            brightness=1.0,
        ))

        config = LEDBuildingConfig(
            building_name=self.SOUTH_TRYON_200_SPEC["name"],
            building_type="south_tryon_200",
            total_leds=480,
            floors=self.SOUTH_TRYON_200_SPEC["floors"],
            zones=zones,
            has_crown_lighting=True,
        )

        self.buildings["south_tryon_200"] = config
        return config

    def create_all_charlotte_led_facades(self) -> Dict[str, LEDBuildingConfig]:
        """
        Create all Charlotte buildings with LED/illuminated facades.

        Returns:
            Dictionary of building ID to LEDBuildingConfig for all LED buildings
        """
        # Create all buildings
        self.create_duke_energy_facade()
        self.create_boa_center_facade()
        self.create_truist_center_facade()
        self.create_wells_fargo_one_facade()
        self.create_fnb_tower_facade()
        self.create_honeywell_tower_facade()
        self.create_ally_center_facade()
        self.create_carillon_tower_facade()
        self.create_nascar_hof_facade()
        self.create_south_tryon_200_facade()

        return self.buildings

    def set_panthers_mode_all(self):
        """Set all LED buildings to Panthers blue."""
        for config in self.buildings.values():
            LEDAnimator.apply_preset_panthers(config)

    def set_holiday_mode_all(self, holiday: str):
        """
        Set all LED buildings to holiday colors.

        Args:
            holiday: "christmas", "halloween", "valentines", "july_4"
        """
        for config in self.buildings.values():
            if holiday == "christmas":
                LEDAnimator.apply_preset_christmas(config)
            elif holiday == "halloween":
                LEDAnimator.apply_preset_halloween(config)
            elif holiday == "valentines":
                LEDAnimator.apply_preset_valentines(config)
            elif holiday == "july_4":
                for zone in config.zones:
                    zone.current_color = LEDColor.INDEPENDENCE_BLUE.value

    def create_generic_led_facade(
        self,
        name: str,
        floors: int,
        led_density: float = 0.5,
    ) -> LEDBuildingConfig:
        """
        Create a generic LED facade for a building.

        Args:
            name: Building name
            floors: Number of floors
            led_density: LED density (0.0-1.0)

        Returns:
            LEDBuildingConfig for generic building
        """
        zones = []
        led_per_floor = int(20 * led_density)

        # Create simple zones per direction
        for direction in ["north", "south", "east", "west"]:
            zone = LEDZone(
                name=f"{direction}_full",
                floor_start=0,
                floor_end=floors - 1,
                position=direction,
                led_count=led_per_floor * floors,
                current_color=LEDColor.WHITE.value,
                brightness=0.8,
            )
            zones.append(zone)

        config = LEDBuildingConfig(
            building_name=name,
            building_type="generic",
            total_leds=led_per_floor * floors * 4,
            floors=floors,
            zones=zones,
        )

        self.buildings[name.lower().replace(" ", "_")] = config
        return config


class LEDMaterialBuilder:
    """Creates Blender materials for LED facades."""

    @staticmethod
    def create_led_emission_material(
        name: str,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        strength: float = 10.0,
    ) -> Any:
        """
        Create an emissive material for LED panels.

        Args:
            name: Material name
            color: RGB color (0-1 range)
            strength: Emission strength

        Returns:
            Blender material object
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create or get material
        mat = bpy.data.materials.get(name)
        if mat:
            return mat

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create nodes
        output = nodes.new('ShaderNodeOutputMaterial')
        emission = nodes.new('ShaderNodeEmission')

        # Set emission properties
        emission.inputs['Color'].default_value = (*color, 1.0)
        emission.inputs['Strength'].default_value = strength

        # Link nodes
        links.new(emission.outputs['Emission'], output.inputs['Surface'])

        # Position nodes
        output.location = (300, 0)
        emission.location = (0, 0)

        return mat

    @staticmethod
    def create_led_panel_material(
        name: str,
        base_color: Tuple[float, float, float] = (0.1, 0.1, 0.1),
        emission_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        emission_strength: float = 5.0,
        mix_factor: float = 0.5,
    ) -> Any:
        """
        Create a mixed material with glass/panel base and LED emission.

        This simulates LED panels embedded in a glass curtain wall.

        Args:
            name: Material name
            base_color: Base panel color
            emission_color: LED emission color
            emission_strength: LED brightness
            mix_factor: Mix between base and emission (0-1)

        Returns:
            Blender material object
        """
        if not BLENDER_AVAILABLE:
            return None

        mat = bpy.data.materials.get(name)
        if mat:
            return mat

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        nodes.clear()

        # Create node network
        output = nodes.new('ShaderNodeOutputMaterial')
        mix_shader = nodes.new('ShaderNodeMixShader')
        glass = nodes.new('ShaderNodeBsdfGlass')
        emission = nodes.new('ShaderNodeEmission')
        fresnel = nodes.new('ShaderNodeFresnel')
        math = nodes.new('ShaderNodeMath')

        # Configure glass
        glass.inputs['Color'].default_value = (*base_color, 1.0)
        glass.inputs['Roughness'].default_value = 0.1
        glass.inputs['IOR'].default_value = 1.45

        # Configure emission
        emission.inputs['Color'].default_value = (*emission_color, 1.0)
        emission.inputs['Strength'].default_value = emission_strength

        # Configure fresnel mix
        math.operation = 'MULTIPLY'
        math.inputs[1].default_value = mix_factor

        # Link nodes
        links.new(fresnel.outputs['Fac'], math.inputs[0])
        links.new(math.outputs['Value'], mix_shader.inputs['Fac'])
        links.new(glass.outputs['BSDF'], mix_shader.inputs[1])
        links.new(emission.outputs['Emission'], mix_shader.inputs[2])
        links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

        # Position nodes
        output.location = (600, 0)
        mix_shader.location = (300, 0)
        glass.location = (0, 100)
        emission.location = (0, -100)
        fresnel.location = (-200, 0)
        math.location = (-200, -200)

        return mat


class LEDAnimator:
    """Animates LED facade systems."""

    @staticmethod
    def set_zone_color(zone: LEDZone, color: Tuple[float, float, float]):
        """Set a zone's color."""
        zone.current_color = color

    @staticmethod
    def apply_preset_panthers(config: LEDBuildingConfig):
        """
        Apply Carolina Panthers colors to a building.

        Duke Energy Center lights blue for Panthers touchdowns.
        """
        for zone in config.zones:
            zone.current_color = LEDColor.PANTHERS_BLUE.value
            zone.brightness = 1.2

    @staticmethod
    def apply_preset_christmas(config: LEDBuildingConfig):
        """Apply Christmas colors (alternating red/green)."""
        for i, zone in enumerate(config.zones):
            if i % 2 == 0:
                zone.current_color = LEDColor.CHRISTMAS_RED.value
            else:
                zone.current_color = LEDColor.CHRISTMAS_GREEN.value
            zone.brightness = 1.0

    @staticmethod
    def apply_preset_halloween(config: LEDBuildingConfig):
        """Apply Halloween colors (orange/purple)."""
        for i, zone in enumerate(config.zones):
            if i % 2 == 0:
                zone.current_color = LEDColor.HALLOWEEN_ORANGE.value
            else:
                zone.current_color = LEDColor.HALLOWEEN_PURPLE.value

    @staticmethod
    def apply_preset_valentines(config: LEDBuildingConfig):
        """Apply Valentine's Day colors."""
        for zone in config.zones:
            zone.current_color = LEDColor.VALENTINES_RED.value
            zone.brightness = 0.9

    @staticmethod
    def apply_wave_animation(config: LEDBuildingConfig, time: float):
        """
        Apply wave animation pattern.

        Args:
            config: Building configuration
            time: Current time (seconds)
        """
        for i, zone in enumerate(config.zones):
            # Calculate wave offset
            wave = math.sin(time * 2 + i * 0.5) * 0.5 + 0.5
            zone.brightness = 0.5 + wave * 0.5

    @staticmethod
    def apply_chase_animation(config: LEDBuildingConfig, time: float):
        """
        Apply chase animation pattern.

        Args:
            config: Building configuration
            time: Current time (seconds)
        """
        active_zone = int(time * 2) % len(config.zones)

        for i, zone in enumerate(config.zones):
            if i == active_zone:
                zone.brightness = 1.2
            else:
                zone.brightness = 0.3

    @staticmethod
    def apply_breathe_animation(config: LEDBuildingConfig, time: float):
        """
        Apply breathing animation pattern.

        Args:
            config: Building configuration
            time: Current time (seconds)
        """
        # Smooth sine wave for breathing effect
        breathe = math.sin(time * 1.5) * 0.4 + 0.6

        for zone in config.zones:
            zone.brightness = breathe


def create_duke_energy_center_leds() -> LEDBuildingConfig:
    """
    Convenience function to create Duke Energy Center LED facade.

    Returns:
        LEDBuildingConfig configured for Duke Energy Center
    """
    builder = LEDFacadeBuilder()
    return builder.create_duke_energy_facade()


def create_all_charlotte_led_buildings() -> Dict[str, LEDBuildingConfig]:
    """
    Create all Charlotte LED buildings.

    Charlotte has multiple buildings with LED/illuminated facades that
    participate in city-wide coordinated lighting events:

    Primary LED Buildings:
    - Duke Energy Center (550 S Tryon): ~2,500 programmable LEDs
    - Bank of America Corporate Center: Crown/accent lighting
    - Truist Center: Architectural accent lighting
    - One Wells Fargo Center: Rounded crown ("The Jukebox")
    - FNB Tower: Modern LED facade (2021)
    - Honeywell Tower: Contemporary LED (2021)
    - Ally Charlotte Center: Modern illuminated facade
    - Carillon Tower: Neo-gothic spire lighting
    - NASCAR Hall of Fame: Curved LED ribbon
    - 200 South Tryon: Curtain wall accent

    Returns:
        Dictionary of building ID to LEDBuildingConfig
    """
    builder = LEDFacadeBuilder()
    return builder.create_all_charlotte_led_facades()


def setup_charlotte_night_scene():
    """
    Set up a complete Charlotte night scene with LED buildings.

    Creates all major LED buildings and applies default night lighting.
    """
    if not BLENDER_AVAILABLE:
        return None

    # Create buildings
    buildings = create_all_charlotte_led_buildings()

    # Create materials for each building
    material_builder = LEDMaterialBuilder()

    for name, config in buildings.items():
        # Create LED panel material for each building
        mat = material_builder.create_led_panel_material(
            name=f"led_{name}",
            emission_color=config.default_color,
            emission_strength=3.0,
        )

    return buildings


# Preset schedules for Duke Energy Center
DUKE_ENERGY_SCHEDULE = {
    "default": {
        "color": LEDColor.WHITE.value,
        "hours": "sundown-midnight",
        "description": "Standard white lighting"
    },
    "panthers_game": {
        "color": LEDColor.PANTHERS_BLUE.value,
        "description": "Panthers game day / touchdown"
    },
    "christmas": {
        "color": "alternating",
        "colors": [LEDColor.CHRISTMAS_RED.value, LEDColor.CHRISTMAS_GREEN.value],
        "dates": "Dec 1-25",
        "description": "Christmas holiday lights"
    },
    "new_year": {
        "color": LEDColor.GOLD.value,
        "description": "New Year celebration"
    },
    "valentines": {
        "color": LEDColor.VALENTINES_RED.value,
        "dates": "Feb 14",
        "description": "Valentine's Day"
    },
    "halloween": {
        "color": "alternating",
        "colors": [LEDColor.HALLOWEEN_ORANGE.value, LEDColor.HALLOWEEN_PURPLE.value],
        "dates": "Oct 31",
        "description": "Halloween"
    },
    "july_4": {
        "color": LEDColor.INDEPENDENCE_BLUE.value,
        "dates": "July 4",
        "description": "Independence Day"
    },
}
