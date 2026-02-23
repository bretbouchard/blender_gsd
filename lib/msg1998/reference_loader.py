"""
MSG 1998 - Reference Image Loader

Handles loading reference images for location building.
"""

from pathlib import Path
from typing import List, Optional

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .types import ReferenceSet


def load_references(location_dir: Path) -> ReferenceSet:
    """
    Load all reference images and fSpy files for a location.

    Expected directory structure:
    location_dir/
    ├── references/
    │   ├── ref_001.jpg
    │   └── ref_002.png
    ├── fspy/
    │   ├── exterior_north.fspy
    │   └── exterior_east.fspy
    └── asset.json

    Args:
        location_dir: Root directory for location assets

    Returns:
        ReferenceSet with all loaded references
    """
    location_id = location_dir.name
    ref_set = ReferenceSet(location_id=location_id)

    if not location_dir.exists():
        return ref_set

    # Find reference images
    ref_dir = location_dir / "references"
    if ref_dir.exists():
        for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
            ref_set.images.extend(ref_dir.glob(f"*{ext}"))
            ref_set.images.extend(ref_dir.glob(f"*{ext.upper()}"))

    # Find fSpy files
    fspy_dir = location_dir / "fspy"
    if fspy_dir.exists():
        ref_set.fspy_files = list(fspy_dir.glob("*.fspy"))

    # Determine primary angle from fSpy filenames
    for fspy in ref_set.fspy_files:
        name_lower = fspy.stem.lower()
        if 'north' in name_lower:
            ref_set.primary_angle = "north"
            break
        elif 'south' in name_lower:
            ref_set.primary_angle = "south"
            break
        elif 'east' in name_lower:
            ref_set.primary_angle = "east"
            break
        elif 'west' in name_lower:
            ref_set.primary_angle = "west"
            break

    return ref_set


def setup_reference_plane(
    image_path: Path,
    camera,
    distance: float = 10.0,
    name: Optional[str] = None
):
    """
    Create image plane aligned with camera for modeling reference.

    Args:
        image_path: Path to reference image
        camera: Blender camera object
        distance: Distance from camera to plane
        name: Optional name for the plane

    Returns:
        Blender mesh object (reference plane)
    """
    if not BLENDER_AVAILABLE:
        return None

    if not image_path.exists():
        return None

    # Load image
    try:
        image = bpy.data.images.load(str(image_path), check_existing=True)
    except RuntimeError:
        return None

    # Calculate plane dimensions based on camera FOV
    if camera and camera.type == 'CAMERA':
        cam = camera.data
        fov = cam.angle
        aspect = image.size[0] / image.size[1] if image.size[1] > 0 else 1.0

        # Calculate plane size at distance
        import math
        height = 2.0 * distance * math.tan(fov / 2.0)
        width = height * aspect
    else:
        width, height = 10.0, 5.625  # Default 16:9 at distance 10

    # Create plane mesh
    plane_name = name or f"ref_plane_{image_path.stem}"
    mesh = bpy.data.meshes.new(plane_name)
    plane_obj = bpy.data.objects.new(plane_name, mesh)
    bpy.context.collection.objects.link(plane_obj)

    # Create vertices
    half_w, half_h = width / 2, height / 2
    vertices = [
        (-half_w, -distance, -half_h),
        (half_w, -distance, -half_h),
        (half_w, -distance, half_h),
        (-half_w, -distance, half_h)
    ]
    mesh.from_pydata(vertices, [], [[0, 1, 2, 3]])

    # Create material with image texture
    mat = bpy.data.materials.new(name=f"{plane_name}_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    tex_image = nodes.new('ShaderNodeTexImage')

    # Configure texture node
    tex_image.image = image

    # Connect nodes
    links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # Position nodes
    output.location = (400, 0)
    principled.location = (0, 0)
    tex_image.location = (-400, 0)

    # Assign material to plane
    plane_obj.data.materials.append(mat)

    # Position in front of camera
    if camera:
        plane_obj.location = camera.location
        # Rotate to face camera
        plane_obj.rotation_euler = camera.rotation_euler

    return plane_obj


def create_reference_collection(name: str = "MSG_References"):
    """
    Create or get a collection for reference images.

    Args:
        name: Collection name

    Returns:
        Blender collection
    """
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.collections:
        return bpy.data.collections[name]

    collection = bpy.data.collections.new(name)
    bpy.context.collection.children.link(collection)
    return collection


def organize_references_by_angle(
    reference_set: ReferenceSet,
    collection=None
) -> dict:
    """
    Organize reference images by camera angle.

    Args:
        reference_set: Set of references to organize
        collection: Optional collection to add reference planes to

    Returns:
        Dict mapping angle names to reference plane objects
    """
    organized = {}

    if not BLENDER_AVAILABLE:
        return organized

    for fspy in reference_set.fspy_files:
        name_lower = fspy.stem.lower()
        angle = "primary"

        if 'north' in name_lower:
            angle = "north"
        elif 'south' in name_lower:
            angle = "south"
        elif 'east' in name_lower:
            angle = "east"
        elif 'west' in name_lower:
            angle = "west"

        # Find matching reference image
        matching_images = [
            img for img in reference_set.images
            if fspy.stem.lower() in img.stem.lower()
        ]

        organized[angle] = {
            "fspy": fspy,
            "images": matching_images
        }

    return organized
