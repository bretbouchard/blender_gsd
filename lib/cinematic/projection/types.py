"""
Projection Types for Anamorphic / Forced Perspective System

Defines dataclasses for camera frustum raycasting, projection results,
and anamorphic installation configurations.

Part of Phase 9.0 - Projection Foundation (REQ-ANAM-01)
Beads: blender_gsd-34
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum


class SurfaceType(Enum):
    """Types of surfaces for projection filtering."""
    FLOOR = "floor"
    WALL = "wall"
    CEILING = "ceiling"
    CUSTOM = "custom"
    ALL = "all"


class ProjectionMode(Enum):
    """How the projection should be applied."""
    EMISSION = "emission"      # Emissive material (glows)
    DIFFUSE = "diffuse"        # Standard diffuse texture
    DECAL = "decal"            # Decal/overlay on existing material
    REPLACE = "replace"        # Replace existing material


@dataclass
class RayHit:
    """
    Result of a single ray-geometry intersection.

    Records where a ray from the camera hit scene geometry,
    including position, normal, and UV information.
    """
    # Hit position in world space
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Surface normal at hit point
    normal: Tuple[float, float, float] = (0.0, 0.0, 1.0)

    # UV coordinates on the hit surface (if available)
    uv: Optional[Tuple[float, float]] = None

    # Distance from ray origin to hit point
    distance: float = 0.0

    # Object that was hit (name in Blender)
    object_name: str = ""

    # Face/polygon index that was hit
    face_index: int = -1

    # Whether this is a valid hit
    hit: bool = False

    # Source pixel coordinates (from projection image)
    pixel_x: int = 0
    pixel_y: int = 0

    # Color at this pixel (from source image)
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "position": list(self.position),
            "normal": list(self.normal),
            "uv": list(self.uv) if self.uv else None,
            "distance": self.distance,
            "object_name": self.object_name,
            "face_index": self.face_index,
            "hit": self.hit,
            "pixel_x": self.pixel_x,
            "pixel_y": self.pixel_y,
            "color": list(self.color),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RayHit:
        """Create from dictionary."""
        uv_data = data.get("uv")
        uv = tuple(uv_data) if uv_data else None

        return cls(
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            normal=tuple(data.get("normal", (0.0, 0.0, 1.0))),
            uv=uv,
            distance=data.get("distance", 0.0),
            object_name=data.get("object_name", ""),
            face_index=data.get("face_index", -1),
            hit=data.get("hit", False),
            pixel_x=data.get("pixel_x", 0),
            pixel_y=data.get("pixel_y", 0),
            color=tuple(data.get("color", (1.0, 1.0, 1.0, 1.0))),
        )


@dataclass
class FrustumConfig:
    """
    Configuration for camera frustum raycasting.

    Defines how rays are generated from the camera viewpoint
    for projection onto scene geometry.
    """
    # Resolution of the ray grid (image dimensions)
    resolution_x: int = 1920
    resolution_y: int = 1080

    # Camera field of view (degrees)
    fov: float = 50.0

    # Near and far clipping distances
    near_clip: float = 0.1
    far_clip: float = 1000.0

    # Sub-sampling for performance (1 = full resolution, 2 = half, etc.)
    subsample: int = 1

    # Only cast rays within this region (0-1 normalized)
    region_min_x: float = 0.0
    region_min_y: float = 0.0
    region_max_x: float = 1.0
    region_max_y: float = 1.0

    # Filter by surface type
    surface_filter: SurfaceType = SurfaceType.ALL

    # Maximum number of hits per ray (for multi-surface projection)
    max_hits: int = 1

    # Ignore objects matching these patterns
    ignore_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resolution_x": self.resolution_x,
            "resolution_y": self.resolution_y,
            "fov": self.fov,
            "near_clip": self.near_clip,
            "far_clip": self.far_clip,
            "subsample": self.subsample,
            "region_min_x": self.region_min_x,
            "region_min_y": self.region_min_y,
            "region_max_x": self.region_max_x,
            "region_max_y": self.region_max_y,
            "surface_filter": self.surface_filter.value,
            "max_hits": self.max_hits,
            "ignore_patterns": self.ignore_patterns,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FrustumConfig:
        """Create from dictionary."""
        surface_filter = SurfaceType(data.get("surface_filter", "all"))

        return cls(
            resolution_x=data.get("resolution_x", 1920),
            resolution_y=data.get("resolution_y", 1080),
            fov=data.get("fov", 50.0),
            near_clip=data.get("near_clip", 0.1),
            far_clip=data.get("far_clip", 1000.0),
            subsample=data.get("subsample", 1),
            region_min_x=data.get("region_min_x", 0.0),
            region_min_y=data.get("region_min_y", 0.0),
            region_max_x=data.get("region_max_x", 1.0),
            region_max_y=data.get("region_max_y", 1.0),
            surface_filter=surface_filter,
            max_hits=data.get("max_hits", 1),
            ignore_patterns=data.get("ignore_patterns", []),
        )


@dataclass
class ProjectionResult:
    """
    Complete result of a frustum projection operation.

    Contains all ray hits, grouped by surface object,
    with statistics and metadata.
    """
    # All ray hits (flat list)
    hits: List[RayHit] = field(default_factory=list)

    # Hits grouped by object name
    hits_by_object: Dict[str, List[RayHit]] = field(default_factory=dict)

    # Total rays cast
    total_rays: int = 0

    # Rays that hit geometry
    hit_count: int = 0

    # Rays that missed
    miss_count: int = 0

    # Processing time in seconds
    process_time: float = 0.0

    # Source camera name
    camera_name: str = ""

    # Source image path (if applicable)
    source_image: str = ""

    # Configuration used
    config: Optional[FrustumConfig] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "hits": [h.to_dict() for h in self.hits],
            "hits_by_object": {
                k: [h.to_dict() for h in v]
                for k, v in self.hits_by_object.items()
            },
            "total_rays": self.total_rays,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "process_time": self.process_time,
            "camera_name": self.camera_name,
            "source_image": self.source_image,
            "config": self.config.to_dict() if self.config else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectionResult:
        """Create from dictionary."""
        hits = [RayHit.from_dict(h) for h in data.get("hits", [])]

        hits_by_object = {}
        for obj_name, obj_hits in data.get("hits_by_object", {}).items():
            hits_by_object[obj_name] = [RayHit.from_dict(h) for h in obj_hits]

        config_data = data.get("config")
        config = FrustumConfig.from_dict(config_data) if config_data else None

        return cls(
            hits=hits,
            hits_by_object=hits_by_object,
            total_rays=data.get("total_rays", 0),
            hit_count=data.get("hit_count", 0),
            miss_count=data.get("miss_count", 0),
            process_time=data.get("process_time", 0.0),
            camera_name=data.get("camera_name", ""),
            source_image=data.get("source_image", ""),
            config=config,
        )

    @property
    def hit_rate(self) -> float:
        """Calculate the percentage of rays that hit geometry."""
        if self.total_rays == 0:
            return 0.0
        return (self.hit_count / self.total_rays) * 100.0

    @property
    def objects_hit(self) -> List[str]:
        """List of object names that were hit."""
        return list(self.hits_by_object.keys())


@dataclass
class AnamorphicProjectionConfig:
    """
    Complete configuration for one anamorphic installation.

    Defines a single projection setup with source image,
    camera position, target surfaces, and visibility settings.
    """
    # Unique name for this projection
    name: str = "anamorphic_01"

    # Source image to project
    source_image: str = ""

    # Projection camera (the "sweet spot" viewpoint)
    camera_name: str = ""

    # Target surface objects (empty = auto-detect)
    target_surfaces: List[str] = field(default_factory=list)

    # Surface types to include
    surface_types: List[SurfaceType] = field(default_factory=lambda: [SurfaceType.ALL])

    # How to apply the projection
    projection_mode: ProjectionMode = ProjectionMode.EMISSION

    # Sweet spot zone (visibility range from camera)
    sweet_spot_radius: float = 0.5  # meters

    # Transition distance for fade in/out
    transition_distance: float = 0.2  # meters

    # Material intensity (for emission mode)
    intensity: float = 1.0

    # Resolution for baking
    bake_resolution: int = 2048

    # Non-destructive mode (keep original materials)
    non_destructive: bool = True

    # Output texture path
    output_texture: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "source_image": self.source_image,
            "camera_name": self.camera_name,
            "target_surfaces": self.target_surfaces,
            "surface_types": [s.value for s in self.surface_types],
            "projection_mode": self.projection_mode.value,
            "sweet_spot_radius": self.sweet_spot_radius,
            "transition_distance": self.transition_distance,
            "intensity": self.intensity,
            "bake_resolution": self.bake_resolution,
            "non_destructive": self.non_destructive,
            "output_texture": self.output_texture,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AnamorphicProjectionConfig:
        """Create from dictionary."""
        surface_types = [
            SurfaceType(s) for s in data.get("surface_types", ["all"])
        ]

        return cls(
            name=data.get("name", "anamorphic_01"),
            source_image=data.get("source_image", ""),
            camera_name=data.get("camera_name", ""),
            target_surfaces=data.get("target_surfaces", []),
            surface_types=surface_types,
            projection_mode=ProjectionMode(data.get("projection_mode", "emission")),
            sweet_spot_radius=data.get("sweet_spot_radius", 0.5),
            transition_distance=data.get("transition_distance", 0.2),
            intensity=data.get("intensity", 1.0),
            bake_resolution=data.get("bake_resolution", 2048),
            non_destructive=data.get("non_destructive", True),
            output_texture=data.get("output_texture", ""),
        )


@dataclass
class SurfaceInfo:
    """
    Information about a detected surface for projection.

    Contains geometry and material info for a surface
    that could be used for projection.
    """
    # Object name in Blender
    object_name: str = ""

    # Surface type classification
    surface_type: SurfaceType = SurfaceType.CUSTOM

    # Bounding box center
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Surface normal (dominant direction)
    normal: Tuple[float, float, float] = (0.0, 0.0, 1.0)

    # Surface area in square meters
    area: float = 0.0

    # Number of faces/polygons
    face_count: int = 0

    # Whether surface is in camera frustum
    in_frustum: bool = False

    # Whether surface is occluded from camera
    occluded: bool = False

    # Has valid UV map
    has_uv: bool = False

    # UV map name
    uv_layer: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "object_name": self.object_name,
            "surface_type": self.surface_type.value,
            "center": list(self.center),
            "normal": list(self.normal),
            "area": self.area,
            "face_count": self.face_count,
            "in_frustum": self.in_frustum,
            "occluded": self.occluded,
            "has_uv": self.has_uv,
            "uv_layer": self.uv_layer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SurfaceInfo:
        """Create from dictionary."""
        return cls(
            object_name=data.get("object_name", ""),
            surface_type=SurfaceType(data.get("surface_type", "custom")),
            center=tuple(data.get("center", (0.0, 0.0, 0.0))),
            normal=tuple(data.get("normal", (0.0, 0.0, 1.0))),
            area=data.get("area", 0.0),
            face_count=data.get("face_count", 0),
            in_frustum=data.get("in_frustum", False),
            occluded=data.get("occluded", False),
            has_uv=data.get("has_uv", False),
            uv_layer=data.get("uv_layer", ""),
        )
