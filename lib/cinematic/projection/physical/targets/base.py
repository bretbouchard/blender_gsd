"""
Base classes for projection target builders.

Provides abstract base class and concrete implementations for creating
Blender geometry from projection target configurations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Tuple, Any
import math

from .types import (
    ProjectionTarget,
    ProjectionSurface,
    TargetGeometryResult,
    TargetType,
)


class TargetBuilder(ABC):
    """
    Abstract base class for projection target builders.

    Subclasses implement geometry creation for specific target types.
    """

    def __init__(self, config: ProjectionTarget):
        """
        Initialize builder with target configuration.

        Args:
            config: ProjectionTarget configuration
        """
        self.config = config

    @abstractmethod
    def create_geometry(self) -> TargetGeometryResult:
        """
        Create Blender geometry for this target.

        Returns:
            TargetGeometryResult with created objects
        """
        pass

    @abstractmethod
    def get_calibration_points(self) -> List[Tuple[float, float, float]]:
        """
        Get default calibration points for this target.

        Returns:
            List of (x, y, z) calibration points
        """
        pass

    @abstractmethod
    def get_recommended_projector_position(
        self,
        throw_ratio: float
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """
        Get recommended projector position and rotation.

        Args:
            throw_ratio: Projector throw ratio

        Returns:
            ((x, y, z), (rx, ry, rz)) position and rotation euler tuple
        """
        pass

    def apply_material(
        self,
        surface_obj: Any,
        surface: ProjectionSurface
    ) -> List[str]:
        """
        Apply material to surface based on surface properties.

        Args:
            surface_obj: Blender object to apply material to
            surface: Surface configuration

        Returns:
            List of warnings/errors
        """
        warnings = []

        try:
            import bpy

            # Create simple diffuse material matching surface properties
            mat_name = f"{surface.name}_material"
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True

            # Set diffuse color based on albedo
            bsdf = mat.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = (
                surface.albedo, surface.albedo, surface.albedo, 1.0
            )
            bsdf.inputs['Roughness'].default_value = 1.0 - surface.glossiness

            # Apply to object
            if surface_obj.data.materials:
                surface_obj.data.materials[0] = mat
            else:
                surface_obj.data.materials.append(mat)

        except ImportError:
            warnings.append("Blender (bpy) not available - material not applied")
        except Exception as e:
            warnings.append(f"Error applying material: {e}")

        return warnings

    def validate_dimensions(self) -> List[str]:
        """
        Validate target dimensions are reasonable.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if self.config.width_m <= 0:
            errors.append(f"Invalid width: {self.config.width_m}")
        if self.config.height_m <= 0:
            errors.append(f"Invalid height: {self.config.height_m}")
        if self.config.depth_m < 0:
            errors.append(f"Invalid depth: {self.config.depth_m}")

        # Check for reasonable size limits
        if self.config.width_m > 100:
            errors.append(f"Width {self.config.width_m}m exceeds 100m limit")
        if self.config.height_m > 100:
            errors.append(f"Height {self.config.height_m}m exceeds 100m limit")

        return errors

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Full validation of target configuration.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = self.validate_dimensions()

        # Validate surfaces
        for surface in self.config.surfaces:
            if surface.area_m2 <= 0:
                errors.append(f"Surface '{surface.name}' has invalid area: {surface.area_m2}")
            if not (0 <= surface.albedo <= 1):
                errors.append(f"Surface '{surface.name}' albedo out of range: {surface.albedo}")
            if not (0 <= surface.glossiness <= 1):
                errors.append(f"Surface '{surface.name}' glossiness out of range: {surface.glossiness}")

        return len(errors) == 0, errors


class PlanarTargetBuilder(TargetBuilder):
    """Builder for planar projection targets."""

    def create_geometry(self) -> TargetGeometryResult:
        """Create a simple planar mesh."""
        result = TargetGeometryResult()

        # Validate first
        is_valid, errors = self.validate()
        if not is_valid:
            result.errors = errors
            return result

        try:
            import bpy

            # Create mesh
            mesh = bpy.data.meshes.new(f"{self.config.name}_mesh")
            obj = bpy.data.objects.new(self.config.name, mesh)

            # Create vertices for rectangle
            w, h = self.config.width_m / 2, self.config.height_m / 2
            verts = [
                (-w, 0, -h),  # Bottom-left
                (w, 0, -h),   # Bottom-right
                (w, 0, h),    # Top-right
                (-w, 0, h),   # Top-left
            ]
            faces = [(0, 1, 2, 3)]

            mesh.from_pydata(verts, [], faces)

            # Create UV layer
            uv_layer = mesh.uv_layers.new(name="ProjectorUV")
            uv_data = uv_layer.data
            uv_data[0].uv = (0, 0)  # Bottom-left
            uv_data[1].uv = (1, 0)  # Bottom-right
            uv_data[2].uv = (1, 1)  # Top-right
            uv_data[3].uv = (0, 1)  # Top-left

            # Link to collection
            bpy.context.collection.objects.link(obj)

            # Apply material to primary surface
            if self.config.surfaces:
                mat_warnings = self.apply_material(obj, self.config.surfaces[0])
                result.warnings.extend(mat_warnings)

            result.object = obj
            result.surfaces = {"main": obj}
            result.uv_layers = {"ProjectorUV": uv_layer}

        except ImportError:
            result.errors.append("Blender (bpy) not available")
        except Exception as e:
            result.errors.append(f"Error creating geometry: {e}")

        return result

    def get_calibration_points(self) -> List[Tuple[float, float, float]]:
        """Get 3 calibration points for planar surface."""
        w, h = self.config.width_m / 2, self.config.height_m / 2
        return [
            (-w, 0, -h),  # Bottom-left
            (w, 0, -h),   # Bottom-right
            (-w, 0, h),   # Top-left
        ]

    def get_recommended_projector_position(
        self,
        throw_ratio: float
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Calculate projector position for optimal coverage."""
        # Distance = throw_ratio * image_width
        distance = throw_ratio * self.config.width_m

        # Position: in front of center, at correct distance
        position = (0.0, -distance, self.config.height_m / 2)

        # Rotation: pointing at center (90 degrees pitch to face forward)
        rotation = (math.pi / 2, 0.0, 0.0)

        return position, rotation


class MultiSurfaceTargetBuilder(TargetBuilder):
    """Builder for multi-surface projection targets."""

    def create_geometry(self) -> TargetGeometryResult:
        """Create multiple connected surfaces."""
        result = TargetGeometryResult()

        # Validate first
        is_valid, errors = self.validate()
        if not is_valid:
            result.errors = errors
            return result

        if not self.config.surfaces:
            result.errors.append("No surfaces defined in multi-surface target")
            return result

        try:
            import bpy

            surfaces_dict = {}

            # Create parent empty
            parent = bpy.data.objects.new(f"{self.config.name}_Group", None)
            parent.empty_display_type = 'PLAIN_AXES'
            bpy.context.collection.objects.link(parent)

            for surface in self.config.surfaces:
                # Create individual surface geometry
                surf_obj, surf_warnings = self._create_surface_object(surface)
                if surf_obj:
                    surf_obj.parent = parent
                    surfaces_dict[surface.name] = surf_obj
                result.warnings.extend(surf_warnings)

            result.object = parent
            result.surfaces = surfaces_dict

        except ImportError:
            result.errors.append("Blender (bpy) not available")
        except Exception as e:
            result.errors.append(f"Error creating geometry: {e}")

        return result

    def _create_surface_object(
        self,
        surface: ProjectionSurface
    ) -> Tuple[Any, List[str]]:
        """Create a single surface object."""
        warnings = []
        obj = None

        try:
            import bpy

            mesh = bpy.data.meshes.new(f"{surface.name}_mesh")
            obj = bpy.data.objects.new(surface.name, mesh)

            # Create planar quad for this surface
            x, y, z = surface.position
            w, h = surface.dimensions

            verts = [
                (x - w/2, y, z - h/2),  # Bottom-left
                (x + w/2, y, z - h/2),  # Bottom-right
                (x + w/2, y, z + h/2),  # Top-right
                (x - w/2, y, z + h/2),  # Top-left
            ]
            faces = [(0, 1, 2, 3)]

            mesh.from_pydata(verts, [], faces)

            # Create UV layer
            uv_layer = mesh.uv_layers.new(name="ProjectorUV")
            uv_data = uv_layer.data
            uv_data[0].uv = (0, 0)
            uv_data[1].uv = (1, 0)
            uv_data[2].uv = (1, 1)
            uv_data[3].uv = (0, 1)

            # Link to collection
            bpy.context.collection.objects.link(obj)

            # Apply material
            mat_warnings = self.apply_material(obj, surface)
            warnings.extend(mat_warnings)

        except ImportError:
            warnings.append("Blender (bpy) not available")
        except Exception as e:
            warnings.append(f"Error creating surface '{surface.name}': {e}")

        return obj, warnings

    def get_calibration_points(self) -> List[Tuple[float, float, float]]:
        """Get 4+ calibration points for multi-surface."""
        # Collect points from all surfaces
        points = []
        for surface in self.config.surfaces:
            if surface.calibration_points:
                points.extend(surface.calibration_points)
            else:
                points.extend(surface.compute_default_calibration_points())
        return points[:4]  # Return first 4 for DLT

    def get_recommended_projector_position(
        self,
        throw_ratio: float
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Calculate position to cover all surfaces."""
        if not self.config.surfaces:
            return (0.0, -1.0, 0.0), (math.pi / 2, 0.0, 0.0)

        # Find bounding box of all surfaces
        min_x = min_z = float('inf')
        max_x = max_z = float('-inf')

        for surface in self.config.surfaces:
            x, y, z = surface.position
            w, h = surface.dimensions

            min_x = min(min_x, x - w/2)
            max_x = max(max_x, x + w/2)
            min_z = min(min_z, z - h/2)
            max_z = max(max_z, z + h/2)

        # Calculate center and required distance
        center_x = (min_x + max_x) / 2
        center_z = (min_z + max_z) / 2
        total_width = max_x - min_x

        distance = throw_ratio * max(total_width, self.config.width_m)

        position = (center_x, -distance, center_z)
        rotation = (math.pi / 2, 0.0, 0.0)

        return position, rotation


def create_builder(config: ProjectionTarget) -> TargetBuilder:
    """
    Factory function to create appropriate builder for target type.

    Args:
        config: ProjectionTarget configuration

    Returns:
        Appropriate TargetBuilder subclass instance
    """
    if config.target_type == TargetType.PLANAR:
        return PlanarTargetBuilder(config)
    elif config.target_type == TargetType.MULTI_SURFACE:
        return MultiSurfaceTargetBuilder(config)
    else:
        # Default to planar for unknown types
        return PlanarTargetBuilder(config)
