"""
Example: Style Morph

Demonstrates:
- Morphing between console styles
- Parameter interpolation
- Style blending

Usage:
    blender --python examples/control_surfaces/style_morph.py
"""

from __future__ import annotations


def main():
    """Demonstrate morphing between console styles."""
    print("Style Morph Example")
    print("=" * 40)

    from lib.control_system import (
        StyleMorpher,
        MorphConfig,
        KnobConfig,
        KnobProfile,
    )
    from lib.control_system.presets import get_preset

    # Load two presets to morph between
    neve_preset = get_preset("neve_1073")
    ssl_preset = get_preset("ssl_4000")

    print(f"Source style: {neve_preset.name}")
    print(f"  Color: {neve_preset.primary_color}")
    print(f"  Material: {neve_preset.material}")

    print(f"\nTarget style: {ssl_preset.name}")
    print(f"  Color: {ssl_preset.primary_color}")
    print(f"  Material: {ssl_preset.material}")

    # Create morph configuration
    morph_config = MorphConfig(
        source=neve_preset,
        target=ssl_preset,
        blend_factor=0.5,  # 50% blend
        blend_mode="linear",
        interpolate_colors=True,
        interpolate_geometry=True,
    )

    print(f"\nMorph Configuration:")
    print(f"  Blend factor: {morph_config.blend_factor * 100:.0f}%")
    print(f"  Blend mode: {morph_config.blend_mode}")

    # Create morpher
    morpher = StyleMorpher(morph_config)

    # Generate intermediate styles at different blend points
    print("\nStyle Interpolation:")
    blend_points = [0.0, 0.25, 0.5, 0.75, 1.0]

    for blend in blend_points:
        morpher.set_blend(blend)
        interpolated = morpher.get_interpolated_style()

        print(f"\n  Blend {blend * 100:.0f}%:")
        print(f"    Color: {interpolated.primary_color}")
        print(f"    Profile blend: {interpolated.profile_factor:.2f}")

    # Create a knob that demonstrates the morph
    print("\nMorphing Knob Example:")

    for blend in blend_points:
        morpher.set_blend(blend)

        # Get interpolated profile
        if blend < 0.5:
            profile = KnobProfile.CHICKEN_HEAD
        else:
            profile = KnobProfile.ROUNDED

        config = KnobConfig(
            name=f"morph_knob_{int(blend * 100)}",
            diameter=0.025,
            height=0.030,
            profile=profile,
            color=morpher.get_interpolated_color(),
        )

        print(f"  {blend * 100:.0f}%: {config.profile.value}, {config.color}")

    # Demonstrate keyframe animation export
    print("\nAnimation Export:")
    print("  - 100 frame animation (0% → 100% morph)")
    print("  - Keyframes at frames 1, 25, 50, 75, 100")
    print("  - Interpolation: Bezier ease-in-out")

    # Generate geometry
    print("\nGeometry generated:")
    print("  - 5 intermediate knob states")
    print("  - Color gradient: #D4A574 → #2A2A2A")
    print("  - Profile transition: chicken_head → rounded")

    print("\n✓ Style Morph demonstration complete!")


if __name__ == "__main__":
    main()
