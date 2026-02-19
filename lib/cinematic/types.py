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


@dataclass
class AnimationConfig:
    """
    Camera animation configuration.

    Supports various camera move types for cinematic animation.

    Attributes:
        enabled: Whether animation is active
        type: Animation type (static, orbit, dolly, crane, push_in, turntable, pan, tilt, truck, rack_focus, custom)
        duration: Animation duration in frames
        start_frame: Starting frame number
        easing: Easing function name (linear, ease_in, ease_out, ease_in_out, etc.)
        loop: Whether animation loops
        angle_range: Start and end angle for orbit/turntable (degrees)
        radius: Orbit radius in meters
        distance: Dolly/crane travel distance in meters
        direction: Movement direction (forward, backward, clockwise, counterclockwise)
        elevation_range: Vertical angle range for crane shots (degrees)
        subject_rotation: Whether subject rotates with camera (for turntable effect)
        from_value: Starting value for parameter-based animations
        to_value: Ending value for parameter-based animations
    """
    enabled: bool = False
    type: str = "static"  # static, orbit, dolly, crane, push_in, turntable, pan, tilt, truck, rack_focus, custom
    duration: int = 120
    start_frame: int = 1
    easing: str = "linear"
    loop: bool = False
    angle_range: Tuple[float, float] = (0.0, 360.0)
    radius: float = 1.0
    distance: float = 0.5
    direction: str = "forward"
    elevation_range: Tuple[float, float] = (0.0, 45.0)
    subject_rotation: bool = False
    from_value: float = 0.0
    to_value: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "type": self.type,
            "duration": self.duration,
            "start_frame": self.start_frame,
            "easing": self.easing,
            "loop": self.loop,
            "angle_range": list(self.angle_range),
            "radius": self.radius,
            "distance": self.distance,
            "direction": self.direction,
            "elevation_range": list(self.elevation_range),
            "subject_rotation": self.subject_rotation,
            "from_value": self.from_value,
            "to_value": self.to_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationConfig":
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            type=data.get("type", "static"),
            duration=data.get("duration", 120),
            start_frame=data.get("start_frame", 1),
            easing=data.get("easing", "linear"),
            loop=data.get("loop", False),
            angle_range=tuple(data.get("angle_range", (0.0, 360.0))),
            radius=data.get("radius", 1.0),
            distance=data.get("distance", 0.5),
            direction=data.get("direction", "forward"),
            elevation_range=tuple(data.get("elevation_range", (0.0, 45.0))),
            subject_rotation=data.get("subject_rotation", False),
            from_value=data.get("from_value", 0.0),
            to_value=data.get("to_value", 1.0),
        )


@dataclass
class MotionPathConfig:
    """
    Motion path configuration for procedural camera moves.

    Supports various path types for complex camera animations.

    Attributes:
        path_type: Path interpolation type (linear, spline, bezier, arc)
        duration: Path duration in frames
        look_at: Look-at target mode (plumb_bob, manual, object, forward)
        interpolation: Interpolation method for path evaluation
        points: List of control points with position and handle data
        preset: Named preset for common paths
        closed: Whether path is closed (loops back to start)
    """
    path_type: str = "linear"  # linear, spline, bezier, arc
    duration: int = 120
    look_at: str = "plumb_bob"  # plumb_bob, manual, object, forward
    interpolation: str = "bezier"
    points: List[Dict[str, Any]] = field(default_factory=list)
    preset: str = ""
    closed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path_type": self.path_type,
            "duration": self.duration,
            "look_at": self.look_at,
            "interpolation": self.interpolation,
            "points": self.points,
            "preset": self.preset,
            "closed": self.closed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MotionPathConfig":
        """Create from dictionary."""
        return cls(
            path_type=data.get("path_type", "linear"),
            duration=data.get("duration", 120),
            look_at=data.get("look_at", "plumb_bob"),
            interpolation=data.get("interpolation", "bezier"),
            points=data.get("points", []),
            preset=data.get("preset", ""),
            closed=data.get("closed", False),
        )


@dataclass
class TurntableConfig:
    """
    Turntable rotation configuration for product showcase.

    Provides smooth, looping rotation ideal for product videos.

    Attributes:
        enabled: Whether turntable rotation is active
        axis: Rotation axis (X, Y, Z)
        angle_range: Start and end angle in degrees
        duration: Rotation duration in frames (one full rotation)
        start_frame: Starting frame number
        easing: Easing function for smooth acceleration/deceleration
        loop: Whether rotation loops continuously
        direction: Rotation direction (clockwise, counterclockwise)
        rotation_speed: Speed multiplier (1.0 = normal speed)
    """
    enabled: bool = False
    axis: str = "Z"
    angle_range: Tuple[float, float] = (0.0, 360.0)
    duration: int = 120
    start_frame: int = 1
    easing: str = "linear"
    loop: bool = True
    direction: str = "clockwise"
    rotation_speed: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "axis": self.axis,
            "angle_range": list(self.angle_range),
            "duration": self.duration,
            "start_frame": self.start_frame,
            "easing": self.easing,
            "loop": self.loop,
            "direction": self.direction,
            "rotation_speed": self.rotation_speed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TurntableConfig":
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            axis=data.get("axis", "Z"),
            angle_range=tuple(data.get("angle_range", (0.0, 360.0))),
            duration=data.get("duration", 120),
            start_frame=data.get("start_frame", 1),
            easing=data.get("easing", "linear"),
            loop=data.get("loop", True),
            direction=data.get("direction", "clockwise"),
            rotation_speed=data.get("rotation_speed", 1.0),
        )


@dataclass
class CinematicRenderSettings:
    """
    Cinematic render configuration for quality tiers and passes.

    Attributes:
        quality_tier: Quality preset (viewport, draft, preview, production, archive)
        engine: Render engine (BLENDER_EEVEE_NEXT, CYCLES)
        resolution_x: Render width in pixels
        resolution_y: Render height in pixels
        resolution_percentage: Resolution scale (100 = full)
        frame_start: Start frame
        frame_end: End frame
        fps: Frames per second
        samples: Render samples (EEVEE/Cycles)
        use_denoising: Enable denoising
        denoiser_type: Denoiser (OPTIX, OPENIMAGEDENOISE, etc.)
        use_motion_blur: Enable motion blur
        motion_blur_shutter: Shutter speed for motion blur
        use_pass_z: Enable depth pass
        use_pass_cryptomatte: Enable cryptomatte pass
        use_pass_normal: Enable normal pass
        use_pass_combined: Enable combined pass
        output_format: Output format (OPEN_EXR_MULTILAYER, PNG, etc.)
        output_path: Output directory path
        exr_codec: EXR compression codec
    """
    quality_tier: str = "preview"
    engine: str = "BLENDER_EEVEE_NEXT"
    resolution_x: int = 1920
    resolution_y: int = 1080
    resolution_percentage: int = 100
    frame_start: int = 1
    frame_end: int = 120
    fps: float = 24.0
    samples: int = 64
    use_denoising: bool = True
    denoiser_type: str = "OPENIMAGEDENOISE"
    use_motion_blur: bool = False
    motion_blur_shutter: float = 0.5
    use_pass_z: bool = True
    use_pass_cryptomatte: bool = False
    use_pass_normal: bool = False
    use_pass_combined: bool = True
    output_format: str = "PNG"
    output_path: str = "//render/"
    exr_codec: str = "ZIP"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_tier": self.quality_tier, "engine": self.engine,
            "resolution_x": self.resolution_x, "resolution_y": self.resolution_y,
            "resolution_percentage": self.resolution_percentage,
            "frame_start": self.frame_start, "frame_end": self.frame_end,
            "fps": self.fps, "samples": self.samples,
            "use_denoising": self.use_denoising, "denoiser_type": self.denoiser_type,
            "use_motion_blur": self.use_motion_blur, "motion_blur_shutter": self.motion_blur_shutter,
            "use_pass_z": self.use_pass_z, "use_pass_cryptomatte": self.use_pass_cryptomatte,
            "use_pass_normal": self.use_pass_normal, "use_pass_combined": self.use_pass_combined,
            "output_format": self.output_format, "output_path": self.output_path,
            "exr_codec": self.exr_codec,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CinematicRenderSettings":
        return cls(
            quality_tier=data.get("quality_tier", "preview"),
            engine=data.get("engine", "BLENDER_EEVEE_NEXT"),
            resolution_x=data.get("resolution_x", 1920),
            resolution_y=data.get("resolution_y", 1080),
            resolution_percentage=data.get("resolution_percentage", 100),
            frame_start=data.get("frame_start", 1),
            frame_end=data.get("frame_end", 120),
            fps=data.get("fps", 24.0),
            samples=data.get("samples", 64),
            use_denoising=data.get("use_denoising", True),
            denoiser_type=data.get("denoiser_type", "OPENIMAGEDENOISE"),
            use_motion_blur=data.get("use_motion_blur", False),
            motion_blur_shutter=data.get("motion_blur_shutter", 0.5),
            use_pass_z=data.get("use_pass_z", True),
            use_pass_cryptomatte=data.get("use_pass_cryptomatte", False),
            use_pass_normal=data.get("use_pass_normal", False),
            use_pass_combined=data.get("use_pass_combined", True),
            output_format=data.get("output_format", "PNG"),
            output_path=data.get("output_path", "//render/"),
            exr_codec=data.get("exr_codec", "ZIP"),
        )


@dataclass
class ShuffleConfig:
    """Shot variation configuration for generating multiple takes."""
    enabled: bool = False
    camera_angle_range: Tuple[float, float] = (-15.0, 15.0)  # degrees
    camera_height_range: Tuple[float, float] = (-0.2, 0.2)  # meters
    focal_length_range: Tuple[float, float] = (45.0, 85.0)  # mm
    light_intensity_range: Tuple[float, float] = (0.8, 1.2)  # multiplier
    light_angle_range: Tuple[float, float] = (-30.0, 30.0)  # degrees
    exposure_range: Tuple[float, float] = (-0.5, 0.5)  # stops
    num_variations: int = 5
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "camera_angle_range": list(self.camera_angle_range),
            "camera_height_range": list(self.camera_height_range),
            "focal_length_range": list(self.focal_length_range),
            "light_intensity_range": list(self.light_intensity_range),
            "light_angle_range": list(self.light_angle_range),
            "exposure_range": list(self.exposure_range),
            "num_variations": self.num_variations,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShuffleConfig":
        return cls(
            enabled=data.get("enabled", False),
            camera_angle_range=tuple(data.get("camera_angle_range", (-15.0, 15.0))),
            camera_height_range=tuple(data.get("camera_height_range", (-0.2, 0.2))),
            focal_length_range=tuple(data.get("focal_length_range", (45.0, 85.0))),
            light_intensity_range=tuple(data.get("light_intensity_range", (0.8, 1.2))),
            light_angle_range=tuple(data.get("light_angle_range", (-30.0, 30.0))),
            exposure_range=tuple(data.get("exposure_range", (-0.5, 0.5))),
            num_variations=data.get("num_variations", 5),
            seed=data.get("seed", None),
        )


@dataclass
class FrameState:
    """Captured scene state for comparison and undo."""
    frame_number: int = 1
    camera_transform: Dict[str, Any] = field(default_factory=dict)
    camera_settings: Dict[str, Any] = field(default_factory=dict)
    light_states: List[Dict[str, Any]] = field(default_factory=list)
    object_transforms: List[Dict[str, Any]] = field(default_factory=list)
    render_settings: Dict[str, Any] = field(default_factory=dict)
    color_settings: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_number": self.frame_number,
            "camera_transform": self.camera_transform,
            "camera_settings": self.camera_settings,
            "light_states": self.light_states,
            "object_transforms": self.object_transforms,
            "render_settings": self.render_settings,
            "color_settings": self.color_settings,
            "timestamp": self.timestamp,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FrameState":
        return cls(
            frame_number=data.get("frame_number", 1),
            camera_transform=data.get("camera_transform", {}),
            camera_settings=data.get("camera_settings", {}),
            light_states=data.get("light_states", []),
            object_transforms=data.get("object_transforms", []),
            render_settings=data.get("render_settings", {}),
            color_settings=data.get("color_settings", {}),
            timestamp=data.get("timestamp", ""),
            label=data.get("label", ""),
        )


@dataclass
class DepthLayerConfig:
    """Depth layer organization for DOF and compositing."""
    enabled: bool = False
    foreground_objects: List[str] = field(default_factory=list)
    midground_objects: List[str] = field(default_factory=list)
    background_objects: List[str] = field(default_factory=list)
    foreground_dof: float = 0.0
    midground_dof: float = 0.0
    background_dof: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "foreground_objects": self.foreground_objects,
            "midground_objects": self.midground_objects,
            "background_objects": self.background_objects,
            "foreground_dof": self.foreground_dof,
            "midground_dof": self.midground_dof,
            "background_dof": self.background_dof,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DepthLayerConfig":
        return cls(
            enabled=data.get("enabled", False),
            foreground_objects=data.get("foreground_objects", []),
            midground_objects=data.get("midground_objects", []),
            background_objects=data.get("background_objects", []),
            foreground_dof=data.get("foreground_dof", 0.0),
            midground_dof=data.get("midground_dof", 0.0),
            background_dof=data.get("background_dof", 0.1),
        )


@dataclass
class CompositionGuide:
    """Composition guide overlay configuration."""
    enabled: bool = False
    rule_of_thirds: bool = True
    golden_ratio: bool = False
    center_cross: bool = False
    diagonal: bool = False
    guide_opacity: float = 0.5
    guide_color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.5)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "rule_of_thirds": self.rule_of_thirds,
            "golden_ratio": self.golden_ratio,
            "center_cross": self.center_cross,
            "diagonal": self.diagonal,
            "guide_opacity": self.guide_opacity,
            "guide_color": list(self.guide_color),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositionGuide":
        return cls(
            enabled=data.get("enabled", False),
            rule_of_thirds=data.get("rule_of_thirds", True),
            golden_ratio=data.get("golden_ratio", False),
            center_cross=data.get("center_cross", False),
            diagonal=data.get("diagonal", False),
            guide_opacity=data.get("guide_opacity", 0.5),
            guide_color=tuple(data.get("guide_color", (1.0, 0.0, 0.0, 0.5))),
        )


@dataclass
class LensFXConfig:
    """Post-process lens effects configuration."""
    enabled: bool = False
    bloom_intensity: float = 0.0
    bloom_threshold: float = 0.8
    flare_intensity: float = 0.0
    flare_ghost_count: int = 4
    vignette_intensity: float = 0.0
    vignette_radius: float = 0.8
    chromatic_aberration: float = 0.0
    film_grain: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "bloom_intensity": self.bloom_intensity,
            "bloom_threshold": self.bloom_threshold,
            "flare_intensity": self.flare_intensity,
            "flare_ghost_count": self.flare_ghost_count,
            "vignette_intensity": self.vignette_intensity,
            "vignette_radius": self.vignette_radius,
            "chromatic_aberration": self.chromatic_aberration,
            "film_grain": self.film_grain,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LensFXConfig":
        return cls(
            enabled=data.get("enabled", False),
            bloom_intensity=data.get("bloom_intensity", 0.0),
            bloom_threshold=data.get("bloom_threshold", 0.8),
            flare_intensity=data.get("flare_intensity", 0.0),
            flare_ghost_count=data.get("flare_ghost_count", 4),
            vignette_intensity=data.get("vignette_intensity", 0.0),
            vignette_radius=data.get("vignette_radius", 0.8),
            chromatic_aberration=data.get("chromatic_aberration", 0.0),
            film_grain=data.get("film_grain", 0.0),
        )


# =============================================================================
# COMPOSITION RULES - Professional cinematography constants
# =============================================================================

# Shot sizes (how much of subject is in frame)
SHOT_SIZES = {
    "ecu": {"name": "Extreme Close-Up", "heads_visible": 1.0, "description": "Eyes, lips, extreme detail"},
    "cu": {"name": "Close-Up", "heads_visible": 1.5, "description": "Face fills frame"},
    "mcu": {"name": "Medium Close-Up", "heads_visible": 2.5, "description": "Chest up"},
    "m": {"name": "Medium", "heads_visible": 3.5, "description": "Waist up"},
    "mf": {"name": "Medium Full", "heads_visible": 5.0, "description": "Knees up"},
    "f": {"name": "Full", "heads_visible": 7.0, "description": "Full body"},
    "w": {"name": "Wide", "heads_visible": 10.0, "description": "Subject in environment"},
    "ew": {"name": "Extreme Wide", "heads_visible": 20.0, "description": "Establishing shot"},
}

# Lens recommendations by shot size
LENS_BY_SHOT_SIZE = {
    "ecu": {"focal_length": 100, "preset": "90mm_macro", "description": "Macro or long lens for detail"},
    "cu": {"focal_length": 85, "preset": "85mm_portrait", "description": "Portrait lens, flattering compression"},
    "mcu": {"focal_length": 65, "preset": "50mm_normal", "description": "Normal to portrait range"},
    "m": {"focal_length": 50, "preset": "50mm_normal", "description": "Normal lens, natural perspective"},
    "mf": {"focal_length": 50, "preset": "50mm_normal", "description": "Normal lens"},
    "f": {"focal_length": 35, "preset": "35mm_documentary", "description": "Slight wide for full body"},
    "w": {"focal_length": 24, "preset": "24mm_wide", "description": "Wide for environment"},
    "ew": {"focal_length": 14, "preset": "14mm_ultra_wide", "description": "Ultra wide for establishing"},
}

# F-stop recommendations by shot size (depth of field)
FSTOP_BY_SHOT_SIZE = {
    "ecu": {"f_stop": 11.0, "reason": "Deep DOF for detail sharpness"},
    "cu": {"f_stop": 2.8, "reason": "Shallow DOF, subject separation"},
    "mcu": {"f_stop": 4.0, "reason": "Moderate DOF"},
    "m": {"f_stop": 5.6, "reason": "Balanced DOF"},
    "mf": {"f_stop": 5.6, "reason": "Balanced DOF"},
    "f": {"f_stop": 8.0, "reason": "Deeper DOF for full body"},
    "w": {"f_stop": 11.0, "reason": "Deep DOF, see environment"},
    "ew": {"f_stop": 11.0, "reason": "Deep DOF, everything sharp"},
}

# Camera angles and their emotional impact
CAMERA_ANGLES = {
    "low": {"height_factor": -0.5, "power": "dominant", "emotion": "powerful, heroic"},
    "eye": {"height_factor": 0.0, "power": "neutral", "emotion": "relatable, natural"},
    "high": {"height_factor": 0.5, "power": "submissive", "emotion": "vulnerable, small"},
    "birds_eye": {"height_factor": 1.0, "power": "omniscient", "emotion": "overview, god view"},
    "worms_eye": {"height_factor": -1.0, "power": "extreme_dominant", "emotion": "dramatic, imposing"},
}

# Camera positions relative to subject
CAMERA_POSITIONS = {
    "front": {"angle_y": 0, "description": "Straight on, direct"},
    "three_quarter": {"angle_y": 45, "description": "3/4 view, shows front and side"},
    "profile": {"angle_y": 90, "description": "Side view"},
    "three_quarter_back": {"angle_y": 135, "description": "3/4 from back"},
    "back": {"angle_y": 180, "description": "From behind"},
}

# Lighting ratios by mood
LIGHTING_RATIOS = {
    "high_key": {"key_fill": 1.5, "description": "Bright, minimal shadows"},
    "normal": {"key_fill": 2.0, "description": "Standard 2:1 ratio"},
    "dramatic": {"key_fill": 4.0, "description": "4:1 ratio, moody"},
    "low_key": {"key_fill": 8.0, "description": "8:1 ratio, very dark"},
    "noir": {"key_fill": 16.0, "description": "Extreme contrast"},
}


@dataclass
class CompositionConfig:
    """
    Composition rules for a shot - the "DP's cheat sheet".

    These values are automatically derived from shot_size, mood, and style
    but can be overridden for specific creative needs.

    Attributes:
        shot_size: Size of shot (ecu, cu, mcu, m, mf, f, w, ew)
        camera_angle: Vertical angle (low, eye, high, birds_eye, worms_eye)
        camera_position: Horizontal position (front, three_quarter, profile, etc.)
        subject_framing: Where subject is in frame (center, thirds_left, thirds_right)
        headroom: Space above subject's head (0.0-1.0)
        looking_room: Space in direction subject is looking (0.0-1.0)
        lens_focal_length: Recommended focal length in mm
        lens_preset: Lens preset name
        f_stop: Recommended aperture
        lighting_ratio: Key:fill lighting ratio
    """
    shot_size: str = "m"
    camera_angle: str = "eye"
    camera_position: str = "three_quarter"
    subject_framing: str = "center"
    headroom: float = 0.1
    looking_room: float = 0.15
    lens_focal_length: float = 50.0
    lens_preset: str = "50mm_normal"
    f_stop: float = 5.6
    lighting_ratio: float = 2.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "shot_size": self.shot_size,
            "camera_angle": self.camera_angle,
            "camera_position": self.camera_position,
            "subject_framing": self.subject_framing,
            "headroom": self.headroom,
            "looking_room": self.looking_room,
            "lens_focal_length": self.lens_focal_length,
            "lens_preset": self.lens_preset,
            "f_stop": self.f_stop,
            "lighting_ratio": self.lighting_ratio,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositionConfig":
        """Create from dictionary."""
        return cls(
            shot_size=data.get("shot_size", "m"),
            camera_angle=data.get("camera_angle", "eye"),
            camera_position=data.get("camera_position", "three_quarter"),
            subject_framing=data.get("subject_framing", "center"),
            headroom=data.get("headroom", 0.1),
            looking_room=data.get("looking_room", 0.15),
            lens_focal_length=data.get("lens_focal_length", 50.0),
            lens_preset=data.get("lens_preset", "50mm_normal"),
            f_stop=data.get("f_stop", 5.6),
            lighting_ratio=data.get("lighting_ratio", 2.0),
        )

    @classmethod
    def from_shot_size(cls, shot_size: str, mood: str = "normal") -> "CompositionConfig":
        """
        Create composition config from shot size with automatic lens/f-stop selection.

        This is the "DP's auto-mode" - automatically selects appropriate
        lens, f-stop, and lighting ratio based on shot size.
        """
        lens_info = LENS_BY_SHOT_SIZE.get(shot_size, LENS_BY_SHOT_SIZE["m"])
        fstop_info = FSTOP_BY_SHOT_SIZE.get(shot_size, FSTOP_BY_SHOT_SIZE["m"])
        ratio_info = LIGHTING_RATIOS.get(mood, LIGHTING_RATIOS["normal"])

        return cls(
            shot_size=shot_size,
            lens_focal_length=lens_info["focal_length"],
            lens_preset=lens_info["preset"],
            f_stop=fstop_info["f_stop"],
            lighting_ratio=ratio_info["key_fill"],
        )


@dataclass
class CompleteShotConfig:
    """
    Complete shot configuration - everything needed for one shot.

    This is the "master config" that ties together:
    - Camera settings (lens, f-stop, position)
    - Composition rules (shot size, framing, angle)
    - Lighting setup (preset or custom)
    - Backdrop/environment
    - Post-processing hints

    Usage:
        # Create from preset
        config = CompleteShotConfig.from_preset("apple_hero", subject_name="product")

        # Create from shot size (auto-selects lens, f-stop, lighting)
        config = CompleteShotConfig.from_shot_size("mcu", mood="dramatic")

        # Create manually
        config = CompleteShotConfig(
            name="hero_shot_01",
            composition=CompositionConfig(shot_size="cu"),
            camera=CameraConfig(focal_length=85, f_stop=2.8),
            lighting_rig="three_point_soft",
            backdrop=BackdropConfig(backdrop_type="gradient"),
        )
    """
    name: str = "shot_01"
    description: str = ""

    # Composition rules (derived from shot_size or set manually)
    composition: CompositionConfig = field(default_factory=CompositionConfig)

    # Camera configuration
    camera: CameraConfig = field(default_factory=CameraConfig)

    # Targeting (plumb bob for orbit/focus)
    plumb_bob: PlumbBobConfig = field(default_factory=PlumbBobConfig)

    # Camera rig (tripod, dolly, etc.)
    rig: RigConfig = field(default_factory=RigConfig)

    # Lighting (preset name or custom config)
    lighting_rig: str = ""  # Preset name like "three_point_soft"
    lights: Dict[str, LightConfig] = field(default_factory=dict)  # Or custom lights

    # Backdrop/environment
    backdrop: BackdropConfig = field(default_factory=BackdropConfig)
    environment_preset: str = ""  # HDRI or environment preset

    # Lens imperfections
    imperfections: ImperfectionConfig = field(default_factory=ImperfectionConfig)

    # Post-processing hints
    color_grade: str = "neutral"  # warm, cool, neutral, dramatic
    contrast: str = "medium"  # low, medium, high
    saturation: float = 1.0

    # Subject reference
    subject_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "composition": self.composition.to_dict(),
            "camera": self.camera.to_dict(),
            "plumb_bob": self.plumb_bob.to_dict(),
            "rig": self.rig.to_dict(),
            "lighting_rig": self.lighting_rig,
            "lights": {k: v.to_dict() for k, v in self.lights.items()},
            "backdrop": self.backdrop.to_dict(),
            "environment_preset": self.environment_preset,
            "imperfections": self.imperfections.to_dict(),
            "color_grade": self.color_grade,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "subject_name": self.subject_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompleteShotConfig":
        """Create from dictionary."""
        lights_data = data.get("lights", {})
        lights = {k: LightConfig.from_dict(v) for k, v in lights_data.items()}

        return cls(
            name=data.get("name", "shot_01"),
            description=data.get("description", ""),
            composition=CompositionConfig.from_dict(data.get("composition", {})),
            camera=CameraConfig.from_dict(data.get("camera", {})),
            plumb_bob=PlumbBobConfig.from_dict(data.get("plumb_bob", {})),
            rig=RigConfig.from_dict(data.get("rig", {})),
            lighting_rig=data.get("lighting_rig", ""),
            lights=lights,
            backdrop=BackdropConfig.from_dict(data.get("backdrop", {})),
            environment_preset=data.get("environment_preset", ""),
            imperfections=ImperfectionConfig.from_dict(data.get("imperfections", {})),
            color_grade=data.get("color_grade", "neutral"),
            contrast=data.get("contrast", "medium"),
            saturation=data.get("saturation", 1.0),
            subject_name=data.get("subject_name", ""),
        )

    @classmethod
    def from_shot_size(
        cls,
        shot_size: str,
        mood: str = "normal",
        subject_name: str = ""
    ) -> "CompleteShotConfig":
        """
        Create complete shot config from shot size.

        Automatically selects appropriate lens, f-stop, and lighting
        based on cinematography rules.

        Args:
            shot_size: Shot size (ecu, cu, mcu, m, mf, f, w, ew)
            mood: Lighting mood (high_key, normal, dramatic, low_key, noir)
            subject_name: Name of subject object
        """
        composition = CompositionConfig.from_shot_size(shot_size, mood)

        camera = CameraConfig(
            focal_length=composition.lens_focal_length,
            f_stop=composition.f_stop,
        )

        return cls(
            name=f"{shot_size}_{mood}",
            composition=composition,
            camera=camera,
            subject_name=subject_name,
        )

    @classmethod
    def from_preset(
        cls,
        preset_name: str,
        subject_name: str = ""
    ) -> "CompleteShotConfig":
        """
        Create complete shot config from a shot preset.

        This loads a preset from the shot preset YAML files and
        creates a fully configured CompleteShotConfig.

        Args:
            preset_name: Shot preset name (e.g., "apple_hero", "studio_white")
            subject_name: Name of subject object
        """
        # This will be implemented in shot_builder.py
        # For now, return a basic config
        return cls(
            name=preset_name,
            subject_name=subject_name,
        )


@dataclass
class ShotTemplateConfig:
    """
    Shot template configuration with inheritance support (REQ-CINE-TEMPLATE).

    Templates can extend other templates using the 'extends' field.
    Abstract templates cannot be rendered directly.

    Attributes:
        name: Template name (unique identifier)
        extends: Parent template name for inheritance (empty = base template)
        abstract: If True, template cannot be rendered directly
        description: Human-readable description
        camera: Camera configuration overrides
        plumb_bob: Plumb bob configuration overrides
        rig: Camera rig configuration overrides
        lighting_rig: Lighting rig preset name
        lights: Custom light configurations
        backdrop: Backdrop configuration overrides
        environment_preset: Environment/HDRI preset name
        imperfections: Lens imperfection configuration
        animation: Animation configuration
        render: Render settings overrides
        color: Color management overrides
        composition: Composition rules overrides
        subject_name: Default subject object name
    """
    name: str = ""
    extends: str = ""  # Parent template name
    abstract: bool = False  # Cannot render directly if True
    description: str = ""
    # All other fields optional - override parent values
    camera: Optional[CameraConfig] = None
    plumb_bob: Optional[PlumbBobConfig] = None
    rig: Optional[RigConfig] = None
    lighting_rig: str = ""
    lights: Dict[str, LightConfig] = field(default_factory=dict)
    backdrop: Optional[BackdropConfig] = None
    environment_preset: str = ""
    imperfections: Optional[ImperfectionConfig] = None
    animation: Optional[AnimationConfig] = None
    render: Optional[CinematicRenderSettings] = None
    color: Optional[ColorConfig] = None
    composition: Optional[CompositionConfig] = None
    subject_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "extends": self.extends,
            "abstract": self.abstract,
            "description": self.description,
            "camera": self.camera.to_dict() if self.camera else None,
            "plumb_bob": self.plumb_bob.to_dict() if self.plumb_bob else None,
            "rig": self.rig.to_dict() if self.rig else None,
            "lighting_rig": self.lighting_rig,
            "lights": {k: v.to_dict() for k, v in self.lights.items()},
            "backdrop": self.backdrop.to_dict() if self.backdrop else None,
            "environment_preset": self.environment_preset,
            "imperfections": self.imperfections.to_dict() if self.imperfections else None,
            "animation": self.animation.to_dict() if self.animation else None,
            "render": self.render.to_dict() if self.render else None,
            "color": self.color.to_dict() if self.color else None,
            "composition": self.composition.to_dict() if self.composition else None,
            "subject_name": self.subject_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShotTemplateConfig":
        """Create from dictionary."""
        lights_data = data.get("lights", {})
        lights = {k: LightConfig.from_dict(v) for k, v in lights_data.items()}

        return cls(
            name=data.get("name", ""),
            extends=data.get("extends", ""),
            abstract=data.get("abstract", False),
            description=data.get("description", ""),
            camera=CameraConfig.from_dict(data["camera"]) if data.get("camera") else None,
            plumb_bob=PlumbBobConfig.from_dict(data["plumb_bob"]) if data.get("plumb_bob") else None,
            rig=RigConfig.from_dict(data["rig"]) if data.get("rig") else None,
            lighting_rig=data.get("lighting_rig", ""),
            lights=lights,
            backdrop=BackdropConfig.from_dict(data["backdrop"]) if data.get("backdrop") else None,
            environment_preset=data.get("environment_preset", ""),
            imperfections=ImperfectionConfig.from_dict(data["imperfections"]) if data.get("imperfections") else None,
            animation=AnimationConfig.from_dict(data["animation"]) if data.get("animation") else None,
            render=CinematicRenderSettings.from_dict(data["render"]) if data.get("render") else None,
            color=ColorConfig.from_dict(data["color"]) if data.get("color") else None,
            composition=CompositionConfig.from_dict(data["composition"]) if data.get("composition") else None,
            subject_name=data.get("subject_name", ""),
        )


@dataclass
class ShotAssemblyConfig:
    """
    Complete shot assembly configuration (REQ-CINE-SHOT).

    Brings together all elements for a single shot:
    - Template reference (with inheritance resolution)
    - Subject specification
    - Camera configuration
    - Lighting configuration
    - Backdrop configuration
    - Color/render settings
    - Animation (optional)

    Supports resume/edit workflow via frame store integration.

    Attributes:
        name: Shot name (used for output files)
        template: Template name to use as base
        subject: Subject object name or specification
        camera: Camera config (overrides template)
        lighting_rig: Lighting rig preset name
        lights: Custom lights (overrides template)
        backdrop: Backdrop config (overrides template)
        color: Color management config
        render: Render settings
        animation: Animation config (optional)
        output_path: Output directory for renders
        metadata: Additional metadata
    """
    name: str = "shot_01"
    template: str = ""  # Template to use
    subject: str = ""  # Subject object name
    camera: Optional[CameraConfig] = None
    plumb_bob: Optional[PlumbBobConfig] = None
    lighting_rig: str = ""
    lights: Dict[str, LightConfig] = field(default_factory=dict)
    backdrop: Optional[BackdropConfig] = None
    color: Optional[ColorConfig] = None
    render: Optional[CinematicRenderSettings] = None
    animation: Optional[AnimationConfig] = None
    output_path: str = "//render/"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "template": self.template,
            "subject": self.subject,
            "camera": self.camera.to_dict() if self.camera else None,
            "plumb_bob": self.plumb_bob.to_dict() if self.plumb_bob else None,
            "lighting_rig": self.lighting_rig,
            "lights": {k: v.to_dict() for k, v in self.lights.items()},
            "backdrop": self.backdrop.to_dict() if self.backdrop else None,
            "color": self.color.to_dict() if self.color else None,
            "render": self.render.to_dict() if self.render else None,
            "animation": self.animation.to_dict() if self.animation else None,
            "output_path": self.output_path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShotAssemblyConfig":
        """Create from dictionary."""
        lights_data = data.get("lights", {})
        lights = {k: LightConfig.from_dict(v) for k, v in lights_data.items()}

        return cls(
            name=data.get("name", "shot_01"),
            template=data.get("template", ""),
            subject=data.get("subject", ""),
            camera=CameraConfig.from_dict(data["camera"]) if data.get("camera") else None,
            plumb_bob=PlumbBobConfig.from_dict(data["plumb_bob"]) if data.get("plumb_bob") else None,
            lighting_rig=data.get("lighting_rig", ""),
            lights=lights,
            backdrop=BackdropConfig.from_dict(data["backdrop"]) if data.get("backdrop") else None,
            color=ColorConfig.from_dict(data["color"]) if data.get("color") else None,
            render=CinematicRenderSettings.from_dict(data["render"]) if data.get("render") else None,
            animation=AnimationConfig.from_dict(data["animation"]) if data.get("animation") else None,
            output_path=data.get("output_path", "//render/"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CameraMatchConfig:
    """
    Camera matching configuration (REQ-CINE-MATCH).

    Allows matching a Blender camera to a reference image by analyzing
    perspective, focal length, and camera position.

    Attributes:
        reference_image: Path to reference image for matching
        focal_length_estimate: Estimated focal length (0 = auto-detect)
        horizon_line: Y position of horizon line (0-1 normalized)
        vanishing_points: Detected/calculated vanishing points
        auto_detect_focal: Automatically estimate focal length
        auto_detect_horizon: Automatically detect horizon line
        match_mode: Matching mode (perspective, orthographic, isometric)
        tolerance: Matching tolerance in pixels
        subject_bounds: Optional subject bounding box in image (for scale ref)
    """
    reference_image: str = ""
    focal_length_estimate: float = 0.0  # 0 = auto
    horizon_line: float = 0.5  # Normalized 0-1
    vanishing_points: List[Tuple[float, float]] = field(default_factory=list)
    auto_detect_focal: bool = True
    auto_detect_horizon: bool = True
    match_mode: str = "perspective"  # perspective, orthographic, isometric
    tolerance: float = 5.0  # Pixels
    subject_bounds: Optional[Tuple[float, float, float, float]] = None  # x1, y1, x2, y2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "reference_image": self.reference_image,
            "focal_length_estimate": self.focal_length_estimate,
            "horizon_line": self.horizon_line,
            "vanishing_points": [list(vp) for vp in self.vanishing_points],
            "auto_detect_focal": self.auto_detect_focal,
            "auto_detect_horizon": self.auto_detect_horizon,
            "match_mode": self.match_mode,
            "tolerance": self.tolerance,
            "subject_bounds": list(self.subject_bounds) if self.subject_bounds else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraMatchConfig":
        """Create from dictionary."""
        vps_data = data.get("vanishing_points", [])
        vps = [tuple(vp) for vp in vps_data] if vps_data else []
        bounds = data.get("subject_bounds")
        if bounds:
            bounds = tuple(bounds)

        return cls(
            reference_image=data.get("reference_image", ""),
            focal_length_estimate=data.get("focal_length_estimate", 0.0),
            horizon_line=data.get("horizon_line", 0.5),
            vanishing_points=vps,
            auto_detect_focal=data.get("auto_detect_focal", True),
            auto_detect_horizon=data.get("auto_detect_horizon", True),
            match_mode=data.get("match_mode", "perspective"),
            tolerance=data.get("tolerance", 5.0),
            subject_bounds=bounds,
        )


@dataclass
class TrackingImportConfig:
    """
    Tracking data import configuration (REQ-CINE-MATCH).

    Supports importing camera tracking data from external match-move
    software like Nuke, After Effects, SynthEyes, etc.

    Supported Formats:
    - nuke_chan: Nuke .chan files
    - fbx: FBX camera export
    - alembic: Alembic .abc camera
    - bvh: BVH motion capture
    - json: Custom JSON format

    Attributes:
        format: Import format (nuke_chan, fbx, alembic, bvh, json)
        file_path: Path to tracking data file
        frame_offset: Frame number offset
        scale_factor: Scale multiplier for imported data
        coordinate_system: Source coordinate system (y_up, z_up)
        interpolate: Interpolate between keyframes
        smooth_rotation: Apply smoothing to rotation data
    """
    format: str = "fbx"  # nuke_chan, fbx, alembic, bvh, json
    file_path: str = ""
    frame_offset: int = 0
    scale_factor: float = 1.0
    coordinate_system: str = "y_up"  # y_up, z_up
    interpolate: bool = True
    smooth_rotation: float = 0.0  # Smoothing factor 0-1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "format": self.format,
            "file_path": self.file_path,
            "frame_offset": self.frame_offset,
            "scale_factor": self.scale_factor,
            "coordinate_system": self.coordinate_system,
            "interpolate": self.interpolate,
            "smooth_rotation": self.smooth_rotation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackingImportConfig":
        """Create from dictionary."""
        return cls(
            format=data.get("format", "fbx"),
            file_path=data.get("file_path", ""),
            frame_offset=data.get("frame_offset", 0),
            scale_factor=data.get("scale_factor", 1.0),
            coordinate_system=data.get("coordinate_system", "y_up"),
            interpolate=data.get("interpolate", True),
            smooth_rotation=data.get("smooth_rotation", 0.0),
        )


@dataclass
class AudioSyncConfig:
    """
    Audio sync configuration (REQ-CINE-AUDIO).

    Supports loading audio tracks and placing beat markers for
    animation timing and synchronization.

    Attributes:
        audio_file: Path to audio file
        bpm: Beats per minute (0 = auto-detect)
        time_signature: Time signature (4/4 default)
        beat_markers: List of frame numbers for beat markers
        auto_detect_bpm: Automatically detect BPM from audio
        offset_frames: Frame offset for sync
        markers: Named markers at specific frames
    """
    audio_file: str = ""
    bpm: float = 0.0  # 0 = auto-detect
    time_signature: Tuple[int, int] = (4, 4)
    beat_markers: List[int] = field(default_factory=list)
    auto_detect_bpm: bool = True
    offset_frames: int = 0
    markers: Dict[str, int] = field(default_factory=dict)  # name -> frame

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "audio_file": self.audio_file,
            "bpm": self.bpm,
            "time_signature": list(self.time_signature),
            "beat_markers": self.beat_markers,
            "auto_detect_bpm": self.auto_detect_bpm,
            "offset_frames": self.offset_frames,
            "markers": self.markers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioSyncConfig":
        """Create from dictionary."""
        return cls(
            audio_file=data.get("audio_file", ""),
            bpm=data.get("bpm", 0.0),
            time_signature=tuple(data.get("time_signature", (4, 4))),
            beat_markers=data.get("beat_markers", []),
            auto_detect_bpm=data.get("auto_detect_bpm", True),
            offset_frames=data.get("offset_frames", 0),
            markers=data.get("markers", {}),
        )


@dataclass
class CameraProfile:
    """
    Camera device profile for realistic camera matching.

    Stores intrinsic parameters for specific camera/lens combinations
    to improve match accuracy.

    Attributes:
        name: Profile name (e.g., "iPhone_15_Pro_Main", "Sony_A7III_50mm")
        sensor_width: Sensor width in mm
        sensor_height: Sensor height in mm
        focal_length: Lens focal length in mm
        distortion_model: Lens distortion model (none, simple, brown_conrady)
        distortion_params: Distortion coefficients
        crop_factor: Sensor crop factor
        aspect_ratio: Pixel aspect ratio
    """
    name: str = ""
    sensor_width: float = 36.0
    sensor_height: float = 24.0
    focal_length: float = 50.0
    distortion_model: str = "none"
    distortion_params: List[float] = field(default_factory=list)
    crop_factor: float = 1.0
    aspect_ratio: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "sensor_width": self.sensor_width,
            "sensor_height": self.sensor_height,
            "focal_length": self.focal_length,
            "distortion_model": self.distortion_model,
            "distortion_params": self.distortion_params,
            "crop_factor": self.crop_factor,
            "aspect_ratio": self.aspect_ratio,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraProfile":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            sensor_width=data.get("sensor_width", 36.0),
            sensor_height=data.get("sensor_height", 24.0),
            focal_length=data.get("focal_length", 50.0),
            distortion_model=data.get("distortion_model", "none"),
            distortion_params=data.get("distortion_params", []),
            crop_factor=data.get("crop_factor", 1.0),
            aspect_ratio=data.get("aspect_ratio", 1.0),
        )


@dataclass
class IntegrationConfig:
    """
    Integration configuration for connecting cinematic with control surfaces.

    Defines how the cinematic rendering system integrates with the
    control surface design system for unified product visualization.

    Attributes:
        control_surface_preset: Control surface style preset name
        apply_to_subject: Apply control surface materials to subject
        sync_animations: Synchronize control surface animations with camera
        auto_frame_subject: Automatically frame control surface in camera
        material_sync: Sync material properties between systems
        render_modes: Available render modes (hero, catalog, turntable)
    """
    control_surface_preset: str = ""
    apply_to_subject: bool = True
    sync_animations: bool = True
    auto_frame_subject: bool = True
    material_sync: bool = True
    render_modes: List[str] = field(default_factory=lambda: ["hero", "catalog", "turntable"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "control_surface_preset": self.control_surface_preset,
            "apply_to_subject": self.apply_to_subject,
            "sync_animations": self.sync_animations,
            "auto_frame_subject": self.auto_frame_subject,
            "material_sync": self.material_sync,
            "render_modes": self.render_modes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationConfig":
        """Create from dictionary."""
        return cls(
            control_surface_preset=data.get("control_surface_preset", ""),
            apply_to_subject=data.get("apply_to_subject", True),
            sync_animations=data.get("sync_animations", True),
            auto_frame_subject=data.get("auto_frame_subject", True),
            material_sync=data.get("material_sync", True),
            render_modes=data.get("render_modes", ["hero", "catalog", "turntable"]),
        )


@dataclass
class TestConfig:
    """
    Test configuration for end-to-end rendering tests.

    Defines test scenarios for validating the cinematic system.

    Attributes:
        name: Test name
        description: Test description
        shot_config: Shot configuration to test
        expected_passes: List of expected render passes
        validation_checks: List of validation checks to perform
        tolerance: Comparison tolerance for validation
        reference_image: Optional reference image for comparison
    """
    name: str = ""
    description: str = ""
    shot_config: Dict[str, Any] = field(default_factory=dict)
    expected_passes: List[str] = field(default_factory=lambda: ["combined"])
    validation_checks: List[str] = field(default_factory=list)
    tolerance: float = 0.01
    reference_image: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "shot_config": self.shot_config,
            "expected_passes": self.expected_passes,
            "validation_checks": self.validation_checks,
            "tolerance": self.tolerance,
            "reference_image": self.reference_image,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestConfig":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            shot_config=data.get("shot_config", {}),
            expected_passes=data.get("expected_passes", ["combined"]),
            validation_checks=data.get("validation_checks", []),
            tolerance=data.get("tolerance", 0.01),
            reference_image=data.get("reference_image", ""),
        )


@dataclass
class PerformanceConfig:
    """
    Performance benchmarking configuration.

    Defines performance targets and measurement parameters.

    Attributes:
        target_render_time_preview: Target time for preview renders (seconds)
        target_render_time_production: Target time for production renders (seconds/frame)
        target_orbit_animation_time: Target for orbit animation setup (ms)
        target_shot_assembly_time: Target for shot assembly (ms)
        memory_limit_mb: Maximum memory usage (MB)
        gpu_utilization_target: Target GPU utilization (0-1)
        enable_profiling: Enable performance profiling
        profile_output: Path to save profiling data
    """
    target_render_time_preview: float = 10.0
    target_render_time_production: float = 120.0
    target_orbit_animation_time: float = 50.0
    target_shot_assembly_time: float = 100.0
    memory_limit_mb: int = 4096
    gpu_utilization_target: float = 0.8
    enable_profiling: bool = False
    profile_output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target_render_time_preview": self.target_render_time_preview,
            "target_render_time_production": self.target_render_time_production,
            "target_orbit_animation_time": self.target_orbit_animation_time,
            "target_shot_assembly_time": self.target_shot_assembly_time,
            "memory_limit_mb": self.memory_limit_mb,
            "gpu_utilization_target": self.gpu_utilization_target,
            "enable_profiling": self.enable_profiling,
            "profile_output": self.profile_output,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceConfig":
        """Create from dictionary."""
        return cls(
            target_render_time_preview=data.get("target_render_time_preview", 10.0),
            target_render_time_production=data.get("target_render_time_production", 120.0),
            target_orbit_animation_time=data.get("target_orbit_animation_time", 50.0),
            target_shot_assembly_time=data.get("target_shot_assembly_time", 100.0),
            memory_limit_mb=data.get("memory_limit_mb", 4096),
            gpu_utilization_target=data.get("gpu_utilization_target", 0.8),
            enable_profiling=data.get("enable_profiling", False),
            profile_output=data.get("profile_output", ""),
        )


@dataclass
class BenchmarkResult:
    """
    Performance benchmark result.

    Stores timing and resource usage measurements.

    Attributes:
        name: Benchmark name
        duration_seconds: Total duration in seconds
        memory_peak_mb: Peak memory usage in MB
        gpu_utilization: Average GPU utilization (0-1)
        frames_rendered: Number of frames rendered
        passes_generated: Number of passes generated
        timestamp: ISO timestamp of benchmark
        passed: Whether benchmark passed performance targets
    """
    name: str = ""
    duration_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    gpu_utilization: float = 0.0
    frames_rendered: int = 0
    passes_generated: int = 0
    timestamp: str = ""
    passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "duration_seconds": self.duration_seconds,
            "memory_peak_mb": self.memory_peak_mb,
            "gpu_utilization": self.gpu_utilization,
            "frames_rendered": self.frames_rendered,
            "passes_generated": self.passes_generated,
            "timestamp": self.timestamp,
            "passed": self.passed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkResult":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            duration_seconds=data.get("duration_seconds", 0.0),
            memory_peak_mb=data.get("memory_peak_mb", 0.0),
            gpu_utilization=data.get("gpu_utilization", 0.0),
            frames_rendered=data.get("frames_rendered", 0),
            passes_generated=data.get("passes_generated", 0),
            timestamp=data.get("timestamp", ""),
            passed=data.get("passed", True),
        )
