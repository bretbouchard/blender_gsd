"""
Example: Three Point Lighting

Demonstrates:
- Classic three-point lighting setup
- Key, fill, and rim light configuration
- Light ratio calculations

Usage:
    blender --python examples/cinematic/three_point_lighting.py
"""

from __future__ import annotations


def main():
    """Create a classic three-point lighting setup."""
    print("Three Point Lighting Example")
    print("=" * 40)

    from lib.cinematic import (
        ThreePointLighting,
        LightConfig,
        LightType,
        SubjectBounds,
    )

    # Define subject (for light positioning)
    subject = SubjectBounds(
        center=(0, 0, 1.0),       # Subject at origin, 1m tall
        width=0.6,                # 60cm wide
        height=1.8,               # 1.8m tall (standing person)
        depth=0.4,                # 40cm deep
    )

    print(f"Subject Configuration:")
    print(f"  Center: {subject.center}")
    print(f"  Dimensions: {subject.width}m x {subject.height}m x {subject.depth}m")

    # Create key light (main illumination)
    key_light = LightConfig(
        name="key_light",
        type=LightType.AREA,
        power=800,                # Watts
        color=(1.0, 0.95, 0.9),   # Slightly warm
        position=(2.5, 2.0, 2.5),  # 45° angle, elevated
        rotation=(-50, 0, -40),   # Aimed at subject
        size=2.0,                 # 2m soft box
        softness=0.8,
    )

    print(f"\nKey Light:")
    print(f"  Type: {key_light.type.value}")
    print(f"  Power: {key_light.power}W")
    print(f"  Position: {key_light.position}")
    print(f"  Size: {key_light.size}m (soft box)")

    # Create fill light (shadow fill)
    fill_light = LightConfig(
        name="fill_light",
        type=LightType.AREA,
        power=240,                # Key:Fill ratio of 3:1
        color=(0.95, 0.95, 1.0),  # Slightly cool (complementary)
        position=(-2.0, 1.5, 1.5),
        rotation=(-40, 0, 30),
        size=2.5,                 # Larger, softer
        softness=0.9,
    )

    fill_ratio = fill_light.power / key_light.power
    print(f"\nFill Light:")
    print(f"  Type: {fill_light.type.value}")
    print(f"  Power: {fill_light.power}W")
    print(f"  Key:Fill ratio: {1/fill_ratio:.1f}:1")

    # Create rim/hair light (separation from background)
    rim_light = LightConfig(
        name="rim_light",
        type=LightType.SPOT,
        power=500,
        color=(1.0, 1.0, 1.0),    # Neutral white
        position=(0, -3.0, 2.5),  # Behind subject
        rotation=(-60, 0, 180),
        spot_angle=25,
        spot_blend=0.3,
    )

    print(f"\nRim Light:")
    print(f"  Type: {rim_light.type.value}")
    print(f"  Power: {rim_light.power}W")
    print(f"  Spot angle: {rim_light.spot_angle}°")

    # Optional: Add background light
    background_light = LightConfig(
        name="background_light",
        type=LightType.AREA,
        power=150,
        color=(1.0, 1.0, 1.0),
        position=(0, -2.0, 0.5),
        rotation=(-90, 0, 0),
        size=3.0,
    )

    print(f"\nBackground Light (optional):")
    print(f"  Power: {background_light.power}W")

    # Create complete setup
    setup = ThreePointLighting(
        subject=subject,
        key=key_light,
        fill=fill_light,
        rim=rim_light,
        background=background_light,
        ambient_strength=0.05,    # Subtle ambient fill
    )

    print(f"\nLighting Ratios:")
    print(f"  Key : Fill = 3.3 : 1")
    print(f"  Key : Rim = 1.6 : 1")

    print("\nScene generated:")
    print("  - Key light (45° front-right, elevated)")
    print("  - Fill light (30° front-left, softer)")
    print("  - Rim light (behind, creates edge)")
    print("  - Background light (separation)")

    print("\n✓ Three Point Lighting setup complete!")


if __name__ == "__main__":
    main()
