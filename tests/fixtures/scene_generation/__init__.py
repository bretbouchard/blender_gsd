"""
Scene Generation Test Fixtures

Provides deterministic test data for BSP solver, L-system, and asset vault testing.
"""
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent

# Sample floor plan fixtures for BSP testing
FLOOR_PLAN_FIXTURES = [
    "sample_floor_plans.json",
]

# Sample road network fixtures for L-system testing
ROAD_NETWORK_FIXTURES = [
    "sample_road_networks.json",
]
