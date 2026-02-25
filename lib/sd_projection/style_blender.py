"""
Style Blender - Multi-style blending and drift animation for SD projection.

Handles:
- Blending multiple style models/LoRAs
- Crossfading between styles over time
- Drift/slipping animation where textures move independently of geometry
- Noise-based texture variation
- Wave-based undulation effects

The "drifting" effect creates that trippy look where:
- The 3D geometry stays fixed
- The projected texture slowly drifts, slips, and slides
- Different parts can drift at different rates
- Creates that "on drugs" visual effect

Usage:
    from lib.sd_projection.style_blender import StyleBlender, DriftConfig

    # Configure drift
    drift = DriftConfig(
        speed=0.1,
        direction=(1.0, 0.5),
        noise_scale=0.3,
        wave_enabled=True,
    )

    # Create blender
    blender = StyleBlender(drift_config=drift)

    # Apply to objects
    blender.apply_drift_material(buildings, texture_path, camera)

    # Animate frame
    blender.update_drift(frame=100)
"""

from __future__ import annotations

import bpy
import mathutils
from mathutils import Vector
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import math
import time
import random

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# =============================================================================
# ENUMS
# =============================================================================

class BlendMode(Enum):
    """How to blend multiple styles."""
    LINEAR = "linear"           # Simple linear blend
    SMOOTH = "smooth"           # Smooth hermite interpolation
    EASE_IN = "ease_in"         # Ease in (slow start, fast end)
    EASE_OUT = "ease_out"       # Ease out (fast start, slow end)
    EASE_IN_OUT = "ease_in_out" # Ease both directions
    BOUNCE = "bounce"           # Bounce between styles
    RANDOM = "random"           # Random style selection


class DriftPattern(Enum):
    """Pattern of texture drift."""
    LINEAR = "linear"           # Constant direction drift
    RADIAL = "radial"           # Drift outward from center
    SPIRAL = "spiral"           # Spiral drift pattern
    CHAOS = "chaos"             # Chaotic/noise-based drift
    WAVE = "wave"               # Wave-like undulation
    PULSE = "pulse"             # Pulsing expansion/contraction


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class StyleLayer:
    """A single style layer in the blend stack."""
    name: str
    weight: float = 1.0
    lora_path: str = ""
    checkpoint: str = ""
    prompt_suffix: str = ""
    # Animation
    animate_weight: bool = False
    weight_keyframes: Dict[int, float] = field(default_factory=dict)  # frame -> weight


@dataclass
class DriftConfig:
    """Configuration for texture drift/slipping animation."""
    # Basic drift
    enabled: bool = True
    speed: float = 0.1              # Drift speed (UV units per frame)
    direction: Tuple[float, float] = (1.0, 0.0)  # UV drift direction (normalized)

    # Pattern
    pattern: DriftPattern = DriftPattern.LINEAR

    # Noise variation
    noise_enabled: bool = True
    noise_scale: float = 5.0        # Noise frequency
    noise_strength: float = 0.2     # How much noise affects drift
    noise_evolution: float = 0.01   # How fast noise changes over time

    # Wave undulation
    wave_enabled: bool = True
    wave_amplitude: float = 0.05    # Wave displacement amount
    wave_frequency: float = 2.0     # Wave cycles per UV unit
    wave_speed: float = 0.5         # Wave animation speed

    # Radial/pulse
    radial_center: Tuple[float, float] = (0.5, 0.5)  # Center for radial patterns
    pulse_frequency: float = 1.0    # Pulse cycles per second

    # Spiral
    spiral_tightness: float = 1.0   # How tight the spiral is
    spiral_expansion: float = 0.1   # How fast spiral expands

    # Per-object variation
    object_variation: float = 0.3   # Random variation between objects

    # Advanced
    turbulence_octaves: int = 4     # Noise octaves for turbulence
    turbulence_roughness: float = 0.5
    z_depth_influence: float = 0.5  # How much depth affects drift speed


@dataclass
class StyleBlendConfig:
    """Configuration for multi-style blending."""
    styles: List[StyleLayer] = field(default_factory=list)
    blend_mode: BlendMode = BlendMode.SMOOTH
    blend_value: float = 0.5        # 0-1 blend position between styles

    # Animation
    animate_blend: bool = False
    blend_speed: float = 0.01       # Blend animation speed
    blend_range: Tuple[float, float] = (0.0, 1.0)  # Min/max blend values

    # Crossfade timing (for animated blend)
    crossfade_duration: float = 30.0  # Frames for crossfade


# =============================================================================
# STYLE BLENDER
# =============================================================================

class StyleBlender:
    """
    Handles style blending and drift animation.

    Creates that "trippy" effect where textures drift and slip
    independently of the underlying geometry.
    """

    def __init__(
        self,
        drift_config: Optional[DriftConfig] = None,
        blend_config: Optional[StyleBlendConfig] = None
    ):
        self.drift_config = drift_config or DriftConfig()
        self.blend_config = blend_config or StyleBlendConfig()

        self._materials: Dict[str, bpy.types.Material] = {}
        self._drivers: List[Any] = []

    def apply_drift_material(
        self,
        objects: List[bpy.types.Object],
        texture_path: Path,
        camera: Optional[bpy.types.Object] = None
    ) -> List[bpy.types.Material]:
        """
        Apply drift-enabled material to objects.

        Creates materials with:
        - Camera projection mapping
        - Animated UV drift
        - Noise-based variation
        - Wave undulation

        Args:
            objects: Objects to apply material to
            texture_path: Path to texture image
            camera: Camera for projection (optional)

        Returns:
            List of created materials
        """
        materials = []

        for i, obj in enumerate(objects):
            mat = self._create_drift_material(
                obj_name=obj.name,
                texture_path=texture_path,
                variation_seed=i * 0.1 if self.drift_config.object_variation > 0 else 0,
                camera=camera
            )

            # Assign material
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

            self._materials[obj.name] = mat
            materials.append(mat)

        return materials

    def _create_drift_material(
        self,
        obj_name: str,
        texture_path: Path,
        variation_seed: float = 0.0,
        camera: Optional[bpy.types.Object] = None
    ) -> bpy.types.Material:
        """Create a single drift material."""
        mat_name = f"{obj_name}_DriftMat"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        config = self.drift_config

        # === NODE LAYOUT ===
        X = -1200
        STEP = 200

        # Output
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (X + 6 * STEP, 0)

        # Principled BSDF
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (X + 5 * STEP, 0)

        # Texture
        tex_image = nodes.new('ShaderNodeTexImage')
        tex_image.location = (X + 3 * STEP, 0)

        # Load texture
        try:
            image = bpy.data.images.load(str(texture_path), check_existing=True)
            tex_image.image = image
        except RuntimeError:
            image = bpy.data.images.new("drift_placeholder", 1024, 1024)
            tex_image.image = image

        # === DRIFT CALCULATION ===
        # Base UV
        uv_map = nodes.new('ShaderNodeUVMap')
        uv_map.location = (X, 200)

        # Frame time
        frame_value = nodes.new('ShaderNodeValue')
        frame_value.location = (X, -200)
        frame_value.outputs[0].default_value = 0.0
        frame_value.label = "Frame"

        # Add driver for frame
        driver = frame_value.outputs[0].driver_add('default_value')
        driver.driver.expression = "frame"
        self._drivers.append(driver)

        # Speed multiplier
        speed_mult = nodes.new('ShaderNodeMath')
        speed_mult.operation = 'MULTIPLY'
        speed_mult.location = (X + STEP, -200)
        speed_mult.inputs[1].default_value = config.speed

        # Direction vector
        direction = nodes.new('ShaderNodeCombineXYZ')
        direction.location = (X + STEP, -400)
        direction.inputs['X'].default_value = config.direction[0]
        direction.inputs['Y'].default_value = config.direction[1]
        direction.inputs['Z'].default_value = 0.0

        # Frame * Speed
        time_speed = nodes.new('ShaderNodeMath')
        time_speed.operation = 'MULTIPLY'
        time_speed.location = (X + 2 * STEP, -200)

        # Time * Direction
        time_dir = nodes.new('ShaderNodeVectorMath')
        time_dir.operation = 'MULTIPLY'
        time_dir.location = (X + 2 * STEP, -400)

        # Add drift to UV
        add_drift = nodes.new('ShaderNodeVectorMath')
        add_drift.operation = 'ADD'
        add_drift.location = (X + 2 * STEP, 100)

        # === NOISE VARIATION ===
        if config.noise_enabled:
            noise = nodes.new('ShaderNodeTexNoise')
            noise.location = (X + STEP, 400)
            noise.inputs['Scale'].default_value = config.noise_scale
            noise.inputs['Detail'].default_value = config.turbulence_octaves
            noise.inputs['Roughness'].default_value = config.turbulence_roughness

            # Noise as vector displacement
            noise_scale = nodes.new('ShaderNodeMath')
            noise_scale.operation = 'MULTIPLY'
            noise_scale.location = (X + 2 * STEP, 400)
            noise_scale.inputs[1].default_value = config.noise_strength

            # Add noise to drift
            add_noise = nodes.new('ShaderNodeVectorMath')
            add_noise.operation = 'ADD'
            add_noise.location = (X + 3 * STEP, 100)

        # === WAVE UNDULATION ===
        if config.wave_enabled:
            wave = nodes.new('ShaderNodeTexWave')
            wave.location = (X + STEP, 600)
            wave.inputs['Scale'].default_value = config.wave_frequency
            wave.inputs['Distortion'].default_value = config.wave_amplitude

            # Wave offset
            wave_add = nodes.new('ShaderNodeVectorMath')
            wave_add.operation = 'ADD'
            wave_add.location = (X + 3 * STEP, 300)

        # === PATTERN-SPECIFIC NODES ===
        if config.pattern == DriftPattern.SPIRAL:
            # Create spiral offset
            spiral_angle = nodes.new('ShaderNodeMath')
            spiral_angle.operation = 'MULTIPLY'
            spiral_angle.location = (X + STEP, 0)
            spiral_angle.inputs[1].default_value = config.spiral_tightness

        elif config.pattern == DriftPattern.RADIAL:
            # Radial offset from center
            center_vec = nodes.new('ShaderNodeCombineXYZ')
            center_vec.location = (X, -600)
            center_vec.inputs['X'].default_value = config.radial_center[0]
            center_vec.inputs['Y'].default_value = config.radial_center[1]

            subtract_center = nodes.new('ShaderNodeVectorMath')
            subtract_center.operation = 'SUBTRACT'
            subtract_center.location = (X + STEP, -600)

        # === CONNECT NODES ===
        # Frame -> Speed
        links.new(frame_value.outputs[0], speed_mult.inputs[0])
        links.new(speed_mult.outputs[0], time_speed.inputs[0])
        time_speed.inputs[1].default_value = 1.0

        # Time * Direction
        links.new(time_speed.outputs[0], time_dir.inputs[0])
        links.new(direction.outputs[0], time_dir.inputs[1])

        # UV + Drift
        links.new(uv_map.outputs[0], add_drift.inputs[0])
        links.new(time_dir.outputs[0], add_drift.inputs[1])

        current_uv = add_drift.outputs[0]

        # Add noise if enabled
        if config.noise_enabled:
            links.new(noise.outputs[1], noise_scale.inputs[0])  # Fac output
            # Convert to vector offset
            noise_vec = nodes.new('ShaderNodeCombineXYZ')
            noise_vec.location = (X + 2 * STEP, 300)
            links.new(noise_scale.outputs[0], noise_vec.inputs['X'])
            links.new(noise_scale.outputs[0], noise_vec.inputs['Y'])

            add_noise2 = nodes.new('ShaderNodeVectorMath')
            add_noise2.operation = 'ADD'
            add_noise2.location = (X + 3 * STEP, 100)
            links.new(current_uv, add_noise2.inputs[0])
            links.new(noise_vec.outputs[0], add_noise2.inputs[1])
            current_uv = add_noise2.outputs[0]

        # Connect to texture
        links.new(current_uv, tex_image.inputs[0])

        # Texture to principled
        links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
        links.new(tex_image.outputs['Alpha'], principled.inputs['Alpha'])

        # Principled to output
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        return mat

    def update_drift(self, frame: int):
        """
        Update drift animation for a specific frame.

        This is called each frame to update the drift animation.
        In practice, Blender's driver system handles this automatically.

        Args:
            frame: Current frame number
        """
        # Drivers handle animation automatically
        # This method can be used for custom updates if needed
        pass

    def set_drift_speed(self, speed: float):
        """Update drift speed in real-time."""
        self.drift_config.speed = speed

        # Update node values
        for obj_name, mat in self._materials.items():
            for node in mat.node_tree.nodes:
                if node.type == 'MATH' and node.operation == 'MULTIPLY':
                    if node.inputs[1].default_value == self.drift_config.speed:
                        node.inputs[1].default_value = speed
                        break

    def set_drift_direction(self, direction: Tuple[float, float]):
        """Update drift direction in real-time."""
        self.drift_config.direction = direction

        for obj_name, mat in self._materials.items():
            for node in mat.node_tree.nodes:
                if node.type == 'COMBXYZ':
                    node.inputs['X'].default_value = direction[0]
                    node.inputs['Y'].default_value = direction[1]


# =============================================================================
# STYLE ANIMATOR
# =============================================================================

class StyleAnimator:
    """
    Animates style blending over time.

    Creates crossfades between different style models,
    with smooth transitions and keyframe support.
    """

    def __init__(self, config: StyleBlendConfig):
        self.config = config
        self._current_blend = config.blend_value
        self._keyframes: List[Tuple[int, float]] = []  # (frame, blend_value)

    def add_keyframe(self, frame: int, blend_value: float):
        """Add a blend keyframe."""
        self._keyframes.append((frame, blend_value))
        self._keyframes.sort(key=lambda x: x[0])

    def get_blend_at_frame(self, frame: int) -> float:
        """
        Calculate blend value at a given frame.

        Interpolates between keyframes based on blend mode.
        """
        if not self._keyframes:
            return self._current_blend

        # Find surrounding keyframes
        prev_frame, prev_value = 0, self._keyframes[0][1] if self._keyframes else 0.5
        next_frame, next_value = float('inf'), prev_value

        for kf_frame, kf_value in self._keyframes:
            if kf_frame <= frame:
                prev_frame, prev_value = kf_frame, kf_value
            if kf_frame > frame and next_frame == float('inf'):
                next_frame, next_value = kf_frame, kf_value
                break

        # If only one keyframe or before first keyframe
        if next_frame == float('inf') or prev_frame == next_frame:
            return prev_value

        # Calculate t (0-1) between keyframes
        t = (frame - prev_frame) / (next_frame - prev_frame)

        # Apply blend mode easing
        t = self._apply_easing(t)

        # Interpolate
        return prev_value + t * (next_value - prev_value)

    def _apply_easing(self, t: float) -> float:
        """Apply easing function based on blend mode."""
        if self.config.blend_mode == BlendMode.LINEAR:
            return t
        elif self.config.blend_mode == BlendMode.SMOOTH:
            # Hermite smoothstep
            return t * t * (3 - 2 * t)
        elif self.config.blend_mode == BlendMode.EASE_IN:
            return t * t
        elif self.config.blend_mode == BlendMode.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif self.config.blend_mode == BlendMode.EASE_IN_OUT:
            if t < 0.5:
                return 2 * t * t
            return 1 - pow(-2 * t + 2, 2) / 2
        elif self.config.blend_mode == BlendMode.BOUNCE:
            # Bounce effect
            if t < 0.5:
                return 4 * t * t * t
            return 1 - pow(-2 * t + 2, 3) / 2
        else:
            return t

    def create_blend_animation(
        self,
        start_frame: int,
        end_frame: int,
        start_blend: float = 0.0,
        end_blend: float = 1.0
    ):
        """
        Create a blend animation between two styles.

        Args:
            start_frame: Animation start frame
            end_frame: Animation end frame
            start_blend: Starting blend value (0-1)
            end_blend: Ending blend value (0-1)
        """
        self.add_keyframe(start_frame, start_blend)
        self.add_keyframe(end_frame, end_blend)


# =============================================================================
# DRIFT PATTERNS
# =============================================================================

class DriftPatternGenerator:
    """Generates custom drift patterns."""

    @staticmethod
    def linear(uv: Tuple[float, float], time: float, config: DriftConfig) -> Tuple[float, float]:
        """Linear drift in a constant direction."""
        dx = config.direction[0] * config.speed * time
        dy = config.direction[1] * config.speed * time
        return (uv[0] + dx, uv[1] + dy)

    @staticmethod
    def radial(uv: Tuple[float, float], time: float, config: DriftConfig) -> Tuple[float, float]:
        """Radial drift outward from center."""
        cx, cy = config.radial_center
        dx = uv[0] - cx
        dy = uv[1] - cy
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            dx /= dist
            dy /= dist

        offset = config.speed * time
        return (uv[0] + dx * offset, uv[1] + dy * offset)

    @staticmethod
    def spiral(uv: Tuple[float, float], time: float, config: DriftConfig) -> Tuple[float, float]:
        """Spiral drift pattern."""
        cx, cy = config.radial_center
        dx = uv[0] - cx
        dy = uv[1] - cy

        angle = math.atan2(dy, dx)
        dist = math.sqrt(dx * dx + dy * dy)

        # Spiral: rotate and expand
        new_angle = angle + config.spiral_tightness * time * 0.01
        new_dist = dist + config.spiral_expansion * time * 0.01

        return (
            cx + new_dist * math.cos(new_angle),
            cy + new_dist * math.sin(new_angle)
        )

    @staticmethod
    def chaos(uv: Tuple[float, float], time: float, config: DriftConfig) -> Tuple[float, float]:
        """Chaotic/noise-based drift."""
        if NUMPY_AVAILABLE:
            # Use numpy for noise
            noise_x = np.sin(uv[0] * config.noise_scale + time) * config.noise_strength
            noise_y = np.sin(uv[1] * config.noise_scale + time * 1.3) * config.noise_strength
            return (uv[0] + noise_x, uv[1] + noise_y)
        else:
            # Fallback
            noise_x = math.sin(uv[0] * config.noise_scale + time) * config.noise_strength
            noise_y = math.sin(uv[1] * config.noise_scale + time * 1.3) * config.noise_strength
            return (uv[0] + noise_x, uv[1] + noise_y)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_drift_material(
    objects: List[bpy.types.Object],
    texture_path: Path,
    drift_speed: float = 0.1,
    drift_direction: Tuple[float, float] = (1.0, 0.0),
    noise_enabled: bool = True,
    wave_enabled: bool = True
) -> List[bpy.types.Material]:
    """
    Quick function to apply drift material to objects.

    Args:
        objects: Objects to apply to
        texture_path: Path to texture
        drift_speed: UV drift speed
        drift_direction: UV drift direction
        noise_enabled: Enable noise variation
        wave_enabled: Enable wave undulation

    Returns:
        List of created materials
    """
    config = DriftConfig(
        speed=drift_speed,
        direction=drift_direction,
        noise_enabled=noise_enabled,
        wave_enabled=wave_enabled,
    )

    blender = StyleBlender(drift_config=config)
    return blender.apply_drift_material(objects, texture_path)


def create_style_crossfade(
    styles: List[str],
    duration_frames: int = 60
) -> StyleAnimator:
    """
    Create a style crossfade animation.

    Args:
        styles: List of style names
        duration_frames: Duration of full crossfade cycle

    Returns:
        StyleAnimator configured for crossfade
    """
    config = StyleBlendConfig(
        styles=[StyleLayer(name=s) for s in styles],
        animate_blend=True,
        blend_speed=1.0 / duration_frames,
    )

    animator = StyleAnimator(config)

    # Create crossfade keyframes
    for i in range(len(styles)):
        frame = i * duration_frames
        blend = i / (len(styles) - 1) if len(styles) > 1 else 0.5
        animator.add_keyframe(frame, blend)

    return animator


__all__ = [
    "StyleBlender",
    "StyleAnimator",
    "DriftConfig",
    "StyleBlendConfig",
    "StyleLayer",
    "BlendMode",
    "DriftPattern",
    "DriftPatternGenerator",
    "create_drift_material",
    "create_style_crossfade",
]
