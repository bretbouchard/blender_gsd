"""
InstanceController - Instance extraction and control via geometry nodes.

Provides utilities for creating, manipulating, and extracting transform
data from instances in Blender's geometry nodes system.

Usage:
    # Create a triangle proxy for custom orientation
    proxy = InstanceController.create_triangle_proxy("MyProxy")

    # Extract matrices from instances
    matrices = InstanceController.extract_transform_matrices(instance_geometry)

    # Parent an object to a triangle
    InstanceController.parent_to_triangle(child_obj, triangle_obj)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import bpy
from mathutils import Matrix, Vector

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bpy.types import Collection, Object


class InstanceController:
    """
    Control instances via geometry nodes.

    Provides static methods for creating proxy geometry, parenting
    objects, and extracting/applying transform matrices for instances.
    """

    @staticmethod
    def create_triangle_proxy(
        name: str = "Triangle_Proxy",
        scale: float = 0.1,
    ) -> Object:
        """
        Create a triangle mesh proxy object for custom orientation.

        Triangle proxies are useful for representing custom coordinate
        systems in geometry nodes. The triangle defines a local frame
        where:
        - The first vertex is the origin
        - The edge from v0 to v1 defines the X axis
        - The edge from v0 to v2 defines the Y axis
        - Z is perpendicular to the triangle face

        Args:
            name: Name for the proxy object.
            scale: Size scale for the triangle (default 0.1 for compact markers).

        Returns:
            The created triangle mesh object.

        Example:
            >>> proxy = InstanceController.create_triangle_proxy("Orient1")
            >>> proxy.location = (1, 2, 3)
        """
        # Create triangle mesh data
        mesh = bpy.data.meshes.new(f"{name}_mesh")

        # Define vertices for a right triangle
        # v0 = origin, v0->v1 = X, v0->v2 = Y
        vertices = [
            (0, 0, 0),           # Origin
            (scale, 0, 0),       # X direction
            (0, scale, 0),       # Y direction
        ]
        faces = [(0, 1, 2)]  # Single triangle face

        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        # Create object and link to collection
        obj = bpy.data.objects.new(name, mesh)

        # Link to active collection
        collection = InstanceController._get_active_collection()
        collection.objects.link(obj)

        return obj

    @staticmethod
    def _get_active_collection() -> Collection:
        """Get the currently active collection for object linking."""
        view_layer = bpy.context.view_layer
        if view_layer.active_layer_collection:
            return view_layer.active_layer_collection.collection
        return bpy.context.scene.collection

    @staticmethod
    def parent_to_triangle(
        child: Object,
        triangle: Object,
        vertex_index: int = 0,
    ) -> None:
        """
        Parent a child object to a triangle proxy.

        Sets up a parent relationship where the child follows the
        triangle's position. Useful for attaching objects to
        procedurally generated instances.

        Args:
            child: The object to be parented.
            triangle: The triangle proxy object to parent to.
            vertex_index: Which vertex to attach to (0, 1, or 2).

        Raises:
            ValueError: If vertex_index is out of range.
            TypeError: If triangle doesn't have mesh data.
        """
        if not triangle.data or not hasattr(triangle.data, "vertices"):
            raise TypeError(f"Object '{triangle.name}' must have mesh data")

        mesh = triangle.data
        if vertex_index < 0 or vertex_index >= len(mesh.vertices):
            raise ValueError(
                f"vertex_index {vertex_index} out of range for triangle with "
                f"{len(mesh.vertices)} vertices"
            )

        # Set parent relationship
        child.parent = triangle

        # Calculate offset based on vertex position
        vertex = mesh.vertices[vertex_index]
        child.location = vertex.co

    @staticmethod
    def extract_transform_matrices(instances: Sequence) -> list[Matrix]:
        """
        Extract 4x4 transformation matrices from instances.

        Converts instance data into standard 4x4 transformation matrices
        that can be used for transforms, parenting, or further computation.

        Args:
            instances: A sequence of instance objects or instance geometry.
                      Can be from realized instances or instance attributes.

        Returns:
            List of 4x4 transformation matrices as mathutils.Matrix objects.

        Raises:
            TypeError: If instances cannot be processed.

        Example:
            >>> # Get matrices from a collection of instance objects
            >>> matrices = InstanceController.extract_transform_matrices(obj.instances)
            >>> for i, matrix in enumerate(matrices):
            ...     print(f"Instance {i}: location = {matrix.translation}")
        """
        matrices: list[Matrix] = []

        for instance in instances:
            if isinstance(instance, Object):
                # Direct object instance
                matrices.append(instance.matrix_world.copy())
            elif hasattr(instance, "matrix"):
                # Instance with matrix attribute
                matrices.append(Matrix(instance.matrix))
            elif hasattr(instance, "location") and hasattr(instance, "rotation"):
                # Instance with separate transforms
                loc = Vector(instance.location)
                rot = instance.rotation
                scale = getattr(instance, "scale", Vector((1, 1, 1)))

                # Build matrix from components
                matrix = (
                    Matrix.LocRotScale(loc, rot, scale)
                    if hasattr(rot, "to_quaternion")
                    else Matrix.Translation(loc) @ Matrix.Rotation(rot, 4, "Z")
                )
                matrices.append(matrix)
            else:
                raise TypeError(
                    f"Cannot extract transform from instance of type {type(instance)}"
                )

        return matrices

    @staticmethod
    def apply_transform_to_instances(
        geometry,
        matrices: Sequence[Matrix],
    ):
        """
        Apply a list of transformation matrices to instances.

        Creates a node setup that applies the given matrices to instance
        geometry. The geometry should be points or instances.

        Args:
            geometry: The geometry to transform (must be instances or points).
            matrices: List of 4x4 transformation matrices to apply.

        Returns:
            The transformed geometry (node reference for chaining).

        Note:
            This is a conceptual interface - actual implementation requires
            integration with NodeTreeBuilder for creating the node setup.

        Example:
            >>> # In a node tree context:
            >>> transformed = InstanceController.apply_transform_to_instances(
            ...     points_geometry,
            ...     [Matrix.Translation((i, 0, 0)) for i in range(10)]
            ... )
        """
        # This method is designed to work within a node tree context
        # In practice, you would use this with NodeTreeBuilder
        # Here we return the concept signature for API completeness
        raise NotImplementedError(
            "apply_transform_to_instances requires a NodeTreeBuilder context. "
            "Use NodeTreeBuilder to create instance transformation nodes."
        )

    @staticmethod
    def create_instance_on_points(
        points_geometry,
        instance_geometry,
        selection=None,
        pick_instance=None,
        instance_index=None,
        rotation=None,
        scale=None,
    ):
        """
        Create a node reference for Instance on Points operation.

        This is a helper for understanding the instance creation API.
        For actual node creation, use NodeTreeBuilder.add_node().

        Args:
            points_geometry: Point cloud or mesh with points.
            instance_geometry: Geometry to instance on each point.
            selection: Boolean field for which points to use (optional).
            pick_instance: Boolean for whether to pick specific instances (optional).
            instance_index: Integer field for which instance to pick (optional).
            rotation: Rotation field for each instance (optional).
            scale: Scale field for each instance (optional).

        Returns:
            Dictionary describing the Instance on Points operation.
        """
        return {
            "node_type": "GeometryNodeInstanceOnPoints",
            "inputs": {
                "Points": points_geometry,
                "Selection": selection,
                "Instance": instance_geometry,
                "Pick Instance": pick_instance,
                "Instance Index": instance_index,
                "Rotation": rotation,
                "Scale": scale,
            },
        }

    @staticmethod
    def realize_instances(geometry, depth: int = 0) -> None:
        """
        Realize instances as actual geometry data.

        Converts instances to real geometry that can be edited.
        This is typically done at the end of a geometry node tree.

        Args:
            geometry: The geometry containing instances.
            depth: Recursion depth for nested instances (0 = all levels).

        Note:
            For use within a node tree, add a "GeometryNodeRealizeInstances"
            node using NodeTreeBuilder.
        """
        # API completeness - actual implementation requires node tree context
        pass

    @staticmethod
    def count_instances(geometry) -> int:
        """
        Count the number of instances in geometry.

        Args:
            geometry: Geometry potentially containing instances.

        Returns:
            Number of instances, or 0 if none.
        """
        if hasattr(geometry, "instances"):
            return len(geometry.instances)
        return 0

    @staticmethod
    def set_instance_transform(
        instance_index: int,
        matrix: Matrix,
        geometry,
    ):
        """
        Set the transform matrix for a specific instance.

        Args:
            instance_index: Index of the instance to modify.
            matrix: The new 4x4 transformation matrix.
            geometry: The geometry containing instances.

        Note:
            This requires realized instances or direct geometry access.
            For geometry nodes, use Set Position or Transform nodes.
        """
        # Conceptual API - actual implementation varies by context
        pass


class InstanceExtractor:
    """
    Extract and analyze instance data from geometry.

    Provides methods for detailed instance analysis and extraction
    of instance properties like position, rotation, scale, and
    custom attributes.
    """

    def __init__(self, geometry):
        """
        Initialize the instance extractor.

        Args:
            geometry: The geometry to extract instances from.
        """
        self.geometry = geometry
        self._instances: Optional[list] = None

    @property
    def instances(self) -> list:
        """Get the list of instances, caching the result."""
        if self._instances is None:
            self._instances = self._extract_instances()
        return self._instances

    def _extract_instances(self) -> list:
        """Extract instances from the geometry."""
        instances = []
        if hasattr(self.geometry, "instances"):
            for inst in self.geometry.instances:
                instances.append(inst)
        return instances

    def get_positions(self) -> list[Vector]:
        """
        Get the position of each instance.

        Returns:
            List of position vectors.
        """
        positions = []
        for matrix in InstanceController.extract_transform_matrices(self.instances):
            positions.append(matrix.translation)
        return positions

    def get_rotations(self) -> list:
        """
        Get the rotation of each instance as Euler angles.

        Returns:
            List of Euler rotations.
        """
        rotations = []
        for matrix in InstanceController.extract_transform_matrices(self.instances):
            # Decompose matrix
            _, rot, _ = matrix.decompose()
            rotations.append(rot.to_euler())
        return rotations

    def get_scales(self) -> list[Vector]:
        """
        Get the scale of each instance.

        Returns:
            List of scale vectors.
        """
        scales = []
        for matrix in InstanceController.extract_transform_matrices(self.instances):
            _, _, scale = matrix.decompose()
            scales.append(scale)
        return scales

    def get_attribute(self, attribute_name: str) -> list:
        """
        Get a custom attribute from instances.

        Args:
            attribute_name: Name of the attribute to retrieve.

        Returns:
            List of attribute values for each instance.
        """
        values = []
        for inst in self.instances:
            if hasattr(inst, attribute_name):
                values.append(getattr(inst, attribute_name))
            elif hasattr(inst, "attributes") and attribute_name in inst.attributes:
                values.append(inst.attributes[attribute_name])
        return values

    def to_dict(self) -> dict:
        """
        Convert all instance data to a dictionary.

        Returns:
            Dictionary with positions, rotations, scales, and count.
        """
        matrices = InstanceController.extract_transform_matrices(self.instances)
        data = {
            "count": len(self.instances),
            "transforms": [],
        }

        for i, matrix in enumerate(matrices):
            loc, rot, scale = matrix.decompose()
            data["transforms"].append(
                {
                    "index": i,
                    "position": tuple(loc),
                    "rotation": tuple(rot.to_euler()),
                    "scale": tuple(scale),
                    "matrix": [list(row) for row in matrix],
                }
            )

        return data
