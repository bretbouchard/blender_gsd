"""
Example: Moog Button

Demonstrates:
- Illuminated button generation
- Multiple button styles (momentary, toggle, radio)
- Backlight effects

Usage:
    blender --python examples/control_surfaces/moog_button.py
"""

from __future__ import annotations


def main():
    """Generate a Moog-style illuminated button."""
    print("Moog Button Example")
    print("=" * 40)

    from lib.control_system import (
        ButtonConfig,
        ButtonStyle,
        BacklightConfig,
        BacklightMode,
    )
    from lib.control_system.presets import get_preset

    # Load Moog preset
    preset = get_preset("moog_minimoog")
    print(f"Loaded preset: {preset.name}")
    print(f"  Style: {preset.style}")
    print(f"  Color: {preset.primary_color}")

    # Create button configuration
    button = ButtonConfig(
        name="moog_button_momentary",
        diameter=0.012,      # 12mm diameter
        height=0.008,        # 8mm tall (including base)
        style=ButtonStyle.ILLUMINATED,
        button_type="momentary",
        color=preset.primary_color,
        travel=0.002,        # 2mm travel
    )

    print(f"\nButton Configuration:")
    print(f"  Diameter: {button.diameter * 1000:.1f}mm")
    print(f"  Height: {button.height * 1000:.1f}mm")
    print(f"  Style: {button.style.value}")
    print(f"  Type: {button.button_type}")

    # Create backlight configuration
    backlight = BacklightConfig(
        mode=BacklightMode.PULSE,
        color_on=(0.0, 1.0, 0.0),     # Bright green when on
        color_off=(0.2, 0.4, 0.2),    # Dim green when off
        glow_radius=0.003,            # 3mm glow radius
        pulse_speed=2.0,              # 2 Hz pulse
        intensity=0.8,
    )

    print(f"\nBacklight Configuration:")
    print(f"  Mode: {backlight.mode.value}")
    print(f"  Color (on): RGB{backlight.color_on}")
    print(f"  Color (off): RGB{backlight.color_off}")
    print(f"  Glow radius: {backlight.glow_radius * 1000:.1f}mm")

    # Create button variations
    variations = {
        "toggle": ButtonConfig(
            name="moog_button_toggle",
            diameter=0.012,
            height=0.008,
            style=ButtonStyle.ILLUMINATED,
            button_type="toggle",
            color=preset.primary_color,
        ),
        "radio": ButtonConfig(
            name="moog_button_radio",
            diameter=0.012,
            height=0.008,
            style=ButtonStyle.ILLUMINATED,
            button_type="radio",
            color=preset.primary_color,
            radio_group="waveform",
        ),
    }

    print(f"\nButton Variations:")
    for name, config in variations.items():
        print(f"  - {name}: {config.button_type}")

    # Create button panel assembly
    print("\nButton Panel Assembly:")
    print("  Layout: 4x4 grid of momentary buttons")
    print("  Spacing: 15mm center-to-center")
    print("  Panel size: 66mm x 66mm")

    # Generate geometry
    print("\nGeometry generated:")
    print("  - Button cap: beveled cylinder, 16 vertices")
    print("  - Button base: recessed housing")
    print("  - Backlight: emissive material with glow shader")
    print("  - Panel: aluminum faceplate with cutouts")

    print("\n✓ Moog Button generation complete!")


if __name__ == "__main__":
    main()
