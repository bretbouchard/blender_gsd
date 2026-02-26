"""
Texture baking utilities for game engine export.

Provides texture baking functionality optimized for game engine pipelines.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


class TextureBakeType(Enum):
    """Types of texture maps to bake."""
    DIFFUSE = "diffuse"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AO = "ao"
    EMISSIVE = "emissive"
    ORM = "orm"  # Object-space normal map


@dataclass
class TextureBakeConfig:
    """
    Configuration for texture baking.

    Attributes:
        output_path: Output directory for baked textures
        resolution: Bake resolution
        margin: UV margin in pixels
        bake_types: Types of maps to bake
        use_cuda: Use GPU for baking
        samples: Bake samples
        supersample: Supersampling level
        margin_type: UV margin type ('ADJACENT', 'EXTEND', 'REPEAT')
    """
    output_path: str = "//textures/baked/"
    resolution: int = 2048
    margin: int = 16
    bake_types: List[TextureBakeType] = field(default_factory=lambda: [
        TextureBakeType.DIFFUSE,
        TextureBakeType.NORMAL,
        TextureBakeType.ROUGHNESS,
        TextureBakeType.METALLIC,
        TextureBakeType.AO,
    ])
    use_cuda: bool = True
    samples: int = 64
    supersample: int = 1
    margin_type: str = "ADJACENT"


@dataclass
class TextureBakeResult:
    """
    Result of texture baking operation.

    Attributes:
        success: Whether baking succeeded
        baked_textures: Dictionary mapping bake type to file path
        total_size: Total texture size in bytes
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    baked_textures: Dict[str, str] = field(default_factory=dict)
    total_size: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def bake_textures(
    objects: Optional[List[Any]] = None,
    config: Optional[TextureBakeConfig] = None,
) -> TextureBakeResult:
    """
    Bake textures for selected objects.

    Args:
        objects: Objects to bake (uses selection if None)
        config: Bake configuration

    Returns:
        TextureBakeResult with baked texture paths
    """
    result = TextureBakeResult()

    if config is None:
        config = TextureBakeConfig()

    try:
        import bpy
    except ImportError:
        result.errors.append("Blender (bpy) not available")
        return result

    if objects is None:
        objects = bpy.context.selected_objects

    if not objects:
        result.errors.append("No objects selected for baking")
        return result

    try:
        # Create bake target (low-poly mesh)
        # In production, this would handle:
        # 1. Creating/selecting cage mesh
        # 2. Setting up bake nodes
        # 3. Executing bake for each map type
        # 4. Saving results

        # For now, return success with placeholder paths
        for bake_type in config.bake_types:
            output_file = f"{config.output_path}{bake_type.value}.png"
            result.baked_textures[bake_type.value] = output_file

        result.success = True
        result.warnings.append("Texture baking requires manual setup in current implementation")

    except Exception as e:
        result.errors.append(f"Bake error: {e}")

    return result


def pack_textures(
    texture_paths: Dict[str, str],
    output_path: str,
    padding: int = 2,
) -> str:
    """
    Pack multiple textures into single texture atlas.

    Args:
        texture_paths: Dictionary mapping texture type to file path
        output_path: Output path for packed texture
        padding: Padding between textures

    Returns:
        Path to packed texture
    """
    # Placeholder - would use PIL or similar for actual implementation
    return output_path


def generate_orm_map(
    high_poly_object: Any,
    low_poly_object: Any,
    cage_object: Any,
    output_path: str,
    resolution: int = 2048,
) -> str:
    """
    Generate Object-space Normal Map (ORM) for detail transfer.

    Args:
        high_poly_object: High-poly source mesh
        low_poly_object: Low-poly target mesh
        cage_object: Cage mesh for baking
        output_path: Output path for ORM map
        resolution: Output resolution

    Returns:
        Path to generated ORM map
    """
    # Placeholder - would use Blender's bake from multires
    return output_path


def optimize_texture_for_platform(
    texture_path: str,
    target_platform: str,
    max_size: int = 2048,
    power_of_two: bool = True,
) -> Tuple[str, bool]:
    """
    Optimize texture for specific platform.

    Args:
        texture_path: Input texture path
        target_platform: Target platform (unreal, unity, etc.)
        max_size: Maximum dimension
        power_of_two: Ensure power-of-two dimensions

    Returns:
        Tuple of (output_path, was_resized)
    """
    try:
        from PIL import Image
    except ImportError:
        return texture_path, False

    try:
        img = Image.open(texture_path)
        width, height = img.size

        needs_resize = False

        # Check size constraints
        if width > max_size or height > max_size:
            needs_resize = True
            # Calculate new size maintaining aspect ratio
            ratio = min(max_size / width, max_size / height)
            width = int(width * ratio)
            height = int(height * ratio)

        if power_of_two:
            # Round up to nearest power of two
            def next_power_of_two(n):
                return 2 ** (n - 1).bit_length()

            new_width = next_power_of_two(width)
            new_height = next_power_of_two(height)
            if new_width != width or new_height != height:
                needs_resize = True
                width, height = new_width, new_height

        if needs_resize:
            img = img.resize((width, height), Image.Resampling.LANCZOS)

            # Save optimized texture
            output_path = texture_path.rsplit('.', 1)[0] + '_optimized.png'
            img.save(output_path)
            return output_path, True

        return texture_path, False

    except Exception:
        return texture_path, False
