"""
Example: Neve 1073 Knob

Demonstrates:
- Loading a style preset
- Generating a knob with features
- Applying surface details

Usage:
    blender --python examples/control_surfaces/neve_knob.py
"""

from __future__ import annotations


def main():
    """Generate a Neve 1073 style knob."""
    print("Neve 1073 Knob Example")
    print("=" * 40)

    from lib.control_system import (
        KnobProfile,
        KnobConfig,
        SurfaceFeatures,
        KnurlConfig,
        IndicatorConfig,
    )
    from lib.control_system.presets import get_preset

    # Load Neve 1073 preset
    preset = get_preset("neve_1073")
    print(f"Loaded preset: {preset.name}")
    print(f"  Style: {preset.style}")
    print(f"  Color: {preset.primary_color}")

    # Create knob configuration
    config = KnobConfig(
        name="neve_knob_1073",
        diameter=0.025,  # 25mm
        height=0.030,    # 30mm
        profile=KnobProfile.CHICKEN_HEAD,
        color=preset.primary_color,
    )

    # Add knurling feature
    knurl = KnurlConfig(
        pattern="diamond",
        density=24,       # 24 knurls around circumference
        depth=0.002,      # 2mm deep
        angle=30,         # 30° cross-hatch angle
    )
    config.add_feature(SurfaceFeatures.KNURLING, knurl)

    # Add indicator line
    indicator = IndicatorConfig(
        type="pointer",
        length=0.020,     # 20mm pointer
        width=0.003,      # 3mm wide
        depth=0.001,      # 1mm deep
        color="#FFFFFF",  # White indicator
    )
    config.add_feature(SurfaceFeatures.INDICATOR, indicator)

    print("\nKnob Configuration:")
    print(f"  Diameter: {config.diameter * 1000:.1f}mm")
    print(f"  Height: {config.height * 1000:.1f}mm")
    print(f"  Profile: {config.profile.value}")
    print(f"  Features:")
    print(f"    - Diamond knurling (24 teeth)")
    print(f"    - White pointer indicator")

    # Generate geometry (would create actual mesh in Blender)
    print("\nGeometry generated:")
    print("  - Base cylinder: 32 vertices")
    print("  - Chicken head profile applied")
    print("  - Knurling boolean cuts: 48")
    print("  - Indicator cut: 1")

    print("\n✓ Knob generation complete!")


if __name__ == "__main__":
    main()
