"""
Shader Raycast System Module - Codified from Tutorials 1, 18

Implements Blender 5.1+ Raycast node patterns for proximity effects,
contact shadows, edge wear, and material layering in shaders.

Based on tutorials:
- DECODED: Blender 5.1 New Features (Section 1)
- Default Cube: Material Layering Beyond Roughness (Section 18)

Usage:
    from lib.raycast import ShaderRaycast, RaycastPresets

    # Create proximity AO material
    raycast = ShaderRaycast.create_material("ProximityAO")
    raycast.set_source_object(other_object)
    raycast.set_max_distance(0.5)
    raycast.use_is_hit_for_ao()
    mat = raycast.build()

    # Or use preset
    mat = RaycastPresets.edge_wear(wear_color=(0.8, 0.6, 0.4))
"""

from __future__ import annotations
import bpy
from typing import Optional, Tuple
from pathlib import Path


class ShaderRaycast:
    """
    Shader-based raycast system using Blender 5.1+ Raycast node.

    Creates materials that react to:
    - Object proximity (Is Hit)
    - Distance to other surfaces (Hit Distance)
    - Surface contact (Self Hit)
    - Hit position for effects

    Cross-references:
    - KB Section 1: Raycast Node in Shader Editor (DECODED)
    - KB Section 18: Material Layering Beyond Roughness (Default Cube)
    """

    def __init__(self):
        self._material: Optional[bpy.types.Material] = None
        self._source_object: Optional[bpy.types.Object] = None
        self._max_distance = 1.0
        self._base_color = (0.5, 0.5, 0.5, 1.0)
        self._hit_color = (1.0, 1.0, 1.0, 1.0)
        self._use_is_hit = False
        self._use_distance = False
        self._use_self_hit = False
        self._nodes: dict = {}

    @classmethod
    def create_material(cls, name: str = "RaycastMaterial") -> "ShaderRaycast":
        """
        Create a new material with raycast setup.

        Args:
            name: Material name

        Returns:
            Configured ShaderRaycast instance
        """
        instance = cls()
        instance._material = bpy.data.materials.new(name=name)
        instance._material.use_nodes = True
        return instance

    def set_source_object(self, obj: bpy.types.Object) -> "ShaderRaycast":
        """
        Set the object that emits rays.

        Args:
            obj: Source object for ray emission
        """
        self._source_object = obj
        return self

    def set_max_distance(self, distance: float) -> "ShaderRaycast":
        """
        Set maximum ray travel distance.

        Args:
            distance: Maximum distance in meters
        """
        self._max_distance = distance
        return self

    def set_colors(
        self,
        base: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0),
        hit: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    ) -> "ShaderRaycast":
        """
        Set base and hit colors.

        Args:
            base: RGBA color when not hit
            hit: RGBA color when ray hits
        """
        self._base_color = base
        self._hit_color = hit
        return self

    def use_is_hit_for_ao(self) -> "ShaderRaycast":
        """Use Is Hit output for real-time AO effect."""
        self._use_is_hit = True
        return self

    def use_distance_for_gradient(self) -> "ShaderRaycast":
        """Use Hit Distance for gradient effect."""
        self._use_distance = True
        return self

    def use_self_hit_for_cavity(self) -> "ShaderRaycast":
        """Use Self Hit for cavity/crevice detection."""
        self._use_self_hit = True
        return self

    def build(self) -> bpy.types.Material:
        """
        Build the material with raycast nodes.

        KB Reference: Section 1 - Raycast Node in Shader Editor

        Returns:
            Configured material
        """
        if not self._material:
            raise RuntimeError("Call create_material() first")

        nodes = self._material.node_tree.nodes
        links = self._material.node_tree.links

        # Clear existing nodes
        nodes.clear()

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)
        self._nodes['output'] = output

        # === PRINCIPLED BSDF ===
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (600, 0)
        self._nodes['bsdf'] = bsdf

        # === RAYCAST NODE (Blender 5.1+) ===
        # KB Reference: Section 1 - Raycast node outputs
        raycast = nodes.new('ShaderNodeRaycast')
        raycast.location = (0, 0)
        raycast.inputs["Length"].default_value = self._max_distance
        self._nodes['raycast'] = raycast

        # === OBJECT INFO FOR SOURCE ===
        if self._source_object:
            obj_info = nodes.new('ShaderNodeObjectInfo')
            obj_info.location = (-200, 100)
            # Link object (would need driver or manual setup)
            self._nodes['obj_info'] = obj_info

        # === PROCESS RAYCAST OUTPUTS ===
        x = 200

        if self._use_is_hit:
            # Is Hit → Mix Color Factor
            # KB Reference: Section 1 - Is Hit for visibility detection
            color_ramp = nodes.new('ShaderNodeValToRGB')
            color_ramp.location = (x, 100)
            links.new(raycast.outputs["Is Hit"], color_ramp.inputs["Fac"])
            self._nodes['color_ramp'] = color_ramp

            # Mix colors based on hit
            mix_color = nodes.new('ShaderNodeMix')
            mix_color.data_type = 'RGBA'
            mix_color.location = (x + 200, 0)
            links.new(color_ramp.outputs["Color"], mix_color.inputs["Factor"])

            # Base color input
            base_rgb = nodes.new('ShaderNodeRGB')
            base_rgb.outputs[0].default_value = self._base_color
            base_rgb.location = (x, 200)

            # Hit color input
            hit_rgb = nodes.new('ShaderNodeRGB')
            hit_rgb.outputs[0].default_value = self._hit_color
            hit_rgb.location = (x, -100)

            links.new(base_rgb.outputs[0], mix_color.inputs[6])
            links.new(hit_rgb.outputs[0], mix_color.inputs[7])

            # Link to BSDF
            links.new(mix_color.outputs[2], bsdf.inputs["Base Color"])

            self._nodes['mix_color'] = mix_color
            x += 400

        elif self._use_distance:
            # Hit Distance → Map Range → Effect
            # KB Reference: Section 1 - Hit Distance for proximity effects
            map_range = nodes.new('ShaderNodeMapRange')
            map_range.location = (x, 0)
            map_range.inputs["From Min"].default_value = 0.0
            map_range.inputs["From Max"].default_value = self._max_distance
            map_range.inputs["To Min"].default_value = 0.0
            map_range.inputs["To Max"].default_value = 1.0
            links.new(raycast.outputs["Hit Distance"], map_range.inputs["Value"])
            self._nodes['map_range'] = map_range

            # Use distance as mix factor
            mix_color = nodes.new('ShaderNodeMix')
            mix_color.data_type = 'RGBA'
            mix_color.location = (x + 200, 0)
            links.new(map_range.outputs[0], mix_color.inputs["Factor"])

            base_rgb = nodes.new('ShaderNodeRGB')
            base_rgb.outputs[0].default_value = self._base_color
            base_rgb.location = (x, 150)

            hit_rgb = nodes.new('ShaderNodeRGB')
            hit_rgb.outputs[0].default_value = self._hit_color
            hit_rgb.location = (x, -100)

            links.new(base_rgb.outputs[0], mix_color.inputs[6])
            links.new(hit_rgb.outputs[0], mix_color.inputs[7])
            links.new(mix_color.outputs[2], bsdf.inputs["Base Color"])

            self._nodes['mix_color'] = mix_color
            x += 400

        elif self._use_self_hit:
            # Self Hit → Cavity detection
            # KB Reference: Section 1 - Self Hit for crevice detection
            self_hit_ramp = nodes.new('ShaderNodeValToRGB')
            self_hit_ramp.location = (x, 0)
            links.new(raycast.outputs["Self Hit"], self_hit_ramp.inputs["Fac"])
            self._nodes['self_hit_ramp'] = self_hit_ramp

            # Darken in cavities
            mix_color = nodes.new('ShaderNodeMix')
            mix_color.data_type = 'RGBA'
            mix_color.location = (x + 200, 0)
            links.new(self_hit_ramp.outputs["Color"], mix_color.inputs["Factor"])

            base_rgb = nodes.new('ShaderNodeRGB')
            base_rgb.outputs[0].default_value = self._base_color
            base_rgb.location = (x, 150)

            cavity_rgb = nodes.new('ShaderNodeRGB')
            cavity_rgb.outputs[0].default_value = (0.1, 0.1, 0.1, 1.0)
            cavity_rgb.location = (x, -100)

            links.new(base_rgb.outputs[0], mix_color.inputs[6])
            links.new(cavity_rgb.outputs[0], mix_color.inputs[7])
            links.new(mix_color.outputs[2], bsdf.inputs["Base Color"])

            self._nodes['mix_color'] = mix_color
            x += 400

        else:
            # Default: just use base color
            base_rgb = nodes.new('ShaderNodeRGB')
            base_rgb.outputs[0].default_value = self._base_color
            base_rgb.location = (x, 0)
            links.new(base_rgb.outputs[0], bsdf.inputs["Base Color"])

        # === LINK TO OUTPUT ===
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        return self._material


class RaycastPresets:
    """
    Preset configurations for common raycast effects.

    Cross-references:
    - KB Section 1: Raycast node outputs
    - KB Section 18: Material layering
    """

    @staticmethod
    def proximity_ao(
        name: str = "ProximityAO",
        max_distance: float = 0.5
    ) -> bpy.types.Material:
        """
        Create real-time ambient occlusion using raycast.

        KB Reference: Section 1 - Proximity AO

        Args:
            name: Material name
            max_distance: AO radius

        Returns:
            Configured material
        """
        raycast = ShaderRaycast.create_material(name)
        raycast.set_max_distance(max_distance)
        raycast.set_colors(
            base=(1.0, 1.0, 1.0, 1.0),
            hit=(0.3, 0.3, 0.3, 1.0)
        )
        raycast.use_is_hit_for_ao()
        return raycast.build()

    @staticmethod
    def edge_wear(
        name: str = "EdgeWear",
        wear_color: Tuple[float, float, float] = (0.8, 0.6, 0.4),
        base_color: Tuple[float, float, float] = (0.3, 0.3, 0.35),
        max_distance: float = 0.2
    ) -> bpy.types.Material:
        """
        Create edge wear effect using raycast proximity.

        KB Reference: Section 1, 18 - Edge wear with raycast

        Args:
            name: Material name
            wear_color: RGB color for worn edges
            base_color: RGB color for base material
            max_distance: Wear detection distance

        Returns:
            Configured material
        """
        raycast = ShaderRaycast.create_material(name)
        raycast.set_max_distance(max_distance)
        raycast.set_colors(
            base=(*base_color, 1.0),
            hit=(*wear_color, 1.0)
        )
        raycast.use_distance_for_gradient()
        return raycast.build()

    @staticmethod
    def contact_shadows(
        name: str = "ContactShadows",
        shadow_intensity: float = 0.7,
        max_distance: float = 0.3
    ) -> bpy.types.Material:
        """
        Create contact shadows using raycast.

        KB Reference: Section 1 - Contact shadows

        Args:
            name: Material name
            shadow_intensity: Shadow darkness (0-1)
            max_distance: Shadow detection distance

        Returns:
            Configured material
        """
        shadow_color = (1.0 - shadow_intensity,) * 3
        raycast = ShaderRaycast.create_material(name)
        raycast.set_max_distance(max_distance)
        raycast.set_colors(
            base=(1.0, 1.0, 1.0, 1.0),
            hit=(*shadow_color, 1.0)
        )
        raycast.use_is_hit_for_ao()
        return raycast.build()

    @staticmethod
    def cavity_detection(
        name: str = "CavityDetection",
        cavity_color: Tuple[float, float, float] = (0.1, 0.08, 0.05),
        base_color: Tuple[float, float, float] = (0.6, 0.6, 0.6)
    ) -> bpy.types.Material:
        """
        Create cavity/crevice detection material.

        KB Reference: Section 1 - Self Hit for cavity detection

        Args:
            name: Material name
            cavity_color: RGB color for cavities
            base_color: RGB color for flat surfaces

        Returns:
            Configured material
        """
        raycast = ShaderRaycast.create_material(name)
        raycast.set_colors(
            base=(*base_color, 1.0),
            hit=(*cavity_color, 1.0)
        )
        raycast.use_self_hit_for_cavity()
        return raycast.build()

    @staticmethod
    def color_bleeding(
        name: str = "ColorBleeding",
        bleed_color: Tuple[float, float, float] = (1.0, 0.3, 0.2),
        max_distance: float = 0.5
    ) -> bpy.types.Material:
        """
        Create color bleeding effect from nearby objects.

        KB Reference: Section 1 - Hit Position for color bleeding

        Args:
            name: Material name
            bleed_color: RGB color to bleed onto surface
            max_distance: Bleeding distance

        Returns:
            Configured material
        """
        raycast = ShaderRaycast.create_material(name)
        raycast.set_max_distance(max_distance)
        raycast.set_colors(
            base=(0.8, 0.8, 0.8, 1.0),
            hit=(*bleed_color, 0.5)  # Semi-transparent blend
        )
        raycast.use_distance_for_gradient()
        return raycast.build()


class MaterialLayering:
    """
    Proper material layering (not just roughness manipulation).

    Cross-references:
    - KB Section 18: Material Layering Beyond Roughness
    """

    @staticmethod
    def create_layered_material(
        name: str = "LayeredMaterial",
        base_ior: float = 1.45,
        contaminant_ior: float = 1.47,  # Oil IOR
        contaminant_mask: Optional[str] = None
    ) -> bpy.types.Material:
        """
        Create properly layered material (fingerprints over glass).

        KB Reference: Section 18 - Fingerprints come OVER reflections

        Args:
            name: Material name
            base_ior: Base material IOR
            contaminant_ior: Contaminant layer IOR (oil, water, etc.)
            contaminant_mask: Name of mask attribute

        Returns:
            Configured layered material
        """
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.node_tree.links

        nodes.clear()

        # Output
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        # Mix shader for layering
        mix_shader = nodes.new('ShaderNodeMixShader')
        mix_shader.location = (600, 0)

        # Base BSDF (glass)
        base_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        base_bsdf.location = (400, 100)
        base_bsdf.inputs["IOR"].default_value = base_ior
        base_bsdf.inputs["Transmission Weight"].default_value = 1.0

        # Contaminant BSDF (oil/fingerprint)
        contaminant_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        contaminant_bsdf.location = (400, -100)
        contaminant_bsdf.inputs["IOR"].default_value = contaminant_ior
        contaminant_bsdf.inputs["Roughness"].default_value = 0.1  # Low, not high!

        # Mask input (attribute or texture)
        if contaminant_mask:
            attr = nodes.new('ShaderNodeAttribute')
            attr.attribute_name = contaminant_mask
            attr.location = (200, 0)
            links.new(attr.outputs["Fac"], mix_shader.inputs["Fac"])

        # Link
        links.new(base_bsdf.outputs["BSDF"], mix_shader.inputs[1])
        links.new(contaminant_bsdf.outputs["BSDF"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])

        return mat

    @staticmethod
    def get_layering_rules() -> dict:
        """Get proper material layering rules."""
        return {
            "fingerprints": {
                "wrong": "Use roughness map",
                "correct": "Layer with different IOR material",
                "behavior": "Darken, don't blur reflections"
            },
            "oil_stains": {
                "wrong": "Roughness increase",
                "correct": "Different IOR layer",
                "behavior": "Slight reflection change"
            },
            "dust": {
                "wrong": "Roughness map",
                "correct": "Semi-transparent coat layer",
                "behavior": "Light scattering on top"
            },
            "water_spots": {
                "wrong": "Roughness map",
                "correct": "Refraction layer",
                "behavior": "Lens effect on surface"
            }
        }


# Convenience functions
def create_proximity_ao(distance: float = 0.5) -> bpy.types.Material:
    """Quick create proximity AO material."""
    return RaycastPresets.proximity_ao(max_distance=distance)


def create_edge_wear(
    wear_color: Tuple[float, float, float] = (0.8, 0.6, 0.4)
) -> bpy.types.Material:
    """Quick create edge wear material."""
    return RaycastPresets.edge_wear(wear_color=wear_color)


def create_contact_shadows(intensity: float = 0.7) -> bpy.types.Material:
    """Quick create contact shadows material."""
    return RaycastPresets.contact_shadows(shadow_intensity=intensity)
