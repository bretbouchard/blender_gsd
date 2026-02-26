"""
Types for projector shader system.

Projection shader types for content-to-surface mapping in physical projector calibration.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, Any
from enum import Enum


class ProjectionMode(Enum):
    """Content projection mode."""
    CAMERA = "camera"           # Project from camera/projector POV
    UV = "uv"                   # Use existing UV coordinates
    TRIPLANAR = "triplanar"     # Triplanar projection


class BlendMode(Enum):
    """Shader blend modes for projection compositing."""
    MIX = "mix"
    ADD = "add"
    MULTIPLY = "multiply"
    OVERLAY = "overlay"
    SCREEN = "screen"


class TextureFilter(Enum):
    """Texture filtering modes."""
    LINEAR = "Linear"
    CLOSEST = "Closest"
    CUBIC = "Cubic"


class TextureExtension(Enum):
    """Texture extension modes."""
    REPEAT = "Repeat"
    EXTEND = "Extend"
    CLIP = "Clip"


@dataclass
class ProjectionShaderConfig:
    """Configuration for projector shader.

    Contains all parameters needed to set up a projection shader
    that projects content from a projector's point of view onto surfaces.
    """
    # Projector optical parameters
    throw_ratio: float = 1.0
    sensor_width: float = 36.0
    resolution_x: int = 1920
    resolution_y: int = 1080
    shift_x: float = 0.0       # Lens shift horizontal (fraction)
    shift_y: float = 0.0       # Lens shift vertical (fraction)

    # Projection settings
    mode: ProjectionMode = ProjectionMode.CAMERA
    blend_mode: BlendMode = BlendMode.MIX
    intensity: float = 1.0

    # Content source
    content_image: Optional[str] = None
    content_video: Optional[str] = None

    # Advanced texture settings
    use_mipmap: bool = True
    filter_type: TextureFilter = TextureFilter.LINEAR
    extension: TextureExtension = TextureExtension.CLIP

    # Color settings
    color_space: str = "sRGB"  # sRGB, Linear, Filmic
    gamma: float = 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "throw_ratio": self.throw_ratio,
            "sensor_width": self.sensor_width,
            "resolution_x": self.resolution_x,
            "resolution_y": self.resolution_y,
            "shift_x": self.shift_x,
            "shift_y": self.shift_y,
            "mode": self.mode.value,
            "blend_mode": self.blend_mode.value,
            "intensity": self.intensity,
            "content_image": self.content_image,
            "content_video": self.content_video,
            "use_mipmap": self.use_mipmap,
            "filter_type": self.filter_type.value,
            "extension": self.extension.value,
            "color_space": self.color_space,
            "gamma": self.gamma,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectionShaderConfig":
        """Create from dictionary."""
        return cls(
            throw_ratio=data.get("throw_ratio", 1.0),
            sensor_width=data.get("sensor_width", 36.0),
            resolution_x=data.get("resolution_x", 1920),
            resolution_y=data.get("resolution_y", 1080),
            shift_x=data.get("shift_x", 0.0),
            shift_y=data.get("shift_y", 0.0),
            mode=ProjectionMode(data.get("mode", "camera")),
            blend_mode=BlendMode(data.get("blend_mode", "mix")),
            intensity=data.get("intensity", 1.0),
            content_image=data.get("content_image"),
            content_video=data.get("content_video"),
            use_mipmap=data.get("use_mipmap", True),
            filter_type=TextureFilter(data.get("filter_type", "Linear")),
            extension=TextureExtension(data.get("extension", "Clip")),
            color_space=data.get("color_space", "sRGB"),
            gamma=data.get("gamma", 1.0),
        )


@dataclass
class ProjectionShaderResult:
    """Result of projection shader creation.

    Contains references to the created Blender objects for the shader setup.
    """
    material: Any = None                 # bpy.types.Material (optional at runtime)
    node_group: Any = None               # bpy.types.NodeGroup
    texture_node: Any = None             # ShaderNodeTexImage
    projection_node: Any = None          # ShaderNodeGroup
    output_node: Any = None              # ShaderNodeOutputMaterial

    # Metadata
    material_name: str = ""
    success: bool = True
    errors: list = field(default_factory=list)


@dataclass
class ProxyGeometryConfig:
    """Configuration for proxy geometry generation.

    Proxy geometry is a simplified mesh that matches the projection surface,
    optimized for UV projection from the projector.
    """
    subdivisions: int = 2
    margin: float = 0.1          # Margin around projection area (meters)
    optimize_uv: bool = True     # Optimize UV layout for projection
    smooth_shading: bool = False # Use smooth shading
    double_sided: bool = True    # Render both sides

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "subdivisions": self.subdivisions,
            "margin": self.margin,
            "optimize_uv": self.optimize_uv,
            "smooth_shading": self.smooth_shading,
            "double_sided": self.double_sided,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyGeometryConfig":
        """Create from dictionary."""
        return cls(
            subdivisions=data.get("subdivisions", 2),
            margin=data.get("margin", 0.1),
            optimize_uv=data.get("optimize_uv", True),
            smooth_shading=data.get("smooth_shading", False),
            double_sided=data.get("double_sided", True),
        )


@dataclass
class ProxyGeometryResult:
    """Result of proxy geometry creation."""
    object_ref: Any = None              # bpy.types.Object
    mesh_name: str = ""
    vertex_count: int = 0
    face_count: int = 0
    uv_bounds: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 1.0)  # u_min, u_max, v_min, v_max
    success: bool = True
    errors: list = field(default_factory=list)
