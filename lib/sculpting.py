"""
Sculpting Effects Module - Codified from Tutorial 31

Implements sculpting utilities and effects including detail
enhancement, surface noise, and creature sculpting workflows.

Based on tutorial: CGMatter - Monster/Creature Sculpting Effects (Section 31)

Usage:
    from lib.sculpting import SculptEnhancer, SurfaceNoise, CreatureSculpt

    # Enhance sculpt details
    enhancer = SculptEnhancer(obj)
    enhancer.add_surface_noise(scale=0.5, strength=0.1)
    enhancer.enhance_details(multires_level=4)
"""

from __future__ import annotations
import bpy
from typing import Optional, Tuple, List, Dict
from pathlib import Path


class SculptEnhancer:
    """
    Enhances sculpted models with procedural details.

    Cross-references:
    - KB Section 31: Creature sculpting effects
    """

    def __init__(self, obj: bpy.types.Object):
        self._obj = obj
        self._noise_scale = 0.5
        self._noise_strength = 0.1
        self._detail_level = 4
        self._modifiers: List[bpy.types.Modifier] = []

    @classmethod
    def from_object(cls, obj: bpy.types.Object) -> "SculptEnhancer":
        """
        Create enhancer for object.

        Args:
            obj: Sculpted object to enhance

        Returns:
            Configured SculptEnhancer instance
        """
        return cls(obj)

    def add_surface_noise(
        self,
        scale: float = 0.5,
        strength: float = 0.1,
        seed: int = 42
    ) -> "SculptEnhancer":
        """
        Add procedural surface noise via displacement.

        KB Reference: Section 31 - Surface detail

        Args:
            scale: Noise scale (smaller = finer detail)
            strength: Displacement strength
            seed: Random seed for variation

        Returns:
            Self for chaining
        """
        self._noise_scale = scale
        self._noise_strength = strength

        # Add displacement modifier
        if self._obj.type == 'MESH':
            mod = self._obj.modifiers.new(name="SurfaceNoise", type='DISPLACE')
            mod.strength = strength
            mod.mid_level = 0.5

            # Create noise texture
            tex = bpy.data.textures.new(f"Noise_{self._obj.name}", 'CLOUDS')
            tex.noise_scale = scale
            tex.noise_depth = 2
            tex.seed = seed

            mod.texture = tex
            self._modifiers.append(mod)

        return self

    def enhance_details(self, multires_level: int = 4) -> "SculptEnhancer":
        """
        Enhance details using multiresolution or subdivision.

        KB Reference: Section 31 - Detail enhancement

        Args:
            multires_level: Subdivision level for detail

        Returns:
            Self for chaining
        """
        self._detail_level = multires_level

        # Check for existing multires
        has_multires = any(m.type == 'MULTIRES' for m in self._obj.modifiers)

        if not has_multires:
            # Add subdivision surface for detail
            mod = self._obj.modifiers.new(name="DetailEnhance", type='SUBSURF')
            mod.levels = min(multires_level, 2)  # Viewport
            mod.render_levels = multires_level
            self._modifiers.append(mod)

        return self

    def add_voxel_remesh(
        self,
        voxel_size: float = 0.05,
        adaptivity: float = 0.0
    ) -> "SculptEnhancer":
        """
        Apply voxel remeshing for clean topology.

        KB Reference: Section 31 - Remeshing workflow

        Args:
            voxel_size: Voxel size for remeshing
            adaptivity: Adaptivity value (0 = uniform)

        Returns:
            Self for chaining
        """
        if self._obj.type == 'MESH':
            # Note: Voxel remesh is an operator, not a modifier
            # This sets up the object for remeshing
            self._obj.data.remesh_voxel_size = voxel_size
            self._obj.data.remesh_voxel_adaptivity = adaptivity

        return self

    def apply_smooth(self, iterations: int = 1) -> "SculptEnhancer":
        """
        Apply smooth modifier.

        Args:
            iterations: Smooth iterations

        Returns:
            Self for chaining
        """
        mod = self._obj.modifiers.new(name="Smooth", type='SMOOTH')
        mod.iterations = iterations
        self._modifiers.append(mod)
        return self

    def get_modifiers(self) -> List[bpy.types.Modifier]:
        """Get list of added modifiers."""
        return self._modifiers.copy()


class SurfaceNoise:
    """
    Procedural surface noise generator.

    Cross-references:
    - KB Section 31: Surface detail patterns
    """

    @staticmethod
    def create_noise_texture(
        name: str = "SculptNoise",
        noise_type: str = 'CLOUDS',
        scale: float = 0.5,
        depth: int = 2
    ) -> bpy.types.Texture:
        """
        Create noise texture for sculpting.

        Args:
            name: Texture name
            noise_type: 'CLOUDS', 'DISTORTED_NOISE', 'STUCCI'
            scale: Noise scale
            depth: Noise depth/detail

        Returns:
            Configured texture
        """
        tex = bpy.data.textures.new(name, noise_type)
        tex.noise_scale = scale
        tex.noise_depth = depth
        return tex

    @staticmethod
    def get_noise_presets() -> Dict:
        """Get noise presets for different surfaces."""
        return {
            "skin_pores": {"scale": 0.02, "depth": 3, "type": "CLOUDS"},
            "rough_skin": {"scale": 0.1, "depth": 2, "type": "STUCCI"},
            "bark": {"scale": 0.3, "depth": 4, "type": "DISTORTED_NOISE"},
            "stone": {"scale": 0.5, "depth": 2, "type": "CLOUDS"},
            "scales": {"scale": 0.15, "depth": 1, "type": "STUCCI"}
        }


class CreatureSculpt:
    """
    Creature sculpting workflow utilities.

    Cross-references:
    - KB Section 31: Monster/Creature sculpting
    """

    def __init__(self):
        self._base_mesh: Optional[bpy.types.Object] = None
        self._detail_passes: List[str] = []
        self._symmetry = True
        self._symmetry_axis = 'X'

    @classmethod
    def create(cls, name: str = "Creature") -> "CreatureSculpt":
        """
        Start new creature sculpt.

        Args:
            name: Creature name

        Returns:
            Configured CreatureSculpt instance
        """
        instance = cls()

        # Create base sphere
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
        instance._base_mesh = bpy.context.active_object
        instance._base_mesh.name = name

        return instance

    @classmethod
    def from_base_mesh(cls, obj: bpy.types.Object) -> "CreatureSculpt":
        """
        Start from existing base mesh.

        Args:
            obj: Base mesh object

        Returns:
            Configured CreatureSculpt instance
        """
        instance = cls()
        instance._base_mesh = obj
        return instance

    def enable_symmetry(self, axis: str = 'X') -> "CreatureSculpt":
        """
        Enable sculpting symmetry.

        KB Reference: Section 31 - Symmetric sculpting

        Args:
            axis: Symmetry axis ('X', 'Y', 'Z')

        Returns:
            Self for chaining
        """
        self._symmetry = True
        self._symmetry_axis = axis

        if self._base_mesh:
            # Enable symmetry in sculpt mode settings
            self._base_mesh.use_symmetry_x = (axis == 'X')
            self._base_mesh.use_symmetry_y = (axis == 'Y')
            self._base_mesh.use_symmetry_z = (axis == 'Z')

        return self

    def add_base_shape(self, shape_type: str = 'humanoid') -> "CreatureSculpt":
        """
        Add base shape guide.

        KB Reference: Section 31 - Base shapes

        Args:
            shape_type: 'humanoid', 'quadruped', 'insect', 'custom'

        Returns:
            Self for chaining
        """
        self._detail_passes.append(f"base_{shape_type}")
        return self

    def add_detail_pass(
        self,
        pass_name: str,
        brush_type: str = 'DRAW'
    ) -> "CreatureSculpt":
        """
        Add detail pass to workflow.

        KB Reference: Section 31 - Detail passes

        Args:
            pass_name: Name for this pass
            brush_type: Suggested brush type

        Returns:
            Self for chaining
        """
        self._detail_passes.append(pass_name)
        return self

    def setup_sculpt_brushes(self) -> Dict:
        """
        Get recommended brush setup for creature sculpting.

        KB Reference: Section 31 - Brush recommendations

        Returns:
            Dictionary of brush configurations
        """
        return {
            "base_shape": {
                "brush": "Clay Strips",
                "strength": 0.5,
                "size": 100,
                "use": "Building up major forms"
            },
            "muscle": {
                "brush": "Crease",
                "strength": 0.3,
                "size": 30,
                "use": "Defining muscle separation"
            },
            "skin_detail": {
                "brush": "Skin / Pores",
                "strength": 0.1,
                "size": 5,
                "use": "Surface skin texture"
            },
            "scales": {
                "brush": "Stencil",
                "strength": 0.2,
                "size": 20,
                "use": "Repeating scale patterns"
            },
            "wrinkles": {
                "brush": "Elastic Deform",
                "strength": 0.4,
                "size": 15,
                "use": "Wrinkles and folds"
            },
            "smooth": {
                "brush": "Smooth",
                "strength": 0.3,
                "size": 50,
                "use": "Blending transitions"
            }
        }

    def get_workflow_stages(self) -> List[str]:
        """
        Get creature sculpting workflow stages.

        KB Reference: Section 31 - Workflow order

        Returns:
            List of workflow stages
        """
        return [
            "1. Base Shape - Block out major forms",
            "2. Proportions - Refine silhouette",
            "3. Anatomy - Add muscle and bone structure",
            "4. Secondary Forms - Smaller details",
            "5. Tertiary Details - Surface texture",
            "6. Polish - Smooth and refine"
        ]

    def get_base_mesh(self) -> Optional[bpy.types.Object]:
        """Get the base mesh object."""
        return self._base_mesh


class SculptingTools:
    """
    General sculpting utilities.

    Cross-references:
    - KB Section 31: Sculpting tips
    """

    @staticmethod
    def get_dyntopo_settings(resolution: str = 'medium') -> Dict:
        """
        Get dynamic topology settings.

        KB Reference: Section 31 - Dyntopo workflow

        Args:
            resolution: 'low', 'medium', 'high', 'ultra'

        Returns:
            Settings dictionary
        """
        resolutions = {
            "low": {"detail_size": 0.5, "use": "Blocking out shapes"},
            "medium": {"detail_size": 0.2, "use": "General sculpting"},
            "high": {"detail_size": 0.1, "use": "Detail work"},
            "ultra": {"detail_size": 0.05, "use": "Fine details"}
        }
        return resolutions.get(resolution, resolutions["medium"])

    @staticmethod
    def get_remesh_settings(purpose: str = 'sculpt') -> Dict:
        """
        Get remesh settings.

        KB Reference: Section 31 - Remeshing

        Args:
            purpose: 'sculpt', 'game', 'print', 'animation'

        Returns:
            Settings dictionary
        """
        settings = {
            "sculpt": {
                "voxel_size": 0.05,
                "adaptivity": 0.0,
                "description": "Clean topology for continued sculpting"
            },
            "game": {
                "voxel_size": 0.1,
                "adaptivity": 0.3,
                "description": "Lower poly count for games"
            },
            "print": {
                "voxel_size": 0.02,
                "adaptivity": 0.0,
                "description": "High detail for 3D printing"
            },
            "animation": {
                "voxel_size": 0.05,
                "adaptivity": 0.1,
                "description": "Balanced for deformation"
            }
        }
        return settings.get(purpose, settings["sculpt"])

    @staticmethod
    def get_common_shortcuts() -> Dict:
        """Get common sculpting shortcuts."""
        return {
            "toggle_sculpt": "Ctrl + Tab",
            "increase_brush": "]",
            "decrease_brush": "[",
            "increase_strength": "Shift + ]",
            "decrease_strength": "Shift + [",
            "invert_brush": "Ctrl",
            "smooth": "Shift",
            "add_subdivision": "Ctrl + R (in sculpt)",
            "dyntopo_toggle": "Ctrl + D"
        }


class SculptPresets:
    """
    Preset configurations for sculpting.

    Cross-references:
    - KB Section 31: Creature types
    """

    @staticmethod
    def creature_skin() -> Dict:
        """Creature skin preset."""
        return {
            "noise_scale": 0.1,
            "noise_strength": 0.05,
            "detail_level": 4,
            "description": "Organic creature skin"
        }

    @staticmethod
    def dragon_scales() -> Dict:
        """Dragon scales preset."""
        return {
            "noise_scale": 0.15,
            "noise_strength": 0.1,
            "detail_level": 5,
            "description": "Reptilian scale texture"
        }

    @staticmethod
    def rough_stone() -> Dict:
        """Rough stone preset."""
        return {
            "noise_scale": 0.5,
            "noise_strength": 0.2,
            "detail_level": 3,
            "description": "Rocky, weathered surface"
        }

    @staticmethod
    def alien_flesh() -> Dict:
        """Alien flesh preset."""
        return {
            "noise_scale": 0.08,
            "noise_strength": 0.03,
            "detail_level": 5,
            "description": "Smooth alien skin with subtle detail"
        }


# Convenience functions
def enhance_sculpt(
    obj: bpy.types.Object,
    noise_scale: float = 0.5,
    noise_strength: float = 0.1
) -> SculptEnhancer:
    """Quick sculpt enhancement."""
    enhancer = SculptEnhancer.from_object(obj)
    enhancer.add_surface_noise(noise_scale, noise_strength)
    enhancer.enhance_details()
    return enhancer


def create_creature_base(name: str = "Creature") -> CreatureSculpt:
    """Quick creature base setup."""
    creature = CreatureSculpt.create(name)
    creature.enable_symmetry('X')
    return creature


def get_quick_reference() -> Dict:
    """Get quick reference for sculpting."""
    return {
        "dyntopo_detail": "0.1-0.5 for blocking, 0.05-0.1 for detail",
        "remesh_voxel": "0.05 standard, 0.02 high detail",
        "symmetry": "Enable X-axis for organic creatures",
        "workflow": "Base → Anatomy → Secondary → Tertiary → Polish",
        "smooth_key": "Hold Shift while sculpting"
    }
