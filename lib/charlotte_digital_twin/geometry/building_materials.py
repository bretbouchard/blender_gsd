"""
Building Material System for Charlotte Digital Twin

Maps OSM building tags to appropriate Blender materials.

Usage:
    from lib.charlotte_digital_twin.geometry import BuildingMaterialMapper

    mapper = BuildingMaterialMapper()

    # Get material for building type
    material_name = mapper.get_material_name(BuildingType.OFFICE)

    # Create material in Blender
    material = mapper.create_material(BuildingType.COMMERCIAL)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .types import BuildingType, BuildingFootprint


@dataclass
class BuildingMaterialProperties:
    """Properties for a building material."""
    name: str
    base_color: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)
    roughness: float = 0.5
    metallic: float = 0.0
    transmission: float = 0.0  # For glass
    ior: float = 1.45  # Index of refraction for glass
    texture_scale: float = 1.0


# Material presets by building material
BUILDING_MATERIALS = {
    "concrete": BuildingMaterialProperties(
        name="concrete",
        base_color=(0.55, 0.53, 0.5, 1.0),
        roughness=0.85,
        texture_scale=2.0,
    ),
    "glass": BuildingMaterialProperties(
        name="glass",
        base_color=(0.6, 0.7, 0.8, 0.3),
        roughness=0.05,
        metallic=0.1,
        transmission=0.9,
        ior=1.45,
        texture_scale=1.0,
    ),
    "brick": BuildingMaterialProperties(
        name="brick",
        base_color=(0.6, 0.35, 0.3, 1.0),
        roughness=0.8,
        texture_scale=0.5,
    ),
    "stone": BuildingMaterialProperties(
        name="stone",
        base_color=(0.5, 0.48, 0.45, 1.0),
        roughness=0.75,
        texture_scale=1.0,
    ),
    "metal": BuildingMaterialProperties(
        name="metal",
        base_color=(0.6, 0.6, 0.65, 1.0),
        roughness=0.3,
        metallic=0.9,
        texture_scale=1.0,
    ),
    "wood": BuildingMaterialProperties(
        name="wood",
        base_color=(0.5, 0.35, 0.2, 1.0),
        roughness=0.6,
        texture_scale=0.3,
    ),
    "stucco": BuildingMaterialProperties(
        name="stucco",
        base_color=(0.9, 0.88, 0.85, 1.0),
        roughness=0.9,
        texture_scale=2.0,
    ),
}

# Building type to material mapping
BUILDING_TYPE_MATERIALS = {
    BuildingType.APARTMENTS: ("stucco", {"roughness_add": 0.05}),
    BuildingType.COMMERCIAL: ("glass", {"roughness_add": -0.02}),
    BuildingType.HOUSE: ("brick", {"roughness_add": 0.0}),
    BuildingType.RETAIL: ("glass", {"roughness_add": 0.0}),
    BuildingType.OFFICE: ("glass", {"roughness_add": -0.02}),
    BuildingType.HOTEL: ("glass", {"roughness_add": -0.02}),
    BuildingType.SCHOOL: ("brick", {"roughness_add": 0.1}),
    BuildingType.HOSPITAL: ("concrete", {"roughness_add": 0.1}),
    BuildingType.CHURCH: ("stone", {"roughness_add": 0.05}),
    BuildingType.INDUSTRIAL: ("metal", {"roughness_add": 0.1}),
    BuildingType.WAREHOUSE: ("metal", {"roughness_add": 0.15}),
    BuildingType.PARKING: ("concrete", {"roughness_add": 0.2}),
    BuildingType.STADIUM: ("concrete", {"roughness_add": 0.1}),
    BuildingType.CIVIC: ("stone", {"roughness_add": 0.0}),
    BuildingType.GOVERNMENT: ("stone", {"roughness_add": -0.05}),
    BuildingType.UNIVERSITY: ("brick", {"roughness_add": 0.05}),
    BuildingType.COLLEGE: ("brick", {"roughness_add": 0.05}),
}


class BuildingMaterialMapper:
    """
    Maps OSM building properties to Blender materials.

    Features:
    - Material type detection from OSM tags
    - Building type adjustments
    - Glass material support for windows
    - Material property caching
    """

    def __init__(self):
        """Initialize material mapper."""
        self._material_cache: Dict[str, Any] = {}
        self._blender_available = False
        self._bpy = None
        try:
            import bpy
            self._bpy = bpy
            self._blender_available = True
        except ImportError:
            pass

    def get_material_name(
        self,
        building_type: BuildingType,
        building_material: Optional[str] = None,
    ) -> str:
        """
        Get material name for building type and material.

        Args:
            building_type: Type of building
            building_material: Material from OSM tags

        Returns:
            Material name string
        """
        # If material specified in tags, use it
        if building_material and building_material in BUILDING_MATERIALS:
            base_name = building_material
        else:
            # Use building type mapping
            base_mat, _ = BUILDING_TYPE_MATERIALS.get(
                building_type,
                ("concrete", {})
            )
            base_name = base_mat

        return f"building_{base_name}"

    def get_material_properties(
        self,
        building_type: BuildingType,
        building_material: Optional[str] = None,
    ) -> BuildingMaterialProperties:
        """
        Get full material properties for building.

        Args:
            building_type: Type of building
            building_material: Material from OSM tags

        Returns:
            BuildingMaterialProperties object
        """
        # Get base material
        if building_material and building_material in BUILDING_MATERIALS:
            base_props = BUILDING_MATERIALS[building_material]
            adjustments = {}
        else:
            base_name, adjustments = BUILDING_TYPE_MATERIALS.get(
                building_type,
                ("concrete", {})
            )
            base_props = BUILDING_MATERIALS[base_name]

        # Apply adjustments
        roughness_add = adjustments.get("roughness_add", 0.0)

        return BuildingMaterialProperties(
            name=f"building_{base_props.name}",
            base_color=base_props.base_color,
            roughness=max(0.0, min(1.0, base_props.roughness + roughness_add)),
            metallic=base_props.metallic,
            transmission=base_props.transmission,
            ior=base_props.ior,
            texture_scale=base_props.texture_scale,
        )

    def create_material(
        self,
        building_type: BuildingType,
        building_material: Optional[str] = None,
        material_name: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Create Blender material for building.

        Args:
            building_type: Type of building
            building_material: Material from OSM tags
            material_name: Override material name

        Returns:
            Blender material or None
        """
        if not self._blender_available:
            return None

        props = self.get_material_properties(building_type, building_material)
        name = material_name or props.name

        # Check cache
        if name in self._material_cache:
            return self._material_cache[name]

        # Check if material exists
        if name in self._bpy.data.materials:
            self._material_cache[name] = self._bpy.data.materials[name]
            return self._material_cache[name]

        # Create new material
        mat = self._bpy.data.materials.new(name=name)
        mat.use_nodes = True

        # Get node tree
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create Principled BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)

        # Set properties
        bsdf.inputs["Base Color"].default_value = props.base_color
        bsdf.inputs["Roughness"].default_value = props.roughness
        bsdf.inputs["Metallic"].default_value = props.metallic

        # Glass properties
        if props.transmission > 0:
            bsdf.inputs["Transmission"].default_value = props.transmission
            bsdf.inputs["IOR"].default_value = props.ior

        # Create Material Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (300, 0)

        # Link nodes
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Cache and return
        self._material_cache[name] = mat
        return mat

    def apply_material_to_building(
        self,
        blender_obj: Any,
        footprint: BuildingFootprint,
    ) -> bool:
        """
        Apply appropriate material to a building mesh.

        Args:
            blender_obj: Blender mesh object
            footprint: BuildingFootprint with metadata

        Returns:
            True if material applied successfully
        """
        if not self._blender_available:
            return False

        # Get building material from tags
        building_material = footprint.tags.get("building:material")

        # Create material
        mat = self.create_material(
            building_type=footprint.building_type,
            building_material=building_material,
        )

        if mat is None:
            return False

        # Apply to object
        if blender_obj.data.materials:
            blender_obj.data.materials[0] = mat
        else:
            blender_obj.data.materials.append(mat)

        return True

    def get_material_from_tags(self, tags: Dict[str, str]) -> str:
        """
        Determine building material from OSM tags.

        Args:
            tags: OSM way tags

        Returns:
            Material type string
        """
        # Direct material tag
        if "building:material" in tags:
            return tags["building:material"]

        # Check building:facade
        facade = tags.get("building:facade", "")
        if "glass" in facade.lower():
            return "glass"
        elif "concrete" in facade.lower():
            return "concrete"
        elif "brick" in facade.lower():
            return "brick"
        elif "stone" in facade.lower():
            return "stone"
        elif "metal" in facade.lower():
            return "metal"

        # Default
        return "concrete"

    def create_glass_material(
        self,
        tint: Tuple[float, float, float] = (0.6, 0.7, 0.8),
        name: str = "building_glass_tinted",
    ) -> Optional[Any]:
        """
        Create a tinted glass material for windows.

        Args:
            tint: RGB tint color
            name: Material name

        Returns:
            Blender material or None
        """
        if not self._blender_available:
            return None

        if name in self._material_cache:
            return self._material_cache[name]

        if name in self._bpy.data.materials:
            self._material_cache[name] = self._bpy.data.materials[name]
            return self._material_cache[name]

        mat = self._bpy.data.materials.new(name=name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Glass BSDF
        glass = nodes.new("ShaderNodeBsdfGlass")
        glass.inputs["Color"].default_value = (*tint, 1.0)
        glass.inputs["Roughness"].default_value = 0.02
        glass.inputs["IOR"].default_value = 1.45

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (300, 0)

        links.new(glass.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache[name] = mat
        return mat


__all__ = [
    "BuildingMaterialMapper",
    "BuildingMaterialProperties",
    "BUILDING_MATERIALS",
    "BUILDING_TYPE_MATERIALS",
]
