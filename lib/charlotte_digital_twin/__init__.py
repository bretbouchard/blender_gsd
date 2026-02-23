"""
Charlotte NC Digital Twin Module

Comprehensive system for creating a digital twin of Charlotte, NC including:
- Road network data acquisition and processing
- Building and POI extraction
- Elevation/terrain data integration
- Traffic flow data import
- Material and geometry generation
- Photorealistic rendering (materials, lighting, weather)

Based on research in .planning/RESEARCH_CHARLOTTE_DIGITAL_TWIN.md

Usage:
    from lib.charlotte_digital_twin import (
        # Data Acquisition
        OSMDownloader,
        OverpassClient,
        ElevationFetcher,

        # Geometry & Materials
        LaneMarkingGenerator,
        AsphaltMaterialBuilder,

        # Lighting
        HDRISetup,
        ProceduralSky,
        setup_realistic_lighting,

        # Infrastructure
        BarrierGenerator,
        BridgeGenerator,
        SignageGenerator,
        LightPoleGenerator,

        # Environment
        TreeGenerator,
        GrassSystem,
        TerrainSystem,

        # Buildings
        BuildingExtractor,
        BuildingGenerator,
        BuildingMaterialBuilder,

        # Vehicles
        HeroCarBuilder,
        CarAnimationSystem,

        # Effects
        TimeOfDaySystem,
        WeatherSystem,
    )

    # Download Charlotte data
    downloader = OSMDownloader()
    osm_path = downloader.get_charlotte_extract()

    # Setup lighting
    setup_realistic_lighting()

    # Create hero car
    car = HeroCarBuilder().create_car(CarType.MUSCLE)
"""

__version__ = "0.1.0"
__author__ = "Bret Bouchard"

# Charlotte bounding box (approximate)
CHARLOTTE_BBOX = {
    "north": 35.4,
    "south": 35.0,
    "east": -80.5,
    "west": -80.9,
}

# Charlotte center point
CHARLOTTE_CENTER = {
    "lat": 35.2271,
    "lon": -80.8431,
}

# Major highways
CHARLOTTE_HIGHWAYS = {
    "I-77": {"name": "Interstate 77", "direction": "N-S", "aadtl": 150000},
    "I-85": {"name": "Interstate 85", "direction": "NE-SW", "aadtl": 140000},
    "I-277": {"name": "Interstate 277", "direction": "Loop", "aadtl": 80000},
    "I-485": {"name": "Interstate 485", "direction": "Beltway", "aadtl": 100000},
}

# Major buildings
CHARLOTTE_BUILDINGS = {
    "bank_of_america_center": {
        "name": "Bank of America Corporate Center",
        "height_m": 312,
        "floors": 60,
        "lat": 35.2276,
        "lon": -80.8436,
    },
    "duke_energy_center": {
        "name": "Duke Energy Center",
        "height_m": 240,
        "floors": 48,
        "lat": 35.2267,
        "lon": -80.8467,
    },
    "wells_fargo_capital": {
        "name": "Wells Fargo Capital Center",
        "height_m": 176,
        "floors": 42,
        "lat": 35.2282,
        "lon": -80.8424,
    },
    "truist_center": {
        "name": "Truist Center",
        "height_m": 150,
        "floors": 36,
        "lat": 35.2252,
        "lon": -80.8401,
    },
    "bank_of_america_stadium": {
        "name": "Bank of America Stadium",
        "height_m": 60,
        "type": "stadium",
        "lat": 35.2258,
        "lon": -80.8533,
    },
}

# Data paths
from pathlib import Path
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "charlotte"
CACHE_DIR = DATA_DIR / "cache"
OSM_DIR = DATA_DIR / "osm"
ELEVATION_DIR = DATA_DIR / "elevation"
TRAFFIC_DIR = DATA_DIR / "traffic"
POI_DIR = DATA_DIR / "poi"

# Ensure directories exist
for d in [DATA_DIR, CACHE_DIR, OSM_DIR, ELEVATION_DIR, TRAFFIC_DIR, POI_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Data Acquisition
from .data_acquisition.base_client import DataClient, RateLimitedClient
from .data_acquisition.osm_downloader import OSMDownloader
from .data_acquisition.overpass_client import OverpassClient
from .data_acquisition.elevation_fetcher import ElevationFetcher
from .data_acquisition.poi_extractor import POIExtractor

# Geometry - Lane Markings
from .geometry.lane_markings import (
    MarkingType,
    MarkingColor,
    MarkingConfig,
    LaneMarkingGenerator,
    generate_highway_markings,
)

# Lighting
from .lighting import (
    HDRISetup,
    HDRIPreset,
    ProceduralSky,
    TimeOfDay as SkyTimeOfDay,
    AtmosphericEffects,
    setup_realistic_lighting,
    setup_charlotte_afternoon,
    setup_charlotte_golden_hour,
)

# Infrastructure
from .infrastructure import (
    BarrierGenerator,
    BridgeGenerator,
    SignageGenerator,
    LightPoleGenerator,
    place_lights_along_road,
)

# Environment
from .environment import (
    TreeGenerator,
    TreeSpecies,
    GrassSystem,
    GrassType,
    TerrainSystem,
    create_charlotte_terrain,
    place_trees_along_road,
)

# Buildings
from .buildings import (
    BuildingExtractor,
    BuildingGenerator,
    BuildingType,
    BuildingMaterialBuilder,
    create_facade_material,
    # LED Facade
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
    # Charlotte Skyline
    CharlotteBuilding,
    BuildingSpec,
    CHARLOTTE_BUILDING_SPECS,
    CharlotteSkylineBuilder,
    create_duke_energy_center,
    create_charlotte_skyline,
    setup_charlotte_night_render,
)

# Vehicles
from .vehicles import (
    HeroCarBuilder,
    CarType,
    CarAnimationSystem,
    AnimationStyle,
    create_hero_car,
    animate_car_chase,
)

# Effects
from .effects import (
    TimeOfDaySystem,
    TimeOfDay as TODTimeOfDay,
    WeatherSystem,
    WeatherType,
    set_scene_time,
    apply_rain_to_scene,
)

__all__ = [
    # Constants
    "__version__",
    "CHARLOTTE_BBOX",
    "CHARLOTTE_CENTER",
    "CHARLOTTE_HIGHWAYS",
    "CHARLOTTE_BUILDINGS",
    "DATA_DIR",
    "CACHE_DIR",

    # Base classes
    "DataClient",
    "RateLimitedClient",

    # Data Acquisition
    "OSMDownloader",
    "OverpassClient",
    "ElevationFetcher",
    "POIExtractor",

    # Geometry
    "MarkingType",
    "MarkingColor",
    "MarkingConfig",
    "LaneMarkingGenerator",
    "generate_highway_markings",

    # Lighting
    "HDRISetup",
    "HDRIPreset",
    "ProceduralSky",
    "SkyTimeOfDay",
    "AtmosphericEffects",
    "setup_realistic_lighting",
    "setup_charlotte_afternoon",
    "setup_charlotte_golden_hour",

    # Infrastructure
    "BarrierGenerator",
    "BridgeGenerator",
    "SignageGenerator",
    "LightPoleGenerator",
    "place_lights_along_road",

    # Environment
    "TreeGenerator",
    "TreeSpecies",
    "GrassSystem",
    "GrassType",
    "TerrainSystem",
    "create_charlotte_terrain",
    "place_trees_along_road",

    # Buildings
    "BuildingExtractor",
    "BuildingGenerator",
    "BuildingType",
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

    # Vehicles
    "HeroCarBuilder",
    "CarType",
    "CarAnimationSystem",
    "AnimationStyle",
    "create_hero_car",
    "animate_car_chase",

    # Effects
    "TimeOfDaySystem",
    "TODTimeOfDay",
    "WeatherSystem",
    "WeatherType",
    "set_scene_time",
    "apply_rain_to_scene",
]
