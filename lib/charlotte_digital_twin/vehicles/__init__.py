"""
Charlotte Digital Twin Vehicles System

Vehicle models and animation:
- Hero car generation
- Car physics animation
- Chase path creation

Usage:
    from lib.charlotte_digital_twin.vehicles import (
        HeroCarBuilder,
        CarAnimationSystem,
        create_hero_car,
        animate_car_chase,
    )

    # Create hero car
    car = create_hero_car(CarType.MUSCLE, paint_color="cherry_red")

    # Animate along path
    animate_car_chase(car, road_points, style=AnimationStyle.AGGRESSIVE)
"""

from .hero_car import (
    CarType,
    CarDimensions,
    CarPaintConfig,
    CAR_DIMENSIONS,
    PAINT_PRESETS,
    HeroCarBuilder,
    create_hero_car,
)

from .car_animation import (
    AnimationStyle,
    VehiclePhysics,
    AnimationConfig,
    PHYSICS_PRESETS,
    CarAnimationSystem,
    create_chase_path,
    animate_car_chase,
)

__version__ = "1.0.0"
__all__ = [
    # Car Model
    "CarType",
    "CarDimensions",
    "CarPaintConfig",
    "CAR_DIMENSIONS",
    "PAINT_PRESETS",
    "HeroCarBuilder",
    "create_hero_car",
    # Animation
    "AnimationStyle",
    "VehiclePhysics",
    "AnimationConfig",
    "PHYSICS_PRESETS",
    "CarAnimationSystem",
    "create_chase_path",
    "animate_car_chase",
]
