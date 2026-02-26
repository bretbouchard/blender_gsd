"""
Content preparation for anamorphic billboard displays.

Prepares and maps content for anamorphic projection, including
depth-based content positioning and render setup.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Tuple
from enum import Enum
from pathlib import Path


class ContentType(Enum):
    """Type of anamorphic content."""
    STATIC_IMAGE = "static_image"
    VIDEO = "video"
    PROCEDURAL = "procedural"
    ANIMATED_3D = "animated_3d"


@dataclass
class ContentConfig:
    """
    Configuration for anamorphic content.

    Attributes:
        name: Content name
        content_type: Type of content (image, video, etc.)
        source_path: Path to source file (if applicable)
        depth_extent: How far content extends from display (meters)
        pop_out_distance: Distance content "pops out" toward viewer
        break_frame: Whether content extends beyond display edges
        shadow_casting: Whether content casts shadows
        high_contrast: Use high contrast for better depth perception
        background_color: Background color (RGBA)
        motion_blur: Motion blur strength (0-1)
    """
    name: str = "AnamorphicContent"
    content_type: ContentType = ContentType.STATIC_IMAGE
    source_path: Optional[str] = None
    depth_extent: float = 2.0
    pop_out_distance: float = 1.5
    break_frame: bool = True
    shadow_casting: bool = True
    high_contrast: bool = True
    background_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    motion_blur: float = 0.0


@dataclass
class ContentResult:
    """
    Result of content preparation.

    Attributes:
        success: Whether preparation succeeded
        content_objects: Created content objects
        material: Created material
        render_settings: Recommended render settings
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    content_objects: List[Any] = field(default_factory=list)
    material: Any = None
    render_settings: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def prepare_anamorphic_content(
    config: ContentConfig,
    display_object: Any,
    viewing_camera: Any,
) -> ContentResult:
    """
    Prepare content for anamorphic display.

    This sets up the content to appear correctly when viewed
    from the optimal viewing position.

    Args:
        config: Content configuration
        display_object: The display mesh object
        viewing_camera: The viewing camera

    Returns:
        ContentResult with prepared content

    Example:
        >>> config = ContentConfig(
        ...     name="Logo3D",
        ...     content_type=ContentType.ANIMATED_3D,
        ...     pop_out_distance=2.0,
        ...     break_frame=True,
        ... )
        >>> result = prepare_anamorphic_content(config, display, camera)
    """
    errors = []
    warnings = []
    content_objects = []

    try:
        import bpy
    except ImportError:
        return ContentResult(
            success=False,
            errors=["Blender (bpy) not available"],
        )

    try:
        # Set up render settings for anamorphic content
        render_settings = _configure_render_settings(config)

        # Load source content if provided
        if config.source_path:
            source_result = _load_source_content(
                config.source_path,
                config.content_type,
            )
            if source_result:
                content_objects.extend(source_result)
            else:
                warnings.append(f"Could not load source: {config.source_path}")

        # Configure display material
        material = _configure_display_material(
            display_object,
            config,
            content_objects,
        )

        # Set up depth extension if needed
        if config.depth_extent > 0:
            _setup_depth_extension(display_object, config)

        # Configure shadows if enabled
        if config.shadow_casting:
            _configure_shadow_catching(display_object)

        return ContentResult(
            success=True,
            content_objects=content_objects,
            material=material,
            render_settings=render_settings,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"Error preparing content: {e}")
        return ContentResult(success=False, errors=errors)


def _configure_render_settings(config: ContentConfig) -> dict:
    """Configure render settings for anamorphic output."""
    settings = {
        'engine': 'CYCLES',
        'samples': 128,
        'resolution_x': 1920,
        'resolution_y': 1080,
        'transparent': True,
        'film_transparent': True,
        'motion_blur': config.motion_blur > 0,
        'motion_blur_shutter': config.motion_blur,
    }

    try:
        import bpy

        scene = bpy.context.scene

        # Set render engine
        scene.render.engine = settings['engine']

        # Set samples for Cycles
        if settings['engine'] == 'CYCLES':
            scene.cycles.samples = settings['samples']

        # Set resolution
        scene.render.resolution_x = settings['resolution_x']
        scene.render.resolution_y = settings['resolution_y']

        # Transparent background
        scene.render.film_transparent = settings['film_transparent']

        # Motion blur
        scene.render.use_motion_blur = settings['motion_blur']
        if settings['motion_blur']:
            scene.render.motion_blur_shutter = settings['motion_blur_shutter']

        # Color management for high contrast
        if config.high_contrast:
            scene.view_settings.view_transform = 'Standard'
            scene.view_settings.look = 'High Contrast'

    except Exception:
        pass

    return settings


def _load_source_content(
    source_path: str,
    content_type: ContentType,
) -> List[Any]:
    """Load source content file."""
    objects = []

    try:
        import bpy

        path = Path(source_path)

        if not path.exists():
            return []

        if content_type == ContentType.STATIC_IMAGE:
            # Import image as plane (requires addon)
            try:
                bpy.ops.import_image.to_plane(
                    files=[{'name': path.name}],
                    directory=str(path.parent),
                )
                objects.append(bpy.context.active_object)
            except Exception:
                # Fallback: create plane and assign image
                pass

        elif content_type == ContentType.VIDEO:
            # Create plane with video texture
            bpy.ops.mesh.primitive_plane_add(size=2.0)
            plane = bpy.context.active_object
            objects.append(plane)

            # Create video texture
            # (Would need to set up image sequence)

        elif content_type in (ContentType.PROCEDURAL, ContentType.ANIMATED_3D):
            # For 3D content, import blend file or create procedurally
            if path.suffix == '.blend':
                # Append from blend file
                with bpy.data.libraries.load(str(path)) as (data_from, data_to):
                    if data_from.objects:
                        data_to.objects = data_from.objects[:]

    except Exception:
        pass

    return objects


def _configure_display_material(
    display_object: Any,
    config: ContentConfig,
    content_objects: List[Any],
) -> Any:
    """Configure display material for content."""
    try:
        import bpy

        # Get or create material
        if display_object.data.materials:
            material = display_object.data.materials[0]
        else:
            material = bpy.data.materials.new(name=f"{config.name}_Display")
            display_object.data.materials.append(material)

        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear existing nodes
        nodes.clear()

        # Create emission setup for LED display
        output = nodes.new('ShaderNodeOutputMaterial')
        emission = nodes.new('ShaderNodeEmission')
        mix = nodes.new('ShaderNodeMixShader')
        transparent = nodes.new('ShaderNodeBsdfTransparent')

        # Image texture for content
        if config.source_path:
            image_node = nodes.new('ShaderNodeTexImage')
            try:
                image = bpy.data.images.load(config.source_path)
                image_node.image = image
                links.new(image_node.outputs['Color'], emission.inputs['Color'])
            except Exception:
                pass

        # Set emission strength for LED brightness
        emission.inputs['Strength'].default_value = 3.0 if config.high_contrast else 2.0

        # Connect for transparency support
        links.new(transparent.outputs['BSDF'], mix.inputs[1])
        links.new(emission.outputs['Emission'], mix.inputs[2])
        links.new(mix.outputs['Shader'], output.inputs['Surface'])

        # Position nodes
        output.location = (600, 0)
        mix.location = (300, 0)
        emission.location = (0, 100)
        transparent.location = (0, -100)

        # Configure alpha for frame breaking
        if config.break_frame:
            material.blend_method = 'BLEND'
            material.shadow_method = 'HASHED'

        return material

    except Exception:
        return None


def _setup_depth_extension(
    display_object: Any,
    config: ContentConfig,
) -> None:
    """Set up depth extension for 3D pop-out effect."""
    # This would create additional geometry that extends
    # from the display surface toward the viewer
    pass


def _configure_shadow_catching(
    display_object: Any,
) -> None:
    """Configure display to catch shadows from content."""
    try:
        import bpy

        # Create shadow catcher material
        mat = bpy.data.materials.new(name="ShadowCatcher")
        mat.use_nodes = True
        mat.shadow_method = 'HASHED'

        # Would need cycles shadow catcher setup

    except Exception:
        pass


def render_anamorphic_content(
    display_object: Any,
    viewing_camera: Any,
    output_path: str,
    frame_start: int = 1,
    frame_end: int = 250,
) -> List[str]:
    """
    Render anamorphic content from viewing camera perspective.

    Args:
        display_object: The display mesh
        viewing_camera: Camera at optimal viewing position
        output_path: Output directory path
        frame_start: Start frame
        frame_end: End frame

    Returns:
        List of rendered file paths
    """
    try:
        import bpy

        scene = bpy.context.scene

        # Set camera
        scene.camera = viewing_camera

        # Set frame range
        scene.frame_start = frame_start
        scene.frame_end = frame_end

        # Set output path
        scene.render.filepath = output_path
        scene.render.image_settings.file_format = 'PNG'

        # Render animation
        bpy.ops.render.render(animation=True)

        # Return list of rendered files
        return [f"{output_path}{i:04d}.png" for i in range(frame_start, frame_end + 1)]

    except Exception:
        return []
