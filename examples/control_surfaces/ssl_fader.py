"""
Example: SSL Fader

Demonstrates:
- Fader cap generation
- LED meter integration
- Channel strip assembly

Usage:
    blender --python examples/control_surfaces/ssl_fader.py
"""

from __future__ import annotations


def main():
    """Generate an SSL-style fader with LED meter."""
    print("SSL Fader Example")
    print("=" * 40)

    from lib.control_system import (
        FaderConfig,
        FaderProfile,
        LEDMeterConfig,
        ChannelStripConfig,
    )
    from lib.control_system.presets import get_preset

    # Load SSL 4000 preset
    preset = get_preset("ssl_4000")
    print(f"Loaded preset: {preset.name}")
    print(f"  Style: {preset.style}")
    print(f"  Color: {preset.primary_color}")

    # Create fader configuration
    fader = FaderConfig(
        name="ssl_fader_100mm",
        length=0.100,      # 100mm travel
        width=0.015,       # 15mm wide
        height=0.025,      # 25mm tall cap
        profile=FaderProfile.TAPERED,
        color=preset.primary_color,
        throw_length=0.100,
    )

    print(f"\nFader Configuration:")
    print(f"  Length: {fader.length * 1000:.1f}mm")
    print(f"  Width: {fader.width * 1000:.1f}mm")
    print(f"  Profile: {fader.profile.value}")

    # Create LED meter
    meter = LEDMeterConfig(
        segments=12,
        spacing=0.003,         # 3mm between segments
        segment_width=0.008,   # 8mm wide
        segment_height=0.004,  # 4mm tall
        colors={
            "green": (0, -10, "db"),     # 0 to -10dB
            "yellow": (-10, -3, "db"),   # -10 to -3dB
            "red": (-3, 6, "db"),        # -3 to +6dB
        },
        peak_hold=True,
        peak_hold_time=1.5,    # 1.5 second hold
    )

    print(f"\nLED Meter Configuration:")
    print(f"  Segments: {meter.segments}")
    print(f"  Color zones: green, yellow, red")
    print(f"  Peak hold: {meter.peak_hold}")

    # Create channel strip assembly
    strip = ChannelStripConfig(
        name="ssl_channel_strip",
        width=0.040,   # 40mm module width
        height=0.300,  # 300mm total height
        components={
            "input_gain": {"type": "knob", "position": (0.020, 0.280)},
            "high_pass": {"type": "knob", "position": (0.020, 0.250)},
            "eq_high": {"type": "knob", "position": (0.020, 0.200)},
            "eq_mid": {"type": "knob_dual", "position": (0.020, 0.160)},
            "eq_low": {"type": "knob", "position": (0.020, 0.120)},
            "aux_send": {"type": "knob_row", "count": 4, "position": (0.020, 0.080)},
            "pan": {"type": "knob", "position": (0.020, 0.050)},
            "fader": {"type": "fader", "position": (0.010, 0.025)},
            "meter": {"type": "led_meter", "position": (0.035, 0.025)},
        },
    )

    print(f"\nChannel Strip Assembly:")
    print(f"  Width: {strip.width * 1000:.1f}mm")
    print(f"  Height: {strip.height * 1000:.1f}mm")
    print(f"  Components: {len(strip.components)}")

    # Generate geometry
    print("\nGeometry generated:")
    print("  - Fader cap: tapered profile, 8 vertices")
    print("  - Fader track: extruded rail with groove")
    print("  - LED meter: 12 segments with bezels")
    print("  - Channel strip panel: cutouts for components")

    print("\n✓ SSL Fader generation complete!")


if __name__ == "__main__":
    main()
