"""
MSG 1998 - Layer Separation System

Separate render into BG/MG/FG layers for compositing.
"""

from typing import Dict, List, Tuple

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .types import CompositeLayer


# Layer mask colors (distinct for compositing)
LAYER_COLORS: Dict[str, Tuple[float, float, float]] = {
    "background": (1.0, 0.0, 0.0),   # Red
    "midground": (0.0, 1.0, 0.0),    # Green
    "foreground": (0.0, 0.0, 1.0),   # Blue
}


def create_composite_layers(
    scene,
    config: Dict
) -> List[CompositeLayer]:
    """
    Create BG/MG/FG layer separation.

    Args:
        scene: Blender scene
        config: Layer configuration

    Returns:
        List of CompositeLayer objects
    """
    layers = []

    for layer_name, mask_color in LAYER_COLORS.items():
        layer = CompositeLayer(
            name=layer_name,
            objects=[],
            render_passes=["beauty", "depth", "normal"],
            mask_color=mask_color
        )
        layers.append(layer)

    return layers


def assign_layer_masks(layers: List[CompositeLayer]) -> None:
    """
    Assign object ID colors for layer masking.

    Args:
        layers: List of layers to assign
    """
    if not BLENDER_AVAILABLE:
        return

    for layer in layers:
        for obj in layer.objects:
            obj.pass_index = _color_to_index(layer.mask_color)


def _color_to_index(color: Tuple[float, float, float]) -> int:
    """Convert RGB color to object index."""
    # Simple hash: R*1 + G*100 + B*10000
    r, g, b = [int(c * 255) for c in color]
    return r + g * 256 + b * 65536


def _index_to_color(index: int) -> Tuple[float, float, float]:
    """Convert object index back to RGB color."""
    r = index % 256
    g = (index // 256) % 256
    b = (index // 65536) % 256
    return (r / 255.0, g / 255.0, b / 255.0)


def assign_object_to_layer(obj, layer_name: str) -> None:
    """
    Assign an object to a specific layer.

    Args:
        obj: Blender object
        layer_name: Layer name ("background", "midground", "foreground")
    """
    if not BLENDER_AVAILABLE:
        return

    if layer_name not in LAYER_COLORS:
        return

    obj.pass_index = _color_to_index(LAYER_COLORS[layer_name])


def get_layer_from_color(color: Tuple[float, float, float]) -> str:
    """
    Get layer name from mask color.

    Args:
        color: RGB color tuple

    Returns:
        Layer name or "unknown"
    """
    for layer_name, layer_color in LAYER_COLORS.items():
        if _colors_match(color, layer_color, tolerance=0.1):
            return layer_name
    return "unknown"


def _colors_match(
    color1: Tuple[float, float, float],
    color2: Tuple[float, float, float],
    tolerance: float = 0.1
) -> bool:
    """Check if two colors match within tolerance."""
    for c1, c2 in zip(color1, color2):
        if abs(c1 - c2) > tolerance:
            return False
    return True


def create_layer_collections(scene) -> Dict[str, any]:
    """
    Create collections for each layer.

    Args:
        scene: Blender scene

    Returns:
        Dict mapping layer names to collections
    """
    if not BLENDER_AVAILABLE:
        return {}

    collections = {}
    master_collection = scene.collection

    for layer_name in LAYER_COLORS.keys():
        collection_name = f"Layer_{layer_name}"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            master_collection.children.link(collection)

        collections[layer_name] = collection

    return collections
