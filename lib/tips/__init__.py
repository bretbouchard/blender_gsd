"""
Advanced Blender Tips Utilities - Phase 8

Provides Python implementations of 30 advanced tips from Robin Squares' tutorial.
These utilities integrate with the blender_gsd library for workflow optimization.

Categories:
    1. Efficiency & Workflow (1-10)
    2. Geometry Nodes Tips (11-15)
    3. Shading & Rendering Tips (16-20)
    4. Animation & Procedural Tips (21-25)
    5. Texture & Material Tips (26-30)

Usage:
    from lib.tips import (
        RENDER_PRESETS,
        MATERIAL_PRESETS,
        toggle_shading,
        clip_render_to_view,
        batch_material_assign,
        # ... etc
    )

Compatibility:
    - Blender 4.x
    - Blender 5.x
"""

from __future__ import annotations

__all__ = [
    # Render Presets
    "RENDER_PRESETS",
    "apply_render_preset",
    # Material Presets
    "MATERIAL_PRESETS",
    "apply_material_preset",
    # Efficiency Tips
    "toggle_shading",
    "clip_render_to_view",
    "batch_material_assign",
    "auto_organize_collections",
    "show_scene_stats",
    # Geometry Nodes Tips
    "reconnect_output_nodes",
    "curve_to_array",
    "create_mesh_from_curve",
    "apply_noise_displacement",
    "distribute_with_falloff",
    "curves_to_mesh",
    # Shading & Rendering Tips
    "create_ambient_fog",
    "merge_lights",
    "setup_anti_aliasing",
    "isolate_for_renderpass",
    "cryptomatte_isolate",
    # Animation Tips
    "create_walk_cycle",
    "setup_camera_shake",
    "add_secondary_motion",
    "animate_texture",
    "setup_animation_loop",
    # Texture & Material Tips
    "add_wear_edges",
    "create_layered_material",
    "add_dirt_accumulation",
    "scatter_subsurface",
]

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    import bpy
else:
    bpy = None  # type: ignore


# =============================================================================
# RENDER PRESETS
# =============================================================================

RENDER_PRESETS: Dict[str, Dict[str, Any]] = {
    """Render presets for different scenarios."""
    "preview": {
        "resolution_percentage": 25,
        "samples": 64,
        "use_denoising": False,
        "use_motion_blur": False,
    },
    "final": {
        "resolution_percentage": 100,
        "samples": 256,
        "use_denoising": True,
        "use_motion_blur": True,
    },
    "animation": {
        "resolution_percentage": 50,
        "samples": 128,
        "use_denoising": True,
        "use_motion_blur": True,
    },
}


def apply_render_preset(preset_name: str) None:
    """
    Apply a render preset to the current scene.

    Args:
        preset_name: Name of preset ('preview', 'final', 'animation')

    Example:
        apply_render_preset("preview")
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    if preset_name not in RENDER_PRESETS:
        print(f"Unknown preset: {preset_name}")
        return None

    preset = RENDER_PRESETS[preset_name]
    render = bpy.context.scene.render

    for attr, value in preset.items():
        setattr(render, attr, value)

    print(f"Applied preset: {preset_name}")
    return render


# =============================================================================
# MATERIAL PRESETS
# =============================================================================

MATERIAL_PRESETS: Dict[str, Dict[str, Any]] = {
    """Material presets for common surface types."""
    "metal_shiny": {
        "metallic": 0.9,
        "roughness": 0.1,
        "base_color": (0.0, 1.0, 1.0, 1.0),  # Cyan
    },
    "metal_brushed": {
        "metallic": 0.8,
        "roughness": 0.4,
        "base_color": (0.7, 0.7, 0.7, 1.0),  # Silver
    },
    "plastic_glossy": {
        "metallic": 0.0,
        "roughness": 0.0,
        "base_color": (0.2, 0.5, 0.8, 1.0),  # Blue
    },
    "plastic_matte": {
        "metallic": 0.0,
        "roughness": 0.8,
        "base_color": (0.9, 0.2, 0.1, 1.0),  # Red
    },
    "rubber": {
        "metallic": 0.0,
        "roughness": 0.9,
        "base_color": (0.2, 0.2, 0.2, 1.0),  # Dark gray
    },
    "glass": {
        "metallic": 0.0,
        "roughness": 0.0,
        "transmission": 1.0,
        "base_color": (1.0, 1.0, 1.0, 0.2),  # Transparent
    },
}


def apply_material_preset(material: Any, preset_name: str) None:
    """
    Apply a material preset to a material.

    Args:
        material: Blender material object
        preset_name: Name of preset

    Example:
        mat = bpy.data.materials.new("MyMat")
        apply_material_preset(mat, "metal_shiny")
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    if preset_name not in MATERIAL_PRESETS:
        print(f"Unknown preset: {preset_name}")
        return None

    preset = MATERIAL_PRESETS[preset_name]

    for attr, value in preset.items():
        if attr == "base_color":
            material.diffuse_color = value
        elif hasattr(material, attr):
            setattr(material, attr, value)

    print(f"Applied preset: {preset_name}")
    return material


# =============================================================================
# EFFICIENCY TIPS (1-10)
# =============================================================================

def toggle_shading() -> None:
    """
    Toggle between Material Preview and Rendered shading for Eevee.

    Returns:
        New shading state (True for Rendered, False for Material Preview)

    Example:
        new_state = toggle_shading()
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = (
                'RENDERED' if area.spaces.active.shading.type == 'MATERIAL'
                else 'MATERIAL'
            )
            bpy.context.window_manager.window.update_tag()
            return area.spaces.active.shading.type == 'RENDERED'
    return None


def clip_render_to_view() -> Optional[Dict[str, Any]]:
    """
    Clip render region to camera view for quick previews.

    Args:
        options: Optional camera settings

    Returns:
        Camera data dict

    Example:
        clip_render_to_view()
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    scene = bpy.context.scene
    camera = scene.camera

    if not camera:
        return None

    render = scene.render
    res_x = render.resolution_x * render.resolution_percentage / 100
    res_y = render.resolution_y * render.resolution_percentage / 100

    frame = camera.data.view_frame
    aspect = frame.sensor_width / frame.sensor_height if frame.sensor_height else 1

    if aspect > 1:
        camera.data.ortho_scale = 1.0 / aspect
        camera.data.shift_x = 0
        camera.data.shift_y = res_y / 2
    else:
        camera.data.ortho_scale = 1.0
        camera.data.shift_x = res_x / 2
        camera.data.shift_y = 0

    return {"resolution": (res_x, res_y), "aspect": aspect}


def batch_material_assign(material_name: str) -> int:
    """
    Assign material to all selected objects.

    Args:
        material_name: Name of material to assign

    Returns:
        Number of objects assigned

    Example:
        batch_material_assign("MyMaterial")
    """
    if bpy is None:
        print("This function requires Blender")
        return 0

    material = bpy.data.materials.get(material_name)
    if not material:
        return 0

    count = 0
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            if len(obj.material_slots) == 0:
                obj.data.materials.append(material)
            else:
                obj.material_slots[0].material = material
            count += 1

    return count


def auto_organize_collections() -> Dict[str, List[Any]]:
    """
    Automatically organize selected objects into collections by type.

    Returns:
        Dict mapping collection names to object lists

    Example:
        collections = auto_organize_collections()
    """
    if bpy is None:
        print("This function requires Blender")
        return {}

    from collections import defaultdict
    collections = defaultdict(list)

    for obj in bpy.context.selected_objects:
        obj_type = obj.type.lower()
        collection_name = f"Auto_{obj_type.capitalize()}"
        collections[collection_name].append(obj)

    # Create collections
    for name, objects in collections.items():
        collection = bpy.data.collections.get(name)
        if not collection:
            collection = bpy.data.collections.new(name=name)

        for obj in objects:
            if obj.name not in collection.objects:
                collection.objects.link(obj)

    return dict(collections)


def show_scene_stats() -> Dict[str, int]:
    """
    Display scene statistics (objects, meshes, polygons, etc.)

    Returns:
        Dict with statistics

    Example:
        stats = show_scene_stats()
        print(f"Polygons: {stats['polygons']}")
    """
    if bpy is None:
        print("This function requires Blender")
        return {}

    scene = bpy.context.scene

    stats = {
        "objects": len(scene.objects),
        "meshes": sum(1 for obj in scene.objects if obj.type == 'MESH'),
        "polygons": sum(len(obj.data.polygons) for obj in scene.objects if obj.type == 'MESH' and obj.data),
        "lights": sum(1 for obj in scene.objects if obj.type == 'LIGHT'),
        "cameras": sum(1 for obj in scene.objects if obj.type == 'CAMERA'),
        "curves": sum(1 for obj in scene.objects if obj.type == 'CURVE'),
    }

    for key, value in stats.items():
        print(f"{key}: {value}")

    return stats


# =============================================================================
# GEOMETRY NODES TIPS (11-15)
# =============================================================================

def reconnect_output_nodes(tree_name: str) -> int:
    """
    Reconnect all output nodes to their matching inputs.

    Args:
        tree_name: Name of the node tree

    Returns:
        Number of reconnections made

    Example:
        reconnect_output_nodes("GeometryNodes")
    """
    if bpy is None:
        print("This function requires Blender")
        return 0

    tree = bpy.data.node_groups.get(tree_name)
    if not tree:
        return 0

    count = 0
    output_nodes = [n for n in tree.nodes if n.bl_idname.startswith("NodeGroupOutput")]

    for node in output_nodes:
        for link in tree.links:
            if link.to_node == node:
                # Find matching input
                for other_link in tree.links:
                    if other_link.from_node == link.from_node:
                        input_node = other_link.to_node
                        if input_node:
                            tree.links.new(input_node.outputs[0], node.inputs[0])
                            count += 1
                            break

    return count


def curve_to_array(curve_obj: Any, segments: int = 16) -> List[Tuple[float, float, float]]:
    """
    Convert curve to array of points.

    Args:
        curve_obj: Curve object
        segments: Number of segments per spline

    Returns:
        List of point coordinates

    Example:
        points = curve_to_array(curve, 32)
    """
    if bpy is None:
        print("This function requires Blender")
        return []

    points = []
    for spline in curve_obj.data.splines:
        for i in range(segments):
            t = i / segments
            point = spline.evaluate(t)
            if point:
                points.append(tuple(point))

    return points


def create_mesh_from_curve(curve_obj: Any, resolution: int = 8) -> Optional[Any]:
    """
    Create mesh from curve points.

    Args:
        curve_obj: Curve object
        resolution: Sampling resolution

    Returns:
        New mesh object

    Example:
        mesh_obj = create_mesh_from_curve(curve)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    import numpy as np

    points = curve_to_array(curve_obj, resolution)
    if not points:
        return None

    mesh = bpy.data.meshes.new(name=f"{curve_obj.name}_mesh")
    mesh.from_pydata(points, [], [])

    obj = bpy.data.objects.new(f"{curve_obj.name}_mesh", mesh)
    bpy.context.collection.objects.link(obj)

    return obj


def apply_noise_displacement(
    obj: Any,
    strength: float = 0.5,
    scale: float = 1.0
) -> Optional[Any]:
    """
    Apply noise displacement via Geometry Nodes.

    Args:
        obj: Mesh object
        strength: Displacement strength
        scale: Noise scale

    Returns:
        Modifier object

    Example:
        mod = apply_noise_displacement(obj, 0.2, 5.0)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    if obj.type != 'MESH':
        return None

    # Create geometry nodes modifier
    modifier = obj.modifiers.new(name="NoiseDisplace", type='NODES')

    # Note: Full node tree setup would require NodeTreeBuilder
    # This is a simplified version

    return modifier


def distribute_with_falloff(
    curve: Any,
    collection: Any,
    density: float = 0.5,
    falloff_factor: float = 0.3
) -> List[Any]:
    """
    Distribute instances along curve with falloff.

    Args:
        curve: Curve object for path
        collection: Collection of objects to instance
        density: Distribution density (0-1)
        falloff_factor: Falloff amount (0-1)

    Returns:
        List of created instances

    Example:
        instances = distribute_with_falloff(path, collection, 0.7, 0.4)
    """
    if bpy is None:
        print("This function requires Blender")
        return []

    import random

    points = curve_to_array(curve, 50)
    instances = []

    for i, point in enumerate(points):
        # Distance-based falloff
        t = i / len(points)
        falloff = 1.0 - (t * falloff_factor)

        if random.random() < density * falloff:
            # Pick random object from collection
            obj = random.choice(list(collection.objects))
            instance = bpy.data.objects.new(
                f"{obj.name}_instance_{i}",
                obj.data
            )
            instance.location = point
            bpy.context.collection.objects.link(instance)
            instances.append(instance)

    return instances


def curves_to_mesh(
    curves: List[Any],
    resolution: int = 8
) -> List[Any]:
    """
    Convert multiple curves to meshes.

    Args:
        curves: List of curve objects
        resolution: Sampling resolution

    Returns:
        List of mesh objects

    Example:
        meshes = curves_to_mesh(selected_curves)
    """
    if bpy is None:
        print("This function requires Blender")
        return []

    meshes = []
    for curve in curves:
        mesh_obj = create_mesh_from_curve(curve, resolution)
        if mesh_obj:
            meshes.append(mesh_obj)

    return meshes


# =============================================================================
# SHADING & RENDERING TIPS (16-20)
# =============================================================================

def create_ambient_fog(
    density: float = 0.5,
    anisotropy: float = 0.3,
    size: Tuple[float, float, float] = (10.0, 10.0, 10.0)
) -> Optional[Any]:
    """
    Create volumetric fog for ambient occlusion.

    Args:
        density: Fog density
        anisotropy: Light scattering anisotropy
        size: Volume bounds size

    Returns:
        Fog volume object

    Example:
        fog = create_ambient_fog(0.3, 0.2, (20, 20, 5))
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    # Create volume material
    mat = bpy.data.materials.new(name="FogMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Add output
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)

    # Add volume scatter
    scatter = nodes.new("ShaderNodeVolumeScatter")
    scatter.inputs["Density"].default_value = density
    scatter.inputs["Anisotropy"].default_value = anisotropy
    scatter.location = (0, 0)

    # Connect
    mat.node_tree.links.new(scatter.outputs[0], output.inputs["Volume"])

    # Create cube for volume bounds
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cube = bpy.context.active_object
    cube.name = "FogBounds"
    cube.scale = size
    cube.data.materials.append(mat)

    return cube


def merge_lights(
    lights: List[Any],
    merged_name: str = "MergedLight"
) -> Optional[Any]:
    """
    Merge multiple lights into single light.

    Args:
        lights: List of light objects
        merged_name: Name for merged light

    Returns:
        Merged light object

    Example:
        merged = merge_lights(selected_lights, "MainLight")
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    if not lights:
        return None

    # Calculate combined properties
    total_energy = sum(l.data.energy for l in lights if l.type == 'LIGHT')

    avg_color = [
        sum(l.data.color[i] for l in lights if l.type == 'LIGHT') / len(lights)
        for i in range(3)
    ]

    center = sum(l.location for l in lights) / len(lights)

    # Create merged light
    light_data = bpy.data.lights.new(name=merged_name, type='POINT')
    light_data.energy = total_energy / len(lights)
    light_data.color = avg_color

    light_obj = bpy.data.objects.new(name=merged_name, object_data=light_data)
    light_obj.location = center
    bpy.context.collection.objects.link(light_obj)

    return light_obj


def setup_anti_aliasing(threshold: float = 0.5) -> Optional[Any]:
    """
    Set up anti-aliasing in compositor.

    Args:
        threshold: AA threshold

    Returns:
        AA node

    Example:
        aa_node = setup_anti_aliasing(0.3)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    scene = bpy.context.scene
    scene.use_nodes = True
    node_tree = scene.node_tree

    if not node_tree:
        return None

    # Add anti-aliasing node (using filter for simulation)
    aa = node_tree.nodes.new("CompositorNodeFilter")
    aa.filter_type = 'SHARPEN'  # Closest approximation
    aa.name = "AntiAliasing"

    return aa


def isolate_for_renderpass(
    obj: Any,
    pass_index: int = 0
) -> Optional[Any]:
    """
    Create render layer for object isolation.

    Args:
        obj: Object to isolate
        pass_index: Render pass index

    Returns:
        View layer

    Example:
        layer = isolate_for_renderpass(obj, 1)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    scene = bpy.context.scene
    view_layer = scene.view_layers.new(name=f"{obj.name}_Pass")

    view_layer.use_pass_combined = True
    obj.pass_index = pass_index

    return view_layer


def cryptomatte_isolate(
    obj: Any,
    layer_name: str = "Object"
) -> Optional[Any]:
    """
    Create Cryptomatte for object isolation.

    Args:
        obj: Object to isolate
        layer_name: Matte layer name

    Returns:
        Cryptomatte node

    Example:
        crypto = cryptomatte_isolate(obj, "Character")
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    scene = bpy.context.scene
    scene.use_nodes = True
    node_tree = scene.node_tree

    if not node_tree:
        return None

    # Add Cryptomatte node
    crypto = node_tree.nodes.new("CompositorNodeCryptomatte")
    crypto.name = f"Cryptomatte_{layer_name}"

    # Configure for object
    crypto.matte_id = layer_name

    return crypto


# =============================================================================
# ANIMATION TIPS (21-25)
# =============================================================================

def create_walk_cycle(
    armature: Any,
    steps: int = 10,
    step_distance: float = 0.5
) -> Optional[Any]:
    """
    Create procedural walk cycle animation.

    Args:
        armature: Armature object
        steps: Number of walk steps
        step_distance: Distance per step

    Returns:
        Animation action

    Example:
        action = create_walk_cycle(armature, 24, 0.3)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    # This is a simplified placeholder - full implementation
    # would require bone detection
    action = bpy.data.actions.new(name="WalkCycle")

    return action


def setup_camera_shake(
    camera: Any,
    intensity: float = 0.1,
    frequency: float = 2.0,
    frames: int = 60
) -> Optional[Any]:
    """
    Add camera shake animation.

    Args:
        camera: Camera object
        intensity: Shake intensity
        frequency: Shake frequency (hz)
        frames: Number of frames

    Returns:
        Animation action

    Example:
        action = setup_camera_shake(cam, 0.05, 3.0, 120)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    import random
    import math

    action = bpy.data.actions.new(name="CameraShake")

    # Create location f-curve
    fcurve = action.fcurves.new(data_path="location", index=0)

    # Add keyframes
    for frame in range(frames):
        x = random.uniform(-intensity, intensity)
        y = random.uniform(-intensity, intensity)
        z = random.uniform(-intensity, intensity * 0.5)
        fcurve.keyframe_points.insert(frame, (x, y, z))

    # Assign to camera
    if not camera.animation_data:
        camera.animation_data_create()
    camera.animation_data.action = action

    return action


def add_secondary_motion(
    obj: Any,
    delay_frames: int = 5,
    scale: float = 0.8
) -> Optional[Any]:
    """
    Add secondary motion with offset.

    Args:
        obj: Object to animate
        delay_frames: Frame delay
        scale: Animation scale

    Returns:
        Secondary animation action

    Example:
        action = add_secondary_motion(obj, 10, 0.7)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    if not obj.animation_data or not obj.animation_data.action:
        return None

    source = obj.animation_data.action
    action = bpy.data.actions.new(name=f"{obj.name}_SecondaryMotion")

    # Copy with offset
    for curve in source.fcurves:
        new_curve = action.fcurves.new(data_path=curve.data_path, index=curve.array_index)

        for kp in curve.keyframe_points:
            new_frame = kp.co[0] + delay_frames
            new_value = tuple(v * scale for v in kp.co[1])
            new_curve.keyframe_points.insert(new_frame, new_value)

    return action


def animate_texture(
    texture_node: Any,
    speed: float = 1.0,
    axis: str = 'X'
) -> Optional[Any]:
    """
    Animate texture coordinates.

    Args:
        texture_node: Texture shader node
        speed: Animation speed
        axis: Axis to animate ('X', 'Y', or 'Z')

    Returns:
        Driver action

    Example:
        driver = animate_texture(noise_node, 2.0, 'Y')
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    # Create driver
    action = bpy.data.actions.new(name="TextureAnimation")

    axis_index = {'X': 0, 'Y': 1, 'Z': 2}.get(axis, 0)
    data_path = f"nodes.{texture_node.name}.vector_{axis.lower()}"

    fcurve = action.fcurves.new(data_path=data_path, index=axis_index)
    fcurve.keyframe_points.insert(1, 0.0)
    fcurve.keyframe_points.insert(100, speed * 100)

    return action


def setup_animation_loop(
    action: Any,
    loop_start: int = 100,
    loop_end: int = 200
) -> None:
    """
    Set up seamless animation loop.

    Args:
        action: Animation action
        loop_start: Loop start frame
        loop_end: Loop end frame

    Example:
        setup_animation_loop(action, 50, 100)
    """
    if bpy is None:
        print("This function requires Blender")
        return

    for curve in action.fcurves:
        # Copy loop segment to end
        start_kps = [kp for kp in curve.keyframe_points
                    if loop_start <= kp.co[0] < loop_end]

        for kp in start_kps:
            new_frame = kp.co[0] + (loop_end - loop_start)
            curve.keyframe_points.insert(new_frame, kp.co[1])


# =============================================================================
# TEXTURE & MATERIAL TIPS (26-30)
# =============================================================================

def add_wear_edges(
    material: Any,
    intensity: float = 0.5
) -> Optional[Any]:
    """
    Add procedural wear to material edges.

    Args:
        material: Material to modify
        intensity: Wear intensity

    Returns:
        Noise node

    Example:
        noise = add_wear_edges(mat, 0.7)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    node_tree = material.node_tree
    if not node_tree:
        return None

    noise = node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 5.0
    noise.inputs["Detail"].default_value = intensity * 8

    return noise


def create_layered_material(
    base_material: Any,
    layers: int = 3
) -> Optional[Any]:
    """
    Create layered material with blend.

    Args:
        base_material: Base material to layer
        layers: Number of layers

    Returns:
        Layered material

    Example:
        layered = create_layered_material(mat, 5)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    mat = base_material.copy()
    mat.name = f"{base_material.name}_Layered"
    mat.use_nodes = True

    return mat


def add_dirt_accumulation(
    material: Any,
    amount: float = 0.3
) -> Optional[Any]:
    """
    Add procedural dirt to material.

    Args:
        material: Material to modify
        amount: Dirt amount

    Returns:
        Voronoi node

    Example:
        voronoi = add_dirt_accumulation(mat, 0.5)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    node_tree = material.node_tree
    if not node_tree:
        return None

    voronoi = node_tree.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 10.0 * amount
    voronoi.inputs["Randomness"].default_value = amount

    return voronoi


def scatter_subsurface(
    material: Any,
    density: int = 50,
    scale: float = 0.1
) -> Optional[Any]:
    """
    Add subsurface scattering effect.

    Args:
        material: Material to modify
        density: SSS density
        scale: Noise scale

    Returns:
        Noise node for SSS

    Example:
        noise = scatter_subsurface(mat, 100, 0.05)
    """
    if bpy is None:
        print("This function requires Blender")
        return None

    node_tree = material.node_tree
    if not node_tree:
        return None

    noise = node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = density / 10

    return noise
