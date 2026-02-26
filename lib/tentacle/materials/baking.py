"""
Tentacle Material Texture Baking

Texture baking system for exporting procedural materials to image maps
compatible with Unreal Engine 5.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any

from .types import BakeConfig, BakeResult

# Module logger for baking operations
logger = logging.getLogger(__name__)


class TextureBaker:
    """
    Texture baker for procedural tentacle materials.

    Converts node-based materials to baked texture maps for UE5 export.
    Supports albedo, normal, roughness, SSS, and emission maps.
    """

    def __init__(self, config: Optional[BakeConfig] = None):
        """
        Initialize texture baker.

        Args:
            config: Baking configuration, uses defaults if None
        """
        self.config = config or BakeConfig()
        self._bpy = None

    def _get_bpy(self):
        """Lazy import of bpy module."""
        if self._bpy is None:
            try:
                import bpy

                self._bpy = bpy
            except ImportError:
                pass
        return self._bpy

    def bake(
        self,
        material_name: str,
        mesh_name: str,
        output_prefix: Optional[str] = None,
    ) -> BakeResult:
        """
        Bake material textures to image files.

        Args:
            material_name: Name of material to bake
            mesh_name: Name of mesh object with material applied
            output_prefix: Prefix for output file names

        Returns:
            BakeResult with paths to baked textures
        """
        start_time = time.time()

        bpy = self._get_bpy()
        if bpy is None:
            return BakeResult(
                success=False,
                error="Blender (bpy) not available - run within Blender",
                bake_time=0.0,
            )

        # Validate inputs
        if material_name not in bpy.data.materials:
            return BakeResult(
                success=False,
                error=f"Material '{material_name}' not found",
                bake_time=0.0,
            )

        if mesh_name not in bpy.data.objects:
            return BakeResult(
                success=False,
                error=f"Mesh '{mesh_name}' not found",
                bake_time=0.0,
            )

        # Setup output directory
        output_dir = self.config.output_directory or bpy.path.abspath("//textures")
        os.makedirs(output_dir, exist_ok=True)

        prefix = output_prefix or f"{material_name}_"
        result = BakeResult(
            resolution=(self.config.resolution, self.config.resolution)
        )

        try:
            # Create bake image
            bake_image = bpy.data.images.new(
                name=f"{prefix}BakeTemp",
                width=self.config.resolution,
                height=self.config.resolution,
                alpha=True,
            )

            # Setup mesh for baking
            mesh = bpy.data.objects[mesh_name]
            self._setup_uv_for_bake(mesh, bake_image)

            # Bake each map type
            if self.config.bake_albedo:
                albedo_path = self._bake_pass(
                    bake_image,
                    mesh,
                    "DIFFUSE",
                    os.path.join(output_dir, f"{prefix}Albedo.png"),
                )
                result.albedo_path = albedo_path

            if self.config.bake_normal:
                normal_path = self._bake_pass(
                    bake_image,
                    mesh,
                    "NORMAL",
                    os.path.join(output_dir, f"{prefix}Normal.png"),
                )
                result.normal_path = normal_path

            if self.config.bake_roughness:
                roughness_path = self._bake_pass(
                    bake_image,
                    mesh,
                    "ROUGHNESS",
                    os.path.join(output_dir, f"{prefix}Roughness.png"),
                )
                result.roughness_path = roughness_path

            if self.config.bake_sss:
                sss_path = self._bake_pass(
                    bake_image,
                    mesh,
                    "SUBSURFACE_COLOR",
                    os.path.join(output_dir, f"{prefix}SSS.png"),
                )
                result.sss_path = sss_path

            if self.config.bake_emission:
                emission_path = self._bake_pass(
                    bake_image,
                    mesh,
                    "EMIT",
                    os.path.join(output_dir, f"{prefix}Emission.png"),
                )
                result.emission_path = emission_path

            # Cleanup temp image
            bpy.data.images.remove(bake_image)

            result.success = True

        except Exception as e:
            result.success = False
            result.error = str(e)

        result.bake_time = time.time() - start_time
        return result

    def _setup_uv_for_bake(self, mesh: Any, bake_image: Any) -> None:
        """
        Setup mesh UV for baking.

        Args:
            mesh: Blender mesh object
            bake_image: Image to bake to
        """
        bpy = self._get_bpy()
        if bpy is None:
            return

        # Ensure mesh has UV layer
        if not mesh.data.uv_layers:
            mesh.data.uv_layers.new(name="BakeUV")

        # Create or find material slot for bake
        # This is a simplified setup - full implementation would
        # handle more complex material setups

    def _bake_pass(
        self,
        bake_image: Any,
        mesh: Any,
        bake_type: str,
        output_path: str,
    ) -> Optional[str]:
        """
        Execute a single bake pass.

        Args:
            bake_image: Image to bake to
            mesh: Mesh object
            bake_type: Type of bake (DIFFUSE, NORMAL, etc.)
            output_path: Path to save baked texture

        Returns:
            Path to baked texture or None on failure
        """
        bpy = self._get_bpy()
        if bpy is None:
            return None

        try:
            # Configure bake settings
            scene = bpy.context.scene
            scene.render.bake_type = bake_type
            scene.render.bake.use_selected_to_active = False
            scene.render.bake.cage_extrusion = 0.01
            scene.render.bake.margin = 16

            if self.config.denoise:
                scene.render.bake.use_denoising = True

            # Set samples
            scene.cycles.samples = self.config.samples

            # Select mesh
            bpy.ops.object.select_all(action="DESELECT")
            mesh.select_set(True)
            bpy.context.view_layer.objects.active = mesh

            # Assign bake image to material nodes
            self._assign_bake_image(mesh, bake_image)

            # Execute bake
            bpy.ops.object.bake()

            # Save result
            bake_image.save_render(filepath=output_path)

            return output_path

        except Exception as e:
            logger.warning(f"Bake pass failed for {bake_type}: {e}")
            return None

    def _assign_bake_image(self, mesh: Any, bake_image: Any) -> None:
        """
        Assign bake image to mesh material nodes.

        Args:
            mesh: Mesh object
            bake_image: Image to assign
        """
        bpy = self._get_bpy()
        if bpy is None:
            return

        for slot in mesh.material_slots:
            if slot.material and slot.material.use_nodes:
                nodes = slot.material.node_tree.nodes
                # Find or create Image Texture node
                img_node = None
                for node in nodes:
                    if node.type == "TEX_IMAGE":
                        img_node = node
                        break

                if img_node is None:
                    img_node = nodes.new("ShaderNodeTexImage")

                img_node.image = bake_image
                # Make active for baking
                slot.material.node_tree.nodes.active = img_node

    def bake_for_unreal(
        self,
        material_name: str,
        mesh_name: str,
        output_dir: str,
        lod_level: int = 0,
    ) -> Dict[str, str]:
        """
        Bake textures optimized for Unreal Engine import.

        Args:
            material_name: Name of material to bake
            mesh_name: Name of mesh with material
            output_dir: Output directory
            lod_level: LOD level (0=highest, affects resolution)

        Returns:
            Dictionary mapping texture type to file path
        """
        # Adjust resolution based on LOD
        base_resolution = self.config.resolution
        lod_resolution = max(512, base_resolution // (2**lod_level))

        # Create LOD-specific config
        lod_config = BakeConfig(
            resolution=lod_resolution,
            bake_albedo=True,
            bake_normal=True,
            bake_roughness=True,
            bake_sss=True,
            bake_emission=self.config.bake_emission,
            output_format="PNG",
            output_directory=output_dir,
            denoise=self.config.denoise,
            samples=self.config.samples,
        )

        baker = TextureBaker(lod_config)
        prefix = f"LOD{lod_level}_{material_name}_"

        result = baker.bake(material_name, mesh_name, prefix)

        textures = {}
        if result.albedo_path:
            textures["BaseColor"] = result.albedo_path
        if result.normal_path:
            textures["Normal"] = result.normal_path
        if result.roughness_path:
            textures["Roughness"] = result.roughness_path
        if result.sss_path:
            textures["SubsurfaceColor"] = result.sss_path
        if result.emission_path:
            textures["Emissive"] = result.emission_path

        return textures


def bake_material(
    material_name: str,
    mesh_name: str,
    output_dir: str,
    resolution: int = 2048,
    bake_types: Optional[List[str]] = None,
) -> BakeResult:
    """
    Convenience function to bake a material's textures.

    Args:
        material_name: Name of material to bake
        mesh_name: Name of mesh with material applied
        output_dir: Output directory for textures
        resolution: Bake resolution in pixels
        bake_types: List of types to bake (albedo, normal, roughness, sss, emission)

    Returns:
        BakeResult with paths to baked textures
    """
    bake_types = bake_types or ["albedo", "normal", "roughness", "sss"]

    config = BakeConfig(
        resolution=resolution,
        bake_albedo="albedo" in bake_types,
        bake_normal="normal" in bake_types,
        bake_roughness="roughness" in bake_types,
        bake_sss="sss" in bake_types,
        bake_emission="emission" in bake_types,
        output_directory=output_dir,
    )

    baker = TextureBaker(config)
    return baker.bake(material_name, mesh_name)


def bake_all_lods(
    material_name: str,
    mesh_name: str,
    output_dir: str,
    base_resolution: int = 2048,
    lod_count: int = 4,
) -> Dict[int, Dict[str, str]]:
    """
    Bake textures for all LOD levels.

    Args:
        material_name: Name of material to bake
        mesh_name: Name of mesh with material
        output_dir: Output directory
        base_resolution: Base resolution for LOD0
        lod_count: Number of LOD levels to generate

    Returns:
        Dictionary mapping LOD level to texture paths
    """
    results = {}

    for lod in range(lod_count):
        config = BakeConfig(
            resolution=max(512, base_resolution // (2**lod)),
            bake_albedo=True,
            bake_normal=True,
            bake_roughness=True,
            bake_sss=True,
            bake_emission=False,
            output_directory=output_dir,
        )

        baker = TextureBaker(config)
        prefix = f"LOD{lod}_"
        result = baker.bake(material_name, mesh_name, prefix)

        textures = {}
        if result.albedo_path:
            textures["BaseColor"] = result.albedo_path
        if result.normal_path:
            textures["Normal"] = result.normal_path
        if result.roughness_path:
            textures["Roughness"] = result.roughness_path
        if result.sss_path:
            textures["SubsurfaceColor"] = result.sss_path

        results[lod] = textures

    return results
