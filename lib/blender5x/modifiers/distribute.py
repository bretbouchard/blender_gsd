"""
Surface Distribution Utilities for Blender 5.0+.

Provides additional utilities for surface-based object distribution
using the new modifiers and Geometry Nodes system.

Example:
    >>> from lib.blender5x.modifiers import SurfaceDistribution
    >>> SurfaceDistribution.scatter_on_surface(surface, instances, density=0.5)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Object, Collection, VertexGroup


class DistributionMethod(Enum):
    """Distribution methods for surface scattering."""

    RANDOM = "random"
    """Random distribution."""

    POISSON = "poisson"
    """Poisson disk distribution (evenly spaced)."""

    GRID = "grid"
    """Regular grid distribution."""

    JITTERED = "jittered"
    """Grid with random offset."""


class AlignmentMode(Enum):
    """Alignment modes for instances."""

    NONE = "none"
    """No alignment (default orientation)."""

    NORMAL = "normal"
    """Align to surface normal."""

    TANGENT = "tangent"
    """Align to surface tangent."""

    OBJECT = "object"
    """Align to a target object."""


@dataclass
class DistributionSettings:
    """Settings for surface distribution."""

    density: float = 1.0
    """Distribution density."""

    method: DistributionMethod = DistributionMethod.RANDOM
    """Distribution method."""

    seed: int = 0
    """Random seed."""

    alignment: AlignmentMode = AlignmentMode.NORMAL
    """Instance alignment mode."""

    scale_min: float = 0.8
    """Minimum random scale."""

    scale_max: float = 1.2
    """Maximum random scale."""

    rotation_min: float = 0.0
    """Minimum random rotation (radians)."""

    rotation_max: float = 6.28318
    """Maximum random rotation (radians)."""

    use_vertex_group: bool = False
    """Use vertex group for density control."""

    vertex_group: str | None = None
    """Vertex group name for density."""

    min_distance: float = 0.0
    """Minimum distance between instances (for Poisson)."""


class SurfaceDistribution:
    """
    Surface distribution utilities for Blender 5.0+.

    Provides comprehensive tools for distributing instances on surfaces.

    Example:
        >>> SurfaceDistribution.scatter_on_surface(
        ...     surface="Ground",
        ...     instances="Trees",
        ...     density=0.1,
        ...     method=DistributionMethod.POISSON,
        ... )
    """

    @staticmethod
    def scatter_on_surface(
        surface: Object | str,
        instances: Collection | str | Object | list,
        settings: DistributionSettings | None = None,
        output_name: str | None = None,
    ) -> str:
        """
        Scatter instances on a surface with full control.

        Args:
            surface: Surface object to scatter on.
            instances: Collection, object, or list of instances to scatter.
            settings: DistributionSettings configuration.
            output_name: Name for output object (creates new if specified).

        Returns:
            Name of the modifier or output object.

        Example:
            >>> settings = DistributionSettings(
            ...     density=0.5,
            ...     method=DistributionMethod.POISSON,
            ...     min_distance=0.5,
            ... )
            >>> mod = SurfaceDistribution.scatter_on_surface(
            ...     "Ground",
            ...     "Rocks",
            ...     settings,
            ... )
        """
        import bpy

        settings = settings or DistributionSettings()

        # Get surface object
        if isinstance(surface, str):
            surface_obj = bpy.data.objects.get(surface)
            if surface_obj is None:
                raise ValueError(f"Surface object not found: {surface}")
        else:
            surface_obj = surface

        # Create output object if specified
        if output_name:
            output_obj = bpy.data.objects.new(output_name, None)
            bpy.context.collection.objects.link(output_obj)
            target_obj = output_obj
        else:
            target_obj = surface_obj

        # Get instance collection
        if isinstance(instances, str):
            coll = bpy.data.collections.get(instances)
            if coll is None:
                # Try as object
                obj = bpy.data.objects.get(instances)
                if obj:
                    coll = bpy.data.collections.new(f"{instances}_coll")
                    coll.objects.link(obj)
                else:
                    raise ValueError(f"Instance collection/object not found: {instances}")
        elif isinstance(instances, bpy.types.Collection):
            coll = instances
        elif isinstance(instances, bpy.types.Object):
            coll = bpy.data.collections.new(f"{instances.name}_coll")
            coll.objects.link(instances)
        elif isinstance(instances, list):
            coll = bpy.data.collections.new(f"ScatterInstances")
            for item in instances:
                if isinstance(item, str):
                    obj = bpy.data.objects.get(item)
                    if obj:
                        coll.objects.link(obj)
                elif isinstance(item, bpy.types.Object):
                    coll.objects.link(item)
        else:
            raise ValueError("Invalid instances type")

        # Create Geometry Nodes tree
        tree_name = f"GN_Scatter_{target_obj.name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Object Info for surface (if creating new object)
        if output_name:
            surface_info = tree.nodes.new("GeometryNodeObjectInfo")
            surface_info.inputs[0].default_value = surface_obj
            surface_info.transform_space = "RELATIVE"
            surface_geo = surface_info.outputs["Geometry"]
        else:
            surface_geo = input_node.outputs[0]

        # Distribute Points on Faces
        distribute = tree.nodes.new("GeometryNodeDistributePointsOnFaces")
        distribute.distribute_method = settings.method.value.upper()
        distribute.inputs["Density"].default_value = settings.density
        distribute.inputs["Seed"].default_value = settings.seed

        if settings.use_vertex_group and settings.vertex_group:
            distribute.use_density_vertex_group = True
            distribute.density_vertex_group = settings.vertex_group

        # Instance on Points
        instance_on_points = tree.nodes.new("GeometryNodeInstanceOnPoints")

        # Rotation (if alignment enabled)
        if settings.alignment != AlignmentMode.NONE:
            align_euler = tree.nodes.new("FunctionNodeAlignEulerToVector")
            align_euler.axis = "Z"

            if settings.alignment == AlignmentMode.NORMAL:
                tree.links.new(distribute.outputs["Normal"], align_euler.inputs["Vector"])

            tree.links.new(align_euler.outputs["Rotation"], instance_on_points.inputs["Rotation"])

        # Random Scale
        random_scale = tree.nodes.new("FunctionNodeRandomValue")
        random_scale.data_type = "FLOAT_VECTOR"
        random_scale.inputs["Min"].default_value = (
            settings.scale_min,
            settings.scale_min,
            settings.scale_min,
        )
        random_scale.inputs["Max"].default_value = (
            settings.scale_max,
            settings.scale_max,
            settings.scale_max,
        )
        random_scale.inputs["Seed"].default_value = settings.seed + 1

        # Random Rotation
        random_rotation = tree.nodes.new("FunctionNodeRandomValue")
        random_rotation.data_type = "FLOAT"
        random_rotation.inputs["Min"].default_value = settings.rotation_min
        random_rotation.inputs["Max"].default_value = settings.rotation_max
        random_rotation.inputs["Seed"].default_value = settings.seed + 2

        # Combine rotation with alignment
        if settings.alignment != AlignmentMode.NONE:
            combine_rot = tree.nodes.new("ShaderNodeVectorMath")
            combine_rot.operation = "ADD"

        # Collection Info
        collection_info = tree.nodes.new("GeometryNodeCollectionInfo")
        collection_info.inputs[0].default_value = coll
        collection_info.transform_space = "RELATIVE"

        # Realize Instances
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Position nodes
        input_node.location = (-1000, 0)
        distribute.location = (-500, 0)
        random_scale.location = (-200, 200)
        random_rotation.location = (-200, 400)
        align_euler.location = (-200, -200)
        instance_on_points.location = (200, 0)
        collection_info.location = (0, -300)
        realize.location = (500, 0)
        output_node.location = (800, 0)

        # Link nodes
        if output_name:
            tree.links.new(surface_geo, distribute.inputs["Mesh"])
        else:
            tree.links.new(input_node.outputs[0], distribute.inputs["Mesh"])

        tree.links.new(distribute.outputs["Points"], instance_on_points.inputs["Points"])
        tree.links.new(random_scale.outputs["Value"], instance_on_points.inputs["Scale"])
        tree.links.new(collection_info.outputs["Geometry"], instance_on_points.inputs["Instance"])
        tree.links.new(instance_on_points.outputs["Instances"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], output_node.inputs[0])

        # Create interface
        if not output_name:
            tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = target_obj.modifiers.new("Scatter", "NODES")
        mod.node_group = tree

        return mod.name

    @staticmethod
    def create_poisson_disk(
        surface: Object | str,
        instances: Collection | str,
        min_distance: float = 0.5,
        density: float = 1.0,
    ) -> str:
        """
        Create Poisson disk distribution for evenly-spaced instances.

        Args:
            surface: Surface object.
            instances: Collection or collection name.
            min_distance: Minimum distance between instances.
            density: Fallback density if Poisson fails.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = SurfaceDistribution.create_poisson_disk(
            ...     "Ground",
            ...     "Trees",
            ...     min_distance=2.0,
            ... )
        """
        settings = DistributionSettings(
            density=density,
            method=DistributionMethod.POISSON,
            min_distance=min_distance,
        )

        return SurfaceDistribution.scatter_on_surface(surface, instances, settings)

    @staticmethod
    def paint_distribution(
        surface: Object | str,
        instances: Collection | str,
        vertex_group: str,
        base_density: float = 1.0,
    ) -> str:
        """
        Create distribution controlled by weight painting.

        Args:
            surface: Surface object.
            instances: Collection to distribute.
            vertex_group: Vertex group name for density control.
            base_density: Base density multiplier.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = SurfaceDistribution.paint_distribution(
            ...     "Ground",
            ...     "Grass",
            ...     "GrassDensity",
            ... )
        """
        settings = DistributionSettings(
            density=base_density,
            use_vertex_group=True,
            vertex_group=vertex_group,
        )

        return SurfaceDistribution.scatter_on_surface(surface, instances, settings)

    @staticmethod
    def add_variation(
        modifier_name: str,
        scale_range: tuple[float, float] = (0.8, 1.2),
        rotation_range: tuple[float, float] = (0.0, 6.28318),
    ) -> None:
        """
        Add random scale and rotation variation to existing distribution.

        Args:
            modifier_name: Name of the existing modifier.
            scale_range: (min, max) scale range.
            rotation_range: (min, max) rotation range in radians.

        Note:
            This modifies the existing Geometry Nodes tree.
        """
        import bpy

        # Find modifier
        for obj in bpy.data.objects:
            mod = obj.modifiers.get(modifier_name)
            if mod and mod.type == "NODES" and mod.node_group:
                tree = mod.node_group

                # Find Instance on Points node
                for node in tree.nodes:
                    if node.type == "INSTANCE_ON_POINTS":
                        # Check if random value already connected
                        if node.inputs["Scale"].links:
                            continue

                        # Add random value node
                        random_scale = tree.nodes.new("FunctionNodeRandomValue")
                        random_scale.data_type = "FLOAT_VECTOR"
                        random_scale.inputs["Min"].default_value = (
                            scale_range[0],
                            scale_range[0],
                            scale_range[0],
                        )
                        random_scale.inputs["Max"].default_value = (
                            scale_range[1],
                            scale_range[1],
                            scale_range[1],
                        )

                        tree.links.new(
                            random_scale.outputs["Value"],
                            node.inputs["Scale"],
                        )
                        break

                break


class InstanceVariation:
    """
    Instance variation utilities for distributed objects.

    Provides tools for adding random variation to distributed instances.
    """

    @staticmethod
    def add_scale_variation(
        tree,
        instance_node,
        scale_min: float,
        scale_max: float,
        seed: int = 0,
    ) -> None:
        """Add scale variation to instance node."""
        random_scale = tree.nodes.new("FunctionNodeRandomValue")
        random_scale.data_type = "FLOAT_VECTOR"
        random_scale.inputs["Min"].default_value = (scale_min, scale_min, scale_min)
        random_scale.inputs["Max"].default_value = (scale_max, scale_max, scale_max)
        random_scale.inputs["Seed"].default_value = seed

        tree.links.new(random_scale.outputs["Value"], instance_node.inputs["Scale"])

    @staticmethod
    def add_rotation_variation(
        tree,
        instance_node,
        axis: str,
        min_angle: float,
        max_angle: float,
        seed: int = 0,
    ) -> None:
        """Add rotation variation around specified axis."""
        import math

        random_rot = tree.nodes.new("FunctionNodeRandomValue")
        random_rot.data_type = "FLOAT"
        random_rot.inputs["Min"].default_value = min_angle
        random_rot.inputs["Max"].default_value = max_angle
        random_rot.inputs["Seed"].default_value = seed

        # Create rotation vector based on axis
        combine_xyz = tree.nodes.new("ShaderNodeCombineXYZ")

        if axis == "X":
            tree.links.new(random_rot.outputs["Value"], combine_xyz.inputs["X"])
            combine_xyz.inputs["Y"].default_value = 0
            combine_xyz.inputs["Z"].default_value = 0
        elif axis == "Y":
            combine_xyz.inputs["X"].default_value = 0
            tree.links.new(random_rot.outputs["Value"], combine_xyz.inputs["Y"])
            combine_xyz.inputs["Z"].default_value = 0
        else:  # Z
            combine_xyz.inputs["X"].default_value = 0
            combine_xyz.inputs["Y"].default_value = 0
            tree.links.new(random_rot.outputs["Value"], combine_xyz.inputs["Z"])

        # Add to existing rotation if present
        if instance_node.inputs["Rotation"].links:
            add_rot = tree.nodes.new("ShaderNodeVectorMath")
            add_rot.operation = "ADD"

            existing_link = instance_node.inputs["Rotation"].links[0]
            tree.links.new(existing_link.from_socket, add_rot.inputs[0])
            tree.links.new(combine_xyz.outputs["Vector"], add_rot.inputs[1])
            tree.links.new(add_rot.outputs["Vector"], instance_node.inputs["Rotation"])
        else:
            tree.links.new(combine_xyz.outputs["Vector"], instance_node.inputs["Rotation"])


# Convenience exports
__all__ = [
    "SurfaceDistribution",
    "InstanceVariation",
    "DistributionSettings",
    "DistributionMethod",
    "AlignmentMode",
]
