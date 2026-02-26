"""
Content mapper for projection surfaces.

Maps content textures to projection surfaces via projector camera projection.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Tuple

from .types import (
    ProjectionShaderConfig,
    ProjectionShaderResult,
    ProjectionMode,
)
from .projector_nodes import create_projector_material
from .proxy_geometry import (
    create_proxy_geometry_for_surface,
    create_multi_surface_proxy,
    create_proxy_mesh_blender,
    ProxyGeometryConfig,
    ProxyGeometryResult,
)


# Import calibration types from parent module
from ..calibration.types import (
    SurfaceCalibration,
    CalibrationType,
)


@dataclass
class ContentMappingResult:
    """Result of content mapping operation."""
    material: Any = None
    proxy_object: Any = None
    surface_object: Any = None
    success: bool = True
    errors: list = field(default_factory=list)


class ContentMapper:
    """Map content textures to projection surfaces.

    This class provides the main workflow for:
    1. Creating projection shaders from projector profiles
    2. Generating proxy geometry for surfaces
    3. Applying content to surfaces via camera projection

    Usage:
        from lib.cinematic.projection.physical.shaders import ContentMapper
        from lib.cinematic.projection.physical.projector import get_projector_profile

        # Get projector profile
        profile = get_projector_profile("epson_home_cinema_2150")

        # Create mapper
        mapper = ContentMapper(profile)

        # Map content to surface
        result = mapper.map_content_to_surface(
            content_path="content.png",
            surface_object=my_surface,
            projector_object=my_projector_camera,
            calibration=my_calibration
        )
    """

    def __init__(self, projector_profile):
        """
        Initialize content mapper with projector profile.

        Args:
            projector_profile: ProjectorProfile instance with optical parameters
        """
        self.profile = projector_profile

        # Create shader config from profile
        self.shader_config = ProjectionShaderConfig(
            throw_ratio=projector_profile.throw_ratio,
            resolution_x=projector_profile.native_resolution[0],
            resolution_y=projector_profile.native_resolution[1],
            shift_x=projector_profile.lens_shift_horizontal,
            shift_y=projector_profile.lens_shift_vertical,
        )

    def map_content_to_surface(
        self,
        content_path: str,
        surface_object: Any,
        projector_object: Any,
        calibration: SurfaceCalibration,
        create_proxy: bool = True,
        proxy_config: Optional[ProxyGeometryConfig] = None
    ) -> ContentMappingResult:
        """
        Map content image/video to surface via projector projection.

        This is the main workflow method that:
        1. Optionally creates proxy geometry
        2. Creates projection shader material
        3. Applies material to surface

        Args:
            content_path: Path to content image/video
            surface_object: Target surface mesh (or None to use proxy)
            projector_object: Projector camera object
            calibration: Surface calibration data
            create_proxy: Whether to create proxy geometry
            proxy_config: Proxy geometry configuration

        Returns:
            ContentMappingResult with created objects
        """
        errors = []
        proxy_object = None

        try:
            # Get calibration points
            calibration_points = [p.world_position for p in calibration.points]
            projector_uvs = [p.projector_uv for p in calibration.points]

            # Create proxy geometry if requested
            if create_proxy and proxy_config:
                if calibration.calibration_type == CalibrationType.THREE_POINT:
                    proxy_result = create_proxy_geometry_for_surface(
                        calibration_points,
                        projector_uvs,
                        proxy_config
                    )
                else:
                    proxy_result = create_multi_surface_proxy(
                        calibration_points,
                        projector_uvs,
                        proxy_config
                    )

                if not proxy_result.success:
                    errors.extend(proxy_result.errors)
                    return ContentMappingResult(success=False, errors=errors)

                # Create Blender mesh object
                # Note: This requires Blender context
                try:
                    import bpy

                    # Create mesh from proxy geometry data
                    # (Simplified - full implementation would extract vertices/faces/uvs)
                    proxy_object = self._create_blender_proxy(
                        calibration,
                        proxy_config,
                        proxy_result
                    )
                except ImportError:
                    pass  # Blender not available

            # Create projection shader
            self.shader_config.content_image = content_path
            shader_result = create_projector_material(
                self.shader_config,
                projector_object
            )

            if not shader_result.success:
                errors.extend(shader_result.errors)
                return ContentMappingResult(success=False, errors=errors)

            # Apply material to surface
            target_object = surface_object or proxy_object
            if target_object:
                self._apply_material_to_object(target_object, shader_result.material)

            return ContentMappingResult(
                material=shader_result.material,
                proxy_object=proxy_object,
                surface_object=target_object,
                success=True,
                errors=[]
            )

        except Exception as e:
            errors.append(f"Error mapping content: {e}")
            return ContentMappingResult(success=False, errors=errors)

    def _create_blender_proxy(
        self,
        calibration: SurfaceCalibration,
        config: ProxyGeometryConfig,
        proxy_result: ProxyGeometryResult
    ) -> Any:
        """
        Create Blender proxy mesh object.

        Internal method to create the actual Blender mesh.
        """
        try:
            import bpy
            import bmesh
        except ImportError:
            return None

        # Get calibration data
        points = calibration.points
        p1 = points[0].world_position
        p2 = points[1].world_position
        p3 = points[2].world_position

        # Compute 4th corner
        v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
        v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
        p4 = (
            p1[0] + v1[0] + v2[0],
            p1[1] + v1[1] + v2[1],
            p1[2] + v1[2] + v2[2]
        )

        # Create mesh
        mesh = bpy.data.meshes.new("Projection_Proxy")
        obj = bpy.data.objects.new("Projection_Proxy", mesh)

        # Link to collection
        bpy.context.collection.objects.link(obj)

        # Create geometry with bmesh
        bm = bmesh.new()

        verts = [
            bm.verts.new(p1),
            bm.verts.new(p2),
            bm.verts.new(p4),
            bm.verts.new(p3),
        ]

        bm.faces.new(verts)
        bm.to_mesh(mesh)
        bm.free()

        # Add UV layer
        uv_layer = mesh.uv_layers.new(name="ProjectorUV")

        # Set UV coordinates from calibration
        uv0 = points[0].projector_uv
        uv1 = points[1].projector_uv
        uv2 = points[2].projector_uv
        uv3 = (uv1[0], uv2[1])  # Top-right

        uvs = [uv0, uv1, uv3, uv2]

        for i, loop in enumerate(mesh.loops):
            if i < len(uvs):
                uv_layer.data[i].uv = uvs[i]

        return obj

    def _apply_material_to_object(self, obj: Any, material: Any) -> None:
        """Apply material to object's first material slot."""
        if not obj or not material:
            return

        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)

    def update_content(self, material: Any, new_content_path: str) -> bool:
        """
        Update content texture in existing material.

        Args:
            material: Blender material with projection shader
            new_content_path: Path to new content image/video

        Returns:
            True if update successful
        """
        from .projector_nodes import update_projection_content
        return update_projection_content(material, new_content_path)

    def set_intensity(self, material: Any, intensity: float) -> bool:
        """
        Set projection intensity (for blending).

        Args:
            material: Blender material with projection shader
            intensity: Intensity value (0.0 to 2.0)

        Returns:
            True if update successful
        """
        from .projector_nodes import set_projection_intensity
        return set_projection_intensity(material, intensity)

    def create_uv_projected_material(
        self,
        content_path: str,
        calibration: SurfaceCalibration
    ) -> ProjectionShaderResult:
        """
        Create material using UV projection mode instead of camera projection.

        UV mode uses the surface's existing UV coordinates rather than
        computing projection from camera position.

        Args:
            content_path: Path to content image
            calibration: Surface calibration (for UV bounds validation)

        Returns:
            ProjectionShaderResult with created material
        """
        # Create config with UV mode
        uv_config = ProjectionShaderConfig(
            throw_ratio=self.shader_config.throw_ratio,
            resolution_x=self.shader_config.resolution_x,
            resolution_y=self.shader_config.resolution_y,
            mode=ProjectionMode.UV,
            content_image=content_path,
        )

        # Create material (without projector object for UV mode)
        return create_projector_material(uv_config, None)


def map_content_to_projector(
    content_path: str,
    projector_profile,
    calibration: SurfaceCalibration,
    surface_object: Any = None,
    projector_object: Any = None
) -> ContentMappingResult:
    """
    Convenience function for content mapping.

    Args:
        content_path: Path to content image/video
        projector_profile: ProjectorProfile instance
        calibration: Surface calibration data
        surface_object: Optional target surface mesh
        projector_object: Optional projector camera object

    Returns:
        ContentMappingResult
    """
    mapper = ContentMapper(projector_profile)
    return mapper.map_content_to_surface(
        content_path=content_path,
        surface_object=surface_object,
        projector_object=projector_object,
        calibration=calibration,
        create_proxy=surface_object is None
    )
