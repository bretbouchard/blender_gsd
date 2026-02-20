"""
Prop System Module

Procedural prop placement and room population with dressing styles.

Implements REQ-SET-03: Prop population
Implements REQ-SET-04: Dressing styles
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
import math
import random
from pathlib import Path

from .set_types import (
    PropConfig,
    PropPlacement,
    PropCategory,
    DressingStyle,
    DRESSING_STYLES,
)


# =============================================================================
# PROP LIBRARY
# =============================================================================

# Built-in prop library for common items
DEFAULT_PROP_LIBRARY: Dict[str, PropConfig] = {
    # Furniture
    "sofa_modern": PropConfig(
        name="sofa_modern",
        category="furniture",
        style="modern",
        material="fabric_neutral",
        dimensions=(2.0, 0.9, 0.8),
        tags=["seating", "living_room", "sofa"],
    ),
    "armchair_modern": PropConfig(
        name="armchair_modern",
        category="furniture",
        style="modern",
        material="fabric_neutral",
        dimensions=(0.8, 0.8, 0.8),
        tags=["seating", "living_room", "chair"],
    ),
    "coffee_table_wood": PropConfig(
        name="coffee_table_wood",
        category="furniture",
        style="modern",
        material="wood_oak",
        dimensions=(1.2, 0.6, 0.45),
        tags=["table", "living_room", "wood"],
    ),
    "dining_table_rect": PropConfig(
        name="dining_table_rect",
        category="furniture",
        style="modern",
        material="wood_oak",
        dimensions=(1.8, 0.9, 0.75),
        tags=["table", "dining", "wood"],
    ),
    "dining_chair_modern": PropConfig(
        name="dining_chair_modern",
        category="furniture",
        style="modern",
        material="wood_oak",
        dimensions=(0.45, 0.45, 0.85),
        tags=["seating", "dining", "chair"],
        variations=4,
    ),
    "desk_office": PropConfig(
        name="desk_office",
        category="furniture",
        style="modern",
        material="wood_oak",
        dimensions=(1.4, 0.7, 0.75),
        tags=["table", "office", "desk"],
    ),
    "office_chair": PropConfig(
        name="office_chair",
        category="furniture",
        style="modern",
        material="fabric_black",
        dimensions=(0.6, 0.6, 1.1),
        tags=["seating", "office", "chair"],
    ),
    "bed_queen": PropConfig(
        name="bed_queen",
        category="furniture",
        style="modern",
        material="fabric_neutral",
        dimensions=(1.6, 2.0, 0.5),
        tags=["bed", "bedroom", "sleeping"],
    ),
    "nightstand": PropConfig(
        name="nightstand",
        category="furniture",
        style="modern",
        material="wood_oak",
        dimensions=(0.5, 0.4, 0.55),
        tags=["storage", "bedroom", "table"],
    ),
    "bookshelf_standard": PropConfig(
        name="bookshelf_standard",
        category="furniture",
        style="modern",
        material="wood_oak",
        dimensions=(0.8, 0.3, 1.8),
        tags=["storage", "books", "shelf"],
    ),
    "dresser_6drawer": PropConfig(
        name="dresser_6drawer",
        category="furniture",
        style="modern",
        material="wood_oak",
        dimensions=(1.2, 0.5, 0.8),
        tags=["storage", "bedroom", "dresser"],
    ),
    "tv_stand": PropConfig(
        name="tv_stand",
        category="furniture",
        style="modern",
        material="wood_oak",
        dimensions=(1.5, 0.4, 0.45),
        tags=["storage", "living_room", "media"],
    ),

    # Decor
    "lamp_floor": PropConfig(
        name="lamp_floor",
        category="decor",
        style="modern",
        material="metal_chrome",
        dimensions=(0.4, 0.4, 1.6),
        tags=["lighting", "lamp", "floor"],
    ),
    "lamp_table": PropConfig(
        name="lamp_table",
        category="decor",
        style="modern",
        material="metal_chrome",
        dimensions=(0.3, 0.3, 0.45),
        tags=["lighting", "lamp", "table"],
    ),
    "vase_modern": PropConfig(
        name="vase_modern",
        category="decor",
        style="modern",
        material="ceramic_white",
        dimensions=(0.2, 0.2, 0.35),
        tags=["vase", "decorative", "ceramic"],
        variations=3,
    ),
    "plant_potted": PropConfig(
        name="plant_potted",
        category="decor",
        style="modern",
        material="ceramic_terracotta",
        dimensions=(0.3, 0.3, 0.6),
        tags=["plant", "nature", "decorative"],
        variations=5,
    ),
    "picture_frame_large": PropConfig(
        name="picture_frame_large",
        category="decor",
        style="modern",
        material="wood_black",
        dimensions=(0.6, 0.02, 0.8),
        tags=["art", "frame", "wall"],
    ),
    "mirror_wall": PropConfig(
        name="mirror_wall",
        category="decor",
        style="modern",
        material="glass_mirror",
        dimensions=(0.6, 0.02, 0.9),
        tags=["mirror", "wall", "decorative"],
    ),
    "rug_area": PropConfig(
        name="rug_area",
        category="decor",
        style="modern",
        material="fabric_wool",
        dimensions=(2.0, 1.5, 0.02),
        tags=["rug", "floor", "textile"],
    ),
    "cushion_decorative": PropConfig(
        name="cushion_decorative",
        category="decor",
        style="modern",
        material="fabric_cotton",
        dimensions=(0.45, 0.45, 0.15),
        tags=["cushion", "textile", "decorative"],
        variations=6,
    ),

    # Electronics
    "tv_55inch": PropConfig(
        name="tv_55inch",
        category="electronics",
        style="modern",
        material="plastic_black",
        dimensions=(1.24, 0.05, 0.7),
        tags=["tv", "screen", "media"],
    ),
    "laptop": PropConfig(
        name="laptop",
        category="electronics",
        style="modern",
        material="metal_aluminum",
        dimensions=(0.35, 0.25, 0.02),
        tags=["computer", "laptop", "office"],
    ),
    "keyboard": PropConfig(
        name="keyboard",
        category="electronics",
        style="modern",
        material="plastic_black",
        dimensions=(0.45, 0.15, 0.02),
        tags=["computer", "keyboard", "office"],
    ),
    "mouse": PropConfig(
        name="mouse",
        category="electronics",
        style="modern",
        material="plastic_black",
        dimensions=(0.12, 0.07, 0.04),
        tags=["computer", "mouse", "office"],
    ),
    "phone_desk": PropConfig(
        name="phone_desk",
        category="electronics",
        style="modern",
        material="plastic_black",
        dimensions=(0.2, 0.15, 0.05),
        tags=["phone", "office", "communication"],
    ),

    # Kitchen
    "toaster": PropConfig(
        name="toaster",
        category="kitchen",
        style="modern",
        material="metal_chrome",
        dimensions=(0.3, 0.2, 0.2),
        tags=["appliance", "kitchen", "toaster"],
    ),
    "coffeemaker": PropConfig(
        name="coffeemaker",
        category="kitchen",
        style="modern",
        material="plastic_black",
        dimensions=(0.25, 0.2, 0.35),
        tags=["appliance", "kitchen", "coffee"],
    ),
    "microwave": PropConfig(
        name="microwave",
        category="kitchen",
        style="modern",
        material="metal_chrome",
        dimensions=(0.5, 0.4, 0.3),
        tags=["appliance", "kitchen", "microwave"],
    ),
    "blender": PropConfig(
        name="blender",
        category="kitchen",
        style="modern",
        material="plastic_black",
        dimensions=(0.2, 0.2, 0.4),
        tags=["appliance", "kitchen", "blender"],
    ),
    "dishes_stack": PropConfig(
        name="dishes_stack",
        category="kitchen",
        style="modern",
        material="ceramic_white",
        dimensions=(0.25, 0.25, 0.1),
        tags=["dishes", "kitchen", "ceramic"],
    ),

    # Bathroom
    "towel_rack": PropConfig(
        name="towel_rack",
        category="bathroom",
        style="modern",
        material="metal_chrome",
        dimensions=(0.6, 0.05, 0.05),
        tags=["bathroom", "towel", "storage"],
    ),
    "towel_folded": PropConfig(
        name="towel_folded",
        category="bathroom",
        style="modern",
        material="fabric_cotton",
        dimensions=(0.4, 0.3, 0.1),
        tags=["bathroom", "towel", "textile"],
        variations=3,
    ),
    "soap_dispenser": PropConfig(
        name="soap_dispenser",
        category="bathroom",
        style="modern",
        material="plastic_white",
        dimensions=(0.08, 0.08, 0.15),
        tags=["bathroom", "soap", "hygiene"],
    ),

    # Lighting
    "pendant_light": PropConfig(
        name="pendant_light",
        category="lighting",
        style="modern",
        material="metal_chrome",
        dimensions=(0.4, 0.4, 0.3),
        tags=["lighting", "ceiling", "pendant"],
    ),
    "sconce_wall": PropConfig(
        name="sconce_wall",
        category="lighting",
        style="modern",
        material="metal_chrome",
        dimensions=(0.15, 0.25, 0.25),
        tags=["lighting", "wall", "sconce"],
    ),

    # Plants
    "plant_large_floor": PropConfig(
        name="plant_large_floor",
        category="plants",
        style="modern",
        material="ceramic_terracotta",
        dimensions=(0.5, 0.5, 1.5),
        tags=["plant", "nature", "floor"],
        variations=3,
    ),
    "succulent_small": PropConfig(
        name="succulent_small",
        category="plants",
        style="modern",
        material="ceramic_white",
        dimensions=(0.1, 0.1, 0.15),
        tags=["plant", "nature", "desk"],
        variations=5,
    ),

    # Books
    "book_stack": PropConfig(
        name="book_stack",
        category="books",
        style="modern",
        material="paper",
        dimensions=(0.2, 0.15, 0.2),
        tags=["book", "reading", "stack"],
        variations=3,
    ),
    "book_open": PropConfig(
        name="book_open",
        category="books",
        style="modern",
        material="paper",
        dimensions=(0.25, 0.2, 0.02),
        tags=["book", "reading", "open"],
    ),

    # Art
    "sculpture_small": PropConfig(
        name="sculpture_small",
        category="art",
        style="modern",
        material="metal_bronze",
        dimensions=(0.15, 0.15, 0.25),
        tags=["art", "sculpture", "decorative"],
        variations=4,
    ),

    # Textiles
    "throw_blanket": PropConfig(
        name="throw_blanket",
        category="textiles",
        style="modern",
        material="fabric_wool",
        dimensions=(1.5, 1.2, 0.02),
        tags=["textile", "blanket", "decorative"],
    ),

    # Storage
    "basket_woven": PropConfig(
        name="basket_woven",
        category="storage",
        style="modern",
        material="wicker",
        dimensions=(0.35, 0.25, 0.2),
        tags=["storage", "basket", "woven"],
        variations=2,
    ),
    "box_storage": PropConfig(
        name="box_storage",
        category="storage",
        style="modern",
        material="cardboard",
        dimensions=(0.4, 0.3, 0.25),
        tags=["storage", "box", "organization"],
        variations=3,
    ),
}


# =============================================================================
# PROP LOADING
# =============================================================================

def load_prop_library(path: str) -> Dict[str, PropConfig]:
    """
    Load prop library from directory or YAML file.

    Args:
        path: Path to prop library file or directory

    Returns:
        Dictionary of prop name -> PropConfig
    """
    lib_path = Path(path)
    library = {}

    if lib_path.is_file() and lib_path.suffix in (".yaml", ".yml"):
        # Load single YAML file
        try:
            import yaml
            with open(lib_path, "r") as f:
                data = yaml.safe_load(f)

            for name, config in data.get("props", {}).items():
                library[name] = PropConfig.from_dict({"name": name, **config})
        except ImportError:
            # Fallback to JSON
            import json
            with open(lib_path.with_suffix(".json"), "r") as f:
                data = json.load(f)

            for name, config in data.get("props", {}).items():
                library[name] = PropConfig.from_dict({"name": name, **config})

    elif lib_path.is_dir():
        # Load all YAML files in directory
        for yaml_file in lib_path.glob("**/*.yaml"):
            file_lib = load_prop_library(str(yaml_file))
            library.update(file_lib)

    return library


def get_prop_config(prop_name: str, library: Optional[Dict[str, PropConfig]] = None) -> Optional[PropConfig]:
    """
    Get prop configuration by name.

    Args:
        prop_name: Name of prop
        library: Optional prop library (uses default if None)

    Returns:
        PropConfig if found, None otherwise
    """
    lib = library or DEFAULT_PROP_LIBRARY
    return lib.get(prop_name)


def find_props_by_category(
    category: str,
    library: Optional[Dict[str, PropConfig]] = None
) -> List[PropConfig]:
    """
    Find all props in a category.

    Args:
        category: Category to search
        library: Optional prop library

    Returns:
        List of matching PropConfig objects
    """
    lib = library or DEFAULT_PROP_LIBRARY
    return [p for p in lib.values() if p.category == category]


def find_props_by_tag(
    tag: str,
    library: Optional[Dict[str, PropConfig]] = None
) -> List[PropConfig]:
    """
    Find all props with a specific tag.

    Args:
        tag: Tag to search for
        library: Optional prop library

    Returns:
        List of matching PropConfig objects
    """
    lib = library or DEFAULT_PROP_LIBRARY
    return [p for p in lib.values() if tag in p.tags]


def find_props_by_style(
    style: str,
    library: Optional[Dict[str, PropConfig]] = None
) -> List[PropConfig]:
    """
    Find all props with a specific style.

    Args:
        style: Style to search for
        library: Optional prop library

    Returns:
        List of matching PropConfig objects
    """
    lib = library or DEFAULT_PROP_LIBRARY
    return [p for p in lib.values() if p.style == style]


# =============================================================================
# PROP PLACEMENT
# =============================================================================

def place_prop(
    prop_name: str,
    position: Tuple[float, float, float],
    rotation: Tuple[float, float, float] = (0, 0, 0),
    scale: float = 1.0,
    variant: int = 0,
    collection: Any = None,
    library: Optional[Dict[str, PropConfig]] = None
) -> Any:
    """
    Place prop in scene at specified position.

    Args:
        prop_name: Name of prop to place
        position: World position (x, y, z)
        rotation: Euler rotation in degrees (x, y, z)
        scale: Scale multiplier
        variant: Variant index for props with variations
        collection: Optional Blender collection
        library: Optional prop library

    Returns:
        Created prop object (placeholder - would be actual mesh in full implementation)
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for prop placement")

    config = get_prop_config(prop_name, library)
    if not config:
        raise ValueError(f"Prop not found: {prop_name}")

    # Create placeholder mesh (full implementation would load actual prop geometry)
    mesh = bpy.data.meshes.new(f"prop_{prop_name}")
    obj = bpy.data.objects.new(f"prop_{prop_name}", mesh)

    bm = bmesh.new()

    # Create bounding box as placeholder
    dims = config.dimensions
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (dims[0] * scale, 0, 0, 0),
        (0, dims[1] * scale, 0, 0),
        (0, 0, dims[2] * scale, 0),
        (0, 0, 0, 1)
    ))

    bm.to_mesh(mesh)
    bm.free()

    # Position and rotate
    obj.location = position
    obj.rotation_euler = tuple(r * math.pi / 180 for r in rotation)

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def populate_room(
    room_config: Any,
    prop_list: List[PropPlacement],
    collection: Any = None,
    library: Optional[Dict[str, PropConfig]] = None
) -> List[Any]:
    """
    Populate room with props from placement list.

    Args:
        room_config: Room configuration (for bounds checking)
        prop_list: List of prop placements
        collection: Optional Blender collection
        library: Optional prop library

    Returns:
        List of created prop objects
    """
    objects = []

    for placement in prop_list:
        try:
            obj = place_prop(
                placement.prop,
                placement.position,
                placement.rotation,
                placement.scale,
                placement.variant,
                collection,
                library
            )
            objects.append(obj)
        except ValueError as e:
            print(f"Warning: {e}")

    return objects


# =============================================================================
# DRESSING STYLES
# =============================================================================

def apply_dressing_style(
    room_config: Any,
    style: str,
    collection: Any = None,
    library: Optional[Dict[str, PropConfig]] = None,
    seed: Optional[int] = None
) -> List[PropPlacement]:
    """
    Auto-generate prop placements for a dressing style.

    Args:
        room_config: Room configuration
        style: Dressing style name
        collection: Optional Blender collection
        library: Optional prop library
        seed: Random seed for reproducibility

    Returns:
        List of generated PropPlacement objects
    """
    if seed is not None:
        random.seed(seed)

    style_config = DRESSING_STYLES.get(style, DRESSING_STYLES["lived_in"])
    placements = []

    # Get room dimensions
    width = room_config.width
    depth = room_config.depth
    height = room_config.height

    # Prop density determines how many props to place
    density = style_config["prop_density"]
    clutter = style_config["clutter"]

    # Select appropriate props based on room type and style
    lib = library or DEFAULT_PROP_LIBRARY

    # Essential furniture (always placed)
    essential_props = _get_essential_props(room_config, lib)
    for prop_config in essential_props:
        placement = _generate_placement(prop_config, room_config, "essential")
        if placement:
            placements.append(placement)

    # Secondary props (based on density)
    secondary_props = _get_secondary_props(room_config, lib)
    num_secondary = int(len(secondary_props) * density)

    selected = random.sample(
        secondary_props,
        min(num_secondary, len(secondary_props))
    )

    for prop_config in selected:
        placement = _generate_placement(prop_config, room_config, "secondary")
        if placement:
            placements.append(placement)

    # Clutter props (based on clutter factor)
    clutter_props = _get_clutter_props(lib)
    num_clutter = int(len(clutter_props) * clutter)

    selected_clutter = random.sample(
        clutter_props,
        min(num_clutter, len(clutter_props))
    )

    for prop_config in selected_clutter:
        placement = _generate_placement(prop_config, room_config, "clutter")
        if placement:
            placements.append(placement)

    return placements


def _get_essential_props(room_config: Any, library: Dict[str, PropConfig]) -> List[PropConfig]:
    """Get essential props for room type."""
    # Simplified - would be more sophisticated based on room type
    essential_names = [
        "sofa_modern",
        "coffee_table_wood",
        "tv_stand",
    ]

    props = []
    for name in essential_names:
        if name in library:
            props.append(library[name])

    return props


def _get_secondary_props(room_config: Any, library: Dict[str, PropConfig]) -> List[PropConfig]:
    """Get secondary props for room type."""
    secondary_names = [
        "armchair_modern",
        "lamp_floor",
        "plant_potted",
        "rug_area",
        "picture_frame_large",
        "bookshelf_standard",
    ]

    props = []
    for name in secondary_names:
        if name in library:
            props.append(library[name])

    return props


def _get_clutter_props(library: Dict[str, PropConfig]) -> List[PropConfig]:
    """Get clutter/detail props."""
    clutter_names = [
        "cushion_decorative",
        "vase_modern",
        "plant_potted",
        "book_stack",
        "succulent_small",
        "throw_blanket",
    ]

    props = []
    for name in clutter_names:
        if name in library:
            props.append(library[name])

    return props


def _generate_placement(
    prop_config: PropConfig,
    room_config: Any,
    placement_type: str
) -> Optional[PropPlacement]:
    """Generate a single prop placement."""
    width = room_config.width
    depth = room_config.depth

    # Get prop dimensions
    dims = prop_config.dimensions

    # Random position within room bounds
    x = random.uniform(dims[0] / 2, width - dims[0] / 2)
    y = random.uniform(dims[1] / 2, depth - dims[1] / 2)

    # Adjust for placement type
    if placement_type == "essential":
        # Essential props near center
        x = width / 2 + random.uniform(-1, 1)
        y = depth / 2 + random.uniform(-0.5, 0.5)
    elif placement_type == "clutter":
        # Clutter near edges and on surfaces
        if random.random() > 0.5:
            x = random.choice([random.uniform(0.5, 1.5), random.uniform(width - 1.5, width - 0.5)])
        if random.random() > 0.5:
            y = random.choice([random.uniform(0.5, 1.5), random.uniform(depth - 1.5, depth - 0.5)])

    # Random rotation for clutter
    if placement_type == "clutter":
        rotation = (0, 0, random.uniform(-30, 30))
    else:
        rotation = (0, 0, random.choice([0, 90, 180, 270]))

    # Select variant if available
    variant = random.randint(0, prop_config.variations - 1) if prop_config.variations > 1 else 0

    return PropPlacement(
        prop=prop_config.name,
        position=(x - width / 2, y - depth / 2, 0),
        rotation=rotation,
        variant=variant,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Constants
    "DEFAULT_PROP_LIBRARY",
    "DRESSING_STYLES",
    # Loading
    "load_prop_library",
    "get_prop_config",
    "find_props_by_category",
    "find_props_by_tag",
    "find_props_by_style",
    # Placement
    "place_prop",
    "populate_room",
    # Dressing
    "apply_dressing_style",
]
