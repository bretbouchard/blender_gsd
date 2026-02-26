"""
Tentacle Shape Key Generator

Procedural shape key generation for squeeze/expand/curl animations.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import math
import numpy as np

try:
    import bpy
    from bpy.types import Object, Mesh, ShapeKey
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None
    Mesh = None
    ShapeKey = None

from .types import (
    ShapeKeyConfig,
    ShapeKeyPreset,
    ShapeKeyResult,
)


# Preset configurations for shape keys
SHAPE_KEY_PRESETS = {
    ShapeKeyPreset.BASE: {
        "diameter_scale": 1.0,
        "length_scale": 1.0,
        "squeeze_position": None,
        "squeeze_width": 0.2,
        "curl_angle": 0.0,
        "curl_start": 1.0,
        "volume_preservation": 0.0,
    },
    ShapeKeyPreset.COMPRESS_50: {
        "diameter_scale": 0.5,
        "length_scale": 2.0,
        "squeeze_position": None,
        "squeeze_width": 0.3,
        "curl_angle": 0.0,
        "curl_start": 1.0,
        "volume_preservation": 0.3,
    },
    ShapeKeyPreset.COMPRESS_75: {
        "diameter_scale": 0.75,
        "length_scale": 1.3,
        "squeeze_position": None,
        "squeeze_width": 0.2,
        "curl_angle": 0.0,
        "curl_start": 1.0,
        "volume_preservation": 0.2,
    },
    ShapeKeyPreset.EXPAND_125: {
        "diameter_scale": 1.25,
        "length_scale": 0.8,
        "squeeze_position": None,
        "squeeze_width": 0.2,
        "curl_angle": 0.0,
        "curl_start": 1.0,
        "volume_preservation": 0.0,
    },
    ShapeKeyPreset.CURL_TIP: {
        "diameter_scale": 1.0,
        "length_scale": 1.0,
        "squeeze_position": None,
        "squeeze_width": 0.1,
        "curl_angle": 180.0,
        "curl_start": 0.8,
        "volume_preservation": 0.0,
    },
    ShapeKeyPreset.CURL_FULL: {
        "diameter_scale": 1.0,
        "length_scale": 0.9,
        "squeeze_position": None,
        "squeeze_width": 0.1,
        "curl_angle": 540.0,
        "curl_start": 0.3,
        "volume_preservation": 0.0,
    },
    ShapeKeyPreset.SQUEEZE_TIP: {
        "diameter_scale": 0.7,
        "length_scale": 1.1,
        "squeeze_position": 0.9,
        "squeeze_width": 0.2,
        "curl_angle": 0.0,
        "curl_start": 1.0,
        "volume_preservation": 0.15,
    },
    ShapeKeyPreset.SQUEEZE_MID: {
        "diameter_scale": 0.7,
        "length_scale": 1.05,
        "squeeze_position": 0.5,
        "squeeze_width": 0.2,
        "curl_angle": 0.0,
        "curl_start": 1.0,
        "volume_preservation": 0.15,
    },
    ShapeKeyPreset.SQUEEZE_BASE: {
        "diameter_scale": 0.7,
        "length_scale": 1.0,
        "squeeze_position": 0.1,
        "squeeze_width": 0.2,
        "curl_angle": 0.0,
        "curl_start": 1.0,
        "volume_preservation": 0.15,
    },
    ShapeKeyPreset.SQUEEZE_LOCAL: {
        "diameter_scale": 0.6,
        "length_scale": 1.2,
        "squeeze_position": 0.5,
        "squeeze_width": 0.3,
        "curl_angle": 0.0,
        "curl_start": 1.0,
        "volume_preservation": 0.1,
    },
}


def get_preset_config(preset: ShapeKeyPreset) -> ShapeKeyConfig:
    """Get configuration for a preset."""
    preset_data = SHAPE_KEY_PRESETS.get(preset, SHAPE_KEY_PRESETS[ShapeKeyPreset.BASE])

    return ShapeKeyConfig(
        name=preset.value,
        preset=preset,
        diameter_scale=preset_data["diameter_scale"],
        length_scale=preset_data["length_scale"],
        squeeze_position=preset_data["squeeze_position"],
        squeeze_width=preset_data["squeeze_width"],
        curl_angle=preset_data["curl_angle"],
        curl_start=preset_data["curl_start"],
        volume_preservation=preset_data["volume_preservation"],
    )


def _calculate_vertex_displacement(
    base_pos: np.ndarray,
    tip_pos: np.ndarray,
    vertex_pos: np.ndarray,
    config: ShapeKeyConfig,
    taper_radii: np.ndarray,
    segment_positions: np.ndarray,
) -> np.ndarray:
    """
    Calculate how a vertex should be displaced for a shape key.

    Args:
        base_pos: Base position of vertex
        tip_pos: Tip position of vertex (along tentacle)
        vertex_pos: Current vertex position
        config: Shape key configuration
        taper_radii: Array of taper radii at each segment
        segment_positions: Positions of segments along tentacle

    Returns:
        Displacement vector for the vertex
    """
    # Calculate tentacle direction and length
    tentacle_dir = tip_pos - base_pos
    tentacle_length = np.linalg.norm(tentacle_dir)

    if tentacle_length < 1e-6:
        return np.zeros(3)

    tentacle_dir_normalized = tentacle_dir / tentacle_length

    # Calculate position along tentacle (0.0 = base, 1.0 = tip)
    vertex_offset = vertex_pos - base_pos
    t = np.dot(vertex_offset, tentacle_dir_normalized) / tentacle_length
    t = np.clip(t, 0.0, 1.0)

    # Get base and target radii
    base_radius = taper_radii[0] if len(taper_radii) > 0 else 0.04
    target_radius = taper_radii[-1] if len(taper_radii) > 0 else 0.01
    current_radius = base_radius + (target_radius - base_radius) * t

    # Calculate radial direction (perpendicular to tentacle axis)
    axial_component = np.dot(vertex_offset, tentacle_dir_normalized) * tentacle_dir_normalized
    radial_component = vertex_offset - axial_component
    radial_length = np.linalg.norm(radial_component)

    if radial_length < 1e-6:
        radial_dir = np.array([1.0, 0.0, 0.0])  # Default direction
    else:
        radial_dir = radial_component / radial_length

    # Initialize displacement
    displacement = np.zeros(3)

    # Apply diameter scaling
    diameter_factor = config.diameter_scale - 1.0
    new_radial_length = radial_length * config.diameter_scale
    displacement += (new_radial_length - radial_length) * radial_dir

    # Apply localized squeeze
    if config.squeeze_position is not None:
        dist_to_center = abs(t - config.squeeze_position)
        width = config.squeeze_width
        # Gaussian-like falloff
        falloff = np.exp(-(dist_to_center ** 2) / (2 * width ** 2))
        squeeze_amount = falloff * 0.3  # Max 30% squeeze at center

        # Apply squeeze radially
        squeezed_radial = new_radial_length * (1.0 - squeeze_amount)
        displacement += (squeezed_radial - new_radial_length) * radial_dir

    # Apply curl deformation
    if config.curl_angle != 0.0 and t >= config.curl_start:
        curl_rad = np.radians(config.curl_angle)
        curl_progress = (t - config.curl_start) / (1.0 - config.curl_start)
        curl_amount = curl_progress * curl_rad

        # Calculate curl displacement (spiral around the tentacle axis)
        curl_radius = current_radius * 2.0 * curl_progress
        curl_x = curl_radius * np.cos(curl_amount)
        curl_y = curl_radius * np.sin(curl_amount)

        # Apply curl in perpendicular plane
        perp1 = np.cross(tentacle_dir_normalized, np.array([0, 0, 1]))
        if np.linalg.norm(perp1) < 1e-6:
            perp1 = np.cross(tentacle_dir_normalized, np.array([0, 1, 0]))
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(tentacle_dir_normalized, perp1)

        displacement += curl_x * perp1 + curl_y * perp2

    # Apply length scaling along tentacle axis
    length_scale_offset = (config.length_scale - 1.0) * t
    displacement += length_scale_offset * axial_component

    # Volume preservation (approximate compensation)
    if config.volume_preservation > 0 and config.diameter_scale < 1.0:
        # When compressed, bulge slightly to preserve volume
        volume_factor = 1.0 + config.volume_preservation * 0.3 * (1.0 - config.diameter_scale)
        displacement *= volume_factor

    return displacement


class ShapeKeyGenerator:
    """Generator for procedural shape keys."""

    def __init__(self):
        """Initialize the shape key generator."""
        pass

    def generate_shape_key(
        self,
        base_vertices: np.ndarray,
        tip_vertices: np.ndarray,
        vertices: np.ndarray,
        taper_radii: np.ndarray,
        segment_positions: np.ndarray,
        config: ShapeKeyConfig,
        mesh_obj: Optional["Object"] = None,
    ) -> ShapeKeyResult:
        """
        Generate a shape key from configuration.

        Args:
            base_vertices: Vertices of the base shape (Nx3)
            tip_vertices: Vertices of the target shape (Nx3)
            vertices: Full vertex array from mesh
            taper_radii: Taper radii at each segment
            segment_positions: Positions of segments along tentacle
            config: Shape key configuration
            mesh_obj: Mesh object for Blender (required for Blender mode)

        Returns:
            ShapeKeyResult with generation details
        """
        if not BLENDER_AVAILABLE or mesh_obj is None:
            # Return numpy-only result for testing
            return self._generate_numpy(
                base_vertices, tip_vertices, vertices,
                taper_radii, segment_positions, config
            )

        # Blender implementation
        return self._generate_blender(
            base_vertices, tip_vertices, vertices,
            taper_radii, segment_positions, config, mesh_obj
        )

    def _generate_numpy(
        self,
        base_vertices: np.ndarray,
        tip_vertices: np.ndarray,
        vertices: np.ndarray,
        taper_radii: np.ndarray,
        segment_positions: np.ndarray,
        config: ShapeKeyConfig,
    ) -> ShapeKeyResult:
        """Generate shape key using numpy (for testing without Blender)."""
        # Calculate base and tip positions (average)
        base_pos = np.mean(base_vertices, axis=0)
        tip_pos = np.mean(tip_vertices, axis=0)

        # Calculate displacements for each vertex
        displacements = np.zeros_like(vertices)
        for i in range(len(vertices)):
            displacement = _calculate_vertex_displacement(
                base_pos, tip_pos, vertices[i],
                config, taper_radii, segment_positions
            )
            displacements[i] = displacement

        # Calculate metrics
        displacement_lengths = np.linalg.norm(displacements, axis=1)
        max_displacement = np.max(displacement_lengths) if len(displacement_lengths) > 0 else 0.0

        # Approximate volume change
        base_volume = self._estimate_volume(vertices)
        deformed_vertices = vertices + displacements
        new_volume = self._estimate_volume(deformed_vertices)
        volume_change = ((new_volume - base_volume) / base_volume * 100.0) if base_volume > 0 else 0.0

        return ShapeKeyResult(
            shape_key_name=config.get_shape_key_name(),
            vertex_count=len(vertices),
            max_displacement=float(max_displacement),
            volume_change=float(volume_change),
            success=True,
        )

    def _generate_blender(
        self,
        base_vertices: np.ndarray,
        tip_vertices: np.ndarray,
        vertices: np.ndarray,
        taper_radii: np.ndarray,
        segment_positions: np.ndarray,
        config: ShapeKeyConfig,
        mesh_obj: "Object",
    ) -> ShapeKeyResult:
        """Generate shape key in Blender."""
        if mesh_obj is None:
            return ShapeKeyResult(
                shape_key_name=config.get_shape_key_name(),
                vertex_count=0,
                max_displacement=0.0,
                volume_change=0.0,
                success=False,
                error="mesh_obj required for Blender shape key generation"
            )

        # Calculate base and tip positions
        base_pos = np.mean(base_vertices, axis=0)
        tip_pos = np.mean(tip_vertices, axis=0)

        # Calculate displacements
        displacements = []
        for i in range(len(vertices)):
            displacement = _calculate_vertex_displacement(
                base_pos, tip_pos, vertices[i],
                config, taper_radii, segment_positions
            )
            displacements.append(displacement)

        # Create shape key
        shape_key = mesh_obj.shape_key_add(name=config.get_shape_key_name())

        # Set vertex positions
        for i, displacement in enumerate(displacements):
            if i < len(shape_key.data):
                new_co = vertices[i] + displacement
                shape_key.data[i].co = (new_co[0], new_co[1], new_co[2])

        # Calculate metrics
        displacement_lengths = [np.linalg.norm(d) for d in displacements]
        max_disp = max(displacement_lengths) if displacement_lengths else 0.0

        base_volume = self._estimate_volume(vertices)
        deformed_vertices = vertices + np.array(displacements)
        new_volume = self._estimate_volume(deformed_vertices)
        volume_change = ((new_volume - base_volume) / base_volume * 100.0) if base_volume > 0 else 0.0

        return ShapeKeyResult(
            shape_key_name=config.get_shape_key_name(),
            vertex_count=len(vertices),
            max_displacement=float(max_disp),
            volume_change=float(volume_change),
            success=True,
        )

    def _estimate_volume(self, vertices: np.ndarray) -> float:
        """Estimate mesh volume using bounding box."""
        if len(vertices) < 4:
            return 0.0

        # Use convex hull to estimate volume if scipy available
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(vertices)
            return float(hull.volume)
        except Exception:
            # Fallback: estimate using bounding box
            mins = np.min(vertices, axis=0)
            maxs = np.max(vertices, axis=0)
            return float(np.prod(maxs - mins))

    def generate_all_presets(
        self,
        base_vertices: np.ndarray,
        tip_vertices: np.ndarray,
        vertices: np.ndarray,
        taper_radii: np.ndarray,
        segment_positions: np.ndarray,
        mesh_obj: Optional["Object"] = None,
    ) -> Dict[str, ShapeKeyResult]:
        """
        Generate all predefined shape keys.

        Args:
            base_vertices: Base shape vertices
            tip_vertices: Target shape vertices (for scaling reference)
            vertices: Full mesh vertices
            taper_radii: Taper radii at each segment
            segment_positions: Segment positions along tentacle
            mesh_obj: Mesh object for Blender (required for Blender mode)

        Returns:
            Dictionary mapping preset names to ShapeKeyResults
        """
        results = {}
        for preset in ShapeKeyPreset:
            if preset == ShapeKeyPreset.BASE:
                continue  # Base shape is the reference

            config = get_preset_config(preset)
            result = self.generate_shape_key(
                base_vertices, tip_vertices, vertices,
                taper_radii, segment_positions, config, mesh_obj
            )
            results[preset.value] = result

        return results
