"""
Water Sphere Swarm - Animated with Morphing

Creates hundreds of water spheres in a ball formation that:
- Slowly drift and orbit within the swarm
- Have individual wave deformations
- Morph and blend into each other
"""

import bpy
import random
import math
import sys
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from water_sphere import create_water_sphere_node_group


def clear_scene():
    """Clear all mesh objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def create_water_material():
    """Create a water material with transparency."""
    mat = bpy.data.materials.new(name="SwarmWater")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Principled BSDF for water
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.1, 0.4, 0.6, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['Alpha'].default_value = 0.7
    bsdf.inputs['IOR'].default_value = 1.33
    mat.blend_method = 'BLEND'

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_animated_swarm_sphere(
    index: int,
    base_position: tuple,
    swarm_radius: float,
    sphere_radius: float,
    material,
    start_frame: int = 1,
    end_frame: int = 250
):
    """Create a single animated sphere with wave deformation."""

    # Create geometry node group for this sphere
    node_group = create_water_sphere_node_group(f"WaterSphere_{index:03d}")

    # Create mesh object
    mesh = bpy.data.meshes.new(f"Sphere_{index:03d}_mesh")
    obj = bpy.data.objects.new(f"Sphere_{index:03d}", mesh)
    bpy.context.collection.objects.link(obj)

    # Add geometry nodes modifier
    modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')
    modifier.node_group = node_group

    # Set parameters - smaller spheres with subtle waves
    modifier['Socket_0'] = sphere_radius  # Size
    modifier['Socket_1'] = 3.0  # Ripple scale
    modifier['Socket_2'] = 0.08  # Ripple intensity (subtle for swarm)
    modifier['Socket_3'] = random.uniform(0, 2 * math.pi)  # Wind angle (varies per sphere)
    modifier['Socket_4'] = random.uniform(0.5, 1.5)  # Wind strength (varies)
    modifier['Socket_5'] = 0.0  # Time (animated)
    modifier['Socket_6'] = 16  # Segments (lower for performance)
    modifier['Socket_7'] = 12  # Rings

    # Assign material
    obj.data.materials.append(material)

    # Set base position
    obj.location = base_position

    # Animate the Time parameter for wave movement
    time_socket = 'Socket_5'
    speed = random.uniform(0.2, 0.5)  # Vary speed per sphere

    bpy.context.scene.frame_set(start_frame)
    modifier[time_socket] = 0.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=start_frame)

    bpy.context.scene.frame_set(end_frame)
    modifier[time_socket] = (end_frame - start_frame) * speed / 24.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=end_frame)

    # Animate position for slow drift/orbit
    # Each sphere has a unique orbit pattern
    orbit_radius = random.uniform(0.1, 0.3)
    orbit_speed = random.uniform(0.1, 0.3)
    orbit_phase = random.uniform(0, 2 * math.pi)
    vertical_drift = random.uniform(-0.1, 0.1)

    # Keyframe positions at multiple points for smooth drift
    num_keyframes = 8
    for i in range(num_keyframes + 1):
        frame = start_frame + (end_frame - start_frame) * i / num_keyframes
        t = (frame - start_frame) / (end_frame - start_frame)

        # Calculate drifted position
        angle = orbit_phase + t * 2 * math.pi * orbit_speed
        drift_x = orbit_radius * math.sin(angle)
        drift_y = orbit_radius * math.cos(angle)
        drift_z = vertical_drift * math.sin(t * 4 * math.pi)

        obj.location = (
            base_position[0] + drift_x,
            base_position[1] + drift_y,
            base_position[2] + drift_z
        )
        obj.keyframe_insert(data_path='location', frame=int(frame))

    return obj


def create_water_sphere_swarm_animated():
    """Create an animated swarm of water spheres with morphing."""

    # Clear scene
    clear_scene()

    # Settings
    num_spheres = 120  # Balance between visual density and performance
    swarm_radius = 3.0
    sphere_radius = 0.2  # Smaller for swarm

    # Create collection for spheres
    swarm_collection = bpy.data.collections.new("AnimatedWaterSwarm")
    bpy.context.scene.collection.children.link(swarm_collection)

    # Create shared water material
    water_mat = create_water_material()

    # Animation settings
    start_frame = 1
    end_frame = 300

    print(f"\nCreating {num_spheres} animated water spheres...")

    # Create spheres with animation
    spheres = []
    for i in range(num_spheres):
        # Random position in sphere (uniform volume distribution)
        phi = random.uniform(0, 2 * math.pi)
        costheta = random.uniform(-1, 1)
        r = swarm_radius * (random.random() ** (1/3))

        theta = math.acos(costheta)
        x = r * math.sin(theta) * math.cos(phi)
        y = r * math.sin(theta) * math.sin(phi)
        z = r * math.cos(theta)

        # Create animated sphere
        sphere = create_animated_swarm_sphere(
            index=i,
            base_position=(x, y, z),
            swarm_radius=swarm_radius,
            sphere_radius=sphere_radius,
            material=water_mat,
            start_frame=start_frame,
            end_frame=end_frame
        )

        # Move to swarm collection
        for coll in sphere.users_collection:
            if coll != swarm_collection:
                coll.objects.unlink(sphere)
        if sphere not in swarm_collection.objects.values():
            swarm_collection.objects.link(sphere)

        spheres.append(sphere)

        if (i + 1) % 20 == 0:
            print(f"  Created {i + 1}/{num_spheres} spheres...")

    # Camera
    bpy.ops.object.camera_add(location=(0, -12, 4))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.2, 0, 0)
    bpy.context.scene.camera = camera

    # Slowly rotate camera around the swarm
    camera.animation_data_create()
    camera.animation_data.action = bpy.data.actions.new("CameraOrbit")

    for i in range(9):
        frame = start_frame + (end_frame - start_frame) * i / 8
        angle = i * math.pi / 4  # 45 degrees per step, full 360 over 8 steps
        cam_dist = 12
        cam_x = cam_dist * math.sin(angle)
        cam_y = -cam_dist * math.cos(angle)

        camera.location = (cam_x, cam_y, 4)
        camera.keyframe_insert(data_path='location', frame=int(frame))

        # Camera always looks at center
        camera.rotation_euler = (1.2, 0, angle)
        camera.keyframe_insert(data_path='rotation_euler', frame=int(frame))

    # Light - animated for subtle light changes
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.0

    # Animate sun position slightly
    sun.location = (5, -5, 10)
    sun.keyframe_insert(data_path='location', frame=start_frame)
    sun.location = (7, -3, 12)
    sun.keyframe_insert(data_path='location', frame=end_frame)

    # Add a second fill light
    bpy.ops.object.light_add(type='AREA', location=(-5, 5, 5))
    fill = bpy.context.active_object
    fill.data.energy = 50.0
    fill.data.size = 5.0

    # Set scene frame range
    bpy.context.scene.frame_start = start_frame
    bpy.context.scene.frame_end = end_frame
    bpy.context.scene.render.fps = 24

    # Set viewport shading
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'

    # Save
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/animated_water_swarm.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("ANIMATED WATER SPHERE SWARM Created!")
    print("="*70)
    print(f"\n{num_spheres} water spheres in a ball formation")
    print(f"Swarm radius: {swarm_radius}")
    print(f"Sphere radius: {sphere_radius}")
    print(f"\nAnimation:")
    print(f"  - Frames: {start_frame}-{end_frame} ({end_frame-start_frame+1} frames)")
    print(f"  - Duration: {(end_frame-start_frame+1)/24:.1f} seconds at 24fps")
    print(f"  - Each sphere has:")
    print(f"    * Individual wave deformation")
    print(f"    * Slow drift/orbit movement")
    print(f"    * Unique wind direction")
    print(f"  - Camera slowly orbits the swarm")
    print(f"\nSaved to: {output_path}")
    print("="*70 + "\n")

    return output_path


if __name__ == "__main__":
    create_water_sphere_swarm_animated()
