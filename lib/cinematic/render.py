"""
Render System for Cinematic Rendering

Provides quality tier presets, render pass configuration, EXR output setup,
denoising, and batch rendering capabilities.

Functions:
    apply_quality_profile: Apply render settings from quality_profiles.yaml
    apply_render_settings: Apply complete render settings from CinematicRenderSettings
    configure_render_passes: Enable render passes from pass_presets.yaml
    setup_cryptomatte: Configure cryptomatte passes for compositing
    setup_exr_output: Configure EXR multi-layer output
    detect_optimal_denoiser: Auto-detect best denoiser for hardware
    enable_denoising: Enable and configure denoising
    set_render_engine: Set render engine (Cycles, EEVEE Next, Workbench)
    set_resolution: Set render resolution
    set_frame_range: Set animation frame range
    render_frame: Render single frame
    render_animation: Render animation sequence
    get_render_settings: Get current render settings as dict
    apply_pass_preset: Apply pass preset from pass_presets.yaml
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import platform

# Blender availability check
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


# =============================================================================
# CONSTANTS
# =============================================================================

# Engine identifiers (CRITICAL: Use BLENDER_EEVEE_NEXT, not deprecated BLENDER_EEVEE)
ENGINES = {
    'CYCLES': 'CYCLES',
    'EEVEE_NEXT': 'BLENDER_EEVEE_NEXT',  # NOT 'BLENDER_EEVEE' (deprecated in Blender 4.2+)
    'WORKBENCH': 'BLENDER_WORKBENCH'
}

# Pass mapping: config name -> view_layer attribute
PASS_MAPPING = {
    # Core passes
    'combined': 'use_pass_combined',
    'depth': 'use_pass_z',
    'normal': 'use_pass_normal',
    'vector': 'use_pass_vector',
    # Material passes
    'diffuse_direct': 'use_pass_diffuse_direct',
    'diffuse_indirect': 'use_pass_diffuse_indirect',
    'diffuse_color': 'use_pass_diffuse_color',
    'glossy_direct': 'use_pass_glossy_direct',
    'glossy_indirect': 'use_pass_glossy_indirect',
    'glossy_color': 'use_pass_glossy_color',
    'transmission_direct': 'use_pass_transmission_direct',
    'transmission_indirect': 'use_pass_transmission_indirect',
    'transmission_color': 'use_pass_transmission_color',
    # Effect passes
    'emission': 'use_pass_emit',
    'environment': 'use_pass_environment',
    'shadow': 'use_pass_shadow',
    'ao': 'use_pass_ambient_occlusion',
    # Cryptomatte (CRITICAL: Must enable for object isolation)
    'cryptomatte_object': 'use_pass_cryptomatte_object',
    'cryptomatte_material': 'use_pass_cryptomatte_material',
    'cryptomatte_asset': 'use_pass_cryptomatte_asset',
}

# EXR codec mapping
EXR_CODECS = {
    'DWAA': 'DWAA',  # Lossy but fast, good for color data
    'ZIP': 'ZIP',    # Lossless, good balance for passes
    'PIZ': 'PIZ',    # Best compression, lossless
    'NONE': 'NONE',  # Uncompressed
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _check_blender_available() -> None:
    """Raise RuntimeError if Blender is not available."""
    if not BLENDER_AVAILABLE:
        raise RuntimeError(
            "Blender (bpy) is not available. "
            "This function must be run from within Blender."
        )


def _has_optix() -> bool:
    """Check if OptiX is available on this system."""
    if not BLENDER_AVAILABLE:
        return False
    try:
        cycles_prefs = bpy.context.preferences.addons.get('cycles')
        if cycles_prefs and hasattr(cycles_prefs, 'preferences'):
            return cycles_prefs.preferences.compute_device_type == 'OPTIX'
    except (AttributeError, KeyError):
        pass
    return False


def _is_apple_silicon() -> bool:
    """Check if running on Apple Silicon."""
    return platform.processor() == 'arm'


# =============================================================================
# QUALITY TIER FUNCTIONS
# =============================================================================

def apply_quality_profile(profile_name: str) -> bool:
    """
    Apply render quality tier from quality_profiles.yaml.

    Supports: viewport_capture, eevee_draft, cycles_preview,
              cycles_production, cycles_archive

    Args:
        profile_name: Quality profile name from quality_profiles.yaml

    Returns:
        True on success

    Raises:
        RuntimeError: If Blender is not available
        ValueError: If profile not found
    """
    _check_blender_available()

    from .preset_loader import get_quality_profile

    scene = bpy.context.scene
    profile = get_quality_profile(profile_name)

    # Set engine
    engine_key = profile.get('engine', 'CYCLES')
    engine_id = ENGINES.get(engine_key)
    if engine_id:
        scene.render.engine = engine_id

    # Set resolution
    resolution = profile.get('resolution', {})
    base = resolution.get('base', 2048)
    scale = resolution.get('scale', 100)
    scene.render.resolution_x = base
    scene.render.resolution_y = base
    scene.render.resolution_percentage = scale

    # Set samples (Cycles only)
    if engine_key == 'CYCLES':
        scene.cycles.samples = profile.get('samples', 64)

        # Adaptive sampling
        adaptive = profile.get('adaptive_sampling', {})
        if adaptive.get('enabled', False):
            scene.cycles.use_adaptive_sampling = True
            scene.cycles.adaptive_threshold = adaptive.get('threshold', 0.01)
            scene.cycles.adaptive_min_samples = adaptive.get('min_samples', 8)

    # Denoiser settings
    denoiser = profile.get('denoiser_settings', {})
    if denoiser.get('enabled', False):
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = denoiser.get('denoiser', 'OPENIMAGEDENOISE')

    return True


def apply_render_settings(settings: "CinematicRenderSettings") -> bool:
    """
    Apply complete render settings from CinematicRenderSettings dataclass.

    Args:
        settings: CinematicRenderSettings dataclass instance

    Returns:
        True on success
    """
    _check_blender_available()

    scene = bpy.context.scene

    # Set engine
    scene.render.engine = settings.engine

    # Set resolution
    scene.render.resolution_x = settings.resolution_x
    scene.render.resolution_y = settings.resolution_y
    scene.render.resolution_percentage = settings.resolution_percentage

    # Set frame range
    scene.frame_start = settings.frame_start
    scene.frame_end = settings.frame_end
    scene.render.fps = int(settings.fps)

    # Set samples for EEVEE/Cycles
    if hasattr(scene, 'cycles') and settings.engine == 'CYCLES':
        scene.cycles.samples = settings.samples
        scene.cycles.use_denoising = settings.use_denoising
        if settings.use_denoising:
            scene.cycles.denoiser = settings.denoiser_type

    # Motion blur
    scene.render.use_motion_blur = settings.use_motion_blur
    if settings.use_motion_blur:
        scene.render.motion_blur_shutter = settings.motion_blur_shutter

    # Passes
    view_layer = bpy.context.view_layer
    view_layer.use_pass_combined = settings.use_pass_combined
    view_layer.use_pass_z = settings.use_pass_z
    view_layer.use_pass_normal = settings.use_pass_normal
    view_layer.use_pass_cryptomatte_object = settings.use_pass_cryptomatte

    # Output format
    scene.render.image_settings.file_format = settings.output_format
    if 'EXR' in settings.output_format:
        scene.render.image_settings.exr_codec = settings.exr_codec

    return True


# =============================================================================
# RENDER PASS FUNCTIONS
# =============================================================================

def configure_render_passes(pass_group: str) -> bool:
    """
    Configure render passes from pass_presets.yaml group.

    Supports: beauty, data_passes, material_passes, cryptomatte,
              full_production, product_minimal

    Args:
        pass_group: Pass group name from pass_presets.yaml

    Returns:
        True on success
    """
    _check_blender_available()

    from .preset_loader import get_pass_preset

    view_layer = bpy.context.view_layer
    preset = get_pass_preset(pass_group)
    passes = preset.get('passes', [])

    # Disable all passes first (clean slate)
    for attr in dir(view_layer):
        if attr.startswith('use_pass_'):
            try:
                setattr(view_layer, attr, False)
            except AttributeError:
                pass

    # Enable requested passes
    for pass_name in passes:
        attr = PASS_MAPPING.get(pass_name)
        if attr and hasattr(view_layer, attr):
            setattr(view_layer, attr, True)

    # CRITICAL: Cryptomatte requires additional setup
    if any(p in passes for p in ['cryptomatte_object', 'cryptomatte_material', 'cryptomatte_asset']):
        view_layer.cryptomatte_levels = 6  # Standard levels
        view_layer.use_pass_cryptomatte_accurate = True

    return True


def setup_cryptomatte(
    object_pass: bool = True,
    material_pass: bool = False,
    asset_pass: bool = False,
    levels: int = 6
) -> bool:
    """
    Configure cryptomatte passes for compositing.

    Args:
        object_pass: Enable object cryptomatte
        material_pass: Enable material cryptomatte
        asset_pass: Enable asset cryptomatte
        levels: Cryptomatte levels (default 6)

    Returns:
        True on success
    """
    _check_blender_available()

    view_layer = bpy.context.view_layer

    view_layer.use_pass_cryptomatte_object = object_pass
    view_layer.use_pass_cryptomatte_material = material_pass
    view_layer.use_pass_cryptomatte_asset = asset_pass

    if any([object_pass, material_pass, asset_pass]):
        view_layer.cryptomatte_levels = levels
        view_layer.use_pass_cryptomatte_accurate = True

    return True


def apply_pass_preset(preset_name: str) -> bool:
    """
    Apply pass preset from pass_presets.yaml.

    Alias for configure_render_passes().

    Args:
        preset_name: Pass preset name

    Returns:
        True on success
    """
    return configure_render_passes(preset_name)


# =============================================================================
# EXR OUTPUT FUNCTIONS
# =============================================================================

def setup_exr_output(
    preset_name: str = 'multi_layer_compositing'
) -> bool:
    """
    Configure EXR output settings from pass_presets.yaml.

    Presets: beauty_only, multi_layer_compositing, archive_storage

    Args:
        preset_name: EXR preset name from pass_presets.yaml

    Returns:
        True on success
    """
    _check_blender_available()

    from .preset_loader import get_exr_settings

    scene = bpy.context.scene
    exr_settings = get_exr_settings(preset_name)

    # Set output format (CRITICAL: Use OPEN_EXR_MULTILAYER for multi-pass)
    scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
    scene.render.image_settings.exr_codec = EXR_CODECS.get(
        exr_settings.get('compression', 'ZIP'), 'ZIP'
    )
    scene.render.image_settings.color_depth = str(exr_settings.get('depth', 32))
    scene.render.image_settings.use_preview = True

    # Enable alpha for compositing
    scene.render.film_transparent = True

    return True


# =============================================================================
# DENOISER FUNCTIONS
# =============================================================================

def detect_optimal_denoiser() -> str:
    """
    Auto-detect best denoiser for current hardware.

    Returns:
        Denoiser identifier: 'OPTIX', 'OPENIMAGEDENOISE', or 'NONE'
    """
    if not BLENDER_AVAILABLE:
        return 'NONE'

    # Check OptiX availability (NVIDIA + OptiX)
    if _has_optix():
        return 'OPTIX'

    # Check Metal on Apple Silicon
    if platform.system() == 'Darwin' and _is_apple_silicon():
        return 'OPENIMAGEDENOISE'  # Metal-accelerated

    # Default to OpenImageDenoise (CPU)
    return 'OPENIMAGEDENOISE'


def enable_denoising(
    denoiser: str = 'auto',
    start_sample: int = 0,
    use_passes: bool = True
) -> bool:
    """
    Enable and configure denoising.

    Args:
        denoiser: Denoiser type ('auto', 'OPTIX', 'OPENIMAGEDENOISE', 'NONE')
        start_sample: Sample to start denoising at
        use_passes: Use denoising passes for better quality

    Returns:
        True on success
    """
    _check_blender_available()

    scene = bpy.context.scene

    if denoiser == 'auto':
        denoiser = detect_optimal_denoiser()

    if denoiser == 'NONE':
        scene.cycles.use_denoising = False
        return True

    scene.cycles.use_denoising = True
    scene.cycles.denoiser = denoiser
    scene.cycles.denoising_start_sample = start_sample

    if hasattr(scene.cycles, 'use_denoising_passes'):
        scene.cycles.use_denoising_passes = use_passes

    return True


# =============================================================================
# BASIC RENDER SETTINGS FUNCTIONS
# =============================================================================

def set_render_engine(engine: str) -> bool:
    """
    Set render engine.

    Args:
        engine: Engine identifier ('CYCLES', 'EEVEE_NEXT', 'WORKBENCH')

    Returns:
        True on success
    """
    _check_blender_available()

    engine_id = ENGINES.get(engine)
    if not engine_id:
        raise ValueError(f"Unknown engine: {engine}. Valid: {list(ENGINES.keys())}")

    bpy.context.scene.render.engine = engine_id
    return True


def set_resolution(width: int, height: int, percentage: int = 100) -> bool:
    """
    Set render resolution.

    Args:
        width: Width in pixels
        height: Height in pixels
        percentage: Resolution scale (100 = full)

    Returns:
        True on success
    """
    _check_blender_available()

    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = percentage
    return True


def set_frame_range(start: int, end: int, fps: int = 24) -> bool:
    """
    Set animation frame range.

    Args:
        start: Start frame
        end: End frame
        fps: Frames per second

    Returns:
        True on success
    """
    _check_blender_available()

    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    scene.render.fps = fps
    return True


# =============================================================================
# RENDER EXECUTION FUNCTIONS
# =============================================================================

def render_frame(
    output_path: Optional[str] = None,
    use_viewport: bool = False
) -> str:
    """
    Render single frame.

    Args:
        output_path: Optional output file path
        use_viewport: Use viewport render (faster, lower quality)

    Returns:
        Output path or empty string
    """
    _check_blender_available()

    scene = bpy.context.scene

    if output_path:
        scene.render.filepath = output_path

    if use_viewport:
        bpy.ops.render.opengl(write_still=True)
    else:
        bpy.ops.render.render(write_still=True)

    return scene.render.filepath


def render_animation(
    output_path: Optional[str] = None,
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None
) -> str:
    """
    Render animation sequence.

    Args:
        output_path: Optional output directory path
        frame_start: Optional start frame (uses scene frame_start if None)
        frame_end: Optional end frame (uses scene frame_end if None)

    Returns:
        Output path
    """
    _check_blender_available()

    scene = bpy.context.scene

    if output_path:
        scene.render.filepath = output_path

    # Use provided frame range or scene defaults
    if frame_start is not None:
        original_start = scene.frame_start
        scene.frame_start = frame_start
    if frame_end is not None:
        original_end = scene.frame_end
        scene.frame_end = frame_end

    bpy.ops.render.render(animation=True)

    # Restore frame range if changed
    if frame_start is not None:
        scene.frame_start = original_start
    if frame_end is not None:
        scene.frame_end = original_end

    return scene.render.filepath


def get_render_settings() -> Dict[str, Any]:
    """
    Get current render settings as dictionary.

    Returns:
        Dictionary with current render settings
    """
    if not BLENDER_AVAILABLE:
        return {"error": "Blender not available"}

    scene = bpy.context.scene
    settings = {
        "engine": scene.render.engine,
        "resolution": f"{scene.render.resolution_x}x{scene.render.resolution_y}",
        "resolution_percentage": scene.render.resolution_percentage,
        "frame_range": f"{scene.frame_start}-{scene.frame_end}",
        "fps": scene.render.fps,
        "film_transparent": scene.render.film_transparent,
        "file_format": scene.render.image_settings.file_format,
    }

    if scene.render.engine == 'CYCLES':
        settings["samples"] = scene.cycles.samples
        settings["use_denoising"] = scene.cycles.use_denoising
        if scene.cycles.use_denoising:
            settings["denoiser"] = scene.cycles.denoiser

    return settings


def get_render_metadata() -> Dict[str, Any]:
    """
    Get render metadata for shot tracking.

    Provides comprehensive render state information including
    enabled passes, output settings, and render configuration.

    Returns:
        Dictionary with render metadata for shot tracking
    """
    if not BLENDER_AVAILABLE:
        return {}

    try:
        scene = bpy.context.scene
        view_layer = bpy.context.view_layer

        # Get enabled passes
        enabled_passes = []
        for pass_name, attr in PASS_MAPPING.items():
            if hasattr(view_layer, attr) and getattr(view_layer, attr, False):
                enabled_passes.append(pass_name)

        metadata = {
            'engine': scene.render.engine,
            'resolution': f"{scene.render.resolution_x}x{scene.render.resolution_y}",
            'resolution_percentage': scene.render.resolution_percentage,
            'frame_range': f"{scene.frame_start}-{scene.frame_end}",
            'fps': scene.render.fps,
            'film_transparent': scene.render.film_transparent,
            'output_path': scene.render.filepath,
            'output_format': scene.render.image_settings.file_format,
            'enabled_passes': enabled_passes,
        }

        # Cycles-specific settings
        if scene.render.engine == 'CYCLES':
            metadata['samples'] = scene.cycles.samples
            metadata['use_denoising'] = scene.cycles.use_denoising
            metadata['denoiser'] = scene.cycles.denoiser if scene.cycles.use_denoising else None
            metadata['use_adaptive_sampling'] = scene.cycles.use_adaptive_sampling
            if scene.cycles.use_adaptive_sampling:
                metadata['adaptive_threshold'] = scene.cycles.adaptive_threshold

        return metadata

    except Exception:
        return {}


# =============================================================================
# COMPOSITE CONFIGURATION FUNCTIONS
# =============================================================================

def apply_render_config(
    quality_tier: str = "cycles_preview",
    pass_group: str = "product_minimal",
    exr_preset: str = "multi_layer_compositing"
) -> bool:
    """
    Apply complete render configuration from presets.

    Combines quality tier, passes, and EXR settings in one call.

    Args:
        quality_tier: Quality profile name from quality_profiles.yaml
        pass_group: Pass preset name from pass_presets.yaml
        exr_preset: EXR settings preset name from pass_presets.yaml

    Returns:
        True on success, False on failure
    """
    _check_blender_available()

    try:
        # Apply quality tier
        if not apply_quality_profile(quality_tier):
            return False

        # Configure passes
        if not configure_render_passes(pass_group):
            return False

        # Configure EXR output
        if not setup_exr_output(exr_preset):
            return False

        return True

    except Exception as e:
        print(f"Error applying render config: {e}")
        return False


# =============================================================================
# BATCH RENDERING FUNCTIONS
# =============================================================================

def batch_render(
    shots: List[Dict[str, Any]],
    parallel_jobs: int = 1,
    resume_on_failure: bool = True
) -> Dict[str, bool]:
    """
    Batch render multiple shots with dependency management.

    Args:
        shots: List of shot configs with keys:
               - 'shot': Shot name (required)
               - 'depends_on': List of dependency shot names (optional)
               - 'quality_tier': Quality profile name (optional)
               - 'pass_group': Pass preset name (optional)
               - 'exr_preset': EXR preset name (optional)
               - 'output_path': Output path for this shot (optional)
               - 'frame_start': Start frame override (optional)
               - 'frame_end': End frame override (optional)
        parallel_jobs: Number of parallel renders (currently single-threaded, parameter for future)
        resume_on_failure: Skip completed renders if resuming

    Returns:
        Dict mapping shot names to success status (True/False)
    """
    _check_blender_available()

    results: Dict[str, bool] = {}
    completed: set = set()

    for shot_config in shots:
        shot_name = shot_config.get('shot', 'unnamed')
        dependencies = shot_config.get('depends_on', [])

        # Check dependencies
        deps_satisfied = all(d in completed for d in dependencies)
        if not deps_satisfied:
            results[shot_name] = False
            continue

        # Check if already rendered (resume)
        output_path = shot_config.get('output_path', '')
        if resume_on_failure and output_path:
            # Resolve Blender path
            abs_path = bpy.path.abspath(output_path)
            output_file = Path(abs_path)

            # Check for common output patterns
            possible_outputs = [
                output_file,
                output_file.with_suffix('.exr'),
                output_file.with_suffix('.png'),
                # Check for frame sequence
                output_file.parent / f"{output_file.stem}0001.exr",
                output_file.parent / f"{output_file.stem}0001.png",
            ]
            if any(p.exists() for p in possible_outputs):
                completed.add(shot_name)
                results[shot_name] = True
                continue

        try:
            # Apply shot-specific config
            quality_tier = shot_config.get('quality_tier', 'cycles_preview')
            pass_group = shot_config.get('pass_group', 'product_minimal')
            exr_preset = shot_config.get('exr_preset', 'multi_layer_compositing')

            apply_render_config(quality_tier, pass_group, exr_preset)

            # Set output path if provided
            scene = bpy.context.scene
            if output_path:
                scene.render.filepath = output_path

            # Set frame range overrides
            frame_start = shot_config.get('frame_start')
            frame_end = shot_config.get('frame_end')

            if frame_start is not None or frame_end is not None:
                render_animation(
                    output_path=output_path if output_path else None,
                    frame_start=frame_start,
                    frame_end=frame_end
                )
            else:
                # Single frame render
                render_frame(output_path if output_path else None)

            results[shot_name] = True
            completed.add(shot_name)

        except Exception as e:
            print(f"Error rendering shot '{shot_name}': {e}")
            results[shot_name] = False

    return results


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Quality tier functions
    "apply_quality_profile",
    "apply_render_settings",
    # Render pass functions
    "configure_render_passes",
    "setup_cryptomatte",
    "apply_pass_preset",
    # EXR output functions
    "setup_exr_output",
    # Denoiser functions
    "detect_optimal_denoiser",
    "enable_denoising",
    # Basic settings functions
    "set_render_engine",
    "set_resolution",
    "set_frame_range",
    # Render execution functions
    "render_frame",
    "render_animation",
    "get_render_settings",
    # Composite configuration
    "apply_render_config",
    "get_render_metadata",
    # Batch rendering
    "batch_render",
    # Constants
    "ENGINES",
    "PASS_MAPPING",
    "EXR_CODECS",
    "BLENDER_AVAILABLE",
]
