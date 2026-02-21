"""
SDF Modeling in Geometry Nodes for Blender 5.0+.

Blender 5.0 introduced Signed Distance Field (SDF) modeling in Geometry Nodes,
enabling boolean operations with smooth blending, morphing, and procedural
modeling workflows.

Example:
    >>> from lib.blender5x.geometry_nodes import SDFModeling
    >>> sdf = SDFModeling.mesh_to_sdf(mesh, voxel_size=0.01)
    >>> result = SDFModeling.boolean_union(sdf_a, sdf_b)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Object, NodeTree


class SDFBlendMode(Enum):
    """SDF blending modes."""

    UNION = "union"
    """Additive union (A + B)."""

    INTERSECTION = "intersection"
    """Intersection (A AND B)."""

    DIFFERENCE = "difference"
    """Subtraction (A - B)."""

    SMOOTH_UNION = "smooth_union"
    """Smooth union with blending."""

    SMOOTH_INTERSECTION = "smooth_intersection"
    """Smooth intersection with blending."""

    SMOOTH_DIFFERENCE = "smooth_difference"
    """Smooth subtraction with blending."""

    CHAMFER = "chamfer"
    """Chamfered union."""

    ROUND = "round"
    """Rounded union."""

    STEPS = "steps"
    """Stepped union (terrace effect)."""


@dataclass
class SDFInfo:
    """Information about an SDF volume."""

    name: str
    """SDF volume name."""

    voxel_size: float
    """Voxel size used for SDF generation."""

    half_band: float
    """Half-band width in voxels."""

    resolution: tuple[int, int, int]
    """Approximate grid resolution."""

    bounds: tuple[tuple[float, float, float], tuple[float, float, float]]
    """Bounding box."""


class SDFModeling:
    """
    Signed Distance Field modeling utilities (Blender 5.0+).

    Provides tools for converting meshes to SDF, performing boolean
    operations with smooth blending, and converting SDF back to mesh.

    Example:
        >>> sdf_a = SDFModeling.mesh_to_sdf(sphere, voxel_size=0.01)
        >>> sdf_b = SDFModeling.mesh_to_sdf(cube, voxel_size=0.01)
        >>> blended = SDFModeling.smooth_union(sdf_a, sdf_b, smoothness=0.1)
        >>> result_mesh = SDFModeling.sdf_to_mesh(blended)
    """

    @staticmethod
    def mesh_to_sdf(
        mesh: Object | str,
        voxel_size: float = 0.01,
        half_band: float = 3.0,
        output_name: str | None = None,
    ) -> str:
        """
        Convert mesh to Signed Distance Field volume.

        Args:
            mesh: Mesh object or name.
            voxel_size: Voxel size for SDF grid.
            half_band: Half-band width in voxels (narrow band level set).
            output_name: Name for output volume object.

        Returns:
            Name of the created SDF volume object.

        Example:
            >>> sdf = SDFModeling.mesh_to_sdf(
            ...     "Sphere",
            ...     voxel_size=0.005,
            ...     half_band=3.0,
            ... )
        """
        import bpy

        # Get mesh object
        if isinstance(mesh, str):
            mesh_obj = bpy.data.objects.get(mesh)
            if mesh_obj is None:
                raise ValueError(f"Mesh object not found: {mesh}")
        else:
            mesh_obj = mesh

        output_name = output_name or f"{mesh_obj.name}_SDF"

        # Create volume object
        volume_data = bpy.data.volumes.new(output_name)
        volume_obj = bpy.data.objects.new(output_name, volume_data)
        bpy.context.collection.objects.link(volume_obj)

        # Create Geometry Nodes tree for mesh to SDF
        tree_name = f"GN_MeshToSDF_{output_name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        output_node = tree.nodes.new("NodeGroupOutput")

        # Mesh to SDF node (Blender 5.0+)
        mesh_to_sdf = tree.nodes.new("GeometryNodeMeshToSDFVolume")
        mesh_to_sdf.voxel_size = voxel_size
        mesh_to_sdf.half_band = half_band

        # Object Info for source mesh
        obj_info = tree.nodes.new("GeometryNodeObjectInfo")
        obj_info.inputs[0].default_value = mesh_obj
        obj_info.transform_space = "RELATIVE"

        # Realize instances (in case mesh is instanced)
        realize = tree.nodes.new("GeometryNodeRealizeInstances")

        # Link nodes
        tree.links.new(obj_info.outputs["Geometry"], realize.inputs["Geometry"])
        tree.links.new(realize.outputs["Geometry"], mesh_to_sdf.inputs["Mesh"])
        tree.links.new(mesh_to_sdf.outputs["SDF"], output_node.inputs["Geometry"])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = volume_obj.modifiers.new("GeometryNodes", "NODES")
        mod.node_group = tree

        return volume_obj.name

    @staticmethod
    def sdf_to_mesh(
        sdf: Object | str,
        iso_level: float = 0.0,
        adaptivity: float = 0.0,
        voxel_size: float = 0.01,
        output_name: str | None = None,
    ) -> str:
        """
        Convert SDF volume back to mesh using marching cubes.

        Args:
            sdf: SDF volume object or name.
            iso_level: Iso-surface level (0.0 = exact surface).
            adaptivity: Mesh simplification adaptivity (0.0-1.0).
            voxel_size: Voxel size for meshing (if different from SDF).
            output_name: Name for output mesh object.

        Returns:
            Name of the created mesh object.

        Example:
            >>> mesh = SDFModeling.sdf_to_mesh(
            ...     "Sphere_SDF",
            ...     iso_level=0.0,
            ...     adaptivity=0.3,
            ... )
        """
        import bpy

        # Get SDF object
        if isinstance(sdf, str):
            sdf_obj = bpy.data.objects.get(sdf)
            if sdf_obj is None:
                raise ValueError(f"SDF object not found: {sdf}")
        else:
            sdf_obj = sdf

        output_name = output_name or f"{sdf_obj.name}_Mesh"

        # Create mesh object
        mesh_data = bpy.data.meshes.new(output_name)
        mesh_obj = bpy.data.objects.new(output_name, mesh_data)
        bpy.context.collection.objects.link(mesh_obj)

        # Create Geometry Nodes tree
        tree_name = f"GN_SDFToMesh_{output_name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        output_node = tree.nodes.new("NodeGroupOutput")

        # Volume to Mesh node
        vol_to_mesh = tree.nodes.new("GeometryNodeVolumeToMesh")
        vol_to_mesh.voxel_size = voxel_size
        vol_to_mesh.adaptivity = adaptivity
        vol_to_mesh.iso_level = iso_level
        vol_to_mesh.grid_name = "distance"  # SDF grid name

        # Object Info for source SDF
        obj_info = tree.nodes.new("GeometryNodeObjectInfo")
        obj_info.inputs[0].default_value = sdf_obj
        obj_info.transform_space = "RELATIVE"

        # Link nodes
        tree.links.new(obj_info.outputs["Geometry"], vol_to_mesh.inputs["Volume"])
        tree.links.new(vol_to_mesh.outputs["Mesh"], output_node.inputs["Geometry"])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = mesh_obj.modifiers.new("GeometryNodes", "NODES")
        mod.node_group = tree

        return mesh_obj.name

    @staticmethod
    def boolean_union(
        sdf_a: Object | str,
        sdf_b: Object | str,
        output_name: str | None = None,
    ) -> str:
        """
        Perform boolean union on two SDF volumes.

        Args:
            sdf_a: First SDF volume.
            sdf_b: Second SDF volume.
            output_name: Name for output volume.

        Returns:
            Name of the created SDF volume.

        Example:
            >>> result = SDFModeling.boolean_union("Sphere_SDF", "Cube_SDF")
        """
        return SDFModeling._sdf_boolean(
            sdf_a, sdf_b, SDFBlendMode.UNION, 0.0, output_name
        )

    @staticmethod
    def boolean_difference(
        sdf_a: Object | str,
        sdf_b: Object | str,
        output_name: str | None = None,
    ) -> str:
        """
        Perform boolean difference (subtraction) on two SDF volumes.

        Args:
            sdf_a: First SDF volume (base).
            sdf_b: Second SDF volume (subtractor).
            output_name: Name for output volume.

        Returns:
            Name of the created SDF volume.

        Example:
            >>> result = SDFModeling.boolean_difference("Cube_SDF", "Sphere_SDF")
        """
        return SDFModeling._sdf_boolean(
            sdf_a, sdf_b, SDFBlendMode.DIFFERENCE, 0.0, output_name
        )

    @staticmethod
    def boolean_intersection(
        sdf_a: Object | str,
        sdf_b: Object | str,
        output_name: str | None = None,
    ) -> str:
        """
        Perform boolean intersection on two SDF volumes.

        Args:
            sdf_a: First SDF volume.
            sdf_b: Second SDF volume.
            output_name: Name for output volume.

        Returns:
            Name of the created SDF volume.

        Example:
            >>> result = SDFModeling.boolean_intersection("Sphere_SDF", "Cube_SDF")
        """
        return SDFModeling._sdf_boolean(
            sdf_a, sdf_b, SDFBlendMode.INTERSECTION, 0.0, output_name
        )

    @staticmethod
    def smooth_union(
        sdf_a: Object | str,
        sdf_b: Object | str,
        smoothness: float = 0.1,
        output_name: str | None = None,
    ) -> str:
        """
        Perform smooth boolean union with blending.

        Args:
            sdf_a: First SDF volume.
            sdf_b: Second SDF volume.
            smoothness: Blend smoothness factor.
            output_name: Name for output volume.

        Returns:
            Name of the created SDF volume.

        Example:
            >>> result = SDFModeling.smooth_union(
            ...     "Sphere_SDF",
            ...     "Cube_SDF",
            ...     smoothness=0.2,
            ... )
        """
        return SDFModeling._sdf_boolean(
            sdf_a, sdf_b, SDFBlendMode.SMOOTH_UNION, smoothness, output_name
        )

    @staticmethod
    def dilate(
        sdf: Object | str,
        amount: float,
        output_name: str | None = None,
    ) -> str:
        """
        Dilate (expand) an SDF volume.

        Args:
            sdf: SDF volume to dilate.
            amount: Amount to expand (positive expands).
            output_name: Name for output volume.

        Returns:
            Name of the created SDF volume.

        Example:
            >>> expanded = SDFModeling.dilate("Sphere_SDF", amount=0.1)
        """
        import bpy

        # Get SDF object
        if isinstance(sdf, str):
            sdf_obj = bpy.data.objects.get(sdf)
            if sdf_obj is None:
                raise ValueError(f"SDF object not found: {sdf}")
        else:
            sdf_obj = sdf

        output_name = output_name or f"{sdf_obj.name}_Dilated"

        # Create volume object
        volume_data = bpy.data.volumes.new(output_name)
        volume_obj = bpy.data.objects.new(output_name, volume_data)
        bpy.context.collection.objects.link(volume_obj)

        # Create Geometry Nodes tree
        tree_name = f"GN_SDFDilate_{output_name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        output_node = tree.nodes.new("NodeGroupOutput")

        # SDF Offset node (Blender 5.0+)
        sdf_offset = tree.nodes.new("GeometryNodeSDFVolumeOffset")
        sdf_offset.inputs["Distance"].default_value = amount

        # Object Info for source
        obj_info = tree.nodes.new("GeometryNodeObjectInfo")
        obj_info.inputs[0].default_value = sdf_obj
        obj_info.transform_space = "RELATIVE"

        # Link nodes
        tree.links.new(obj_info.outputs["Geometry"], sdf_offset.inputs["SDF"])
        tree.links.new(sdf_offset.outputs["SDF"], output_node.inputs["Geometry"])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = volume_obj.modifiers.new("GeometryNodes", "NODES")
        mod.node_group = tree

        return volume_obj.name

    @staticmethod
    def erode(
        sdf: Object | str,
        amount: float,
        output_name: str | None = None,
    ) -> str:
        """
        Erode (shrink) an SDF volume.

        Args:
            sdf: SDF volume to erode.
            amount: Amount to shrink (positive shrinks).
            output_name: Name for output volume.

        Returns:
            Name of the created SDF volume.

        Example:
            >>> shrunk = SDFModeling.erode("Sphere_SDF", amount=0.05)
        """
        # Erosion is negative dilation
        return SDFModeling.dilate(sdf, -amount, output_name or f"{sdf}_Eroded")

    @staticmethod
    def blend_shapes(
        shapes: list[Object | str],
        weights: list[float],
        smoothness: float = 0.1,
        output_name: str = "BlendedShape",
    ) -> str:
        """
        Blend multiple SDF shapes with weighted interpolation.

        Args:
            shapes: List of SDF volumes to blend.
            weights: Corresponding blend weights (0.0-1.0).
            smoothness: Global blend smoothness.
            output_name: Name for output volume.

        Returns:
            Name of the created SDF volume.

        Example:
            >>> result = SDFModeling.blend_shapes(
            ...     shapes=["Sphere_SDF", "Cube_SDF", "Cylinder_SDF"],
            ...     weights=[0.5, 0.3, 0.2],
            ...     smoothness=0.15,
            ... )
        """
        import bpy

        if len(shapes) != len(weights):
            raise ValueError("Number of shapes must match number of weights")

        # Get shape objects
        shape_objs = []
        for shape in shapes:
            if isinstance(shape, str):
                obj = bpy.data.objects.get(shape)
                if obj is None:
                    raise ValueError(f"Shape object not found: {shape}")
                shape_objs.append(obj)
            else:
                shape_objs.append(shape)

        # Create volume object
        volume_data = bpy.data.volumes.new(output_name)
        volume_obj = bpy.data.objects.new(output_name, volume_data)
        bpy.context.collection.objects.link(volume_obj)

        # Create Geometry Nodes tree
        tree_name = f"GN_SDFBlend_{output_name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        output_node = tree.nodes.new("NodeGroupOutput")

        # Start with first shape
        prev_result = None

        for i, (shape_obj, weight) in enumerate(zip(shape_objs, weights)):
            # Object Info for shape
            obj_info = tree.nodes.new("GeometryNodeObjectInfo")
            obj_info.inputs[0].default_value = shape_obj
            obj_info.transform_space = "RELATIVE"

            if prev_result is None:
                prev_result = obj_info.outputs["Geometry"]
            else:
                # SDF Smooth Boolean
                smooth_bool = tree.nodes.new("GeometryNodeSDFVolumeSmoothBoolean")
                smooth_bool.operation = "UNION"
                smooth_bool.inputs["Smoothness"].default_value = smoothness * weight

                # Link
                tree.links.new(prev_result, smooth_bool.inputs["SDF A"])
                tree.links.new(obj_info.outputs["Geometry"], smooth_bool.inputs["SDF B"])

                prev_result = smooth_bool.outputs["SDF"]

        # Link final result
        tree.links.new(prev_result, output_node.inputs["Geometry"])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = volume_obj.modifiers.new("GeometryNodes", "NODES")
        mod.node_group = tree

        return volume_obj.name

    @staticmethod
    def _sdf_boolean(
        sdf_a: Object | str,
        sdf_b: Object | str,
        mode: SDFBlendMode,
        smoothness: float,
        output_name: str | None,
    ) -> str:
        """Internal method for SDF boolean operations."""
        import bpy

        # Get SDF objects
        if isinstance(sdf_a, str):
            sdf_a_obj = bpy.data.objects.get(sdf_a)
            if sdf_a_obj is None:
                raise ValueError(f"SDF object not found: {sdf_a}")
        else:
            sdf_a_obj = sdf_a

        if isinstance(sdf_b, str):
            sdf_b_obj = bpy.data.objects.get(sdf_b)
            if sdf_b_obj is None:
                raise ValueError(f"SDF object not found: {sdf_b}")
        else:
            sdf_b_obj = sdf_b

        output_name = output_name or f"{sdf_a_obj.name}_Boolean"

        # Create volume object
        volume_data = bpy.data.volumes.new(output_name)
        volume_obj = bpy.data.objects.new(output_name, volume_data)
        bpy.context.collection.objects.link(volume_obj)

        # Create Geometry Nodes tree
        tree_name = f"GN_SDFBoolean_{output_name}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

        # Add nodes
        output_node = tree.nodes.new("NodeGroupOutput")

        # Object Info nodes
        obj_info_a = tree.nodes.new("GeometryNodeObjectInfo")
        obj_info_a.inputs[0].default_value = sdf_a_obj
        obj_info_a.transform_space = "RELATIVE"

        obj_info_b = tree.nodes.new("GeometryNodeObjectInfo")
        obj_info_b.inputs[0].default_value = sdf_b_obj
        obj_info_b.transform_space = "RELATIVE"

        # SDF Boolean node
        if mode in (SDFBlendMode.SMOOTH_UNION, SDFBlendMode.SMOOTH_INTERSECTION, SDFBlendMode.SMOOTH_DIFFERENCE):
            sdf_bool = tree.nodes.new("GeometryNodeSDFVolumeSmoothBoolean")
            sdf_bool.inputs["Smoothness"].default_value = smoothness

            if mode == SDFBlendMode.SMOOTH_UNION:
                sdf_bool.operation = "UNION"
            elif mode == SDFBlendMode.SMOOTH_INTERSECTION:
                sdf_bool.operation = "INTERSECT"
            else:
                sdf_bool.operation = "DIFFERENCE"
        else:
            sdf_bool = tree.nodes.new("GeometryNodeSDFVolumeBoolean")

            if mode == SDFBlendMode.UNION:
                sdf_bool.operation = "UNION"
            elif mode == SDFBlendMode.INTERSECTION:
                sdf_bool.operation = "INTERSECT"
            else:
                sdf_bool.operation = "DIFFERENCE"

        # Link nodes
        tree.links.new(obj_info_a.outputs["Geometry"], sdf_bool.inputs["SDF A"])
        tree.links.new(obj_info_b.outputs["Geometry"], sdf_bool.inputs["SDF B"])
        tree.links.new(sdf_bool.outputs["SDF"], output_node.inputs["Geometry"])

        # Create interface
        tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        # Add modifier
        mod = volume_obj.modifiers.new("GeometryNodes", "NODES")
        mod.node_group = tree

        return volume_obj.name


# Convenience exports
__all__ = [
    "SDFModeling",
    "SDFBlendMode",
    "SDFInfo",
]
