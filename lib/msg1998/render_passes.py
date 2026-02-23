"""
MSG 1998 - Render Pass Configuration

Configure render passes for SD compositing.
"""

from typing import List, Optional

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .types import MSGRenderPasses


def configure_render_passes(
    scene,
    passes: Optional[MSGRenderPasses] = None
) -> None:
    """
    Enable/disable render passes for scene.

    Args:
        scene: Blender scene
        passes: Render pass configuration
    """
    if not BLENDER_AVAILABLE:
        return

    if passes is None:
        passes = MSGRenderPasses()

    # Get render layers
    view_layer = scene.view_layers.active

    # Enable passes
    view_layer.use_pass_combined = passes.beauty
    view_layer.use_pass_z = passes.depth
    view_layer.use_pass_normal = passes.normal
    view_layer.use_pass_object_index = passes.object_id
    view_layer.use_pass_diffuse_color = passes.diffuse
    view_layer.use_pass_shadow = passes.shadow
    view_layer.use_pass_ambient_occlusion = passes.ao

    # Cryptomatte
    if passes.cryptomatte:
        if "crypto_object" not in [p.name for p in view_layer.freestyle_linesets]:
            view_layer.use_pass_cryptomatte_object = "object" in passes.cryptomatte_layers
            view_layer.use_pass_cryptomatte_material = "material" in passes.cryptomatte_layers
            view_layer.use_pass_cryptomatte_asset = "asset" in passes.cryptomatte_layers


def get_pass_output_path(
    base_path: str,
    pass_name: str,
    frame: int = 1
) -> str:
    """
    Generate output path for render pass.

    Args:
        base_path: Base output path
        pass_name: Name of the pass
        frame: Frame number

    Returns:
        Formatted path string
    """
    # Blender uses #### for frame numbers
    return f"{base_path}/{pass_name}_####.exr"


def create_multilayer_exr_setup(
    scene,
    output_path: str
) -> None:
    """
    Configure scene for multilayer EXR output.

    Args:
        scene: Blender scene
        output_path: Output file path
    """
    if not BLENDER_AVAILABLE:
        return

    # Set output format
    scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
    scene.render.image_settings.color_depth = '32'
    scene.render.image_settings.exr_codec = 'ZIP'
    scene.render.filepath = output_path


def get_required_passes() -> MSGRenderPasses:
    """
    Get standard passes required for SD compositing.

    Returns:
        MSGRenderPasses with all required passes enabled
    """
    return MSGRenderPasses(
        beauty=True,
        depth=True,
        normal=True,
        object_id=True,
        diffuse=True,
        shadow=True,
        ao=True,
        cryptomatte=True,
        cryptomatte_layers=["object", "material"]
    )


def validate_pass_setup(scene) -> List[str]:
    """
    Validate scene has required passes enabled.

    Args:
        scene: Blender scene

    Returns:
        List of missing passes
    """
    missing = []

    if not BLENDER_AVAILABLE:
        return ["Blender not available"]

    view_layer = scene.view_layers.active
    required = MSGRenderPasses()

    if not view_layer.use_pass_z:
        missing.append("depth")
    if not view_layer.use_pass_normal:
        missing.append("normal")
    if not view_layer.use_pass_object_index:
        missing.append("object_id")

    return missing
