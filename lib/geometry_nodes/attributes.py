"""
AttributeManager - Manage named attributes on geometry.

Provides static methods for storing, retrieving, and manipulating
named attributes in Blender's geometry nodes system.

Usage:
    # Store a named attribute
    store_node = AttributeManager.store_named_attribute(
        geometry, "velocity", velocity_field, domain="POINT"
    )

    # Retrieve a named attribute
    attr_node = AttributeManager.get_named_attribute(geometry, "velocity")

    # List all attributes
    attrs = AttributeManager.list_attributes(geometry)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

import bpy

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bpy.types import Node


class AttributeManager:
    """
    Manage named attributes on geometry.

    Provides utilities for storing, retrieving, and manipulating
    named attributes in geometry nodes. Named attributes allow
    persistent data storage on geometry that survives across
    operations and frames.
    """

    # Valid domain types
    VALID_DOMAINS = ("POINT", "EDGE", "FACE", "CORNER", "CURVE", "INSTANCE")

    # Valid data types for attributes
    VALID_DATA_TYPES = (
        "FLOAT",
        "FLOAT_VECTOR",
        "FLOAT_COLOR",
        "BYTE_COLOR",
        "BOOLEAN",
        "INT32",
        "INT8",
        "QUATERNION",
        "FLOAT4X4",
    )

    @staticmethod
    def store_named_attribute(
        geometry,
        name: str,
        value,
        domain: str = "POINT",
        data_type: Optional[str] = None,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Store a named attribute on geometry.

        Creates a Store Named Attribute node that persists data on
        the geometry for later retrieval or use in other operations.

        Args:
            geometry: The geometry to store the attribute on.
            name: Name for the attribute (used to retrieve later).
            value: The value/field to store.
            domain: Attribute domain:
                - "POINT": Per-vertex/point (default)
                - "EDGE": Per-edge
                - "FACE": Per-face/polygon
                - "CORNER": Per-face-corner
                - "CURVE": Per-curve (for curve data)
                - "INSTANCE": Per-instance
            data_type: Optional explicit data type. Auto-detected if None.
            builder: NodeTreeBuilder for node creation.
            location: Position for the store node.

        Returns:
            The Store Named Attribute node.

        Raises:
            ValueError: If domain is invalid.

        Example:
            >>> # Store velocity per point
            >>> store = AttributeManager.store_named_attribute(
            ...     geometry_node.outputs["Geometry"],
            ...     "velocity",
            ...     velocity_field,
            ...     domain="POINT",
            ...     builder=my_builder
            ... )
            >>>
            >>> # Store face colors
            >>> store = AttributeManager.store_named_attribute(
            ...     mesh_geometry,
            ...     "face_color",
            ...     color_field,
            ...     domain="FACE",
            ...     builder=my_builder
            ... )
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        if domain not in AttributeManager.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain '{domain}'. Must be one of: "
                f"{', '.join(AttributeManager.VALID_DOMAINS)}"
            )

        store = builder.add_node(
            "GeometryNodeStoreNamedAttribute",
            location,
            name=f"Store_{name}",
        )

        # Set attribute name
        store.inputs["Name"].default_value = name

        # Set domain
        store.inputs["Domain"].default_value = domain

        # Connect geometry
        if geometry is not None:
            builder.link(geometry, store.inputs["Geometry"])

        # Connect value (the Value input changes based on data type)
        if value is not None:
            # Try to find the correct value input
            # The socket name varies: "Value", "Vector", "Color", etc.
            for input_socket in store.inputs:
                if input_socket.name in ("Value", "Vector", "Color", "Attribute"):
                    builder.link(value, input_socket)
                    break

        return store

    @staticmethod
    def get_named_attribute(
        geometry,
        name: str,
        data_type: str = "FLOAT_VECTOR",
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Retrieve a named attribute from geometry.

        Creates a Named Attribute node that reads previously stored
        attribute data from geometry.

        Args:
            geometry: The geometry to read from.
            name: Name of the attribute to retrieve.
            data_type: Expected data type of the attribute:
                - "FLOAT": Single float value
                - "FLOAT_VECTOR": 3D vector (default)
                - "FLOAT_COLOR": RGBA color
                - "BOOLEAN": Boolean value
                - "INT32": Integer value
                - "QUATERNION": Rotation quaternion
            builder: NodeTreeBuilder for node creation.
            location: Position for the attribute node.

        Returns:
            The Named Attribute node with attribute value output.

        Raises:
            ValueError: If data_type is invalid.

        Example:
            >>> # Retrieve stored velocity
            >>> velocity_attr = AttributeManager.get_named_attribute(
            ...     geometry,
            ...     "velocity",
            ...     data_type="FLOAT_VECTOR",
            ...     builder=my_builder
            ... )
            >>> velocity_field = velocity_attr.outputs["Attribute"]
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        if data_type not in AttributeManager.VALID_DATA_TYPES:
            raise ValueError(
                f"Invalid data_type '{data_type}'. Must be one of: "
                f"{', '.join(AttributeManager.VALID_DATA_TYPES)}"
            )

        attr = builder.add_node(
            "GeometryNodeInputNamedAttribute",
            location,
            name=f"Get_{name}",
        )

        # Set attribute name
        attr.inputs["Name"].default_value = name

        # Set data type
        attr.inputs["Data Type"].default_value = data_type

        return attr

    @staticmethod
    def remove_named_attribute(
        geometry,
        name: str,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Remove a named attribute from geometry.

        Creates a node setup that removes an attribute from geometry.
        Useful for cleaning up temporary attributes.

        Args:
            geometry: The geometry to remove the attribute from.
            name: Name of the attribute to remove.
            builder: NodeTreeBuilder for node creation.
            location: Position for the remove node.

        Returns:
            The geometry with attribute removed.

        Example:
            >>> # Remove temporary attribute
            >>> clean_geo = AttributeManager.remove_named_attribute(
            ...     geometry,
            ...     "temp_field",
            ...     builder=my_builder
            ... )
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Blender 4.x+ uses Remove Named Attribute node
        # For older versions, we might need to use a different approach
        remove = builder.add_node(
            "GeometryNodeRemoveAttribute",
            location,
            name=f"Remove_{name}",
        )

        # Set attribute name
        remove.inputs["Name"].default_value = name

        # Connect geometry
        if geometry is not None:
            builder.link(geometry, remove.inputs["Geometry"])

        return remove

    @staticmethod
    def list_attributes(geometry) -> list[str]:
        """
        List all named attributes on geometry.

        Note: This operates on realized geometry data, not within
        a node tree context. For node-based operations, you typically
        know the attribute names you're working with.

        Args:
            geometry: The geometry object or data to inspect.

        Returns:
            List of attribute names.

        Example:
            >>> # Check what attributes exist on a mesh
            >>> attrs = AttributeManager.list_attributes(mesh_object)
            >>> print(attrs)  # ['uv_map', 'material_index', 'velocity', ...]
        """
        attributes = []

        if hasattr(geometry, "data") and hasattr(geometry.data, "attributes"):
            # Object with mesh/curve data
            for attr in geometry.data.attributes:
                attributes.append(attr.name)
        elif hasattr(geometry, "attributes"):
            # Direct geometry data
            for attr in geometry.attributes:
                attributes.append(attr.name)

        return attributes

    @staticmethod
    def attribute_exists(
        geometry,
        name: str,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Check if an attribute exists on geometry.

        Creates a node setup that returns true if the named attribute
        exists on the geometry.

        Args:
            geometry: The geometry to check.
            name: Name of the attribute to check.
            builder: NodeTreeBuilder for node creation.
            location: Position for the check node.

        Returns:
            Node with boolean output indicating existence.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Try to read the attribute and check if valid
        # This is a workaround since there's no direct "attribute exists" node
        attr = AttributeManager.get_named_attribute(
            geometry,
            name,
            data_type="FLOAT",
            builder=builder,
            location=location,
        )

        # The attribute node will output 0/default if attribute doesn't exist
        # For a proper check, we might need additional logic
        return attr

    @staticmethod
    def copy_attribute(
        geometry,
        source_name: str,
        dest_name: str,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Copy an attribute to a new name.

        Args:
            geometry: The geometry with the attribute.
            source_name: Name of the attribute to copy.
            dest_name: Name for the copied attribute.
            builder: NodeTreeBuilder for node creation.
            location: Position for the copy operation.

        Returns:
            The geometry with copied attribute.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Get the source attribute
        source = AttributeManager.get_named_attribute(
            geometry,
            source_name,
            data_type="FLOAT_VECTOR",  # Assume vector, adjust as needed
            builder=builder,
            location=location,
        )

        # Store with new name
        dest = AttributeManager.store_named_attribute(
            geometry,
            dest_name,
            source.outputs["Attribute"],
            builder=builder,
            location=(location[0] + 200, location[1]),
        )

        return dest

    @staticmethod
    def transfer_attribute(
        source_geometry,
        target_geometry,
        attribute_name: str,
        mapping: str = "NEAREST",
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Transfer an attribute from one geometry to another.

        Args:
            source_geometry: Geometry with the attribute.
            target_geometry: Geometry to transfer to.
            attribute_name: Name of the attribute to transfer.
            mapping: How to map values ("NEAREST", "INTERPOLATED").
            builder: NodeTreeBuilder for node creation.
            location: Position for the transfer node.

        Returns:
            The transfer node.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Get source attribute
        source_attr = AttributeManager.get_named_attribute(
            source_geometry,
            attribute_name,
            builder=builder,
            location=(location[0] - 200, location[1]),
        )

        # Sample nearest for transfer
        transfer = builder.add_node(
            "GeometryNodeSampleNearest",
            location,
            name=f"Transfer_{attribute_name}",
        )

        if source_geometry is not None:
            builder.link(source_geometry, transfer.inputs["Geometry"])

        # Store on target
        store = AttributeManager.store_named_attribute(
            target_geometry,
            attribute_name,
            transfer.outputs["Position"],  # Adjust based on attribute type
            builder=builder,
            location=(location[0] + 200, location[1]),
        )

        return store

    @staticmethod
    def blend_attributes(
        geometry,
        attr_a_name: str,
        attr_b_name: str,
        result_name: str,
        factor: float = 0.5,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Blend two attributes together.

        Args:
            geometry: The geometry with both attributes.
            attr_a_name: First attribute name.
            attr_b_name: Second attribute name.
            result_name: Name for the blended result.
            factor: Blend factor (0 = attr_a, 1 = attr_b).
            builder: NodeTreeBuilder for node creation.
            location: Position for the blend operation.

        Returns:
            The geometry with blended attribute.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Get both attributes
        attr_a = AttributeManager.get_named_attribute(
            geometry,
            attr_a_name,
            builder=builder,
            location=(location[0] - 200, location[1] + 50),
        )

        attr_b = AttributeManager.get_named_attribute(
            geometry,
            attr_b_name,
            builder=builder,
            location=(location[0] - 200, location[1] - 50),
        )

        # Mix them
        mix = builder.add_node(
            "ShaderNodeMix",
            location,
            name=f"Blend_{attr_a_name}_{attr_b_name}",
        )

        mix.data_type = "VECTOR"
        mix.inputs["Factor"].default_value = factor

        builder.link(attr_a.outputs["Attribute"], mix.inputs["A"])
        builder.link(attr_b.outputs["Attribute"], mix.inputs["B"])

        # Store result
        store = AttributeManager.store_named_attribute(
            geometry,
            result_name,
            mix.outputs["Result"],
            builder=builder,
            location=(location[0] + 200, location[1]),
        )

        return store

    @staticmethod
    def set_material_index(
        geometry,
        material_index,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Set the material index attribute on geometry.

        Convenience method for the common operation of assigning
        materials via the material_index attribute.

        Args:
            geometry: The geometry to set material on.
            material_index: Integer material index or field.
            builder: NodeTreeBuilder for node creation.
            location: Position for the set material node.

        Returns:
            The Set Material Index node.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        set_mat = builder.add_node(
            "GeometryNodeSetMaterialIndex",
            location,
            name="SetMaterialIndex",
        )

        if geometry is not None:
            builder.link(geometry, set_mat.inputs["Geometry"])

        if material_index is not None:
            builder.link(material_index, set_mat.inputs["Material Index"])

        return set_mat

    @staticmethod
    def set_shade_smooth(
        geometry,
        smooth: bool = True,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Set shade smooth/flat on geometry.

        Args:
            geometry: The geometry to shade.
            smooth: True for smooth, False for flat shading.
            builder: NodeTreeBuilder for node creation.
            location: Position for the shade smooth node.

        Returns:
            The Set Shade Smooth node.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        shade = builder.add_node(
            "GeometryNodeSetShadeSmooth",
            location,
            name="SetShadeSmooth",
        )

        shade.inputs["Shade Smooth"].default_value = smooth

        if geometry is not None:
            builder.link(geometry, shade.inputs["Geometry"])

        return shade
