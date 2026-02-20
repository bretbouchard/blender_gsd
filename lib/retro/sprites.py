"""
Sprite Sheet Generator

Provides sprite sheet generation from animation frames with
trimming, pivot calculation, and multiple export formats.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List, TYPE_CHECKING
import math

from lib.retro.isometric_types import SpriteSheetConfig, SpriteSheetResult

if TYPE_CHECKING:
    try:
        from PIL import Image
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False

    try:
        import numpy as np
        HAS_NUMPY = True
    except ImportError:
        HAS_NUMPY = False


# =============================================================================
# SPRITE FRAME DATA
# =============================================================================

@dataclass
class SpriteFrame:
    """
    Single sprite frame data.

    Attributes:
        image: Frame image data
        x: X position in sprite sheet
        y: Y position in sprite sheet
        width: Frame width
        height: Frame height
        trimmed: Whether frame was trimmed
        trim_offset: (left, top, right, bottom) trim offset
        source_size: Original size before trimming
        pivot: Pivot point (x, y) normalized 0-1
    """
    image: Any = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    trimmed: bool = False
    trim_offset: Tuple[int, int, int, int] = (0, 0, 0, 0)
    source_size: Tuple[int, int] = (0, 0)
    pivot: Tuple[float, float] = (0.5, 0.5)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "trimmed": self.trimmed,
            "trim_offset": list(self.trim_offset),
            "source_size": list(self.source_size),
            "pivot": list(self.pivot),
        }


# =============================================================================
# MAIN SPRITE SHEET FUNCTIONS
# =============================================================================

def generate_sprite_sheet(
    images: List[Any],
    config: SpriteSheetConfig
) -> SpriteSheetResult:
    """
    Generate sprite sheet from image sequence.

    Args:
        images: List of images (PIL Images or numpy arrays)
        config: Sprite sheet configuration

    Returns:
        SpriteSheetResult with sheet image and metadata
    """
    result = SpriteSheetResult()
    result.frame_count = len(images)

    warnings = []

    try:
        from PIL import Image as PILImage
        import numpy as np

        if not images:
            warnings.append("No images provided")
            result.warnings = warnings
            return result

        # Get sheet dimensions
        sheet_width, sheet_height = config.get_sheet_size(len(images))

        # Create sprite sheet canvas
        sheet = PILImage.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))

        frames = []
        col = 0
        row = 0
        trimmed_count = 0

        for i, img in enumerate(images):
            # Convert numpy array to PIL if needed
            if isinstance(img, np.ndarray):
                if img.shape[-1] == 4:
                    pil_img = PILImage.fromarray(img, 'RGBA')
                elif img.shape[-1] == 3:
                    pil_img = PILImage.fromarray(img, 'RGB').convert('RGBA')
                else:
                    pil_img = PILImage.fromarray(img).convert('RGBA')
            else:
                pil_img = img.convert('RGBA') if img.mode != 'RGBA' else img

            # Store original size
            source_width, source_height = pil_img.size
            source_size = (source_width, source_height)

            # Trim if enabled
            trim_offset = (0, 0, 0, 0)
            if config.trim:
                pil_img, trim_box = trim_sprite(pil_img)
                if trim_box != (0, 0, source_width, source_height):
                    trimmed_count += 1
                    # Calculate offset from original
                    trim_offset = (
                        trim_box[0],  # left
                        trim_box[1],  # top
                        source_width - trim_box[2],  # right
                        source_height - trim_box[3]  # bottom
                    )

            # Calculate position in sheet
            x = config.padding + col * (config.frame_width + config.spacing)
            y = config.padding + row * (config.frame_height + config.spacing)

            # Resize to fit frame if needed
            if pil_img.size != (config.frame_width, config.frame_height):
                # Center the sprite
                temp = PILImage.new('RGBA', (config.frame_width, config.frame_height), (0, 0, 0, 0))
                paste_x = (config.frame_width - pil_img.width) // 2
                paste_y = (config.frame_height - pil_img.height) // 2
                temp.paste(pil_img, (paste_x, paste_y))
                pil_img = temp

            # Paste to sheet
            sheet.paste(pil_img, (x, y))

            # Calculate pivot
            pivot = calculate_pivot(pil_img, trim_offset, config)

            # Create frame data
            frame = SpriteFrame(
                x=x,
                y=y,
                width=config.frame_width,
                height=config.frame_height,
                trimmed=config.trim and trim_offset != (0, 0, 0, 0),
                trim_offset=trim_offset,
                source_size=source_size,
                pivot=pivot,
            )
            frames.append(frame)

            # Next position
            col += 1
            if col >= config.columns:
                col = 0
                row += 1

        result.image = sheet
        result.sheet_size = (sheet_width, sheet_height)
        result.trimmed_count = trimmed_count

        # Generate metadata
        if config.generate_json:
            result.metadata = generate_sprite_metadata(sheet, config, frames)

    except ImportError:
        warnings.append("PIL or numpy not available for sprite sheet generation")
    except Exception as e:
        warnings.append(f"Sprite sheet generation error: {str(e)}")

    result.warnings = warnings
    return result


def trim_sprite(image: Any) -> Tuple[Any, Tuple[int, int, int, int]]:
    """
    Trim transparent borders from sprite.

    Args:
        image: PIL Image

    Returns:
        (trimmed_image, (left, top, right, bottom)) tuple
    """
    try:
        from PIL import Image as PILImage

        # Get bounding box of non-transparent pixels
        bbox = image.getbbox()

        if bbox is None:
            # Image is completely transparent
            return image, (0, 0, image.width, image.height)

        # Crop to bounding box
        trimmed = image.crop(bbox)

        return trimmed, bbox

    except ImportError:
        return image, (0, 0, image.width, image.height)


def calculate_pivot(
    image: Any,
    trim_offset: Tuple[int, int, int, int],
    config: SpriteSheetConfig
) -> Tuple[float, float]:
    """
    Calculate pivot point relative to trimmed sprite.

    Args:
        image: PIL Image (after trimming)
        trim_offset: (left, top, right, bottom) trim offset from original
        config: Sprite sheet configuration

    Returns:
        Pivot point (x, y) normalized 0-1
    """
    # Use configured pivot
    pivot_x = config.pivot_x
    pivot_y = config.pivot_y

    # Adjust for trim offset if we want to maintain world position
    # This is the offset needed to align with original sprite position
    # left_trim / original_width gives the x offset

    return (pivot_x, pivot_y)


def calculate_pivot_world(
    trim_offset: Tuple[int, int, int, int],
    original_size: Tuple[int, int],
    config: SpriteSheetConfig
) -> Tuple[float, float]:
    """
    Calculate pivot point adjusted for world position.

    Args:
        trim_offset: (left, top, right, bottom) trim offset
        original_size: Original sprite size
        config: Sprite sheet configuration

    Returns:
        Adjusted pivot point (x, y) normalized 0-1
    """
    left, top, right, bottom = trim_offset
    orig_w, orig_h = original_size

    # Adjust pivot for trim
    trim_w = orig_w - left - right
    trim_h = orig_h - top - bottom

    if trim_w == 0 or trim_h == 0:
        return (config.pivot_x, config.pivot_y)

    # Calculate where the pivot point is in the trimmed sprite
    pivot_x = (config.pivot_x * orig_w - left) / trim_w
    pivot_y = (config.pivot_y * orig_h - top) / trim_h

    return (pivot_x, pivot_y)


# =============================================================================
# METADATA GENERATION
# =============================================================================

def generate_sprite_metadata(
    sheet: Any,
    config: SpriteSheetConfig,
    frames: List[SpriteFrame]
) -> Dict[str, Any]:
    """
    Generate metadata JSON for sprite sheet.

    Args:
        sheet: Sprite sheet image
        config: Sprite sheet configuration
        frames: List of frame data

    Returns:
        Metadata dict in specified format
    """
    if config.json_format == "phaser":
        return export_phaser_json(config, frames)
    elif config.json_format == "unity":
        return export_unity_json(config, frames)
    elif config.json_format == "godot":
        return export_godot_json(config, frames)
    else:
        return export_generic_json(config, frames)


def export_phaser_json(
    config: SpriteSheetConfig,
    frames: List[SpriteFrame]
) -> Dict[str, Any]:
    """
    Generate Phaser-compatible JSON.

    Phaser 3 format:
    {
        "frames": {
            "frame_0": {
                "frame": {"x": 0, "y": 0, "w": 32, "h": 32},
                "rotated": false,
                "trimmed": true,
                "spriteSourceSize": {"x": 2, "y": 2, "w": 28, "h": 28},
                "sourceSize": {"w": 32, "h": 32},
                "pivot": {"x": 0.5, "y": 0.5}
            },
            ...
        },
        "meta": {
            "app": "Blender GSD",
            "version": "1.0",
            "image": "spritesheet.png",
            "format": "RGBA8888",
            "size": {"w": 256, "h": 256}
        }
    }
    """
    frame_data = {}

    for i, frame in enumerate(frames):
        frame_name = f"frame_{i}"
        frame_data[frame_name] = {
            "frame": {
                "x": frame.x,
                "y": frame.y,
                "w": frame.width,
                "h": frame.height,
            },
            "rotated": False,
            "trimmed": frame.trimmed,
            "spriteSourceSize": {
                "x": frame.trim_offset[0],
                "y": frame.trim_offset[1],
                "w": frame.width,
                "h": frame.height,
            },
            "sourceSize": {
                "w": frame.source_size[0],
                "h": frame.source_size[1],
            },
            "pivot": {
                "x": frame.pivot[0],
                "y": frame.pivot[1],
            },
        }

    sheet_width, sheet_height = config.get_sheet_size(len(frames))

    return {
        "frames": frame_data,
        "meta": {
            "app": "Blender GSD",
            "version": "1.0",
            "image": "spritesheet.png",
            "format": "RGBA8888",
            "size": {"w": sheet_width, "h": sheet_height},
            "scale": 1,
        },
    }


def export_unity_json(
    config: SpriteSheetConfig,
    frames: List[SpriteFrame]
) -> Dict[str, Any]:
    """
    Generate Unity-compatible JSON.

    Unity format (simplified):
    {
        "name": "spritesheet",
        "width": 256,
        "height": 256,
        "sprites": [
            {
                "name": "sprite_0",
                "x": 0,
                "y": 0,
                "width": 32,
                "height": 32,
                "pivotX": 0.5,
                "pivotY": 0.5
            },
            ...
        ]
    }
    """
    sprites = []

    for i, frame in enumerate(frames):
        sprites.append({
            "name": f"sprite_{i}",
            "x": frame.x,
            "y": frame.y,
            "width": frame.width,
            "height": frame.height,
            "pivotX": frame.pivot[0],
            "pivotY": frame.pivot[1],
            "border": [0, 0, 0, 0],  # 9-slice borders
        })

    sheet_width, sheet_height = config.get_sheet_size(len(frames))

    return {
        "name": "spritesheet",
        "width": sheet_width,
        "height": sheet_height,
        "pixelsToUnits": 100,
        "sprites": sprites,
    }


def export_godot_json(
    config: SpriteSheetConfig,
    frames: List[SpriteFrame]
) -> Dict[str, Any]:
    """
    Generate Godot-compatible JSON.

    Godot format:
    {
        "frames": [
            {
                "filename": "sprite_0",
                "frame": {"x": 0, "y": 0, "w": 32, "h": 32},
                "rotated": false,
                "trimmed": false,
                "spriteSourceSize": {"x": 0, "y": 0, "w": 32, "h": 32},
                "sourceSize": {"w": 32, "h": 32},
                "duration": 100
            },
            ...
        ],
        "meta": {
            "app": "Blender GSD",
            "version": "1.0",
            "image": "spritesheet.png",
            "format": "RGBA8888",
            "size": {"w": 256, "h": 256}
        }
    }
    """
    frame_data = []

    for i, frame in enumerate(frames):
        frame_data.append({
            "filename": f"sprite_{i}",
            "frame": {
                "x": frame.x,
                "y": frame.y,
                "w": frame.width,
                "h": frame.height,
            },
            "rotated": False,
            "trimmed": frame.trimmed,
            "spriteSourceSize": {
                "x": frame.trim_offset[0],
                "y": frame.trim_offset[1],
                "w": frame.width,
                "h": frame.height,
            },
            "sourceSize": {
                "w": frame.source_size[0],
                "h": frame.source_size[1],
            },
            "duration": 100,  # ms per frame
        })

    sheet_width, sheet_height = config.get_sheet_size(len(frames))

    return {
        "frames": frame_data,
        "meta": {
            "app": "Blender GSD",
            "version": "1.0",
            "image": "spritesheet.png",
            "format": "RGBA8888",
            "size": {"w": sheet_width, "h": sheet_height},
        },
    }


def export_generic_json(
    config: SpriteSheetConfig,
    frames: List[SpriteFrame]
) -> Dict[str, Any]:
    """
    Generate generic JSON format.

    Generic format:
    {
        "frames": [
            {
                "index": 0,
                "x": 0,
                "y": 0,
                "width": 32,
                "height": 32,
                "trimmed": false,
                "pivot_x": 0.5,
                "pivot_y": 0.5
            },
            ...
        ],
        "config": {...}
    }
    """
    frame_data = []

    for i, frame in enumerate(frames):
        frame_data.append({
            "index": i,
            "x": frame.x,
            "y": frame.y,
            "width": frame.width,
            "height": frame.height,
            "trimmed": frame.trimmed,
            "trim_offset": list(frame.trim_offset),
            "source_size": list(frame.source_size),
            "pivot_x": frame.pivot[0],
            "pivot_y": frame.pivot[1],
        })

    sheet_width, sheet_height = config.get_sheet_size(len(frames))

    return {
        "frames": frame_data,
        "sheet_size": [sheet_width, sheet_height],
        "config": config.to_dict(),
    }


# =============================================================================
# ANIMATION HELPERS
# =============================================================================

def extract_animation_frames(
    animation: Any,
    config: SpriteSheetConfig,
    start_frame: int = 1,
    end_frame: Optional[int] = None
) -> List[Any]:
    """
    Extract frames from Blender animation.

    Args:
        animation: Blender animation data
        config: Sprite sheet configuration
        start_frame: Start frame number
        end_frame: End frame number (None for current end)

    Returns:
        List of rendered frame images
    """
    frames = []

    try:
        import bpy
        from PIL import Image as PILImage
        import tempfile
        import os

        scene = bpy.context.scene

        if end_frame is None:
            end_frame = scene.frame_end

        # Create temp directory for frames
        temp_dir = tempfile.mkdtemp()

        original_frame = scene.frame_current
        original_render = scene.render

        try:
            # Set render settings
            scene.render.resolution_x = config.frame_width
            scene.render.resolution_y = config.frame_height
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = 'PNG'
            scene.render.image_settings.color_mode = 'RGBA'

            for frame_num in range(start_frame, end_frame + 1):
                scene.frame_set(frame_num)

                # Render frame
                output_path = os.path.join(temp_dir, f"frame_{frame_num:04d}.png")
                scene.render.filepath = output_path
                bpy.ops.render.render(write_still=True)

                # Load rendered image
                if os.path.exists(output_path):
                    img = PILImage.open(output_path)
                    frames.append(img)

        finally:
            # Restore original settings
            scene.frame_set(original_frame)
            scene.render = original_render

            # Clean up temp files
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)

    except ImportError:
        pass
    except Exception:
        pass

    return frames


def generate_walk_cycle_sheet(
    character: Any,
    config: SpriteSheetConfig,
    direction: str = "right",
    frame_count: int = 8
) -> SpriteSheetResult:
    """
    Generate walk cycle sprite sheet.

    Args:
        character: Blender character object
        config: Sprite sheet configuration
        direction: Walk direction (right, left, up, down)
        frame_count: Number of frames in walk cycle

    Returns:
        SpriteSheetResult with walk cycle sheet
    """
    result = SpriteSheetResult()

    try:
        import bpy

        # Configure for walk cycle
        walk_config = SpriteSheetConfig(
            columns=frame_count,
            rows=1,
            frame_width=config.frame_width,
            frame_height=config.frame_height,
            trim=config.trim,
            json_format=config.json_format,
        )

        # Find walk animation
        if character.animation_data and character.animation_data.action:
            action = character.animation_data.action

            # Extract frames
            frames = extract_animation_frames(
                action,
                walk_config,
                start_frame=int(action.frame_range[0]),
                end_frame=int(action.frame_range[1]),
            )

            if frames:
                result = generate_sprite_sheet(frames, walk_config)

    except ImportError:
        result.warnings.append("Blender not available")
    except Exception as e:
        result.warnings.append(f"Walk cycle generation error: {str(e)}")

    return result


def generate_animation_sheet(
    scene: Any,
    animation_name: str,
    config: SpriteSheetConfig,
    directions: List[str] = None
) -> SpriteSheetResult:
    """
    Generate sprite sheet from named animation.

    Args:
        scene: Blender scene
        animation_name: Name of animation to export
        config: Sprite sheet configuration
        directions: List of directions (for directional sprites)

    Returns:
        SpriteSheetResult with animation sheet
    """
    result = SpriteSheetResult()

    if directions is None:
        directions = ["right"]

    try:
        import bpy

        all_frames = []

        # Collect frames for all directions
        for direction in directions:
            frames = extract_animation_frames(
                scene.animation_data,
                config,
            )
            all_frames.extend(frames)

        if all_frames:
            # Adjust config for multiple directions
            direction_config = SpriteSheetConfig(
                columns=len(all_frames) // len(directions),
                rows=len(directions),
                frame_width=config.frame_width,
                frame_height=config.frame_height,
                trim=config.trim,
                json_format=config.json_format,
            )

            result = generate_sprite_sheet(all_frames, direction_config)

    except ImportError:
        result.warnings.append("Blender not available")
    except Exception as e:
        result.warnings.append(f"Animation sheet generation error: {str(e)}")

    return result


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_frame_position(
    frame_index: int,
    config: SpriteSheetConfig
) -> Tuple[int, int]:
    """
    Get position of a frame in the sprite sheet.

    Args:
        frame_index: Frame index
        config: Sprite sheet configuration

    Returns:
        (x, y) position in pixels
    """
    col = frame_index % config.columns
    row = frame_index // config.columns

    x = config.padding + col * (config.frame_width + config.spacing)
    y = config.padding + row * (config.frame_height + config.spacing)

    return (x, y)


def get_frame_bounds(
    frame_index: int,
    config: SpriteSheetConfig
) -> Tuple[int, int, int, int]:
    """
    Get bounds of a frame in the sprite sheet.

    Args:
        frame_index: Frame index
        config: Sprite sheet configuration

    Returns:
        (x, y, width, height) tuple
    """
    x, y = get_frame_position(frame_index, config)
    return (x, y, config.frame_width, config.frame_height)


def calculate_frame_count(config: SpriteSheetConfig) -> int:
    """
    Calculate total frames in sprite sheet.

    Args:
        config: Sprite sheet configuration

    Returns:
        Total frame count
    """
    return config.columns * config.rows


def optimize_sheet_layout(
    frame_count: int,
    frame_width: int,
    frame_height: int,
    max_size: Optional[Tuple[int, int]] = None
) -> Tuple[int, int]:
    """
    Calculate optimal columns and rows for frame count.

    Args:
        frame_count: Number of frames
        frame_width: Frame width
        frame_height: Frame height
        max_size: Optional maximum sheet size

    Returns:
        (columns, rows) tuple
    """
    if frame_count <= 0:
        return (1, 1)

    # Try square layout first
    sqrt = math.sqrt(frame_count)
    cols = math.ceil(sqrt)
    rows = math.ceil(frame_count / cols)

    # Adjust for max size if specified
    if max_size:
        max_width, max_height = max_size
        max_cols = max_width // frame_width
        max_rows = max_height // frame_height

        if cols > max_cols:
            cols = max_cols
            rows = math.ceil(frame_count / cols)

        if rows > max_rows:
            rows = max_rows
            cols = math.ceil(frame_count / rows)

    return (cols, rows)
