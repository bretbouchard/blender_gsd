"""
Erosion - Erosion systems for weathered mesh effects.

Based on CGMatter tutorials for procedural erosion. Creates realistic
weathered, worn, and decayed mesh appearances using edge erosion and
face pitting techniques.

Flow Overview:
    Edge Erosion:
        Edge Angle -> Separate -> Delete Faces -> Mesh to Curve
        -> Resample -> Tube -> SDF Remesh -> Boolean

    Face Erosion:
        Distribute Points -> Noise -> Delete by threshold
        -> Points to SDF -> Grid to Mesh -> Boolean

Usage:
    # Quick erosion
    eroded = ErosionSystem(mesh).erode_edges().erode_faces().finalize()

    # Custom erosion parameters
    system = ErosionSystem(mesh)
    system.erode_edges(angle_threshold=6.0, noise_scale=0.5)
    system.erode_faces(point_count=2000, threshold=0.4)
    result = system.finalize()

    # Direct tube cutter creation
    cutter = EdgeErosion.create_tube_cutter(points, base_radius=0.1)
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Optional

from mathutils import Vector

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bpy.types import Node, Object

    from .node_builder import NodeTreeBuilder


class EdgeErosion:
    """
    Edge erosion for weathered mesh look.

    Creates erosion effects along mesh edges based on angle between
    adjacent faces. Sharp edges get more erosion, creating realistic
    wear patterns.

    The erosion creates tube-like cutters along edges that are
    subtracted from the mesh using boolean operations.
    """

    @staticmethod
    def erode_by_angle(
        mesh: Optional[Object] = None,
        angle_threshold: float = 6.0,
        noise_scale: float = 1.0,
        erosion_radius: float = 0.05,
        noise_amplitude: float = 0.02,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Erode edges based on angle between faces.

        Sharp edges (above threshold) are converted to curves, then
        tube cutters are generated and subtracted from the mesh.

        Flow:
            1. Edge Angle -> Separate geometry by threshold
            2. Delete faces (keep edges)
            3. Mesh to Curve
            4. Resample curve (for smooth cutter)
            5. Create noise-controlled tube
            6. SDF Remesh (optional for smooth result)
            7. Boolean subtract from original

        Args:
            mesh: Mesh object to erode (optional, use builder input if None).
            angle_threshold: Angle in degrees above which edges are eroded (default 6.0).
            noise_scale: Scale of noise on tube radius (default 1.0).
            erosion_radius: Base radius of erosion tubes (default 0.05).
            noise_amplitude: Amplitude of noise variation (default 0.02).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            The final boolean node, or None if no builder provided.

        Example:
            >>> result = EdgeErosion.erode_by_angle(
            ...     mesh,
            ...     angle_threshold=10.0,
            ...     noise_scale=2.0,
            ...     builder=my_builder
            ... )
        """
        if builder is None:
            return None

        # Convert angle to radians for internal use
        angle_rad = angle_threshold

        # Get input geometry
        if mesh is not None:
            # Create Object Info node to get mesh
            obj_info = builder.add_node(
                "GeometryNodeObjectInfo",
                (location[0] - 200, location[1]),
                name="MeshInput",
            )
            obj_info.inputs[0].default_value = mesh
            obj_info.transform_space = "RELATIVE"
            input_geo = obj_info.outputs["Geometry"]
        else:
            # Use group input
            group_input = builder.add_group_input((location[0] - 200, location[1]))
            input_geo = group_input.outputs.get("Geometry", group_input.outputs[0])

        # Step 1: Calculate edge angle
        edge_angle = builder.add_node(
            "GeometryNodeInputMeshEdgeAngle",
            (location[0], location[1] + 100),
            name="EdgeAngle",
        )
        builder.link(input_geo, edge_angle.inputs["Mesh"])

        # Step 2: Convert angle threshold to radians and compare
        threshold_node = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 100, location[1] + 100),
            name="AngleThreshold",
        )
        threshold_node.operation = "LESS_THAN"
        builder.link(edge_angle.outputs["Unsigned Angle"], threshold_node.inputs[0])
        threshold_node.inputs[1].default_value = angle_rad

        # Step 3: Separate geometry by angle (select sharp edges)
        separate = builder.add_node(
            "GeometryNodeSeparateGeometry",
            (location[0] + 200, location[1]),
            name="SeparateSharpEdges",
        )
        builder.link(input_geo, separate.inputs["Geometry"])
        builder.link(threshold_node.outputs[0], separate.inputs["Selection"])

        # Step 4: Delete faces, keep only edges
        delete_faces = builder.add_node(
            "GeometryNodeDeleteGeometry",
            (location[0] + 350, location[1]),
            name="DeleteFaces",
        )
        delete_faces.inputs["Domain"].default_value = "FACE"
        delete_faces.inputs["Mode"].default_value = "ALL"
        builder.link(separate.outputs["Selection"], delete_faces.inputs["Geometry"])

        # Step 5: Mesh to Curve
        mesh_to_curve = builder.add_node(
            "GeometryNodeMeshToCurve",
            (location[0] + 500, location[1]),
            name="EdgeToCurve",
        )
        builder.link(delete_faces.outputs["Geometry"], mesh_to_curve.inputs["Mesh"])

        # Step 6: Resample curve for smooth cutter
        resample = builder.add_node(
            "GeometryNodeResampleCurve",
            (location[0] + 650, location[1]),
            name="ResampleForTube",
        )
        resample.inputs["Count"].default_value = 64
        builder.link(mesh_to_curve.outputs["Curve"], resample.inputs["Curve"])

        # Step 7: Create noise-controlled tube radius
        # Get curve point positions for noise
        curve_pos = builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] + 650, location[1] + 100),
            name="CurvePosition",
        )

        noise = builder.add_node(
            "ShaderNodeTexNoise",
            (location[0] + 800, location[1] + 100),
            name="RadiusNoise",
        )
        noise.inputs["Scale"].default_value = noise_scale
        builder.link(curve_pos.outputs["Position"], noise.inputs["Vector"])

        # Map noise to radius variation
        map_range = builder.add_node(
            "ShaderNodeMapRange",
            (location[0] + 950, location[1] + 100),
            name="MapNoiseToRadius",
        )
        map_range.inputs["From Min"].default_value = 0.0
        map_range.inputs["From Max"].default_value = 1.0
        map_range.inputs["To Min"].default_value = erosion_radius - noise_amplitude
        map_range.inputs["To Max"].default_value = erosion_radius + noise_amplitude
        builder.link(noise.outputs["Fac"], map_range.inputs["Value"])

        # Step 8: Set curve radius
        set_radius = builder.add_node(
            "GeometryNodeSetCurveRadius",
            (location[0] + 800, location[1]),
            name="SetTubeRadius",
        )
        set_radius.inputs["Radius"].default_value = erosion_radius
        builder.link(resample.outputs["Curve"], set_radius.inputs["Curve"])
        builder.link(map_range.outputs["Result"], set_radius.inputs["Radius"])

        # Step 9: Curve to mesh (create tube)
        curve_circle = builder.add_node(
            "GeometryNodeCurvePrimitiveCircle",
            (location[0] + 950, location[1] - 100),
            name="TubeProfile",
        )
        curve_circle.inputs["Resolution"].default_value = 8
        curve_circle.inputs["Radius"].default_value = 1.0

        curve_to_mesh = builder.add_node(
            "GeometryNodeCurveToMesh",
            (location[0] + 1100, location[1]),
            name="CreateTube",
        )
        builder.link(set_radius.outputs["Curve"], curve_to_mesh.inputs["Curve"])
        builder.link(curve_circle.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

        # Step 10: Boolean subtract from original
        boolean = builder.add_node(
            "GeometryNodeBoolean",
            (location[0] + 1300, location[1]),
            name="ErodeBoolean",
        )
        boolean.inputs["Operation"].default_value = "DIFFERENCE"
        builder.link(input_geo, boolean.inputs["Mesh A"])
        builder.link(curve_to_mesh.outputs["Mesh"], boolean.inputs["Mesh B"])

        return boolean

    @staticmethod
    def create_tube_cutter(
        points: Sequence[Vector],
        base_radius: float = 0.05,
        noise_amplitude: float = 0.02,
        noise_scale: float = 1.0,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Create noise-controlled tube for boolean cutting.

        Creates a tube along a path defined by points with noise-modulated
        radius for organic erosion effects.

        Args:
            points: Sequence of Vector points defining the tube path.
            base_radius: Base radius of the tube (default 0.05).
            noise_amplitude: Amplitude of radius noise (default 0.02).
            noise_scale: Scale of noise pattern (default 1.0).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            The curve to mesh node outputting the tube, or None.

        Note:
            This creates the cutter geometry only. Use with Boolean
            node to subtract from target mesh.

        Example:
            >>> points = [Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((2, 0, 0))]
            >>> cutter = EdgeErosion.create_tube_cutter(
            ...     points, base_radius=0.1, noise_amplitude=0.03, builder=my_builder
            ... )
        """
        if builder is None or not points:
            return None

        # Create curve from points
        # In geometry nodes, we'd use Curve Line or create points
        # For simplicity, create a curve line and resample

        curve_line = builder.add_node(
            "GeometryNodeCurvePrimitiveLine",
            location,
            name="TubePath",
        )

        # Set start and end from points
        if len(points) >= 2:
            curve_line.inputs["Start"].default_value = tuple(points[0])
            curve_line.inputs["End"].default_value = tuple(points[-1])

        # Resample to match point count
        resample = builder.add_node(
            "GeometryNodeResampleCurve",
            (location[0] + 150, location[1]),
            name="ResampleTubePath",
        )
        resample.inputs["Count"].default_value = len(points)
        builder.link(curve_line.outputs["Curve"], resample.inputs["Curve"])

        # Add noise to radius
        position = builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] + 150, location[1] + 100),
            name="TubePosition",
        )

        noise = builder.add_node(
            "ShaderNodeTexNoise",
            (location[0] + 300, location[1] + 100),
            name="TubeRadiusNoise",
        )
        noise.inputs["Scale"].default_value = noise_scale
        builder.link(position.outputs["Position"], noise.inputs["Vector"])

        # Map noise to radius
        map_range = builder.add_node(
            "ShaderNodeMapRange",
            (location[0] + 450, location[1] + 100),
            name="MapToRadius",
        )
        map_range.inputs["From Min"].default_value = 0.0
        map_range.inputs["From Max"].default_value = 1.0
        map_range.inputs["To Min"].default_value = base_radius - noise_amplitude
        map_range.inputs["To Max"].default_value = base_radius + noise_amplitude
        builder.link(noise.outputs["Fac"], map_range.inputs["Value"])

        # Set radius
        set_radius = builder.add_node(
            "GeometryNodeSetCurveRadius",
            (location[0] + 300, location[1]),
            name="SetTubeRadius",
        )
        builder.link(resample.outputs["Curve"], set_radius.inputs["Curve"])
        builder.link(map_range.outputs["Result"], set_radius.inputs["Radius"])

        # Create profile circle
        profile = builder.add_node(
            "GeometryNodeCurvePrimitiveCircle",
            (location[0] + 450, location[1] - 100),
            name="TubeProfile",
        )
        profile.inputs["Resolution"].default_value = 8

        # Curve to mesh
        curve_to_mesh = builder.add_node(
            "GeometryNodeCurveToMesh",
            (location[0] + 600, location[1]),
            name="TubeMesh",
        )
        builder.link(set_radius.outputs["Curve"], curve_to_mesh.inputs["Curve"])
        builder.link(profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

        return curve_to_mesh


class FaceErosion:
    """
    Face erosion with pitting and surface decay.

    Creates pitted, decayed surface effects by distributing points
    based on noise and creating boolean cutters at those locations.
    """

    @staticmethod
    def erode_by_noise(
        mesh: Optional[Object] = None,
        point_count: int = 1500,
        threshold: float = 0.5,
        noise_scale: float = 1.0,
        pit_radius: float = 0.02,
        pit_depth: float = 0.05,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Erode faces based on noise threshold.

        Distributes points on the mesh surface, filters by noise
        threshold, and creates pit cutters at those locations.

        Flow:
            1. Distribute Points on surface
            2. Noise texture evaluation
            3. Delete points below threshold
            4. Create spheres/cones at remaining points
            5. Points to SDF / Grid to Mesh
            6. Boolean subtract from original

        Args:
            mesh: Mesh object to erode.
            point_count: Number of points to distribute (default 1500).
            threshold: Noise threshold (0-1, default 0.5).
            noise_scale: Scale of noise pattern (default 1.0).
            pit_radius: Radius of each pit (default 0.02).
            pit_depth: Depth of pits (default 0.05).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            The final boolean node, or None if no builder.

        Example:
            >>> result = FaceErosion.erode_by_noise(
            ...     mesh,
            ...     point_count=2000,
            ...     threshold=0.6,
            ...     noise_scale=2.0,
            ...     builder=my_builder
            ... )
        """
        if builder is None:
            return None

        # Get input geometry
        if mesh is not None:
            obj_info = builder.add_node(
                "GeometryNodeObjectInfo",
                (location[0] - 200, location[1]),
                name="MeshInput",
            )
            obj_info.inputs[0].default_value = mesh
            obj_info.transform_space = "RELATIVE"
            input_geo = obj_info.outputs["Geometry"]
        else:
            group_input = builder.add_group_input((location[0] - 200, location[1]))
            input_geo = group_input.outputs.get("Geometry", group_input.outputs[0])

        # Step 1: Distribute points on surface
        distribute = builder.add_node(
            "GeometryNodeDistributePointsOnFaces",
            (location[0], location[1]),
            name="DistributePitPoints",
        )
        distribute.inputs["Density"].default_value = point_count
        builder.link(input_geo, distribute.inputs["Mesh"])

        # Step 2: Evaluate noise at point positions
        position = builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] + 150, location[1] + 100),
            name="PointPosition",
        )

        noise = builder.add_node(
            "ShaderNodeTexNoise",
            (location[0] + 300, location[1] + 100),
            name="PitNoise",
        )
        noise.inputs["Scale"].default_value = noise_scale
        builder.link(position.outputs["Position"], noise.inputs["Vector"])

        # Step 3: Threshold comparison
        compare = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] + 100),
            name="NoiseThreshold",
        )
        compare.operation = "GREATER_THAN"
        builder.link(noise.outputs["Fac"], compare.inputs[0])
        compare.inputs[1].default_value = threshold

        # Step 4: Delete points below threshold
        delete = builder.add_node(
            "GeometryNodeDeleteGeometry",
            (location[0] + 600, location[1]),
            name="DeleteLowNoise",
        )
        builder.link(distribute.outputs["Points"], delete.inputs["Geometry"])
        builder.link(compare.outputs[0], delete.inputs["Selection"])

        # Step 5: Instance pit geometry at points
        # Create a cone/sphere for pit shape
        pit_shape = builder.add_node(
            "GeometryNodeMeshCone",
            (location[0] + 600, location[1] - 150),
            name="PitShape",
        )
        pit_shape.inputs["Radius Top"].default_value = 0.0  # Pointed top
        pit_shape.inputs["Radius Bottom"].default_value = pit_radius
        pit_shape.inputs["Depth"].default_value = pit_depth
        pit_shape.inputs["Vertices"].default_value = 8

        # Instance on points
        instance = builder.add_node(
            "GeometryNodeInstanceOnPoints",
            (location[0] + 800, location[1]),
            name="InstancePits",
        )
        builder.link(delete.outputs["Geometry"], instance.inputs["Points"])
        builder.link(pit_shape.outputs["Mesh"], instance.inputs["Instance"])

        # Get normal for orientation
        normal = builder.add_node(
            "GeometryNodeInputNormal",
            (location[0] + 650, location[1] + 50),
            name="SurfaceNormal",
        )

        # Rotate to align with normal
        align_euler = builder.add_node(
            "FunctionNodeAlignEulerToVector",
            (location[0] + 750, location[1] + 50),
            name="AlignToNormal",
        )
        align_euler.inputs["Axis"].default_value = "Z"
        builder.link(normal.outputs["Normal"], align_euler.inputs["Vector"])
        builder.link(align_euler.outputs["Rotation"], instance.inputs["Rotation"])

        # Step 6: Realize instances
        realize = builder.add_node(
            "GeometryNodeRealizeInstances",
            (location[0] + 1000, location[1]),
            name="RealizePits",
        )
        builder.link(instance.outputs["Instances"], realize.inputs["Geometry"])

        # Step 7: Boolean subtract
        boolean = builder.add_node(
            "GeometryNodeBoolean",
            (location[0] + 1200, location[1]),
            name="PitBoolean",
        )
        boolean.inputs["Operation"].default_value = "DIFFERENCE"
        builder.link(input_geo, boolean.inputs["Mesh A"])
        builder.link(realize.outputs["Geometry"], boolean.inputs["Mesh B"])

        return boolean

    @staticmethod
    def remove_floaters(
        mesh: Optional[Object] = None,
        min_area: float = 0.001,
        min_volume: float = 0.0001,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Remove disconnected floating pieces from erosion.

        After erosion, small disconnected pieces may be left floating.
        This removes them based on area/volume threshold.

        Flow:
            1. Mesh Island -> Get island index
            2. Accumulate Field (face area or volume)
            3. Delete if total < threshold

        Args:
            mesh: Mesh object to clean.
            min_area: Minimum face area to keep (default 0.001).
            min_volume: Minimum volume to keep (default 0.0001).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node with cleaned geometry, or None.

        Example:
            >>> cleaned = FaceErosion.remove_floaters(
            ...     eroded_mesh, min_area=0.005, builder=my_builder
            ... )
        """
        if builder is None:
            return None

        # Get input geometry
        if mesh is not None:
            obj_info = builder.add_node(
                "GeometryNodeObjectInfo",
                (location[0] - 200, location[1]),
                name="MeshInput",
            )
            obj_info.inputs[0].default_value = mesh
            obj_info.transform_space = "RELATIVE"
            input_geo = obj_info.outputs["Geometry"]
        else:
            group_input = builder.add_group_input((location[0] - 200, location[1]))
            input_geo = group_input.outputs.get("Geometry", group_input.outputs[0])

        # Step 1: Get island index
        island = builder.add_node(
            "GeometryNodeInputMeshIsland",
            (location[0], location[1] + 50),
            name="MeshIsland",
        )
        builder.link(input_geo, island.inputs["Mesh"])

        # Step 2: Get face area
        face_area = builder.add_node(
            "GeometryNodeInputMeshFaceArea",
            (location[0], location[1] - 50),
            name="FaceArea",
        )
        builder.link(input_geo, face_area.inputs["Mesh"])

        # Step 3: Accumulate area by island
        accumulate = builder.add_node(
            "GeometryNodeAccumulateField",
            (location[0] + 200, location[1]),
            name="AccumulateIslandArea",
        )
        builder.link(face_area.outputs["Area"], accumulate.inputs["Value"])
        builder.link(island.outputs["Index"], accumulate.inputs["Group Index"])

        # Step 4: Compare to threshold
        compare = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1]),
            name="AreaThreshold",
        )
        compare.operation = "GREATER_THAN"
        builder.link(accumulate.outputs["Total"], compare.inputs[0])
        compare.inputs[1].default_value = min_area

        # Step 5: Delete small pieces
        delete = builder.add_node(
            "GeometryNodeDeleteGeometry",
            (location[0] + 600, location[1]),
            name="DeleteFloaters",
        )
        builder.link(input_geo, delete.inputs["Geometry"])
        builder.link(compare.outputs[0], delete.inputs["Selection"])

        return delete


class ErosionSystem:
    """
    Combined edge and face erosion system.

    Provides a fluent interface for building complex erosion effects
    with support for chaining operations and subdivision.

    Example:
        >>> result = (
        ...     ErosionSystem(mesh, builder)
        ...     .erode_edges(angle_threshold=8.0)
        ...     .erode_faces(point_count=1000)
        ...     .add_subdivision(levels=2)
        ...     .finalize()
        ... )
    """

    def __init__(
        self,
        mesh: Optional[Object] = None,
        builder: Optional[NodeTreeBuilder] = None,
    ):
        """
        Initialize the erosion system.

        Args:
            mesh: Mesh object to erode.
            builder: NodeTreeBuilder for node creation.
        """
        self.mesh = mesh
        self.builder = builder
        self._operations: list[Callable] = []
        self._last_node: Optional[Node] = None

    def erode_edges(
        self,
        angle_threshold: float = 6.0,
        noise_scale: float = 1.0,
        erosion_radius: float = 0.05,
        noise_amplitude: float = 0.02,
    ) -> "ErosionSystem":
        """
        Apply edge erosion.

        Args:
            angle_threshold: Angle in degrees above which edges erode.
            noise_scale: Scale of noise on tube radius.
            erosion_radius: Base radius of erosion tubes.
            noise_amplitude: Amplitude of noise variation.

        Returns:
            Self for method chaining.
        """
        if self.builder:
            self._last_node = EdgeErosion.erode_by_angle(
                mesh=self.mesh if self._last_node is None else None,
                angle_threshold=angle_threshold,
                noise_scale=noise_scale,
                erosion_radius=erosion_radius,
                noise_amplitude=noise_amplitude,
                builder=self.builder,
                location=(0, len(self._operations) * -300),
            )
        self._operations.append("edge_erosion")
        return self

    def erode_faces(
        self,
        point_count: int = 1500,
        threshold: float = 0.5,
        noise_scale: float = 1.0,
        pit_radius: float = 0.02,
        pit_depth: float = 0.05,
    ) -> "ErosionSystem":
        """
        Apply face erosion with pitting.

        Args:
            point_count: Number of pit points.
            threshold: Noise threshold for pit placement.
            noise_scale: Scale of noise pattern.
            pit_radius: Radius of each pit.
            pit_depth: Depth of pits.

        Returns:
            Self for method chaining.
        """
        if self.builder:
            self._last_node = FaceErosion.erode_by_noise(
                mesh=None,  # Use previous output
                point_count=point_count,
                threshold=threshold,
                noise_scale=noise_scale,
                pit_radius=pit_radius,
                pit_depth=pit_depth,
                builder=self.builder,
                location=(0, len(self._operations) * -300),
            )
        self._operations.append("face_erosion")
        return self

    def remove_floaters(
        self,
        min_area: float = 0.001,
    ) -> "ErosionSystem":
        """
        Remove floating pieces after erosion.

        Args:
            min_area: Minimum area to keep.

        Returns:
            Self for method chaining.
        """
        if self.builder:
            self._last_node = FaceErosion.remove_floaters(
                mesh=None,
                min_area=min_area,
                builder=self.builder,
                location=(0, len(self._operations) * -300),
            )
        self._operations.append("remove_floaters")
        return self

    def add_subdivision(
        self,
        levels: int = 1,
        boundary_smooth: str = "ALL",
    ) -> "ErosionSystem":
        """
        Add subdivision surface for smooth result.

        Args:
            levels: Number of subdivision levels.
            boundary_smooth: Boundary smooth mode ("ALL", "PRESERVE_CORNERS").

        Returns:
            Self for method chaining.
        """
        if self.builder and self._last_node:
            subdivide = self.builder.add_node(
                "GeometryNodeSubdivisionSurface",
                (0, len(self._operations) * -300),
                name="SubdivideEroded",
            )
            subdivide.inputs["Level"].default_value = levels
            subdivide.inputs["Boundary Smooth"].default_value = boundary_smooth

            self.builder.link(
                self._last_node.outputs["Geometry"],
                subdivide.inputs["Mesh"],
            )
            self._last_node = subdivide

        self._operations.append("subdivision")
        return self

    def add_smooth_shading(self) -> "ErosionSystem":
        """
        Apply smooth shading to result.

        Returns:
            Self for method chaining.
        """
        if self.builder and self._last_node:
            smooth = self.builder.add_node(
                "GeometryNodeSetShadeSmooth",
                (0, len(self._operations) * -300),
                name="SmoothShading",
            )
            smooth.inputs["Shade Smooth"].default_value = True

            self.builder.link(
                self._last_node.outputs["Geometry"],
                smooth.inputs["Geometry"],
            )
            self._last_node = smooth

        self._operations.append("smooth_shading")
        return self

    def finalize(self) -> Optional[Node]:
        """
        Finalize and return the result node.

        Returns:
            The final node in the erosion pipeline.
        """
        if self.builder and self._last_node:
            # Add group output if not present
            output = self.builder.add_node(
                "NodeGroupOutput",
                (200, 0),
                name="ErosionOutput",
            )
            self.builder.link(
                self._last_node.outputs["Geometry"],
                output.inputs["Geometry"],
            )
        return self._last_node


# Convenience function for quick erosion
def erode_mesh(
    mesh: Object,
    edge_angle: float = 6.0,
    face_points: int = 1500,
    noise_scale: float = 1.0,
    builder: Optional[NodeTreeBuilder] = None,
) -> Optional[Node]:
    """
    Quick erosion with default settings.

    Applies both edge and face erosion with sensible defaults.

    Args:
        mesh: Mesh to erode.
        edge_angle: Edge angle threshold in degrees.
        face_points: Number of face pit points.
        noise_scale: Scale of noise patterns.
        builder: NodeTreeBuilder for node creation.

    Returns:
        Final erosion node, or None.

    Example:
        >>> eroded = erode_mesh(my_mesh, edge_angle=8.0, builder=my_builder)
    """
    return (
        ErosionSystem(mesh, builder)
        .erode_edges(angle_threshold=edge_angle, noise_scale=noise_scale)
        .erode_faces(point_count=face_points, noise_scale=noise_scale)
        .remove_floaters()
        .finalize()
    )
