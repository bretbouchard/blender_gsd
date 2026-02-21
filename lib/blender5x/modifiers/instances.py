"""
Instance Modifiers for Blender 5.0+.

Provides utilities for creating and managing instance modifiers,
including instancing on curves, points, and particles.

Example:
    >>> from lib.blender5x.modifiers import InstanceModifiers
    >>> InstanceModifiers.instance_on_curve(target, curve, count=10)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Object, Collection, Curve


class InstanceMode(Enum):
    """Instance modes."""

    OBJECT = "object"
    """Single object instance."""

    COLLECTION = "collection"
    """Collection instance."""

    RANDOM = "random"
    """Random from collection."""


class CurveFollowMode(Enum):
    """Curve follow modes."""

    PARALLEL = "parallel"
    """Parallel to curve tangent."""

    PERPENDICULAR = "perpendicular"
    """Perpendicular to curve."""

    STRETCH = "stretch"
    """Stretch along curve."""

    BOUNDS = "bounds"
    """Fit within curve bounds."""


@dataclass
class InstanceSettings:
    """Settings for instance modifiers."""

    mode: InstanceMode = InstanceMode.OBJECT
    """Instance mode."""

    object: str | None = None
    """Object to instance."""

    collection: str | None = None
    """Collection to instance."""

    count: int = 10
    """Number of instances."""

    use_random_rotation: bool = False
    """Apply random rotation."""

    use_random_scale: bool = False
    """Apply random scale."""

    scale_min: float = 0.8
    """Minimum scale."""

    scale_max: float = 1.2
    """Maximum scale."""

    align_to_path: bool = True
    """Align instances to path."""

    use_material_index: bool = False
    """Use material index for variation."""


class InstanceModifiers:
    """
    Instance modifier utilities for Blender 5.0+.

    Provides tools for creating instance-based modifiers.

    Example:
        >>> InstanceModifiers.instance_on_curve(
        ...     "FencePost",
        ...     "FencePath",
        ...     count=20,
        ... )
    """

    @staticmethod
    def instance_on_curve(
        target: Object | str,
        curve: Object | str,
        count: int = 10,
        follow_mode: CurveFollowMode = CurveFollowMode.PARALLEL,
        name: str = "CurveInstance",
    ) -> str:
        """
        Instance objects along a curve.

        Args:
            target: Object to instance.
            curve: Curve object to follow.
            count: Number of instances.
            follow_mode: How instances follow the curve.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = InstanceModifiers.instance_on_curve(
            ...     "Post",
            ...     "Path",
            ...     count=15,
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

        # Create Geometry Nodes modifier on curve
        tree_name = f"GN_{name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Curve to Points
        curve_to_points = tree.nodes.new("GeometryNodeCurveToPoints")
        curve_to_points.mode = "COUNT"
        curve_to_points.inputs["Count"].default_value = count

        # Object Info
        obj_info = tree.nodes.new("GeometryNodeObjectInfo")
        obj_info.inputs[0].default_value = target_obj
        obj_info.transform_space = "RELATIVE"

        # Instance on Points
        instance_on_points = tree.nodes.new("GeometryNodeInstanceOnPoints")

        # Align to path
        if follow_mode == CurveFollowMode.PARALLEL:
            align_euler = tree.nodes.new("FunctionNodeAlignEulerToVector")
            align_euler.axis = "Z"
            tree.links.new(curve_to_points.outputs["Tangent"], align_euler.inputs["Vector"])
            tree.links.new(align_euler.outputs["Rotation"], instance_on_points.inputs["Rotation"])

        # Realize Instances
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Position nodes
        input_node.location = (-800, 0)
        curve_to_points.location = (-400, 0)
        obj_info.location = (-200, -200)
        align_euler.location = (-100, 200)
        instance_on_points.location = (200, 0)
        realize.location = (500, 0)
        output_node.location = (800, 0)

        # Link nodes
        tree.links.new(input_node.outputs[0], curve_to_points.inputs["Curve"])
        tree.links.new(curve_to_points.outputs["Points"], instance_on_points.inputs["Points"])
        tree.links.new(obj_info.outputs["Geometry"], instance_on_points.inputs["Instance"])
        tree.links.new(instance_on_points.outputs["Instances"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], output_node.inputs[0])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier to curve
        mod = curve_obj.modifiers.new(name, "NODES")
        mod.node_group = tree

        return mod.name

    @staticmethod
    def instance_on_points(
        points: Object | str,
        instance: Object | str | Collection | str,
        settings: InstanceSettings | None = None,
        name: str = "PointInstance",
    ) -> str:
        """
        Instance objects on point cloud.

        Args:
            points: Point cloud object.
            instance: Object or collection to instance.
            settings: InstanceSettings configuration.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> settings = InstanceSettings(
            ...     use_random_rotation=True,
            ...     use_random_scale=True,
            ... )
            >>> mod = InstanceModifiers.instance_on_points(
            ...     "Particles",
            ...     "Tree",
            ...     settings,
            ... )
        """
        import bpy

        settings = settings or InstanceSettings()

        # Get point cloud object
        if isinstance(points, str):
            points_obj = bpy.data.objects.get(points)
        else:
            points_obj = points

        if points_obj is None:
            raise ValueError(f"Points object not found: {points}")

        # Create Geometry Nodes tree
        tree_name = f"GN_{name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Instance on Points
        instance_on_points = tree.nodes.new("GeometryNodeInstanceOnPoints")

        # Get instance source
        if isinstance(instance, str):
            # Check if it's a collection
            coll = bpy.data.collections.get(instance)
            if coll:
                collection_info = tree.nodes.new("GeometryNodeCollectionInfo")
                collection_info.inputs[0].default_value = coll
                instance_source = collection_info.outputs["Geometry"]
            else:
                # It's an object
                obj = bpy.data.objects.get(instance)
                if obj:
                    obj_info = tree.nodes.new("GeometryNodeObjectInfo")
                    obj_info.inputs[0].default_value = obj
                    instance_source = obj_info.outputs["Geometry"]
                else:
                    raise ValueError(f"Instance not found: {instance}")
        elif isinstance(instance, bpy.types.Object):
            obj_info = tree.nodes.new("GeometryNodeObjectInfo")
            obj_info.inputs[0].default_value = instance
            instance_source = obj_info.outputs["Geometry"]
        elif isinstance(instance, bpy.types.Collection):
            collection_info = tree.nodes.new("GeometryNodeCollectionInfo")
            collection_info.inputs[0].default_value = instance
            instance_source = collection_info.outputs["Geometry"]
        else:
            raise ValueError("Invalid instance type")

        # Add random variation
        if settings.use_random_scale:
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
            tree.links.new(random_scale.outputs["Value"], instance_on_points.inputs["Scale"])

        if settings.use_random_rotation:
            random_rotation = tree.nodes.new("FunctionNodeRandomValue")
            random_rotation.data_type = "FLOAT_VECTOR"
            random_rotation.inputs["Min"].default_value = (0, 0, 0)
            random_rotation.inputs["Max"].default_value = (6.28, 6.28, 6.28)
            tree.links.new(random_rotation.outputs["Value"], instance_on_points.inputs["Rotation"])

        # Realize Instances
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Position nodes
        input_node.location = (-600, 0)
        instance_on_points.location = (0, 0)
        random_scale.location = (-200, 200)
        random_rotation.location = (-200, 400)
        realize.location = (300, 0)
        output_node.location = (600, 0)

        # Link nodes
        tree.links.new(input_node.outputs[0], instance_on_points.inputs["Points"])
        tree.links.new(instance_source, instance_on_points.inputs["Instance"])
        tree.links.new(instance_on_points.outputs["Instances"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], output_node.inputs[0])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = points_obj.modifiers.new(name, "NODES")
        mod.node_group = tree

        return mod.name

    @staticmethod
    def instance_on_vertices(
        mesh: Object | str,
        instance: Object | str,
        scale: float = 1.0,
        align_to_normal: bool = False,
        name: str = "VertexInstance",
    ) -> str:
        """
        Instance objects on mesh vertices.

        Args:
            mesh: Mesh object.
            instance: Object to instance.
            scale: Uniform scale for instances.
            align_to_normal: Align to vertex normals.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = InstanceModifiers.instance_on_vertices(
            ...     "BaseMesh",
            ...     "Spike",
            ...     align_to_normal=True,
            ... )
        """
        import bpy

        # Get objects
        if isinstance(mesh, str):
            mesh_obj = bpy.data.objects.get(mesh)
        else:
            mesh_obj = mesh

        if isinstance(instance, str):
            instance_obj = bpy.data.objects.get(instance)
        else:
            instance_obj = instance

        if mesh_obj is None:
            raise ValueError(f"Mesh object not found: {mesh}")
        if instance_obj is None:
            raise ValueError(f"Instance object not found: {instance}")

        # Create Geometry Nodes tree
        tree_name = f"GN_{name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Mesh to Points (vertices)
        mesh_to_points = tree.nodes.new("GeometryNodeMeshToPoints")
        mesh_to_points.mode = "VERTICES"

        # Object Info
        obj_info = tree.nodes.new("GeometryNodeObjectInfo")
        obj_info.inputs[0].default_value = instance_obj

        # Instance on Points
        instance_on_points = tree.nodes.new("GeometryNodeInstanceOnPoints")
        instance_on_points.inputs["Scale"].default_value = (scale, scale, scale)

        # Align to normal if requested
        if align_to_normal:
            normal = tree.nodes.new("GeometryNodeInputNormal")
            align_euler = tree.nodes.new("FunctionNodeAlignEulerToVector")
            align_euler.axis = "Z"
            tree.links.new(normal.outputs["Normal"], align_euler.inputs["Vector"])
            tree.links.new(align_euler.outputs["Rotation"], instance_on_points.inputs["Rotation"])

        # Realize Instances
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Position nodes
        input_node.location = (-800, 0)
        mesh_to_points.location = (-400, 0)
        normal.location = (-200, 200)
        align_euler.location = (0, 200)
        obj_info.location = (-200, -200)
        instance_on_points.location = (200, 0)
        realize.location = (500, 0)
        output_node.location = (800, 0)

        # Link nodes
        tree.links.new(input_node.outputs[0], mesh_to_points.inputs["Mesh"])
        tree.links.new(mesh_to_points.outputs["Points"], instance_on_points.inputs["Points"])
        tree.links.new(obj_info.outputs["Geometry"], instance_on_points.inputs["Instance"])
        tree.links.new(instance_on_points.outputs["Instances"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], output_node.inputs[0])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = mesh_obj.modifiers.new(name, "NODES")
        mod.node_group = tree

        return mod.name

    @staticmethod
    def replace_with_collection(
        target: Object | str,
        collection: str,
        keep_transform: bool = True,
        name: str = "CollectionInstance",
    ) -> str:
        """
        Replace object with collection instances.

        Args:
            target: Object to replace.
            collection: Collection name to instance.
            keep_transform: Keep object transform for instances.
            name: Modifier name.

        Returns:
            Name of the created modifier.

        Example:
            >>> mod = InstanceModifiers.replace_with_collection(
            ...     "Proxy",
            ...     "DetailedModel",
            ... )
        """
        import bpy

        # Get target object
        if isinstance(target, str):
            target_obj = bpy.data.objects.get(target)
        else:
            target_obj = target

        if target_obj is None:
            raise ValueError(f"Target object not found: {target}")

        # Get collection
        coll = bpy.data.collections.get(collection)
        if coll is None:
            raise ValueError(f"Collection not found: {collection}")

        # Create Geometry Nodes tree
        tree_name = f"GN_{name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Collection Info
        collection_info = tree.nodes.new("GeometryNodeCollectionInfo")
        collection_info.inputs[0].default_value = coll
        collection_info.transform_space = "RELATIVE" if keep_transform else "ORIGINAL"

        # Realize Instances (optional)
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Position nodes
        input_node.location = (-400, 0)
        collection_info.location = (0, 0)
        realize.location = (300, 0)
        output_node.location = (600, 0)

        # Link nodes
        tree.links.new(collection_info.outputs["Geometry"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], output_node.inputs[0])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = target_obj.modifiers.new(name, "NODES")
        mod.node_group = tree

        return mod.name


# Convenience exports
__all__ = [
    "InstanceModifiers",
    "InstanceSettings",
    "InstanceMode",
    "CurveFollowMode",
]
