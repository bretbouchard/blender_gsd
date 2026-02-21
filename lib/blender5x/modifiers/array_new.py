"""
New Array Modifier for Blender 5.0+.

Blender 5.0 introduced a completely redesigned array modifier with
linear, radial, and curve-based distribution, plus interactive gizmos
for real-time adjustment.

Example:
    >>> from lib.blender5x.modifiers import NewArrayModifier, SurfaceDistribute
    >>> NewArrayModifier.create_radial(target, count=12, axis="Z")
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Object, Modifier


class ArrayFitType(Enum):
    """Array fit types."""

    FIXED_COUNT = "FIXED_COUNT"
    """Fixed number of copies."""

    FIT_LENGTH = "FIT_LENGTH"
    """Fit within specified length."""

    FIT_CURVE = "FIT_CURVE"
    """Fit along curve length."""


class ArrayDistribution(Enum):
    """Distribution modes."""

    LINEAR = "linear"
    """Linear distribution along an axis."""

    RADIAL = "radial"
    """Radial distribution around an axis."""

    CURVE = "curve"
    """Distribution along a curve path."""

    SURFACE = "surface"
    """Distribution on a surface."""


@dataclass
class ArraySettings:
    """Settings for array modifier."""

    count: int = 5
    """Number of copies."""

    fit_type: ArrayFitType = ArrayFitType.FIXED_COUNT
    """How to determine array length."""

    relative_offset: tuple[float, float, float] = (1.0, 0.0, 0.0)
    """Relative offset between copies."""

    constant_offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Constant offset between copies."""

    use_object_offset: bool = False
    """Use object transform for offset."""

    offset_object: str | None = None
    """Object to use for offset."""

    use_merge_vertices: bool = False
    """Merge vertices between copies."""

    merge_distance: float = 0.01
    """Merge distance threshold."""

    use_relative_offset: bool = True
    """Use relative offset."""

    start_cap: str | None = None
    """Start cap object."""

    end_cap: str | None = None
    """End cap object."""


class NewArrayModifier:
    """
    Blender 5.0 new array modifier utilities.

    Provides tools for creating and configuring array modifiers with
    the redesigned system in Blender 5.0.

    Example:
        >>> NewArrayModifier.create_linear(target, count=5, offset=(2, 0, 0))
        >>> NewArrayModifier.create_radial(target, count=12, axis="Z")
    """

    @staticmethod
    def create(
        target: Object | str,
        settings: ArraySettings,
        name: str = "Array",
    ) -> str:
        """
        Create an array modifier with specified settings.

        Args:
            target: Target object.
            settings: ArraySettings configuration.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> settings = ArraySettings(
            ...     count=10,
            ...     relative_offset=(1.5, 0, 0),
            ... )
            >>> mod = NewArrayModifier.create("Cube", settings)
        """
        import bpy

        # Get target object
        if isinstance(target, str):
            target_obj = bpy.data.objects.get(target)
            if target_obj is None:
                raise ValueError(f"Object not found: {target}")
        else:
            target_obj = target

        # Create array modifier
        mod = target_obj.modifiers.new(name, "ARRAY")

        # Configure settings
        mod.count = settings.count
        mod.fit_type = settings.fit_type.value

        # Offsets
        mod.use_relative_offset = settings.use_relative_offset
        if settings.use_relative_offset:
            mod.relative_offset_displace = list(settings.relative_offset)

        mod.use_constant_offset = any(v != 0 for v in settings.constant_offset)
        if mod.use_constant_offset:
            mod.constant_offset_displace = list(settings.constant_offset)

        # Object offset
        if settings.use_object_offset and settings.offset_object:
            offset_obj = bpy.data.objects.get(settings.offset_object)
            if offset_obj:
                mod.use_object_offset = True
                mod.offset_object = offset_obj

        # Merge
        mod.use_merge_vertices = settings.use_merge_vertices
        if settings.use_merge_vertices:
            mod.merge_threshold = settings.merge_distance

        # Caps
        if settings.start_cap:
            cap_obj = bpy.data.objects.get(settings.start_cap)
            if cap_obj:
                mod.start_cap = cap_obj

        if settings.end_cap:
            cap_obj = bpy.data.objects.get(settings.end_cap)
            if cap_obj:
                mod.end_cap = cap_obj

        return mod.name

    @staticmethod
    def create_linear(
        target: Object | str,
        count: int = 5,
        offset: tuple[float, float, float] = (2.0, 0.0, 0.0),
        relative: bool = True,
        name: str = "LinearArray",
    ) -> str:
        """
        Create a linear array modifier.

        Args:
            target: Target object.
            count: Number of copies.
            offset: Offset between copies.
            relative: Use relative (True) or constant (False) offset.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = NewArrayModifier.create_linear(
            ...     "Brick",
            ...     count=20,
            ...     offset=(2.5, 0, 0),
            ... )
        """
        settings = ArraySettings(
            count=count,
            relative_offset=offset if relative else (1.0, 0.0, 0.0),
            constant_offset=offset if not relative else (0.0, 0.0, 0.0),
            use_relative_offset=relative,
        )

        return NewArrayModifier.create(target, settings, name)

    @staticmethod
    def create_radial(
        target: Object | str,
        count: int = 12,
        axis: str = "Z",
        center: tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "RadialArray",
    ) -> str:
        """
        Create a radial array modifier.

        Creates copies arranged in a circle around the specified axis.

        Args:
            target: Target object.
            count: Number of copies around the circle.
            axis: Rotation axis ('X', 'Y', or 'Z').
            center: Center point for the radial array.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = NewArrayModifier.create_radial(
            ...     "Spoke",
            ...     count=8,
            ...     axis="Z",
            ...     center=(0, 0, 0),
            ... )
        """
        import bpy
        import math

        # Get target object
        if isinstance(target, str):
            target_obj = bpy.data.objects.get(target)
            if target_obj is None:
                raise ValueError(f"Object not found: {target}")
        else:
            target_obj = target

        # Create an empty object for radial offset
        empty_name = f"{name}_Offset"
        empty = bpy.data.objects.new(empty_name, None)
        empty.empty_display_type = "ARROWS"
        bpy.context.collection.objects.link(empty)

        # Position empty at center
        empty.location = center

        # Rotate empty based on axis and count
        angle = 2 * math.pi / count
        if axis == "X":
            empty.rotation_euler = (angle, 0, 0)
        elif axis == "Y":
            empty.rotation_euler = (0, angle, 0)
        else:  # Z
            empty.rotation_euler = (0, 0, angle)

        # Create array modifier
        settings = ArraySettings(
            count=count,
            use_object_offset=True,
            offset_object=empty.name,
        )

        return NewArrayModifier.create(target_obj, settings, name)

    @staticmethod
    def create_curve_array(
        target: Object | str,
        curve: Object | str,
        count: int = 10,
        fit_type: ArrayFitType = ArrayFitType.FIT_CURVE,
        name: str = "CurveArray",
    ) -> str:
        """
        Create a curve-following array modifier.

        Distributes copies along a curve path.

        Args:
            target: Target object.
            curve: Curve object to follow.
            count: Number of copies (if fit_type is FIXED_COUNT).
            fit_type: How to determine array length.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = NewArrayModifier.create_curve_array(
            ...     "FencePost",
            ...     "FencePath",
            ...     count=20,
            ... )
        """
        import bpy

        # Get objects
        if isinstance(target, str):
            target_obj = bpy.data.objects.get(target)
        else:
            target_obj = target

        if isinstance(curve, str):
            curve_obj = bpy.data.objects.get(curve)
        else:
            curve_obj = curve

        if target_obj is None:
            raise ValueError(f"Target object not found: {target}")
        if curve_obj is None:
            raise ValueError(f"Curve object not found: {curve}")

        # Create array modifier
        mod = target_obj.modifiers.new(name, "ARRAY")

        mod.fit_type = fit_type.value
        mod.count = count

        # Add curve modifier for path following
        curve_mod = target_obj.modifiers.new(f"{name}_Curve", "CURVE")
        curve_mod.object = curve_obj
        curve_mod.deform_axis = "POS_Z"

        return mod.name

    @staticmethod
    def enable_gizmo(modifier: Modifier | str) -> None:
        """
        Enable interactive gizmo for the array modifier.

        Args:
            modifier: Array modifier or name.

        Note:
            Gizmos are automatically shown in the 3D viewport when
            the modifier is selected in the properties panel.

        Example:
            >>> NewArrayModifier.enable_gizmo("Array")
        """
        # In Blender 5.0, gizmos are controlled via the UI
        # This would typically be handled by the viewport
        # The modifier automatically shows gizmos when selected
        pass


class SurfaceDistribute:
    """
    Surface distribution modifier utilities (Blender 5.0+).

    Provides tools for distributing objects on surfaces using
    the new surface distribution system.

    Example:
        >>> SurfaceDistribute.distribute_collection(
        ...     surface="Ground",
        ...     collection="Rocks",
        ...     density=0.5,
        ... )
    """

    @staticmethod
    def distribute_collection(
        surface: Object | str,
        collection: str,
        density: float = 1.0,
        seed: int = 0,
        name: str = "SurfaceDistribute",
    ) -> str:
        """
        Distribute collection instances on a surface.

        Uses Geometry Nodes to scatter collection instances.

        Args:
            surface: Surface object to distribute on.
            collection: Collection name to distribute.
            density: Distribution density.
            seed: Random seed.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = SurfaceDistribute.distribute_collection(
            ...     surface="Ground",
            ...     collection="Trees",
            ...     density=0.1,
            ...     seed=42,
            ... )
        """
        import bpy

        # Get surface object
        if isinstance(surface, str):
            surface_obj = bpy.data.objects.get(surface)
            if surface_obj is None:
                raise ValueError(f"Surface object not found: {surface}")
        else:
            surface_obj = surface

        # Get collection
        coll = bpy.data.collections.get(collection)
        if coll is None:
            raise ValueError(f"Collection not found: {collection}")

        # Create Geometry Nodes modifier
        tree_name = f"GN_{name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Distribute Points on Faces
        distribute = tree.nodes.new("GeometryNodeDistributePointsOnFaces")
        distribute.distribute_method = "RANDOM"
        distribute.inputs["Density"].default_value = density
        distribute.inputs["Seed"].default_value = seed

        # Instance on Points
        instance_on_points = tree.nodes.new("GeometryNodeInstanceOnPoints")

        # Object Info for collection instances
        collection_info = tree.nodes.new("GeometryNodeCollectionInfo")
        collection_info.inputs[0].default_value = coll
        collection_info.transform_space = "RELATIVE"

        # Realize Instances
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Position nodes
        input_node.location = (-600, 0)
        distribute.location = (-300, 0)
        instance_on_points.location = (0, 0)
        collection_info.location = (-100, -200)
        realize.location = (300, 0)
        output_node.location = (600, 0)

        # Link nodes
        tree.links.new(input_node.outputs[0], distribute.inputs["Mesh"])
        tree.links.new(distribute.outputs["Points"], instance_on_points.inputs["Points"])
        tree.links.new(collection_info.outputs["Geometry"], instance_on_points.inputs["Instance"])
        tree.links.new(instance_on_points.outputs["Instances"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], output_node.inputs[0])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = surface_obj.modifiers.new(name, "NODES")
        mod.node_group = tree

        return mod.name

    @staticmethod
    def with_vertex_group(
        surface: Object | str,
        collection: str,
        vertex_group: str,
        base_density: float = 1.0,
        name: str = "VGDistribute",
    ) -> str:
        """
        Distribute collection using vertex group for density control.

        Args:
            surface: Surface object.
            collection: Collection to distribute.
            vertex_group: Vertex group name for density mask.
            base_density: Base density multiplier.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = SurfaceDistribute.with_vertex_group(
            ...     surface="Ground",
            ...     collection="Grass",
            ...     vertex_group="GrassMask",
            ... )
        """
        import bpy

        # Get objects
        if isinstance(surface, str):
            surface_obj = bpy.data.objects.get(surface)
        else:
            surface_obj = surface

        if surface_obj is None:
            raise ValueError(f"Surface object not found: {surface}")

        coll = bpy.data.collections.get(collection)
        if coll is None:
            raise ValueError(f"Collection not found: {collection}")

        # Check vertex group exists
        if vertex_group not in surface_obj.vertex_groups:
            raise ValueError(f"Vertex group not found: {vertex_group}")

        # Create Geometry Nodes tree
        tree_name = f"GN_{name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Distribute Points on Faces
        distribute = tree.nodes.new("GeometryNodeDistributePointsOnFaces")
        distribute.distribute_method = "RANDOM"
        distribute.use_density_vertex_group = True
        distribute.density_vertex_group = vertex_group
        distribute.inputs["Density"].default_value = base_density

        # Instance on Points
        instance_on_points = tree.nodes.new("GeometryNodeInstanceOnPoints")

        # Collection Info
        collection_info = tree.nodes.new("GeometryNodeCollectionInfo")
        collection_info.inputs[0].default_value = coll

        # Realize
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Position nodes
        input_node.location = (-600, 0)
        distribute.location = (-300, 0)
        instance_on_points.location = (0, 0)
        collection_info.location = (-100, -200)
        realize.location = (300, 0)
        output_node.location = (600, 0)

        # Link nodes
        tree.links.new(input_node.outputs[0], distribute.inputs["Mesh"])
        tree.links.new(distribute.outputs["Points"], instance_on_points.inputs["Points"])
        tree.links.new(collection_info.outputs["Geometry"], instance_on_points.inputs["Instance"])
        tree.links.new(instance_on_points.outputs["Instances"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], output_node.inputs[0])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = surface_obj.modifiers.new(name, "NODES")
        mod.node_group = tree

        return mod.name

    @staticmethod
    def aligned_to_normal(
        surface: Object | str,
        collection: str,
        density: float = 1.0,
        name: str = "NormalDistribute",
    ) -> str:
        """
        Distribute collection aligned to surface normals.

        Args:
            surface: Surface object.
            collection: Collection to distribute.
            density: Distribution density.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = SurfaceDistribute.aligned_to_normal(
            ...     surface="Ground",
            ...     collection="Rocks",
            ...     density=0.2,
            ... )
        """
        import bpy

        # Get objects
        if isinstance(surface, str):
            surface_obj = bpy.data.objects.get(surface)
        else:
            surface_obj = surface

        if surface_obj is None:
            raise ValueError(f"Surface object not found: {surface}")

        coll = bpy.data.collections.get(collection)
        if coll is None:
            raise ValueError(f"Collection not found: {collection}")

        # Create Geometry Nodes tree
        tree_name = f"GN_{name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Distribute Points on Faces
        distribute = tree.nodes.new("GeometryNodeDistributePointsOnFaces")
        distribute.distribute_method = "RANDOM"
        distribute.inputs["Density"].default_value = density

        # Instance on Points with alignment
        instance_on_points = tree.nodes.new("GeometryNodeInstanceOnPoints")

        # Normal input
        normal_node = tree.nodes.new("GeometryNodeInputNormal")

        # Align Euler to Vector
        align_euler = tree.nodes.new("FunctionNodeAlignEulerToVector")
        align_euler.axis = "Z"

        # Collection Info
        collection_info = tree.nodes.new("GeometryNodeCollectionInfo")
        collection_info.inputs[0].default_value = coll

        # Realize
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Position nodes
        input_node.location = (-800, 0)
        distribute.location = (-500, 0)
        normal_node.location = (-300, 200)
        align_euler.location = (-100, 200)
        instance_on_points.location = (0, 0)
        collection_info.location = (0, -200)
        realize.location = (300, 0)
        output_node.location = (600, 0)

        # Link nodes
        tree.links.new(input_node.outputs[0], distribute.inputs["Mesh"])
        tree.links.new(distribute.outputs["Points"], instance_on_points.inputs["Points"])
        tree.links.new(distribute.outputs["Normal"], align_euler.inputs["Vector"])
        tree.links.new(align_euler.outputs["Rotation"], instance_on_points.inputs["Rotation"])
        tree.links.new(collection_info.outputs["Geometry"], instance_on_points.inputs["Instance"])
        tree.links.new(instance_on_points.outputs["Instances"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], output_node.inputs[0])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = surface_obj.modifiers.new(name, "NODES")
        mod.node_group = tree

        return mod.name


# Convenience exports
__all__ = [
    "NewArrayModifier",
    "SurfaceDistribute",
    "ArraySettings",
    "ArrayFitType",
    "ArrayDistribution",
]
