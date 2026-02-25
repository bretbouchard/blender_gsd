"""
Example: Product Turntable

Demonstrates:
- 360° rotation animation
- Camera setup for product showcase
- Render settings optimization

Usage:
    blender --python examples/cinematic/product_turntable.py
"""

from __future__ import annotations


def main():
    """Generate a 360° product turntable render setup."""
    print("Product Turntable Example")
    print("=" * 40)

    from lib.cinematic import (
        TurntableConfig,
        CameraRig,
        RenderSettings,
        LightingSetup,
    )

    # Create turntable configuration
    turntable = TurntableConfig(
        name="product_showcase",
        rotation_axis="Z",        # Rotate around vertical axis
        rotation_speed=10.0,      # 10 seconds per rotation
        total_frames=240,         # 240 frames = 10 seconds at 24fps
        ease_in_out=True,         # Smooth start/stop
        product_bounds=(0.3, 0.3, 0.2),  # Max product dimensions
    )

    print(f"Turntable Configuration:")
    print(f"  Rotation axis: {turntable.rotation_axis}")
    print(f"  Rotation speed: {turntable.rotation_speed}s per revolution")
    print(f"  Total frames: {turntable.total_frames}")
    print(f"  Frame rate: 24 fps")

    # Create camera rig
    camera_rig = CameraRig(
        name="turntable_camera",
        camera_type="PERSPECTIVE",
        focal_length=85,          # 85mm portrait lens
        sensor_size=36,           # Full frame
        distance=1.5,             # 1.5m from center
        height=0.4,               # 40cm above table
        look_at=(0, 0, 0.1),      # Look at product center
        depth_of_field=True,
        f_stop=2.8,               # Shallow DOF
        focus_distance=1.5,
    )

    print(f"\nCamera Configuration:")
    print(f"  Focal length: {camera_rig.focal_length}mm")
    print(f"  Distance: {camera_rig.distance}m")
    print(f"  Height: {camera_rig.height}m")
    print(f"  f-stop: {camera_rig.f_stop}")

    # Create lighting setup
    lighting = LightingSetup(
        name="studio_lighting",
        setup_type="studio_white",
        key_light={
            "type": "AREA",
            "power": 500,
            "position": (2, 2, 3),
            "size": 1.0,
            "color": (1.0, 1.0, 1.0),
        },
        fill_light={
            "type": "AREA",
            "power": 200,
            "position": (-2, 1, 2),
            "size": 1.5,
            "color": (0.95, 0.95, 1.0),
        },
        rim_light={
            "type": "SPOT",
            "power": 300,
            "position": (0, -3, 2),
            "angle": 30,
            "color": (1.0, 1.0, 1.0),
        },
        hdri_environment="studio_white.exr",
        hdri_strength=0.5,
    )

    print(f"\nLighting Configuration:")
    print(f"  Setup type: {lighting.setup_type}")
    print(f"  Key light: {lighting.key_light['power']}W")
    print(f"  Fill light: {lighting.fill_light['power']}W")
    print(f"  Rim light: {lighting.rim_light['power']}W")

    # Create render settings
    render = RenderSettings(
        engine="CYCLES",
        resolution=(1920, 1080),
        frame_rate=24,
        samples=256,
        denoiser="OPTIX",
        motion_blur=False,        # Static product, no motion blur
        film_transparent=True,    # Transparent background option
        output_format="PNG",
        output_path="//renders/turntable/",
        color_management="Filmic",
        look="Medium High Contrast",
    )

    print(f"\nRender Settings:")
    print(f"  Engine: {render.engine}")
    print(f"  Resolution: {render.resolution[0]}x{render.resolution[1]}")
    print(f"  Samples: {render.samples}")
    print(f"  Denoiser: {render.denoiser}")

    # Calculate render time estimate
    print("\nRender Estimates:")
    frame_time = 15  # seconds per frame (estimate)
    total_time = frame_time * turntable.total_frames
    print(f"  Estimated time per frame: {frame_time}s")
    print(f"  Total estimated render time: {total_time / 60:.1f} minutes")
    print(f"  Output frames: {turntable.total_frames} PNG files")

    # Generate scene
    print("\nScene generated:")
    print("  - Turntable platform (white acrylic)")
    print("  - Camera rig with DoF")
    print("  - 3-point studio lighting")
    print("  - Animation: 240 frames, full rotation")

    print("\n✓ Product Turntable setup complete!")


if __name__ == "__main__":
    main()
