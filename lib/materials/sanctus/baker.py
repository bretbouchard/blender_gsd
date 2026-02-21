"""
Sanctus Baker - Texture Baking Utilities
========================================

Texture baking utilities for converting procedural materials
to baked textures for game engines and optimized rendering.

Supports:
- Multi-channel baking (diffuse, normal, roughness, metallic, AO)
- UDIM tile baking
- Game engine export (Unreal, Unity)
- Custom resolution and format options
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
import os
import json

try:
    import bpy
    from bpy.types import Image, Material, Object, ShaderNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Image = Any
    Material = Any
    Object = Any
    ShaderNodeTree = Any


class BakeChannel(Enum):
    """Texture channels for baking."""
    DIFFUSE = "diffuse"
    ALBEDO = "albedo"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AO = "ao"
    EMISSION = "emission"
    HEIGHT = "height"
    CURVATURE = "curvature"
    SPECULAR = "specular"
    GLOSSINESS = "glossiness"
    OPACITY = "opacity"
    SUBSURFACE = "subsurface"


class ExportEngine(Enum):
    """Target game engines for export."""
    UNREAL = "unreal"
    UNITY = "unity"
    GODOT = "godot"
    GLTF = "gltf"
    CUSTOM = "custom"


@dataclass
class BakeSettings:
    """Settings for texture baking."""
    resolution: int = 2048
    samples: int = 1
    margin: int = 16
    bake_type: str = "EMIT"
    use_clear: bool = True
    use_selected_to_active: bool = False
    cage_extrusion: float = 0.0
    max_ray_distance: float = 0.0
    use_pass_direct: bool = True
    use_pass_indirect: bool = True
    use_pass_color: bool = True
    device: str = "CPU"  # or "GPU"


class SanctusBaker:
    """
    Bake procedural materials to textures.

    Provides comprehensive texture baking capabilities for
    converting procedural materials to game-ready textures.
    """

    # Channel to bake type mapping
    CHANNEL_BAKE_MAP = {
        BakeChannel.DIFFUSE: "DIFFUSE",
        BakeChannel.ALBEDO: "DIFFUSE",
        BakeChannel.NORMAL: "NORMAL",
        BakeChannel.ROUGHNESS: "ROUGHNESS",
        BakeChannel.METALLIC: "METALLIC",
        BakeChannel.AO: "AO",
        BakeChannel.EMISSION: "EMIT",
        BakeChannel.HEIGHT: "DISPLACEMENT",
        BakeChannel.CURVATURE: "CURVATURE",
        BakeChannel.SPECULAR: "SPECULAR",
        BakeChannel.GLOSSINESS: "GLOSSINESS",
    }

    # Game engine naming conventions
    ENGINE_NAMING = {
        ExportEngine.UNREAL: {
            BakeChannel.DIFFUSE: "{name}_BaseColor",
            BakeChannel.NORMAL: "{name}_Normal",
            BakeChannel.ROUGHNESS: "{name}_Roughness",
            BakeChannel.METALLIC: "{name}_Metallic",
            BakeChannel.AO: "{name}_AO",
            BakeChannel.EMISSION: "{name}_Emissive",
            BakeChannel.HEIGHT: "{name}_Height",
            BakeChannel.OPACITY: "{name}_Opacity",
        },
        ExportEngine.UNITY: {
            BakeChannel.DIFFUSE: "{name}_Albedo",
            BakeChannel.NORMAL: "{name}_Normal",
            BakeChannel.ROUGHNESS: "{name}_Smoothness",  # Inverted
            BakeChannel.METALLIC: "{name}_Metallic",
            BakeChannel.AO: "{name}_Occlusion",
            BakeChannel.EMISSION: "{name}_Emission",
            BakeChannel.HEIGHT: "{name}_Height",
            BakeChannel.OPACITY: "{name}_Alpha",
        },
        ExportEngine.GODOT: {
            BakeChannel.DIFFUSE: "{name}_albedo",
            BakeChannel.NORMAL: "{name}_normal",
            BakeChannel.ROUGHNESS: "{name}_roughness",
            BakeChannel.METALLIC: "{name}_metallic",
            BakeChannel.AO: "{name}_ao",
            BakeChannel.EMISSION: "{name}_emission",
            BakeChannel.HEIGHT: "{name}_height",
            BakeChannel.OPACITY: "{name}_alpha",
        },
        ExportEngine.GLTF: {
            BakeChannel.DIFFUSE: "{name}_baseColor",
            BakeChannel.NORMAL: "{name}_normal",
            BakeChannel.ROUGHNESS: "{name}_roughness",
            BakeChannel.METALLIC: "{name}_metallicRoughness",
            BakeChannel.AO: "{name}_occlusion",
            BakeChannel.EMISSION: "{name}_emissive",
        },
    }

    # Engine-specific texture packing
    ENGINE_PACKING = {
        ExportEngine.UNREAL: {
            "ORM": [BakeChannel.AO, BakeChannel.ROUGHNESS, BakeChannel.METALLIC],
        },
        ExportEngine.UNITY: {
            "MetallicGloss": [
                (BakeChannel.METALLIC, "R"),
                (BakeChannel.ROUGHNESS, "A"),  # Smoothness in alpha
            ],
        },
        ExportEngine.GLTF: {
            "MetallicRoughness": [
                (BakeChannel.ROUGHNESS, "G"),
                (BakeChannel.METALLIC, "B"),
            ],
        },
    }

    def __init__(self, material: Optional[Material] = None):
        """
        Initialize the baker.

        Args:
            material: Optional material to bake
        """
        self.material = material
        self.settings = BakeSettings()
        self._baked_textures: Dict[str, Image] = {}

    def bake_all(
        self,
        resolution: int = 2048,
        output_path: Optional[str] = None,
        channels: Optional[List[BakeChannel]] = None,
    ) -> Dict[str, str]:
        """
        Bake all common texture channels.

        Args:
            resolution: Texture resolution
            output_path: Directory to save textures
            channels: List of channels to bake (default: common channels)

        Returns:
            Dictionary mapping channel names to file paths
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for baking")

        if channels is None:
            channels = [
                BakeChannel.DIFFUSE,
                BakeChannel.NORMAL,
                BakeChannel.ROUGHNESS,
                BakeChannel.METALLIC,
                BakeChannel.AO,
            ]

        results = {}

        for channel in channels:
            try:
                image = self.bake_channel(channel, resolution)
                if image and output_path:
                    filepath = self._save_texture(image, channel, output_path)
                    results[channel.value] = filepath
                elif image:
                    results[channel.value] = image.name
            except Exception as e:
                print(f"Failed to bake {channel.value}: {e}")
                results[channel.value] = None

        return results

    def bake_channel(
        self,
        channel: BakeChannel,
        resolution: int = 2048,
        samples: int = 1,
    ) -> Optional[Image]:
        """
        Bake a single texture channel.

        Args:
            channel: Channel to bake
            resolution: Texture resolution
            samples: Number of AA samples

        Returns:
            Baked image or None on failure
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for baking")

        if not self.material:
            raise ValueError("No material set for baking")

        # Create bake image
        image_name = f"{self.material.name}_{channel.value}"
        image = bpy.data.images.new(
            name=image_name,
            width=resolution,
            height=resolution,
            alpha=True,
        )

        # Setup for baking
        self._setup_bake_target(image)

        # Configure bake settings
        bpy.context.scene.render.bake_type = self.CHANNEL_BAKE_MAP.get(
            channel, "EMIT"
        )
        bpy.context.scene.render.bake.margin = self.settings.margin
        bpy.context.scene.render.bake.use_clear = self.settings.use_clear

        # Bake
        try:
            bpy.ops.object.bake(type=bpy.context.scene.render.bake_type)
            self._baked_textures[channel.value] = image
            return image
        except Exception as e:
            print(f"Bake failed: {e}")
            bpy.data.images.remove(image)
            return None

    def bake_to_udim(
        self,
        resolution: int = 2048,
        tile_range: Tuple[int, int] = (1001, 1010),
        output_path: Optional[str] = None,
    ) -> Dict[int, Dict[str, str]]:
        """
        Bake textures to UDIM tiles.

        Args:
            resolution: Texture resolution per tile
            tile_range: Range of UDIM tiles (1001-1010, etc.)
            output_path: Directory to save textures

        Returns:
            Dictionary mapping tile numbers to texture paths
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for baking")

        results = {}

        for tile in range(tile_range[0], tile_range[1] + 1):
            tile_results = {}

            # Create UDIM image
            image_name = f"{self.material.name}_tile_{tile}"
            image = bpy.data.images.new(
                name=image_name,
                width=resolution,
                height=resolution,
                tiled=True,
            )

            # Setup UDIM tile
            try:
                # Set active UDIM tile
                bpy.context.scene.uvedit_tile = tile

                # Bake each channel
                for channel in [BakeChannel.DIFFUSE, BakeChannel.NORMAL,
                                BakeChannel.ROUGHNESS, BakeChannel.METALLIC]:
                    baked = self.bake_channel(channel, resolution)
                    if baked:
                        if output_path:
                            tile_results[channel.value] = self._save_texture(
                                baked, channel, output_path, tile
                            )
                        else:
                            tile_results[channel.value] = baked.name

                results[tile] = tile_results
            except Exception as e:
                print(f"Failed to bake UDIM tile {tile}: {e}")
                results[tile] = None

        return results

    def export_for_game(
        self,
        engine: Union[ExportEngine, str] = "unreal",
        resolution: int = 1024,
        output_path: Optional[str] = None,
        pack_channels: bool = True,
    ) -> Dict[str, str]:
        """
        Export textures optimized for a game engine.

        Args:
            engine: Target game engine
            resolution: Texture resolution
            output_path: Directory to save textures
            pack_channels: Whether to pack channels per engine conventions

        Returns:
            Dictionary mapping texture names to file paths
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for baking")

        if isinstance(engine, str):
            engine = ExportEngine(engine.lower())

        # Get channels needed for this engine
        channels = self._get_engine_channels(engine)

        # Bake all required channels
        baked = self.bake_all(
            resolution=resolution,
            output_path=output_path,
            channels=channels,
        )

        results = {}

        # Rename according to engine conventions
        naming = self.ENGINE_NAMING.get(engine, {})
        material_name = self.material.name if self.material else "material"

        for channel, filepath in baked.items():
            if filepath:
                channel_enum = BakeChannel(channel)
                if channel_enum in naming:
                    new_name = naming[channel_enum].format(name=material_name)
                    results[new_name] = filepath
                else:
                    results[f"{material_name}_{channel}"] = filepath

        # Pack channels if requested
        if pack_channels:
            packed = self._pack_channels(baked, engine, output_path)
            results.update(packed)

        return results

    def _get_engine_channels(self, engine: ExportEngine) -> List[BakeChannel]:
        """Get required channels for an engine."""
        base_channels = [
            BakeChannel.DIFFUSE,
            BakeChannel.NORMAL,
            BakeChannel.ROUGHNESS,
            BakeChannel.METALLIC,
        ]

        engine_extra = {
            ExportEngine.UNREAL: [BakeChannel.AO, BakeChannel.EMISSION],
            ExportEngine.UNITY: [BakeChannel.AO],
            ExportEngine.GODOT: [BakeChannel.AO, BakeChannel.EMISSION],
            ExportEngine.GLTF: [BakeChannel.AO, BakeChannel.EMISSION],
        }

        return base_channels + engine_extra.get(engine, [])

    def _pack_channels(
        self,
        baked: Dict[str, str],
        engine: ExportEngine,
        output_path: Optional[str],
    ) -> Dict[str, str]:
        """Pack channels according to engine conventions."""
        if not BLENDER_AVAILABLE:
            return {}

        results = {}
        packing = self.ENGINE_PACKING.get(engine, {})

        for pack_name, channels in packing.items():
            # Create packed texture
            # This is simplified - actual implementation would
            # composite multiple textures into one
            pass

        return results

    def _setup_bake_target(self, image: Image) -> None:
        """Setup material nodes for baking to target image."""
        if not self.material or not self.material.use_nodes:
            return

        node_tree = self.material.node_tree
        nodes = node_tree.nodes

        # Find or create texture node
        tex_node = None
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image == image:
                tex_node = node
                break

        if not tex_node:
            tex_node = nodes.new('ShaderNodeTexImage')

        tex_node.image = image
        tex_node.select = True
        nodes.active = tex_node

    def _save_texture(
        self,
        image: Image,
        channel: BakeChannel,
        output_path: str,
        tile: Optional[int] = None,
    ) -> str:
        """Save a baked texture to disk."""
        if not BLENDER_AVAILABLE:
            return ""

        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Generate filename
        material_name = self.material.name if self.material else "material"
        if tile:
            filename = f"{material_name}_{channel.value}_tile_{tile}.png"
        else:
            filename = f"{material_name}_{channel.value}.png"

        filepath = os.path.join(output_path, filename)

        # Save image
        image.filepath_raw = filepath
        image.file_format = 'PNG'
        bpy.ops.image.save_as(save_as_render=True, filepath=filepath)

        return filepath

    def bake_curvature_map(
        self,
        resolution: int = 2048,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Bake a curvature map for masking effects.

        Args:
            resolution: Texture resolution
            output_path: Directory to save texture

        Returns:
            File path to baked curvature map
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for baking")

        # Curvature baking requires geometry nodes or bevel shader trick
        # This is a simplified placeholder
        return self.bake_channel(BakeChannel.CURVATURE, resolution)

    def bake_height_map(
        self,
        resolution: int = 2048,
        output_path: Optional[str] = None,
        subdivision_levels: int = 5,
    ) -> Optional[str]:
        """
        Bake a height/displacement map.

        Args:
            resolution: Texture resolution
            output_path: Directory to save texture
            subdivision_levels: Subdivision for displacement

        Returns:
            File path to baked height map
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for baking")

        return self.bake_channel(BakeChannel.HEIGHT, resolution)

    def create_normal_from_height(
        self,
        height_image: Image,
        strength: float = 1.0,
    ) -> Optional[Image]:
        """
        Create a normal map from a height map.

        Args:
            height_image: Source height/displacement image
            strength: Normal map strength

        Returns:
            Generated normal map image
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for image processing")

        # Create new image for normal map
        normal_name = f"{height_image.name}_normal"
        normal_image = bpy.data.images.new(
            name=normal_name,
            width=height_image.size[0],
            height=height_image.size[1],
        )

        # Get height pixels and compute normal
        # This is a simplified Sobel filter implementation
        height_pixels = list(height_image.pixels)
        width = height_image.size[0]
        height = height_image.size[1]
        normal_pixels = [0.0] * (width * height * 4)

        for y in range(height):
            for x in range(width):
                # Get surrounding heights
                idx = (y * width + x) * 4

                # Sobel operator
                left = height_pixels[max(0, idx - 4)] if x > 0 else height_pixels[idx]
                right = height_pixels[min(width * 4 - 4, idx + 4)] if x < width - 1 else height_pixels[idx]
                top = height_pixels[max(0, idx - width * 4)] if y > 0 else height_pixels[idx]
                bottom = height_pixels[min(height * width * 4 - 4, idx + width * 4)] if y < height - 1 else height_pixels[idx]

                # Compute normal
                dx = (right - left) * strength
                dy = (bottom - top) * strength

                # Normalize
                length = (dx * dx + dy * dy + 1) ** 0.5

                normal_idx = idx
                normal_pixels[normal_idx] = (dx / length + 1) * 0.5  # R
                normal_pixels[normal_idx + 1] = (dy / length + 1) * 0.5  # G
                normal_pixels[normal_idx + 2] = (1 / length + 1) * 0.5  # B
                normal_pixels[normal_idx + 3] = 1.0  # A

        normal_image.pixels = normal_pixels
        return normal_image

    def invert_roughness(
        self,
        roughness_image: Image,
    ) -> Optional[Image]:
        """
        Invert a roughness map to create a glossiness map.

        Args:
            roughness_image: Source roughness image

        Returns:
            Inverted glossiness image
        """
        if not BLENDER_AVAILABLE:
            return None

        gloss_name = f"{roughness_image.name}_gloss"
        gloss_image = bpy.data.images.new(
            name=gloss_name,
            width=roughness_image.size[0],
            height=roughness_image.size[1],
        )

        pixels = list(roughness_image.pixels)
        inverted = [0.0] * len(pixels)

        for i in range(0, len(pixels), 4):
            inverted[i] = 1.0 - pixels[i]
            inverted[i + 1] = 1.0 - pixels[i + 1]
            inverted[i + 2] = 1.0 - pixels[i + 2]
            inverted[i + 3] = pixels[i + 3]

        gloss_image.pixels = inverted
        return gloss_image

    def create_ao_from_curvature(
        self,
        curvature_image: Image,
        blur_amount: float = 0.0,
    ) -> Optional[Image]:
        """
        Create an AO map from a curvature map.

        Args:
            curvature_image: Source curvature image
            blur_amount: Amount of blur to apply

        Returns:
            Generated AO image
        """
        if not BLENDER_AVAILABLE:
            return None

        ao_name = f"{curvature_image.name}_ao"
        ao_image = bpy.data.images.new(
            name=ao_name,
            width=curvature_image.size[0],
            height=curvature_image.size[1],
        )

        # Copy curvature as AO (simplified)
        pixels = list(curvature_image.pixels)
        ao_image.pixels = pixels

        return ao_image

    def get_baked_texture(
        self,
        channel: Union[BakeChannel, str],
    ) -> Optional[Image]:
        """
        Get a previously baked texture.

        Args:
            channel: Channel to retrieve

        Returns:
            Baked image or None
        """
        if isinstance(channel, BakeChannel):
            channel = channel.value
        return self._baked_textures.get(channel)

    def clear_baked_textures(self) -> None:
        """Clear all cached baked textures."""
        if BLENDER_AVAILABLE:
            for image in self._baked_textures.values():
                if image:
                    try:
                        bpy.data.images.remove(image)
                    except Exception:
                        pass
        self._baked_textures.clear()

    def export_texture_set(
        self,
        output_path: str,
        engine: ExportEngine = ExportEngine.UNREAL,
        resolution: int = 2048,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Export a complete texture set with metadata.

        Args:
            output_path: Directory to export to
            engine: Target engine
            resolution: Texture resolution
            include_metadata: Export metadata JSON

        Returns:
            Dictionary with export results
        """
        results = self.export_for_game(
            engine=engine,
            resolution=resolution,
            output_path=output_path,
        )

        if include_metadata:
            metadata = {
                "material_name": self.material.name if self.material else "unknown",
                "engine": engine.value,
                "resolution": resolution,
                "textures": results,
                "channels": list(self._baked_textures.keys()),
            }

            metadata_path = os.path.join(output_path, "texture_set_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            results["metadata"] = metadata_path

        return results
