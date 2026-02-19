"""
Texture Baking System for Anamorphic Projection

Bakes projected images onto geometry textures for anamorphic projection.
Supports diffuse, emission, and decal modes with non-destructive workflow
and export format compatibility.

Part of Phase 9.3 - Texture Baking (REQ-ANAM-04)
Beads: blender_gsd-37
"""

from __future__ import annotations
import os
import math
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from .types import (
    RayHit,
    FrustumConfig,
    ProjectionResult,
    SurfaceInfo,
    SurfaceType,
    ProjectionMode,
    AnamorphicProjectionConfig,
)

# Blender API guard for testing outside Blender
try:
    import bpy
    import mathutils
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Fallback Vector implementation for testing outside Blender
    class Vector:
        """Simple Vector fallback for testing outside Blender."""
        def __init__(self, data):
            if hasattr(data, '__iter__'):
                self._data = list(data)[:3]
                while len(self._data) < 3:
                    self._data.append(0.0)
            else:
                self._data = [float(data), 0.0, 0.0]

        def __getitem__(self, i):
            return self._data[i]

        def __add__(self, other):
            return Vector([self._data[i] + other._data[i] for i in range(3)])

        def __sub__(self, other):
            return Vector([self._data[i] - other._data[i] for i in range(3)])

        def __truediv__(self, scalar):
            return Vector([x / scalar for x in self._data])

        def __mul__(self, scalar):
            return Vector([x * scalar for x in self._data])

        def __rmul__(self, scalar):
            return self.__mul__(scalar)

        def dot(self, other):
            return sum(self._data[i] * other._data[i] for i in range(3))

        def length(self):
            return (sum(x * x for x in self._data)) ** 0.5

        def normalized(self):
            l = self.length()
            if l > 0:
                return Vector([x / l for x in self._data])
            return Vector([0, 0, 0])

        def normalize(self):
            l = self.length()
            if l > 0:
                self._data = [x / l for x in self._data]

        def cross(self, other):
            return Vector([
                self._data[1] * other._data[2] - self._data[2] * other._data[1],
                self._data[2] * other._data[0] - self._data[0] * other._data[2],
                self._data[0] * other._data[1] - self._data[1] * other._data[0],
            ])

        def copy(self):
            return Vector(self._data)

        @property
        def x(self):
            return self._data[0]

        @property
        def y(self):
            return self._data[1]

        @property
        def z(self):
            return self._data[2]

        def __iter__(self):
            return iter(self._data)

        def __repr__(self):
            return f"Vector({self._data})"

    Matrix = None


class BakeMode:
    """Texture baking modes."""
    DIFFUSE = "diffuse"           # Standard diffuse/albedo texture
    EMISSION = "emission"         # Emissive/self-illuminated texture
    DECAL = "decal"               # Overlay/blend with existing material
    COMBINED = "combined"         # Combined pass (diffuse + emission)
    SHADOW = "shadow"             # Shadow-only bake


class BakeFormat:
    """Output texture formats."""
    PNG = "PNG"
    JPEG = "JPEG"
    TARGA = "TARGA"
    OPEN_EXR = "OPEN_EXR"
    TIFF = "TIFF"


@dataclass
class BakeConfig:
    """Configuration for texture baking."""
    # Output resolution
    resolution_x: int = 2048
    resolution_y: int = 2048

    # Bake mode
    bake_mode: str = BakeMode.EMISSION

    # Output format
    output_format: str = BakeFormat.PNG

    # Output path (directory)
    output_path: str = "//textures/"

    # UV layer to use
    uv_layer: str = "ProjectionUV"

    # Margin around UV islands (pixels)
    margin: int = 16

    # Whether to use cage for baking
    use_cage: bool = False

    # Cage extrusion distance
    cage_extrusion: float = 0.1

    # Whether to bake from selected to active
    selected_to_active: bool = False

    # Maximum ray distance for AO baking
    max_ray_distance: float = 1.0

    # Anti-aliasing samples (1, 2, 4, 8, 16)
    samples: int = 4

    # Whether to clear image before baking
    clear_image: bool = True

    # Whether to save externally
    save_external: bool = True

    # Color space for output (sRGB, Linear, etc.)
    color_space: str = "sRGB"

    # Whether to use non-destructive workflow
    non_destructive: bool = True

    # Material slot name pattern for new materials
    material_name_pattern: str = "{object}_{mode}_baked"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resolution_x": self.resolution_x,
            "resolution_y": self.resolution_y,
            "bake_mode": self.bake_mode,
            "output_format": self.output_format,
            "output_path": self.output_path,
            "uv_layer": self.uv_layer,
            "margin": self.margin,
            "use_cage": self.use_cage,
            "cage_extrusion": self.cage_extrusion,
            "selected_to_active": self.selected_to_active,
            "max_ray_distance": self.max_ray_distance,
            "samples": self.samples,
            "clear_image": self.clear_image,
            "save_external": self.save_external,
            "color_space": self.color_space,
            "non_destructive": self.non_destructive,
            "material_name_pattern": self.material_name_pattern,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BakeConfig:
        """Create from dictionary."""
        return cls(
            resolution_x=data.get("resolution_x", 2048),
            resolution_y=data.get("resolution_y", 2048),
            bake_mode=data.get("bake_mode", BakeMode.EMISSION),
            output_format=data.get("output_format", BakeFormat.PNG),
            output_path=data.get("output_path", "//textures/"),
            uv_layer=data.get("uv_layer", "ProjectionUV"),
            margin=data.get("margin", 16),
            use_cage=data.get("use_cage", False),
            cage_extrusion=data.get("cage_extrusion", 0.1),
            selected_to_active=data.get("selected_to_active", False),
            max_ray_distance=data.get("max_ray_distance", 1.0),
            samples=data.get("samples", 4),
            clear_image=data.get("clear_image", True),
            save_external=data.get("save_external", True),
            color_space=data.get("color_space", "sRGB"),
            non_destructive=data.get("non_destructive", True),
            material_name_pattern=data.get("material_name_pattern", "{object}_{mode}_baked"),
        )


@dataclass
class BakeResult:
    """Result of a texture baking operation."""
    object_name: str
    texture_path: str
    texture_name: str
    material_name: str
    resolution: Tuple[int, int]
    bake_mode: str
    bake_time: float  # seconds
    success: bool
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "object_name": self.object_name,
            "texture_path": self.texture_path,
            "texture_name": self.texture_name,
            "material_name": self.material_name,
            "resolution": list(self.resolution),
            "bake_mode": self.bake_mode,
            "bake_time": self.bake_time,
            "success": self.success,
            "error_message": self.error_message,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BakeResult:
        """Create from dictionary."""
        return cls(
            object_name=data.get("object_name", ""),
            texture_path=data.get("texture_path", ""),
            texture_name=data.get("texture_name", ""),
            material_name=data.get("material_name", ""),
            resolution=tuple(data.get("resolution", (2048, 2048))),
            bake_mode=data.get("bake_mode", BakeMode.EMISSION),
            bake_time=data.get("bake_time", 0.0),
            success=data.get("success", False),
            error_message=data.get("error_message", ""),
            warnings=data.get("warnings", []),
        )


def bake_projection_texture(
    projection_config: AnamorphicProjectionConfig,
    bake_config: Optional[BakeConfig] = None,
) -> List[BakeResult]:
    """
    Bake projected image onto geometry textures.

    Main entry point for texture baking. Takes the projection configuration
    and bakes the projected image onto the target surfaces.

    Args:
        projection_config: Complete projection configuration
        bake_config: Baking configuration

    Returns:
        List of BakeResult for each processed object
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for texture baking")

    config = bake_config or BakeConfig()
    results = []

    # Get source image
    source_image = _load_source_image(projection_config.source_image)
    if source_image is None:
        raise ValueError(f"Could not load source image: {projection_config.source_image}")

    # Get target surfaces
    target_objects = _get_target_objects(
        projection_config.target_surfaces,
        projection_config.camera_name,
        projection_config.surface_types,
    )

    if not target_objects:
        raise ValueError("No target objects found for baking")

    # Process each target object
    for obj in target_objects:
        result = _bake_object_texture(
            obj,
            source_image,
            projection_config,
            config,
        )
        results.append(result)

    return results


def bake_object_texture(
    object_name: str,
    source_image_path: str,
    camera_name: str,
    bake_config: Optional[BakeConfig] = None,
    projection_mode: str = ProjectionMode.EMISSION,
) -> BakeResult:
    """
    Bake texture for a single object using camera projection.

    Convenience function for baking a single object without
    full projection configuration.

    Args:
        object_name: Object to bake onto
        source_image_path: Path to source image
        camera_name: Camera for projection
        bake_config: Baking configuration
        projection_mode: How to apply the texture

    Returns:
        BakeResult with baking details
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for texture baking")

    obj = bpy.data.objects.get(object_name)
    if obj is None:
        return BakeResult(
            object_name=object_name,
            texture_path="",
            texture_name="",
            material_name="",
            resolution=(0, 0),
            bake_mode=projection_mode,
            bake_time=0.0,
            success=False,
            error_message=f"Object not found: {object_name}",
        )

    config = bake_config or BakeConfig()

    # Create minimal projection config
    proj_config = AnamorphicProjectionConfig(
        source_image=source_image_path,
        camera_name=camera_name,
        projection_mode=ProjectionMode(projection_mode),
        target_surfaces=[object_name],
    )

    # Load source image
    source_image = _load_source_image(source_image_path)
    if source_image is None:
        return BakeResult(
            object_name=object_name,
            texture_path="",
            texture_name="",
            material_name="",
            resolution=(config.resolution_x, config.resolution_y),
            bake_mode=projection_mode,
            bake_time=0.0,
            success=False,
            error_message=f"Could not load image: {source_image_path}",
        )

    return _bake_object_texture(obj, source_image, proj_config, config)


def create_bake_material(
    object_name: str,
    texture_path: str,
    projection_mode: str = ProjectionMode.EMISSION,
    non_destructive: bool = True,
    intensity: float = 1.0,
) -> str:
    """
    Create a material with baked texture for an object.

    Creates a new material with the baked texture applied according
    to the specified projection mode.

    Args:
        object_name: Object to create material for
        texture_path: Path to baked texture
        projection_mode: How the texture should be rendered
        non_destructive: If True, preserve original material
        intensity: Material intensity (for emission)

    Returns:
        Name of created material
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for material creation")

    obj = bpy.data.objects.get(object_name)
    if obj is None:
        raise ValueError(f"Object not found: {object_name}")

    # Create material name
    mat_name = f"{object_name}_{projection_mode}_material"

    # Check if material exists
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

    # Clear existing nodes
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Create nodes based on projection mode
    output_node = nodes.new('ShaderNodeOutputMaterial')
    output_node.location = (400, 0)

    # Load texture
    texture_node = nodes.new('ShaderNodeTexImage')
    texture_node.location = (-400, 0)

    # Load image
    if os.path.isabs(texture_path):
        image = bpy.data.images.load(texture_path, check_existing=True)
    else:
        # Try relative path
        blend_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else ""
        abs_path = os.path.join(blend_dir, texture_path.replace("//", ""))
        image = bpy.data.images.load(abs_path, check_existing=True)

    texture_node.image = image

    if projection_mode == ProjectionMode.EMISSION:
        # Emission shader
        emission_node = nodes.new('ShaderNodeEmission')
        emission_node.location = (0, 0)
        emission_node.inputs['Strength'].default_value = intensity

        # Link texture to emission color
        links.new(texture_node.outputs['Color'], emission_node.inputs['Color'])
        links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])

    elif projection_mode == ProjectionMode.DIFFUSE:
        # Diffuse BSDF
        diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
        diffuse_node.location = (0, 0)

        links.new(texture_node.outputs['Color'], diffuse_node.inputs['Color'])
        links.new(diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])

    elif projection_mode == ProjectionMode.DECAL:
        # Mix shader for decal blending
        mix_node = nodes.new('ShaderNodeMixShader')
        mix_node.location = (200, 0)

        # Diffuse as base
        diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
        diffuse_node.location = (-200, -100)

        # Emission for decal
        emission_node = nodes.new('ShaderNodeEmission')
        emission_node.location = (-200, 100)
        emission_node.inputs['Strength'].default_value = intensity

        # Use alpha for mix factor
        links.new(texture_node.outputs['Color'], emission_node.inputs['Color'])
        links.new(texture_node.outputs['Alpha'], mix_node.inputs['Fac'])
        links.new(diffuse_node.outputs['BSDF'], mix_node.inputs[1])
        links.new(emission_node.outputs['Emission'], mix_node.inputs[2])
        links.new(mix_node.outputs['Shader'], output_node.inputs['Surface'])

    else:  # REPLACE
        # Just diffuse with texture
        diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
        diffuse_node.location = (0, 0)

        links.new(texture_node.outputs['Color'], diffuse_node.inputs['Color'])
        links.new(diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])

    # Add UV map node
    uv_node = nodes.new('ShaderNodeUVMap')
    uv_node.location = (-600, -200)
    uv_node.uv_map = "ProjectionUV"

    links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])

    # Assign material to object
    if non_destructive:
        # Add new material slot
        mat_slot = obj.data.materials.append(mat)
    else:
        # Replace all materials
        obj.data.materials.clear()
        obj.data.materials.append(mat)

    return mat_name


def prepare_for_baking(
    objects: List[str],
    uv_layer: str = "ProjectionUV",
    create_uv: bool = True,
) -> Dict[str, Any]:
    """
    Prepare objects for texture baking.

    Sets up UV layers, ensures proper materials, and configures
    baking settings.

    Args:
        objects: List of object names to prepare
        uv_layer: UV layer name to use/create
        create_uv: Whether to create UV layer if missing

    Returns:
        Dictionary with preparation results
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for bake preparation")

    results = {
        "prepared": [],
        "skipped": [],
        "errors": [],
    }

    for obj_name in objects:
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            results["errors"].append(f"Object not found: {obj_name}")
            continue

        if obj.type != 'MESH':
            results["skipped"].append(f"{obj_name} (not a mesh)")
            continue

        # Check/create UV layer
        uv_found = False
        for layer in obj.data.uv_layers:
            if layer.name == uv_layer:
                uv_found = True
                break

        if not uv_found and create_uv:
            obj.data.uv_layers.new(name=uv_layer)
            results["prepared"].append(f"{obj_name} (created UV)")
        elif uv_found:
            results["prepared"].append(f"{obj_name} (UV exists)")
        else:
            results["skipped"].append(f"{obj_name} (no UV)")

    return results


def cleanup_bake_artifacts(
    texture_names: Optional[List[str]] = None,
    material_names: Optional[List[str]] = None,
    keep_used: bool = True,
) -> Dict[str, int]:
    """
    Clean up temporary textures and materials from baking.

    Removes unused bake textures and materials to save memory.

    Args:
        texture_names: Specific textures to remove (None = all bake textures)
        material_names: Specific materials to remove (None = all bake materials)
        keep_used: If True, don't remove textures/materials in use

    Returns:
        Dictionary with cleanup counts
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for cleanup")

    removed = {
        "textures": 0,
        "materials": 0,
    }

    # Clean up textures
    if texture_names:
        for tex_name in texture_names:
            if tex_name in bpy.data.images:
                image = bpy.data.images[tex_name]
                if not keep_used or image.users == 0:
                    bpy.data.images.remove(image)
                    removed["textures"] += 1
    else:
        # Remove all unused bake textures
        for image in bpy.data.images:
            if "_baked" in image.name and (not keep_used or image.users == 0):
                bpy.data.images.remove(image)
                removed["textures"] += 1

    # Clean up materials
    if material_names:
        for mat_name in material_names:
            if mat_name in bpy.data.materials:
                mat = bpy.data.materials[mat_name]
                if not keep_used or mat.users == 0:
                    bpy.data.materials.remove(mat)
                    removed["materials"] += 1
    else:
        # Remove all unused bake materials
        for mat in bpy.data.materials:
            if "_baked" in mat.name and (not keep_used or mat.users == 0):
                bpy.data.materials.remove(mat)
                removed["materials"] += 1

    return removed


def export_baked_textures(
    output_dir: str,
    format: str = BakeFormat.PNG,
    texture_names: Optional[List[str]] = None,
) -> List[str]:
    """
    Export baked textures to external files.

    Saves all (or specified) baked textures to the output directory.

    Args:
        output_dir: Directory to save textures
        format: Output format (PNG, JPEG, etc.)
        texture_names: Specific textures to export (None = all)

    Returns:
        List of exported file paths
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for texture export")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    exported = []

    # Get textures to export
    if texture_names:
        images = [bpy.data.images.get(name) for name in texture_names if name in bpy.data.images]
    else:
        # Export all baked textures
        images = [img for img in bpy.data.images if "_baked" in img.name]

    for image in images:
        if image is None:
            continue

        # Determine file extension
        ext_map = {
            BakeFormat.PNG: ".png",
            BakeFormat.JPEG: ".jpg",
            BakeFormat.TARGA: ".tga",
            BakeFormat.OPEN_EXR: ".exr",
            BakeFormat.TIFF: ".tif",
        }
        ext = ext_map.get(format, ".png")

        # Build output path
        safe_name = image.name.replace(" ", "_").replace("/", "_")
        output_path = os.path.join(output_dir, f"{safe_name}{ext}")

        # Set format and save
        image.file_format = format
        image.filepath_raw = output_path
        image.save()

        exported.append(output_path)

    return exported


# Private helper functions

def _load_source_image(image_path: str):
    """Load source image for projection."""
    if not image_path:
        return None

    try:
        # Handle relative paths
        if image_path.startswith("//"):
            blend_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else ""
            abs_path = os.path.join(blend_dir, image_path[2:])
        else:
            abs_path = image_path

        image = bpy.data.images.load(abs_path, check_existing=True)
        return image
    except Exception:
        return None


def _get_target_objects(
    surface_names: List[str],
    camera_name: str,
    surface_types: List[SurfaceType],
) -> List:
    """Get target objects for baking."""
    objects = []

    if surface_names:
        # Use specified surfaces
        for name in surface_names:
            obj = bpy.data.objects.get(name)
            if obj and obj.type == 'MESH':
                objects.append(obj)
    else:
        # Auto-detect from scene
        for obj in bpy.context.scene.objects:
            if obj.type != 'MESH':
                continue
            objects.append(obj)

    return objects


def _bake_object_texture(
    obj,
    source_image,
    projection_config: AnamorphicProjectionConfig,
    bake_config: BakeConfig,
) -> BakeResult:
    """Bake texture for a single object."""
    import time
    start_time = time.time()

    try:
        # Create bake texture
        texture_name = f"{obj.name}_baked"
        bake_image = bpy.data.images.new(
            name=texture_name,
            width=bake_config.resolution_x,
            height=bake_config.resolution_y,
            alpha=True,
        )

        # Set UV layer as active
        uv_layer_found = False
        for layer in obj.data.uv_layers:
            if layer.name == bake_config.uv_layer:
                obj.data.uv_layers.active = layer
                uv_layer_found = True
                break

        if not uv_layer_found:
            return BakeResult(
                object_name=obj.name,
                texture_path="",
                texture_name=texture_name,
                material_name="",
                resolution=(bake_config.resolution_x, bake_config.resolution_y),
                bake_mode=bake_config.bake_mode,
                bake_time=time.time() - start_time,
                success=False,
                error_message=f"UV layer '{bake_config.uv_layer}' not found",
            )

        # Create temporary material for baking
        temp_mat_name = f"_temp_bake_{obj.name}"
        temp_mat = bpy.data.materials.new(name=temp_mat_name)
        temp_mat.use_nodes = True

        # Setup nodes for projection
        nodes = temp_mat.node_tree.nodes
        links = temp_mat.node_tree.links
        nodes.clear()

        # Texture node with source image
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = source_image
        tex_node.select = True
        nodes.active = tex_node

        # Setup bake settings
        scene = bpy.context.scene
        render_settings = scene.render

        # Store original settings
        original_engine = render_settings.engine
        original_bake_type = render_settings.bake_type

        # Configure bake
        render_settings.engine = 'CYCLES'
        render_settings.bake_type = _get_bake_type(bake_config.bake_mode)

        # Cycles bake settings
        cycles_settings = scene.cycles
        cycles_settings.bake_margin = bake_config.margin
        cycles_settings.use_clear = bake_config.clear_image
        cycles_settings.samples = bake_config.samples

        if bake_config.use_cage:
            cycles_settings.use_bake_cage = True
            cycles_settings.bake_cage_extrusion = bake_config.cage_extrusion

        # Assign material temporarily
        original_materials = list(obj.data.materials)
        obj.data.materials.clear()
        obj.data.materials.append(temp_mat)

        # Set bake image
        tex_node.image = bake_image

        # Select object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Bake
        bpy.ops.object.bake()

        # Restore original materials
        obj.data.materials.clear()
        for mat in original_materials:
            obj.data.materials.append(mat)

        # Restore render settings
        render_settings.engine = original_engine
        render_settings.bake_type = original_bake_type

        # Remove temp material
        bpy.data.materials.remove(temp_mat)

        # Save baked texture
        texture_path = ""
        if bake_config.save_external:
            output_path = _resolve_output_path(bake_config.output_path, obj.name)
            os.makedirs(output_path, exist_ok=True)

            file_name = f"{obj.name}_baked.{_get_file_extension(bake_config.output_format)}"
            texture_path = os.path.join(output_path, file_name)

            bake_image.file_format = bake_config.output_format
            bake_image.filepath_raw = texture_path
            bake_image.save()

        # Create final material if non-destructive
        material_name = ""
        if bake_config.non_destructive:
            material_name = create_bake_material(
                obj.name,
                texture_path or f"//textures/{obj.name}_baked.png",
                projection_config.projection_mode.value,
                non_destructive=True,
                intensity=projection_config.intensity,
            )

        bake_time = time.time() - start_time

        return BakeResult(
            object_name=obj.name,
            texture_path=texture_path,
            texture_name=texture_name,
            material_name=material_name,
            resolution=(bake_config.resolution_x, bake_config.resolution_y),
            bake_mode=bake_config.bake_mode,
            bake_time=bake_time,
            success=True,
        )

    except Exception as e:
        return BakeResult(
            object_name=obj.name,
            texture_path="",
            texture_name="",
            material_name="",
            resolution=(bake_config.resolution_x, bake_config.resolution_y),
            bake_mode=bake_config.bake_mode,
            bake_time=time.time() - start_time,
            success=False,
            error_message=str(e),
        )


def _get_bake_type(mode: str) -> str:
    """Convert bake mode to Blender bake type."""
    mode_map = {
        BakeMode.EMISSION: 'EMIT',
        BakeMode.DIFFUSE: 'DIFFUSE',
        BakeMode.DECAL: 'DIFFUSE',
        BakeMode.COMBINED: 'COMBINED',
        BakeMode.SHADOW: 'SHADOW',
    }
    return mode_map.get(mode, 'EMIT')


def _resolve_output_path(path_pattern: str, object_name: str) -> str:
    """Resolve output path, handling relative paths."""
    if path_pattern.startswith("//"):
        blend_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else ""
        return os.path.join(blend_dir, path_pattern[2:])
    return path_pattern


def _get_file_extension(format: str) -> str:
    """Get file extension for format."""
    ext_map = {
        BakeFormat.PNG: "png",
        BakeFormat.JPEG: "jpg",
        BakeFormat.TARGA: "tga",
        BakeFormat.OPEN_EXR: "exr",
        BakeFormat.TIFF: "tif",
    }
    return ext_map.get(format, "png")
