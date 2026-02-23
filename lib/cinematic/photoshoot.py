"""
Photoshoot Orchestrator Module

Coordinates complete photoshoot sessions including lighting, camera,
backdrops, and equipment for automated studio photography.

Features:
- Complete photoshoot session management
- Lighting + camera + backdrop coordination
- Shot list generation and execution
- Multi-angle capture automation
- Exposure bracketing

Usage:
    from lib.cinematic.photoshoot import (
        PhotoshootSession,
        PhotoshootConfig,
        ShotConfig,
        create_portrait_session,
        create_product_session,
    )

    # Create a portrait session
    session = create_portrait_session("rembrandt", "gray_backdrop")
    session.add_shot("front_view", camera_angle=(0, 0))
    session.add_shot("three_quarter", camera_angle=(30, 0))
    session.execute()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import math

from .types import CameraConfig, LightConfig, Transform3D
from .light_rigs import create_light_rig, list_light_rig_presets
from .equipment import get_equipment_preset, list_equipment_presets


class PhotoshootType(Enum):
    """Types of photoshoot sessions."""
    PORTRAIT = "portrait"
    PRODUCT = "product"
    FASHION = "fashion"
    FOOD = "food"
    AUTOMOTIVE = "automotive"
    JEWELRY = "jewelry"
    ARCHITECTURAL = "architectural"
    STILL_LIFE = "still_life"


class ShotType(Enum):
    """Types of camera shots."""
    FULL_SHOT = "full_shot"          # Full subject in frame
    THREE_QUARTER = "three_quarter"  # 3/4 view
    CLOSE_UP = "close_up"            # Close detail shot
    DETAIL = "detail"                # Macro/detail
    OVERVIEW = "overview"            # Wide establishing shot
    PROFILE = "profile"              # Side view
    TOP_DOWN = "top_down"            # Overhead view
    LOW_ANGLE = "low_angle"          # Hero angle


class ExposureMode(Enum):
    """Exposure modes for bracketing."""
    SINGLE = "single"                # Single exposure
    BRACKET_3 = "bracket_3"          # 3-shot bracket
    BRACKET_5 = "bracket_5"          # 5-shot bracket
    BRACKET_7 = "bracket_7"          # 7-shot bracket (HDR)


@dataclass
class ShotConfig:
    """Configuration for a single shot."""
    name: str
    shot_type: ShotType = ShotType.FULL_SHOT
    camera_angle: Tuple[float, float] = (0.0, 0.0)  # azimuth, elevation (degrees)
    camera_distance: float = 2.0  # meters
    camera_height: float = 1.2  # meters
    focal_length: float = 85.0  # mm
    f_stop: float = 2.8
    exposure_mode: ExposureMode = ExposureMode.SINGLE
    bracket_steps: float = 1.0  # EV steps for bracketing
    focus_point: Optional[Tuple[float, float, float]] = None
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "shot_type": self.shot_type.value,
            "camera_angle": self.camera_angle,
            "camera_distance": self.camera_distance,
            "camera_height": self.camera_height,
            "focal_length": self.focal_length,
            "f_stop": self.f_stop,
            "exposure_mode": self.exposure_mode.value,
            "bracket_steps": self.bracket_steps,
            "focus_point": self.focus_point,
            "description": self.description,
            "enabled": self.enabled,
        }


@dataclass
class PhotoshootConfig:
    """Complete photoshoot session configuration."""
    name: str
    photoshoot_type: PhotoshootType
    lighting_preset: str = "three_point_soft"
    equipment_preset: Optional[str] = None
    backdrop_type: str = "seamless_gray"
    backdrop_color: str = "#808080"
    subject_position: Tuple[float, float, float] = (0.0, 0.0, 0.5)
    shots: List[ShotConfig] = field(default_factory=list)
    output_format: str = "PNG"
    output_resolution: Tuple[int, int] = (4096, 4096)
    render_engine: str = "cycles"
    samples: int = 128
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_shot(self, shot: ShotConfig) -> None:
        """Add a shot to the session."""
        self.shots.append(shot)

    def get_enabled_shots(self) -> List[ShotConfig]:
        """Get list of enabled shots."""
        return [s for s in self.shots if s.enabled]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "photoshoot_type": self.photoshoot_type.value,
            "lighting_preset": self.lighting_preset,
            "equipment_preset": self.equipment_preset,
            "backdrop_type": self.backdrop_type,
            "backdrop_color": self.backdrop_color,
            "subject_position": self.subject_position,
            "shots": [s.to_dict() for s in self.shots],
            "output_format": self.output_format,
            "output_resolution": self.output_resolution,
            "render_engine": self.render_engine,
            "samples": self.samples,
            "metadata": self.metadata,
        }

    def to_json(self, path: Path) -> None:
        """Save configuration to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhotoshootConfig":
        """Create from dictionary."""
        shots = [ShotConfig(**s) for s in data.get("shots", [])]
        return cls(
            name=data["name"],
            photoshoot_type=PhotoshootType(data["photoshoot_type"]),
            lighting_preset=data.get("lighting_preset", "three_point_soft"),
            equipment_preset=data.get("equipment_preset"),
            backdrop_type=data.get("backdrop_type", "seamless_gray"),
            backdrop_color=data.get("backdrop_color", "#808080"),
            subject_position=tuple(data.get("subject_position", (0.0, 0.0, 0.5))),
            shots=shots,
            output_format=data.get("output_format", "PNG"),
            output_resolution=tuple(data.get("output_resolution", (4096, 4096))),
            render_engine=data.get("render_engine", "cycles"),
            samples=data.get("samples", 128),
            metadata=data.get("metadata", {}),
        )


class PhotoshootSession:
    """
    Orchestrates a complete photoshoot session.

    Manages lighting, camera positions, backdrops, and shot execution
    for automated studio photography.
    """

    def __init__(self, config: PhotoshootConfig):
        """
        Initialize photoshoot session.

        Args:
            config: Session configuration
        """
        self.config = config
        self.lights: List[LightConfig] = []
        self.cameras: List[CameraConfig] = []
        self._setup_lighting()
        self._setup_cameras()

    def _setup_lighting(self) -> None:
        """Set up lighting from preset."""
        try:
            self.lights = create_light_rig(
                self.config.lighting_preset,
                self.config.subject_position,
            )
        except ValueError:
            # Fall back to default if preset not found
            self.lights = create_light_rig(
                "three_point_soft",
                self.config.subject_position,
            )

    def _setup_cameras(self) -> None:
        """Set up cameras for each shot."""
        self.cameras = []
        for shot in self.config.get_enabled_shots():
            camera = self._create_camera_for_shot(shot)
            self.cameras.append(camera)

    def _create_camera_for_shot(self, shot: ShotConfig) -> CameraConfig:
        """Create camera configuration for a shot."""
        # Calculate camera position from angle and distance
        azimuth_rad = math.radians(shot.camera_angle[0])
        elevation_rad = math.radians(shot.camera_angle[1])

        # Subject position as orbit center
        sx, sy, sz = self.config.subject_position

        # Calculate camera position (orbit around subject)
        x = sx + shot.camera_distance * math.sin(azimuth_rad)
        y = sy - shot.camera_distance * math.cos(azimuth_rad)
        z = shot.camera_height + shot.camera_distance * math.sin(elevation_rad)

        # Calculate rotation to point at subject
        dx = sx - x
        dy = sy - y
        dz = sz - z

        horizontal_angle = math.degrees(math.atan2(dx, -dy))
        vertical_angle = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))

        return CameraConfig(
            name=f"camera_{shot.name}",
            focal_length=shot.focal_length,
            f_stop=shot.f_stop,
            sensor_width=36.0,  # Full frame
            transform=Transform3D(
                position=(x, y, z),
                rotation=(vertical_angle + 90, 0, horizontal_angle),
            ),
        )

    def add_shot(
        self,
        name: str,
        shot_type: ShotType = ShotType.FULL_SHOT,
        camera_angle: Tuple[float, float] = (0.0, 0.0),
        **kwargs
    ) -> ShotConfig:
        """
        Add a new shot to the session.

        Args:
            name: Shot name/identifier
            shot_type: Type of shot
            camera_angle: (azimuth, elevation) in degrees
            **kwargs: Additional shot parameters

        Returns:
            Created ShotConfig
        """
        shot = ShotConfig(
            name=name,
            shot_type=shot_type,
            camera_angle=camera_angle,
            **kwargs
        )
        self.config.add_shot(shot)
        self._setup_cameras()
        return shot

    def get_shot_by_name(self, name: str) -> Optional[ShotConfig]:
        """Get shot by name."""
        for shot in self.config.shots:
            if shot.name == name:
                return shot
        return None

    def enable_shot(self, name: str) -> None:
        """Enable a shot by name."""
        shot = self.get_shot_by_name(name)
        if shot:
            shot.enabled = True
            self._setup_cameras()

    def disable_shot(self, name: str) -> None:
        """Disable a shot by name."""
        shot = self.get_shot_by_name(name)
        if shot:
            shot.enabled = False
            self._setup_cameras()

    def set_lighting(self, preset: str) -> None:
        """Change lighting preset."""
        self.config.lighting_preset = preset
        self._setup_lighting()

    def get_light_configs(self) -> List[LightConfig]:
        """Get all light configurations."""
        return self.lights

    def get_camera_configs(self) -> List[CameraConfig]:
        """Get all camera configurations."""
        return self.cameras

    def get_exposure_values(self, shot: ShotConfig) -> List[float]:
        """
        Get exposure values for a shot (for bracketing).

        Args:
            shot: Shot configuration

        Returns:
            List of EV values
        """
        if shot.exposure_mode == ExposureMode.SINGLE:
            return [0.0]
        elif shot.exposure_mode == ExposureMode.BRACKET_3:
            return [-shot.bracket_steps, 0.0, shot.bracket_steps]
        elif shot.exposure_mode == ExposureMode.BRACKET_5:
            step = shot.bracket_steps
            return [-2*step, -step, 0.0, step, 2*step]
        elif shot.exposure_mode == ExposureMode.BRACKET_7:
            step = shot.bracket_steps
            return [-3*step, -2*step, -step, 0.0, step, 2*step, 3*step]
        return [0.0]

    def generate_shot_list(self) -> List[Dict[str, Any]]:
        """
        Generate complete shot list with all parameters.

        Returns:
            List of shot dictionaries with full parameters
        """
        shot_list = []
        for i, shot in enumerate(self.config.get_enabled_shots()):
            camera = self.cameras[i] if i < len(self.cameras) else None
            exposures = self.get_exposure_values(shot)

            shot_data = {
                "shot_index": i,
                "shot_name": shot.name,
                "shot_type": shot.shot_type.value,
                "camera_config": {
                    "position": camera.transform.position if camera else None,
                    "rotation": camera.transform.rotation if camera else None,
                    "focal_length": camera.focal_length if camera else shot.focal_length,
                    "f_stop": camera.f_stop if camera else shot.f_stop,
                },
                "exposures": exposures,
                "description": shot.description,
            }
            shot_list.append(shot_data)

        return shot_list

    def execute(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Execute the photoshoot session.

        In a real implementation, this would render all shots.
        Here we return the configuration for external rendering.

        Args:
            output_dir: Directory for output files

        Returns:
            Dictionary with session results
        """
        shot_list = self.generate_shot_list()

        results = {
            "session_name": self.config.name,
            "session_type": self.config.photoshoot_type.value,
            "total_shots": len(shot_list),
            "shot_list": shot_list,
            "light_configs": [l.__dict__ for l in self.lights],
            "output_settings": {
                "format": self.config.output_format,
                "resolution": self.config.output_resolution,
                "render_engine": self.config.render_engine,
                "samples": self.config.samples,
            },
            "backdrop": {
                "type": self.config.backdrop_type,
                "color": self.config.backdrop_color,
            },
        }

        if output_dir:
            output_path = output_dir / f"{self.config.name}_session.json"
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            results["output_file"] = str(output_path)

        return results


# =============================================================================
# SESSION FACTORY FUNCTIONS
# =============================================================================

def create_portrait_session(
    lighting_preset: str = "portrait_rembrandt",
    backdrop: str = "gray",
    subject_height: float = 1.7
) -> PhotoshootSession:
    """
    Create a portrait photography session.

    Args:
        lighting_preset: Lighting preset name
        backdrop: Backdrop color/type
        subject_height: Subject height for positioning

    Returns:
        Configured PhotoshootSession
    """
    config = PhotoshootConfig(
        name=f"portrait_{lighting_preset}",
        photoshoot_type=PhotoshootType.PORTRAIT,
        lighting_preset=lighting_preset,
        equipment_preset="portrait_studio",
        backdrop_type=f"seamless_{backdrop}",
        backdrop_color=_get_backdrop_color(backdrop),
        subject_position=(0.0, 0.0, subject_height * 0.5),
        shots=[
            ShotConfig("front_view", ShotType.FULL_SHOT, (0, 0), 2.5, subject_height * 0.6),
            ShotConfig("three_quarter_left", ShotType.THREE_QUARTER, (-30, 5), 2.5, subject_height * 0.6),
            ShotConfig("three_quarter_right", ShotType.THREE_QUARTER, (30, 5), 2.5, subject_height * 0.6),
            ShotConfig("profile_left", ShotType.PROFILE, (-90, 0), 2.0, subject_height * 0.6),
            ShotConfig("profile_right", ShotType.PROFILE, (90, 0), 2.0, subject_height * 0.6),
            ShotConfig("close_up", ShotType.CLOSE_UP, (0, 0), 1.2, subject_height * 0.7, focal_length=135),
        ],
    )
    return PhotoshootSession(config)


def create_product_session(
    product_type: str = "electronics",
    backdrop: str = "white"
) -> PhotoshootSession:
    """
    Create a product photography session.

    Args:
        product_type: Type of product (electronics, cosmetics, food, etc.)
        backdrop: Backdrop color/type

    Returns:
        Configured PhotoshootSession
    """
    # Map product type to lighting preset
    lighting_map = {
        "electronics": "product_electronics",
        "cosmetics": "product_cosmetics",
        "food": "product_food",
        "jewelry": "product_jewelry",
        "fashion": "product_fashion",
        "automotive": "product_automotive",
        "furniture": "product_furniture",
        "industrial": "product_industrial",
    }

    lighting_preset = lighting_map.get(product_type, "product_hero")

    config = PhotoshootConfig(
        name=f"product_{product_type}",
        photoshoot_type=PhotoshootType.PRODUCT,
        lighting_preset=lighting_preset,
        equipment_preset="product_table",
        backdrop_type=f"seamless_{backdrop}",
        backdrop_color=_get_backdrop_color(backdrop),
        subject_position=(0.0, 0.0, 0.3),
        shots=[
            ShotConfig("hero_front", ShotType.FULL_SHOT, (0, 15), 1.5, 0.5),
            ShotConfig("hero_angle_left", ShotType.THREE_QUARTER, (-30, 20), 1.5, 0.5),
            ShotConfig("hero_angle_right", ShotType.THREE_QUARTER, (30, 20), 1.5, 0.5),
            ShotConfig("top_down", ShotType.TOP_DOWN, (0, 89), 1.5, 2.0),
            ShotConfig("detail_close", ShotType.DETAIL, (15, 10), 0.5, 0.4, focal_length=100),
            ShotConfig("back_view", ShotType.FULL_SHOT, (180, 15), 1.5, 0.5),
        ],
    )
    return PhotoshootSession(config)


def create_fashion_session(
    style: str = "editorial",
    backdrop: str = "gray"
) -> PhotoshootSession:
    """
    Create a fashion photography session.

    Args:
        style: Style of shoot (editorial, catalog, beauty)
        backdrop: Backdrop color/type

    Returns:
        Configured PhotoshootSession
    """
    lighting_preset = "portrait_dramatic" if style == "editorial" else "portrait_high_key"

    config = PhotoshootConfig(
        name=f"fashion_{style}",
        photoshoot_type=PhotoshootType.FASHION,
        lighting_preset=lighting_preset,
        equipment_preset="beauty_setup",
        backdrop_type=f"seamless_{backdrop}",
        backdrop_color=_get_backdrop_color(backdrop),
        subject_position=(0.0, 0.0, 0.8),
        shots=[
            ShotConfig("full_front", ShotType.FULL_SHOT, (0, 0), 4.0, 1.0),
            ShotConfig("full_angle", ShotType.THREE_QUARTER, (25, 5), 4.0, 1.0),
            ShotConfig("waist_up", ShotType.THREE_QUARTER, (0, 0), 2.5, 1.1),
            ShotConfig("portrait", ShotType.CLOSE_UP, (15, 5), 2.0, 1.2),
            ShotConfig("detail", ShotType.DETAIL, (0, 10), 0.8, 1.0, focal_length=100),
        ],
    )
    return PhotoshootSession(config)


def create_food_session(
    style: str = "overhead",
    backdrop: str = "dark"
) -> PhotoshootSession:
    """
    Create a food photography session.

    Args:
        style: Style of shoot (overhead, angle, hero)
        backdrop: Backdrop color/type

    Returns:
        Configured PhotoshootSession
    """
    config = PhotoshootConfig(
        name=f"food_{style}",
        photoshoot_type=PhotoshootType.FOOD,
        lighting_preset="product_food",
        equipment_preset="food_photography",
        backdrop_type=f"textured_{backdrop}",
        backdrop_color=_get_backdrop_color(backdrop),
        subject_position=(0.0, 0.0, 0.2),
        shots=[
            ShotConfig("overhead", ShotType.TOP_DOWN, (0, 85), 1.2, 1.5),
            ShotConfig("hero_angle", ShotType.THREE_QUARTER, (35, 35), 1.0, 0.5),
            ShotConfig("side_view", ShotType.PROFILE, (90, 15), 1.0, 0.4),
            ShotConfig("close_detail", ShotType.DETAIL, (20, 25), 0.4, 0.3, focal_length=100),
        ],
    )
    return PhotoshootSession(config)


def create_jewelry_session(
    style: str = "hero",
    backdrop: str = "black"
) -> PhotoshootSession:
    """
    Create a jewelry photography session.

    Args:
        style: Style of shoot (hero, catalog, macro)
        backdrop: Backdrop color/type

    Returns:
        Configured PhotoshootSession
    """
    config = PhotoshootConfig(
        name=f"jewelry_{style}",
        photoshoot_type=PhotoshootType.JEWELRY,
        lighting_preset="product_jewelry",
        equipment_preset="jewelry_table",
        backdrop_type=f"velvet_{backdrop}",
        backdrop_color=_get_backdrop_color(backdrop),
        subject_position=(0.0, 0.0, 0.1),
        output_resolution=(6000, 6000),
        shots=[
            ShotConfig("hero_front", ShotType.FULL_SHOT, (0, 20), 0.4, 0.2, focal_length=100),
            ShotConfig("angle_left", ShotType.THREE_QUARTER, (-40, 25), 0.4, 0.2, focal_length=100),
            ShotConfig("angle_right", ShotType.THREE_QUARTER, (40, 25), 0.4, 0.2, focal_length=100),
            ShotConfig("macro_detail", ShotType.DETAIL, (15, 15), 0.15, 0.15, focal_length=150),
        ],
    )
    return PhotoshootSession(config)


def create_automotive_session(
    style: str = "studio",
    backdrop: str = "dark"
) -> PhotoshootSession:
    """
    Create an automotive photography session.

    Args:
        style: Style of shoot (studio, dramatic, catalog)
        backdrop: Backdrop color/type

    Returns:
        Configured PhotoshootSession
    """
    config = PhotoshootConfig(
        name=f"automotive_{style}",
        photoshoot_type=PhotoshootType.AUTOMOTIVE,
        lighting_preset="product_automotive",
        equipment_preset="automotive_studio",
        backdrop_type=f"cyclorama_{backdrop}",
        backdrop_color=_get_backdrop_color(backdrop),
        subject_position=(0.0, 0.0, 0.4),
        output_resolution=(8000, 5333),  # 3:2 ratio for automotive
        shots=[
            ShotConfig("front_three_quarter", ShotType.THREE_QUARTER, (-30, 10), 8.0, 1.2),
            ShotConfig("rear_three_quarter", ShotType.THREE_QUARTER, (150, 10), 8.0, 1.2),
            ShotConfig("side_profile", ShotType.PROFILE, (90, 5), 8.0, 1.0),
            ShotConfig("front_straight", ShotType.FULL_SHOT, (0, 10), 8.0, 1.2),
            ShotConfig("rear_straight", ShotType.FULL_SHOT, (180, 10), 8.0, 1.2),
            ShotConfig("detail_wheel", ShotType.DETAIL, (-60, 15), 2.0, 0.5, focal_length=100),
            ShotConfig("detail_interior", ShotType.DETAIL, (45, 30), 2.0, 1.0, focal_length=85),
        ],
    )
    return PhotoshootSession(config)


def _get_backdrop_color(name: str) -> str:
    """Get hex color for backdrop name."""
    colors = {
        "white": "#FFFFFF",
        "black": "#0A0A0A",
        "gray": "#808080",
        "light_gray": "#C0C0C0",
        "dark_gray": "#404040",
        "blue": "#1E3A5F",
        "red": "#8B0000",
        "green": "#1B4332",
        "brown": "#3E2723",
        "beige": "#F5F5DC",
        "navy": "#0A1628",
        "burgundy": "#722F37",
    }
    return colors.get(name.lower(), colors["gray"])


def list_photoshoot_presets() -> List[str]:
    """List available photoshoot preset types."""
    return [
        "portrait_rembrandt",
        "portrait_butterfly",
        "portrait_loop",
        "portrait_clamshell",
        "portrait_dramatic",
        "product_electronics",
        "product_cosmetics",
        "product_food",
        "product_jewelry",
        "product_fashion",
        "product_automotive",
        "product_furniture",
        "fashion_editorial",
        "fashion_catalog",
        "food_overhead",
        "food_hero",
        "jewelry_hero",
        "jewelry_macro",
        "automotive_studio",
        "automotive_dramatic",
    ]


def create_session_from_preset(preset: str) -> PhotoshootSession:
    """
    Create a photoshoot session from preset name.

    Args:
        preset: Preset name (see list_photoshoot_presets)

    Returns:
        Configured PhotoshootSession
    """
    # Portrait presets
    if preset.startswith("portrait_"):
        lighting = preset.replace("portrait_", "portrait_")
        return create_portrait_session(lighting)

    # Product presets
    if preset.startswith("product_"):
        product_type = preset.replace("product_", "")
        return create_product_session(product_type)

    # Fashion presets
    if preset.startswith("fashion_"):
        style = preset.replace("fashion_", "")
        return create_fashion_session(style)

    # Food presets
    if preset.startswith("food_"):
        style = preset.replace("food_", "")
        return create_food_session(style)

    # Jewelry presets
    if preset.startswith("jewelry_"):
        style = preset.replace("jewelry_", "")
        return create_jewelry_session(style)

    # Automotive presets
    if preset.startswith("automotive_"):
        style = preset.replace("automotive_", "")
        return create_automotive_session(style)

    # Default to portrait
    return create_portrait_session()
