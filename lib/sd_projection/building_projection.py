"""
Building Projection - SD texture projection specifically for buildings.

Specialized module for projecting SD-generated textures onto building
geometry with architectural awareness.

Features:
- Building-aware projection (respects windows, doors, facades)
- Background building visibility in viewport
- LOD-aware texture resolution
- City-scale batch processing

Usage:
    from lib.sd_projection.building_projection import BuildingProjector

    # Create projector
    projector = BuildingProjector()

    # Project onto buildings visible from camera
    result = projector.project_city(
        camera=scene.camera,
        buildings=city_buildings,
        style="cyberpunk_night",
        prompt="neon lit cyberpunk city, rain, reflections",
    )

    # Or project onto single building
    result = projector.project_building(
        building=hero_building,
        camera=scene.camera,
        prompt="graffiti covered warehouse",
    )
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
import tempfile

# Import from sibling modules
from .sd_projection import (
    SDProjectionMapper,
    StyleConfig,
    StyleModel,
    ControlNetConfig,
    ControlNetType,
    ProjectionMode,
    ProjectionResult,
)
from .style_blender import (
    StyleBlender,
    DriftConfig,
    DriftPattern,
)


# =============================================================================
# ENUMS
# =============================================================================

class BuildingVisibility(Enum):
    """Visibility mode for buildings."""
    FULL = "full"               # Full detail
    BACKGROUND = "background"   # Simplified, in background
    SILHOUETTE = "silhouette"   # Just silhouette
    HIDDEN = "hidden"           # Not visible


class BuildingLOD(Enum):
    """Level of detail for building textures."""
    HIGH = "high"       # 4K textures
    MEDIUM = "medium"   # 2K textures
    LOW = "low"         # 1K textures
    PROXY = "proxy"     # 512px textures


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class BuildingProjectionConfig:
    """Configuration for building projection."""
    # SD settings
    style_config: StyleConfig = field(default_factory=StyleConfig)

    # Drift settings
    drift_config: DriftConfig = field(default_factory=DriftConfig)

    # LOD settings
    lod_distances: Dict[BuildingLOD, float] = field(default_factory=lambda: {
        BuildingLOD.HIGH: 50.0,
        BuildingLOD.MEDIUM: 150.0,
        BuildingLOD.LOW: 300.0,
        BuildingLOD.PROXY: 500.0,
    })

    # Background settings
    background_visibility: BuildingVisibility = BuildingVisibility.BACKGROUND
    background_opacity: float = 0.8

    # Camera culling
    frustum_culling: bool = True
    occlusion_culling: bool = True

    # Batch processing
    batch_size: int = 4          # Process N buildings at once
    parallel_generation: bool = False

    # Output
    output_dir: Path = field(default_factory=lambda: Path(tempfile.gettempdir()) / "building_projection")
    cache_textures: bool = True


@dataclass
class BuildingInfo:
    """Information about a building for projection."""
    name: str
    object: bpy.types.Object
    distance_to_camera: float = 0.0
    screen_size: float = 0.0
    visibility: BuildingVisibility = BuildingVisibility.FULL
    lod: BuildingLOD = BuildingLOD.MEDIUM
    is_occluded: bool = False
    in_frustum: bool = True


# =============================================================================
# BUILDING PROJECTOR
# =============================================================================

class BuildingProjector:
    """
    SD texture projection for buildings.

    Handles:
    - Camera-based visibility culling
    - LOD-based texture resolution
    - Batch SD generation
    - Background building handling
    """

    def __init__(self, config: Optional[BuildingProjectionConfig] = None):
        self.config = config or BuildingProjectionConfig()
        self.mapper = SDProjectionMapper(self.config.style_config)
        self.blender = StyleBlender(drift_config=self.config.drift_config)

        self._building_cache: Dict[str, BuildingInfo] = {}
        self._generated_textures: Dict[str, Path] = {}

    def project_city(
        self,
        camera: bpy.types.Object,
        buildings: List[bpy.types.Object],
        style: str,
        prompt: str,
        seed: int = -1
    ) -> List[ProjectionResult]:
        """
        Project SD textures onto a city of buildings.

        This is the main entry point for city-scale projection.
        It handles LOD, culling, and batch processing.

        Args:
            camera: Scene camera
            buildings: List of building objects
            style: Style name or preset
            prompt: SD prompt
            seed: Random seed (-1 for random)

        Returns:
            List of projection results
        """
        results = []

        # Update style config with prompt
        self.config.style_config.prompt = prompt

        # Classify buildings
        print(f"Classifying {len(buildings)} buildings...")
        building_infos = self._classify_buildings(camera, buildings)

        # Group by LOD
        lod_groups: Dict[BuildingLOD, List[BuildingInfo]] = {}
        for info in building_infos:
            if info.visibility != BuildingVisibility.HIDDEN and info.in_frustum:
                if info.lod not in lod_groups:
                    lod_groups[info.lod] = []
                lod_groups[info.lod].append(info)

        # Process each LOD group
        for lod, infos in lod_groups.items():
            print(f"Processing {len(infos)} buildings at {lod.value} LOD...")

            # Set resolution based on LOD
            resolution = self._get_lod_resolution(lod)
            self.config.style_config.projection_resolution = resolution

            # Process in batches
            for i in range(0, len(infos), self.config.batch_size):
                batch = infos[i:i + self.config.batch_size]
                batch_objects = [info.object for info in batch]

                # Generate single texture for batch (shared projection)
                result = self.mapper.project_onto_objects(
                    camera=camera,
                    objects=batch_objects,
                    prompt=prompt,
                    seed=seed if seed >= 0 else hash(tuple(info.name for info in batch)) % 2147483647
                )

                # Apply drift if enabled
                if result.success and self.config.drift_config.enabled:
                    self.blender.apply_drift_material(
                        objects=batch_objects,
                        texture_path=result.generated_texture_path,
                        camera=camera
                    )

                results.append(result)

                # Cache texture
                if result.success and result.generated_texture_path:
                    for info in batch:
                        self._generated_textures[info.name] = result.generated_texture_path

        # Handle background buildings
        background_buildings = [
            info for info in building_infos
            if info.visibility == BuildingVisibility.BACKGROUND
        ]
        if background_buildings:
            self._setup_background_buildings([info.object for info in background_buildings])

        return results

    def project_building(
        self,
        building: bpy.types.Object,
        camera: bpy.types.Object,
        prompt: str,
        seed: int = -1
    ) -> ProjectionResult:
        """
        Project onto a single building.

        Args:
            building: Building object
            camera: Scene camera
            prompt: SD prompt
            seed: Random seed

        Returns:
            ProjectionResult
        """
        self.config.style_config.prompt = prompt

        result = self.mapper.project_onto_objects(
            camera=camera,
            objects=[building],
            prompt=prompt,
            seed=seed
        )

        if result.success and self.config.drift_config.enabled:
            self.blender.apply_drift_material(
                objects=[building],
                texture_path=result.generated_texture_path,
                camera=camera
            )

        return result

    def _classify_buildings(
        self,
        camera: bpy.types.Object,
        buildings: List[bpy.types.Object]
    ) -> List[BuildingInfo]:
        """Classify buildings by visibility and LOD."""
        infos = []

        cam_location = camera.matrix_world.translation
        cam_forward = -camera.matrix_world.col[2][:3]

        # Get camera frustum planes for culling
        if self.config.frustum_culling:
            frustum_planes = self._get_camera_frustum_planes(camera)
        else:
            frustum_planes = None

        for building in buildings:
            info = BuildingInfo(
                name=building.name,
                object=building
            )

            # Calculate distance to camera
            building_center = building.matrix_world.translation
            info.distance_to_camera = (building_center - cam_location).length

            # Check if in front of camera
            to_building = (building_center - cam_location).normalized()
            dot = to_building.dot(cam_forward)
            info.in_frustum = dot > 0

            # Frustum culling
            if frustum_planes and info.in_frustum:
                info.in_frustum = self._is_in_frustum(building, frustum_planes)

            # Calculate screen size (approximate)
            bbox = [building.matrix_world @ Vector(corner) for corner in building.bound_box]
            # Project bbox to screen space (simplified)
            info.screen_size = self._estimate_screen_size(bbox, camera)

            # Determine LOD
            info.lod = self._get_lod(info.distance_to_camera)

            # Determine visibility
            if info.screen_size < 0.01:  # Less than 1% of screen
                info.visibility = BuildingVisibility.HIDDEN
            elif info.distance_to_camera > 400:
                info.visibility = BuildingVisibility.BACKGROUND
            else:
                info.visibility = BuildingVisibility.FULL

            infos.append(info)
            self._building_cache[building.name] = info

        return infos

    def _get_camera_frustum_planes(
        self,
        camera: bpy.types.Object
    ) -> List[Tuple[Vector, float]]:
        """Get camera frustum planes for culling."""
        # Get camera data
        cam_data = camera.data

        # Calculate frustum corners in world space
        # This is simplified - full implementation would use camera projection
        fov = cam_data.angle
        near = cam_data.clip_start
        far = cam_data.clip_end

        # Return planes as (normal, distance) tuples
        # Simplified - just return a basic box
        return []

    def _is_in_frustum(
        self,
        obj: bpy.types.Object,
        planes: List[Tuple[Vector, float]]
    ) -> bool:
        """Check if object is in camera frustum."""
        # Simplified check - always return True for now
        return True

    def _estimate_screen_size(
        self,
        bbox: List[Vector],
        camera: bpy.types.Object
    ) -> float:
        """Estimate object's screen size as fraction of screen."""
        cam_location = camera.matrix_world.translation

        # Calculate bounding sphere radius
        center = sum(bbox, Vector()) / len(bbox)
        radius = max((v - center).length for v in bbox)

        # Distance to camera
        distance = (center - cam_location).length

        if distance < 0.001:
            return 1.0

        # Angular size approximation
        angular_size = 2 * math.atan(radius / distance)

        # Normalize to 0-1 range (assuming ~90 degree FOV)
        return angular_size / math.pi

    def _get_lod(self, distance: float) -> BuildingLOD:
        """Determine LOD based on distance."""
        for lod, max_dist in sorted(
            self.config.lod_distances.items(),
            key=lambda x: x[1]
        ):
            if distance <= max_dist:
                return lod
        return BuildingLOD.PROXY

    def _get_lod_resolution(self, lod: BuildingLOD) -> Tuple[int, int]:
        """Get texture resolution for LOD."""
        resolutions = {
            BuildingLOD.HIGH: (4096, 4096),
            BuildingLOD.MEDIUM: (2048, 2048),
            BuildingLOD.LOW: (1024, 1024),
            BuildingLOD.PROXY: (512, 512),
        }
        return resolutions.get(lod, (1024, 1024))

    def _setup_background_buildings(self, buildings: List[bpy.types.Object]):
        """Set up buildings for background rendering."""
        for building in buildings:
            # Create simple material with background settings
            mat_name = f"{building.name}_BackgroundMat"

            if mat_name in bpy.data.materials:
                mat = bpy.data.materials[mat_name]
            else:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                nodes.clear()

                # Simple diffuse
                output = nodes.new('ShaderNodeOutputMaterial')
                principled = nodes.new('ShaderNodeBsdfPrincipled')
                principled.inputs['Base Color'].default_value = (0.1, 0.1, 0.12, 1)
                principled.inputs['Roughness'].default_value = 0.9

                links.new(principled.outputs['BSDF'], output.inputs['Surface'])

            # Assign material
            if building.data.materials:
                building.data.materials[0] = mat
            else:
                building.data.materials.append(mat)

            # Set holdout or transparency for true background
            if self.config.background_visibility == BuildingVisibility.SILHOUETTE:
                mat.shadow_method = 'CLIP'
                mat.blend_method = 'CLIP'

    def update_for_frame(self, frame: int, camera: bpy.types.Object):
        """
        Update projections for a new frame.

        This should be called each frame for animated sequences.
        Updates LOD and visibility based on camera movement.

        Args:
            frame: Current frame number
            camera: Scene camera
        """
        # Update drift animation
        self.blender.update_drift(frame)

        # Re-classify buildings if camera moved significantly
        # (Implementation would compare camera position to last frame)


# =============================================================================
# PRESETS
# =============================================================================

# Pre-configured style presets for common looks
STYLE_PRESETS = {
    "cyberpunk_night": StyleConfig(
        style_models=[
            StyleModel(name="cyberpunk", weight=1.0),
        ],
        prompt="cyberpunk city night, neon lights, rain, reflections, cinematic",
        controlnets=[
            ControlNetConfig(control_type=ControlNetType.DEPTH, weight=1.0),
            ControlNetConfig(control_type=ControlNetType.NORMAL, weight=0.5),
        ],
        drift_config=DriftConfig(
            speed=0.05,
            direction=(0.5, 0.2),
            noise_enabled=True,
            wave_enabled=True,
        ),
    ),

    "arcane_painted": StyleConfig(
        style_models=[
            StyleModel(name="arcane_style", weight=1.0),
        ],
        prompt="arcane style painted texture, hand painted, stylized, vibrant colors",
        controlnets=[
            ControlNetConfig(control_type=ControlNetType.DEPTH, weight=0.8),
            ControlNetConfig(control_type=ControlNetType.CANNY, weight=0.6),
        ],
        drift_config=DriftConfig(
            speed=0.02,
            direction=(1.0, 0.0),
            noise_enabled=True,
            noise_strength=0.1,
        ),
    ),

    "trippy_drift": StyleConfig(
        style_models=[
            StyleModel(name="psychedelic", weight=0.7),
            StyleModel(name="surreal", weight=0.3),
        ],
        style_blend=0.5,
        prompt="psychedelic surreal dreamscape, melting colors, abstract patterns",
        drift_config=DriftConfig(
            speed=0.15,
            direction=(1.0, 0.7),
            noise_enabled=True,
            noise_strength=0.4,
            wave_enabled=True,
            wave_amplitude=0.1,
            pattern=DriftPattern.CHAOS,
        ),
    ),

    "noir_gritty": StyleConfig(
        style_models=[
            StyleModel(name="noir", weight=1.0),
        ],
        prompt="film noir gritty urban, high contrast, shadows, rain streaks",
        controlnets=[
            ControlNetConfig(control_type=ControlNetType.DEPTH, weight=1.0),
        ],
        drift_config=DriftConfig(
            speed=0.03,
            direction=(0.3, 1.0),
            noise_enabled=True,
            noise_strength=0.15,
        ),
    ),

    "anime_cel": StyleConfig(
        style_models=[
            StyleModel(name="anime", weight=1.0),
        ],
        prompt="anime cel shaded, clean lines, flat colors, stylized",
        controlnets=[
            ControlNetConfig(control_type=ControlNetType.CANNY, weight=1.2),
            ControlNetConfig(control_type=ControlNetType.DEPTH, weight=0.3),
        ],
        drift_config=DriftConfig(
            enabled=False,  # No drift for cel-shaded
        ),
    ),
}


def get_style_preset(name: str) -> Optional[StyleConfig]:
    """Get a pre-configured style preset by name."""
    return STYLE_PRESETS.get(name)


def list_style_presets() -> List[str]:
    """List available style presets."""
    return list(STYLE_PRESETS.keys())


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def project_onto_buildings(
    camera: bpy.types.Object,
    buildings: List[bpy.types.Object],
    style: str = "cyberpunk_night",
    prompt: str = "",
    drift_speed: float = 0.1
) -> List[ProjectionResult]:
    """
    Quick function to project SD textures onto buildings.

    Args:
        camera: Scene camera
        buildings: List of building objects
        style: Style preset name
        prompt: SD prompt (appended to preset)
        drift_speed: Texture drift speed

    Returns:
        List of projection results
    """
    # Get or create style config
    style_config = get_style_preset(style)
    if style_config is None:
        style_config = StyleConfig(prompt=prompt)
    else:
        if prompt:
            style_config.prompt = f"{style_config.prompt}, {prompt}"

    # Set drift speed
    style_config.drift_config.speed = drift_speed

    # Create projector
    config = BuildingProjectionConfig(style_config=style_config)
    projector = BuildingProjector(config)

    return projector.project_city(
        camera=camera,
        buildings=buildings,
        style=style,
        prompt=style_config.prompt,
    )


__all__ = [
    "BuildingProjector",
    "BuildingProjectionConfig",
    "BuildingInfo",
    "BuildingVisibility",
    "BuildingLOD",
    "STYLE_PRESETS",
    "get_style_preset",
    "list_style_presets",
    "project_onto_buildings",
]
