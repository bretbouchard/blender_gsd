"""
Cycles X Configuration System

Provides configuration utilities for Cycles render engine in Blender 5.x.

Features:
- Hardware-specific configurations (OptiX, HIP, Metal, CPU)
- Quality presets for different use cases
- Adaptive sampling and path guiding configuration
- Denoiser configuration

Usage:
    from lib.render.cycles_config import apply_cycles_config, get_cycles_preset

    # Apply a preset
    config = get_cycles_preset('production')
    apply_cycles_config(config)

    # Configure for specific hardware
    configure_optix()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import platform


class DeviceType(Enum):
    """Render device types."""
    CPU = "CPU"
    CUDA = "CUDA"
    OPTIX = "OPTIX"
    HIP = "HIP"
    METAL = "METAL"
    ONEAPI = "ONEAPI"


class DenoiserType(Enum):
    """Denoiser types."""
    OPTIX = "OPTIX"
    OPENIMAGEDENOISE = "OPENIMAGEDENOISE"
    NONE = "NONE"


@dataclass
class CyclesConfig:
    """
    Cycles X render configuration.

    Attributes:
        name: Configuration name
        samples: Render samples
        adaptive_sampling: Enable adaptive sampling
        adaptive_threshold: Noise threshold for adaptive sampling
        adaptive_min_samples: Minimum samples before adaptive kicks in
        use_denoising: Enable denoising
        denoiser: Denoiser type
        denoising_start_sample: Sample to start denoising
        use_guiding: Enable path guiding
        guiding_quality: Guiding quality (0-1)
        use_caustics: Enable reflective/refractive caustics
        blur_glossy: Glossy blur amount
        volume_samples: Volume sampling rate
        volume_step_rate: Volume step rate
        max_bounces: Maximum light bounces
        diffuse_bounces: Maximum diffuse bounces
        glossy_bounces: Maximum glossy bounces
        transmission_bounces: Maximum transmission bounces
        volume_bounces: Maximum volume bounces
        transparent_max_bounces: Maximum transparent bounces
        use_transparent_shadows: Enable transparent shadows
        sample_clamp_direct: Clamp direct light samples
        sample_clamp_indirect: Clamp indirect light samples
        light_sampling_threshold: Light sampling threshold
        device_type: Render device type
    """
    name: str
    samples: int = 256
    adaptive_sampling: bool = True
    adaptive_threshold: float = 0.01
    adaptive_min_samples: int = 8
    use_denoising: bool = True
    denoiser: str = "OPENIMAGEDENOISE"
    denoising_start_sample: int = 0
    use_guiding: bool = True
    guiding_quality: float = 0.5
    use_caustics: bool = False
    blur_glossy: float = 0.0
    volume_samples: int = 1
    volume_step_rate: float = 1.0
    max_bounces: int = 12
    diffuse_bounces: int = 4
    glossy_bounces: int = 4
    transmission_bounces: int = 8
    volume_bounces: int = 0
    transparent_max_bounces: int = 8
    use_transparent_shadows: bool = True
    sample_clamp_direct: float = 0.0
    sample_clamp_indirect: float = 0.0
    light_sampling_threshold: float = 0.0
    device_type: str = "AUTO"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "samples": self.samples,
            "adaptive_sampling": self.adaptive_sampling,
            "adaptive_threshold": self.adaptive_threshold,
            "adaptive_min_samples": self.adaptive_min_samples,
            "use_denoising": self.use_denoising,
            "denoiser": self.denoiser,
            "denoising_start_sample": self.denoising_start_sample,
            "use_guiding": self.use_guiding,
            "guiding_quality": self.guiding_quality,
            "use_caustics": self.use_caustics,
            "blur_glossy": self.blur_glossy,
            "volume_samples": self.volume_samples,
            "volume_step_rate": self.volume_step_rate,
            "max_bounces": self.max_bounces,
            "diffuse_bounces": self.diffuse_bounces,
            "glossy_bounces": self.glossy_bounces,
            "transmission_bounces": self.transmission_bounces,
            "volume_bounces": self.volume_bounces,
            "transparent_max_bounces": self.transparent_max_bounces,
            "use_transparent_shadows": self.use_transparent_shadows,
            "sample_clamp_direct": self.sample_clamp_direct,
            "sample_clamp_indirect": self.sample_clamp_indirect,
            "light_sampling_threshold": self.light_sampling_threshold,
            "device_type": self.device_type,
        }


# =============================================================================
# CYCLES PRESETS
# =============================================================================

CYCLES_PRESETS: Dict[str, CyclesConfig] = {
    "preview": CyclesConfig(
        name="preview",
        samples=32,
        adaptive_sampling=True,
        adaptive_threshold=0.05,
        use_denoising=True,
        denoiser="OPENIMAGEDENOISE",
        use_guiding=False,
        max_bounces=8,
    ),
    "draft": CyclesConfig(
        name="draft",
        samples=64,
        adaptive_sampling=True,
        adaptive_threshold=0.02,
        use_denoising=True,
        denoiser="OPENIMAGEDENOISE",
        use_guiding=True,
        guiding_quality=0.3,
        max_bounces=8,
    ),
    "production": CyclesConfig(
        name="production",
        samples=256,
        adaptive_sampling=True,
        adaptive_threshold=0.01,
        adaptive_min_samples=8,
        use_denoising=True,
        denoiser="OPTIX",
        use_guiding=True,
        guiding_quality=0.5,
        max_bounces=12,
        diffuse_bounces=4,
        glossy_bounces=4,
        transmission_bounces=8,
    ),
    "high_quality": CyclesConfig(
        name="high_quality",
        samples=512,
        adaptive_sampling=True,
        adaptive_threshold=0.005,
        adaptive_min_samples=16,
        use_denoising=True,
        denoiser="OPTIX",
        use_guiding=True,
        guiding_quality=0.7,
        use_caustics=True,
        max_bounces=16,
        diffuse_bounces=6,
        glossy_bounces=6,
        transmission_bounces=12,
    ),
    "archive": CyclesConfig(
        name="archive",
        samples=1024,
        adaptive_sampling=True,
        adaptive_threshold=0.001,
        adaptive_min_samples=32,
        use_denoising=True,
        denoiser="OPTIX",
        use_guiding=True,
        guiding_quality=1.0,
        use_caustics=True,
        max_bounces=24,
        diffuse_bounces=8,
        glossy_bounces=8,
        transmission_bounces=16,
        volume_samples=4,
    ),
    "product": CyclesConfig(
        name="product",
        samples=512,
        adaptive_sampling=True,
        adaptive_threshold=0.005,
        use_denoising=True,
        denoiser="OPTIX",
        use_guiding=True,
        guiding_quality=0.7,
        use_caustics=True,
        max_bounces=16,
        diffuse_bounces=6,
        glossy_bounces=8,
        transmission_bounces=12,
    ),
    "animation": CyclesConfig(
        name="animation",
        samples=128,
        adaptive_sampling=True,
        adaptive_threshold=0.02,
        use_denoising=True,
        denoiser="OPENIMAGEDENOISE",
        use_guiding=True,
        guiding_quality=0.4,
        max_bounces=8,
    ),
    "interior": CyclesConfig(
        name="interior",
        samples=512,
        adaptive_sampling=True,
        adaptive_threshold=0.01,
        use_denoising=True,
        denoiser="OPTIX",
        use_guiding=True,
        guiding_quality=0.8,
        max_bounces=24,
        diffuse_bounces=8,
        glossy_bounces=4,
        transmission_bounces=8,
        sample_clamp_indirect=10.0,
    ),
}


# =============================================================================
# CONFIGURATION FUNCTIONS
# =============================================================================

def get_cycles_preset(name: str) -> CyclesConfig:
    """
    Get a Cycles preset by name.

    Args:
        name: Preset name

    Returns:
        CyclesConfig instance

    Raises:
        KeyError: If preset not found
    """
    if name not in CYCLES_PRESETS:
        available = list(CYCLES_PRESETS.keys())
        raise KeyError(f"Cycles preset '{name}' not found. Available: {available}")
    return CYCLES_PRESETS[name]


def apply_cycles_config(config: CyclesConfig) -> bool:
    """
    Apply Cycles configuration to current scene.

    Args:
        config: CyclesConfig instance

    Returns:
        True on success

    Raises:
        RuntimeError: If Blender not available or engine not Cycles
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    scene = bpy.context.scene

    if scene.render.engine != "CYCLES":
        scene.render.engine = "CYCLES"

    cycles = scene.cycles

    # Samples
    cycles.samples = config.samples

    # Adaptive sampling
    cycles.use_adaptive_sampling = config.adaptive_sampling
    if config.adaptive_sampling:
        cycles.adaptive_threshold = config.adaptive_threshold
        cycles.adaptive_min_samples = config.adaptive_min_samples

    # Denoising
    cycles.use_denoising = config.use_denoising
    if config.use_denoising:
        cycles.denoiser = config.denoiser
        cycles.denoising_start_sample = config.denoising_start_sample

    # Path guiding
    cycles.use_guiding = config.use_guiding
    if config.use_guiding:
        cycles.guiding_quality = config.guiding_quality

    # Caustics
    cycles.use_caustics = config.use_caustics
    cycles.blur_glossy = config.blur_glossy

    # Volume
    cycles.volume_samples = config.volume_samples
    cycles.volume_step_rate = config.volume_step_rate

    # Bounces
    cycles.max_bounces = config.max_bounces
    cycles.diffuse_bounces = config.diffuse_bounces
    cycles.glossy_bounces = config.glossy_bounces
    cycles.transmission_bounces = config.transmission_bounces
    cycles.volume_bounces = config.volume_bounces
    cycles.transparent_max_bounces = config.transparent_max_bounces

    # Shadows
    cycles.use_transparent_shadows = config.use_transparent_shadows

    # Sampling clamping
    cycles.sample_clamp_direct = config.sample_clamp_direct
    cycles.sample_clamp_indirect = config.sample_clamp_indirect
    cycles.light_sampling_threshold = config.light_sampling_threshold

    return True


def configure_optix() -> bool:
    """
    Configure Cycles for OptiX (NVIDIA RTX).

    OptiX provides:
    - Hardware-accelerated ray tracing
    - OptiX denoiser (best quality)
    - RTX direct illumination

    Returns:
        True on success
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    # Get Cycles preferences
    cycles_prefs = bpy.context.preferences.addons.get("cycles")
    if not cycles_prefs:
        raise RuntimeError("Cycles addon not found.")

    prefs = cycles_prefs.preferences
    prefs.compute_device_type = "OPTIX"

    # Enable all OptiX devices
    for device in prefs.get_devices_for_type("OPTIX"):
        device.use = True

    scene = bpy.context.scene
    scene.cycles.device = "GPU"
    scene.cycles.denoiser = "OPTIX"

    return True


def configure_hip() -> bool:
    """
    Configure Cycles for HIP (AMD).

    HIP provides:
    - AMD GPU acceleration
    - ROCm-based rendering

    Returns:
        True on success
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    cycles_prefs = bpy.context.preferences.addons.get("cycles")
    if not cycles_prefs:
        raise RuntimeError("Cycles addon not found.")

    prefs = cycles_prefs.preferences
    prefs.compute_device_type = "HIP"

    # Enable all HIP devices
    for device in prefs.get_devices_for_type("HIP"):
        device.use = True

    scene = bpy.context.scene
    scene.cycles.device = "GPU"
    # HIP uses OIDN denoiser
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

    return True


def configure_metal() -> bool:
    """
    Configure Cycles for Metal (Apple Silicon).

    Metal provides:
    - Apple Silicon GPU acceleration
    - M-series chip optimization
    - Unified memory

    Returns:
        True on success
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    cycles_prefs = bpy.context.preferences.addons.get("cycles")
    if not cycles_prefs:
        raise RuntimeError("Cycles addon not found.")

    prefs = cycles_prefs.preferences
    prefs.compute_device_type = "METAL"

    # Enable all Metal devices
    for device in prefs.get_devices_for_type("METAL"):
        device.use = True

    scene = bpy.context.scene
    scene.cycles.device = "GPU"
    # Metal uses OIDN denoiser (Metal-accelerated)
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

    return True


def configure_cpu(threads: int = 0) -> bool:
    """
    Configure Cycles for CPU rendering.

    Args:
        threads: Number of threads (0 = auto)

    Returns:
        True on success
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    scene = bpy.context.scene
    scene.cycles.device = "CPU"

    if threads > 0:
        scene.render.threads = threads
    else:
        scene.render.threads_mode = "AUTO"

    # CPU uses OIDN denoiser
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

    return True


def detect_optimal_device() -> str:
    """
    Detect optimal render device for current hardware.

    Returns:
        Device type string: 'OPTIX', 'HIP', 'METAL', or 'CPU'
    """
    try:
        import bpy
    except ImportError:
        return "CPU"

    cycles_prefs = bpy.context.preferences.addons.get("cycles")
    if not cycles_prefs:
        return "CPU"

    prefs = cycles_prefs.preferences

    # Check available device types in order of preference
    for device_type in ["OPTIX", "HIP", "METAL", "CUDA"]:
        devices = prefs.get_devices_for_type(device_type)
        if devices:
            return device_type

    return "CPU"


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "CyclesConfig",
    "DeviceType",
    "DenoiserType",
    "get_cycles_preset",
    "apply_cycles_config",
    "configure_optix",
    "configure_hip",
    "configure_metal",
    "configure_cpu",
    "detect_optimal_device",
    "CYCLES_PRESETS",
]
