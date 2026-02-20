"""
City Environment System - Complete System

A comprehensive city generation and traffic simulation system for Blender 5.x.
From procedural roads to high-speed car chases with camera systems.

## Phases

**Phase 1: Geo Data Bridge**
- GeoDataBridge: Import real-world location data
- BlenderGIS integration for OSM data
- Terrain generation from elevation data
- Coordinate system transformations

**Phase 2: Road Network**
- RoadNetwork: Procedural road generation
- LaneSystem: Multi-lane roads with markings
- IntersectionHandler: Traffic lights, turn lanes
- BridgeGenerator: Overpasses, underpasses

**Phase 3: Buildings**
- BuildingGenerator: Procedural skyscrapers and structures
- BuildingVariator: Style diversity within city
- DowntownCore: High-density urban areas
- SuburbanSprawl: Residential neighborhoods

**Phase 4: Street Elements**
- StreetLightSystem: Roadside lighting
- SignGenerator: Traffic signs, billboards
- BannerSystem: Street banners, decorations
- UtilityPoles: Power lines, street furniture

**Phase 5: Traffic AI**
- TrafficController: Traffic flow management
- VehicleAgent: AI-driven vehicle behavior
- LaneFollowing: Stay in lane, change lanes
- AvoidanceSystem: Obstacle and chase avoidance

**Phase 6: Chase Coordinator**
- ChaseDirector: Orchestrate chase sequences
- PathPlanner: Route through city
- CrashPointSystem: Scripted collision points
- FollowerController: Pursuit vehicles

**Phase 7: Camera Systems**
- ChaseCamera: Dynamic follow cameras
- AerialCamera: Drone/helicopter shots
- InCarCamera: Dashboard/POV shots
- StaticCamera: Fixed position coverage

## Quick Start

```python
# Import Charlotte, NC geo data
from lib.animation.city import GeoDataBridge, create_city_from_geo
city = create_city_from_geo(
    location="Charlotte, NC",
    bbox=(-80.92, 35.14, -80.68, 35.32),  # South, West, North, East
    detail_level="full"
)

# Generate road network
from lib.animation.city import RoadNetwork, create_road_network
roads = create_road_network(city, lanes=4, style="urban")

# Add buildings
from lib.animation.city import BuildingGenerator, generate_downtown
buildings = generate_downtown(city, height_range=(50, 300), density=0.8)

# Setup traffic
from lib.animation.city import TrafficController, setup_traffic
traffic = setup_traffic(roads, vehicle_count=100, style="urban")

# Create chase sequence
from lib.animation.city import ChaseDirector, create_chase
chase = create_chase(
    path=roads.get_route(start="Uptown", end="Airport"),
    hero_car=hero,
    pursuit_count=3,
    crash_points=[("Trade & Tryon", 0.3), ("I-77 Exit", 0.7)]
)

# Setup cameras
from lib.animation.city import ChaseCamera, setup_chase_cameras
cameras = setup_chase_cameras(chase, types=["follow", "aerial", "in_car", "static"])
```
"""

# Phase 1: Geo Data
from .geo_data import (
    GeoDataBridge,
    GeoBoundingBox,
    GeoLocation,
    TerrainData,
    OSMData,
    import_osm_data,
    import_terrain,
    geocode_location,
    GEO_PRESETS,
)

# Phase 2: Road Network
from .road_network import (
    RoadNetwork,
    RoadSegment,
    LaneConfig,
    Intersection,
    BridgeType,
    RoadStyle,
    create_road_network,
    create_road_segment,
    ROAD_PRESETS,
)

# Phase 3: Buildings
from .buildings import (
    BuildingGenerator,
    BuildingConfig,
    BuildingStyle,
    SkyscraperConfig,
    create_building,
    generate_downtown,
    generate_neighborhood,
    BUILDING_PRESETS,
)

# Phase 4: Street Elements
from .street_elements import (
    StreetLightSystem,
    SignGenerator,
    BannerSystem,
    UtilitySystem,
    StreetLightConfig,
    SignConfig,
    create_street_lights,
    create_signs,
    STREET_ELEMENT_PRESETS,
)

# Phase 5: Traffic AI
from .traffic_ai import (
    TrafficController,
    VehicleAgent,
    LaneFollowing,
    AvoidanceSystem,
    TrafficConfig,
    AgentState,
    setup_traffic,
    TRAFFIC_PRESETS,
)

# Phase 6: Chase Coordinator
from .chase_coordinator import (
    ChaseDirector,
    PathPlanner,
    CrashPointSystem,
    FollowerController,
    ChaseConfig,
    ChaseState,
    CrashPoint,
    create_chase,
    CHASE_PRESETS,
)

# Phase 7: Camera Systems
from .chase_cameras import (
    ChaseCameraSystem,
    FollowCamera,
    AerialCamera,
    InCarCamera,
    StaticCamera,
    CameraConfig,
    CameraType,
    setup_chase_cameras,
    CAMERA_PRESETS,
)

# Orchestrator
from .city_builder import (
    CityBuilder,
    CityConfig,
    CITY_PRESETS as BUILDER_PRESETS,
    create_city,
)

# Runtime Systems
from .traffic_animator import (
    TrafficAnimator,
    TrafficScene,
    AnimatedVehicle,
    start_traffic_animation,
    stop_traffic_animation,
)

from .osm_importer import (
    OSMCityImporter,
    ImportedCity,
    import_charlotte,
    import_location,
    create_city_from_osm,
    CHARLOTTE_PRESETS,
)

from .render_pipeline import (
    ChaseRenderPipeline,
    RenderConfig,
    RenderQueue,
    RENDER_PRESETS,
    quick_render,
    render_chase,
    create_playblast,
)


__all__ = [
    # === PHASE 1: GEO DATA ===
    'GeoDataBridge',
    'GeoBoundingBox',
    'GeoLocation',
    'TerrainData',
    'OSMData',
    'import_osm_data',
    'import_terrain',
    'geocode_location',
    'GEO_PRESETS',

    # === PHASE 2: ROAD NETWORK ===
    'RoadNetwork',
    'RoadSegment',
    'LaneConfig',
    'Intersection',
    'BridgeType',
    'RoadStyle',
    'create_road_network',
    'create_road_segment',
    'ROAD_PRESETS',

    # === PHASE 3: BUILDINGS ===
    'BuildingGenerator',
    'BuildingConfig',
    'BuildingStyle',
    'SkyscraperConfig',
    'create_building',
    'generate_downtown',
    'generate_neighborhood',
    'BUILDING_PRESETS',

    # === PHASE 4: STREET ELEMENTS ===
    'StreetLightSystem',
    'SignGenerator',
    'BannerSystem',
    'UtilitySystem',
    'StreetLightConfig',
    'SignConfig',
    'create_street_lights',
    'create_signs',
    'STREET_ELEMENT_PRESETS',

    # === PHASE 5: TRAFFIC AI ===
    'TrafficController',
    'VehicleAgent',
    'LaneFollowing',
    'AvoidanceSystem',
    'TrafficConfig',
    'AgentState',
    'setup_traffic',
    'TRAFFIC_PRESETS',

    # === PHASE 6: CHASE COORDINATOR ===
    'ChaseDirector',
    'PathPlanner',
    'CrashPointSystem',
    'FollowerController',
    'ChaseConfig',
    'ChaseState',
    'CrashPoint',
    'create_chase',
    'CHASE_PRESETS',

    # === PHASE 7: CAMERA SYSTEMS ===
    'ChaseCameraSystem',
    'FollowCamera',
    'AerialCamera',
    'InCarCamera',
    'StaticCamera',
    'CameraConfig',
    'CameraType',
    'setup_chase_cameras',
    'CAMERA_PRESETS',

    # === ORCHESTRATOR ===
    'CityBuilder',
    'CityConfig',
    'BUILDER_PRESETS',
    'create_city',

    # === RUNTIME SYSTEMS ===
    'TrafficAnimator',
    'TrafficScene',
    'AnimatedVehicle',
    'start_traffic_animation',
    'stop_traffic_animation',

    'OSMCityImporter',
    'ImportedCity',
    'import_charlotte',
    'import_location',
    'create_city_from_osm',
    'CHARLOTTE_PRESETS',

    'ChaseRenderPipeline',
    'RenderConfig',
    'RenderQueue',
    'RENDER_PRESETS',
    'quick_render',
    'render_chase',
    'create_playblast',
]
