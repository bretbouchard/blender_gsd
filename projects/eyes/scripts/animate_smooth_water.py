"""
Animate Smooth Water Sphere - Different Animation Methods

Shows various ways to animate the smooth water sphere.
"""

import bpy
import sys
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from water_sphere_smooth import create_smooth_water_sphere


def animate_with_keyframes(obj, start_frame=1, end_frame=250, speed=0.2):
    """
    Method 1: Keyframe Animation (Already set up)
    Simple linear time animation.
    """
    if not obj.modifiers or obj.modifiers[0].type != 'NODES':
        return

    modifier = obj.modifiers[0]
    time_socket = 'Socket_4'  # Time is the 5th socket (0-indexed)

    # Set start keyframe
    bpy.context.scene.frame_set(start_frame)
    modifier[time_socket] = 0.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=start_frame)

    # Set end keyframe
    bpy.context.scene.frame_set(end_frame)
    modifier[time_socket] = (end_frame - start_frame) * speed / 24.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=end_frame)

    print(f"✓ Keyframe animation set: frames {start_frame}-{end_frame}, speed {speed}")


def animate_with_driver(obj, speed=0.2):
    """
    Method 2: Driver Animation (Real-time)
    Automatically syncs with timeline - no keyframes needed.
    """
    if not obj.modifiers or obj.modifiers[0].type != 'NODES':
        return

    modifier = obj.modifiers[0]
    time_socket = 'Socket_4'

    # Remove existing keyframes if any
    try:
        modifier.animation_data_clear()
    except:
        pass

    # Add driver
    driver = modifier.driver_add(f'["{time_socket}"]')
    driver.driver.type = 'SCRIPTED'
    driver.driver.expression = f"frame * {speed} / 24.0"

    print(f"✓ Driver animation set: auto-syncs with timeline, speed {speed}")


def animate_with_cycle(obj, start_frame=1, end_frame=250, speed=0.2, cycles=3):
    """
    Method 3: Cyclic Animation (Looping)
    Creates a seamless loop that repeats.
    """
    if not obj.modifiers or obj.modifiers[0].type != 'NODES':
        return

    modifier = obj.modifiers[0]
    time_socket = 'Socket_4'

    # Calculate loop duration
    loop_duration = (end_frame - start_frame) // cycles

    # Set cyclic keyframes
    for i in range(cycles + 1):
        frame = start_frame + (i * loop_duration)
        bpy.context.scene.frame_set(frame)
        modifier[time_socket] = (i * loop_duration) * speed / 24.0
        modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=frame)

    # Set extrapolation to cyclic
    if not modifier.animation_data:
        return

    fcurve = modifier.animation_data.drivers[0] if modifier.animation_data.drivers else modifier.animation_data.action.fcurves[0]
    if fcurve:
        fcurve.modifiers.new(type='CYCLES')

    print(f"✓ Cyclic animation set: {cycles} loops over {end_frame - start_frame} frames")


def animate_with_easing(obj, start_frame=1, end_frame=250, speed=0.2):
    """
    Method 4: Eased Animation (Smooth Start/Stop)
    Uses bezier interpolation for smooth acceleration/deceleration.
    """
    if not obj.modifiers or obj.modifiers[0].type != 'NODES':
        return

    modifier = obj.modifiers[0]
    time_socket = 'Socket_4'

    # Set keyframes
    bpy.context.scene.frame_set(start_frame)
    modifier[time_socket] = 0.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=start_frame)

    bpy.context.scene.frame_set(end_frame)
    modifier[time_socket] = (end_frame - start_frame) * speed / 24.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=end_frame)

    # Set bezier interpolation for smooth easing
    if modifier.animation_data and modifier.animation_data.action:
        for fcurve in modifier.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'BEZIER'
                keyframe.easing = 'EASE_IN_OUT'

    print(f"✓ Eased animation set: smooth start/stop over {end_frame - start_frame} frames")


def setup_timeline_playback():
    """Configure timeline for smooth playback."""
    scene = bpy.context.scene

    # Set frame range
    scene.frame_start = 1
    scene.frame_end = 250

    # Set playback settings
    scene.render.fps = 24
    scene.render.fps_base = 1

    # Enable sync to playback speed
    scene.sync_mode = 'AUDIO_SYNC'  # Smooth playback

    print("✓ Timeline configured: 1-250 frames at 24 FPS")


def create_animation_demo():
    """Create a demo scene showing all animation methods."""
    print("\n" + "="*60)
    print("Creating Smooth Water Sphere Animation Demo")
    print("="*60 + "\n")

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Setup timeline
    setup_timeline_playback()

    # Create 4 spheres with different animation methods
    positions = [(-4, 0, 0), (-1.3, 0, 0), (1.3, 0, 0), (4, 0, 0)]
    methods = [
        ("Keyframe", animate_with_keyframes),
        ("Driver", animate_with_driver),
        ("Cyclic", lambda obj: animate_with_cycle(obj, cycles=3)),
        ("Eased", animate_with_easing)
    ]

    spheres = []
    for i, ((name, method), pos) in enumerate(zip(methods, positions)):
        print(f"\nCreating sphere {i+1}: {name} animation...")

        sphere = create_smooth_water_sphere(
            size=1.0,
            wave_scale=1.5,
            wave_height=0.08,
            wind_speed=0.3,
            location=pos,
            name=f"Water_{name}"
        )
        spheres.append(sphere)

        # Apply animation method
        method(sphere)

    # Setup camera to see all spheres
    bpy.ops.object.camera_add(location=(0, -12, 4))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.3, 0, 0)
    bpy.context.scene.camera = camera

    # Add lighting
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 2.0

    # Save
    output_path = script_dir.parent / "smooth_water_animation_demo.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    print("\n" + "="*60)
    print("Animation Demo Created!")
    print("="*60)
    print("\n4 Spheres with Different Animation Methods:")
    print("  1. Keyframe - Simple linear animation")
    print("  2. Driver - Auto-syncs with timeline (no keyframes)")
    print("  3. Cyclic - Seamless looping (3 cycles)")
    print("  4. Eased - Smooth start/stop")
    print("\nTo Play Animation:")
    print("  - Open: smooth_water_animation_demo.blend")
    print("  - Press SPACE to play/pause")
    print("  - Scrub timeline to see different speeds")
    print("\nTo Change Animation:")
    print("  - Select sphere → Go to Modifiers tab")
    print("  - Find 'Socket_4' (Time) with keyframe icon")
    print("  - Hover and press I to add keyframe")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    create_animation_demo()
