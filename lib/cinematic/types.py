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

    Supports area, spot, point, and sun light types with type-specific properties.

    Area Light Properties:
    - shape: SQUARE, RECTANGLE, DISK, ELLIPSE
    - size: Width/radius
    - size_y: Height (for RECTANGLE/ELLIPSE)
    - spread: Spread angle in radians

    Spot Light Properties:
    - spot_size: Cone angle in radians
    - spot_blend: Edge softness (0-1)

    Color Temperature (Blender 4.0+):
    - use_temperature: Enable Kelvin-based color
    - temperature: Color temperature in Kelvin
    """
    name: str = "key_light"
    light_type: str = "area"  # area, spot, point, sun
    intensity: float = 1000.0  # watts
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    transform: Transform3D = field(default_factory=Transform3D)
    # Area light properties
    shape: str = "RECTANGLE"  # SQUARE, RECTANGLE, DISK, ELLIPSE
    size: float = 1.0  # Width/radius for area lights
    size_y: float = 1.0  # Height for RECTANGLE/ELLIPSE area lights
    spread: float = 1.047  # Spread angle in radians (60 degrees default)
    # Spot light properties
    spot_size: float = 0.785  # Cone angle in radians (45 degrees default)
    spot_blend: float = 0.5  # Edge softness 0-1
    # Shadow properties
    shadow_soft_size: float = 0.1  # Shadow softness radius
    use_shadow: bool = True
    # Color temperature (Blender 4.0+)
    use_temperature: bool = False
    temperature: float = 6500.0  # Kelvin (daylight default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "light_type": self.light_type,
            "intensity": self.intensity,
            "color": list(self.color),
            "transform": self.transform.to_dict(),
            "shape": self.shape,
            "size": self.size,
            "size_y": self.size_y,
            "spread": self.spread,
            "spot_size": self.spot_size,
            "spot_blend": self.spot_blend,
            "shadow_soft_size": self.shadow_soft_size,
            "use_shadow": self.use_shadow,
            "use_temperature": self.use_temperature,
            "temperature": self.temperature,
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
            shape=data.get("shape", "RECTANGLE"),
            size=data.get("size", 1.0),
            size_y=data.get("size_y", 1.0),
            spread=data.get("spread", 1.047),
            spot_size=data.get("spot_size", 0.785),
            spot_blend=data.get("spot_blend", 0.5),
            shadow_soft_size=data.get("shadow_soft_size", 0.1),
            use_shadow=data.get("use_shadow", True),
            use_temperature=data.get("use_temperature", False),
            temperature=data.get("temperature", 6500.0),
        )


@dataclass
class GelConfig:
    """
    Configuration for light gel/color filter.

    Gels are used to modify light color, softness, and character.
    Common types: CTB (Color Temperature Blue), CTO (Color Temperature Orange),
    diffusion, and creative color gels.

    Attributes:
        name: Preset name (e.g., "cto_full", "diffusion_half")
        color: RGB color multiplier (1.0, 1.0, 1.0 = no change)
        temperature_shift: Kelvin temperature shift (-/+) for CTB/CTO
        softness: Diffusion amount (0 = none, 1 = heavy)
        transmission: Light transmission factor (0-1, 1 = full transmission)
        combines: List of gel preset names if this is a combined gel
    """
    name: str = "none"
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    temperature_shift: float = 0.0
    softness: float = 0.0
    transmission: float = 1.0
    combines: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "color": list(self.color),
            "temperature_shift": self.temperature_shift,
            "softness": self.softness,
            "transmission": self.transmission,
            "combines": self.combines,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GelConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", "none"),
            color=tuple(data.get("color", (1.0, 1.0, 1.0))),
            temperature_shift=data.get("temperature_shift", 0.0),
            softness=data.get("softness", 0.0),
            transmission=data.get("transmission", 1.0),
            combines=data.get("combines", []),
        )


@dataclass
class HDRIConfig:
    """
    Configuration for HDRI environment lighting.

    HDRIs provide realistic environment lighting and reflections.
    Common for studio setups and outdoor scenes.

    Attributes:
        name: Preset name (e.g., "studio_bright", "golden_hour")
        file: Path to HDRI file (.hdr, .exr)
        exposure: Exposure adjustment (0 = default, positive = brighter)
        rotation: Rotation angle in radians for HDRI orientation
        background_visible: If True, HDRI is visible in render background
        saturation: Color saturation multiplier (1.0 = normal)
    """
    name: str = "studio_bright"
    file: str = ""
    exposure: float = 0.0
    rotation: float = 0.0
    background_visible: bool = False
    saturation: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "file": self.file,
            "exposure": self.exposure,
            "rotation": self.rotation,
            "background_visible": self.background_visible,
            "saturation": self.saturation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HDRIConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", "studio_bright"),
            file=data.get("file", ""),
            exposure=data.get("exposure", 0.0),
            rotation=data.get("rotation", 0.0),
            background_visible=data.get("background_visible", False),
            saturation=data.get("saturation", 1.0),
        )


@dataclass
class LightRigConfig:
    """
    Configuration for lighting rig preset.

    A light rig defines a complete lighting setup with multiple lights
    and optionally an HDRI environment. Supports preset inheritance.

    Attributes:
        name: Preset name (e.g., "three_point_soft", "product_hero")
        description: Human-readable description
        extends: Parent preset name for inheritance
        lights: Dictionary of light name -> LightConfig dict
        hdri: Optional HDRIConfig dict for environment lighting
    """
    name: str = "three_point_soft"
    description: str = ""
    extends: str = ""
    lights: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hdri: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "extends": self.extends,
            "lights": self.lights,
            "hdri": self.hdri,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LightRigConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", "three_point_soft"),
            description=data.get("description", ""),
            extends=data.get("extends", ""),
            lights=data.get("lights", {}),
            hdri=data.get("hdri"),
        )


@dataclass
class BackdropConfig:
    """
    Backdrop configuration for product rendering.

    Supports infinite curve, gradient, HDRI, and mesh backdrops.

    Attributes:
        backdrop_type: Type of backdrop (infinite_curve, gradient, hdri, mesh)
        color_bottom: Bottom color for gradient backdrops (RGB 0-1)
        color_top: Top color for gradient backdrops (RGB 0-1)
        radius: Radius/size of the backdrop
        shadow_catcher: Whether backdrop acts as shadow catcher
        curve_height: Height of vertical wall for infinite curves (meters)
        curve_segments: Resolution of curve geometry
        gradient_type: Gradient type (linear, radial, angular)
        gradient_stops: List of gradient color stops with position and color
        hdri_preset: Name of HDRI preset for HDRI backdrops
        mesh_file: Path to mesh file for mesh backdrops
        mesh_scale: Scale factor for mesh environments
    """
    backdrop_type: str = "infinite_curve"  # infinite_curve, gradient, hdri, mesh
    color_bottom: Tuple[float, float, float] = (0.95, 0.95, 0.95)
    color_top: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    radius: float = 5.0
    shadow_catcher: bool = True
    # Infinite curve properties
    curve_height: float = 3.0  # Height of vertical wall for infinite curves
    curve_segments: int = 32   # Resolution of curve
    # Gradient properties
    gradient_type: str = "linear"  # linear, radial, angular for gradient backdrops
    gradient_stops: List[Dict] = field(default_factory=list)  # Gradient color stops
    # HDRI properties
    hdri_preset: str = ""     # Name of HDRI preset for HDRI backdrops
    # Mesh properties
    mesh_file: str = ""       # Path to mesh file for mesh backdrops
    mesh_scale: float = 1.0   # Scale for mesh environments

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "backdrop_type": self.backdrop_type,
            "color_bottom": list(self.color_bottom),
            "color_top": list(self.color_top),
            "radius": self.radius,
            "shadow_catcher": self.shadow_catcher,
            "curve_height": self.curve_height,
            "curve_segments": self.curve_segments,
            "gradient_type": self.gradient_type,
            "gradient_stops": self.gradient_stops,
            "hdri_preset": self.hdri_preset,
            "mesh_file": self.mesh_file,
            "mesh_scale": self.mesh_scale,
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
            curve_height=data.get("curve_height", 3.0),
            curve_segments=data.get("curve_segments", 32),
            gradient_type=data.get("gradient_type", "linear"),
            gradient_stops=data.get("gradient_stops", []),
            hdri_preset=data.get("hdri_preset", ""),
            mesh_file=data.get("mesh_file", ""),
            mesh_scale=data.get("mesh_scale", 1.0),
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


@dataclass
class PlumbBobConfig:
    """
    Configuration for plumb bob targeting system.

    The plumb bob defines the visual center of interest for camera orbit,
    focus, and dolly operations.

    Modes:
    - auto: Calculate from subject bounding box + offset
    - manual: Use explicit world coordinates
    - object: Use another object's location + offset

    Focus Modes:
    - auto: Focus distance calculated from camera to target
    - manual: Use explicit focus_distance value
    """
    mode: str = "auto"  # auto, manual, object
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # World space offset
    manual_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # For manual mode
    target_object: str = ""  # For object mode
    focus_mode: str = "auto"  # auto, manual
    focus_distance: float = 0.0  # Manual focus distance in meters (used when focus_mode="manual")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "offset": list(self.offset),
            "manual_position": list(self.manual_position),
            "target_object": self.target_object,
            "focus_mode": self.focus_mode,
            "focus_distance": self.focus_distance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PlumbBobConfig:
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "auto"),
            offset=tuple(data.get("offset", (0.0, 0.0, 0.0))),
            manual_position=tuple(data.get("manual_position", (0.0, 0.0, 0.0))),
            target_object=data.get("target_object", ""),
            focus_mode=data.get("focus_mode", "auto"),
            focus_distance=data.get("focus_distance", 0.0),
        )


@dataclass
class RigConfig:
    """
    Configuration for camera rig systems.

    Supports various rig types with motion constraints and smoothing.
    All rotations in Euler degrees (XYZ order).
    """
    rig_type: str = "tripod"  # tripod, tripod_orbit, dolly, dolly_curved, crane, steadicam, drone
    constraints: Dict[str, Any] = field(default_factory=dict)  # Motion constraints
    smoothing: Dict[str, float] = field(default_factory=dict)  # Smoothing params for steadicam
    track_config: Dict[str, Any] = field(default_factory=dict)  # Track config for dolly

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rig_type": self.rig_type,
            "constraints": self.constraints,
            "smoothing": self.smoothing,
            "track_config": self.track_config,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RigConfig:
        """Create from dictionary."""
        return cls(
            rig_type=data.get("rig_type", "tripod"),
            constraints=data.get("constraints", {}),
            smoothing=data.get("smoothing", {}),
            track_config=data.get("track_config", {}),
        )


@dataclass
class ImperfectionConfig:
    """
    Configuration for lens imperfections.

    Simulates real-world lens characteristics like flare, vignette,
    chromatic aberration, and bokeh shape.
    """
    name: str = "clean"  # Preset name
    flare_enabled: bool = False
    flare_intensity: float = 0.0  # 0.0 to 1.0
    flare_streaks: int = 8
    vignette: float = 0.0  # 0.0 to 1.0
    chromatic_aberration: float = 0.0  # Amount of CA
    bokeh_shape: str = "circular"  # circular, hexagonal, octagonal, rounded
    bokeh_swirl: float = 0.0  # For vintage lenses

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "flare_enabled": self.flare_enabled,
            "flare_intensity": self.flare_intensity,
            "flare_streaks": self.flare_streaks,
            "vignette": self.vignette,
            "chromatic_aberration": self.chromatic_aberration,
            "bokeh_shape": self.bokeh_shape,
            "bokeh_swirl": self.bokeh_swirl,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImperfectionConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", "clean"),
            flare_enabled=data.get("flare_enabled", False),
            flare_intensity=data.get("flare_intensity", 0.0),
            flare_streaks=data.get("flare_streaks", 8),
            vignette=data.get("vignette", 0.0),
            chromatic_aberration=data.get("chromatic_aberration", 0.0),
            bokeh_shape=data.get("bokeh_shape", "circular"),
            bokeh_swirl=data.get("bokeh_swirl", 0.0),
        )


@dataclass
class MultiCameraLayout:
    """
    Configuration for multi-camera setups.

    Supports various layout types for multi-camera compositing.
    Composite output creates a grid layout in a single rendered image.
    """
    layout_type: str = "grid"  # grid, horizontal, vertical, circle, arc, custom
    spacing: float = 2.0  # Distance between cameras
    cameras: List[str] = field(default_factory=list)  # Camera names
    positions: List[Tuple[float, float, float]] = field(default_factory=list)  # For custom layout
    composite_output: bool = True  # Enable compositor-based composite output (grid layout to single image)
    composite_rows: int = 0  # Number of rows in composite (0 = auto-calculate)
    composite_cols: int = 0  # Number of columns in composite (0 = auto-calculate)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "layout_type": self.layout_type,
            "spacing": self.spacing,
            "cameras": self.cameras,
            "positions": [list(p) for p in self.positions],
            "composite_output": self.composite_output,
            "composite_rows": self.composite_rows,
            "composite_cols": self.composite_cols,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MultiCameraLayout:
        """Create from dictionary."""
        positions_data = data.get("positions", [])
        positions = [tuple(p) for p in positions_data] if positions_data else []
        return cls(
            layout_type=data.get("layout_type", "grid"),
            spacing=data.get("spacing", 2.0),
            cameras=data.get("cameras", []),
            positions=positions,
            composite_output=data.get("composite_output", True),
            composite_rows=data.get("composite_rows", 0),
            composite_cols=data.get("composite_cols", 0),
        )


@dataclass
class ColorConfig:
    """
    Color management configuration for cinematic rendering.

    Controls view transform, exposure, gamma, and look settings
    for Blender's color management system.

    Attributes:
        view_transform: Blender view transform (Standard, AgX, Filmic, Filmic Log, Raw, Log, ACEScg)
        exposure: Global exposure adjustment (-inf to +inf)
        gamma: Gamma correction (0 to 5)
        look: Color look preset (e.g., "AgX Default Medium High Contrast")
        display_device: Output display device (sRGB, DCI-P3, etc.)
        working_color_space: Scene linear color space (AgX, ACEScg, Filmic, Standard)
    """
    view_transform: str = "AgX"
    exposure: float = 0.0
    gamma: float = 1.0
    look: str = "None"
    display_device: str = "sRGB"
    working_color_space: str = "AgX"  # Scene linear color space

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "view_transform": self.view_transform,
            "exposure": self.exposure,
            "gamma": self.gamma,
            "look": self.look,
            "display_device": self.display_device,
            "working_color_space": self.working_color_space,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorConfig":
        """Create from dictionary."""
        return cls(
            view_transform=data.get("view_transform", "AgX"),
            exposure=data.get("exposure", 0.0),
            gamma=data.get("gamma", 1.0),
            look=data.get("look", "None"),
            display_device=data.get("display_device", "sRGB"),
            working_color_space=data.get("working_color_space", "AgX"),
        )


@dataclass
class LUTConfig:
    """
    LUT configuration with intensity blending support.

    Supports technical, film, and creative LUTs for color grading.

    Attributes:
        name: Preset name (e.g., "kodak_2383", "fuji_400h")
        lut_path: Path to .cube file
        intensity: Blend intensity 0.0-1.0 (default 0.8 per REQ-CINE-LUT)
        enabled: Whether LUT is active
        lut_type: LUT category (technical, film, creative)
        precision: LUT resolution (33 for film, 65 for technical)
    """
    name: str = ""
    lut_path: str = ""
    intensity: float = 0.8  # Default per REQ-CINE-LUT
    enabled: bool = True
    lut_type: str = "creative"  # technical, film, creative
    precision: int = 33  # 33 for film, 65 for technical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "lut_path": self.lut_path,
            "intensity": self.intensity,
            "enabled": self.enabled,
            "lut_type": self.lut_type,
            "precision": self.precision,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LUTConfig":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            lut_path=data.get("lut_path", ""),
            intensity=data.get("intensity", 0.8),
            enabled=data.get("enabled", True),
            lut_type=data.get("lut_type", "creative"),
            precision=data.get("precision", 33),
        )


@dataclass
class ExposureLockConfig:
    """
    Auto-exposure lock configuration per REQ-CINE-LUT.

    Provides automatic exposure targeting based on scene luminance
    with highlight and shadow protection.

    Attributes:
        enabled: Whether auto-exposure lock is active
        target_gray: Target middle gray value (0.18 = 18% gray)
        highlight_protection: Maximum highlight value to protect (0-1)
        shadow_protection: Minimum shadow value to protect (0-1)
    """
    enabled: bool = False
    target_gray: float = 0.18  # 18% gray
    highlight_protection: float = 0.95
    shadow_protection: float = 0.02

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "target_gray": self.target_gray,
            "highlight_protection": self.highlight_protection,
            "shadow_protection": self.shadow_protection,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExposureLockConfig":
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            target_gray=data.get("target_gray", 0.18),
            highlight_protection=data.get("highlight_protection", 0.95),
            shadow_protection=data.get("shadow_protection", 0.02),
        )
