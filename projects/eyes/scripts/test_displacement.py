"""
Test Water Sphere - Extreme Displacement Test

Creates a test with VERY obvious displacement to verify it's working.
"""

import bpy
import sys
from pathlib import Path

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from water_sphere import create_water_sphere_node_group


def test_extreme_displacement():
    """Create a sphere with extreme displacement to verify it works."""
    print("\n" + "="*60)
    print("Testing EXTREME Displacement")
    print("="*60)

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create the node group
    node_group = create_water_sphere_node_group()

    # Create a test sphere
    mesh = bpy.data.meshes.new("TestMesh")
    obj = bpy.data.objects.new("TestSphere", mesh)
    bpy.context.collection.objects.link(obj)

    # Add modifier
    modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')
    modifier.node_group = node_group

    # Set EXTREME values to make displacement obvious
    modifier['Socket_0'] = 2.0           # Size
    modifier['Socket_1'] = 0.5           # Ripple Scale (low = bigger waves)
    modifier['Socket_2'] = 0.5           # Ripple Intensity (VERY HIGH - 50% of size!)
    modifier['Socket_3'] = 0.0           # Wind Angle
    modifier['Socket_4'] = 1.0           # Wind Strength
    modifier['Socket_5'] = 0.0           # Time
    modifier['Socket_6'] = 32            # Segments
    modifier['Socket_7'] = 24            # Rings

    # Add camera
    bpy.ops.object.camera_add(location=(0, -10, 2))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.2, 0, 0)
    bpy.context.scene.camera = camera

    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.0

    # Create a simple gray material
    mat = bpy.data.materials.new(name="GrayMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.7, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.3
    obj.data.materials.append(mat)

    # Save
    output_path = script_dir.parent / "extreme_displacement_test.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    # Get vertex count from evaluated object
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    vertex_count = len(mesh.vertices)
    eval_obj.to_mesh_clear()

    print(f"\nResults:")
    print(f"  - Vertex count: {vertex_count}")
    print(f"  - Expected with subdiv level 3: ~6000-10000 vertices")
    print(f"  - Base sphere (32x24): ~768 vertices")
    print(f"  - If vertex count is ~768, subdivision/displacement NOT working")
    print(f"  - If vertex count is ~6000+, subdivision IS working")
    print(f"  - Saved to: {output_path}")
    print("="*60 + "\n")

    return vertex_count


if __name__ == "__main__":
    count = test_extreme_displacement()
    print(f"VERTEX_COUNT={count}")
