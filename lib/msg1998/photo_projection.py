"""
MSG 1998 - Photo Projection System

Camera-based photo projection for texturing from reference images.
"""

from pathlib import Path
from typing import Optional

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .types import FSpyImportResult


class ProjectionSetup:
    """Camera-based photo projection setup."""

    def __init__(
        self,
        source_image_path: Path,
        camera,
        target_mesh,
        uv_layer_name: str = "ProjectionUV"
    ):
        self.source_image_path = source_image_path
        self.camera = camera
        self.target_mesh = target_mesh
        self.uv_layer_name = uv_layer_name
        self.projection_camera = None
        self.image = None

    def setup(self):
        """Set up the projection system."""
        if not BLENDER_AVAILABLE:
            return False

        # Load image
        try:
            self.image = bpy.data.images.load(str(self.source_image_path), check_existing=True)
        except RuntimeError:
            return False

        # Create projection camera (copy of matched camera)
        if self.camera:
            proj_cam_data = self.camera.data.copy()
            proj_cam_obj = self.camera.copy()
            proj_cam_obj.data = proj_cam_data
            proj_cam_obj.name = f"{self.target_mesh.name}_proj_cam"
            bpy.context.collection.objects.link(proj_cam_obj)
            self.projection_camera = proj_cam_obj

        return True

    def project(self):
        """Apply projection to target mesh."""
        if not BLENDER_AVAILABLE or not self.projection_camera:
            return False

        # This would use Blender's UV projection from view
        # In practice, this requires camera-based UV unwrapping
        return True


def setup_photo_projection(
    image_path: Path,
    camera,
    target_mesh
) -> Optional[ProjectionSetup]:
    """
    Set up photo projection from matched camera.

    Args:
        image_path: Path to reference image
        camera: Matched camera from fSpy
        target_mesh: Mesh to project onto

    Returns:
        ProjectionSetup or None if failed
    """
    if not image_path.exists():
        return None

    setup = ProjectionSetup(
        source_image_path=image_path,
        camera=camera,
        target_mesh=target_mesh
    )

    if setup.setup():
        return setup

    return None


def bake_projection(
    projection: ProjectionSetup,
    resolution: int = 4096,
    output_path: Optional[Path] = None
):
    """
    Bake projected texture to UV map.

    Args:
        projection: Projection setup
        resolution: Output texture resolution
        output_path: Optional path to save texture

    Returns:
        Baked image or None
    """
    if not BLENDER_AVAILABLE:
        return None

    if not projection.target_mesh:
        return None

    # Create new image for baking
    image_name = f"{projection.target_mesh.name}_baked"
    image = bpy.data.images.new(
        name=image_name,
        width=resolution,
        height=resolution
    )

    # Set up UV layer if needed
    mesh = projection.target_mesh.data
    if projection.uv_layer_name not in mesh.uv_layers:
        uv_layer = mesh.uv_layers.new(name=projection.uv_layer_name)
    else:
        uv_layer = mesh.uv_layers[projection.uv_layer_name]

    mesh.uv_layers.active = uv_layer

    # Configure bake settings
    scene = bpy.context.scene
    scene.render.bake.use_pass_direct = False
    scene.render.bake.use_pass_indirect = False
    scene.render.bake.use_pass_color = True

    # Note: Actual baking requires proper material setup with projection
    # This is a simplified implementation

    if output_path:
        image.filepath_raw = str(output_path)
        image.file_format = 'PNG'
        image.save()

    return image


def project_from_camera_view(
    camera,
    mesh,
    image_path: Path
) -> bool:
    """
    Project image from camera view onto mesh.

    This uses Blender's project_from_view UV unwrapping.

    Args:
        camera: Camera to project from
        mesh: Target mesh object
        image_path: Source image path

    Returns:
        Success status
    """
    if not BLENDER_AVAILABLE:
        return False

    if not image_path.exists():
        return False

    # Load image
    try:
        image = bpy.data.images.load(str(image_path), check_existing=True)
    except RuntimeError:
        return False

    # Set active object
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.mode_set(mode='EDIT')

    # Select all geometry
    bpy.ops.mesh.select_all(action='SELECT')

    # UV project from view using camera
    # This is simplified - full implementation would need camera setup
    bpy.ops.uv.project_from_view(orthographic=False)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Create material with projected image
    mat = bpy.data.materials.new(name=f"{mesh.name}_proj_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear and rebuild
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    tex_image = nodes.new('ShaderNodeTexImage')

    tex_image.image = image

    links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    output.location = (400, 0)
    principled.location = (0, 0)
    tex_image.location = (-400, 0)

    # Assign material
    if mesh.data.materials:
        mesh.data.materials[0] = mat
    else:
        mesh.data.materials.append(mat)

    return True


def create_camera_aligned_plane(
    camera,
    image_path: Path,
    distance: float = 10.0
):
    """
    Create a plane aligned with camera for reference/projection.

    Args:
        camera: Camera to align with
        image_path: Image to display on plane
        distance: Distance from camera

    Returns:
        Created plane object
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

    # Calculate plane size based on camera FOV
    import math
    fov = camera.data.angle if camera and camera.type == 'CAMERA' else 1.0
    aspect = image.size[0] / image.size[1] if image.size[1] > 0 else 1.0

    height = 2.0 * distance * math.tan(fov / 2.0)
    width = height * aspect

    # Create plane
    bpy.ops.mesh.primitive_plane_add(size=1)
    plane = bpy.context.active_object
    plane.name = f"proj_plane_{image_path.stem}"

    # Scale to correct aspect
    plane.scale = (width, height, 1.0)

    # Position in front of camera
    if camera:
        # Get camera forward direction
        forward = -camera.matrix_world.col[2][:3]
        from mathutils import Vector
        plane.location = camera.location + Vector(forward) * distance

        # Rotate to face camera
        plane.rotation_euler = camera.rotation_euler

    # Create material with image
    mat = bpy.data.materials.new(name=f"{plane.name}_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    tex_image = nodes.new('ShaderNodeTexImage')
    tex_image.image = image

    links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
    links.new(tex_image.outputs['Alpha'], principled.inputs['Alpha'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    plane.data.materials.append(mat)

    # Enable transparency
    mat.blend_method = 'BLEND'
    mat.shadow_method = 'CLIP'

    return plane
