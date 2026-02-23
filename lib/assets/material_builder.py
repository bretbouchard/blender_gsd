"""
PBR Material Builder for KitBash3D and similar assets.

Builds Principled BSDF materials from texture maps following
standard PBR naming conventions.

Supported texture suffixes:
- basecolor, diffuse, albedo -> Base Color
- roughness -> Roughness
- metallic -> Metallic
- normal -> Normal Map
- height, bump -> Bump/Displacement
- ao, ambient_occlusion -> Ambient Occlusion
- specular -> Specular
- glossiness -> Roughness (inverted)
- emission -> Emission
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Material, Node, ShaderNodeTree


@dataclass
class TextureSet:
    """Collection of PBR textures for a single material."""

    name: str
    """Base name of the material/texture set."""

    basecolor: Path | None = None
    """Base color/albedo map."""

    roughness: Path | None = None
    """Roughness map."""

    metallic: Path | None = None
    """Metallic map."""

    normal: Path | None = None
    """Normal map."""

    height: Path | None = None
    """Height/bump map."""

    ao: Path | None = None
    """Ambient occlusion map."""

    specular: Path | None = None
    """Specular map."""

    glossiness: Path | None = None
    """Glossiness map (inverted roughness)."""

    emission: Path | None = None
    """Emission map."""

    opacity: Path | None = None
    """Opacity/alpha map."""

    def has_textures(self) -> bool:
        """Check if any textures are assigned."""
        return any([
            self.basecolor,
            self.roughness,
            self.metallic,
            self.normal,
            self.height,
            self.ao,
            self.specular,
            self.glossiness,
            self.emission,
            self.opacity,
        ])


# Texture suffix patterns for detection
TEXTURE_PATTERNS = {
    "basecolor": [
        r"_basecolor",
        r"_base_color",
        r"_albedo",
        r"_diffuse",
        r"_color",
        r"_col",
    ],
    "roughness": [
        r"_roughness",
        r"_rough",
    ],
    "metallic": [
        r"_metallic",
        r"_metal",
        r"_metalness",
    ],
    "normal": [
        r"_normal",
        r"_nrm",
        r"_norm",
    ],
    "height": [
        r"_height",
        r"_bump",
        r"_disp",
        r"_displacement",
    ],
    "ao": [
        r"_ao",
        r"_ambient_occlusion",
        r"_ambientocclusion",
        r"_occlusion",
    ],
    "specular": [
        r"_specular",
        r"_spec",
        r"_spcular",
    ],
    "glossiness": [
        r"_glossiness",
        r"_gloss",
        r"_glossy",
    ],
    "emission": [
        r"_emission",
        r"_emissive",
        r"_glow",
        r"_light",
    ],
    "opacity": [
        r"_opacity",
        r"_alpha",
        r"_mask",
    ],
}


@dataclass
class MaterialBuildResult:
    """Result of material building operation."""

    material: Material | None = None
    """Created material."""

    texture_set: TextureSet | None = None
    """Detected texture set."""

    warnings: list[str] = field(default_factory=list)
    """Non-fatal issues encountered."""

    errors: list[str] = field(default_factory=list)
    """Fatal errors that prevented material creation."""


class PBRMaterialBuilder:
    """
    Builds Principled BSDF materials from PBR texture sets.

    Detects texture types from naming conventions and creates
    properly connected node setups.

    Example:
        >>> builder = PBRMaterialBuilder()
        >>> result = builder.build_from_textures("metal_01", texture_dir)
        >>> if result.material:
        ...     print(f"Created: {result.material.name}")
    """

    def __init__(self):
        """Initialize the material builder."""
        self._texture_cache: dict[str, TextureSet] = {}

    def detect_texture_set(
        self,
        material_name: str,
        texture_dir: Path,
        recursive: bool = False,
    ) -> TextureSet:
        """
        Detect all textures for a material in a directory.

        Args:
            material_name: Base name to search for (e.g., "assetsA", "bricksA")
            texture_dir: Directory containing texture files
            recursive: Search subdirectories

        Returns:
            TextureSet with detected textures.
        """
        texture_set = TextureSet(name=material_name)

        if not texture_dir.exists():
            return texture_set

        # Get search pattern
        search_pattern = "**/*" if recursive else "*"

        # Find all image files
        image_extensions = {".jpg", ".jpeg", ".png", ".tga", ".bmp", ".exr", ".hdr"}

        for file_path in texture_dir.glob(search_pattern):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in image_extensions:
                continue

            # Check if this file matches our material
            filename = file_path.stem.lower()

            # Normalize material name for matching
            mat_name_lower = material_name.lower().replace("-", "_")

            # Check if file contains material name
            if mat_name_lower not in filename:
                continue

            # Detect texture type
            texture_type = self._detect_texture_type(filename)
            if texture_type and hasattr(texture_set, texture_type):
                setattr(texture_set, texture_type, file_path)

        return texture_set

    def _detect_texture_type(self, filename: str) -> str | None:
        """Detect texture type from filename."""
        filename_lower = filename.lower()

        for texture_type, patterns in TEXTURE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return texture_type

        return None

    def build_from_textures(
        self,
        material_name: str,
        texture_dir: Path,
        use_ao: bool = True,
        use_displacement: bool = False,
    ) -> MaterialBuildResult:
        """
        Build a Principled BSDF material from textures.

        Args:
            material_name: Name for the material
            texture_dir: Directory containing textures
            use_ao: Connect AO to Mix node (otherwise just load)
            use_displacement: Enable displacement output

        Returns:
            MaterialBuildResult with created material and status.
        """
        import bpy

        result = MaterialBuildResult()

        # Detect textures
        texture_set = self.detect_texture_set(material_name, texture_dir)
        result.texture_set = texture_set

        if not texture_set.has_textures():
            result.errors.append(f"No textures found for {material_name}")
            return result

        # Create material
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        result.material = mat

        # Get node tree
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links

        # Clear default nodes
        nodes.clear()

        # Create output node
        output_node = nodes.new("ShaderNodeOutputMaterial")
        output_node.location = (800, 0)

        # Create Principled BSDF
        bsdf_node = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf_node.location = (400, 0)

        # Link to output
        links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

        # Create and connect textures
        last_texture_node = None
        ao_node = None

        # Base Color
        if texture_set.basecolor:
            color_node = self._create_image_node(nodes, texture_set.basecolor, "Base Color")
            color_node.location = (-400, 300)
            links.new(color_node.outputs["Color"], bsdf_node.inputs["Base Color"])

            # Connect alpha if present
            if texture_set.opacity:
                links.new(color_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
            elif self._has_alpha(texture_set.basecolor):
                # Image has alpha channel
                mat.blend_method = "BLEND"
                mat.shadow_method = "HASHED"
                links.new(color_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])

            last_texture_node = color_node

        # Roughness (direct or inverted from glossiness)
        roughness_source = texture_set.roughness or texture_set.glossiness
        if roughness_source:
            rough_node = self._create_image_node(nodes, roughness_source, "Roughness")
            rough_node.location = (-400, 100)
            rough_node.image.colorspace_settings.name = "Non-Color"

            if texture_set.glossiness and not texture_set.roughness:
                # Invert glossiness to get roughness
                invert_node = nodes.new("ShaderNodeInvert")
                invert_node.location = (-200, 100)
                links.new(rough_node.outputs["Color"], invert_node.inputs["Color"])
                links.new(invert_node.outputs["Color"], bsdf_node.inputs["Roughness"])
            else:
                links.new(rough_node.outputs["Color"], bsdf_node.inputs["Roughness"])

        # Metallic
        if texture_set.metallic:
            metal_node = self._create_image_node(nodes, texture_set.metallic, "Metallic")
            metal_node.location = (-400, -50)
            metal_node.image.colorspace_settings.name = "Non-Color"
            links.new(metal_node.outputs["Color"], bsdf_node.inputs["Metallic"])

        # Specular
        if texture_set.specular:
            spec_node = self._create_image_node(nodes, texture_set.specular, "Specular")
            spec_node.location = (-400, -200)
            spec_node.image.colorspace_settings.name = "Non-Color"
            links.new(spec_node.outputs["Color"], bsdf_node.inputs["Specular IOR Level"])

        # Normal Map
        if texture_set.normal:
            normal_node = self._create_image_node(nodes, texture_set.normal, "Normal")
            normal_node.location = (-400, -350)
            normal_node.image.colorspace_settings.name = "Non-Color"

            normal_map_node = nodes.new("ShaderNodeNormalMap")
            normal_map_node.location = (-200, -350)
            links.new(normal_node.outputs["Color"], normal_map_node.inputs["Color"])
            links.new(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

        # Height/Bump
        if texture_set.height and use_displacement:
            height_node = self._create_image_node(nodes, texture_set.height, "Height")
            height_node.location = (-400, -500)
            height_node.image.colorspace_settings.name = "Non-Color"

            disp_node = nodes.new("ShaderNodeDisplacement")
            disp_node.location = (-200, -500)
            links.new(height_node.outputs["Color"], disp_node.inputs["Height"])
            links.new(disp_node.outputs["Displacement"], output_node.inputs["Displacement"])

        # Ambient Occlusion
        if texture_set.ao and use_ao:
            ao_node = self._create_image_node(nodes, texture_set.ao, "AO")
            ao_node.location = (-600, 0)
            ao_node.image.colorspace_settings.name = "Non-Color"

            # Mix AO with base color
            if last_texture_node:
                mix_node = nodes.new("ShaderNodeMixRGB")
                mix_node.location = (-200, 300)
                mix_node.blend_type = "MULTIPLY"
                mix_node.inputs["Factor"].default_value = 0.5

                links.new(last_texture_node.outputs["Color"], mix_node.inputs["Color1"])
                links.new(ao_node.outputs["Color"], mix_node.inputs["Color2"])
                links.new(mix_node.outputs["Color"], bsdf_node.inputs["Base Color"])

        # Emission
        if texture_set.emission:
            emit_node = self._create_image_node(nodes, texture_set.emission, "Emission")
            emit_node.location = (-400, 450)
            links.new(emit_node.outputs["Color"], bsdf_node.inputs["Emission Color"])
            bsdf_node.inputs["Emission Strength"].default_value = 1.0

        return result

    def _create_image_node(
        self,
        nodes,
        image_path: Path,
        label: str,
    ) -> Node:
        """Create an image texture node."""
        import bpy

        node = nodes.new("ShaderNodeTexImage")
        node.label = label

        # Load or reuse image
        image = bpy.data.images.get(image_path.name)
        if not image:
            image = bpy.data.images.load(str(image_path))
        elif image.filepath != str(image_path):
            # Same name but different path - create new
            image = bpy.data.images.load(str(image_path))

        node.image = image
        return node

    def _has_alpha(self, image_path: Path) -> bool:
        """Check if an image has an alpha channel."""
        # Simple heuristic based on format
        return image_path.suffix.lower() in {".png", ".tga", ".exr"}

    def build_from_kitbash_textures(
        self,
        material_name: str,
        texture_dir: Path,
        prefix: str = "KB3D_WZT",
    ) -> MaterialBuildResult:
        """
        Build material from KitBash3D texture naming convention.

        KitBash format: {PREFIX}_{MaterialName}_{type}.jpg
        Example: KB3D_WZT_assetsA_basecolor.jpg

        Args:
            material_name: Material name (e.g., "assetsA", "bricksA")
            texture_dir: Directory with textures
            prefix: KitBash prefix (e.g., "KB3D_WZT")

        Returns:
            MaterialBuildResult with created material.
        """
        import bpy
        import fnmatch

        result = MaterialBuildResult()

        # Find textures with KitBash naming
        texture_set = TextureSet(name=material_name)

        if not texture_dir.exists():
            result.errors.append(f"Texture directory not found: {texture_dir}")
            return result

        # Map KitBash suffixes to texture types
        kitbash_mapping = {
            "basecolor": "basecolor",
            "diffuse": "basecolor",
            "roughness": "roughness",
            "metallic": "metallic",
            "normal": "normal",
            "height": "height",
            "ambient_occlusion": "ao",
            "specular": "specular",
            "glossiness": "glossiness",
        }

        # Build list of all texture files in directory (for case-insensitive matching)
        texture_files = list(texture_dir.glob("*.[jJ][pP][gG]"))
        texture_files.extend(texture_dir.glob("*.[pP][nN][gG]"))
        texture_files.extend(texture_dir.glob("*.[tT][gG][aA]"))

        # Build lookup by lowercase filename
        texture_lookup = {f.name.lower(): f for f in texture_files}

        # Strip prefix from material name if already present
        # e.g., "KB3D_DPK_AtlasEXLarges" with prefix "KB3D_DPK" -> "AtlasEXLarges"
        base_material_name = material_name
        if prefix and material_name.upper().startswith(prefix.upper() + "_"):
            base_material_name = material_name[len(prefix) + 1:]

        # Try multiple material name variations
        # MTL may have "assetA" but textures use "assetsA"
        # Case may differ (concreteA vs ConcreteA)
        name_variations = [
            base_material_name,  # original (possibly stripped)
            material_name,  # full original name
        ]

        # Add "s" before capital letters for patterns like assetA -> assetsA
        s_before_capital = re.sub(r'([A-Z])', r's\1', base_material_name)  # assetA -> assetsA
        if s_before_capital != base_material_name and s_before_capital not in name_variations:
            name_variations.append(s_before_capital)

        # Also try removing 's' if present
        stripped_s = base_material_name.rstrip("s")
        if stripped_s not in name_variations:
            name_variations.append(stripped_s)

        # Capitalize first letter
        if base_material_name:
            cap_name = base_material_name[0].upper() + base_material_name[1:]
            if cap_name not in name_variations:
                name_variations.append(cap_name)

        # Search for textures using case-insensitive lookup
        for suffix, tex_type in kitbash_mapping.items():
            found = False
            for name_var in name_variations:
                if not name_var:
                    continue
                # Try each extension (case-insensitive via lowercase lookup)
                for ext in [".jpg", ".png", ".tga"]:
                    expected_name = f"{prefix}_{name_var}_{suffix}{ext}".lower()
                    if expected_name in texture_lookup:
                        setattr(texture_set, tex_type, texture_lookup[expected_name])
                        found = True
                        break

                # If found, move to next texture type
                if found:
                    break

        result.texture_set = texture_set

        if not texture_set.has_textures():
            result.errors.append(f"No KitBash textures found for {material_name}")
            return result

        # Build the material
        return self._build_from_texture_set(material_name, texture_set)

    def _build_from_texture_set(
        self,
        material_name: str,
        texture_set: TextureSet,
    ) -> MaterialBuildResult:
        """Build material from an already-detected texture set."""
        import bpy

        result = MaterialBuildResult(texture_set=texture_set)

        if not texture_set.has_textures():
            result.errors.append("Texture set has no textures")
            return result

        # Create material
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        result.material = mat

        # Build node tree (same as build_from_textures)
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        nodes.clear()

        # Output node
        output_node = nodes.new("ShaderNodeOutputMaterial")
        output_node.location = (800, 0)

        # BSDF node
        bsdf_node = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf_node.location = (400, 0)
        links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

        # Add textures (same logic as build_from_textures)
        self._connect_textures(nodes, links, bsdf_node, output_node, texture_set)

        return result

    def _connect_textures(
        self,
        nodes,
        links,
        bsdf_node: Node,
        output_node: Node,
        texture_set: TextureSet,
    ):
        """Connect texture nodes to BSDF."""
        # Base Color
        if texture_set.basecolor:
            color_node = self._create_image_node(nodes, texture_set.basecolor, "Base Color")
            color_node.location = (-400, 300)
            links.new(color_node.outputs["Color"], bsdf_node.inputs["Base Color"])

        # Roughness
        roughness_source = texture_set.roughness or texture_set.glossiness
        if roughness_source:
            rough_node = self._create_image_node(nodes, roughness_source, "Roughness")
            rough_node.location = (-400, 100)
            rough_node.image.colorspace_settings.name = "Non-Color"

            if texture_set.glossiness and not texture_set.roughness:
                invert = nodes.new("ShaderNodeInvert")
                invert.location = (-200, 100)
                links.new(rough_node.outputs["Color"], invert.inputs["Color"])
                links.new(invert.outputs["Color"], bsdf_node.inputs["Roughness"])
            else:
                links.new(rough_node.outputs["Color"], bsdf_node.inputs["Roughness"])

        # Metallic
        if texture_set.metallic:
            metal_node = self._create_image_node(nodes, texture_set.metallic, "Metallic")
            metal_node.location = (-400, -50)
            metal_node.image.colorspace_settings.name = "Non-Color"
            links.new(metal_node.outputs["Color"], bsdf_node.inputs["Metallic"])

        # Normal
        if texture_set.normal:
            normal_node = self._create_image_node(nodes, texture_set.normal, "Normal")
            normal_node.location = (-400, -350)
            normal_node.image.colorspace_settings.name = "Non-Color"

            normal_map = nodes.new("ShaderNodeNormalMap")
            normal_map.location = (-200, -350)
            links.new(normal_node.outputs["Color"], normal_map.inputs["Color"])
            links.new(normal_map.outputs["Normal"], bsdf_node.inputs["Normal"])

        # AO (multiply with base color)
        if texture_set.ao and texture_set.basecolor:
            ao_node = self._create_image_node(nodes, texture_set.ao, "AO")
            ao_node.location = (-600, 0)
            ao_node.image.colorspace_settings.name = "Non-Color"

            # Find base color node
            for node in nodes:
                if node.label == "Base Color":
                    mix = nodes.new("ShaderNodeMixRGB")
                    mix.location = (-200, 300)
                    mix.blend_type = "MULTIPLY"
                    mix.inputs["Factor"].default_value = 0.7
                    links.new(node.outputs["Color"], mix.inputs["Color1"])
                    links.new(ao_node.outputs["Color"], mix.inputs["Color2"])
                    # Reconnect to BSDF
                    links.new(mix.outputs["Color"], bsdf_node.inputs["Base Color"])
                    break
