"""
Water Sphere Swarm - Simple version that works

Uses point cloud with instanced spheres.
"""

import bpy
import random
import math


def create_water_sphere_swarm():
    """Create a swarm of water spheres."""

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Settings
    num_spheres = 150
    swarm_radius = 3.0
    sphere_radius = 0.25

    # Create collection for spheres
    swarm_collection = bpy.data.collections.new("WaterSwarm")
    bpy.context.scene.collection.children.link(swarm_collection)

    # Create water material
    mat = bpy.data.materials.new(name="SwarmWater")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.1, 0.3, 0.5, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['Alpha'].default_value = 0.8
    mat.blend_method = 'BLEND'

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # Create spheres randomly distributed in a ball
    for i in range(num_spheres):
        # Random position in sphere
        phi = random.uniform(0, 2 * math.pi)
        costheta = random.uniform(-1, 1)
        r = swarm_radius * (random.random() ** (1/3))  # Uniform in volume

        theta = math.acos(costheta)
        x = r * math.sin(theta) * math.cos(phi)
        y = r * math.sin(theta) * math.sin(phi)
        z = r * math.cos(theta)

        # Create sphere
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16,
            ring_count=12,
            radius=sphere_radius,
            location=(x, y, z)
        )
        sphere = bpy.context.active_object
        sphere.name = f"Sphere_{i:03d}"

        # Assign material
        sphere.data.materials.append(mat)

        # Move to swarm collection
        for coll in sphere.users_collection:
            coll.objects.unlink(sphere)
        swarm_collection.objects.link(sphere)

    # Camera
    bpy.ops.object.camera_add(location=(0, -12, 4))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.2, 0, 0)
    bpy.context.scene.camera = camera

    # Light
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.0

    # Save
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/water_sphere_swarm.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("WATER SPHERE SWARM Created!")
    print("="*70)
    print(f"\n{num_spheres} water spheres in a ball formation")
    print(f"Swarm radius: {swarm_radius}")
    print(f"Sphere radius: {sphere_radius}")
    print(f"\nSaved to: {output_path}")
    print("="*70 + "\n")


if __name__ == "__main__":
    create_water_sphere_swarm()
