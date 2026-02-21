"""
Hair - Fur/hair systems for procedural hair generation.

Based on CGMatter tutorials for procedural hair. Creates realistic
fur and hair effects using spiral clumps, variation, and noise distortion.

Flow Overview:
    1. Create spiral hair clump using Spiral node
    2. Add random variation to clump parameters
    3. Apply noise distortion for organic look
    4. Convert curve to mesh with profile
    5. Instance on surface points

Usage:
    # Create single hair clump
    clump = HairClumpGenerator.create_spiral_clump(height=2.0, rotations=8.0)

    # Create fur system
    fur = FurSystem(surface_mesh)
    fur.set_density(1000)
    fur.add_clump_variants(5)
    fur.set_scale_range(0.5, 1.5)
    fur.build()
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any, Callable, Optional

from mathutils import Vector

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bpy.types import Material, Node, Object

    from .node_builder import NodeTreeBuilder


# Size distribution curves from CGMatter tutorial
SIZE_CURVES: dict[str, Callable[[float], float]] = {
    "uniform": lambda x: x,
    "bias_small": lambda x: x ** 2,
    "bias_large": lambda x: x ** 0.5,
    "bell": lambda x: 0.5 + 0.5 * math.sin((x - 0.5) * math.pi),
    "exponential": lambda x: 1 - math.exp(-3 * x),
    "sigmoid": lambda x: 1 / (1 + math.exp(-10 * (x - 0.5))),
}


class HairClumpGenerator:
    """
    Generate procedural hair clumps.

    Creates individual hair clumps using spiral curves with
    customizable parameters. Clumps can be varied and distorted
    for realistic appearance.

    The spiral clump is generated using Blender's Spiral node,
    which creates a curve that spirals upward.
    """

    @staticmethod
    def create_spiral_clump(
        height: float = 2.0,
        start_radius: float = 1.0,
        end_radius: float = 0.5,
        rotations: float = 8.0,
        resolution: int = 64,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Create spiral hair clump using Spiral node.

        Creates a spiral curve that tapers from start_radius to
        end_radius while rising to height. The rotations parameter
        controls how many times the spiral twists.

        Flow:
            1. Spiral node -> Creates spiral curve
            2. Set Curve Radius -> Taper from start to end
            3. (Optional) Curve to Mesh with profile

        Args:
            height: Height of the clump (default 2.0).
            start_radius: Radius at the base (default 1.0).
            end_radius: Radius at the tip (default 0.5).
            rotations: Number of spiral rotations (default 8.0).
            resolution: Number of curve points (default 64).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            The spiral curve node, or None if no builder.

        Example:
            >>> clump = HairClumpGenerator.create_spiral_clump(
            ...     height=3.0, rotations=12.0, builder=my_builder
            ... )
        """
        if builder is None:
            return None

        # Create spiral curve using Curve Spiral node
        # Note: Blender 4.x has GeometryNodeCurveSpiral
        spiral = builder.add_node(
            "GeometryNodeCurveSpiral",
            location,
            name="HairSpiral",
        )

        # Set spiral parameters
        spiral.inputs["Resolution"].default_value = resolution
        spiral.inputs["Rotations"].default_value = rotations
        spiral.inputs["Start Radius"].default_value = start_radius
        spiral.inputs["End Radius"].default_value = end_radius
        spiral.inputs["Height"].default_value = height

        return spiral

    @staticmethod
    def add_variation(
        clump_node: Optional[Node] = None,
        seed: int = 0,
        radius_range: tuple[float, float] = (0.5, 1.5),
        rotation_range: tuple[float, float] = (0.5, 1.2),
        height_range: tuple[float, float] = (1.0, 2.0),
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Add random variation to clump parameters.

        Creates random variations based on a seed, useful for
        instancing clumps with varied appearances.

        Args:
            clump_node: The spiral clump node to vary.
            seed: Random seed for variation (default 0).
            radius_range: (min, max) radius multiplier range.
            rotation_range: (min, max) rotation multiplier range.
            height_range: (min, max) height multiplier range.
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node with varied parameters, or None.

        Example:
            >>> varied = HairClumpGenerator.add_variation(
            ...     clump, seed=42, height_range=(0.8, 1.5), builder=my_builder
            ... )
        """
        if builder is None or clump_node is None:
            return None

        # Use Random Value nodes for each parameter
        random.seed(seed)

        # Radius variation
        radius_random = builder.add_node(
            "FunctionNodeRandomValue",
            (location[0], location[1] + 100),
            name="RadiusRandom",
        )
        radius_random.inputs["Min"].default_value = radius_range[0]
        radius_random.inputs["Max"].default_value = radius_range[1]
        radius_random.inputs["ID"].default_value = seed

        # Rotation variation
        rotation_random = builder.add_node(
            "FunctionNodeRandomValue",
            (location[0], location[1] + 50),
            name="RotationRandom",
        )
        rotation_random.inputs["Min"].default_value = rotation_range[0]
        rotation_random.inputs["Max"].default_value = rotation_range[1]
        rotation_random.inputs["ID"].default_value = seed + 1

        # Height variation
        height_random = builder.add_node(
            "FunctionNodeRandomValue",
            (location[0], location[1]),
            name="HeightRandom",
        )
        height_random.inputs["Min"].default_value = height_range[0]
        height_random.inputs["Max"].default_value = height_range[1]
        height_random.inputs["ID"].default_value = seed + 2

        # Apply variations by scaling the curve
        # Note: For full variation, we'd modify the spiral inputs
        # Here we create a transform node
        transform = builder.add_node(
            "GeometryNodeTransform",
            (location[0] + 200, location[1]),
            name="VariationTransform",
        )

        # Connect height random to scale Z
        combine_scale = builder.add_node(
            "ShaderNodeCombineXYZ",
            (location[0] + 100, location[1]),
            name="CombineVariationScale",
        )
        builder.link(height_random.outputs["Value"], combine_scale.inputs["Z"])
        combine_scale.inputs["X"].default_value = 1.0
        combine_scale.inputs["Y"].default_value = 1.0

        builder.link(clump_node.outputs["Curve"], transform.inputs["Geometry"])
        builder.link(combine_scale.outputs["Vector"], transform.inputs["Scale"])

        return transform

    @staticmethod
    def distort(
        clump_node: Optional[Node] = None,
        strength: float = 0.1,
        noise_scale: float = 1.0,
        noise_detail: float = 3.0,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Apply noise distortion to clump.

        Adds organic distortion to hair using noise-based displacement.
        The distortion is applied along the curve length.

        Flow:
            1. Position input -> Noise texture
            2. Scale noise by strength
            3. Set Position with displacement

        Args:
            clump_node: The clump curve node to distort.
            strength: Distortion strength (default 0.1).
            noise_scale: Scale of noise pattern (default 1.0).
            noise_detail: Detail level of noise (default 3.0).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node with distorted curve, or None.

        Example:
            >>> distorted = HairClumpGenerator.distort(
            ...     clump, strength=0.2, noise_scale=2.0, builder=my_builder
            ... )
        """
        if builder is None or clump_node is None:
            return None

        # Get curve position
        position = builder.add_node(
            "GeometryNodeInputPosition",
            (location[0], location[1] + 100),
            name="ClumpPosition",
        )

        # Create noise texture for displacement
        noise = builder.add_node(
            "ShaderNodeTexNoise",
            (location[0] + 100, location[1] + 100),
            name="DistortionNoise",
        )
        noise.inputs["Scale"].default_value = noise_scale
        noise.inputs["Detail"].default_value = noise_detail
        builder.link(position.outputs["Position"], noise.inputs["Vector"])

        # Scale noise to displacement strength
        scale = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 250, location[1] + 100),
            name="ScaleDisplacement",
        )
        scale.operation = "SCALE"
        scale.inputs[1].default_value = strength
        builder.link(noise.outputs["Color"], scale.inputs[0])

        # Add displacement to position
        add_pos = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 400, location[1] + 100),
            name="AddDisplacement",
        )
        add_pos.operation = "ADD"
        builder.link(position.outputs["Position"], add_pos.inputs[0])
        builder.link(scale.outputs[0], add_pos.inputs[1])

        # Set new position
        set_pos = builder.add_node(
            "GeometryNodeSetPosition",
            (location[0] + 550, location[1]),
            name="SetDistortedPosition",
        )
        builder.link(clump_node.outputs.get("Curve", clump_node.outputs.get("Geometry")), set_pos.inputs["Geometry"])
        builder.link(add_pos.outputs[0], set_pos.inputs["Position"])

        return set_pos

    @staticmethod
    def clump_to_mesh(
        clump_node: Optional[Node] = None,
        profile_resolution: int = 3,
        profile_radius: float = 0.02,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Convert curve clump to renderable mesh.

        Uses Curve to Mesh with a circle profile to create
        a renderable hair mesh from the curve.

        Flow:
            1. Curve Circle (profile)
            2. Curve to Mesh

        Args:
            clump_node: The clump curve node.
            profile_resolution: Circle resolution (default 3 for triangle).
            profile_radius: Profile circle radius (default 0.02).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node outputting hair mesh, or None.

        Example:
            >>> mesh = HairClumpGenerator.clump_to_mesh(
            ...     clump, profile_resolution=4, builder=my_builder
            ... )
        """
        if builder is None or clump_node is None:
            return None

        # Create profile circle
        profile = builder.add_node(
            "GeometryNodeCurvePrimitiveCircle",
            (location[0], location[1] - 100),
            name="HairProfile",
        )
        profile.inputs["Resolution"].default_value = profile_resolution
        profile.inputs["Radius"].default_value = profile_radius

        # Curve to mesh
        curve_to_mesh = builder.add_node(
            "GeometryNodeCurveToMesh",
            (location[0] + 150, location[1]),
            name="HairMesh",
        )

        # Get curve output from clump node
        curve_output = clump_node.outputs.get("Curve", clump_node.outputs.get("Geometry"))
        builder.link(curve_output, curve_to_mesh.inputs["Curve"])
        builder.link(profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

        return curve_to_mesh

    @staticmethod
    def create_taper(
        clump_node: Optional[Node] = None,
        base_radius: float = 0.05,
        tip_radius: float = 0.0,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Create taper from base to tip.

        Sets curve radius to taper from base_radius at the bottom
        to tip_radius at the top for realistic hair thickness.

        Args:
            clump_node: The clump curve node.
            base_radius: Radius at base (default 0.05).
            tip_radius: Radius at tip (default 0.0 for point).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node with tapered curve, or None.
        """
        if builder is None or clump_node is None:
            return None

        # Get spline factor (0 at start, 1 at end)
        spline_factor = builder.add_node(
            "GeometryNodeInputSplineCurve",
            (location[0], location[1] + 50),
            name="SplineFactor",
        )

        curve_output = clump_node.outputs.get("Curve", clump_node.outputs.get("Geometry"))
        builder.link(curve_output, spline_factor.inputs["Curve"])

        # Map factor to radius
        map_range = builder.add_node(
            "ShaderNodeMapRange",
            (location[0] + 100, location[1] + 50),
            name="MapTaper",
        )
        map_range.inputs["From Min"].default_value = 0.0
        map_range.inputs["From Max"].default_value = 1.0
        map_range.inputs["To Min"].default_value = base_radius
        map_range.inputs["To Max"].default_value = tip_radius
        builder.link(spline_factor.outputs["Factor"], map_range.inputs["Value"])

        # Set curve radius
        set_radius = builder.add_node(
            "GeometryNodeSetCurveRadius",
            (location[0] + 250, location[1]),
            name="SetTaperRadius",
        )
        builder.link(curve_output, set_radius.inputs["Curve"])
        builder.link(map_range.outputs["Result"], set_radius.inputs["Radius"])

        return set_radius


class FurSystem:
    """
    Complete fur/hair system.

    Provides a fluent interface for building full fur systems with
    density control, clump variants, scale ranges, and materials.

    Example:
        >>> fur = FurSystem(surface_mesh, builder)
        >>> fur.set_density(1000)
        >>> fur.add_clump_variants(5)
        >>> fur.set_scale_range(0.5, 1.5)
        >>> fur.set_size_curve("bias_small")
        >>> fur.build()
    """

    # Size distribution presets
    SIZE_PRESETS = SIZE_CURVES

    def __init__(
        self,
        surface: Optional[Object] = None,
        builder: Optional[NodeTreeBuilder] = None,
    ):
        """
        Initialize the fur system.

        Args:
            surface: Surface mesh to grow fur on.
            builder: NodeTreeBuilder for node creation.
        """
        self.surface = surface
        self.builder = builder
        self._density: int = 1000
        self._clump_variants: int = 3
        self._scale_range: tuple[float, float] = (0.8, 1.2)
        self._height_range: tuple[float, float] = (1.0, 2.0)
        self._size_curve: str = "uniform"
        self._noise_strength: float = 0.1
        self._noise_scale: float = 1.0
        self._profile_resolution: int = 3
        self._profile_radius: float = 0.02
        self._material: Optional[Material] = None
        self._melanin: float = 0.5

    def set_density(self, count: int) -> "FurSystem":
        """
        Set fur density (number of hair clumps).

        Args:
            count: Number of hair clumps.

        Returns:
            Self for method chaining.
        """
        self._density = max(1, count)
        return self

    def add_clump_variants(self, count: int = 3) -> "FurSystem":
        """
        Set number of clump variants for variation.

        Multiple variants are created and randomly selected
        for each hair clump position.

        Args:
            count: Number of variant clumps (default 3).

        Returns:
            Self for method chaining.
        """
        self._clump_variants = max(1, count)
        return self

    def set_scale_range(self, min_scale: float, max_scale: float) -> "FurSystem":
        """
        Set scale range for clump size variation.

        Args:
            min_scale: Minimum scale multiplier.
            max_scale: Maximum scale multiplier.

        Returns:
            Self for method chaining.
        """
        self._scale_range = (min(0.1, min_scale), max(0.1, max_scale))
        return self

    def set_height_range(self, min_height: float, max_height: float) -> "FurSystem":
        """
        Set height range for clumps.

        Args:
            min_height: Minimum clump height.
            max_height: Maximum clump height.

        Returns:
            Self for method chaining.
        """
        self._height_range = (max(0.1, min_height), max(0.1, max_height))
        return self

    def set_size_curve(self, curve_name: str) -> "FurSystem":
        """
        Set size distribution curve.

        Controls how hair sizes are distributed across the surface.

        Args:
            curve_name: Name of size curve:
                - "uniform": Equal distribution
                - "bias_small": More small hairs
                - "bias_large": More large hairs
                - "bell": Bell curve distribution
                - "exponential": Exponential falloff
                - "sigmoid": S-curve distribution

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If curve_name is invalid.
        """
        if curve_name not in self.SIZE_PRESETS:
            raise ValueError(
                f"Invalid size curve '{curve_name}'. "
                f"Available: {', '.join(self.SIZE_PRESETS.keys())}"
            )
        self._size_curve = curve_name
        return self

    def set_noise_distortion(
        self,
        strength: float = 0.1,
        scale: float = 1.0,
    ) -> "FurSystem":
        """
        Set noise distortion parameters.

        Args:
            strength: Distortion strength.
            scale: Noise scale.

        Returns:
            Self for method chaining.
        """
        self._noise_strength = max(0, strength)
        self._noise_scale = max(0.1, scale)
        return self

    def set_profile(self, resolution: int = 3, radius: float = 0.02) -> "FurSystem":
        """
        Set hair profile parameters.

        Args:
            resolution: Profile circle resolution (3=triangle, 4=square, etc.).
            radius: Profile radius.

        Returns:
            Self for method chaining.
        """
        self._profile_resolution = max(3, resolution)
        self._profile_radius = max(0.001, radius)
        return self

    def create_material(self, melanin: float = 0.5) -> "FurSystem":
        """
        Configure hair material with Principled Hair BSDF.

        Args:
            melanin: Melanin amount for hair color (0-1, default 0.5).
                    Lower = lighter hair, higher = darker hair.

        Returns:
            Self for method chaining.
        """
        self._melanin = max(0, min(1, melanin))
        self._material = None  # Will create during build
        return self

    def set_material(self, material: Material) -> "FurSystem":
        """
        Set an existing material for the fur.

        Args:
            material: Material to use for fur.

        Returns:
            Self for method chaining.
        """
        self._material = material
        return self

    def _create_clump_collection(
        self,
        location: tuple[float, float] = (0, 0),
    ) -> list[Node]:
        """
        Create multiple clump variants.

        Args:
            location: Starting location for nodes.

        Returns:
            List of clump variant nodes.
        """
        if self.builder is None:
            return []

        clumps = []
        for i in range(self._clump_variants):
            # Create base spiral clump
            clump = HairClumpGenerator.create_spiral_clump(
                height=self._height_range[1],
                start_radius=1.0,
                end_radius=0.3,
                rotations=8.0 + i * 2,  # Vary rotations per variant
                builder=self.builder,
                location=(location[0] + i * 400, location[1]),
            )

            if clump is None:
                continue

            # Add taper
            tapered = HairClumpGenerator.create_taper(
                clump,
                base_radius=self._profile_radius,
                tip_radius=0.0,
                builder=self.builder,
                location=(location[0] + i * 400 + 100, location[1]),
            )

            # Add distortion
            if self._noise_strength > 0:
                distorted = HairClumpGenerator.distort(
                    tapered or clump,
                    strength=self._noise_strength,
                    noise_scale=self._noise_scale,
                    builder=self.builder,
                    location=(location[0] + i * 400 + 200, location[1]),
                )
                clumps.append(distorted)
            else:
                clumps.append(tapered or clump)

        return clumps

    def build(
        self,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Build the complete fur system.

        Creates clump variants, distributes them on the surface,
        and converts to renderable mesh.

        Flow:
            1. Create clump variants (off-screen)
            2. Distribute points on surface
            3. Instance clumps with random selection and scale
            4. Convert to mesh with profile
            5. Apply material

        Args:
            location: Starting position for main nodes.

        Returns:
            Final fur mesh node, or None.

        Example:
            >>> fur = FurSystem(surface, builder)
            >>> fur.set_density(1000).add_clump_variants(5)
            >>> result = fur.build()
        """
        if self.builder is None:
            return None

        # Get surface geometry
        if self.surface is not None:
            obj_info = self.builder.add_node(
                "GeometryNodeObjectInfo",
                (location[0] - 200, location[1]),
                name="SurfaceInput",
            )
            obj_info.inputs[0].default_value = self.surface
            obj_info.transform_space = "RELATIVE"
            surface_geo = obj_info.outputs["Geometry"]
        else:
            group_input = self.builder.add_group_input((location[0] - 200, location[1]))
            surface_geo = group_input.outputs.get("Geometry", group_input.outputs[0])

        # Create clump variants (store as collection for instancing)
        # In practice, we'd create these as a geometry collection
        # Here we create them inline for simplicity

        # For a full implementation, we'd:
        # 1. Create clump variants in a separate node group
        # 2. Join them into a collection
        # 3. Use Instance on Points with Pick Instance

        # Simplified: Create single clump and vary via transform
        base_clump = HairClumpGenerator.create_spiral_clump(
            height=self._height_range[1],
            start_radius=1.0,
            end_radius=0.3,
            rotations=8.0,
            builder=self.builder,
            location=(location[0] - 400, location[1] - 200),
        )

        if base_clump is None:
            return None

        # Add taper to base clump
        tapered = HairClumpGenerator.create_taper(
            base_clump,
            base_radius=self._profile_radius,
            builder=self.builder,
            location=(location[0] - 300, location[1] - 200),
        )

        # Add distortion
        if self._noise_strength > 0:
            distorted = HairClumpGenerator.distort(
                tapered or base_clump,
                strength=self._noise_strength,
                noise_scale=self._noise_scale,
                builder=self.builder,
                location=(location[0] - 200, location[1] - 200),
            )
            clump_geo = distorted
        else:
            clump_geo = tapered or base_clump

        # Convert to mesh for instancing
        clump_mesh = HairClumpGenerator.clump_to_mesh(
            clump_geo,
            profile_resolution=self._profile_resolution,
            profile_radius=self._profile_radius,
            builder=self.builder,
            location=(location[0] - 100, location[1] - 200),
        )

        # Distribute points on surface
        distribute = self.builder.add_node(
            "GeometryNodeDistributePointsOnFaces",
            (location[0], location[1]),
            name="DistributeFurPoints",
        )
        distribute.inputs["Density"].default_value = self._density
        self.builder.link(surface_geo, distribute.inputs["Mesh"])

        # Get normal for proper orientation
        normal = self.builder.add_node(
            "GeometryNodeInputNormal",
            (location[0] + 100, location[1] + 100),
            name="SurfaceNormal",
        )

        # Align rotation to normal
        align = self.builder.add_node(
            "FunctionNodeAlignEulerToVector",
            (location[0] + 200, location[1] + 100),
            name="AlignToNormal",
        )
        align.inputs["Axis"].default_value = "Z"
        self.builder.link(normal.outputs["Normal"], align.inputs["Vector"])

        # Random scale based on size curve
        random_scale = self.builder.add_node(
            "FunctionNodeRandomValue",
            (location[0] + 100, location[1] - 100),
            name="RandomScale",
        )
        random_scale.inputs["Min"].default_value = self._scale_range[0]
        random_scale.inputs["Max"].default_value = self._scale_range[1]

        # Apply size curve transformation
        # For simplicity, use a float curve node
        float_curve = self.builder.add_node(
            "ShaderNodeFloatCurve",
            (location[0] + 200, location[1] - 100),
            name="SizeCurve",
        )
        self.builder.link(random_scale.outputs["Value"], float_curve.inputs["Value"])

        # Instance clumps on points
        instance = self.builder.add_node(
            "GeometryNodeInstanceOnPoints",
            (location[0] + 300, location[1]),
            name="InstanceFur",
        )
        self.builder.link(distribute.outputs["Points"], instance.inputs["Points"])

        if clump_mesh is not None:
            self.builder.link(clump_mesh.outputs["Mesh"], instance.inputs["Instance"])

        self.builder.link(align.outputs["Rotation"], instance.inputs["Rotation"])
        self.builder.link(float_curve.outputs["Value"], instance.inputs["Scale"])

        # Realize instances
        realize = self.builder.add_node(
            "GeometryNodeRealizeInstances",
            (location[0] + 500, location[1]),
            name="RealizeFur",
        )
        self.builder.link(instance.outputs["Instances"], realize.inputs["Geometry"])

        # Set material if configured
        if self._material is not None or self._melanin > 0:
            set_material = self.builder.add_node(
                "GeometryNodeSetMaterial",
                (location[0] + 700, location[1]),
                name="SetFurMaterial",
            )
            if self._material is not None:
                set_material.inputs["Material"].default_value = self._material

            self.builder.link(realize.outputs["Geometry"], set_material.inputs["Geometry"])
            return set_material

        return realize


def create_fur(
    surface: Object,
    density: int = 1000,
    height: float = 1.0,
    builder: Optional[NodeTreeBuilder] = None,
) -> Optional[Node]:
    """
    Quick fur creation with sensible defaults.

    Args:
        surface: Surface mesh to grow fur on.
        density: Number of hair clumps.
        height: Hair height.
        builder: NodeTreeBuilder for node creation.

    Returns:
        Fur mesh node, or None.

    Example:
        >>> fur = create_fur(my_surface, density=2000, builder=my_builder)
    """
    return (
        FurSystem(surface, builder)
        .set_density(density)
        .set_height_range(height * 0.8, height * 1.2)
        .add_clump_variants(3)
        .set_noise_distortion(0.1, 1.0)
        .build()
    )
