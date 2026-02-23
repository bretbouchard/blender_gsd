"""
Charlotte Digital Twin Data Module

Provides data acquisition and management for Charlotte buildings:

- OpenStreetMap (Overpass API) - building footprints, heights
- Microsoft Global ML Building Footprints
- Curated local database of Charlotte buildings
- CTBUH skyscraper data

Usage:
    from lib.charlotte_digital_twin.data import (
        CharlotteBuildingDataFetcher,
        CharlotteBuildingDatabase,
        get_charlotte_building_database,
        get_led_buildings,
    )

    # Get curated database
    db = get_charlotte_building_database()
    duke = db.get_building("duke_energy_center")

    # Get all LED buildings
    led_buildings = get_led_buildings()

    # Fetch from OSM
    fetcher = CharlotteBuildingDataFetcher()
    osm_buildings = fetcher.fetch_osm_buildings()
"""

from .building_data import (
    BuildingDataSource,
    BuildingData,
    CharlotteBuildingDataFetcher,
    CharlotteBuildingDatabase,
    get_charlotte_tall_buildings,
    get_charlotte_building_database,
    get_led_buildings,
    fetch_osm_buildings,
    load_cached_osm_buildings,
    get_named_osm_buildings,
    CHARLOTTE_BBOX,
    CHARLOTTE_UPTOWN_BBOX,
)

__version__ = "1.0.0"
__all__ = [
    # Classes
    "BuildingDataSource",
    "BuildingData",
    "CharlotteBuildingDataFetcher",
    "CharlotteBuildingDatabase",
    # Functions
    "get_charlotte_tall_buildings",
    "get_charlotte_building_database",
    "get_led_buildings",
    "fetch_osm_buildings",
    "load_cached_osm_buildings",
    "get_named_osm_buildings",
    # Constants
    "CHARLOTTE_BBOX",
    "CHARLOTTE_UPTOWN_BBOX",
]
