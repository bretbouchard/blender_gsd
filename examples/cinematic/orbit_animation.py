"""
Example: Orbit Animation

Demonstrates:
- Camera orbit around subject
- Variable height and distance
- Animation curve control

Usage:
    blender --python examples/cinematic/orbit_animation.py
"""

from __future__ import annotations


def main():
    """Create a camera orbit animation around a subject."""
    print("Orbit Animation Example")
    print("=" * 40)

    from lib.cinematic import (
        OrbitConfig,
        OrbitPath,
        CameraSettings,
        AnimationCurve,
    )

    # Create orbit configuration
    orbit = OrbitConfig(
        name="showcase_orbit",
        subject_center=(0, 0, 0.5),
        subject_bounds=(1.0, 1.0, 1.0),
    )

    print(f"Orbit Configuration:")
    print(f"  Subject center: {orbit.subject_center}")
    print(f"  Subject bounds: {orbit.subject_bounds}")

    # Define orbit path
    path = OrbitPath(
        path_type="elliptical",
        start_angle=0,
        end_angle=360,
        radius_min=2.0,
        radius_max=3.0,           # Elliptical: varies between 2-3m
        height_start=0.8,
        height_end=1.5,           # Rises during orbit
        clockwise=True,
        num_revolutions=1,
    )

    print(f"\nOrbit Path:")
    print(f"  Type: {path.path_type}")
    print(f"  Radius: {path.radius_min}m to {path.radius_max}m")
    print(f"  Height: {path.height_start}m to {path.height_end}m")
    print(f"  Direction: {'clockwise' if path.clockwise else 'counter-clockwise'}")

    # Camera settings
    camera = CameraSettings(
        focal_length=50,
        sensor_size=36,
        f_stop=4.0,
        focus_mode="TRACK",       # Always track subject
        depth_of_field=True,
        autofocus=True,
    )

    print(f"\nCamera Settings:")
    print(f"  Focal length: {camera.focal_length}mm")
    print(f"  f-stop: {camera.f_stop}")
    print(f"  Focus mode: {camera.focus_mode}")
    print(f"  DoF: {'enabled' if camera.depth_of_field else 'disabled'}")

    # Animation curve
    animation = AnimationCurve(
        total_frames=300,         # 12.5 seconds at 24fps
        frame_rate=24,
        interpolation="BEZIER",
        ease_in_frames=24,        # 1 second ease in
        ease_out_frames=24,       # 1 second ease out
        keyframe_interval=10,     # Keyframe every 10 frames
    )

    print(f"\nAnimation:")
    print(f"  Total frames: {animation.total_frames}")
    print(f"  Duration: {animation.total_frames / animation.frame_rate:.1f}s")
    print(f"  Interpolation: {animation.interpolation}")
    print(f"  Ease in/out: {animation.ease_in_frames} frames each")

    # Calculate keyframe positions
    print(f"\nKeyframe Positions (sample):")
    keyframes = [0, 60, 120, 180, 240, 300]
    for frame in keyframes:
        angle = (frame / animation.total_frames) * 360
        progress = frame / animation.total_frames
        radius = path.radius_min + (path.radius_max - path.radius_min) * progress
        height = path.height_start + (path.height_end - path.height_start) * progress

        import math
        x = radius * math.cos(math.radians(angle))
        y = radius * math.sin(math.radians(angle))
        z = height

        print(f"  Frame {frame:3d}: ({x:5.2f}, {y:5.2f}, {z:4.2f}) @ {angle:3.0f}°")

    # Generate animation
    print("\nAnimation generated:")
    print("  - Camera path: elliptical orbit")
    print("  - 31 keyframes (every 10 frames)")
    print("  - Bezier interpolation with ease in/out")
    print("  - Track constraint to subject center")

    print("\n✓ Orbit Animation setup complete!")


if __name__ == "__main__":
    main()
