"""
Road Material System for Charlotte Digital Twin

Maps OSM road tags to appropriate Blender materials.

Usage:
    from lib.charlotte_digital_twin.geometry import RoadMaterialMapper

    mapper = RoadMaterialMapper()

    # Get material for road type
    material_name = mapper.get_material_name(RoadType.PRIMARY, surface="asphalt")

    # Create material in Blender
    material = mapper.create_material(RoadType.RESIDENTIAL)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .types import RoadType, RoadSegment


@dataclass
class MaterialProperties:
    """Properties for a road material."""
    name: str
    base_color: Tuple[float, float, float, float] = (0.15, 0.15, 0.15, 1.0)
    roughness: float = 0.8
    metallic: float = 0.0
    normal_strength: float = 1.0
    texture_scale: float = 1.0


# Material presets by surface type
SURFACE_MATERIALS = {
    "asphalt": MaterialProperties(
        name="asphalt",
        base_color=(0.12, 0.12, 0.12, 1.0),
        roughness=0.85,
        texture_scale=2.0,
    ),
    "concrete": MaterialProperties(
        name="concrete",
        base_color=(0.45, 0.45, 0.45, 1.0),
        roughness=0.7,
        texture_scale=4.0,
    ),
    "gravel": MaterialProperties(
        name="gravel",
        base_color=(0.5, 0.45, 0.4, 1.0),
        roughness=0.95,
        texture_scale=1.0,
    ),
    "paving_stones": MaterialProperties(
        name="paving_stones",
        base_color=(0.4, 0.38, 0.35, 1.0),
        roughness=0.75,
        texture_scale=0.5,
    ),
    "sett": MaterialProperties(
        name="cobblestone",
        base_color=(0.35, 0.32, 0.3, 1.0),
        roughness=0.8,
        texture_scale=0.3,
    ),
    "cobblestone": MaterialProperties(
        name="cobblestone",
        base_color=(0.35, 0.32, 0.3, 1.0),
        roughness=0.85,
        texture_scale=0.3,
    ),
    "unpaved": MaterialProperties(
        name="dirt",
        base_color=(0.45, 0.35, 0.25, 1.0),
        roughness=0.95,
        texture_scale=3.0,
    ),
    "dirt": MaterialProperties(
        name="dirt",
        base_color=(0.45, 0.35, 0.25, 1.0),
        roughness=0.95,
        texture_scale=3.0,
    ),
    "grass": MaterialProperties(
        name="grass_path",
        base_color=(0.3, 0.45, 0.2, 1.0),
        roughness=0.9,
        texture_scale=1.0,
    ),
    "sand": MaterialProperties(
        name="sand",
        base_color=(0.76, 0.7, 0.5, 1.0),
        roughness=0.95,
        texture_scale=2.0,
    ),
    "wood": MaterialProperties(
        name="wood",
        base_color=(0.4, 0.3, 0.2, 1.0),
        roughness=0.6,
        texture_scale=0.2,
    ),
    "metal": MaterialProperties(
        name="metal_deck",
        base_color=(0.5, 0.5, 0.55, 1.0),
        roughness=0.4,
        metallic=0.8,
        texture_scale=1.0,
    ),
}

# Road type adjustments
ROAD_TYPE_ADJUSTMENTS = {
    RoadType.MOTORWAY: {"roughness_add": -0.05, "name_suffix": "_highway"},
    RoadType.MOTORWAY_LINK: {"roughness_add": -0.05, "name_suffix": "_highway"},
    RoadType.TRUNK: {"roughness_add": -0.05, "name_suffix": "_main"},
    RoadType.TRUNK_LINK: {"roughness_add": -0.05, "name_suffix": "_main"},
    RoadType.PRIMARY: {"roughness_add": 0.0, "name_suffix": "_main"},
    RoadType.PRIMARY_LINK: {"roughness_add": 0.0, "name_suffix": "_main"},
    RoadType.SECONDARY: {"roughness_add": 0.05, "name_suffix": "_secondary"},
    RoadType.SECONDARY_LINK: {"roughness_add": 0.05, "name_suffix": "_secondary"},
    RoadType.TERTIARY: {"roughness_add": 0.1, "name_suffix": "_local"},
    RoadType.TERTIARY_LINK: {"roughness_add": 0.1, "name_suffix": "_local"},
    RoadType.RESIDENTIAL: {"roughness_add": 0.15, "name_suffix": "_residential"},
    RoadType.SERVICE: {"roughness_add": 0.2, "name_suffix": "_service"},
    RoadType.UNCLASSIFIED: {"roughness_add": 0.2, "name_suffix": "_unclassified"},
    RoadType.PEDESTRIAN: {"roughness_add": 0.1, "name_suffix": "_pedestrian"},
    RoadType.FOOTWAY: {"roughness_add": 0.15, "name_suffix": "_footway"},
    RoadType.CYCLEWAY: {"roughness_add": 0.1, "name_suffix": "_cycle"},
    RoadType.PATH: {"roughness_add": 0.25, "name_suffix": "_path"},
    RoadType.TRACK: {"roughness_add": 0.25, "name_suffix": "_track"},
    RoadType.STEPS: {"roughness_add": 0.1, "name_suffix": "_steps"},
}


class RoadMaterialMapper:
    """
    Maps OSM road properties to Blender materials.

    Features:
    - Surface type detection from OSM tags
    - Road type adjustments
    - Material creation in Blender
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
        road_type: RoadType,
        surface: Optional[str] = None,
    ) -> str:
        """
        Get material name for road type and surface.

        Args:
            road_type: Type of road
            surface: Surface type from OSM tags

        Returns:
            Material name string
        """
        # Get base surface
        surface = surface or "asphalt"
        base_props = SURFACE_MATERIALS.get(surface, SURFACE_MATERIALS["asphalt"])

        # Get road type adjustments
        adjustments = ROAD_TYPE_ADJUSTMENTS.get(road_type, {})
        suffix = adjustments.get("name_suffix", "")

        return f"{base_props.name}{suffix}"

    def get_material_properties(
        self,
        road_type: RoadType,
        surface: Optional[str] = None,
    ) -> MaterialProperties:
        """
        Get full material properties for road.

        Args:
            road_type: Type of road
            surface: Surface type from OSM tags

        Returns:
            MaterialProperties object
        """
        # Get base surface
        surface = surface or "asphalt"
        base_props = SURFACE_MATERIALS.get(surface, SURFACE_MATERIALS["asphalt"])

        # Get adjustments
        adjustments = ROAD_TYPE_ADJUSTMENTS.get(road_type, {})
        roughness_add = adjustments.get("roughness_add", 0.0)
        suffix = adjustments.get("name_suffix", "")

        # Create adjusted properties
        return MaterialProperties(
            name=f"{base_props.name}{suffix}",
            base_color=base_props.base_color,
            roughness=max(0.0, min(1.0, base_props.roughness + roughness_add)),
            metallic=base_props.metallic,
            normal_strength=base_props.normal_strength,
            texture_scale=base_props.texture_scale,
        )

    def create_material(
        self,
        road_type: RoadType,
        surface: Optional[str] = None,
        material_name: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Create Blender material for road.

        Args:
            road_type: Type of road
            surface: Surface type from OSM tags
            material_name: Override material name

        Returns:
            Blender material or None
        """
        if not self._blender_available:
            return None

        props = self.get_material_properties(road_type, surface)
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

        # Create Material Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (300, 0)

        # Link nodes
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Cache and return
        self._material_cache[name] = mat
        return mat

    def apply_material_to_segment(
        self,
        blender_obj: Any,
        segment: RoadSegment,
    ) -> bool:
        """
        Apply appropriate material to a road segment mesh.

        Args:
            blender_obj: Blender mesh object
            segment: RoadSegment with metadata

        Returns:
            True if material applied successfully
        """
        if not self._blender_available:
            return False

        # Get or create material
        mat = self.create_material(
            road_type=segment.road_type,
            surface=segment.surface,
        )

        if mat is None:
            return False

        # Apply to object
        if blender_obj.data.materials:
            blender_obj.data.materials[0] = mat
        else:
            blender_obj.data.materials.append(mat)

        return True

    def create_materials_for_types(
        self,
        road_types: List[RoadType],
        surfaces: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create materials for multiple road types.

        Args:
            road_types: List of road types
            surfaces: Optional list of surface types

        Returns:
            Dictionary mapping material names to materials
        """
        materials = {}
        surfaces = surfaces or ["asphalt"]

        for road_type in road_types:
            for surface in surfaces:
                mat = self.create_material(road_type, surface)
                if mat:
                    materials[mat.name] = mat

        return materials

    def get_surface_from_tags(self, tags: Dict[str, str]) -> str:
        """
        Determine surface type from OSM tags.

        Args:
            tags: OSM way tags

        Returns:
            Surface type string
        """
        # Direct surface tag
        if "surface" in tags:
            return tags["surface"]

        # Infer from tracktype
        tracktype = tags.get("tracktype", "")
        if tracktype:
            if tracktype in ["grade1"]:
                return "asphalt"
            elif tracktype in ["grade2"]:
                return "gravel"
            elif tracktype in ["grade3", "grade4", "grade5"]:
                return "dirt"

        # Infer from highway type
        highway = tags.get("highway", "")
        if highway in ["footway", "pedestrian", "steps"]:
            return "concrete"
        elif highway in ["path", "track"]:
            return "dirt"
        elif highway in ["cycleway"]:
            return "asphalt"

        # Default
        return "asphalt"


__all__ = [
    "RoadMaterialMapper",
    "MaterialProperties",
    "SURFACE_MATERIALS",
    "ROAD_TYPE_ADJUSTMENTS",
]
