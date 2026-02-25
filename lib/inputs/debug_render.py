"""
Debug Render Utilities for Control Surface System

Provides render scripts and utilities for generating debug visualization
renders of control surfaces with per-section coloring.

Usage:
    from lib.inputs.debug_render import render_debug_view, DebugRenderConfig

    # Create debug render configuration
    config = DebugRenderConfig(
        output_path="/renders/debug/",
        preset="rainbow",
        resolution=(1920, 1080)
    )

    # Render debug view
    render_debug_view(config)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import bpy

from .debug_materials import (
    create_all_debug_materials,
    create_debug_palette,
    SECTION_NAMES,
    DEBUG_PRESETS,
)


@dataclass
class DebugRenderConfig:
    """Configuration for debug rendering."""

    # Output settings
    output_path: str = "//renders/debug/"
    file_prefix: str = "debug_"
    file_format: str = "PNG"  # PNG, JPEG, EXR

    # Resolution
    resolution: Tuple[int, int] = (1920, 1080)

    # Debug settings
    preset: str = "rainbow"  # rainbow, grayscale, complementary, heat_map
    metallic: float = 0.0
    roughness: float = 0.5

    # Render settings
    samples: int = 16
    use_denoising: bool = True
    transparent_background: bool = True

    # View settings
    camera_distance: float = 0.5
    camera_angle: float = 45.0  # degrees from horizontal
    use_orthographic: bool = False
    orthographic_scale: float = 0.05


@dataclass
class DebugRenderResult:
    """Result of a debug render operation."""

    success: bool
    output_path: str = ""
    error: str = ""
    render_time_seconds: float = 0.0


def setup_debug_scene(config: DebugRenderConfig) -> Dict[str, bpy.types.Material]:
    """
    Set up the scene for debug rendering.

    Creates debug materials and configures render settings.

    Args:
        config: Debug render configuration

    Returns:
        Dictionary mapping section names to debug materials
    """
    # Create debug materials
    materials = create_all_debug_materials(
        preset=config.preset,
        metallic=config.metallic,
        roughness=config.roughness
    )

    # Configure render settings
    scene = bpy.context.scene

    # Resolution
    scene.render.resolution_x = config.resolution[0]
    scene.render.resolution_y = config.resolution[1]
    scene.render.resolution_percentage = 100

    # File format
    scene.render.image_settings.file_format = config.file_format

    # Transparency
    scene.render.film_transparent = config.transparent_background

    # Cycles settings
    if scene.cycles:
        scene.cycles.samples = config.samples
        scene.cycles.use_denoising = config.use_denoising

    return materials


def create_debug_camera(config: DebugRenderConfig) -> bpy.types.Object:
    """
    Create a camera for debug rendering.

    Args:
        config: Debug render configuration

    Returns:
        The created camera object
    """
    # Create camera
    cam_data = bpy.data.cameras.new("Debug_Camera")
    cam_obj = bpy.data.objects.new("Debug_Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)

    # Set camera type
    if config.use_orthographic:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = config.orthographic_scale
    else:
        cam_data.type = 'PERSP'
        cam_data.lens = 50  # 50mm lens

    # Position camera
    import math
    angle_rad = math.radians(config.camera_angle)
    distance = config.camera_distance

    x = distance * math.sin(angle_rad)
    z = distance * math.cos(angle_rad)

    cam_obj.location = (x, -distance, z)

    # Point camera at origin
    direction = (-x, distance, -z)
    rot_quat = cam_obj.matrix_world.to_quaternion()
    # Use track-to constraint for simplicity
    track = cam_obj.constraints.new('TRACK_TO')
    track.target = None  # Will track origin
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    return cam_obj


def apply_debug_materials_to_object(
    obj: bpy.types.Object,
    materials: Dict[str, bpy.types.Material],
    section_name: str = "A_Top"
) -> None:
    """
    Apply a debug material to an object.

    For objects with geometry nodes, sets the debug material inputs.

    Args:
        obj: Blender object
        materials: Dictionary of debug materials by section name
        section_name: Which section's debug material to apply
    """
    if section_name not in materials:
        section_name = SECTION_NAMES[0]

    mat = materials[section_name]

    # Check if object has geometry nodes modifier
    for modifier in obj.modifiers:
        if modifier.type == 'NODES' and modifier.node_group:
            # Try to find and set the debug material input
            tree = modifier.node_group
            for item in tree.interface.items_tree:
                if item.item_type == 'SOCKET' and item.name == f"Debug_{section_name}_Material":
                    # Set the material input
                    setattr(modifier, f'[{item.identifier}]', mat)

                elif item.item_type == 'SOCKET' and item.name == "Debug_Mode":
                    # Enable debug mode
                    setattr(modifier, f'[{item.identifier}]', True)

    # Also set as object material
    if obj.data and hasattr(obj.data, 'materials'):
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)


def render_debug_view(config: DebugRenderConfig) -> DebugRenderResult:
    """
    Render a debug view of the current scene.

    Sets up debug materials, configures render settings, and renders.

    Args:
        config: Debug render configuration

    Returns:
        DebugRenderResult with render status and output path
    """
    import time
    start_time = time.time()

    try:
        # Setup scene
        materials = setup_debug_scene(config)

        # Create debug camera
        cam_obj = create_debug_camera(config)
        bpy.context.scene.camera = cam_obj

        # Apply debug materials to all mesh objects
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                # Distribute sections across objects
                section_idx = hash(obj.name) % len(SECTION_NAMES)
                section_name = SECTION_NAMES[section_idx]
                apply_debug_materials_to_object(obj, materials, section_name)

        # Set output path
        output_file = f"{config.output_path}{config.file_prefix}debug"
        bpy.context.scene.render.filepath = output_file

        # Render
        bpy.ops.render.render(write_still=True)

        elapsed = time.time() - start_time

        return DebugRenderResult(
            success=True,
            output_path=output_file,
            render_time_seconds=elapsed
        )

    except Exception as e:
        elapsed = time.time() - start_time
        return DebugRenderResult(
            success=False,
            error=str(e),
            render_time_seconds=elapsed
        )


def render_all_debug_presets(
    base_config: DebugRenderConfig = None
) -> List[DebugRenderResult]:
    """
    Render debug views using all available presets.

    Creates comparison renders with each color preset.

    Args:
        base_config: Base configuration (output_path will be modified per preset)

    Returns:
        List of render results for each preset
    """
    if base_config is None:
        base_config = DebugRenderConfig()

    results = []

    for preset_name in DEBUG_PRESETS.keys():
        # Create config for this preset
        config = DebugRenderConfig(
            output_path=f"{base_config.output_path}{preset_name}/",
            file_prefix=f"{preset_name}_",
            preset=preset_name,
            resolution=base_config.resolution,
            metallic=base_config.metallic,
            roughness=base_config.roughness,
            samples=base_config.samples,
            use_denoising=base_config.use_denoising,
            transparent_background=base_config.transparent_background,
        )

        result = render_debug_view(config)
        results.append(result)

    return results


def enable_debug_mode_on_object(obj: bpy.types.Object, enable: bool = True) -> bool:
    """
    Enable or disable debug mode on an object with geometry nodes.

    Args:
        obj: Blender object with geometry nodes modifier
        enable: True to enable debug mode, False to disable

    Returns:
        True if successful, False if no geometry nodes found
    """
    for modifier in obj.modifiers:
        if modifier.type == 'NODES' and modifier.node_group:
            tree = modifier.node_group
            for item in tree.interface.items_tree:
                if item.item_type == 'SOCKET' and item.name == "Debug_Mode":
                    setattr(modifier, f'[{item.identifier}]', enable)
                    return True
    return False


def create_debug_composite(
    input_path: str,
    output_path: str,
    labels: List[str] = None
) -> bool:
    """
    Create a composite image showing multiple debug presets side by side.

    This uses Blender's compositor to create a comparison image.

    Args:
        input_path: Path pattern for input images (with {} for preset name)
        output_path: Path for output composite image
        labels: Optional labels for each preset

    Returns:
        True if successful
    """
    # This would require Blender's compositor API
    # For now, return a placeholder
    print(f"Debug composite creation not yet implemented")
    print(f"Input pattern: {input_path}")
    print(f"Output: {output_path}")
    return False


# Convenience function for command-line use
def main():
    """Main entry point for command-line debug rendering."""
    import argparse

    parser = argparse.ArgumentParser(description="Debug render for control surfaces")
    parser.add_argument("--output", "-o", default="//renders/debug/", help="Output path")
    parser.add_argument("--preset", "-p", default="rainbow",
                       choices=list(DEBUG_PRESETS.keys()),
                       help="Color preset")
    parser.add_argument("--all-presets", action="store_true", help="Render all presets")
    parser.add_argument("--resolution", "-r", default="1920x1080", help="Resolution (WxH)")
    parser.add_argument("--samples", "-s", type=int, default=16, help="Render samples")

    args = parser.parse_args()

    # Parse resolution
    res = tuple(map(int, args.resolution.split("x")))

    config = DebugRenderConfig(
        output_path=args.output,
        preset=args.preset,
        resolution=res,
        samples=args.samples,
    )

    if args.all_presets:
        results = render_all_debug_presets(config)
        for result in results:
            status = "OK" if result.success else f"FAILED: {result.error}"
            print(f"{result.output_path}: {status}")
    else:
        result = render_debug_view(config)
        status = "OK" if result.success else f"FAILED: {result.error}"
        print(f"Render: {status}")
        if result.success:
            print(f"Output: {result.output_path}")
            print(f"Time: {result.render_time_seconds:.2f}s")


if __name__ == "__main__":
    main()
