"""
Exports - Mesh and preview export utilities.

Output profiles define the contract. Export functions execute it.
"""

from __future__ import annotations
import bpy
from pathlib import Path
from .scene_ops import select_objects


def export_mesh(
    root_objects: list[bpy.types.Object],
    mesh_out_cfg: dict,
    root: Path
) -> Path:
    """
    Export mesh to file.

    Args:
        root_objects: Objects to export
        mesh_out_cfg: Output config with 'file' and optional 'profile'
        root: Project root path

    Returns:
        Path to exported file
    """
    filepath = (root / mesh_out_cfg["file"]).resolve()
    filepath.parent.mkdir(parents=True, exist_ok=True)

    select_objects(root_objects)
    profile = mesh_out_cfg.get("profile", "stl_clean")

    if profile.startswith("stl"):
        bpy.ops.export_mesh.stl(
            filepath=str(filepath),
            use_selection=True,
            apply_modifiers=True,
        )
    elif profile == "gltf_preview":
        bpy.ops.export_scene.gltf(
            filepath=str(filepath.with_suffix("")),
            export_format="GLB",
            use_selection=True,
            apply_modifiers=True,
        )
    else:
        raise RuntimeError(f"Unsupported mesh export profile: {profile}")

    return filepath


def render_preview(
    root_objects: list[bpy.types.Object],
    preview_cfg: dict,
    root: Path
) -> Path:
    """
    Render preview image.

    Args:
        root_objects: Objects to include in render
        preview_cfg: Render config with 'file' and optional 'profile'
        root: Project root path

    Returns:
        Path to rendered image
    """
    filepath = (root / preview_cfg["file"]).resolve()
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Basic render setup
    bpy.context.scene.render.filepath = str(filepath)

    # Apply profile settings if specified
    profile = preview_cfg.get("profile", "studio_white_1k")
    if profile == "studio_white_1k":
        bpy.context.scene.render.resolution_x = 1024
        bpy.context.scene.render.resolution_y = 1024
        bpy.context.scene.render.film_transparent = True
        if hasattr(bpy.context.scene.render, 'engine'):
            bpy.context.scene.render.engine = 'CYCLES'

    bpy.ops.render.render(write_still=True)

    return filepath


def ensure_render_rig() -> None:
    """
    Ensure a basic camera and light exist in the scene.

    Creates default studio setup if missing.
    """
    # Camera
    if not bpy.data.objects.get("Camera"):
        bpy.ops.object.camera_add(
            location=(1.2, -1.4, 1.0),
            rotation=(1.1, 0.0, 0.8)
        )
        cam = bpy.context.active_object
        cam.name = "Camera"
        bpy.context.scene.camera = cam

    # Key light
    if not bpy.data.objects.get("KeyLight"):
        bpy.ops.object.light_add(
            type="AREA",
            location=(1.5, -0.5, 2.0)
        )
        light = bpy.context.active_object
        light.name = "KeyLight"
        light.data.energy = 1200
