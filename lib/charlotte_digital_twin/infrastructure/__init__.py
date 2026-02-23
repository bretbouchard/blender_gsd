"""
Charlotte Digital Twin Infrastructure System

Highway infrastructure components:
- Road barriers (Jersey barriers, guardrails)
- Bridge supports and overpass structures
- Highway signage (exit signs, directional signs)
- Light poles and street lighting

Usage:
    from lib.charlotte_digital_twin.infrastructure import (
        BarrierGenerator,
        BridgeGenerator,
        SignageGenerator,
        LightPoleGenerator,
    )

    # Generate barriers along highway
    barriers = BarrierGenerator()
    barriers.generate_jersey_barriers(road_points, offset=5.0)

    # Generate bridge supports
    bridges = BridgeGenerator()
    bridges.generate_supports(bridge_segments)
"""

from .barriers import (
    BarrierType,
    BarrierConfig,
    BarrierGenerator,
    create_jersey_barrier,
    create_guardrail,
    place_barriers_along_road,
)

from .bridges import (
    BridgeType,
    BridgeSupportConfig,
    BridgeGenerator,
    create_support_column,
    generate_bridge_geometry,
)

from .signage import (
    SignType,
    SignConfig,
    SignageGenerator,
    create_exit_sign,
    create_overhead_gantry,
)

from .light_poles import (
    PoleType,
    LightPoleConfig,
    LightPoleGenerator,
    create_highway_light,
    place_lights_along_road,
)

__version__ = "1.0.0"
__all__ = [
    # Barriers
    "BarrierType",
    "BarrierConfig",
    "BarrierGenerator",
    "create_jersey_barrier",
    "create_guardrail",
    "place_barriers_along_road",
    # Bridges
    "BridgeType",
    "BridgeSupportConfig",
    "BridgeGenerator",
    "create_support_column",
    "generate_bridge_geometry",
    # Signage
    "SignType",
    "SignConfig",
    "SignageGenerator",
    "create_exit_sign",
    "create_overhead_gantry",
    # Light Poles
    "PoleType",
    "LightPoleConfig",
    "LightPoleGenerator",
    "create_highway_light",
    "place_lights_along_road",
]
