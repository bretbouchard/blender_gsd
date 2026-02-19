"""
Camera Position Zones for Anamorphic Projection

Defines camera position zones ("sweet spots") for visibility control.
Supports sphere, box, and custom zone volumes with animated camera support.

Part of Phase 9.4 - Camera Position Zones (REQ-ANAM-05)
Beads: blender_gsd-38
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .types import SurfaceInfo, SurfaceType

# Blender API guard for testing outside Blender
try:
    import bpy
    import mathutils
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Fallback Vector implementation for testing outside Blender
    class Vector:
        """Simple Vector fallback for testing outside Blender."""
        def __init__(self, data):
            if hasattr(data, '__iter__'):
                self._data = list(data)[:3]
                while len(self._data) < 3:
                    self._data.append(0.0)
            else:
                self._data = [float(data), 0.0, 0.0]

        def __getitem__(self, i):
            return self._data[i]

        def __add__(self, other):
            return Vector([self._data[i] + other._data[i] for i in range(3)])

        def __sub__(self, other):
            return Vector([self._data[i] - other._data[i] for i in range(3)])

        def __truediv__(self, scalar):
            return Vector([x / scalar for x in self._data])

        def __mul__(self, scalar):
            return Vector([x * scalar for x in self._data])

        def __rmul__(self, scalar):
            return self.__mul__(scalar)

        def dot(self, other):
            return sum(self._data[i] * other._data[i] for i in range(3))

        def length(self):
            return (sum(x * x for x in self._data)) ** 0.5

        def normalized(self):
            l = self.length()
            if l > 0:
                return Vector([x / l for x in self._data])
            return Vector([0, 0, 0])

        def normalize(self):
            l = self.length()
            if l > 0:
                self._data = [x / l for x in self._data]

        def cross(self, other):
            return Vector([
                self._data[1] * other._data[2] - self._data[2] * other._data[1],
                self._data[2] * other._data[0] - self._data[0] * other._data[2],
                self._data[0] * other._data[1] - self._data[1] * other._data[0],
            ])

        def copy(self):
            return Vector(self._data)

        @property
        def x(self):
            return self._data[0]

        @property
        def y(self):
            return self._data[1]

        @property
        def z(self):
            return self._data[2]

        def __iter__(self):
            return iter(self._data)

        def __repr__(self):
            return f"Vector({self._data})"

    Matrix = None


class ZoneType(Enum):
    """Types of camera zones."""
    SPHERE = "sphere"       # Spherical zone
    BOX = "box"             # Axis-aligned box
    CAPSULE = "capsule"     # Capsule (cylinder with hemispheres)
    CUSTOM = "custom"       # Custom mesh-based zone
    FRUSTUM = "frustum"     # Camera frustum-shaped zone


class ZoneTransition:
    """Types of zone transitions."""
    SHARP = "sharp"         # Instant on/off
    LINEAR = "linear"       # Linear fade
    SMOOTH = "smooth"       # Smooth (ease-in-out) fade
    EXPONENTIAL = "exponential"  # Exponential fade


@dataclass
class CameraZone:
    """
    Defines a camera position zone for visibility control.

    A zone defines a volume where the camera position affects
    object visibility, typically used for "sweet spot" viewing.
    """
    # Unique identifier
    id: str = ""

    # Zone name
    name: str = "zone_01"

    # Zone type
    zone_type: ZoneType = ZoneType.SPHERE

    # Center position (world space)
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Zone dimensions (interpretation depends on type)
    # Sphere: (radius, 0, 0)
    # Box: (half_width, half_height, half_depth)
    # Capsule: (radius, height, 0)
    dimensions: Tuple[float, float, float] = (1.0, 0.0, 0.0)

    # Transition type at zone boundary
    transition_type: str = ZoneTransition.LINEAR

    # Transition distance (fade range)
    transition_distance: float = 0.2

    # Target objects for visibility control
    target_objects: List[str] = field(default_factory=list)

    # Target collections (all objects in collection)
    target_collections: List[str] = field(default_factory=list)

    # Whether zone is enabled
    enabled: bool = True

    # Priority (higher = evaluated first)
    priority: int = 0

    # Associated projection/installation name
    installation_name: str = ""

    # Optional rotation for box/capsule zones (Euler XYZ degrees)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Invert zone (visible outside instead of inside)
    invert: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "zone_type": self.zone_type.value,
            "center": list(self.center),
            "dimensions": list(self.dimensions),
            "transition_type": self.transition_type,
            "transition_distance": self.transition_distance,
            "target_objects": self.target_objects,
            "target_collections": self.target_collections,
            "enabled": self.enabled,
            "priority": self.priority,
            "installation_name": self.installation_name,
            "rotation": list(self.rotation),
            "invert": self.invert,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CameraZone:
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "zone_01"),
            zone_type=ZoneType(data.get("zone_type", "sphere")),
            center=tuple(data.get("center", (0.0, 0.0, 0.0))),
            dimensions=tuple(data.get("dimensions", (1.0, 0.0, 0.0))),
            transition_type=data.get("transition_type", ZoneTransition.LINEAR),
            transition_distance=data.get("transition_distance", 0.2),
            target_objects=data.get("target_objects", []),
            target_collections=data.get("target_collections", []),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            installation_name=data.get("installation_name", ""),
            rotation=tuple(data.get("rotation", (0.0, 0.0, 0.0))),
            invert=data.get("invert", False),
        )

    def contains_point(self, point: Tuple[float, float, float]) -> float:
        """
        Check if point is in zone and return blend factor.

        Returns a value 0.0-1.0:
        - 0.0 = outside zone
        - 0.0-1.0 = in transition zone
        - 1.0 = fully inside zone

        Args:
            point: World space position to check

        Returns:
            Blend factor (0.0-1.0)
        """
        px, py, pz = point
        cx, cy, cz = self.center

        if self.zone_type == ZoneType.SPHERE:
            return self._check_sphere(px, py, pz, cx, cy, cz)
        elif self.zone_type == ZoneType.BOX:
            return self._check_box(px, py, pz, cx, cy, cz)
        elif self.zone_type == ZoneType.CAPSULE:
            return self._check_capsule(px, py, pz, cx, cy, cz)
        else:
            # Default to sphere
            return self._check_sphere(px, py, pz, cx, cy, cz)

    def _check_sphere(self, px, py, pz, cx, cy, cz) -> float:
        """Check sphere zone."""
        dx = px - cx
        dy = py - cy
        dz = pz - cz
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        radius = self.dimensions[0]
        inner_radius = max(0, radius - self.transition_distance)

        if distance >= radius:
            factor = 0.0
        elif distance <= inner_radius:
            factor = 1.0
        else:
            # In transition zone
            t = (distance - inner_radius) / self.transition_distance
            factor = self._apply_transition(1.0 - t)

        return (1.0 - factor) if self.invert else factor

    def _check_box(self, px, py, pz, cx, cy, cz) -> float:
        """Check axis-aligned box zone."""
        half_w, half_h, half_d = self.dimensions

        # Calculate distance from center in each axis
        dx = abs(px - cx)
        dy = abs(py - cy)
        dz = abs(pz - cz)

        # Check if inside full box
        inside = (dx <= half_w and dy <= half_h and dz <= half_d)

        # Check if inside inner box (for transition)
        inner_w = max(0, half_w - self.transition_distance)
        inner_h = max(0, half_h - self.transition_distance)
        inner_d = max(0, half_d - self.transition_distance)

        fully_inside = (dx <= inner_w and dy <= inner_h and dz <= inner_d)

        if fully_inside:
            factor = 1.0
        elif not inside:
            factor = 0.0
        else:
            # In transition zone - find closest edge
            edge_distances = [
                (half_w - dx) / self.transition_distance if dx > inner_w else 1.0,
                (half_h - dy) / self.transition_distance if dy > inner_h else 1.0,
                (half_d - dz) / self.transition_distance if dz > inner_d else 1.0,
            ]
            t = 1.0 - min(edge_distances)
            factor = self._apply_transition(1.0 - t)

        return factor if not self.invert else (1.0 - factor)

    def _check_capsule(self, px, py, pz, cx, cy, cz) -> float:
        """Check capsule zone (simplified - cylinder + hemispheres)."""
        radius = self.dimensions[0]
        height = self.dimensions[1]
        half_height = height / 2

        # Distance from center in XY plane
        dx = px - cx
        dy = py - cy
        xy_distance = math.sqrt(dx * dx + dy * dy)

        # Vertical position relative to cylinder center
        dz = pz - cz

        # Check cylinder section
        if abs(dz) <= half_height:
            # In cylinder section
            if xy_distance >= radius:
                factor = 0.0
            else:
                inner_r = max(0, radius - self.transition_distance)
                if xy_distance <= inner_r:
                    factor = 1.0
                else:
                    t = (xy_distance - inner_r) / self.transition_distance
                    factor = self._apply_transition(1.0 - t)
        else:
            # In hemisphere section
            if dz > half_height:
                # Top hemisphere
                sphere_center = (cx, cy, cz + half_height)
            else:
                # Bottom hemisphere
                sphere_center = (cx, cy, cz - half_height)

            dx_s = px - sphere_center[0]
            dy_s = py - sphere_center[1]
            dz_s = pz - sphere_center[2]
            distance = math.sqrt(dx_s * dx_s + dy_s * dy_s + dz_s * dz_s)

            if distance >= radius:
                factor = 0.0
            else:
                inner_r = max(0, radius - self.transition_distance)
                if distance <= inner_r:
                    factor = 1.0
                else:
                    t = (distance - inner_r) / self.transition_distance
                    factor = self._apply_transition(1.0 - t)

        return factor if not self.invert else (1.0 - factor)

    def _apply_transition(self, t: float) -> float:
        """Apply transition curve to blend factor."""
        t = max(0.0, min(1.0, t))

        if self.transition_type == ZoneTransition.SHARP:
            return 1.0 if t > 0.5 else 0.0
        elif self.transition_type == ZoneTransition.LINEAR:
            return t
        elif self.transition_type == ZoneTransition.SMOOTH:
            # Smoothstep
            return t * t * (3 - 2 * t)
        elif self.transition_type == ZoneTransition.EXPONENTIAL:
            return t * t
        else:
            return t


@dataclass
class ZoneState:
    """Current state of camera zone evaluation."""
    # Camera position when evaluated
    camera_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Current frame when evaluated
    frame: int = 0

    # Active zones (zones where factor > 0)
    active_zones: List[str] = field(default_factory=list)

    # Zone factors by zone ID
    zone_factors: Dict[str, float] = field(default_factory=dict)

    # Object visibility factors
    object_visibility: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "camera_position": list(self.camera_position),
            "frame": self.frame,
            "active_zones": self.active_zones,
            "zone_factors": self.zone_factors,
            "object_visibility": self.object_visibility,
        }


@dataclass
class ZoneManagerConfig:
    """Configuration for zone manager."""
    # Whether to use frame-based caching
    use_cache: bool = True

    # Cache size (frames)
    cache_size: int = 100

    # Default transition type for new zones
    default_transition: str = ZoneTransition.LINEAR

    # Default transition distance
    default_transition_distance: float = 0.2

    # Whether to blend overlapping zones
    blend_overlapping: bool = True

    # Blend mode for overlapping zones ("max", "add", "multiply")
    blend_mode: str = "max"


class ZoneManager:
    """
    Manages camera zones for visibility control.

    Handles zone creation, evaluation, and animated camera support
    for multiple installations per scene.
    """

    def __init__(self, config: Optional[ZoneManagerConfig] = None):
        self.config = config or ZoneManagerConfig()
        self.zones: Dict[str, CameraZone] = {}
        self._cache: Dict[int, ZoneState] = {}

    def add_zone(self, zone: CameraZone) -> None:
        """Add a zone to the manager."""
        if not zone.id:
            zone.id = zone.name
        self.zones[zone.id] = zone
        self._invalidate_cache()

    def remove_zone(self, zone_id: str) -> bool:
        """Remove a zone by ID."""
        if zone_id in self.zones:
            del self.zones[zone_id]
            self._invalidate_cache()
            return True
        return False

    def get_zone(self, zone_id: str) -> Optional[CameraZone]:
        """Get a zone by ID."""
        return self.zones.get(zone_id)

    def get_all_zones(self) -> List[CameraZone]:
        """Get all zones."""
        return list(self.zones.values())

    def get_zones_for_installation(self, installation_name: str) -> List[CameraZone]:
        """Get all zones for a specific installation."""
        return [
            z for z in self.zones.values()
            if z.installation_name == installation_name
        ]

    def evaluate(
        self,
        camera_position: Tuple[float, float, float],
        frame: int = 0,
    ) -> ZoneState:
        """
        Evaluate all zones for a camera position.

        Args:
            camera_position: Current camera world position
            frame: Current frame number (for caching)

        Returns:
            ZoneState with visibility information
        """
        # Check cache
        if self.config.use_cache and frame in self._cache:
            cached = self._cache[frame]
            if cached.camera_position == camera_position:
                return cached

        state = ZoneState(
            camera_position=camera_position,
            frame=frame,
        )

        # Evaluate each zone (sorted by priority)
        sorted_zones = sorted(
            [z for z in self.zones.values() if z.enabled],
            key=lambda z: -z.priority
        )

        for zone in sorted_zones:
            factor = zone.contains_point(camera_position)

            if factor > 0:
                state.active_zones.append(zone.id)
                state.zone_factors[zone.id] = factor

                # Update object visibility
                for obj_name in zone.target_objects:
                    self._update_visibility(state, obj_name, factor)

                # Update collection objects
                for coll_name in zone.target_collections:
                    self._update_collection_visibility(state, coll_name, factor)

        # Cache result
        if self.config.use_cache:
            self._cache[frame] = state
            # Trim cache if needed
            if len(self._cache) > self.config.cache_size:
                oldest = min(self._cache.keys())
                del self._cache[oldest]

        return state

    def _update_visibility(
        self,
        state: ZoneState,
        obj_name: str,
        factor: float,
    ) -> None:
        """Update object visibility based on blend mode."""
        if obj_name not in state.object_visibility:
            state.object_visibility[obj_name] = factor
        else:
            current = state.object_visibility[obj_name]
            if self.config.blend_mode == "max":
                state.object_visibility[obj_name] = max(current, factor)
            elif self.config.blend_mode == "add":
                state.object_visibility[obj_name] = min(1.0, current + factor)
            elif self.config.blend_mode == "multiply":
                state.object_visibility[obj_name] = current * factor

    def _update_collection_visibility(
        self,
        state: ZoneState,
        collection_name: str,
        factor: float,
    ) -> None:
        """Update visibility for all objects in a collection."""
        if not HAS_BLENDER:
            return

        collection = bpy.data.collections.get(collection_name)
        if collection:
            for obj in collection.all_objects:
                self._update_visibility(state, obj.name, factor)

    def _invalidate_cache(self) -> None:
        """Invalidate the evaluation cache."""
        self._cache.clear()

    def clear(self) -> None:
        """Remove all zones."""
        self.zones.clear()
        self._invalidate_cache()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize manager state to dictionary."""
        return {
            "config": {
                "use_cache": self.config.use_cache,
                "cache_size": self.config.cache_size,
                "default_transition": self.config.default_transition,
                "default_transition_distance": self.config.default_transition_distance,
                "blend_overlapping": self.config.blend_overlapping,
                "blend_mode": self.config.blend_mode,
            },
            "zones": [z.to_dict() for z in self.zones.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ZoneManager:
        """Create manager from dictionary."""
        config_data = data.get("config", {})
        config = ZoneManagerConfig(
            use_cache=config_data.get("use_cache", True),
            cache_size=config_data.get("cache_size", 100),
            default_transition=config_data.get("default_transition", ZoneTransition.LINEAR),
            default_transition_distance=config_data.get("default_transition_distance", 0.2),
            blend_overlapping=config_data.get("blend_overlapping", True),
            blend_mode=config_data.get("blend_mode", "max"),
        )

        manager = cls(config)

        for zone_data in data.get("zones", []):
            zone = CameraZone.from_dict(zone_data)
            manager.add_zone(zone)

        return manager


def create_sphere_zone(
    name: str,
    center: Tuple[float, float, float],
    radius: float,
    transition_distance: float = 0.2,
    target_objects: Optional[List[str]] = None,
) -> CameraZone:
    """
    Convenience function to create a spherical zone.

    Args:
        name: Zone name
        center: Zone center (world space)
        radius: Sphere radius
        transition_distance: Fade distance at edge
        target_objects: Objects controlled by this zone

    Returns:
        CameraZone configured as sphere
    """
    return CameraZone(
        id=name,
        name=name,
        zone_type=ZoneType.SPHERE,
        center=center,
        dimensions=(radius, 0.0, 0.0),
        transition_distance=transition_distance,
        target_objects=target_objects or [],
    )


def create_box_zone(
    name: str,
    center: Tuple[float, float, float],
    half_extents: Tuple[float, float, float],
    transition_distance: float = 0.2,
    target_objects: Optional[List[str]] = None,
) -> CameraZone:
    """
    Convenience function to create a box zone.

    Args:
        name: Zone name
        center: Zone center (world space)
        half_extents: (half_width, half_height, half_depth)
        transition_distance: Fade distance at edge
        target_objects: Objects controlled by this zone

    Returns:
        CameraZone configured as box
    """
    return CameraZone(
        id=name,
        name=name,
        zone_type=ZoneType.BOX,
        center=center,
        dimensions=half_extents,
        transition_distance=transition_distance,
        target_objects=target_objects or [],
    )


def create_sweet_spot(
    installation_name: str,
    camera_position: Tuple[float, float, float],
    sweet_spot_radius: float = 0.5,
    transition_distance: float = 0.2,
    target_objects: Optional[List[str]] = None,
) -> CameraZone:
    """
    Create a "sweet spot" zone for anamorphic viewing.

    This is the recommended zone type for anamorphic installations,
    where the artwork only looks correct from this specific position.

    Args:
        installation_name: Name of the projection installation
        camera_position: Ideal viewing position
        sweet_spot_radius: Radius of ideal viewing area
        transition_distance: Distance for fade transition
        target_objects: Objects to control visibility for

    Returns:
        CameraZone configured as sweet spot
    """
    return CameraZone(
        id=f"{installation_name}_sweet_spot",
        name=f"{installation_name} Sweet Spot",
        zone_type=ZoneType.SPHERE,
        center=camera_position,
        dimensions=(sweet_spot_radius, 0.0, 0.0),
        transition_type=ZoneTransition.SMOOTH,
        transition_distance=transition_distance,
        target_objects=target_objects or [],
        installation_name=installation_name,
        priority=100,  # High priority for sweet spots
    )


def get_zone_visualization_data(
    zone: CameraZone,
    resolution: int = 32,
) -> Dict[str, Any]:
    """
    Get visualization data for a zone (for debug/preview).

    Returns points and values for visualizing the zone volume.

    Args:
        zone: Zone to visualize
        resolution: Number of samples per axis

    Returns:
        Dictionary with visualization data
    """
    cx, cy, cz = zone.center

    if zone.zone_type == ZoneType.SPHERE:
        radius = zone.dimensions[0]
        extent = radius + zone.transition_distance

        points = []
        values = []

        for i in range(resolution):
            for j in range(resolution):
                for k in range(resolution):
                    # Map to zone space
                    px = cx - extent + (2 * extent * i / (resolution - 1))
                    py = cy - extent + (2 * extent * j / (resolution - 1))
                    pz = cz - extent + (2 * extent * k / (resolution - 1))

                    factor = zone.contains_point((px, py, pz))

                    if factor > 0:
                        points.append((px, py, pz))
                        values.append(factor)

        return {
            "points": points,
            "values": values,
            "zone_type": zone.zone_type.value,
            "center": zone.center,
            "dimensions": zone.dimensions,
        }

    elif zone.zone_type == ZoneType.BOX:
        hw, hh, hd = zone.dimensions
        margin = zone.transition_distance

        points = []
        values = []

        for i in range(resolution):
            for j in range(resolution):
                for k in range(resolution):
                    px = cx - (hw + margin) + (2 * (hw + margin) * i / (resolution - 1))
                    py = cy - (hh + margin) + (2 * (hh + margin) * j / (resolution - 1))
                    pz = cz - (hd + margin) + (2 * (hd + margin) * k / (resolution - 1))

                    factor = zone.contains_point((px, py, pz))

                    if factor > 0:
                        points.append((px, py, pz))
                        values.append(factor)

        return {
            "points": points,
            "values": values,
            "zone_type": zone.zone_type.value,
            "center": zone.center,
            "dimensions": zone.dimensions,
        }

    return {
        "points": [],
        "values": [],
        "zone_type": zone.zone_type.value,
    }
