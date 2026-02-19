"""
Backdrop System Module

Provides backdrop creation, configuration, and management functions for
cinematic product visualization. Supports infinite curves, gradient materials,
HDRI backdrops, and shadow catcher configuration.

All bpy access is guarded for testing outside Blender.

Usage:
    from lib.cinematic.backdrops import create_backdrop, create_backdrop_from_preset
    from lib.cinematic.backdrops import create_infinite_curve, setup_shadow_catcher
    from lib.cinematic.types import BackdropConfig

    # Create infinite curve backdrop from config
    config = BackdropConfig(
        backdrop_type="infinite_curve",
        radius=5.0,
        curve_height=3.0,
        color_bottom=(0.95, 0.95, 0.95),
        color_top=(1.0, 1.0, 1.0),
        shadow_catcher=True
    )
    backdrop = create_backdrop(config)

    # Create backdrop from preset
    backdrop = create_backdrop_from_preset("studio_white")

    # Set up shadow catcher on existing object
    setup_shadow_catcher(backdrop, enabled=True)
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import math

from .types import BackdropConfig

# Guarded bpy import
try:
    import bpy
    import bmesh
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    bmesh = None
    mathutils = None
    BLENDER_AVAILABLE = False


def create_infinite_curve(
    name: str = "gsd_backdrop",
    radius: float = 5.0,
    curve_height: float = 3.0,
    curve_segments: int = 32,
    depth: float = 10.0
) -> Optional[Any]:
    """
    Create procedural infinite curve backdrop using bmesh.

    Generates a seamless sweep geometry with floor, curved transition,
    and vertical wall sections. Uses bmesh for context-free mesh creation.

    Algorithm:
    1. Generate floor vertices along X axis at Z=0
    2. Generate curve vertices using quarter circle formula (sin/cos)
    3. Generate wall vertices at curve_height
    4. Extrude along Y axis for depth
    5. Connect faces with proper winding order

    Args:
        name: Object name for the backdrop
        radius: Distance from center to floor edge
        curve_height: Height of vertical wall section
        curve_segments: Resolution of curve transition (higher = smoother)
        depth: Extent along Y axis (front to back)

    Returns:
        Created backdrop object, or None if Blender not available

    Note:
        This function does NOT use bpy.ops - uses bmesh directly for
        context-free operation suitable for batch processing.
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Check context
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return None

        scene = bpy.context.scene

        # Create mesh
        mesh = bpy.data.meshes.new(f"{name}_mesh")
        obj = bpy.data.objects.new(name, mesh)

        # Link to scene collection
        scene.collection.objects.link(obj)

        # Build geometry with bmesh
        bm = bmesh.new()

        # Calculate curve radius (proportional to main radius)
        curve_radius = radius * 0.3

        # Generate profile vertices (X-Z plane at Y=0)
        # Three sections: floor, curve, wall
        floor_verts_front = []
        curve_verts_front = []
        wall_verts_front = []

        # Floor vertices (from -radius to -curve_radius on X)
        floor_width = radius - curve_radius
        floor_segments = curve_segments // 2
        if floor_segments < 2:
            floor_segments = 2

        for i in range(floor_segments + 1):
            t = i / floor_segments
            x = -radius + (floor_width * t)
            v = bm.verts.new((x, 0, 0))
            floor_verts_front.append(v)

        # Curve vertices (quarter circle transition)
        for i in range(curve_segments + 1):
            t = i / curve_segments
            angle = math.pi / 2 * t
            x = -curve_radius + (curve_radius * math.cos(angle))
            z = curve_radius * math.sin(angle)
            v = bm.verts.new((x, 0, z))
            curve_verts_front.append(v)

        # Wall vertices (vertical at curve_height)
        wall_width = radius + curve_radius  # -curve_radius to +radius
        wall_segments = curve_segments // 2
        if wall_segments < 2:
            wall_segments = 2

        for i in range(wall_segments + 1):
            t = i / wall_segments
            x = -curve_radius + (wall_width * t)
            v = bm.verts.new((x, 0, curve_height))
            wall_verts_front.append(v)

        # Extrude profile along Y axis (depth)
        # Create back vertices (at Y = -depth)
        all_front_verts = floor_verts_front + curve_verts_front + wall_verts_front
        all_back_verts = []

        for v in all_front_verts:
            back_v = bm.verts.new((v.co.x, -depth, v.co.z))
            all_back_verts.append(back_v)

        # Create faces connecting front to back
        for i in range(len(all_front_verts) - 1):
            # Quad face: front[i], front[i+1], back[i+1], back[i]
            try:
                bm.faces.new([
                    all_front_verts[i],
                    all_front_verts[i + 1],
                    all_back_verts[i + 1],
                    all_back_verts[i]
                ])
            except ValueError:
                # Face already exists, skip
                pass

        # Cap the ends
        # Front cap
        try:
            bm.faces.new(all_front_verts)
        except ValueError:
            pass

        # Back cap (reverse winding)
        try:
            bm.faces.new(list(reversed(all_back_verts)))
        except ValueError:
            pass

        # Update mesh from bmesh
        bm.to_mesh(mesh)
        bm.free()

        # Recalculate normals
        mesh.update()

        return obj

    except Exception:
        # Any Blender access error, return None
        return None


def create_gradient_material(
    name: str = "gsd_backdrop_mat",
    color_bottom: Tuple[float, float, float] = (0.95, 0.95, 0.95),
    color_top: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    gradient_height: float = 3.0
) -> Optional[Any]:
    """
    Create gradient material based on Z position using shader nodes.

    Node tree structure:
    1. ShaderNodeNewGeometry (Position output)
    2. ShaderNodeSeparateXYZ (Z channel)
    3. ShaderNodeMath (DIVIDE by gradient_height)
    4. ShaderNodeValToRGB (ColorRamp for gradient)
    5. ShaderNodeBsdfPrincipled (Base Color from ramp)
    6. ShaderNodeOutputMaterial

    Args:
        name: Material name
        color_bottom: RGB color at Z=0 (0-1 range)
        color_top: RGB color at Z=gradient_height (0-1 range)
        gradient_height: Height over which gradient transitions

    Returns:
        Created material, or None if Blender not available
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Create material
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create nodes in order
        # 1. Geometry node for position
        geometry = nodes.new('ShaderNodeNewGeometry')

        # 2. Separate XYZ for Z position
        separate = nodes.new('ShaderNodeSeparateXYZ')

        # 3. Math node to normalize Z position
        math_divide = nodes.new('ShaderNodeMath')
        math_divide.operation = 'DIVIDE'
        math_divide.inputs[1].default_value = gradient_height

        # 4. Color ramp for gradient
        ramp = nodes.new('ShaderNodeValToRGB')
        # Set interpolation to LINEAR to avoid banding
        ramp.color_ramp.interpolation = 'LINEAR'
        # Configure color stops
        ramp.color_ramp.elements[0].color = (*color_bottom, 1.0)
        ramp.color_ramp.elements[1].color = (*color_top, 1.0)

        # 5. Principled BSDF
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.inputs['Roughness'].default_value = 0.5

        # 6. Material Output
        output = nodes.new('ShaderNodeOutputMaterial')

        # Position nodes in horizontal layout
        geometry.location = (-800, 0)
        separate.location = (-600, 0)
        math_divide.location = (-400, 0)
        ramp.location = (-200, 0)
        principled.location = (0, 0)
        output.location = (200, 0)

        # Link nodes
        links.new(geometry.outputs['Position'], separate.inputs['Vector'])
        links.new(separate.outputs['Z'], math_divide.inputs[0])
        links.new(math_divide.outputs['Value'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        return mat

    except Exception:
        return None


def apply_gradient_material(
    obj: Any,
    color_bottom: Tuple[float, float, float] = (0.95, 0.95, 0.95),
    color_top: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    gradient_height: float = 3.0,
    material_name: Optional[str] = None
) -> Optional[Any]:
    """
    Create and apply gradient material to an object.

    Convenience function that creates a gradient material and assigns it
    to the object's material slots.

    Args:
        obj: Blender object to apply material to
        color_bottom: RGB color at Z=0 (0-1 range)
        color_top: RGB color at Z=gradient_height (0-1 range)
        gradient_height: Height over which gradient transitions
        material_name: Optional name for the material (auto-generated if None)

    Returns:
        Created material, or None if failed
    """
    if not BLENDER_AVAILABLE or obj is None:
        return None

    try:
        # Generate material name if not provided
        if material_name is None:
            material_name = f"{obj.name}_gradient_mat"

        # Create gradient material
        mat = create_gradient_material(
            name=material_name,
            color_bottom=color_bottom,
            color_top=color_top,
            gradient_height=gradient_height
        )

        if mat is None:
            return None

        # Assign material to object
        if obj.data.materials:
            # Replace existing material
            obj.data.materials[0] = mat
        else:
            # Add new material slot
            obj.data.materials.append(mat)

        return mat

    except Exception:
        return None


def setup_shadow_catcher(
    obj: Any,
    enabled: bool = True
) -> bool:
    """
    Configure object as shadow catcher for alpha compositing.

    Sets up the object to receive shadows while being transparent
    in the final render. This is essential for product photography
    compositing workflows.

    For Cycles: Uses is_shadow_catcher property
    For EEVEE: Configures material blend/shadow settings

    Args:
        obj: Blender object to configure
        enabled: True to enable shadow catcher, False to disable

    Returns:
        True if successful, False if failed

    Note:
        Requires film_transparent = True in render settings for
        correct alpha output. Use configure_render_for_shadow_catcher()
        to set this up.
    """
    if not BLENDER_AVAILABLE or obj is None:
        return False

    try:
        # Set shadow catcher property (Cycles)
        if hasattr(obj, 'is_shadow_catcher'):
            obj.is_shadow_catcher = enabled

        # Configure material settings if material exists
        if hasattr(obj.data, 'materials') and obj.data.materials:
            mat = obj.data.materials[0]
            if mat is not None:
                # Shadow method for shadows
                if hasattr(mat, 'shadow_method'):
                    mat.shadow_method = 'CLIP'

                # Backface culling for correct alpha
                if hasattr(mat, 'use_backface_culling'):
                    mat.use_backface_culling = True

                # Blend method for transparency
                if hasattr(mat, 'blend_method'):
                    mat.blend_method = 'HASHED'

        return True

    except Exception:
        return False


def configure_render_for_shadow_catcher(
    scene: Optional[Any] = None
) -> bool:
    """
    Configure render settings for shadow catcher output.

    Sets up the scene to output correct alpha channel for shadow
    catcher compositing. This must be called after setup_shadow_catcher()
    for proper results.

    Settings configured:
    - film_transparent: True (enables alpha output)
    - use_pass_shadow: True (enables shadow pass)

    Args:
        scene: Blender scene to configure (uses current scene if None)

    Returns:
        True if successful, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Get scene from context if not provided
        if scene is None:
            if not hasattr(bpy, "context") or bpy.context.scene is None:
                return False
            scene = bpy.context.scene

        # Enable transparent film for alpha output
        scene.render.film_transparent = True

        # Enable shadow pass
        if hasattr(scene, 'view_layers') and scene.view_layers:
            view_layer = scene.view_layers[0]
            if hasattr(view_layer, 'use_pass_shadow'):
                view_layer.use_pass_shadow = True

        return True

    except Exception:
        return False


def create_backdrop(
    config: Optional[BackdropConfig] = None,
    **kwargs
) -> Optional[Any]:
    """
    Create backdrop with specified configuration.

    Main entry point for backdrop creation. Supports both BackdropConfig
    objects and keyword arguments. Dispatches to appropriate backdrop
    creation function based on backdrop_type.

    Supported backdrop types:
    - infinite_curve: Procedural sweep geometry with gradient material
    - hdri: HDRI environment lighting (delegates to hdri.py)
    - gradient: Gradient-only backdrop (future implementation)
    - mesh: Custom mesh file (future implementation)

    Args:
        config: BackdropConfig with all settings (uses kwargs if None)
        **kwargs: Individual settings to create BackdropConfig

    Returns:
        Created backdrop object (None for HDRI backdrops which modify world)

    Example:
        # Using config object
        config = BackdropConfig(
            backdrop_type="infinite_curve",
            radius=5.0,
            curve_height=3.0
        )
        backdrop = create_backdrop(config)

        # Using keyword arguments
        backdrop = create_backdrop(
            backdrop_type="infinite_curve",
            radius=5.0,
            curve_height=3.0,
            color_bottom=(0.9, 0.9, 0.9),
            color_top=(1.0, 1.0, 1.0),
            shadow_catcher=True
        )
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Create config from kwargs if not provided
        if config is None:
            config = BackdropConfig(**kwargs)

        backdrop_type = config.backdrop_type

        if backdrop_type == "infinite_curve":
            # Create infinite curve geometry
            obj = create_infinite_curve(
                name="gsd_backdrop",
                radius=config.radius,
                curve_height=config.curve_height,
                curve_segments=config.curve_segments
            )

            if obj is None:
                return None

            # Apply gradient material
            apply_gradient_material(
                obj,
                color_bottom=config.color_bottom,
                color_top=config.color_top,
                gradient_height=config.curve_height
            )

            # Configure shadow catcher if enabled
            if config.shadow_catcher:
                setup_shadow_catcher(obj, enabled=True)
                configure_render_for_shadow_catcher()

            return obj

        elif backdrop_type == "hdri":
            # Delegate to hdri.py for HDRI backdrops
            from .hdri import setup_hdri, load_hdri_preset

            if config.hdri_preset:
                # Load from preset
                success = load_hdri_preset(config.hdri_preset)
            else:
                # Set up directly (would need file path in config)
                # For now, just return None as HDRI preset is required
                return None

            # HDRI backdrops modify world settings, not objects
            return None if success else None

        elif backdrop_type == "gradient":
            # Future: gradient-only backdrop
            # For now, treat as infinite_curve
            obj = create_infinite_curve(
                name="gsd_backdrop",
                radius=config.radius,
                curve_height=config.curve_height,
                curve_segments=config.curve_segments
            )

            if obj is None:
                return None

            apply_gradient_material(
                obj,
                color_bottom=config.color_bottom,
                color_top=config.color_top,
                gradient_height=config.curve_height
            )

            return obj

        elif backdrop_type == "mesh":
            # Future: load mesh from file
            # For now, return None
            return None

        else:
            # Unknown backdrop type
            return None

    except Exception:
        return None


def create_backdrop_from_preset(preset_name: str) -> Optional[Any]:
    """
    Create backdrop from named preset.

    Dispatches to the correct preset loader based on preset type.
    Tries preset loaders in order:
    1. Infinite curve presets (get_infinite_curve_preset)
    2. Gradient presets (get_gradient_preset)
    3. Environment/HDRI presets (get_environment_preset)

    Args:
        preset_name: Name of the preset to load

    Returns:
        Created backdrop object, or None if failed

    Raises:
        ValueError: If preset not found in any preset file

    Example:
        # Load infinite curve preset
        backdrop = create_backdrop_from_preset("studio_white")

        # Load HDRI preset
        backdrop = create_backdrop_from_preset("product_studio")
    """
    if not BLENDER_AVAILABLE:
        return None

    from .preset_loader import (
        get_infinite_curve_preset,
        get_gradient_preset,
        get_environment_preset,
        list_infinite_curve_presets,
        list_gradient_presets,
        list_environment_presets
    )

    # Try infinite curve preset first
    try:
        preset = get_infinite_curve_preset(preset_name)
        config = BackdropConfig(
            backdrop_type="infinite_curve",
            radius=preset.get("radius", 5.0),
            curve_height=preset.get("curve_height", 3.0),
            curve_segments=preset.get("curve_segments", 32),
            color_bottom=tuple(preset.get("color_bottom", [0.95, 0.95, 0.95])),
            color_top=tuple(preset.get("color_top", [1.0, 1.0, 1.0])),
            shadow_catcher=preset.get("shadow_catcher", True)
        )
        return create_backdrop(config)
    except (ValueError, FileNotFoundError):
        pass

    # Try gradient preset
    try:
        preset = get_gradient_preset(preset_name)
        config = BackdropConfig(
            backdrop_type="gradient",
            color_bottom=tuple(preset.get("color_bottom", [0.95, 0.95, 0.95])),
            color_top=tuple(preset.get("color_top", [1.0, 1.0, 1.0])),
            gradient_type=preset.get("gradient_type", "linear"),
            gradient_stops=preset.get("stops", [])
        )
        return create_backdrop(config)
    except (ValueError, FileNotFoundError):
        pass

    # Try environment/HDRI preset
    try:
        preset = get_environment_preset(preset_name)
        hdri_preset = preset.get("hdri_preset", "")
        if hdri_preset:
            config = BackdropConfig(
                backdrop_type="hdri",
                hdri_preset=hdri_preset
            )
            return create_backdrop(config)
    except (ValueError, FileNotFoundError):
        pass

    # No preset found - raise with helpful message
    available = []
    try:
        available.extend(list_infinite_curve_presets())
    except (FileNotFoundError, RuntimeError):
        pass
    try:
        available.extend(list_gradient_presets())
    except (FileNotFoundError, RuntimeError):
        pass
    try:
        available.extend(list_environment_presets())
    except (FileNotFoundError, RuntimeError):
        pass

    raise ValueError(
        f"Backdrop preset '{preset_name}' not found. "
        f"Available presets: {sorted(set(available))}"
    )


def delete_backdrop(name: str = "gsd_backdrop") -> bool:
    """
    Delete a backdrop object and its associated material.

    Removes the backdrop object from the scene and deletes its
    mesh data and material to free resources.

    Args:
        name: Name of the backdrop object to delete

    Returns:
        True if deleted, False if not found or failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Find backdrop object
        if name not in bpy.data.objects:
            return False

        obj = bpy.data.objects[name]
        mesh = obj.data
        materials = list(obj.data.materials) if hasattr(obj.data, 'materials') else []

        # Unlink from all collections
        for collection in bpy.data.collections:
            if obj.name in collection.objects:
                collection.objects.unlink(obj)

        # Also check scene collection
        if hasattr(bpy.context, "scene") and bpy.context.scene is not None:
            scene_collection = bpy.context.scene.collection
            if obj.name in scene_collection.objects:
                scene_collection.objects.unlink(obj)

        # Delete object
        bpy.data.objects.remove(obj)

        # Delete mesh data
        if mesh and mesh.name in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)

        # Delete associated materials (only if named for backdrop)
        for mat in materials:
            if mat and "gsd_backdrop" in mat.name:
                if mat.name in bpy.data.materials:
                    bpy.data.materials.remove(mat)

        return True

    except Exception:
        return False


def get_backdrop(name: str = "gsd_backdrop") -> Optional[Any]:
    """
    Get a backdrop object by name.

    Args:
        name: Name of the backdrop object

    Returns:
        Backdrop object, or None if not found
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        if name not in bpy.data.objects:
            return None

        return bpy.data.objects[name]
    except Exception:
        return None


def list_backdrops() -> List[str]:
    """
    List all backdrop objects in the current scene.

    Returns:
        List of backdrop object names (starting with "gsd_backdrop")
    """
    if not BLENDER_AVAILABLE:
        return []

    try:
        backdrops = []
        for obj in bpy.data.objects:
            if obj.type == "MESH" and obj.name.startswith("gsd_backdrop"):
                backdrops.append(obj.name)
        return sorted(backdrops)
    except Exception:
        return []
