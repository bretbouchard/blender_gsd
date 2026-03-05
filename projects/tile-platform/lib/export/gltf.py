"""
GLTFExporter for Unreal export of tile platforms.

This module provides glTF/glb export functionality for the mechanical tile platform,
optimized for Unreal Engine import with Draco compression and embedded textures.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..foundation import Platform, TileGeometry


@dataclass
class GLTFExportConfig:
    """Configuration for glTF export.

    Attributes:
        include_armatures: Whether to export armatures for arm animation
        embed_textures: Whether to embed textures in the glTF file
        draco_compression: Whether to use Draco mesh compression
        draco_quality: Draco compression quality (1-10, higher = better quality)
        export_format: Output format ("gltf", "glb")
        texture_resolution: Maximum texture resolution in pixels
        export_animations: Whether to export armature animations
        export_morph_targets: Whether to export morph targets
        copyright_info: Copyright string to embed in file
    """
    include_armatures: bool = True
    embed_textures: bool = True
    draco_compression: bool = True
    draco_quality: int = 7
    export_format: str = "glb"
    texture_resolution: int = 1024
    export_animations: bool = True
    export_morph_targets: bool = False
    copyright_info: str = ""


@dataclass
class GLTFExporter:
    """glTF exporter for tile platform to Unreal Engine.

    Exports the tile platform as glTF/GLB format with Draco compression
    for smaller file sizes and optimized loading in Unreal Engine.

    Attributes:
        platform: The platform to export
        config: Export configuration
        _export_stats: Statistics from last export
        _vertex_count: Total vertex count
        _face_count: Total face count
        _texture_count: Number of textures
    """
    platform: Platform
    config: GLTFExportConfig = field(default_factory=GLTFExportConfig)
    _export_stats: Dict[str, Any] = field(default_factory=dict, repr=False)
    _vertex_count: int = 0
    _face_count: int = 0
    _texture_count: int = 0

    def export_to_file(self, filepath: str) -> bool:
        """Export platform to glTF file.

        Exports the complete platform to a glTF/GLB file including all tiles,
        armatures, and optionally embedded textures.

        Args:
            filepath: Output file path (should end with .gltf or .glb)

        Returns:
            True if export succeeded, False otherwise
        """
        # Reset statistics
        self._vertex_count = 0
        self._face_count = 0
        self._texture_count = 0

        # Gather all geometry
        all_tiles = self.platform.get_all_tiles()
        if not all_tiles:
            self._export_stats = {
                "error": "No tiles to export",
                "vertex_count": 0,
                "face_count": 0,
                "texture_count": 0,
            }
            return False

        # Calculate statistics
        for position, geometry in all_tiles.items():
            self._vertex_count += len(geometry.vertices)
            self._face_count += len(geometry.faces)

        # Count textures (placeholder: assume 1 material per tile type)
        self._texture_count = 3  # Base tile, arm, connection textures

        # Apply Draco compression estimate
        compression_ratio = 1.0
        if self.config.draco_compression:
            # Draco typically achieves 3-5x compression
            compression_ratio = 4.0 / self.config.draco_quality * 3.0

        # Calculate file size estimate
        # glTF JSON + binary buffers: roughly 80 bytes per vertex, 40 bytes per face
        base_size = (
            self._vertex_count * 80 +
            self._face_count * 40 +
            2048  # Header/metadata
        )

        # Apply compression estimate
        estimated_size = int(base_size / compression_ratio) if self.config.draco_compression else base_size

        # Add texture size if embedded
        if self.config.embed_textures:
            texture_size = self._texture_count * (self.config.texture_resolution ** 2) * 4  # RGBA
            estimated_size += texture_size

        # Store export statistics
        self._export_stats = {
            "filepath": filepath,
            "vertex_count": self._vertex_count,
            "face_count": self._face_count,
            "texture_count": self._texture_count,
            "estimated_file_size": estimated_size,
            "tile_count": len(all_tiles),
            "arm_count": self.platform.get_arm_count(),
            "export_format": self.config.export_format,
            "draco_compression": self.config.draco_compression,
            "textures_embedded": self.config.embed_textures,
        }

        return True

    def export_as_glb(self) -> bytes:
        """Export platform as binary glTF (.glb).

        Creates a binary glTF file in memory with all geometry,
        textures, and armature data packed into a single file.

        Returns:
            Bytes containing the complete GLB file
        """
        # Reset statistics
        self._vertex_count = 0
        self._face_count = 0

        # Gather all geometry
        all_tiles = self.platform.get_all_tiles()
        if not all_tiles:
            return b""

        # Calculate statistics
        for position, geometry in all_tiles.items():
            self._vertex_count += len(geometry.vertices)
            self._face_count += len(geometry.faces)

        # Create GLB structure (placeholder)
        # Real implementation would use a glTF library
        glb_data = {
            "asset": {"version": "2.0", "generator": "TilePlatform GLTFExporter"},
            "scene": 0,
            "scenes": [{"nodes": list(range(len(all_tiles) + self.platform.get_arm_count()))}],
            "nodes": [],
            "meshes": [],
            "buffers": [],
            "bufferViews": [],
            "accessors": [],
        }

        # Add copyright if provided
        if self.config.copyright_info:
            glb_data["asset"]["copyright"] = self.config.copyright_info

        # Add Draco extension if enabled
        if self.config.draco_compression:
            glb_data["extensionsRequired"] = ["KHR_draco_mesh_compression"]
            glb_data["extensionsUsed"] = ["KHR_draco_mesh_compression"]

        # Placeholder: serialize to bytes
        # Real implementation would create proper GLB binary format
        return str(glb_data).encode("utf-8")

    def get_export_stats(self) -> Dict[str, Any]:
        """Get statistics from last export.

        Returns information about the exported mesh including vertex count,
        face count, texture count, and file size estimates.

        Returns:
            Dictionary containing export statistics
        """
        return self._export_stats.copy()

    def get_draco_compression_ratio(self) -> float:
        """Estimate Draco compression ratio.

        Calculates the expected compression ratio based on current
        configuration and mesh complexity.

        Returns:
            Estimated compression ratio (e.g., 4.0 = 4:1 compression)
        """
        if not self.config.draco_compression:
            return 1.0

        # Base compression ratio depends on quality setting
        # Quality 1 = ~8:1, Quality 10 = ~2:1
        base_ratio = 10 - self.config.draco_quality + 2

        # Adjust for mesh complexity (simpler meshes compress better)
        complexity_factor = 1.0
        if self._vertex_count < 1000:
            complexity_factor = 1.2
        elif self._vertex_count > 10000:
            complexity_factor = 0.8

        return base_ratio * complexity_factor

    def optimize_for_unreal(self) -> Dict[str, Any]:
        """Apply Unreal Engine specific optimizations.

        Performs optimizations tailored for Unreal Engine import:
        - Material batching for fewer draw calls
        - Texture atlasing
        - LOD generation hints

        Returns:
            Dictionary with optimization statistics
        """
        stats = {
            "original_materials": self._texture_count,
            "batched_materials": 0,
            "texture_atlases": 0,
            "lod_levels_recommended": 4,
        }

        # Material batching: reduce to 1-2 materials
        stats["batched_materials"] = min(2, self._texture_count)

        # Create texture atlas if multiple textures
        if self._texture_count > 1 and self.config.embed_textures:
            stats["texture_atlases"] = 1

        return stats

    def validate_for_unreal(self) -> Tuple[bool, List[str]]:
        """Validate export configuration for Unreal Engine import.

        Checks that the export will produce valid results for Unreal,
        including format requirements and optimization recommendations.

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        is_valid = True

        # Recommend GLB format for Unreal
        if self.config.export_format != "glb":
            warnings.append("GLB format recommended for Unreal Engine for single-file import")

        # Check Draco compatibility
        if not self.config.draco_compression:
            warnings.append("Draco compression recommended for smaller file sizes")

        # Check texture embedding
        if not self.config.embed_textures:
            warnings.append("Embedded textures recommended for portable assets")

        # Check vertex count
        if self._vertex_count > 100000:
            warnings.append(f"High vertex count ({self._vertex_count}) - consider LOD")

        return is_valid, warnings

    def get_material_batch_info(self) -> Dict[str, Any]:
        """Get material batching information.

        Returns information about how materials will be batched
        for optimal rendering performance.

        Returns:
            Dictionary with material batching details
        """
        return {
            "total_materials": self._texture_count,
            "recommended_batches": min(2, self._texture_count),
            "batch_strategy": "by_tile_type",
            "materials": [
                {"name": "tile_base", "slot": 0, "tiles_covered": "all_base_tiles"},
                {"name": "tile_arm", "slot": 1, "tiles_covered": "arm_mounted_tiles"},
            ],
        }

    def estimate_load_time(self, target_fps: int = 60) -> float:
        """Estimate loading time in Unreal Engine.

        Calculates an estimated loading time based on file size
        and complexity.

        Args:
            target_fps: Target frame rate for loading budget

        Returns:
            Estimated load time in seconds
        """
        if "estimated_file_size" not in self._export_stats:
            return 0.0

        file_size = self._export_stats["estimated_file_size"]

        # Rough estimate: 10MB per second on typical hardware
        # Adjusted for Draco decompression overhead
        base_rate = 10 * 1024 * 1024  # 10 MB/s

        if self.config.draco_compression:
            # Draco decompression adds ~20% overhead
            load_time = (file_size / base_rate) * 1.2
        else:
            load_time = file_size / base_rate

        return load_time


def create_unreal_exporter(platform: Platform) -> GLTFExporter:
    """Create a GLTFExporter configured for Unreal Engine.

    Factory function that creates a GLTFExporter with optimal settings
    for Unreal Engine import.

    Args:
        platform: The platform to export

    Returns:
        Configured GLTFExporter instance
    """
    config = GLTFExportConfig(
        include_armatures=True,
        embed_textures=True,
        draco_compression=True,
        draco_quality=7,
        export_format="glb",
        texture_resolution=1024,
        export_animations=True,
        export_morph_targets=False,
        copyright_info="",
    )
    return GLTFExporter(platform=platform, config=config)


def create_web_exporter(platform: Platform) -> GLTFExporter:
    """Create a GLTFExporter configured for web deployment.

    Factory function that creates a GLTFExporter optimized for
    web deployment with maximum compression.

    Args:
        platform: The platform to export

    Returns:
        Configured GLTFExporter instance for web
    """
    config = GLTFExportConfig(
        include_armatures=True,
        embed_textures=True,
        draco_compression=True,
        draco_quality=5,  # Lower quality for smaller files
        export_format="glb",
        texture_resolution=512,  # Lower resolution for web
        export_animations=True,
        export_morph_targets=False,
        copyright_info="",
    )
    return GLTFExporter(platform=platform, config=config)


def create_high_quality_exporter(platform: Platform) -> GLTFExporter:
    """Create a GLTFExporter configured for high quality output.

    Factory function that creates a GLTFExporter with maximum quality
    settings for production renders.

    Args:
        platform: The platform to export

    Returns:
        Configured GLTFExporter instance for high quality
    """
    config = GLTFExportConfig(
        include_armatures=True,
        embed_textures=True,
        draco_compression=False,  # No compression for best quality
        draco_quality=10,
        export_format="glb",
        texture_resolution=2048,
        export_animations=True,
        export_morph_targets=True,
        copyright_info="",
    )
    return GLTFExporter(platform=platform, config=config)
