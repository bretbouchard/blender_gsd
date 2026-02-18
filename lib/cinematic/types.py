"""
Core Data Types for Cinematic System

Defines dataclasses for camera configuration, lighting, backdrops,
render settings, and shot state persistence.

All classes designed for YAML serialization via to_yaml_dict() and
deserialization via from_yaml_dict() class methods.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple, List


@dataclass
class Transform3D:
    """
    3D transform with position, rotation, and scale.

    All rotations in Euler degrees (XYZ order).
    """
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Euler degrees
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    def to_blender(self) -> Dict[str, Any]:
        """Convert to Blender-compatible format."""
        return {
            "location": list(self.position),
            "rotation_euler": [r * 0.017453292519943295 for r in self.rotation],  # deg to rad
            "scale": list(self.scale),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": list(self.scale),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Transform3D:
        """Create from dictionary."""
        return cls(
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            rotation=tuple(data.get("rotation", (0.0, 0.0, 0.0))),
            scale=tuple(data.get("scale", (1.0, 1.0, 1.0))),
        )


@dataclass
class CameraConfig:
    """
    Complete camera configuration.

    Includes physical camera parameters and transform.
    All dimensions in meters or mm as appropriate.
    """
    name: str = "hero_camera"
    focal_length: float = 50.0  # mm
    focus_distance: float = 1.0  # meters (0 = auto)
    sensor_width: float = 36.0  # mm
    sensor_height: float = 24.0  # mm
    f_stop: float = 4.0
    aperture_blades: int = 9
    transform: Transform3D = field(default_factory=Transform3D)

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary for rendering."""
        return {
            "name": self.name,
            "focal_length": self.focal_length,
            "focus_distance": self.focus_distance,
            "sensor_width": self.sensor_width,
            "sensor_height": self.sensor_height,
            "f_stop": self.f_stop,
            "aperture_blades": self.aperture_blades,
            "transform": self.transform.to_blender(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "focal_length": self.focal_length,
            "focus_distance": self.focus_distance,
            "sensor_width": self.sensor_width,
            "sensor_height": self.sensor_height,
            "f_stop": self.f_stop,
            "aperture_blades": self.aperture_blades,
            "transform": self.transform.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CameraConfig:
        """Create from dictionary."""
        transform_data = data.get("transform", {})
        return cls(
            name=data.get("name", "hero_camera"),
            focal_length=data.get("focal_length", 50.0),
            focus_distance=data.get("focus_distance", 1.0),
            sensor_width=data.get("sensor_width", 36.0),
            sensor_height=data.get("sensor_height", 24.0),
            f_stop=data.get("f_stop", 4.0),
            aperture_blades=data.get("aperture_blades", 9),
            transform=Transform3D.from_dict(transform_data),
        )


@dataclass
class LightConfig:
    """
    Light configuration for cinematic lighting.

    Supports area, spot, point, and sun light types.
    """
    name: str = "key_light"
    light_type: str = "area"  # area, spot, point, sun
    intensity: float = 1000.0  # watts
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    transform: Transform3D = field(default_factory=Transform3D)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "light_type": self.light_type,
            "intensity": self.intensity,
            "color": list(self.color),
            "transform": self.transform.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LightConfig:
        """Create from dictionary."""
        transform_data = data.get("transform", {})
        return cls(
            name=data.get("name", "key_light"),
            light_type=data.get("light_type", "area"),
            intensity=data.get("intensity", 1000.0),
            color=tuple(data.get("color", (1.0, 1.0, 1.0))),
            transform=Transform3D.from_dict(transform_data),
        )


@dataclass
class BackdropConfig:
    """
    Backdrop configuration for product rendering.

    Supports infinite curve, gradient, HDRI, and mesh backdrops.
    """
    backdrop_type: str = "infinite_curve"  # infinite_curve, gradient, hdri, mesh
    color_bottom: Tuple[float, float, float] = (0.95, 0.95, 0.95)
    color_top: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    radius: float = 5.0
    shadow_catcher: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "backdrop_type": self.backdrop_type,
            "color_bottom": list(self.color_bottom),
            "color_top": list(self.color_top),
            "radius": self.radius,
            "shadow_catcher": self.shadow_catcher,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BackdropConfig:
        """Create from dictionary."""
        return cls(
            backdrop_type=data.get("backdrop_type", "infinite_curve"),
            color_bottom=tuple(data.get("color_bottom", (0.95, 0.95, 0.95))),
            color_top=tuple(data.get("color_top", (1.0, 1.0, 1.0))),
            radius=data.get("radius", 5.0),
            shadow_catcher=data.get("shadow_catcher", True),
        )


@dataclass
class RenderSettings:
    """
    Render configuration for quality control.

    Supports Cycles, EEVEE Next, and Workbench engines.
    """
    engine: str = "CYCLES"  # CYCLES, BLENDER_EEVEE_NEXT, BLENDER_WORKBENCH
    resolution_x: int = 2048
    resolution_y: int = 2048
    samples: int = 64
    quality_tier: str = "cycles_preview"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "engine": self.engine,
            "resolution_x": self.resolution_x,
            "resolution_y": self.resolution_y,
            "samples": self.samples,
            "quality_tier": self.quality_tier,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RenderSettings:
        """Create from dictionary."""
        return cls(
            engine=data.get("engine", "CYCLES"),
            resolution_x=data.get("resolution_x", 2048),
            resolution_y=data.get("resolution_y", 2048),
            samples=data.get("samples", 64),
            quality_tier=data.get("quality_tier", "cycles_preview"),
        )


@dataclass
class ShotState:
    """
    Complete shot state for persistence.

    This is the key class for saving and loading shot configurations.
    Includes camera, lights, backdrop, and render settings.

    Usage:
        state = ShotState(shot_name="hero_knob_01")
        state.camera.focal_length = 85.0

        # Save to YAML
        manager = StateManager()
        manager.save(state, Path("shots/hero_knob_01.yaml"))

        # Load from YAML
        loaded = manager.load(Path("shots/hero_knob_01.yaml"))
    """
    shot_name: str
    version: int = 1
    timestamp: str = ""
    camera: CameraConfig = field(default_factory=CameraConfig)
    lights: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    backdrop: Dict[str, Any] = field(default_factory=dict)
    render_settings: Dict[str, Any] = field(default_factory=dict)

    def to_yaml_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for YAML serialization.

        Returns a clean dictionary suitable for yaml.dump().
        """
        return {
            "shot_name": self.shot_name,
            "version": self.version,
            "timestamp": self.timestamp,
            "camera": self.camera.to_dict(),
            "lights": self.lights,
            "backdrop": self.backdrop,
            "render_settings": self.render_settings,
        }

    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> ShotState:
        """
        Create ShotState from YAML dictionary.

        Reconstructs nested dataclasses from dictionary data.
        """
        camera_data = data.get("camera", {})
        return cls(
            shot_name=data.get("shot_name", "unnamed_shot"),
            version=data.get("version", 1),
            timestamp=data.get("timestamp", ""),
            camera=CameraConfig.from_dict(camera_data),
            lights=data.get("lights", {}),
            backdrop=data.get("backdrop", {}),
            render_settings=data.get("render_settings", {}),
        )
