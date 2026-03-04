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

        # Create clump variants for Pick Instance selection
        # Implements the CGMatter "Single Random Value" pattern where each
        # variant has slightly different characteristics (rotations, distortion)
        b = self.builder
        clumps: list[Node] = []
        clump_start_x = location[0] - 800

        for i in range(self._clump_variants):
            clump_x = clump_start_x + i * 200
            clump_y = location[1] - 350

            # Create base spiral clump with variant-specific rotations
            clump = HairClumpGenerator.create_spiral_clump(
                height=self._height_range[1],
                start_radius=1.0,
                end_radius=0.3,
                rotations=8.0 + i * 2,  # Vary rotations per variant for diversity
                builder=b,
                location=(clump_x, clump_y),
            )

            if clump is None:
                continue

            # Add taper for realistic hair thickness
            tapered = HairClumpGenerator.create_taper(
                clump,
                base_radius=self._profile_radius,
                tip_radius=0.0,
                builder=b,
                location=(clump_x + 100, clump_y),
            )

            # Add distortion with variant-specific strength for more variety
            if self._noise_strength > 0:
                current = HairClumpGenerator.distort(
                    tapered or clump,
                    strength=self._noise_strength * (0.8 + i * 0.15),
                    noise_scale=self._noise_scale,
                    builder=b,
                    location=(clump_x + 150, clump_y),
                )
            else:
                current = tapered or clump

            # Convert to mesh for instancing
            clump_mesh = HairClumpGenerator.clump_to_mesh(
                current,
                profile_resolution=self._profile_resolution,
                profile_radius=self._profile_radius,
                builder=b,
                location=(clump_x + 200, clump_y),
            )

            if clump_mesh is not None:
                clumps.append(clump_mesh)

        if not clumps:
            return None

        # Join all clump variants for Pick Instance selection
        # When Pick Instance is enabled on Instance on Points, each point
        # randomly selects one element from the joined geometry
        if len(clumps) > 1:
            join_clumps = b.add_node(
                "GeometryNodeJoinGeometry",
                (location[0] - 300, location[1] - 350),
                name="JoinClumpVariants",
            )
            for clump in clumps:
                b.link(clump.outputs["Mesh"], join_clumps.inputs["Geometry"])
            clump_source = join_clumps.outputs["Geometry"]
        else:
            clump_source = clumps[0].outputs["Mesh"]

        # Distribute points on surface
        distribute = b.add_node(
            "GeometryNodeDistributePointsOnFaces",
            (location[0], location[1]),
            name="DistributeFurPoints",
        )
        distribute.inputs["Density"].default_value = self._density
        b.link(surface_geo, distribute.inputs["Mesh"])

        # Get normal for proper orientation
        normal = b.add_node(
            "GeometryNodeInputNormal",
            (location[0] + 100, location[1] + 100),
            name="SurfaceNormal",
        )

        # Align rotation to normal
        align = b.add_node(
            "FunctionNodeAlignEulerToVector",
            (location[0] + 200, location[1] + 100),
            name="AlignToNormal",
        )
        align.inputs["Axis"].default_value = "Z"
        b.link(normal.outputs["Normal"], align.inputs["Vector"])

        # Random scale based on size curve
        random_scale = b.add_node(
            "FunctionNodeRandomValue",
            (location[0] + 100, location[1] - 100),
            name="RandomScale",
        )
        random_scale.inputs["Min"].default_value = self._scale_range[0]
        random_scale.inputs["Max"].default_value = self._scale_range[1]

        # Apply size curve transformation
        float_curve = b.add_node(
            "ShaderNodeFloatCurve",
            (location[0] + 200, location[1] - 100),
            name="SizeCurve",
        )
        b.link(random_scale.outputs["Value"], float_curve.inputs["Value"])

        # Random selection index for Pick Instance (CGMatter pattern)
        # Each point gets a random index to select which clump variant to use
        index_node = b.add_node(
            "GeometryNodeInputIndex",
            (location[0] + 150, location[1] - 200),
            name="PointIndex",
        )

        random_variant = b.add_node(
            "FunctionNodeRandomValue",
            (location[0] + 250, location[1] - 200),
            name="RandomVariantIndex",
        )
        random_variant.inputs["Min"].default_value = 0
        random_variant.inputs["Max"].default_value = self._clump_variants - 1
        b.link(index_node.outputs["Index"], random_variant.inputs["ID"])

        # Instance clumps on points with Pick Instance enabled
        # Pick Instance allows each point to select a different element from joined geometry
        instance = b.add_node(
            "GeometryNodeInstanceOnPoints",
            (location[0] + 400, location[1]),
            name="InstanceFur",
        )
        b.link(distribute.outputs["Points"], instance.inputs["Points"])

        # Connect clump variants - this enables Pick Instance behavior
        b.link(clump_source, instance.inputs["Instance"])

        b.link(align.outputs["Rotation"], instance.inputs["Rotation"])
        b.link(float_curve.outputs["Value"], instance.inputs["Scale"])

        # Connect random variant selection to instance indices
        # This tells each point which clump variant to pick
        b.link(random_variant.outputs["Value"], instance.inputs["Selection Indices"])

        # Realize instances
        realize = b.add_node(
            "GeometryNodeRealizeInstances",
            (location[0] + 600, location[1]),
            name="RealizeFur",
        )
        b.link(instance.outputs["Instances"], realize.inputs["Geometry"])

        # Set material if configured
        if self._material is not None or self._melanin > 0:
            set_material = b.add_node(
                "GeometryNodeSetMaterial",
                (location[0] + 800, location[1]),
                name="SetFurMaterial",
            )
            if self._material is not None:
                set_material.inputs["Material"].default_value = self._material

            b.link(realize.outputs["Geometry"], set_material.inputs["Geometry"])
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


def create_hair_material(
    name: str = "HairMaterial",
    melanin: float = 0.5,
    roughness: float = 0.3,
    radial_roughness: float = 0.4,
    coat: float = 0.0,
    base_color: Optional[tuple[float, float, float, float]] = None,
) -> "Material":
    """
    Create Principled Hair BSDF material for realistic hair rendering.

    This creates a hair material using Blender's Principled Hair BSDF shader,
    which provides physically-based hair shading with melanin control.

    Args:
        name: Material name (default "HairMaterial").
        melanin: Hair darkness (0=white, 1=black, default 0.5).
        roughness: Fiber texture amount (default 0.3).
        radial_roughness: Cross-section detail (default 0.4).
        coat: Optional shine/coat layer (default 0.0).
        base_color: Override color tuple (r, g, b, a). If provided,
                   melanin is ignored and color mode is used.

    Returns:
        Configured material with Principled Hair BSDF.

    Example:
        >>> # Brown hair
        >>> mat = create_hair_material("BrownHair", melanin=0.7)
        >>> # Custom colored hair
        >>> mat = create_hair_material("RedHair", base_color=(0.8, 0.2, 0.1, 1.0))
    """
    import bpy

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output node
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    # Principled Hair BSDF
    hair = nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.location = (300, 0)

    if base_color is not None:
        # Use direct color mode
        hair.inputs["Parametrization"].default_value = "COLOR"
        hair.inputs["Color"].default_value = base_color
    else:
        # Use melanin mode for realistic hair
        hair.inputs["Parametrization"].default_value = "MELANIN"
        hair.inputs["Melanin"].default_value = melanin

    hair.inputs["Roughness"].default_value = roughness
    hair.inputs["Radial Roughness"].default_value = radial_roughness
    hair.inputs["Coat"].default_value = coat

    links.new(hair.outputs["BSDF"], output.inputs["Surface"])

    return mat


def create_stylized_hair_material(
    name: str = "StylizedHair",
    color: tuple[float, float, float, float] = (0.8, 0.6, 0.4, 1.0),
    emission_strength: float = 1.0,
) -> "Material":
    """
    Create emission-based stylized hair material for NPR/toon rendering.

    This creates a simple emission material for stylized cartoon-like hair,
    useful for anime or low-poly art styles.

    Args:
        name: Material name (default "StylizedHair").
        color: Emission color (r, g, b, a).
        emission_strength: Emission strength (default 1.0).

    Returns:
        Configured material with Emission shader.

    Example:
        >>> # Bright stylized hair
        >>> mat = create_stylized_hair_material(
        ...     "AnimeHair",
        ...     color=(1.0, 0.8, 0.6, 1.0),
        ...     emission_strength=2.0
        ... )
    """
    import bpy

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output node
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)

    # Emission shader
    emission = nodes.new("ShaderNodeEmission")
    emission.location = (100, 0)
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = emission_strength

    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    return mat


class HairCurvesBuilder:
    """
    Modern curves workflow builder for Blender 5.x hair systems.

    Uses Blender's native Hair Curves nodes (Generate Hair Curves, Interpolate
    Hair Curves, Clump, Curl, Frizz, etc.) for a more integrated hair workflow.

    This builder targets the modern Hair Curves data type rather than
    converting curves to mesh immediately, enabling:
    - Native hair curve editing in the viewport
    - Better integration with hair physics/simulation
    - Access to specialized hair deformation nodes
    - Curve-scoped attributes for shading

    Flow:
        1. Generate or interpolate hair curves from surface
        2. Apply deformation chain (clump, curl, frizz, smooth)
        3. Set curve profile for thickness control
        4. Optionally convert to mesh for rendering

    Example:
        >>> builder = HairCurvesBuilder(surface_mesh, node_builder)
        >>> builder.generate_from_surface(density=500, length=0.3)
        >>> builder.add_clumping(factor=0.5, shape=0.3)
        >>> builder.add_curl(radius=0.02, frequency=3)
        >>> builder.add_frizz(amount=0.1)
        >>> builder.set_profile(base_radius=0.01, tip_radius=0.0)
        >>> result = builder.build()
    """

    def __init__(
        self,
        surface: Optional[Object] = None,
        builder: Optional[NodeTreeBuilder] = None,
    ):
        """
        Initialize the hair curves builder.

        Args:
            surface: Surface mesh to grow hair on.
            builder: NodeTreeBuilder for node creation.
        """
        self.surface = surface
        self.builder = builder
        self._density: int = 500
        self._length: float = 0.3
        self._points_per_curve: int = 8
        self._clump_factor: float = 0.0
        self._clump_shape: float = 0.5
        self._curl_radius: float = 0.0
        self._curl_frequency: float = 1.0
        self._frizz_amount: float = 0.0
        self._frizz_frequency: float = 1.0
        self._smooth_factor: float = 0.0
        self._smooth_iterations: int = 1
        self._base_radius: float = 0.01
        self._tip_radius: float = 0.0
        self._profile_shape: str = "taper"  # taper, uniform, bulb
        self._guides: Optional[Object] = None
        self._interpolation_amount: int = 50
        self._noise_scale: float = 1.0
        self._noise_factor: float = 0.0
        self._seed: int = 0
        self._convert_to_mesh: bool = False
        self._material: Optional[Material] = None

    def generate_from_surface(
        self,
        density: int = 500,
        length: float = 0.3,
        points_per_curve: int = 8,
    ) -> "HairCurvesBuilder":
        """
        Configure hair generation from surface distribution.

        Uses Distribute Points on Faces + Generate Hair Curves for
        procedural fur/hair coverage.

        Args:
            density: Number of hair curves to generate.
            length: Length of each hair curve.
            points_per_curve: Resolution of each curve (default 8).

        Returns:
            Self for method chaining.
        """
        self._density = max(1, density)
        self._length = max(0.01, length)
        self._points_per_curve = max(2, points_per_curve)
        self._guides = None  # Clear guides if using surface generation
        return self

    def interpolate_from_guides(
        self,
        guides: Object,
        amount: int = 50,
    ) -> "HairCurvesBuilder":
        """
        Configure hair interpolation from guide curves.

        Uses Interpolate Hair Curves node for controlled hairstyles.
        Guide curves can be drawn manually or procedurally generated.

        Args:
            guides: Object containing guide curves.
            amount: Number of curves to interpolate per guide.

        Returns:
            Self for method chaining.
        """
        self._guides = guides
        self._interpolation_amount = max(1, amount)
        return self

    def set_seed(self, seed: int) -> "HairCurvesBuilder":
        """
        Set random seed for reproducible results.

        Args:
            seed: Random seed value.

        Returns:
            Self for method chaining.
        """
        self._seed = seed
        return self

    def add_clumping(
        self,
        factor: float = 0.5,
        shape: float = 0.5,
    ) -> "HairCurvesBuilder":
        """
        Add hair clumping effect.

        Clumping groups nearby hair strands together, creating natural
        hair clusters. Higher factor = more pronounced grouping.

        Args:
            factor: Clumping strength (0-1, default 0.5).
                   0 = no clumping, 1 = maximum clumping.
            shape: Shape of clump (0-1, default 0.5).
                   0 = linear, 1 = curved toward tip.

        Returns:
            Self for method chaining.
        """
        self._clump_factor = max(0, min(1, factor))
        self._clump_shape = max(0, min(1, shape))
        return self

    def add_curl(
        self,
        radius: float = 0.02,
        frequency: float = 3.0,
    ) -> "HairCurvesBuilder":
        """
        Add curl effect to hair curves.

        Creates spiral curls along the hair length using Curl Hair Curves node.

        Args:
            radius: Curl radius in Blender units (default 0.02).
            frequency: Number of curl rotations (default 3.0).

        Returns:
            Self for method chaining.
        """
        self._curl_radius = max(0, radius)
        self._curl_frequency = max(0.1, frequency)
        return self

    def add_frizz(
        self,
        amount: float = 0.1,
        frequency: float = 1.0,
    ) -> "HairCurvesBuilder":
        """
        Add frizz/flyaway effect to hair curves.

        Creates natural frizz and flyaways using Frizz Hair Curves node.

        Args:
            amount: Frizz amount (0-1, default 0.1).
            frequency: Frizz frequency/detail level (default 1.0).

        Returns:
            Self for method chaining.
        """
        self._frizz_amount = max(0, min(1, amount))
        self._frizz_frequency = max(0.1, frequency)
        return self

    def add_noise(
        self,
        factor: float = 0.1,
        scale: float = 1.0,
    ) -> "HairCurvesBuilder":
        """
        Add noise displacement to hair curves.

        Uses Noise Hair Curves node for organic variation.

        Args:
            factor: Noise displacement factor (default 0.1).
            scale: Noise texture scale (default 1.0).

        Returns:
            Self for method chaining.
        """
        self._noise_factor = max(0, factor)
        self._noise_scale = max(0.1, scale)
        return self

    def add_smoothing(
        self,
        factor: float = 0.5,
        iterations: int = 2,
    ) -> "HairCurvesBuilder":
        """
        Add smoothing to hair curves.

        Smooths out kinks and sharp angles using Smooth Hair Curves node.

        Args:
            factor: Smoothing strength (0-1, default 0.5).
            iterations: Number of smoothing passes (default 2).

        Returns:
            Self for method chaining.
        """
        self._smooth_factor = max(0, min(1, factor))
        self._smooth_iterations = max(1, iterations)
        return self

    def set_profile(
        self,
        base_radius: float = 0.01,
        tip_radius: float = 0.0,
        shape: str = "taper",
    ) -> "HairCurvesBuilder":
        """
        Set hair curve profile (thickness along length).

        Uses Set Hair Curve Profile node for precise radius control.

        Args:
            base_radius: Radius at hair root (default 0.01).
            tip_radius: Radius at hair tip (default 0.0 for point).
            shape: Profile shape preset:
                - "taper": Linear taper from base to tip
                - "uniform": Constant radius
                - "bulb": Thicker in middle, tapered at ends

        Returns:
            Self for method chaining.
        """
        self._base_radius = max(0.001, base_radius)
        self._tip_radius = max(0, tip_radius)
        self._profile_shape = shape
        return self

    def convert_to_mesh(
        self,
        profile_resolution: int = 3,
    ) -> "HairCurvesBuilder":
        """
        Configure conversion to mesh for rendering.

        Converts hair curves to mesh geometry using Curve to Mesh node.
        Required for some render engines that don't support hair curves natively.

        Args:
            profile_resolution: Profile circle resolution (default 3 for triangle).

        Returns:
            Self for method chaining.
        """
        self._convert_to_mesh = True
        self._profile_resolution = profile_resolution
        return self

    def keep_as_curves(self) -> "HairCurvesBuilder":
        """
        Keep output as hair curves (no mesh conversion).

        This is the default behavior. Use for native hair curve workflows
        with viewport editing and physics support.

        Returns:
            Self for method chaining.
        """
        self._convert_to_mesh = False
        return self

    def set_material(self, material: Material) -> "HairCurvesBuilder":
        """
        Set material for the hair.

        Args:
            material: Material to apply.

        Returns:
            Self for method chaining.
        """
        self._material = material
        return self

    def build(
        self,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Build the hair curves system.

        Creates the complete node tree for hair curve generation,
        deformation, and optional mesh conversion.

        Flow:
            1. Generate/Interpolate hair curves
            2. Apply deformation chain (clump, curl, frizz, noise, smooth)
            3. Set curve profile
            4. Optionally convert to mesh
            5. Apply material

        Args:
            location: Starting position for main nodes.

        Returns:
            Final hair node, or None.

        Example:
            >>> builder = HairCurvesBuilder(surface, node_builder)
            >>> builder.generate_from_surface(500, 0.3)
            >>> builder.add_clumping(0.5).add_curl(0.02, 3)
            >>> builder.set_profile(0.01, 0.0)
            >>> result = builder.build()
        """
        if self.builder is None:
            return None

        b = self.builder
        current_x = location[0]
        current_y = location[1]

        # Get surface geometry
        if self.surface is not None:
            obj_info = b.add_node(
                "GeometryNodeObjectInfo",
                (current_x - 300, current_y),
                name="SurfaceInput",
            )
            obj_info.inputs[0].default_value = self.surface
            obj_info.transform_space = "RELATIVE"
            surface_geo = obj_info.outputs["Geometry"]
        else:
            group_input = b.add_group_input((current_x - 300, current_y))
            surface_geo = group_input.outputs.get("Geometry", group_input.outputs[0])

        # Step 1: Generate or Interpolate hair curves
        if self._guides is not None:
            # Interpolate from guide curves
            guides_info = b.add_node(
                "GeometryNodeObjectInfo",
                (current_x - 300, current_y - 200),
                name="GuidesInput",
            )
            guides_info.inputs[0].default_value = self._guides
            guides_info.transform_space = "RELATIVE"

            hair_curves = b.add_node(
                "GeometryNodeInterpolateHairCurves",
                (current_x, current_y),
                name="InterpolateHairCurves",
            )
            b.link(guides_info.outputs["Geometry"], hair_curves.inputs["Guides"])
            b.link(surface_geo, hair_curves.inputs["Surface"])
            hair_curves.inputs["Amount"].default_value = self._interpolation_amount
        else:
            # Generate from surface distribution
            distribute = b.add_node(
                "GeometryNodeDistributePointsOnFaces",
                (current_x - 150, current_y),
                name="DistributeHairPoints",
            )
            distribute.inputs["Density"].default_value = self._density
            distribute.inputs["Seed"].default_value = self._seed
            b.link(surface_geo, distribute.inputs["Mesh"])

            hair_curves = b.add_node(
                "GeometryNodeGenerateHairCurves",
                (current_x, current_y),
                name="GenerateHairCurves",
            )
            b.link(distribute.outputs["Points"], hair_curves.inputs["Points"])
            b.link(surface_geo, hair_curves.inputs["Surface"])
            hair_curves.inputs["Curve Length"].default_value = self._length
            hair_curves.inputs["Points per Curve"].default_value = self._points_per_curve

        current_output = hair_curves.outputs["Curves"]
        current_x += 200

        # Step 2: Apply deformation chain

        # Clumping
        if self._clump_factor > 0:
            clump = b.add_node(
                "GeometryNodeClumpHairCurves",
                (current_x, current_y),
                name="ClumpHair",
            )
            clump.inputs["Clump Factor"].default_value = self._clump_factor
            clump.inputs["Clump Shape"].default_value = self._clump_shape
            b.link(current_output, clump.inputs["Curves"])
            current_output = clump.outputs["Curves"]
            current_x += 150

        # Curling
        if self._curl_radius > 0:
            curl = b.add_node(
                "GeometryNodeCurlHairCurves",
                (current_x, current_y),
                name="CurlHair",
            )
            curl.inputs["Curl Radius"].default_value = self._curl_radius
            curl.inputs["Curl Frequency"].default_value = self._curl_frequency
            b.link(current_output, curl.inputs["Curves"])
            current_output = curl.outputs["Curves"]
            current_x += 150

        # Frizz
        if self._frizz_amount > 0:
            frizz = b.add_node(
                "GeometryNodeFrizzHairCurves",
                (current_x, current_y),
                name="FrizzHair",
            )
            frizz.inputs["Frizz Amount"].default_value = self._frizz_amount
            frizz.inputs["Frizz Frequency"].default_value = self._frizz_frequency
            b.link(current_output, frizz.inputs["Curves"])
            current_output = frizz.outputs["Curves"]
            current_x += 150

        # Noise displacement
        if self._noise_factor > 0:
            noise = b.add_node(
                "GeometryNodeNoiseHairCurves",
                (current_x, current_y),
                name="NoiseHair",
            )
            noise.inputs["Noise Factor"].default_value = self._noise_factor
            noise.inputs["Noise Scale"].default_value = self._noise_scale
            b.link(current_output, noise.inputs["Curves"])
            current_output = noise.outputs["Curves"]
            current_x += 150

        # Smoothing
        if self._smooth_factor > 0:
            smooth = b.add_node(
                "GeometryNodeSmoothHairCurves",
                (current_x, current_y),
                name="SmoothHair",
            )
            smooth.inputs["Smooth Factor"].default_value = self._smooth_factor
            smooth.inputs["Iterations"].default_value = self._smooth_iterations
            b.link(current_output, smooth.inputs["Curves"])
            current_output = smooth.outputs["Curves"]
            current_x += 150

        # Step 3: Set curve profile
        profile = b.add_node(
            "GeometryNodeSetHairCurveProfile",
            (current_x, current_y),
            name="SetHairProfile",
        )

        # Configure profile based on shape preset
        if self._profile_shape == "uniform":
            # Constant radius
            profile.inputs["Base Radius"].default_value = self._base_radius
            profile.inputs["Tip Radius"].default_value = self._base_radius
        elif self._profile_shape == "bulb":
            # Thicker in middle - use curve node for control
            profile.inputs["Base Radius"].default_value = self._base_radius
            profile.inputs["Tip Radius"].default_value = self._tip_radius
        else:  # taper (default)
            profile.inputs["Base Radius"].default_value = self._base_radius
            profile.inputs["Tip Radius"].default_value = self._tip_radius

        b.link(current_output, profile.inputs["Curves"])
        current_output = profile.outputs["Curves"]
        current_x += 200

        # Step 4: Optional mesh conversion
        if self._convert_to_mesh:
            # Create profile circle for mesh conversion
            profile_circle = b.add_node(
                "GeometryNodeCurvePrimitiveCircle",
                (current_x, current_y - 100),
                name="MeshProfile",
            )
            profile_circle.inputs["Resolution"].default_value = getattr(
                self, "_profile_resolution", 3
            )
            profile_circle.inputs["Radius"].default_value = self._base_radius

            curve_to_mesh = b.add_node(
                "GeometryNodeCurveToMesh",
                (current_x + 150, current_y),
                name="HairToMesh",
            )
            b.link(current_output, curve_to_mesh.inputs["Curve"])
            b.link(profile_circle.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
            current_output = curve_to_mesh.outputs["Mesh"]
            current_x += 300

        # Step 5: Apply material if configured
        if self._material is not None:
            set_material = b.add_node(
                "GeometryNodeSetMaterial",
                (current_x, current_y),
                name="SetHairMaterial",
            )
            set_material.inputs["Material"].default_value = self._material
            b.link(current_output, set_material.inputs["Geometry"])
            current_output = set_material.outputs["Geometry"]
            current_x += 150

        # Step 6: Connect to Group Output
        group_output = b.add_group_output((current_x, current_y))
        b.link(current_output, group_output.inputs.get("Geometry", group_output.inputs[0]))

        return group_output


class MultiLayerFur:
    """
    Multi-layer realistic fur system with undercoat, guard hairs, and whisker layers.

    Creates realistic animal fur with three distinct layers:
    - Undercoat: Dense, short, curly base fur
    - Guard hairs: Longer, straighter protective hairs
    - Whiskers: Very long, sparse sensory hairs

    Each layer has independent control over density, length, curl, and other properties.

    Flow:
        1. Create undercoat layer (short, dense, curly)
        2. Create guard hair layer (longer, sparser, straighter)
        3. Create whisker layer (very long, very sparse)
        4. Join all layers together
        5. Apply materials

    Example:
        >>> fur = MultiLayerFur(surface_mesh, node_builder)
        >>> fur.set_undercoat(density=2000, length=0.05, curl=0.8)
        >>> fur.set_guard_hairs(density=200, length=0.15, curl=0.1)
        >>> fur.set_whiskers(density=15, length=0.4)
        >>> fur.set_region_mask("back", vertex_group)  # Optional regional control
        >>> result = fur.build()
    """

    def __init__(
        self,
        surface: Optional[Object] = None,
        builder: Optional[NodeTreeBuilder] = None,
    ):
        """
        Initialize the multi-layer fur system.

        Args:
            surface: Surface mesh to grow fur on.
            builder: NodeTreeBuilder for node creation.
        """
        self.surface = surface
        self.builder = builder

        # Undercoat parameters
        self._undercoat_density: int = 2000
        self._undercoat_length: float = 0.05
        self._undercoat_curl: float = 0.8
        self._undercoat_clump: float = 0.3
        self._undercoat_enabled: bool = True

        # Guard hair parameters
        self._guard_density: int = 200
        self._guard_length: float = 0.15
        self._guard_curl: float = 0.1
        self._guard_clump: float = 0.1
        self._guard_enabled: bool = True

        # Whisker parameters
        self._whisker_density: int = 15
        self._whisker_length: float = 0.4
        self._whisker_curl: float = 0.0
        self._whisker_enabled: bool = True

        # Global parameters
        self._seed: int = 0
        self._noise_strength: float = 0.1
        self._profile_radius: float = 0.005
        self._material: Optional[Material] = None
        self._undercoat_material: Optional[Material] = None
        self._guard_material: Optional[Material] = None
        self._whisker_material: Optional[Material] = None

    def set_undercoat(
        self,
        density: int = 2000,
        length: float = 0.05,
        curl: float = 0.8,
        clump: float = 0.3,
    ) -> "MultiLayerFur":
        """
        Configure undercoat layer.

        The undercoat is the dense, short, curly base fur that provides
        insulation and volume.

        Args:
            density: Number of undercoat hairs (default 2000).
            length: Undercoat hair length (default 0.05).
            curl: Curl amount (0-1, default 0.8 for very curly).
            clump: Clumping factor (0-1, default 0.3).

        Returns:
            Self for method chaining.
        """
        self._undercoat_density = max(1, density)
        self._undercoat_length = max(0.01, length)
        self._undercoat_curl = max(0, min(1, curl))
        self._undercoat_clump = max(0, min(1, clump))
        self._undercoat_enabled = True
        return self

    def set_guard_hairs(
        self,
        density: int = 200,
        length: float = 0.15,
        curl: float = 0.1,
        clump: float = 0.1,
    ) -> "MultiLayerFur":
        """
        Configure guard hair layer.

        Guard hairs are longer, straighter hairs that protect the undercoat
        and give the fur its overall direction and appearance.

        Args:
            density: Number of guard hairs (default 200).
            length: Guard hair length (default 0.15).
            curl: Curl amount (0-1, default 0.1 for nearly straight).
            clump: Clumping factor (0-1, default 0.1).

        Returns:
            Self for method chaining.
        """
        self._guard_density = max(1, density)
        self._guard_length = max(0.01, length)
        self._guard_curl = max(0, min(1, curl))
        self._guard_clump = max(0, min(1, clump))
        self._guard_enabled = True
        return self

    def set_whiskers(
        self,
        density: int = 15,
        length: float = 0.4,
    ) -> "MultiLayerFur":
        """
        Configure whisker layer.

        Whiskers are very long, sparse sensory hairs typically found around
        the muzzle/face area of animals.

        Args:
            density: Number of whiskers (default 15).
            length: Whisker length (default 0.4).

        Returns:
            Self for method chaining.
        """
        self._whisker_density = max(1, density)
        self._whisker_length = max(0.01, length)
        self._whisker_enabled = True
        return self

    def enable_undercoat(self, enabled: bool = True) -> "MultiLayerFur":
        """Enable or disable undercoat layer."""
        self._undercoat_enabled = enabled
        return self

    def enable_guard_hairs(self, enabled: bool = True) -> "MultiLayerFur":
        """Enable or disable guard hair layer."""
        self._guard_enabled = enabled
        return self

    def enable_whiskers(self, enabled: bool = True) -> "MultiLayerFur":
        """Enable or disable whisker layer."""
        self._whisker_enabled = enabled
        return self

    def set_seed(self, seed: int) -> "MultiLayerFur":
        """Set random seed for reproducible results."""
        self._seed = seed
        return self

    def set_noise(self, strength: float = 0.1) -> "MultiLayerFur":
        """Set noise distortion strength for all layers."""
        self._noise_strength = max(0, strength)
        return self

    def set_profile_radius(self, radius: float = 0.005) -> "MultiLayerFur":
        """Set base profile radius for all hair strands."""
        self._profile_radius = max(0.001, radius)
        return self

    def set_material(self, material: Material) -> "MultiLayerFur":
        """Set material for all fur layers."""
        self._material = material
        return self

    def set_layer_materials(
        self,
        undercoat: Optional[Material] = None,
        guard: Optional[Material] = None,
        whiskers: Optional[Material] = None,
    ) -> "MultiLayerFur":
        """
        Set separate materials for each fur layer.

        Args:
            undercoat: Material for undercoat.
            guard: Material for guard hairs.
            whiskers: Material for whiskers.

        Returns:
            Self for method chaining.
        """
        self._undercoat_material = undercoat
        self._guard_material = guard
        self._whisker_material = whiskers
        return self

    def _create_fur_layer(
        self,
        b: "NodeTreeBuilder",
        surface_geo: "Node",
        density: int,
        length: float,
        curl: float,
        clump: float,
        seed_offset: int,
        layer_name: str,
        start_location: tuple[float, float],
        material: Optional[Material] = None,
    ) -> Optional[Node]:
        """
        Create a single fur layer using spiral clump pattern.

        Internal helper method for building individual fur layers.
        """
        # Distribute points
        distribute = b.add_node(
            "GeometryNodeDistributePointsOnFaces",
            start_location,
            name=f"Distribute{layer_name}",
        )
        distribute.inputs["Density"].default_value = density
        distribute.inputs["Seed"].default_value = self._seed + seed_offset
        b.link(surface_geo, distribute.inputs["Mesh"])

        # Create spiral clump
        spiral = b.add_node(
            "GeometryNodeCurveSpiral",
            (start_location[0] + 150, start_location[1]),
            name=f"Spiral{layer_name}",
        )
        spiral.inputs["Resolution"].default_value = 16
        spiral.inputs["Rotations"].default_value = 3 + curl * 8
        spiral.inputs["Start Radius"].default_value = 0.3
        spiral.inputs["End Radius"].default_value = 0.05
        spiral.inputs["Height"].default_value = length

        # Add taper
        taper = b.add_node(
            "GeometryNodeSetCurveRadius",
            (start_location[0] + 300, start_location[1]),
            name=f"Taper{layer_name}",
        )
        b.link(spiral.outputs["Curve"], taper.inputs["Curve"])
        taper.inputs["Radius"].default_value = self._profile_radius

        # Add noise if enabled
        if self._noise_strength > 0:
            noise = b.add_node(
                "GeometryNodeSetPosition",
                (start_location[0] + 450, start_location[1]),
                name=f"Noise{layer_name}",
            )
            b.link(taper.outputs["Curve"], noise.inputs["Geometry"])
            # Noise displacement would be connected here
            current = noise
            current_x = start_location[0] + 600
        else:
            current = taper
            current_x = start_location[0] + 450

        # Convert to mesh
        profile_circle = b.add_node(
            "GeometryNodeCurvePrimitiveCircle",
            (current_x, start_location[1] - 100),
            name=f"Profile{layer_name}",
        )
        profile_circle.inputs["Resolution"].default_value = 3
        profile_circle.inputs["Radius"].default_value = self._profile_radius

        curve_to_mesh = b.add_node(
            "GeometryNodeCurveToMesh",
            (current_x + 100, start_location[1]),
            name=f"Mesh{layer_name}",
        )
        current_output = current.outputs.get("Curve", current.outputs.get("Geometry"))
        b.link(current_output, curve_to_mesh.inputs["Curve"])
        b.link(profile_circle.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

        # Instance on distributed points
        instance = b.add_node(
            "GeometryNodeInstanceOnPoints",
            (current_x + 250, start_location[1]),
            name=f"Instance{layer_name}",
        )
        b.link(distribute.outputs["Points"], instance.inputs["Points"])
        b.link(curve_to_mesh.outputs["Mesh"], instance.inputs["Instance"])

        # Random scale
        random_scale = b.add_node(
            "FunctionNodeRandomValue",
            (current_x + 150, start_location[1] - 150),
            name=f"Scale{layer_name}",
        )
        random_scale.inputs["Min"].default_value = 0.7
        random_scale.inputs["Max"].default_value = 1.3
        random_scale.inputs["ID"].default_value = self._seed + seed_offset
        b.link(random_scale.outputs["Value"], instance.inputs["Scale"])

        # Align to normal
        normal = b.add_node(
            "GeometryNodeInputNormal",
            (current_x + 100, start_location[1] + 100),
        )
        align = b.add_node(
            "FunctionNodeAlignEulerToVector",
            (current_x + 200, start_location[1] + 100),
        )
        align.inputs["Axis"].default_value = "Z"
        b.link(normal.outputs["Normal"], align.inputs["Vector"])
        b.link(align.outputs["Rotation"], instance.inputs["Rotation"])

        # Realize instances
        realize = b.add_node(
            "GeometryNodeRealizeInstances",
            (current_x + 400, start_location[1]),
            name=f"Realize{layer_name}",
        )
        b.link(instance.outputs["Instances"], realize.inputs["Geometry"])

        # Apply material if specified
        mat_to_use = material or self._material
        if mat_to_use is not None:
            set_mat = b.add_node(
                "GeometryNodeSetMaterial",
                (current_x + 550, start_location[1]),
                name=f"Material{layer_name}",
            )
            set_mat.inputs["Material"].default_value = mat_to_use
            b.link(realize.outputs["Geometry"], set_mat.inputs["Geometry"])
            return set_mat

        return realize

    def build(
        self,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Build the complete multi-layer fur system.

        Creates all enabled layers and joins them together.

        Args:
            location: Starting position for nodes.

        Returns:
            Final joined fur geometry node, or None.
        """
        if self.builder is None:
            return None

        b = self.builder

        # Get surface geometry
        if self.surface is not None:
            obj_info = b.add_node(
                "GeometryNodeObjectInfo",
                (location[0] - 300, location[1]),
                name="SurfaceInput",
            )
            obj_info.inputs[0].default_value = self.surface
            obj_info.transform_space = "RELATIVE"
            surface_geo = obj_info.outputs["Geometry"]
        else:
            group_input = b.add_group_input((location[0] - 300, location[1]))
            surface_geo = group_input.outputs.get("Geometry", group_input.outputs[0])

        layers: list[Node] = []
        layer_y_offset = 0

        # Create undercoat layer
        if self._undercoat_enabled:
            undercoat = self._create_fur_layer(
                b,
                surface_geo,
                self._undercoat_density,
                self._undercoat_length,
                self._undercoat_curl,
                self._undercoat_clump,
                0,
                "Undercoat",
                (location[0], location[1] + layer_y_offset),
                self._undercoat_material,
            )
            if undercoat is not None:
                layers.append(undercoat)
            layer_y_offset -= 400

        # Create guard hair layer
        if self._guard_enabled:
            guard = self._create_fur_layer(
                b,
                surface_geo,
                self._guard_density,
                self._guard_length,
                self._guard_curl,
                self._guard_clump,
                1000,
                "GuardHair",
                (location[0], location[1] + layer_y_offset),
                self._guard_material,
            )
            if guard is not None:
                layers.append(guard)
            layer_y_offset -= 400

        # Create whisker layer
        if self._whisker_enabled:
            whisker = self._create_fur_layer(
                b,
                surface_geo,
                self._whisker_density,
                self._whisker_length,
                self._whisker_curl,
                0.0,
                2000,
                "Whisker",
                (location[0], location[1] + layer_y_offset),
                self._whisker_material,
            )
            if whisker is not None:
                layers.append(whisker)

        # Join all layers
        if not layers:
            return None

        if len(layers) == 1:
            return layers[0]

        join = b.add_node(
            "GeometryNodeJoinGeometry",
            (location[0] + 1200, location[1]),
            name="JoinFurLayers",
        )

        for layer in layers:
            output = layer.outputs.get("Geometry", layer.outputs.get("Mesh"))
            if output is not None:
                b.link(output, join.inputs["Geometry"])

        return join


def create_fur_ball(
    radius: float = 1.0,
    density: int = 3000,
    hair_length: float = 0.3,
    builder: Optional[NodeTreeBuilder] = None,
    location: tuple[float, float] = (0, 0),
) -> Optional[Node]:
    """
    Quick fur ball creation - convenient test asset.

    Creates a sphere with procedural fur for quick testing and
    visualization of fur parameters.

    Args:
        radius: Sphere radius (default 1.0).
        density: Fur density (default 3000).
        hair_length: Hair strand length (default 0.3).
        builder: NodeTreeBuilder for node creation.
        location: Starting position for nodes.

    Returns:
        Final fur ball node, or None.

    Example:
        >>> # Quick test fur ball
        >>> fur_ball = create_fur_ball(radius=2.0, density=5000, builder=my_builder)
    """
    if builder is None:
        return None

    b = builder
    current_x = location[0]

    # Create base sphere
    sphere = b.add_node(
        "GeometryNodeMeshUVSphere",
        location,
        name="FurBallBase",
    )
    sphere.inputs["Radius"].default_value = radius
    sphere.inputs["Segments"].default_value = 32
    sphere.inputs["Rings"].default_value = 16

    current_x += 200

    # Create fur system using FurSystem
    fur = FurSystem(None, b)
    fur.set_density(density)
    fur.set_height_range(hair_length * 0.7, hair_length * 1.3)
    fur.add_clump_variants(5)
    fur.set_scale_range(0.6, 1.4)
    fur.set_noise_distortion(0.15, 1.5)
    fur.set_profile(resolution=3, radius=0.01)

    # Build fur on the sphere
    # We need to connect the sphere output to the fur input
    # Since FurSystem.build() expects a surface, we need to handle this

    # Get sphere geometry
    sphere_output = sphere.outputs["Mesh"]

    # Distribute points on sphere
    distribute = b.add_node(
        "GeometryNodeDistributePointsOnFaces",
        (current_x, location[1]),
        name="DistributeFurPoints",
    )
    distribute.inputs["Density"].default_value = density
    b.link(sphere_output, distribute.inputs["Mesh"])

    current_x += 200

    # Create multiple clump variants
    clumps: list[Node] = []
    for i in range(5):
        clump_x = location[0] - 400
        clump_y = location[1] - 400 + i * 150

        spiral = b.add_node(
            "GeometryNodeCurveSpiral",
            (clump_x, clump_y),
            name=f"Clump{i}",
        )
        spiral.inputs["Resolution"].default_value = 24
        spiral.inputs["Rotations"].default_value = 6 + i * 2
        spiral.inputs["Start Radius"].default_value = 0.4
        spiral.inputs["End Radius"].default_value = 0.05
        spiral.inputs["Height"].default_value = hair_length

        # Taper
        taper = HairClumpGenerator.create_taper(
            spiral,
            base_radius=0.01,
            tip_radius=0.0,
            builder=b,
            location=(clump_x + 100, clump_y),
        )

        # Distort
        distorted = HairClumpGenerator.distort(
            taper or spiral,
            strength=0.15,
            noise_scale=1.5,
            builder=b,
            location=(clump_x + 200, clump_y),
        )

        # To mesh
        mesh = HairClumpGenerator.clump_to_mesh(
            distorted,
            profile_resolution=3,
            profile_radius=0.01,
            builder=b,
            location=(clump_x + 350, clump_y),
        )

        if mesh is not None:
            clumps.append(mesh)

    # Join clumps
    if len(clumps) > 1:
        join_clumps = b.add_node(
            "GeometryNodeJoinGeometry",
            (location[0] - 200, location[1] - 400),
            name="JoinClumps",
        )
        for clump in clumps:
            b.link(clump.outputs["Mesh"], join_clumps.inputs["Geometry"])
        clump_source = join_clumps.outputs["Geometry"]
    elif clumps:
        clump_source = clumps[0].outputs["Mesh"]
    else:
        return sphere

    # Get normal
    normal = b.add_node(
        "GeometryNodeInputNormal",
        (current_x, location[1] + 100),
    )

    # Align rotation
    align = b.add_node(
        "FunctionNodeAlignEulerToVector",
        (current_x + 100, location[1] + 100),
    )
    align.inputs["Axis"].default_value = "Z"
    b.link(normal.outputs["Normal"], align.inputs["Vector"])

    # Random scale
    random_scale = b.add_node(
        "FunctionNodeRandomValue",
        (current_x, location[1] - 100),
    )
    random_scale.inputs["Min"].default_value = 0.6
    random_scale.inputs["Max"].default_value = 1.4

    # Random variant selection
    index = b.add_node(
        "GeometryNodeInputIndex",
        (current_x, location[1] - 200),
    )
    random_variant = b.add_node(
        "FunctionNodeRandomValue",
        (current_x + 100, location[1] - 200),
    )
    random_variant.inputs["Min"].default_value = 0
    random_variant.inputs["Max"].default_value = 4
    b.link(index.outputs["Index"], random_variant.inputs["ID"])

    current_x += 200

    # Instance on points
    instance = b.add_node(
        "GeometryNodeInstanceOnPoints",
        (current_x, location[1]),
        name="InstanceFur",
    )
    b.link(distribute.outputs["Points"], instance.inputs["Points"])
    b.link(clump_source, instance.inputs["Instance"])
    b.link(align.outputs["Rotation"], instance.inputs["Rotation"])
    b.link(random_scale.outputs["Value"], instance.inputs["Scale"])
    b.link(random_variant.outputs["Value"], instance.inputs["Selection Indices"])

    current_x += 200

    # Realize instances
    realize = b.add_node(
        "GeometryNodeRealizeInstances",
        (current_x, location[1]),
        name="RealizeFur",
    )
    b.link(instance.outputs["Instances"], realize.inputs["Geometry"])

    current_x += 200

    # Join sphere and fur
    join_all = b.add_node(
        "GeometryNodeJoinGeometry",
        (current_x, location[1]),
        name="JoinFurBall",
    )
    b.link(sphere_output, join_all.inputs["Geometry"])
    b.link(realize.outputs["Geometry"], join_all.inputs["Geometry"])

    return join_all
