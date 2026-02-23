"""
Charlotte Digital Twin Buildings System

Building generation and materials:
- OSM building extraction
- Procedural building generation
- PBR building materials (glass, concrete, brick, metal)

Usage:
    from lib.charlotte_digital_twin.buildings import (
        BuildingExtractor,
        BuildingGenerator,
        BuildingMaterialBuilder,
    )

    # Extract buildings from OSM
    extractor = BuildingExtractor()
    footprints = extractor.parse_osm_file("charlotte.osm")

    # Generate 3D buildings
    generator = BuildingGenerator()
    for fp in footprints:
        generator.create_building(fp)

    # Create materials
    materials = BuildingMaterialBuilder()
    glass = materials.create_glass_material()
    concrete = materials.create_concrete_material()
"""

from .building_extraction import (
    BuildingType,
    BuildingFootprint,
    BuildingConfig,
    BUILDING_TYPE_COLORS,
    BuildingExtractor,
    BuildingGenerator,
    generate_buildings_from_osm,
    create_placeholder_building,
)

from .building_materials import (
    FacadeType,
    WindowType,
    RoofMaterial,
    GlassConfig,
    ConcreteConfig,
    BrickConfig,
    MetalConfig,
    GLASS_PRESETS,
    BuildingMaterialBuilder,
    create_facade_material,
)

from .led_facade import (
    LEDColor,
    LEDAnimationType,
    LEDZone,
    LEDBuildingConfig,
    LEDFacadeBuilder,
    LEDMaterialBuilder,
    LEDAnimator,
    create_duke_energy_center_leds,
    create_all_charlotte_led_buildings,
    setup_charlotte_night_scene,
    DUKE_ENERGY_SCHEDULE,
)

from .charlotte_skyline import (
    CharlotteBuilding,
    BuildingSpec,
    CHARLOTTE_BUILDING_SPECS,
    CharlotteSkylineBuilder,
    create_duke_energy_center,
    create_charlotte_skyline,
    setup_charlotte_night_render,
)

from .geojson_importer import (
    BuildingMaterialType,
    BuildingFootprint as GeoJSONBuildingFootprint,
    GeoJSONLoader,
    CoordinateConverter,
    CharlotteBuildingGenerator,
    BuildingMaterialGenerator,
    IntegratedCharlotteGenerator,
    generate_uptown_charlotte,
    generate_charlotte_led_buildings,
    generate_charlotte_tall_buildings,
    generate_charlotte_scene,
)

__version__ = "1.0.0"
__all__ = [
    # Extraction
    "BuildingType",
    "BuildingFootprint",
    "BuildingConfig",
    "BUILDING_TYPE_COLORS",
    "BuildingExtractor",
    "BuildingGenerator",
    "generate_buildings_from_osm",
    "create_placeholder_building",
    # Materials
    "FacadeType",
    "WindowType",
    "RoofMaterial",
    "GlassConfig",
    "ConcreteConfig",
    "BrickConfig",
    "MetalConfig",
    "GLASS_PRESETS",
    "BuildingMaterialBuilder",
    "create_facade_material",
    # LED Facade
    "LEDColor",
    "LEDAnimationType",
    "LEDZone",
    "LEDBuildingConfig",
    "LEDFacadeBuilder",
    "LEDMaterialBuilder",
    "LEDAnimator",
    "create_duke_energy_center_leds",
    "create_all_charlotte_led_buildings",
    "setup_charlotte_night_scene",
    "DUKE_ENERGY_SCHEDULE",
    # Charlotte Skyline
    "CharlotteBuilding",
    "BuildingSpec",
    "CHARLOTTE_BUILDING_SPECS",
    "CharlotteSkylineBuilder",
    "create_duke_energy_center",
    "create_charlotte_skyline",
    "setup_charlotte_night_render",
    # GeoJSON Importer
    "BuildingMaterialType",
    "GeoJSONBuildingFootprint",
    "GeoJSONLoader",
    "CoordinateConverter",
    "CharlotteBuildingGenerator",
    "BuildingMaterialGenerator",
    "IntegratedCharlotteGenerator",
    "generate_uptown_charlotte",
    "generate_charlotte_led_buildings",
    "generate_charlotte_tall_buildings",
    "generate_charlotte_scene",
]
