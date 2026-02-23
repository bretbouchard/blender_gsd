"""
Asset Vault Thumbnail Generator

Generate preview thumbnails for assets.
Requires Blender (bpy) for rendering.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .enums import AssetFormat
from .types import AssetInfo


# Thumbnail configuration
THUMBNAIL_SIZE: Tuple[int, int] = (256, 256)
THUMBNAIL_FORMAT: str = "PNG"
THUMBNAIL_DIR: str = ".gsd-state/thumbnails"


@dataclass
class ThumbnailConfig:
    """Configuration for thumbnail generation."""
    size: Tuple[int, int] = (256, 256)
    format: str = "PNG"
    background: Tuple[float, float, float, float] = (0.1, 0.1, 0.1, 1.0)
    lighting: str = "studio"  # "studio", "flat", "hdri"
    camera_distance: float = 3.0
    auto_frame: bool = True


class ThumbnailGenerator:
    """
    Generate thumbnails for 3D assets.

    Creates preview renders for assets using Blender's render engine.
    """

    def __init__(self, config: Optional[ThumbnailConfig] = None):
        """
        Initialize the thumbnail generator.

        Args:
            config: Thumbnail configuration
        """
        self.config = config or ThumbnailConfig()

    def generate_thumbnail(
        self,
        asset: AssetInfo,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Generate a thumbnail for an asset.

        Args:
            asset: Asset to generate thumbnail for
            output_path: Output path (default: auto-generated)

        Returns:
            Path to thumbnail, or None on failure
        """
        # Determine output path
        if output_path is None:
            output_path = get_thumbnail_path(asset)

        # Check if thumbnail already exists
        if output_path.exists():
            return output_path

        # Dispatch by format
        generators = {
            AssetFormat.BLEND: self._generate_blend_thumbnail,
            AssetFormat.FBX: self._generate_fbx_thumbnail,
            AssetFormat.OBJ: self._generate_obj_thumbnail,
            AssetFormat.GLB: self._generate_glb_thumbnail,
        }

        generator = generators.get(asset.format)
        if generator is None:
            return None

        return generator(asset.path, output_path)

    def _generate_blend_thumbnail(
        self,
        path: Path,
        output_path: Path,
    ) -> Optional[Path]:
        """Generate thumbnail for .blend file."""
        try:
            import bpy

            # Create new scene for rendering
            scene = bpy.data.scenes.new("ThumbnailScene")

            # Import first object/collection
            with bpy.data.libraries.load(str(path)) as (data_from, data_to):
                if data_from.objects:
                    data_to.objects = [data_from.objects[0]]
                elif data_from.collections:
                    data_to.collections = [data_from.collections[0]]

            # Set up camera and lighting
            self._setup_thumbnail_scene(scene)

            # Render
            self._render_thumbnail(scene, output_path)

            # Cleanup
            bpy.data.scenes.remove(scene)

            return output_path if output_path.exists() else None

        except ImportError:
            # bpy not available
            return self._extract_embedded_thumbnail(path, output_path)
        except Exception:
            return None

    def _generate_fbx_thumbnail(
        self,
        path: Path,
        output_path: Path,
    ) -> Optional[Path]:
        """Generate thumbnail for FBX file."""
        try:
            import bpy

            scene = bpy.data.scenes.new("ThumbnailScene")

            # Import FBX
            bpy.ops.import_scene.fbx(filepath=str(path))

            self._setup_thumbnail_scene(scene)
            self._render_thumbnail(scene, output_path)

            bpy.data.scenes.remove(scene)
            return output_path if output_path.exists() else None

        except (ImportError, Exception):
            return None

    def _generate_obj_thumbnail(
        self,
        path: Path,
        output_path: Path,
    ) -> Optional[Path]:
        """Generate thumbnail for OBJ file."""
        try:
            import bpy

            scene = bpy.data.scenes.new("ThumbnailScene")

            # Import OBJ
            try:
                bpy.ops.wm.obj_import(filepath=str(path))
            except AttributeError:
                bpy.ops.import_scene.obj(filepath=str(path))

            # Apply default material
            self._apply_default_material(scene)

            self._setup_thumbnail_scene(scene)
            self._render_thumbnail(scene, output_path)

            bpy.data.scenes.remove(scene)
            return output_path if output_path.exists() else None

        except (ImportError, Exception):
            return None

    def _generate_glb_thumbnail(
        self,
        path: Path,
        output_path: Path,
    ) -> Optional[Path]:
        """Generate thumbnail for GLB/GLTF file."""
        try:
            import bpy

            scene = bpy.data.scenes.new("ThumbnailScene")

            bpy.ops.import_scene.gltf(filepath=str(path))

            self._setup_thumbnail_scene(scene)
            self._render_thumbnail(scene, output_path)

            bpy.data.scenes.remove(scene)
            return output_path if output_path.exists() else None

        except (ImportError, Exception):
            return None

    def _setup_thumbnail_scene(self, scene) -> None:
        """Set up camera and lighting for thumbnail."""
        import bpy
        import math

        # Find objects in scene
        objects = [obj for obj in scene.objects if obj.type == 'MESH']

        if not objects:
            return

        # Calculate bounding box
        min_co = [float('inf')] * 3
        max_co = [float('-inf')] * 3

        for obj in objects:
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ bpy.mathutils.Vector(corner)
                for i in range(3):
                    min_co[i] = min(min_co[i], world_corner[i])
                    max_co[i] = max(max_co[i], world_corner[i])

        center = [(min_co[i] + max_co[i]) / 2 for i in range(3)]
        size = max(max_co[i] - min_co[i] for i in range(3))

        # Create camera
        camera_data = bpy.data.cameras.new("ThumbnailCamera")
        camera_object = bpy.data.objects.new("ThumbnailCamera", camera_data)
        scene.collection.objects.link(camera_object)
        scene.camera = camera_object

        # Position camera
        distance = size * self.config.camera_distance
        camera_object.location = (center[0], center[1] - distance, center[2])
        camera_object.rotation_euler = (math.radians(90), 0, 0)

        # Create key light
        light_data = bpy.data.lights.new("KeyLight", type='SUN')
        light_data.energy = 5
        light_object = bpy.data.objects.new("KeyLight", light_data)
        scene.collection.objects.link(light_object)
        light_object.location = (center[0] + size, center[1] - size, center[2] + size)
        light_object.rotation_euler = (math.radians(45), 0, math.radians(45))

        # Set render settings
        scene.render.resolution_x = self.config.size[0]
        scene.render.resolution_y = self.config.size[1]
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'

    def _apply_default_material(self, scene) -> None:
        """Apply default gray material to objects."""
        import bpy

        mat = bpy.data.materials.new(name="DefaultThumbnail")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)

        for obj in scene.objects:
            if obj.type == 'MESH':
                obj.data.materials.append(mat)

    def _render_thumbnail(self, scene, output_path: Path) -> None:
        """Render the thumbnail."""
        import bpy

        output_path.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True, scene=scene.name)

    def _extract_embedded_thumbnail(
        self,
        path: Path,
        output_path: Path,
    ) -> Optional[Path]:
        """Extract embedded thumbnail from file."""
        # Blend files can have embedded previews
        try:
            import bpy

            # Try to extract blend preview
            if path.suffix.lower() == '.blend':
                # This requires opening the file in Blender
                pass

        except ImportError:
            pass

        return None

    def batch_generate(
        self,
        assets: List[AssetInfo],
        parallel: bool = False,
        skip_existing: bool = True,
    ) -> Dict[str, Path]:
        """
        Generate thumbnails for multiple assets.

        Args:
            assets: Assets to process
            parallel: Enable parallel processing (not implemented)
            skip_existing: Skip if thumbnail already exists

        Returns:
            Dictionary mapping asset paths to thumbnail paths
        """
        results = {}

        for asset in assets:
            thumbnail_path = get_thumbnail_path(asset)

            if skip_existing and thumbnail_path.exists():
                results[str(asset.path)] = thumbnail_path
                continue

            generated = self.generate_thumbnail(asset, thumbnail_path)
            if generated:
                results[str(asset.path)] = generated

        return results


def extract_embedded_thumbnail(
    path: Path,
    format: AssetFormat,
    output_path: Optional[Path] = None,
) -> Optional[Path]:
    """
    Extract embedded thumbnail from file.

    Args:
        path: Path to asset file
        format: Asset format
        output_path: Output path for thumbnail

    Returns:
        Path to extracted thumbnail, or None if unavailable
    """
    # GLB/GLTF can have embedded preview images
    if format in (AssetFormat.GLB, AssetFormat.GLTF):
        return _extract_gltf_thumbnail(path, output_path)

    return None


def _extract_gltf_thumbnail(path: Path, output_path: Optional[Path]) -> Optional[Path]:
    """Extract thumbnail from glTF/GLB."""
    try:
        import json
        import struct

        with open(path, "rb") as f:
            if path.suffix.lower() == ".glb":
                # Parse GLB
                magic = struct.unpack("<I", f.read(4))[0]
                if magic != 0x46546C67:
                    return None

                f.read(4)  # version
                f.read(4)  # total length

                chunk_length = struct.unpack("<I", f.read(4))[0]
                chunk_type = struct.unpack("<I", f.read(4))[0]

                if chunk_type == 0x4E4F534A:  # JSON
                    json_data = f.read(chunk_length).decode("utf-8")
                    gltf = json.loads(json_data)

                    # Look for default scene image
                    # This is simplified - real implementation would check all image sources
                    pass

    except Exception:
        pass

    return None


def get_thumbnail_path(asset: AssetInfo) -> Path:
    """
    Get the expected thumbnail path for an asset.

    Args:
        asset: Asset to get thumbnail path for

    Returns:
        Path to thumbnail file
    """
    # Use hash of path for unique filename
    path_hash = hashlib.md5(str(asset.path).encode()).hexdigest()[:12]
    filename = f"{asset.name}_{path_hash}.png"

    return Path(THUMBNAIL_DIR) / filename
