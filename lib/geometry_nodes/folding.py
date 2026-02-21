"""
Folding - Doctor Strange-style building folding effect.

Based on CGMatter tutorials for the building folding effect. Creates
the illusion of buildings folding in on themselves like in the
Doctor Strange movie, using wedge-shaped visibility masking and
instance rotation.

Flow Overview:
    1. Calculate wedge angle: alpha = 2*pi / instance_count
    2. Create folding material with wedge mask
    3. Setup geometry nodes for instance rotation
    4. Animate rotation over time

Usage:
    # Create folding effect
    folder = BuildingFolder(base_mesh, instance_count=12)
    folder.setup_folding_geometry(builder)
    folder.create_folding_material()
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Optional

import bpy
from mathutils import Vector

if TYPE_CHECKING:
    from bpy.types import Material, Node, NodeTree, Object

    from .node_builder import NodeTreeBuilder


class BuildingFolder:
    """
    Doctor Strange-style building folding effect.

    Creates a folding effect where multiple instances of a building
    rotate around a central point, with wedge-shaped visibility
    masks creating the illusion of infinite folding.

    The effect uses:
    1. Multiple instances arranged in a circle
    2. Each instance has a material with wedge masking
    3. Rotation animation creates the folding motion

    Attributes:
        base_mesh: The mesh to fold.
        instance_count: Number of instances in the fold.
        radius: Radius of the folding circle.
        wedge_angle: Angle of visibility wedge (2*pi/count).

    Example:
        >>> folder = BuildingFolder(building_mesh, instance_count=12)
        >>> folder.setup_folding_geometry(builder)
        >>> folder.create_folding_material()
        >>> folder.create_animation_driver(duration=5.0)
    """

    def __init__(
        self,
        base_mesh: Optional[Object] = None,
        instance_count: int = 12,
        radius: float = 5.0,
    ):
        """
        Initialize the building folder.

        Args:
            base_mesh: The mesh object to create folding effect from.
            instance_count: Number of instances (default 12).
            radius: Radius of the folding circle (default 5.0).
        """
        self.base_mesh = base_mesh
        self.instance_count = max(3, instance_count)
        self.radius = max(0.1, radius)
        self.wedge_angle = self.calculate_alpha_angle(instance_count)
        self._animation_duration: float = 5.0
        self._fold_axis: str = "Z"
        self._material: Optional[Material] = None

    @staticmethod
    def calculate_alpha_angle(instance_count: int) -> float:
        """
        Calculate wedge angle for visibility masking.

        Formula: alpha = 2*pi / number_of_instances

        Args:
            instance_count: Number of instances in the fold.

        Returns:
            Wedge angle in radians.

        Example:
            >>> angle = BuildingFolder.calculate_alpha_angle(12)
            >>> # Returns approximately 0.524 radians (30 degrees)
        """
        if instance_count <= 0:
            raise ValueError("instance_count must be positive")
        return 2 * math.pi / instance_count

    @staticmethod
    def create_folding_material(
        instance_count: int,
        wedge_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        material_name: str = "FoldingMaterial",
    ) -> Optional[Material]:
        """
        Create shader material for wedge masking.

        The material creates a wedge-shaped alpha mask that hides
        portions of each instance based on rotation angle.

        Flow:
            Texture Coord -> Separate XYZ -> Vector Rotate
            -> Mask calculations -> Alpha output

        The mask is calculated as:
            1. Get local position
            2. Rotate by instance index * wedge_angle
            3. Create wedge mask using atan2(Y, X)
            4. Output to alpha channel

        Args:
            instance_count: Number of instances (for wedge calculation).
            wedge_color: Base color of the material (default white).
            material_name: Name for the created material.

        Returns:
            Created Material, or None if creation failed.

        Example:
            >>> mat = BuildingFolder.create_folding_material(
            ...     instance_count=12,
            ...     wedge_color=(0.8, 0.9, 1.0, 1.0)
            ... )
        """
        # Check if we're in a Blender context
        if not hasattr(bpy, "data"):
            return None

        # Create or get material
        if material_name in bpy.data.materials:
            return bpy.data.materials[material_name]

        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create node setup
        # Output node
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (800, 0)

        # Principled BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (600, 0)
        bsdf.inputs["Base Color"].default_value = wedge_color

        # Texture Coordinate
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-600, 0)

        # Separate XYZ
        separate = nodes.new("ShaderNodeSeparateXYZ")
        separate.location = (-400, 0)

        # Vector Rotate
        rotate = nodes.new("ShaderNodeVectorRotate")
        rotate.location = (-200, 0)
        rotate.inputs["Rotation Type"].default_value = "AXIS_ANGLE"

        # Math nodes for angle calculation
        # Angle = instance_index * wedge_angle
        # For shader, we use a driver or attribute

        # Calculate wedge angle
        wedge_angle = 2 * math.pi / instance_count

        # Arctangent2 for angle from position
        atan2 = nodes.new("ShaderNodeMath")
        atan2.location = (0, 100)
        atan2.operation = "ARCTANGENT2"

        # Separate rotated position
        separate_rot = nodes.new("ShaderNodeSeparateXYZ")
        separate_rot.location = (0, -100)

        # Greater than for wedge mask
        greater_than = nodes.new("ShaderNodeMath")
        greater_than.location = (200, 100)
        greater_than.operation = "GREATER_THAN"
        greater_than.inputs[1].default_value = 0.0

        # Add for upper wedge
        add_upper = nodes.new("ShaderNodeMath")
        add_upper.location = (200, 0)
        add_upper.operation = "ADD"

        # Subtract for comparing
        subtract = nodes.new("ShaderNodeMath")
        subtract.location = (200, -100)
        subtract.operation = "SUBTRACT"
        subtract.inputs[1].default_value = wedge_angle

        # Greater than for upper bound
        greater_than_upper = nodes.new("ShaderNodeMath")
        greater_than_upper.location = (400, -100)
        greater_than_upper.operation = "GREATER_THAN"
        greater_than_upper.inputs[1].default_value = 0.0

        # Boolean AND for wedge mask
        and_node = nodes.new("ShaderNodeMath")
        and_node.location = (400, 0)
        and_node.operation = "MULTIPLY"

        # Connect nodes
        links.new(tex_coord.outputs["Object"], separate.inputs["Vector"])
        vector_input = rotate.inputs["Vector"] if "Vector" in rotate.inputs else rotate.inputs[0]
        links.new(separate.outputs["X"], vector_input)
        links.new(separate.outputs["X"], atan2.inputs[0])
        links.new(separate.outputs["Y"], atan2.inputs[1])
        links.new(rotate.outputs["Vector"], separate_rot.inputs["Vector"])
        links.new(separate_rot.outputs["X"], greater_than.inputs[0])
        links.new(atan2.outputs[0], add_upper.inputs[0])
        links.new(atan2.outputs[0], subtract.inputs[0])
        links.new(subtract.outputs[0], greater_than_upper.inputs[0])
        links.new(greater_than.outputs[0], and_node.inputs[0])
        links.new(greater_than_upper.outputs[0], and_node.inputs[1])
        links.new(and_node.outputs[0], bsdf.inputs["Alpha"])
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        return material

    @staticmethod
    def setup_folding_geometry(
        base_mesh: Optional[Object] = None,
        instance_count: int = 12,
        radius: float = 5.0,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Setup geometry nodes for folding instances.

        Creates a circle of points, instances the base mesh on each,
        and sets up rotation animation.

        Flow:
            1. Mesh Circle -> Create points in a circle
            2. Instance on Points -> Place instances
            3. Transform -> Store rotation attribute
            4. Store Named Attribute -> For animation

        Args:
            base_mesh: Mesh to instance.
            instance_count: Number of instances.
            radius: Circle radius.
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Final node with folding geometry, or None.

        Example:
            >>> result = BuildingFolder.setup_folding_geometry(
            ...     building_mesh,
            ...     instance_count=12,
            ...     radius=5.0,
            ...     builder=my_builder
            ... )
        """
        if builder is None:
            return None

        # Create circle of points
        circle = builder.add_node(
            "GeometryNodeMeshCircle",
            location,
            name="FoldCircle",
        )
        circle.inputs["Vertices"].default_value = instance_count
        circle.inputs["Radius"].default_value = radius

        # Get object info for base mesh
        if base_mesh is not None:
            obj_info = builder.add_node(
                "GeometryNodeObjectInfo",
                (location[0] + 150, location[1] - 100),
                name="BaseMeshInfo",
            )
            obj_info.inputs[0].default_value = base_mesh
            obj_info.transform_space = "RELATIVE"
            instance_geo = obj_info.outputs["Geometry"]
        else:
            group_input = builder.add_group_input((location[0], location[1] - 100))
            instance_geo = group_input.outputs.get("Instance", group_input.outputs[1] if len(group_input.outputs) > 1 else None)

        if instance_geo is None:
            return circle

        # Get index for rotation calculation
        index = builder.add_node(
            "GeometryNodeInputIndex",
            (location[0] + 100, location[1] + 100),
            name="InstanceIndex",
        )

        # Calculate rotation angle for each instance
        # angle = index * wedge_angle
        wedge_angle = 2 * math.pi / instance_count

        multiply = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 200, location[1] + 100),
            name="CalcRotationAngle",
        )
        multiply.operation = "MULTIPLY"
        multiply.inputs[1].default_value = wedge_angle
        builder.link(index.outputs["Index"], multiply.inputs[0])

        # Create rotation vector (around Z axis)
        combine_rot = builder.add_node(
            "ShaderNodeCombineXYZ",
            (location[0] + 350, location[1] + 100),
            name="CombineRotation",
        )
        combine_rot.inputs["X"].default_value = 0.0
        combine_rot.inputs["Y"].default_value = 0.0
        builder.link(multiply.outputs[0], combine_rot.inputs["Z"])

        # Instance on points
        instance = builder.add_node(
            "GeometryNodeInstanceOnPoints",
            (location[0] + 500, location[1]),
            name="FoldInstances",
        )
        builder.link(circle.outputs["Mesh"], instance.inputs["Points"])
        builder.link(instance_geo, instance.inputs["Instance"])
        builder.link(combine_rot.outputs["Vector"], instance.inputs["Rotation"])

        # Store instance index as attribute for material
        store_attr = builder.add_node(
            "GeometryNodeStoreNamedAttribute",
            (location[0] + 700, location[1]),
            name="StoreInstanceIndex",
        )
        store_attr.inputs["Name"].default_value = "instance_index"
        store_attr.inputs["Domain"].default_value = "INSTANCE"
        builder.link(instance.outputs["Instances"], store_attr.inputs["Geometry"])
        builder.link(index.outputs["Index"], store_attr.inputs["Value"])

        # Realize instances (optional, for mesh output)
        realize = builder.add_node(
            "GeometryNodeRealizeInstances",
            (location[0] + 900, location[1]),
            name="RealizeFold",
        )
        builder.link(store_attr.outputs["Geometry"], realize.inputs["Geometry"])

        return realize

    def set_fold_axis(self, axis: str) -> "BuildingFolder":
        """
        Set the axis for folding rotation.

        Args:
            axis: Fold axis ("X", "Y", or "Z").

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If axis is invalid.
        """
        if axis not in ("X", "Y", "Z"):
            raise ValueError(f"Invalid axis '{axis}'. Must be X, Y, or Z.")
        self._fold_axis = axis
        return self

    def set_animation_duration(self, duration: float) -> "BuildingFolder":
        """
        Set the animation duration for one complete fold cycle.

        Args:
            duration: Duration in seconds.

        Returns:
            Self for method chaining.
        """
        self._animation_duration = max(0.1, duration)
        return self

    @staticmethod
    def create_animation_driver(
        duration: float = 5.0,
        frame_start: int = 1,
        frame_end: int = 250,
    ) -> dict[str, Any]:
        """
        Create animation driver configuration.

        Returns configuration for creating Blender drivers that
        animate the folding effect over time.

        Args:
            duration: Duration of one fold cycle in seconds.
            frame_start: Starting frame.
            frame_end: Ending frame.

        Returns:
            Dictionary with driver configuration.

        Note:
            Apply this configuration to the rotation input of the
            folding geometry nodes using Blender's driver system.

        Example:
            >>> config = BuildingFolder.create_animation_driver(duration=5.0)
            >>> # Apply to rotation driver in Blender
        """
        # Calculate frames per fold cycle
        fps = 24  # Default Blender FPS
        frames_per_cycle = int(duration * fps)

        return {
            "type": "rotational",
            "duration": duration,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "frames_per_cycle": frames_per_cycle,
            "expression": f"((frame - {frame_start}) % {frames_per_cycle}) / {frames_per_cycle} * 2 * pi",
            "variables": {
                "frame_start": frame_start,
                "frames_per_cycle": frames_per_cycle,
            },
        }

    def build(
        self,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
        create_material: bool = True,
    ) -> Optional[Node]:
        """
        Build the complete folding effect.

        Combines geometry setup and material creation.

        Args:
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.
            create_material: Whether to create folding material.

        Returns:
            Final folding geometry node, or None.

        Example:
            >>> folder = BuildingFolder(building, instance_count=12)
            >>> result = folder.build(builder)
        """
        # Create geometry
        result = self.setup_folding_geometry(
            self.base_mesh,
            self.instance_count,
            self.radius,
            builder,
            location,
        )

        # Create material if requested
        if create_material and self._material is None:
            self._material = self.create_folding_material(self.instance_count)

        return result


class FoldingAnimator:
    """
    Animation controller for building folding effect.

    Provides methods for setting up keyframe animation and
    controlling the folding parameters over time.

    Example:
        >>> animator = FoldingAnimator(folder)
        >>> animator.setup_keyframes(scene, start_frame=1, end_frame=120)
    """

    def __init__(self, folder: BuildingFolder):
        """
        Initialize the animator.

        Args:
            folder: BuildingFolder instance to animate.
        """
        self.folder = folder
        self._keyframes: list[dict[str, Any]] = []

    def setup_keyframes(
        self,
        scene,
        start_frame: int = 1,
        end_frame: int = 120,
        rotation_axis: str = "Z",
    ) -> "FoldingAnimator":
        """
        Setup keyframes for folding animation.

        Creates keyframe data structure for animating rotation.

        Args:
            scene: Blender scene (for frame rate).
            start_frame: Starting frame.
            end_frame: Ending frame.
            rotation_axis: Axis to rotate around.

        Returns:
            Self for method chaining.

        Note:
            This creates keyframe data. Apply using Blender's
            animation system.
        """
        frame_count = end_frame - start_frame
        rotation_per_frame = (2 * math.pi) / frame_count

        # Create keyframe points
        self._keyframes = [
            {
                "frame": start_frame,
                "rotation": 0.0,
                "easing": "LINEAR",
            },
            {
                "frame": end_frame,
                "rotation": 2 * math.pi,
                "easing": "LINEAR",
            },
        ]

        return self

    def get_rotation_at_frame(self, frame: int) -> float:
        """
        Get rotation value at a specific frame.

        Args:
            frame: Frame number.

        Returns:
            Rotation in radians.
        """
        if not self._keyframes:
            return 0.0

        # Interpolate between keyframes
        for i, kf in enumerate(self._keyframes[:-1]):
            next_kf = self._keyframes[i + 1]
            if kf["frame"] <= frame <= next_kf["frame"]:
                t = (frame - kf["frame"]) / (next_kf["frame"] - kf["frame"])
                return kf["rotation"] + t * (next_kf["rotation"] - kf["rotation"])

        # Outside keyframe range
        if frame < self._keyframes[0]["frame"]:
            return self._keyframes[0]["rotation"]
        return self._keyframes[-1]["rotation"]

    def add_easing(
        self,
        easing_type: str = "EASE_IN_OUT",
    ) -> "FoldingAnimator":
        """
        Add easing to the animation.

        Args:
            easing_type: Type of easing curve:
                - "LINEAR": No easing
                - "EASE_IN": Slow start
                - "EASE_OUT": Slow end
                - "EASE_IN_OUT": Slow start and end

        Returns:
            Self for method chaining.
        """
        # Update keyframes with easing
        for kf in self._keyframes:
            kf["easing"] = easing_type

        return self


def create_folding_effect(
    base_mesh: Object,
    instance_count: int = 12,
    radius: float = 5.0,
    builder: Optional[NodeTreeBuilder] = None,
    animate: bool = True,
    duration: float = 5.0,
) -> Optional[Node]:
    """
    Quick folding effect creation.

    Args:
        base_mesh: Mesh to fold.
        instance_count: Number of instances.
        radius: Folding circle radius.
        builder: NodeTreeBuilder for node creation.
        animate: Whether to setup animation.
        duration: Animation duration in seconds.

    Returns:
        Folding geometry node, or None.

    Example:
        >>> result = create_folding_effect(
        ...     building,
        ...     instance_count=16,
        ...     radius=8.0,
        ...     builder=my_builder
        ... )
    """
    folder = BuildingFolder(base_mesh, instance_count, radius)

    if animate:
        folder.set_animation_duration(duration)

    return folder.build(builder, create_material=True)
