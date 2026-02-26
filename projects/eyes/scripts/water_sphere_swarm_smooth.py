"""
Water Sphere Swarm - Smooth Spheres

Creates hundreds of smooth water spheres in a ball formation that:
- Are smooth (no bumpy wave deformation)
- Slowly drift and orbit within the swarm
- Morph and blend into each other
"""

import bpy
import random
import math
import bmesh


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
    """Create a dark-to-pearlescent material based on distance from center."""
    mat = bpy.data.materials.new(name="PearlescentWater")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Node positions
    x = 0

    # 1. Geometry node for position
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.location = (x, 0)
    x += 180

    # 2. Vector Math - Length (distance from origin)
    vec_length = nodes.new('ShaderNodeVectorMath')
    vec_length.operation = 'LENGTH'
    vec_length.location = (x, 0)
    x += 180

    # 3. Math - Divide (normalize by swarm radius)
    math_divide = nodes.new('ShaderNodeMath')
    math_divide.operation = 'DIVIDE'
    math_divide.inputs[1].default_value = 1.5  # swarm radius
    math_divide.location = (x, 0)
    x += 180

    # 4. Color Ramp - dark outside to white/pearlescent center
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.color_ramp.interpolation = 'LINEAR'
    # Dark color at position 0.0 (far from center)
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.04, 1.0)  # Very dark blue-black
    # White/pearlescent at position 1.0 (close to center)
    color_ramp.color_ramp.elements[1].position = 1.0
    color_ramp.color_ramp.elements[1].color = (0.95, 0.95, 1.0, 1.0)  # Slightly cool white
    color_ramp.location = (x, 0)
    x += 180

    # 5. Math - Subtract to invert (1 - distance = center is 1, outside is 0)
    math_invert = nodes.new('ShaderNodeMath')
    math_invert.operation = 'SUBTRACT'
    math_invert.inputs[0].default_value = 1.0
    math_invert.location = (x, 0)
    x += 180

    # 6. Principled BSDF for pearlescent look
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['IOR'].default_value = 1.45
    bsdf.inputs['Transmission Weight'].default_value = 0.5
    bsdf.inputs['Alpha'].default_value = 0.85
    bsdf.location = (x, 0)
    x += 200

    # 7. Material Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (x, 0)

    # Link nodes
    links.new(geometry.outputs['Position'], vec_length.inputs[0])
    links.new(vec_length.outputs['Value'], math_divide.inputs[0])
    links.new(math_divide.outputs['Value'], math_invert.inputs[1])
    links.new(math_invert.outputs['Value'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    mat.blend_method = 'BLEND'

    return mat


def create_backdrop():
    """Create a studio backdrop for photoshoot."""
    # Create infinite curve backdrop
    radius = 6.0
    curve_height = 4.0
    curve_segments = 32

    mesh = bpy.data.meshes.new("Backdrop_mesh")
    obj = bpy.data.objects.new("Backdrop", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    # Calculate curve radius
    curve_radius = radius * 0.3

    # Generate profile vertices
    floor_verts_front = []
    curve_verts_front = []
    wall_verts_front = []

    # Floor vertices
    floor_width = radius - curve_radius
    floor_segments = curve_segments // 2
    if floor_segments < 2:
        floor_segments = 2

    for i in range(floor_segments + 1):
        t = i / floor_segments
        x = -radius + (floor_width * t)
        v = bm.verts.new((x, 0, 0))
        floor_verts_front.append(v)

    # Curve vertices
    for i in range(curve_segments + 1):
        t = i / curve_segments
        angle = math.pi / 2 * t
        x = -curve_radius + (curve_radius * math.cos(angle))
        z = curve_radius * math.sin(angle)
        v = bm.verts.new((x, 0, z))
        curve_verts_front.append(v)

    # Wall vertices
    wall_width = radius + curve_radius
    wall_segments = curve_segments // 2
    if wall_segments < 2:
        wall_segments = 2

    for i in range(wall_segments + 1):
        t = i / wall_segments
        x = -curve_radius + (wall_width * t)
        v = bm.verts.new((x, 0, curve_height))
        wall_verts_front.append(v)

    # Extrude along Y axis
    depth = 12.0
    all_front_verts = floor_verts_front + curve_verts_front + wall_verts_front
    all_back_verts = []

    for v in all_front_verts:
        back_v = bm.verts.new((v.co.x, -depth, v.co.z))
        all_back_verts.append(back_v)

    # Create faces
    for i in range(len(all_front_verts) - 1):
        try:
            bm.faces.new([
                all_front_verts[i],
                all_front_verts[i + 1],
                all_back_verts[i + 1],
                all_back_verts[i]
            ])
        except ValueError:
            pass

    # Cap ends
    try:
        bm.faces.new(all_front_verts)
    except ValueError:
        pass
    try:
        bm.faces.new(list(reversed(all_back_verts)))
    except ValueError:
        pass

    bm.to_mesh(mesh)
    bm.free()

    # Position backdrop behind the swarm
    obj.location = (0, 4, -1.5)

    # Create dark gradient material for backdrop
    mat = bpy.data.materials.new("BackdropMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Simple dark gradient
    geometry = nodes.new('ShaderNodeNewGeometry')
    separate = nodes.new('ShaderNodeSeparateXYZ')
    math_div = nodes.new('ShaderNodeMath')
    math_div.operation = 'DIVIDE'
    math_div.inputs[1].default_value = curve_height

    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'LINEAR'
    ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.02, 1.0)  # Black bottom
    ramp.color_ramp.elements[1].color = (0.08, 0.08, 0.1, 1.0)   # Slightly lighter top

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.9
    output = nodes.new('ShaderNodeOutputMaterial')

    geometry.location = (-600, 0)
    separate.location = (-400, 0)
    math_div.location = (-200, 0)
    ramp.location = (0, 0)
    bsdf.location = (200, 0)
    output.location = (400, 0)

    links.new(geometry.outputs['Position'], separate.inputs['Vector'])
    links.new(separate.outputs['Z'], math_div.inputs[0])
    links.new(math_div.outputs['Value'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    obj.data.materials.append(mat)

    return obj


def create_smooth_sphere(name: str, radius: float, segments: int = 32, rings: int = 24):
    """Create a smooth UV sphere mesh."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)

    # Create sphere using bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    bm.to_mesh(mesh)
    bm.free()

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj


def create_water_sphere_swarm_smooth():
    """Create a swarm of smooth water spheres with drift animation."""

    # Clear scene
    clear_scene()

    # Settings
    num_spheres = 10000  # Dense fill
    swarm_radius = 1.5   # Much tighter
    base_radius = 0.06   # Larger base for bigger spheres

    # Size distribution: more large spheres to fill volume
    # (size_multiplier, percentage)
    size_categories = [
        (0.3, 0.30),    # 30% tiny
        (0.8, 0.35),    # 35% medium
        (2.0, 0.25),    # 25% large
        (4.0, 0.10),    # 10% very large (4x)
    ]

    def get_random_size():
        """Pick a random size based on distribution."""
        r = random.random()
        cumulative = 0
        for size_mult, percentage in size_categories:
            cumulative += percentage
            if r < cumulative:
                return base_radius * size_mult
        return base_radius

    # Create collection for spheres
    swarm_collection = bpy.data.collections.new("SmoothWaterSwarm")
    bpy.context.scene.collection.children.link(swarm_collection)

    # Create shared water material
    water_mat = create_water_material()

    # Create backdrop
    print("Creating studio backdrop...")
    backdrop = create_backdrop()

    # Animation settings
    start_frame = 1
    end_frame = 300

    print(f"\nCreating {num_spheres} smooth water spheres with varied sizes...")

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

        # Get random size for this sphere
        sphere_radius = get_random_size()

        # Create smooth sphere (fewer segments for tiny ones, more for large)
        segments = max(12, min(32, int(16 * (sphere_radius / base_radius))))
        rings = max(8, min(24, int(12 * (sphere_radius / base_radius))))

        sphere = create_smooth_sphere(
            name=f"Sphere_{i:03d}",
            radius=sphere_radius,
            segments=segments,
            rings=rings
        )
        bpy.context.collection.objects.link(sphere)

        # Assign material
        sphere.data.materials.append(water_mat)

        # Set base position
        sphere.location = (x, y, z)

        # Animate position for slow drift/orbit
        orbit_radius = random.uniform(0.1, 0.4)
        orbit_speed = random.uniform(0.1, 0.3)
        orbit_phase = random.uniform(0, 2 * math.pi)
        vertical_drift = random.uniform(-0.15, 0.15)

        # Keyframe positions at multiple points for smooth drift
        num_keyframes = 8
        for j in range(num_keyframes + 1):
            frame = start_frame + (end_frame - start_frame) * j / num_keyframes
            t = (frame - start_frame) / (end_frame - start_frame)

            # Calculate drifted position
            angle = orbit_phase + t * 2 * math.pi * orbit_speed
            drift_x = orbit_radius * math.sin(angle)
            drift_y = orbit_radius * math.cos(angle)
            drift_z = vertical_drift * math.sin(t * 4 * math.pi)

            sphere.location = (
                x + drift_x,
                y + drift_y,
                z + drift_z
            )
            sphere.keyframe_insert(data_path='location', frame=int(frame))

        # Move to swarm collection
        for coll in sphere.users_collection:
            if coll != swarm_collection:
                coll.objects.unlink(sphere)
        if sphere not in swarm_collection.objects.values():
            swarm_collection.objects.link(sphere)

        spheres.append(sphere)

        if (i + 1) % 20 == 0:
            print(f"  Created {i + 1}/{num_spheres} spheres...")

    # Camera - orbiting around the swarm
    bpy.ops.object.camera_add(location=(0, -12, 4))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.2, 0, 0)
    bpy.context.scene.camera = camera

    # Animate camera orbit
    for i in range(9):
        frame = start_frame + (end_frame - start_frame) * i / 8
        angle = i * math.pi / 4
        cam_dist = 12
        cam_x = cam_dist * math.sin(angle)
        cam_y = -cam_dist * math.cos(angle)

        camera.location = (cam_x, cam_y, 4)
        camera.keyframe_insert(data_path='location', frame=int(frame))

        camera.rotation_euler = (1.2, 0, angle)
        camera.keyframe_insert(data_path='rotation_euler', frame=int(frame))

    # Lighting
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.0

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
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/smooth_water_swarm.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("SMOOTH WATER SPHERE SWARM Created!")
    print("="*70)
    print(f"\n{num_spheres} smooth water spheres in a solid ball formation")
    print(f"Swarm radius: {swarm_radius}")
    print(f"\nSize distribution:")
    print(f"  - 30% tiny (0.3x)")
    print(f"  - 35% medium (0.8x)")
    print(f"  - 25% large (2x)")
    print(f"  - 10% very large (4x)")
    print(f"\nAnimation:")
    print(f"  - Frames: {start_frame}-{end_frame} ({end_frame-start_frame+1} frames)")
    print(f"  - Duration: {(end_frame-start_frame+1)/24:.1f} seconds at 24fps")
    print(f"  - Smooth spheres (no bumpy waves)")
    print(f"  - Slow drift/orbit movement")
    print(f"  - Camera orbits the swarm")
    print(f"\nSaved to: {output_path}")
    print("="*70 + "\n")

    return output_path


if __name__ == "__main__":
    create_water_sphere_swarm_smooth()
