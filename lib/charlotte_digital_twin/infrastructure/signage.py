"""
Highway Signage Generator

Generates highway signs:
- Exit signs
- Overhead gantries
- Directional signs
- Speed limit signs
- Mile markers
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any


class SignType(Enum):
    """Types of highway signs."""
    EXIT_SIGN = "exit"
    OVERHEAD_GANTRY = "gantry"
    DIRECTIONAL = "directional"
    SPEED_LIMIT = "speed"
    MILE_MARKER = "mile"
    EXIT_NUMBER = "exit_number"


@dataclass
class SignConfig:
    """Configuration for sign generation."""
    # Dimensions (meters)
    width: float = 2.4
    height: float = 1.5
    thickness: float = 0.05

    # Colors
    background_color: Tuple[float, float, float] = (0.1, 0.4, 0.1)  # Green
    text_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # White
    border_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    # Text
    text: str = "EXIT"
    font_size: float = 0.3

    # Pole
    pole_height: float = 5.0
    pole_diameter: float = 0.15


# Standard sign configurations
SIGN_CONFIGS = {
    SignType.EXIT_SIGN: SignConfig(
        width=2.4,
        height=1.5,
        background_color=(0.1, 0.4, 0.1),  # Green
        text="EXIT",
    ),
    SignType.DIRECTIONAL: SignConfig(
        width=3.0,
        height=1.8,
        background_color=(0.1, 0.4, 0.1),  # Green
        text="",
    ),
    SignType.SPEED_LIMIT: SignConfig(
        width=0.6,
        height=0.75,
        background_color=(1.0, 1.0, 1.0),  # White
        text_color=(0.0, 0.0, 0.0),  # Black
        text="65",
    ),
    SignType.MILE_MARKER: SignConfig(
        width=0.3,
        height=0.9,
        background_color=(1.0, 1.0, 1.0),
        text_color=(0.0, 0.0, 0.0),
        pole_height=1.2,
    ),
}


class SignageGenerator:
    """
    Generates highway signage geometry.

    Creates signs as 3D objects with proper materials and placement.
    """

    def __init__(self):
        """Initialize signage generator."""
        self._material_cache: Dict[str, Any] = {}

    def create_sign(
        self,
        sign_type: SignType = SignType.DIRECTIONAL,
        text: Optional[str] = None,
        config: Optional[SignConfig] = None,
        name: str = "Highway_Sign",
    ) -> Optional[Object]:
        """
        Create a highway sign.

        Args:
            sign_type: Type of sign
            text: Override text
            config: Override configuration
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or SIGN_CONFIGS.get(sign_type, SignConfig())
        if text:
            config.text = text

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        w, h, t = config.width / 2, config.height / 2, config.thickness / 2

        # Sign panel vertices
        v1 = bm.verts.new((-w, -t, -h))
        v2 = bm.verts.new((w, -t, -h))
        v3 = bm.verts.new((w, t, -h))
        v4 = bm.verts.new((-w, t, -h))
        v5 = bm.verts.new((-w, -t, h))
        v6 = bm.verts.new((w, -t, h))
        v7 = bm.verts.new((w, t, h))
        v8 = bm.verts.new((-w, t, h))

        bm.verts.ensure_lookup_table()

        # Faces
        bm.faces.new([v1, v2, v3, v4])  # Back
        bm.faces.new([v5, v8, v7, v6])  # Front
        bm.faces.new([v1, v5, v6, v2])  # Bottom
        bm.faces.new([v2, v6, v7, v3])  # Right
        bm.faces.new([v3, v7, v8, v4])  # Top
        bm.faces.new([v4, v8, v5, v1])  # Left

        bm.to_mesh(mesh)
        bm.free()

        # Apply material
        mat = self._get_sign_material(config)
        if mat:
            obj.data.materials.append(mat)

        # Set origin to bottom center
        obj.location = (0, 0, config.height / 2)

        return obj

    def create_overhead_gantry(
        self,
        span_width: float = 15.0,
        height: float = 6.0,
        sign_text: str = "I-277 WEST",
        name: str = "Overhead_Gantry",
    ) -> Optional[Object]:
        """
        Create an overhead sign gantry.

        Args:
            span_width: Width between poles
            height: Height to sign
            sign_text: Text to display
            name: Object name

        Returns:
            Blender mesh object (parent with children)
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create parent empty
        gantry = bpy.data.objects.new(name, None)
        gantry.empty_display_type = "PLAIN_AXES"

        # Create left pole
        left_pole = self._create_pole(height, "Gantry_Pole_L")
        left_pole.location = (-span_width / 2, 0, 0)
        left_pole.parent = gantry

        # Create right pole
        right_pole = self._create_pole(height, "Gantry_Pole_R")
        right_pole.location = (span_width / 2, 0, 0)
        right_pole.parent = gantry

        # Create horizontal beam
        beam = self._create_beam(span_width, 0.2, 0.3, "Gantry_Beam")
        beam.location = (0, 0, height)
        beam.parent = gantry

        # Create sign
        sign_config = SignConfig(
            width=min(span_width * 0.8, 8.0),
            height=1.8,
            text=sign_text,
            background_color=(0.1, 0.4, 0.1),
        )
        sign = self.create_sign(SignType.DIRECTIONAL, sign_text, sign_config, "Gantry_Sign")
        if sign:
            sign.location = (0, 0.2, height - 0.9)
            sign.parent = gantry

        return gantry

    def create_exit_sign(
        self,
        exit_number: str = "1A",
        destination: str = "Downtown",
        name: str = "Exit_Sign",
    ) -> Optional[Object]:
        """
        Create an exit sign.

        Args:
            exit_number: Exit number
            destination: Destination text
            name: Object name

        Returns:
            Blender mesh object
        """
        config = SignConfig(
            width=2.4,
            height=2.0,
            text=f"EXIT {exit_number}\n{destination}",
            background_color=(0.1, 0.4, 0.1),
            pole_height=5.0,
        )

        sign = self.create_sign(SignType.EXIT_SIGN, config.text, config, name)

        if sign:
            # Add pole
            pole = self._create_pole(config.pole_height, f"{name}_Pole")
            pole.location = (0, 0, -config.height / 2)

        return sign

    def _create_pole(
        self,
        height: float,
        name: str,
    ) -> Optional[Object]:
        """Create a sign pole."""
        if not BLENDER_AVAILABLE:
            return None

        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.075,
            depth=height,
            location=(0, 0, height / 2),
        )
        pole = bpy.context.active_object
        pole.name = name

        # Apply metal material
        mat = self._get_metal_material()
        if mat:
            pole.data.materials.append(mat)

        return pole

    def _create_beam(
        self,
        length: float,
        height: float,
        depth: float,
        name: str,
    ) -> Optional[Object]:
        """Create a horizontal beam."""
        if not BLENDER_AVAILABLE:
            return None

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        hl, hh, hd = length / 2, height / 2, depth / 2

        v1 = bm.verts.new((-hl, -hd, -hh))
        v2 = bm.verts.new((hl, -hd, -hh))
        v3 = bm.verts.new((hl, hd, -hh))
        v4 = bm.verts.new((-hl, hd, -hh))
        v5 = bm.verts.new((-hl, -hd, hh))
        v6 = bm.verts.new((hl, -hd, hh))
        v7 = bm.verts.new((hl, hd, hh))
        v8 = bm.verts.new((-hl, hd, hh))

        bm.verts.ensure_lookup_table()

        bm.faces.new([v1, v2, v3, v4])
        bm.faces.new([v5, v8, v7, v6])
        bm.faces.new([v1, v5, v6, v2])
        bm.faces.new([v2, v6, v7, v3])
        bm.faces.new([v3, v7, v8, v4])
        bm.faces.new([v4, v8, v5, v1])

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_metal_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _get_sign_material(self, config: SignConfig) -> Optional[Any]:
        """Get or create sign material."""
        if not BLENDER_AVAILABLE:
            return None

        cache_key = f"sign_{config.background_color}"
        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        mat = bpy.data.materials.new("Highway_Sign")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*config.background_color, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.3
            bsdf.inputs["Metallic"].default_value = 0.0

        self._material_cache[cache_key] = mat
        return mat

    def _get_metal_material(self) -> Optional[Any]:
        """Get or create metal material."""
        if not BLENDER_AVAILABLE:
            return None

        if "sign_metal" in self._material_cache:
            return self._material_cache["sign_metal"]

        mat = bpy.data.materials.new("Sign_Metal")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.8
            bsdf.inputs["Roughness"].default_value = 0.4

        self._material_cache["sign_metal"] = mat
        return mat


def create_exit_sign(exit_number: str = "1A") -> Optional[Object]:
    """Convenience function to create an exit sign."""
    generator = SignageGenerator()
    return generator.create_exit_sign(exit_number=exit_number)


def create_overhead_gantry(sign_text: str = "I-277 WEST") -> Optional[Object]:
    """Convenience function to create an overhead gantry."""
    generator = SignageGenerator()
    return generator.create_overhead_gantry(sign_text=sign_text)


__all__ = [
    "SignType",
    "SignConfig",
    "SIGN_CONFIGS",
    "SignageGenerator",
    "create_exit_sign",
    "create_overhead_gantry",
]
