"""
FieldOperations - Common field operations in geometry nodes.

Provides static methods for field evaluation, accumulation,
sampling, and ray casting operations that work with Blender's
geometry nodes field system.

Usage:
    # Accumulate values across geometry
    accumulated = FieldOperations.accumulate_field(distance_field, group_id=face_id)

    # Sample nearest point
    nearest_value = FieldOperations.sample_nearest(source_geo, sample_pos)

    # Ray cast for collision detection
    hit = FieldOperations.ray_cast(target_geo, ray_origin, ray_dir)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

import bpy
from mathutils import Vector

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bpy.types import Node


class FieldOperations:
    """
    Common field operations in geometry nodes.

    Provides utility methods for working with fields in geometry nodes,
    including accumulation, evaluation, sampling, and ray casting.

    All methods return node references that can be used within a
    NodeTreeBuilder context.
    """

    @staticmethod
    def accumulate_field(
        field,
        group_id=None,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Accumulate field values across geometry.

        Creates an accumulation that sums up field values element by
        element. When grouped, accumulates within each group separately.

        Args:
            field: The field to accumulate (node output or field reference).
            group_id: Optional group identifier field for grouped accumulation.
            builder: Optional NodeTreeBuilder for node creation.
            location: Position for the accumulation node.

        Returns:
            The Accumulate Field node.

        Example:
            >>> # Accumulate distance along a curve
            >>> accumulated = FieldOperations.accumulate_field(
            ...     distance_field,
            ...     builder=my_builder
            ... )
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        accumulate = builder.add_node(
            "GeometryNodeAccumulateField",
            location,
            name="Accumulate",
        )

        # Connect the field to accumulate
        if field is not None:
            builder.link(field, accumulate.inputs["Value"])

        # Set group ID if provided
        if group_id is not None:
            builder.link(group_id, accumulate.inputs["Group Index"])

        return accumulate

    @staticmethod
    def evaluate_at_positions(
        field,
        positions,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Evaluate a field at specific positions.

        Samples a field's values at arbitrary world positions, rather
        than at the geometry's point locations.

        Args:
            field: The field to evaluate.
            positions: Position vector(s) to sample at.
            builder: NodeTreeBuilder for node creation.
            location: Position for the evaluation node.

        Returns:
            The Evaluate at Positions node (or equivalent setup).

        Example:
            >>> # Sample a noise field at custom positions
            >>> values = FieldOperations.evaluate_at_positions(
            ...     noise_field,
            ...     custom_positions,
            ...     builder=my_builder
            ... )
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Use Sample Index for field evaluation at positions
        # The position influences which element we sample
        sample_index = builder.add_node(
            "GeometryNodeSampleIndex",
            location,
            name="EvaluateAtPositions",
        )

        # Connect positions
        if positions is not None:
            builder.link(positions, sample_index.inputs["Position"])

        # Connect field to sample
        if field is not None:
            builder.link(field, sample_index.inputs["Value"])

        return sample_index

    @staticmethod
    def sample_nearest(
        geometry,
        sample_position,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Sample the nearest point on geometry.

        Finds the closest point on the target geometry to a given
        sample position and returns information about it.

        Args:
            geometry: The geometry to sample from.
            sample_position: World position to find nearest point to.
            builder: NodeTreeBuilder for node creation.
            location: Position for the sample node.

        Returns:
            The Sample Nearest node.

        Example:
            >>> # Find nearest point on surface
            >>> nearest = FieldOperations.sample_nearest(
            ...     surface_geometry,
            ...     query_position,
            ...     builder=my_builder
            ... )
            >>> # Access: nearest.outputs["Position"], nearest.outputs["Distance"]
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        sample = builder.add_node(
            "GeometryNodeSampleNearest",
            location,
            name="SampleNearest",
        )

        # Connect geometry
        if geometry is not None:
            builder.link(geometry, sample.inputs["Geometry"])

        # Connect sample position
        if sample_position is not None:
            builder.link(sample_position, sample.inputs["Sample Position"])

        return sample

    @staticmethod
    def ray_cast(
        geometry,
        source_position,
        ray_direction,
        max_distance: float = 100.0,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Cast a ray against geometry for intersection testing.

        Performs ray casting from a source position in a given direction
        to find intersections with geometry. Useful for collision detection,
        visibility queries, and procedural placement.

        Args:
            geometry: The geometry to cast against.
            source_position: Starting point of the ray.
            ray_direction: Direction vector of the ray.
            max_distance: Maximum distance to cast (default 100.0).
            builder: NodeTreeBuilder for node creation.
            location: Position for the ray cast node.

        Returns:
            The Ray Cast node with outputs:
            - "Is Hit": Boolean whether ray hit geometry
            - "Hit Position": World position of hit point
            - "Hit Normal": Normal at hit point
            - "Hit Distance": Distance from source to hit
            - "Attribute": Sampled attribute value at hit

        Example:
            >>> # Check for ground collision
            >>> ray = FieldOperations.ray_cast(
            ...     ground_geometry,
            ...     particle_position,
            ...     Vector((0, 0, -1)),  # Downward ray
            ...     max_distance=10.0,
            ...     builder=my_builder
            ... )
            >>> # Access hit info
            >>> is_hit = ray.outputs["Is Hit"]
            >>> hit_pos = ray.outputs["Hit Position"]
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        raycast = builder.add_node(
            "GeometryNodeRaycast",
            location,
            name="RayCast",
        )

        # Set max distance
        raycast.inputs["Ray Length"].default_value = max_distance

        # Connect geometry
        if geometry is not None:
            builder.link(geometry, raycast.inputs["Target Geometry"])

        # Connect source position
        if source_position is not None:
            builder.link(source_position, raycast.inputs["Source Position"])

        # Connect ray direction
        if ray_direction is not None:
            builder.link(ray_direction, raycast.inputs["Ray Direction"])

        return raycast

    @staticmethod
    def sample_surface(
        geometry,
        value_field,
        sample_position,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Sample a value on a surface at a given position.

        Interpolates a field value on mesh surface geometry at
        arbitrary positions.

        Args:
            geometry: Surface geometry to sample.
            value_field: Field to sample from the surface.
            sample_position: Position to sample at.
            builder: NodeTreeBuilder for node creation.
            location: Position for the sample node.

        Returns:
            The Sample Surface node.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        sample = builder.add_node(
            "GeometryNodeSampleNearestSurface",
            location,
            name="SampleSurface",
        )

        # Connect geometry
        if geometry is not None:
            builder.link(geometry, sample.inputs["Geometry"])

        # Connect sample position
        if sample_position is not None:
            builder.link(sample_position, sample.inputs["Sample Position"])

        # Connect value field
        if value_field is not None:
            builder.link(value_field, sample.inputs["Value"])

        return sample

    @staticmethod
    def evaluate_field(
        value_field,
        geometry=None,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Evaluate a field on geometry.

        Creates an evaluator that computes field values on the
        provided geometry.

        Args:
            value_field: The field to evaluate.
            geometry: Geometry to evaluate on (uses input if None).
            builder: NodeTreeBuilder for node creation.
            location: Position for the evaluation node.

        Returns:
            Node setup for field evaluation.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Field evaluation happens implicitly in geometry nodes
        # We can use Store Named Attribute to evaluate and store
        store = builder.add_node(
            "GeometryNodeStoreNamedAttribute",
            location,
            name="EvaluateField",
        )

        store.inputs["Name"].default_value = "evaluated_field"

        # Connect geometry if provided
        if geometry is not None:
            builder.link(geometry, store.inputs["Geometry"])

        # Connect field value
        if value_field is not None:
            builder.link(value_field, store.inputs["Value"])

        return store

    @staticmethod
    def field_min_max(
        field,
        geometry=None,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> tuple[Node, Node]:
        """
        Compute minimum and maximum values of a field.

        Args:
            field: The field to analyze.
            geometry: Geometry to analyze on.
            builder: NodeTreeBuilder for node creation.
            location: Position for the analysis nodes.

        Returns:
            Tuple of (min_node, max_node).
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Use Attribute Statistics for min/max
        stats = builder.add_node(
            "GeometryNodeAttributeStatistic",
            location,
            name="FieldStats",
        )

        # Connect geometry
        if geometry is not None:
            builder.link(geometry, stats.inputs["Geometry"])

        # Connect field
        if field is not None:
            builder.link(field, stats.inputs["Selection"])

        # Note: stats.outputs has "Min" and "Max"
        return stats, stats  # Return same node, access different outputs

    @staticmethod
    def interpolate_field(
        field_a,
        field_b,
        factor,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Interpolate between two fields.

        Args:
            field_a: First field.
            field_b: Second field.
            factor: Interpolation factor (0 = field_a, 1 = field_b).
            builder: NodeTreeBuilder for node creation.
            location: Position for the interpolation node.

        Returns:
            The interpolation node.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        mix = builder.add_node(
            "ShaderNodeMix",
            location,
            name="MixFields",
        )

        # Set data type for vector mixing
        mix.data_type = "VECTOR"

        # Connect inputs
        if factor is not None:
            builder.link(factor, mix.inputs["Factor"])

        if field_a is not None:
            builder.link(field_a, mix.inputs["A"])

        if field_b is not None:
            builder.link(field_b, mix.inputs["B"])

        return mix

    @staticmethod
    def mask_by_distance(
        positions,
        center: tuple[float, float, float],
        radius: float,
        falloff: str = "SMOOTH",
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Create a distance-based mask field.

        Creates a selection mask based on distance from a center point,
        useful for localizing effects.

        Args:
            positions: Position field to measure from.
            center: Center point for distance calculation.
            radius: Radius of the mask effect.
            falloff: Falloff type ("LINEAR", "SMOOTH", "INVERSE_SQUARE").
            builder: NodeTreeBuilder for node creation.
            location: Position for the mask node.

        Returns:
            Node producing a 0-1 mask field.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Create center position node
        center_node = builder.add_node(
            "GeometryNodeInputVector",
            (location[0] - 200, location[1]),
            name="MaskCenter",
            Vector=center,
        )

        # Calculate distance
        distance = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0], location[1]),
            name="DistanceToCenter",
        )
        distance.operation = "DISTANCE"

        if positions is not None:
            builder.link(positions, distance.inputs[0])
        builder.link(center_node.outputs["Vector"], distance.inputs[1])

        # Map distance to 0-1 range
        map_range = builder.add_node(
            "ShaderNodeMapRange",
            (location[0] + 200, location[1]),
            name="MapDistance",
        )

        map_range.inputs["From Min"].default_value = 0.0
        map_range.inputs["From Max"].default_value = radius
        map_range.inputs["To Min"].default_value = 1.0
        map_range.inputs["To Max"].default_value = 0.0

        builder.link(distance.outputs["Value"], map_range.inputs["Value"])

        return map_range

    @staticmethod
    def curve_parameter(
        curve_geometry=None,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Get curve parameter (0-1 along curve length).

        Args:
            curve_geometry: Curve geometry (uses input if None).
            builder: NodeTreeBuilder for node creation.
            location: Position for the spline parameter node.

        Returns:
            Spline Parameter node.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        spline_param = builder.add_node(
            "GeometryNodeInputSplineCurve",
            location,
            name="CurveParameter",
        )

        return spline_param

    @staticmethod
    def proximity(
        source_geometry,
        target_geometry,
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Measure distance between geometries.

        Args:
            source_geometry: Geometry to measure from.
            target_geometry: Geometry to measure to.
            builder: NodeTreeBuilder for node creation.
            location: Position for the proximity node.

        Returns:
            Geometry Proximity node.
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        proximity = builder.add_node(
            "GeometryNodeGeometryProximity",
            location,
            name="Proximity",
        )

        # Connect geometries
        if source_geometry is not None:
            builder.link(source_geometry, proximity.inputs["Source Position"])

        if target_geometry is not None:
            builder.link(target_geometry, proximity.inputs["Target Geometry"])

        return proximity

    # =========================================================================
    # UV PASS-THROUGH METHODS (Blender 5.x Pattern)
    # =========================================================================

    @staticmethod
    def store_uv_for_shader(
        geometry,
        uv_data,
        uv_name: str = "UV",
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Store UV coordinates for shader access.

        Uses Store Named Attribute with Face Corner domain to pass UVs
        from Geometry Nodes to shader. This is the critical pattern for
        UV pass-through in Blender 5.x.

        **Critical:** UVs must be stored at Face Corner (CORNER) domain,
        not Point domain, for proper interpolation across faces.

        Args:
            geometry: Geometry to store UVs on.
            uv_data: UV coordinate data (2D vector field).
            uv_name: Name for the UV attribute (default "UV").
            builder: NodeTreeBuilder for node creation.
            location: Position for the store node.

        Returns:
            Store Named Attribute node.

        Example (Geometry Nodes):
            >>> # Store procedurally generated UVs
            >>> position = builder.add_node("GeometryNodeInputPosition")
            >>> uv_from_pos = builder.add_node("ShaderNodeSeparateXYZ")
            >>> builder.link(position.outputs["Position"], uv_from_pos.inputs[0])
            >>>
            >>> # Create 2D UV from XZ position
            >>> combine = builder.add_node("ShaderNodeCombineXYZ")
            >>> # ... connect X→X, Z→Y
            >>>
            >>> store = FieldOperations.store_uv_for_shader(
            ...     geometry,
            ...     combine.outputs["Vector"],
            ...     uv_name="ProceduralUV",
            ...     builder=builder
            ... )

        Example (Shader - Reading stored UVs):
            >>> # In material node tree
            >>> attr = material_nodes.new("ShaderNodeAttribute")
            >>> attr.attribute_name = "ProceduralUV"
            >>> # Connect attr.outputs["Vector"] to texture vector input
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        store = builder.add_node(
            "GeometryNodeStoreNamedAttribute",
            location,
            name=f"StoreUV_{uv_name}",
        )

        # Critical: Face Corner domain for UVs
        # This ensures proper interpolation across faces
        store.domain = 'CORNER'

        # Set data type to 2D vector for UVs
        store.data_type = 'FLOAT_VECTOR'

        # Set attribute name
        store.inputs["Name"].default_value = uv_name

        # Connect geometry
        if geometry is not None:
            builder.link(geometry, store.inputs["Geometry"])

        # Connect UV data (2D vector stored as 3D with Z=0)
        if uv_data is not None:
            builder.link(uv_data, store.inputs["Value"])

        return store

    @staticmethod
    def store_named_attribute(
        geometry,
        value,
        attribute_name: str,
        domain: str = 'POINT',
        data_type: str = 'FLOAT',
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Store a named attribute for cross-node or shader access.

        Generic attribute storage that can be used for UVs, colors,
        weights, or any custom data.

        Args:
            geometry: Geometry to store attribute on.
            value: Field value to store.
            attribute_name: Name for the attribute.
            domain: Attribute domain ('POINT', 'EDGE', 'FACE', 'CORNER', 'CURVE', 'INSTANCE').
            data_type: Data type ('FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'BYTE_COLOR', 'BOOLEAN', 'QUATERNION', 'FLOAT4X4').
            builder: NodeTreeBuilder for node creation.
            location: Position for the store node.

        Returns:
            Store Named Attribute node.

        Domain Quick Reference:
            - POINT: Per-vertex data
            - EDGE: Per-edge data
            - FACE: Per-face data
            - CORNER: Per-face-corner (loops) - **USE FOR UVs**
            - CURVE: Per-curve data (hair/curves)
            - INSTANCE: Per-instance data
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        store = builder.add_node(
            "GeometryNodeStoreNamedAttribute",
            location,
            name=f"Store_{attribute_name}",
        )

        # Set domain and data type
        store.domain = domain
        store.data_type = data_type

        # Set attribute name
        store.inputs["Name"].default_value = attribute_name

        # Connect geometry
        if geometry is not None:
            builder.link(geometry, store.inputs["Geometry"])

        # Connect value
        if value is not None:
            builder.link(value, store.inputs["Value"])

        return store

    @staticmethod
    def get_named_attribute(
        attribute_name: str,
        data_type: str = 'FLOAT',
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Read a named attribute from geometry.

        Creates an input node that reads attribute values. Use this
        to access attributes stored via Store Named Attribute.

        Args:
            attribute_name: Name of the attribute to read.
            data_type: Data type ('FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR').
            builder: NodeTreeBuilder for node creation.
            location: Position for the input node.

        Returns:
            Named Attribute input node.

        Example:
            >>> # Read stored UV attribute
            >>> uv_input = FieldOperations.get_named_attribute(
            ...     "ProceduralUV",
            ...     data_type='FLOAT_VECTOR',
            ...     builder=builder
            ... )
            >>> # Use uv_input.outputs["Attribute"] for texture sampling
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        attr_input = builder.add_node(
            "GeometryNodeInputNamedAttribute",
            location,
            name=f"Get_{attribute_name}",
        )

        # Set data type
        attr_input.data_type = data_type

        # Set attribute name
        attr_input.inputs["Name"].default_value = attribute_name

        return attr_input

    @staticmethod
    def create_uv_from_position(
        geometry,
        plane: str = "XZ",
        scale: tuple[float, float] = (1.0, 1.0),
        offset: tuple[float, float] = (0.0, 0.0),
        uv_name: str = "UV",
        builder=None,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Create and store UV coordinates from position.

        Convenience method that generates UVs from world position and
        stores them for shader access. Common pattern for procedural
        textures.

        Args:
            geometry: Geometry to generate UVs for.
            plane: Which axes to use ("XZ", "XY", "YZ").
            scale: UV scale (u_scale, v_scale).
            offset: UV offset (u_offset, v_offset).
            uv_name: Name for the UV attribute.
            builder: NodeTreeBuilder for node creation.
            location: Position for nodes.

        Returns:
            Store Named Attribute node.

        Example:
            >>> # Create UVs for top-down road texture
            >>> store = FieldOperations.create_uv_from_position(
            ...     road_geometry,
            ...     plane="XZ",  # Use X for U, Z for V
            ...     scale=(0.25, 0.25),  # 4m texture tiling
            ...     uv_name="RoadUV",
            ...     builder=builder
            ... )
        """
        if builder is None:
            raise ValueError("builder parameter required for node creation")

        # Get position
        position = builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] - 400, location[1]),
            name="Position",
        )

        # Separate position
        separate = builder.add_node(
            "ShaderNodeSeparateXYZ",
            (location[0] - 200, location[1]),
            name="SeparatePos",
        )
        builder.link(position.outputs["Position"], separate.inputs[0])

        # Select axes based on plane
        u_source = None
        v_source = None

        if plane == "XZ":
            u_source = separate.outputs["X"]
            v_source = separate.outputs["Z"]
        elif plane == "XY":
            u_source = separate.outputs["X"]
            v_source = separate.outputs["Y"]
        elif plane == "YZ":
            u_source = separate.outputs["Y"]
            v_source = separate.outputs["Z"]
        else:
            raise ValueError(f"Invalid plane: {plane}. Use 'XZ', 'XY', or 'YZ'.")

        # Scale U
        scale_u = builder.add_node(
            "ShaderNodeMath",
            (location[0], location[1] + 50),
            name="ScaleU",
        )
        scale_u.operation = 'MULTIPLY'
        scale_u.inputs[1].default_value = scale[0]
        builder.link(u_source, scale_u.inputs[0])

        # Offset U
        offset_u = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 100, location[1] + 50),
            name="OffsetU",
        )
        offset_u.operation = 'ADD'
        offset_u.inputs[1].default_value = offset[0]
        builder.link(scale_u.outputs[0], offset_u.inputs[0])

        # Scale V
        scale_v = builder.add_node(
            "ShaderNodeMath",
            (location[0], location[1] - 50),
            name="ScaleV",
        )
        scale_v.operation = 'MULTIPLY'
        scale_v.inputs[1].default_value = scale[1]
        builder.link(v_source, scale_v.inputs[0])

        # Offset V
        offset_v = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 100, location[1] - 50),
            name="OffsetV",
        )
        offset_v.operation = 'ADD'
        offset_v.inputs[1].default_value = offset[1]
        builder.link(scale_v.outputs[0], offset_v.inputs[0])

        # Combine to 2D vector (UV)
        combine = builder.add_node(
            "ShaderNodeCombineXYZ",
            (location[0] + 200, location[1]),
            name="CombineUV",
        )
        builder.link(offset_u.outputs[0], combine.inputs["X"])
        builder.link(offset_v.outputs[0], combine.inputs["Y"])
        # Z stays at 0

        # Store UV
        store = FieldOperations.store_uv_for_shader(
            geometry,
            combine.outputs["Vector"],
            uv_name=uv_name,
            builder=builder,
            location=(location[0] + 400, location[1]),
        )

        return store
