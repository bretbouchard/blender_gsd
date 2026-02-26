"""
Target preview visualization system.

Provides tools for creating visual overlays showing target geometry,
calibration points, surface normals, and projector frustums.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Any
from pathlib import Path

from .types import ProjectionTarget, ProjectionSurface, TargetType


@dataclass
class PreviewConfig:
    """
    Configuration for target preview visualization.

    Attributes:
        show_wireframe: Show wireframe overlay on surfaces
        show_surface_normal: Show surface normal arrows
        show_calibration_points: Show calibration point markers
        show_bounding_box: Show bounding box
        show_frustum: Show projector frustum (if projector provided)
        wireframe_color: RGBA color for wireframe
        normal_color: RGBA color for normal arrows
        point_color: RGBA color for calibration points
        bbox_color: RGBA color for bounding box
        frustum_color: RGBA color for frustum
        point_size: Size of calibration point markers
        normal_length: Length of normal arrows
        line_width: Width of wireframe lines
        frustum_alpha: Transparency of frustum
    """
    show_wireframe: bool = True
    show_surface_normal: bool = True
    show_calibration_points: bool = True
    show_bounding_box: bool = True
    show_frustum: bool = True

    # Colors (RGBA)
    wireframe_color: Tuple[float, float, float, float] = (1.0, 1.0, 0.0, 1.0)  # Yellow
    normal_color: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 1.0)    # Green
    point_color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 1.0)     # Red
    bbox_color: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)      # Blue
    frustum_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.3)   # White, transparent

    # Sizes
    point_size: float = 0.05
    normal_length: float = 0.5
    line_width: float = 2.0
    frustum_alpha: float = 0.3

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'show_wireframe': self.show_wireframe,
            'show_surface_normal': self.show_surface_normal,
            'show_calibration_points': self.show_calibration_points,
            'show_bounding_box': self.show_bounding_box,
            'show_frustum': self.show_frustum,
            'wireframe_color': list(self.wireframe_color),
            'normal_color': list(self.normal_color),
            'point_color': list(self.point_color),
            'bbox_color': list(self.bbox_color),
            'frustum_color': list(self.frustum_color),
            'point_size': self.point_size,
            'normal_length': self.normal_length,
            'line_width': self.line_width,
            'frustum_alpha': self.frustum_alpha,
        }


@dataclass
class PreviewResult:
    """
    Result of preview creation.

    Attributes:
        success: Whether preview was created successfully
        objects: List of created preview objects (names when Blender not available)
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = True
    objects: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TargetPreview:
    """
    Create preview visualization for projection targets.

    Creates visual overlays showing target geometry, calibration points,
    surface normals, and projector frustums.

    Example:
        >>> config = PreviewConfig(show_frustum=True)
        >>> preview = TargetPreview(config)
        >>> result = preview.create_preview(target, projector_camera)
        >>> # Preview objects now visible in viewport
        >>> preview.toggle_visibility(False)  # Hide
        >>> preview.clear_preview()  # Remove
    """

    def __init__(self, config: PreviewConfig = None):
        self.config = config or PreviewConfig()
        self.preview_objects: List[Any] = []
        self._blender_available = None

    @property
    def blender_available(self) -> bool:
        """Check if Blender is available."""
        if self._blender_available is None:
            try:
                import bpy
                self._blender_available = True
            except ImportError:
                self._blender_available = False
        return self._blender_available

    def create_preview(
        self,
        target: ProjectionTarget,
        projector: Optional[Any] = None
    ) -> PreviewResult:
        """
        Create preview visualization for target.

        Args:
            target: ProjectionTarget to visualize
            projector: Optional projector camera object for frustum

        Returns:
            PreviewResult with created objects and status
        """
        result = PreviewResult()

        if not self.blender_available:
            result.warnings.append("Blender (bpy) not available - preview not created")
            return result

        try:
            import bpy

            # Clear existing preview
            self.clear_preview()

            # Create wireframe overlay
            if self.config.show_wireframe:
                wireframe_result = self._create_wireframe(target)
                self.preview_objects.extend(wireframe_result)
                result.objects.extend([o.name for o in wireframe_result])

            # Create surface normal indicators
            if self.config.show_surface_normal:
                normal_result = self._create_normal_indicators(target)
                self.preview_objects.extend(normal_result)
                result.objects.extend([o.name for o in normal_result])

            # Create calibration point markers
            if self.config.show_calibration_points:
                point_result = self._create_point_markers(target)
                self.preview_objects.extend(point_result)
                result.objects.extend([o.name for o in point_result])

            # Create bounding box
            if self.config.show_bounding_box:
                bbox_result = self._create_bounding_box(target)
                self.preview_objects.extend(bbox_result)
                result.objects.extend([o.name for o in bbox_result])

            # Create projector frustum
            if self.config.show_frustum and projector:
                frustum_result = self._create_frustum(projector, target)
                self.preview_objects.extend(frustum_result)
                result.objects.extend([o.name for o in frustum_result])

        except Exception as e:
            result.errors.append(f"Error creating preview: {e}")
            result.success = False

        return result

    def _create_wireframe(self, target: ProjectionTarget) -> List[Any]:
        """Create wireframe overlay for target surfaces."""
        objects = []

        try:
            import bpy

            for surface in target.surfaces:
                # Create wireframe mesh from corners
                x, y, z = surface.position
                w, h = surface.dimensions

                # Create mesh
                mesh = bpy.data.meshes.new(f"WF_{surface.name}")
                obj = bpy.data.objects.new(f"WF_{surface.name}", mesh)

                verts = [
                    (x - w/2, y, z - h/2),
                    (x + w/2, y, z - h/2),
                    (x + w/2, y, z + h/2),
                    (x - w/2, y, z + h/2),
                ]
                edges = [(0, 1), (1, 2), (2, 3), (3, 0)]

                mesh.from_pydata(verts, edges, [])

                # Link to collection
                bpy.context.collection.objects.link(obj)

                # Set wireframe display
                obj.display_type = 'WIRE'

                objects.append(obj)

        except Exception:
            pass

        return objects

    def _create_normal_indicators(self, target: ProjectionTarget) -> List[Any]:
        """Create arrows showing surface normals."""
        objects = []

        try:
            import bpy

            for surface in target.surfaces:
                x, y, z = surface.position
                nx, ny, nz = surface.surface_normal

                # Create arrow at surface center
                # Use cone to indicate direction
                bpy.ops.mesh.primitive_cone_add(
                    radius1=0.02,
                    radius2=0,
                    depth=self.config.normal_length,
                    location=(x + nx * self.config.normal_length/2,
                             y + ny * self.config.normal_length/2,
                             z + nz * self.config.normal_length/2)
                )
                arrow = bpy.context.active_object
                arrow.name = f"Normal_{surface.name}"

                # Rotate to point in normal direction
                import mathutils
                direction = mathutils.Vector((nx, ny, nz))
                arrow.rotation_mode = 'QUATERNION'
                arrow.rotation_quaternion = direction.to_track_quat('Z', 'Y')

                # Set color
                self._set_object_color(arrow, self.config.normal_color)

                objects.append(arrow)

        except Exception:
            pass

        return objects

    def _create_point_markers(self, target: ProjectionTarget) -> List[Any]:
        """Create sphere markers for calibration points."""
        objects = []

        try:
            import bpy

            for surface in target.surfaces:
                for i, point in enumerate(surface.calibration_points):
                    # Create sphere at point location
                    bpy.ops.mesh.primitive_uv_sphere_add(
                        radius=self.config.point_size,
                        location=point
                    )
                    sphere = bpy.context.active_object
                    sphere.name = f"CalPoint_{surface.name}_{i}"

                    # Set color
                    self._set_object_color(sphere, self.config.point_color)

                    objects.append(sphere)

        except Exception:
            pass

        return objects

    def _create_bounding_box(self, target: ProjectionTarget) -> List[Any]:
        """Create bounding box visualization."""
        objects = []

        try:
            import bpy

            # Create cube at bounding box dimensions
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(0, 0, target.height_m / 2)
            )
            cube = bpy.context.active_object
            cube.name = f"BBox_{target.name}"

            # Scale to match dimensions
            cube.scale = (
                target.width_m,
                max(target.depth_m, 0.01),
                target.height_m
            )

            # Set wireframe display
            cube.display_type = 'WIRE'
            self._set_object_color(cube, self.config.bbox_color)

            objects.append(cube)

        except Exception:
            pass

        return objects

    def _create_frustum(
        self,
        projector: Any,
        target: ProjectionTarget
    ) -> List[Any]:
        """Create projector frustum visualization."""
        objects = []

        try:
            import bpy

            # Create cone representing projector FOV
            distance = 3.0  # Default distance

            bpy.ops.mesh.primitive_cone_add(
                radius1=0.5,  # Base radius
                radius2=0.1,  # Tip radius (at projector)
                depth=distance,
                location=projector.location if hasattr(projector, 'location') else (0, -distance/2, 1)
            )
            cone = bpy.context.active_object
            cone.name = f"Frustum_{target.name}"

            # Set transparent material
            self._set_object_color(cone, self.config.frustum_color)

            # Set transparency
            if cone.data.materials:
                mat = cone.data.materials[0]
                mat.blend_method = 'BLEND'
                mat.shadow_method = 'CLIP'

            objects.append(cone)

        except Exception:
            pass

        return objects

    def _set_object_color(self, obj: Any, color: Tuple[float, float, float, float]):
        """Set object color (creates material if needed)."""
        try:
            import bpy

            mat_name = f"PreviewMat_{obj.name}"
            mat = bpy.data.materials.get(mat_name)

            if not mat:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True

                # Set color on Principled BSDF
                bsdf = mat.node_tree.nodes.get('Principled BSDF')
                if bsdf:
                    bsdf.inputs['Base Color'].default_value = color
                    bsdf.inputs['Alpha'].default_value = color[3]

                # Enable blend for transparency
                if color[3] < 1.0:
                    mat.blend_method = 'BLEND'
                    mat.shadow_method = 'CLIP'

            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

        except Exception:
            pass

    def clear_preview(self):
        """Remove all preview objects."""
        if not self.blender_available:
            return

        try:
            import bpy

            for obj in self.preview_objects:
                if obj and obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)

            self.preview_objects.clear()

        except Exception:
            self.preview_objects.clear()

    def toggle_visibility(self, visible: bool):
        """Toggle visibility of preview objects."""
        for obj in self.preview_objects:
            if obj:
                obj.hide_viewport = not visible
                obj.hide_render = not visible


def preview_target(
    target: ProjectionTarget,
    projector: Optional[Any] = None,
    config: Optional[PreviewConfig] = None
) -> TargetPreview:
    """
    Convenience function to create target preview.

    Args:
        target: ProjectionTarget to visualize
        projector: Optional projector camera object
        config: Optional preview configuration

    Returns:
        TargetPreview instance with created visualization

    Example:
        >>> preview = preview_target(
        ...     target=my_reading_room,
        ...     projector=projector_camera,
        ...     config=PreviewConfig(show_frustum=True)
        ... )
        >>> # Preview objects now visible in viewport
        >>> preview.toggle_visibility(False)  # Hide
        >>> preview.clear_preview()  # Remove
    """
    preview = TargetPreview(config or PreviewConfig())
    preview.create_preview(target, projector)
    return preview
