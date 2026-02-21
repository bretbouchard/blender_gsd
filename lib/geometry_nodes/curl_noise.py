"""
CurlNoise - Divergence-free curl noise for particle simulations.

Based on CGMatter tutorials for curl noise particles. Curl noise creates
swirling, vortex-like motion that is divergence-free, making it ideal
for fluid-like particle effects without accumulation.

Mathematical Foundation:
    For a scalar field s(x,y,z):
        2D Curl: curl(s) = (ds/dy, -ds/dx, 0)

    For a vector field V = (Vx, Vy, Vz):
        3D Curl: curl(V) = (dVz/dy - dVy/dz, dVx/dz - dVz/dx, dVy/dx - dVx/dy)

Usage:
    # Calculate curl from a scalar field
    curl = CurlNoise.curl_2d(scalar_func, position)

    # Create curl from Blender noise texture
    curl = CurlNoise.from_noise_texture(position, scale=1.0, detail=3)

    # Build a curl-based particle system
    system = CurlParticleSystem(particle_count=1000)
    system.add_layer(CurlNoise.from_noise_texture, scale=1.0, strength=0.5)
    system.build_node_tree(builder)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Callable, Optional

from mathutils import Vector

if TYPE_CHECKING:
    from bpy.types import Node, NodeTree

    from .node_builder import NodeTreeBuilder


class CurlNoise:
    """
    Divergence-free curl noise for particles and fluid-like effects.

    Curl noise is computed by taking the curl (rotational) of a scalar
    or vector field. The resulting vector field is guaranteed to be
    divergence-free, making it perfect for fluid-like motion without
    particle accumulation or depletion.

    All methods are static and can be used directly or within a
    NodeTreeBuilder context for geometry nodes.
    """

    @staticmethod
    def curl_2d(
        scalar_field: Callable[[Vector], float],
        position: Vector,
        epsilon: float = 0.001,
    ) -> Vector:
        """
        Calculate 2D curl from a scalar field.

        For a field V with only Z component (height field):
            Curl X = dVz/dY
            Curl Y = -dVz/dX
            Curl Z = 0

        Args:
            scalar_field: Function that takes a Vector and returns a float.
                         Represents a height or scalar field in 2D.
            position: The position to calculate curl at.
            epsilon: Finite difference step size (default 0.001).

        Returns:
            3D Vector representing the curl (X, Y, 0).

        Example:
            >>> def height_field(pos):
            ...     return math.sin(pos.x) * math.cos(pos.y)
            >>> curl = CurlNoise.curl_2d(height_field, Vector((1, 2, 0)))
        """
        # Partial derivative with respect to Y
        pos_y_plus = position + Vector((0, epsilon, 0))
        pos_y_minus = position - Vector((0, epsilon, 0))
        dVz_dY = (scalar_field(pos_y_plus) - scalar_field(pos_y_minus)) / (2 * epsilon)

        # Partial derivative with respect to X
        pos_x_plus = position + Vector((epsilon, 0, 0))
        pos_x_minus = position - Vector((epsilon, 0, 0))
        dVz_dX = (scalar_field(pos_x_plus) - scalar_field(pos_x_minus)) / (2 * epsilon)

        return Vector((dVz_dY, -dVz_dX, 0.0))

    @staticmethod
    def curl_3d(
        vector_field: Callable[[Vector], Vector],
        position: Vector,
        epsilon: float = 0.001,
    ) -> Vector:
        """
        Calculate full 3D curl from a vector field.

        Uses the mathematical definition:
            Curl X = dVz/dY - dVy/dZ
            Curl Y = dVx/dZ - dVz/dX
            Curl Z = dVy/dX - dVx/dY

        Args:
            vector_field: Function that takes a Vector and returns a Vector.
                         The vector field to compute curl of.
            position: The position to calculate curl at.
            epsilon: Finite difference step size (default 0.001).

        Returns:
            3D Vector representing the curl.

        Example:
            >>> def velocity_field(pos):
            ...     return Vector((math.sin(pos.y), math.cos(pos.z), pos.x))
            >>> curl = CurlNoise.curl_3d(velocity_field, Vector((1, 2, 3)))
        """
        # Compute partial derivatives using central differences
        # dVx/dY
        vx_y_plus = vector_field(position + Vector((0, epsilon, 0))).x
        vx_y_minus = vector_field(position - Vector((0, epsilon, 0))).x
        dVx_dY = (vx_y_plus - vx_y_minus) / (2 * epsilon)

        # dVx/dZ
        vx_z_plus = vector_field(position + Vector((0, 0, epsilon))).x
        vx_z_minus = vector_field(position - Vector((0, 0, epsilon))).x
        dVx_dZ = (vx_z_plus - vx_z_minus) / (2 * epsilon)

        # dVy/dX
        vy_x_plus = vector_field(position + Vector((epsilon, 0, 0))).y
        vy_x_minus = vector_field(position - Vector((epsilon, 0, 0))).y
        dVy_dX = (vy_x_plus - vy_x_minus) / (2 * epsilon)

        # dVy/dZ
        vy_z_plus = vector_field(position + Vector((0, 0, epsilon))).y
        vy_z_minus = vector_field(position - Vector((0, 0, epsilon))).y
        dVy_dZ = (vy_z_plus - vy_z_minus) / (2 * epsilon)

        # dVz/dX
        vz_x_plus = vector_field(position + Vector((epsilon, 0, 0))).z
        vz_x_minus = vector_field(position - Vector((epsilon, 0, 0))).z
        dVz_dX = (vz_x_plus - vz_x_minus) / (2 * epsilon)

        # dVz/dY
        vz_y_plus = vector_field(position + Vector((0, epsilon, 0))).z
        vz_y_minus = vector_field(position - Vector((0, epsilon, 0))).z
        dVz_dY = (vz_y_plus - vz_y_minus) / (2 * epsilon)

        # Compute curl components
        curl_x = dVz_dY - dVy_dZ
        curl_y = dVx_dZ - dVz_dX
        curl_z = dVy_dX - dVx_dY

        return Vector((curl_x, curl_y, curl_z))

    @staticmethod
    def from_noise_texture(
        position: Vector,
        scale: float = 1.0,
        detail: int = 3,
        distortion: float = 0.0,
    ) -> Vector:
        """
        Calculate curl from Blender noise texture parameters.

        This is a pure Python approximation of Blender's noise texture.
        For actual geometry nodes, use from_noise_texture_gn() to build
        the proper node tree.

        Args:
            position: World position to sample at.
            scale: Scale of the noise pattern (default 1.0).
            detail: Detail level/octaves (default 3).
            distortion: Distortion amount (default 0.0).

        Returns:
            Curl vector approximating Blender noise texture.

        Note:
            This is a Python approximation. For accurate results in
            geometry nodes, use the node-based version.
        """
        # Simple Perlin-like noise approximation using sine waves
        # This is a simplified approximation - real Blender noise is more complex
        def noise_component(pos: Vector, octaves: int) -> float:
            """Multi-octave noise approximation."""
            value = 0.0
            amplitude = 1.0
            frequency = 1.0
            max_value = 0.0

            for _ in range(octaves):
                # Simple pseudo-noise using sine waves
                n = (
                    math.sin(pos.x * frequency * 1.7 + pos.y * 0.8)
                    + math.sin(pos.y * frequency * 2.1 + pos.z * 0.6)
                    + math.sin(pos.z * frequency * 1.5 + pos.x * 0.9)
                ) / 3.0
                value += n * amplitude
                max_value += amplitude
                amplitude *= 0.5
                frequency *= 2.0

            return value / max_value

        # Scale position
        scaled_pos = position * scale

        # Create a scalar field from noise
        def noise_field(p: Vector) -> float:
            return noise_component(p + Vector((distortion * 0.1, 0, 0)), detail)

        # Calculate curl from this noise field
        return CurlNoise.curl_3d(
            lambda p: Vector((noise_field(p), noise_field(p + Vector((100, 0, 0))), noise_field(p + Vector((0, 100, 0))))),
            scaled_pos,
        )

    @staticmethod
    def from_noise_texture_gn(
        builder: NodeTreeBuilder,
        position_socket,
        scale: float = 1.0,
        detail: float = 3.0,
        distortion: float = 0.0,
        location: tuple[float, float] = (0, 0),
    ) -> tuple[Node, Node, Node]:
        """
        Build curl noise nodes using Blender's Noise Texture.

        Creates a node setup that computes curl from Blender's noise
        texture using finite differences within geometry nodes.

        Flow:
            Position -> Scale -> Noise Texture (3x for X, Y, Z offsets)
            -> Combine XYZ -> Curl Calculation -> Vector Math

        Args:
            builder: NodeTreeBuilder for node creation.
            position_socket: Socket providing position data.
            scale: Scale of the noise pattern (default 1.0).
            detail: Detail level (default 3.0).
            distortion: Distortion amount (default 0.0).
            location: Position for the first node.

        Returns:
            Tuple of (curl_vector_node, noise_x_node, noise_y_node, noise_z_node).

        Example:
            >>> curl_node, *_ = CurlNoise.from_noise_texture_gn(
            ...     builder, position_node.outputs["Position"], scale=2.0
            ... )
            >>> # curl_node.outputs["Vector"] contains the curl
        """
        epsilon = 0.001

        # Create scale vector
        scale_node = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0], location[1]),
            name="ScalePosition",
        )
        scale_node.operation = "SCALE"
        scale_node.inputs[1].default_value = scale

        builder.link(position_socket, scale_node.inputs[0])

        # Create epsilon offsets for finite differences
        # We need to sample noise at 6 positions for full 3D curl
        offset_x_plus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] + 150),
            name="OffsetXPlus",
        )
        offset_x_plus.operation = "ADD"
        offset_x_plus.inputs[1].default_value = (epsilon, 0, 0)

        offset_x_minus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] + 100),
            name="OffsetXMinus",
        )
        offset_x_minus.operation = "ADD"
        offset_x_minus.inputs[1].default_value = (-epsilon, 0, 0)

        offset_y_plus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] + 50),
            name="OffsetYPlus",
        )
        offset_y_plus.operation = "ADD"
        offset_y_plus.inputs[1].default_value = (0, epsilon, 0)

        offset_y_minus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1]),
            name="OffsetYMinus",
        )
        offset_y_minus.operation = "ADD"
        offset_y_minus.inputs[1].default_value = (0, -epsilon, 0)

        offset_z_plus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] - 50),
            name="OffsetZPlus",
        )
        offset_z_plus.operation = "ADD"
        offset_z_plus.inputs[1].default_value = (0, 0, epsilon)

        offset_z_minus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] - 100),
            name="OffsetZMinus",
        )
        offset_z_minus.operation = "ADD"
        offset_z_minus.inputs[1].default_value = (0, 0, -epsilon)

        # Connect scale to all offsets
        builder.link(scale_node.outputs[0], offset_x_plus.inputs[0])
        builder.link(scale_node.outputs[0], offset_x_minus.inputs[0])
        builder.link(scale_node.outputs[0], offset_y_plus.inputs[0])
        builder.link(scale_node.outputs[0], offset_y_minus.inputs[0])
        builder.link(scale_node.outputs[0], offset_z_plus.inputs[0])
        builder.link(scale_node.outputs[0], offset_z_minus.inputs[0])

        # Create noise textures for each offset
        def add_noise_texture(loc, name):
            noise = builder.add_node(
                "ShaderNodeTexNoise",
                loc,
                name=name,
            )
            noise.inputs["Scale"].default_value = 1.0
            noise.inputs["Detail"].default_value = detail
            noise.inputs["Distortion"].default_value = distortion
            return noise

        # For curl, we sample a scalar field (using Fac output)
        noise_x_plus = add_noise_texture((location[0] + 250, location[1] + 150), "NoiseXPlus")
        noise_x_minus = add_noise_texture((location[0] + 250, location[1] + 100), "NoiseXMinus")
        noise_y_plus = add_noise_texture((location[0] + 250, location[1] + 50), "NoiseYPlus")
        noise_y_minus = add_noise_texture((location[0] + 250, location[1]), "NoiseYMinus")
        noise_z_plus = add_noise_texture((location[0] + 250, location[1] - 50), "NoiseZPlus")
        noise_z_minus = add_noise_texture((location[0] + 250, location[1] - 100), "NoiseZMinus")

        # Connect offsets to noise textures
        builder.link(offset_x_plus.outputs[0], noise_x_plus.inputs["Vector"])
        builder.link(offset_x_minus.outputs[0], noise_x_minus.inputs["Vector"])
        builder.link(offset_y_plus.outputs[0], noise_y_plus.inputs["Vector"])
        builder.link(offset_y_minus.outputs[0], noise_y_minus.inputs["Vector"])
        builder.link(offset_z_plus.outputs[0], noise_z_plus.inputs["Vector"])
        builder.link(offset_z_minus.outputs[0], noise_z_minus.inputs["Vector"])

        # Calculate partial derivatives
        # dN/dX = (N(x+e) - N(x-e)) / 2e
        div_2e = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] + 200),
            name="DivideBy2Epsilon",
        )
        div_2e.operation = "DIVIDE"
        div_2e.inputs[1].default_value = 2 * epsilon

        # dN/dX
        dN_dX = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] + 150),
            name="dN_dX",
        )
        dN_dX.operation = "SUBTRACT"
        builder.link(noise_x_plus.outputs["Fac"], dN_dX.inputs[0])
        builder.link(noise_x_minus.outputs["Fac"], dN_dX.inputs[1])

        dN_dX_div = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] + 150),
            name="dN_dX_Div",
        )
        dN_dX_div.operation = "DIVIDE"
        dN_dX_div.inputs[1].default_value = 2 * epsilon
        builder.link(dN_dX.outputs[0], dN_dX_div.inputs[0])

        # dN/dY
        dN_dY = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] + 50),
            name="dN_dY",
        )
        dN_dY.operation = "SUBTRACT"
        builder.link(noise_y_plus.outputs["Fac"], dN_dY.inputs[0])
        builder.link(noise_y_minus.outputs["Fac"], dN_dY.inputs[1])

        dN_dY_div = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] + 50),
            name="dN_dY_Div",
        )
        dN_dY_div.operation = "DIVIDE"
        dN_dY_div.inputs[1].default_value = 2 * epsilon
        builder.link(dN_dY.outputs[0], dN_dY_div.inputs[0])

        # dN/dZ
        dN_dZ = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] - 50),
            name="dN_dZ",
        )
        dN_dZ.operation = "SUBTRACT"
        builder.link(noise_z_plus.outputs["Fac"], dN_dZ.inputs[0])
        builder.link(noise_z_minus.outputs["Fac"], dN_dZ.inputs[1])

        dN_dZ_div = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] - 50),
            name="dN_dZ_Div",
        )
        dN_dZ_div.operation = "DIVIDE"
        dN_dZ_div.inputs[1].default_value = 2 * epsilon
        builder.link(dN_dZ.outputs[0], dN_dZ_div.inputs[0])

        # For 2D curl: curl = (dN/dY, -dN/dX, 0)
        # Negate dN/dX
        neg_dN_dX = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 550, location[1] + 150),
            name="Neg_dN_dX",
        )
        neg_dN_dX.operation = "MULTIPLY"
        neg_dN_dX.inputs[1].default_value = -1.0
        builder.link(dN_dX_div.outputs[0], neg_dN_dX.inputs[0])

        # Combine into curl vector
        curl = builder.add_node(
            "ShaderNodeCombineXYZ",
            (location[0] + 650, location[1]),
            name="CurlVector",
        )
        builder.link(dN_dY_div.outputs[0], curl.inputs["X"])
        builder.link(neg_dN_dX.outputs[0], curl.inputs["Y"])
        curl.inputs["Z"].default_value = 0.0

        return curl, noise_x_plus, noise_y_plus

    @staticmethod
    def from_voronoi_distance(
        position: Vector,
        scale: float = 1.0,
    ) -> Vector:
        """
        Calculate curl from Voronoi distance field.

        Voronoi-based curl creates interesting cellular swirling patterns
        centered around Voronoi cell centers.

        Args:
            position: World position to sample at.
            scale: Scale of the Voronoi pattern (default 1.0).

        Returns:
            Curl vector based on Voronoi distance gradient.

        Note:
            This is a Python approximation. For geometry nodes,
            use from_voronoi_distance_gn() for accurate results.
        """
        # Approximate Voronoi distance field
        # Using a simple hash function for cell centers
        def hash_to_float(x: float, y: float) -> float:
            """Simple hash function for pseudo-random values."""
            return (math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1.0

        def voronoi_distance(p: Vector) -> float:
            """Approximate Voronoi distance."""
            cell_x = math.floor(p.x)
            cell_y = math.floor(p.y)

            min_dist = float("inf")
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    neighbor_x = cell_x + dx
                    neighbor_y = cell_y + dy

                    # Random point in cell
                    point_x = neighbor_x + hash_to_float(neighbor_x, neighbor_y)
                    point_y = neighbor_y + hash_to_float(neighbor_y, neighbor_x)

                    dist = math.sqrt((p.x - point_x) ** 2 + (p.y - point_y) ** 2)
                    min_dist = min(min_dist, dist)

            return min_dist

        scaled_pos = position * scale

        # Calculate curl of the distance field
        return CurlNoise.curl_2d(voronoi_distance, scaled_pos)

    @staticmethod
    def from_voronoi_distance_gn(
        builder: NodeTreeBuilder,
        position_socket,
        scale: float = 1.0,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Build curl noise from Voronoi texture in geometry nodes.

        Uses Blender's Voronoi texture Distance output as a scalar field
        and computes its curl.

        Args:
            builder: NodeTreeBuilder for node creation.
            position_socket: Socket providing position data.
            scale: Scale of the Voronoi pattern (default 1.0).
            location: Position for the first node.

        Returns:
            The curl vector node.
        """
        epsilon = 0.001

        # Scale position
        scale_node = builder.add_node(
            "ShaderNodeVectorMath",
            location,
            name="ScaleVoronoi",
        )
        scale_node.operation = "SCALE"
        scale_node.inputs[1].default_value = scale
        builder.link(position_socket, scale_node.inputs[0])

        # Create offset nodes for finite differences
        offset_y_plus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] + 100),
            name="OffsetYPlus",
        )
        offset_y_plus.operation = "ADD"
        offset_y_plus.inputs[1].default_value = (0, epsilon, 0)

        offset_y_minus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] + 50),
            name="OffsetYMinus",
        )
        offset_y_minus.operation = "ADD"
        offset_y_minus.inputs[1].default_value = (0, -epsilon, 0)

        offset_x_plus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1]),
            name="OffsetXPlus",
        )
        offset_x_plus.operation = "ADD"
        offset_x_plus.inputs[1].default_value = (epsilon, 0, 0)

        offset_x_minus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] - 50),
            name="OffsetXMinus",
        )
        offset_x_minus.operation = "ADD"
        offset_x_minus.inputs[1].default_value = (-epsilon, 0, 0)

        # Connect scaled position to offsets
        builder.link(scale_node.outputs[0], offset_y_plus.inputs[0])
        builder.link(scale_node.outputs[0], offset_y_minus.inputs[0])
        builder.link(scale_node.outputs[0], offset_x_plus.inputs[0])
        builder.link(scale_node.outputs[0], offset_x_minus.inputs[0])

        # Create Voronoi textures
        voronoi_y_plus = builder.add_node(
            "ShaderNodeTexVoronoi",
            (location[0] + 250, location[1] + 100),
            name="VoronoiYPlus",
        )
        voronoi_y_plus.inputs["Scale"].default_value = 1.0

        voronoi_y_minus = builder.add_node(
            "ShaderNodeTexVoronoi",
            (location[0] + 250, location[1] + 50),
            name="VoronoiYMinus",
        )
        voronoi_y_minus.inputs["Scale"].default_value = 1.0

        voronoi_x_plus = builder.add_node(
            "ShaderNodeTexVoronoi",
            (location[0] + 250, location[1]),
            name="VoronoiXPlus",
        )
        voronoi_x_plus.inputs["Scale"].default_value = 1.0

        voronoi_x_minus = builder.add_node(
            "ShaderNodeTexVoronoi",
            (location[0] + 250, location[1] - 50),
            name="VoronoiXMinus",
        )
        voronoi_x_minus.inputs["Scale"].default_value = 1.0

        # Connect offsets to Voronoi
        builder.link(offset_y_plus.outputs[0], voronoi_y_plus.inputs["Vector"])
        builder.link(offset_y_minus.outputs[0], voronoi_y_minus.inputs["Vector"])
        builder.link(offset_x_plus.outputs[0], voronoi_x_plus.inputs["Vector"])
        builder.link(offset_x_minus.outputs[0], voronoi_x_minus.inputs["Vector"])

        # Calculate derivatives
        dD_dY = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] + 75),
            name="dDistance_dY",
        )
        dD_dY.operation = "SUBTRACT"
        builder.link(voronoi_y_plus.outputs["Distance"], dD_dY.inputs[0])
        builder.link(voronoi_y_minus.outputs["Distance"], dD_dY.inputs[1])

        dD_dY_div = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] + 75),
            name="dD_dY_Div",
        )
        dD_dY_div.operation = "DIVIDE"
        dD_dY_div.inputs[1].default_value = 2 * epsilon
        builder.link(dD_dY.outputs[0], dD_dY_div.inputs[0])

        dD_dX = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] - 25),
            name="dDistance_dX",
        )
        dD_dX.operation = "SUBTRACT"
        builder.link(voronoi_x_plus.outputs["Distance"], dD_dX.inputs[0])
        builder.link(voronoi_x_minus.outputs["Distance"], dD_dX.inputs[1])

        dD_dX_div = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] - 25),
            name="dD_dX_Div",
        )
        dD_dX_div.operation = "DIVIDE"
        dD_dX_div.inputs[1].default_value = 2 * epsilon
        builder.link(dD_dX.outputs[0], dD_dX_div.inputs[0])

        # Negate dD/dX
        neg_dD_dX = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 520, location[1] - 25),
            name="Neg_dD_dX",
        )
        neg_dD_dX.operation = "MULTIPLY"
        neg_dD_dX.inputs[1].default_value = -1.0
        builder.link(dD_dX_div.outputs[0], neg_dD_dX.inputs[0])

        # Combine into curl
        curl = builder.add_node(
            "ShaderNodeCombineXYZ",
            (location[0] + 600, location[1]),
            name="VoronoiCurl",
        )
        builder.link(dD_dY_div.outputs[0], curl.inputs["X"])
        builder.link(neg_dD_dX.outputs[0], curl.inputs["Y"])
        curl.inputs["Z"].default_value = 0.0

        return curl

    @staticmethod
    def from_wave_texture(
        position: Vector,
        scale: float = 1.0,
        distortion: float = 1.0,
    ) -> Vector:
        """
        Calculate curl from wave texture (creates periodic whirlpools).

        Wave texture curl creates regular spiral patterns that repeat,
        useful for stylized effects.

        Args:
            position: World position to sample at.
            scale: Scale of the wave pattern (default 1.0).
            distortion: Amount of distortion (default 1.0).

        Returns:
            Curl vector based on wave texture.

        Note:
            This is a Python approximation. For geometry nodes,
            use from_wave_texture_gn() for accurate results.
        """
        # Simple wave function
        def wave_field(p: Vector) -> float:
            dist = math.sqrt(p.x ** 2 + p.y ** 2)
            return math.sin(dist * scale * 2 * math.pi) * distortion

        scaled_pos = position * scale
        return CurlNoise.curl_2d(wave_field, scaled_pos)

    @staticmethod
    def from_wave_texture_gn(
        builder: NodeTreeBuilder,
        position_socket,
        scale: float = 1.0,
        distortion: float = 1.0,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Build curl noise from Wave texture in geometry nodes.

        Args:
            builder: NodeTreeBuilder for node creation.
            position_socket: Socket providing position data.
            scale: Scale of the wave pattern (default 1.0).
            distortion: Distortion amount (default 1.0).
            location: Position for the first node.

        Returns:
            The curl vector node.
        """
        epsilon = 0.001

        # Scale position
        scale_node = builder.add_node(
            "ShaderNodeVectorMath",
            location,
            name="ScaleWave",
        )
        scale_node.operation = "SCALE"
        scale_node.inputs[1].default_value = scale
        builder.link(position_socket, scale_node.inputs[0])

        # Create offsets for finite differences
        offset_y_plus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] + 50),
            name="WaveOffsetYPlus",
        )
        offset_y_plus.operation = "ADD"
        offset_y_plus.inputs[1].default_value = (0, epsilon, 0)

        offset_y_minus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1]),
            name="WaveOffsetYMinus",
        )
        offset_y_minus.operation = "ADD"
        offset_y_minus.inputs[1].default_value = (0, -epsilon, 0)

        offset_x_plus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] - 50),
            name="WaveOffsetXPlus",
        )
        offset_x_plus.operation = "ADD"
        offset_x_plus.inputs[1].default_value = (epsilon, 0, 0)

        offset_x_minus = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 100, location[1] - 100),
            name="WaveOffsetXMinus",
        )
        offset_x_minus.operation = "ADD"
        offset_x_minus.inputs[1].default_value = (-epsilon, 0, 0)

        builder.link(scale_node.outputs[0], offset_y_plus.inputs[0])
        builder.link(scale_node.outputs[0], offset_y_minus.inputs[0])
        builder.link(scale_node.outputs[0], offset_x_plus.inputs[0])
        builder.link(scale_node.outputs[0], offset_x_minus.inputs[0])

        # Create Wave textures
        wave_y_plus = builder.add_node(
            "ShaderNodeTexWave",
            (location[0] + 250, location[1] + 50),
            name="WaveYPlus",
        )
        wave_y_plus.inputs["Scale"].default_value = 1.0
        wave_y_plus.inputs["Distortion"].default_value = distortion

        wave_y_minus = builder.add_node(
            "ShaderNodeTexWave",
            (location[0] + 250, location[1]),
            name="WaveYMinus",
        )
        wave_y_minus.inputs["Scale"].default_value = 1.0
        wave_y_minus.inputs["Distortion"].default_value = distortion

        wave_x_plus = builder.add_node(
            "ShaderNodeTexWave",
            (location[0] + 250, location[1] - 50),
            name="WaveXPlus",
        )
        wave_x_plus.inputs["Scale"].default_value = 1.0
        wave_x_plus.inputs["Distortion"].default_value = distortion

        wave_x_minus = builder.add_node(
            "ShaderNodeTexWave",
            (location[0] + 250, location[1] - 100),
            name="WaveXMinus",
        )
        wave_x_minus.inputs["Scale"].default_value = 1.0
        wave_x_minus.inputs["Distortion"].default_value = distortion

        builder.link(offset_y_plus.outputs[0], wave_y_plus.inputs["Vector"])
        builder.link(offset_y_minus.outputs[0], wave_y_minus.inputs["Vector"])
        builder.link(offset_x_plus.outputs[0], wave_x_plus.inputs["Vector"])
        builder.link(offset_x_minus.outputs[0], wave_x_minus.inputs["Vector"])

        # Calculate curl
        dW_dY = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] + 25),
            name="dWave_dY",
        )
        dW_dY.operation = "SUBTRACT"
        builder.link(wave_y_plus.outputs["Fac"], dW_dY.inputs[0])
        builder.link(wave_y_minus.outputs["Fac"], dW_dY.inputs[1])

        dW_dY_div = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] + 25),
            name="dW_dY_Div",
        )
        dW_dY_div.operation = "DIVIDE"
        dW_dY_div.inputs[1].default_value = 2 * epsilon
        builder.link(dW_dY.outputs[0], dW_dY_div.inputs[0])

        dW_dX = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] - 75),
            name="dWave_dX",
        )
        dW_dX.operation = "SUBTRACT"
        builder.link(wave_x_plus.outputs["Fac"], dW_dX.inputs[0])
        builder.link(wave_x_minus.outputs["Fac"], dW_dX.inputs[1])

        dW_dX_div = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] - 75),
            name="dW_dX_Div",
        )
        dW_dX_div.operation = "DIVIDE"
        dW_dX_div.inputs[1].default_value = 2 * epsilon
        builder.link(dW_dX.outputs[0], dW_dX_div.inputs[0])

        neg_dW_dX = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 520, location[1] - 75),
            name="Neg_dW_dX",
        )
        neg_dW_dX.operation = "MULTIPLY"
        neg_dW_dX.inputs[1].default_value = -1.0
        builder.link(dW_dX_div.outputs[0], neg_dW_dX.inputs[0])

        curl = builder.add_node(
            "ShaderNodeCombineXYZ",
            (location[0] + 600, location[1]),
            name="WaveCurl",
        )
        builder.link(dW_dY_div.outputs[0], curl.inputs["X"])
        builder.link(neg_dW_dX.outputs[0], curl.inputs["Y"])
        curl.inputs["Z"].default_value = 0.0

        return curl

    @staticmethod
    def from_sine_waves(
        position: Vector,
        frequency: float = 1.0,
    ) -> Vector:
        """
        Calculate curl from sine waves (creates regular spirals).

        Simple analytical curl from sine wave field - creates perfectly
        regular spiral patterns.

        Args:
            position: World position to sample at.
            frequency: Frequency of the sine waves (default 1.0).

        Returns:
            Curl vector from sine wave field.
        """
        # For sine wave field: sin(x) * sin(y)
        # The curl is: (cos(y)*sin(x), -cos(x)*sin(y), 0)
        x = position.x * frequency
        y = position.y * frequency

        curl_x = math.cos(y) * math.sin(x) * frequency
        curl_y = -math.cos(x) * math.sin(y) * frequency

        return Vector((curl_x, curl_y, 0.0))


class CurlLayer:
    """A single layer in a multi-layer curl noise system."""

    def __init__(
        self,
        curl_generator: Callable,
        scale: float = 1.0,
        strength: float = 1.0,
        offset: Vector = None,
    ):
        """
        Initialize a curl layer.

        Args:
            curl_generator: Function that generates curl values.
            scale: Scale of this layer's noise.
            strength: Strength multiplier for this layer.
            offset: Position offset for this layer.
        """
        self.curl_generator = curl_generator
        self.scale = scale
        self.strength = strength
        self.offset = offset or Vector((0, 0, 0))


class CurlParticleSystem:
    """
    Build curl-based particle simulation in geometry nodes.

    Creates a complete curl noise particle system with support for
    multiple layered curl noises, forces, and substep integration.

    The system uses simulation zones to update particle positions
    over time using curl noise velocity fields.

    Attributes:
        particle_count: Number of particles in the system.
        layers: List of curl noise layers.
        substeps: Number of simulation substeps per frame.
        forces: List of additional forces to apply.

    Example:
        >>> system = CurlParticleSystem(particle_count=1000)
        >>> system.add_layer(CurlNoise.from_noise_texture, scale=1.0, strength=0.5)
        >>> system.add_layer(CurlNoise.from_voronoi_distance, scale=2.0, strength=0.3)
        >>> system.set_substeps(5)
        >>> system.add_force("gravity", strength=0.1)
        >>> tree = system.build_node_tree(builder)
    """

    # Available force types
    FORCE_TYPES = ("gravity", "wind", "turbulence", "drag", "attraction", "vortex")

    def __init__(self, particle_count: int):
        """
        Initialize the curl particle system.

        Args:
            particle_count: Number of particles to simulate.
        """
        self.particle_count = particle_count
        self.layers: list[CurlLayer] = []
        self.substeps: int = 1
        self.forces: list[dict[str, Any]] = []
        self._curl_nodes: list[Node] = []

    def add_layer(
        self,
        curl_generator: Callable,
        scale: float = 1.0,
        strength: float = 1.0,
        offset: Vector = None,
    ) -> "CurlParticleSystem":
        """
        Add a curl noise layer.

        Multiple layers can be combined for complex swirling patterns.
        Each layer uses its own scale and strength.

        Args:
            curl_generator: Function that generates curl (from CurlNoise class).
            scale: Scale of this layer's noise (default 1.0).
            strength: Strength multiplier (default 1.0).
            offset: Position offset for variation (default None).

        Returns:
            Self for method chaining.

        Example:
            >>> system.add_layer(CurlNoise.from_noise_texture, scale=1.0, strength=0.5)
            >>> system.add_layer(CurlNoise.from_voronoi_distance, scale=0.5, strength=0.3)
        """
        layer = CurlLayer(curl_generator, scale, strength, offset)
        self.layers.append(layer)
        return self

    def set_substeps(self, count: int) -> "CurlParticleSystem":
        """
        Set the number of simulation substeps per frame.

        More substeps improve stability but increase computation time.

        Args:
            count: Number of substeps (default 1).

        Returns:
            Self for method chaining.
        """
        self.substeps = max(1, count)
        return self

    def add_force(self, force_type: str, **params) -> "CurlParticleSystem":
        """
        Add an additional force to the system.

        Forces are applied after curl noise velocity.

        Args:
            force_type: Type of force:
                - "gravity": Downward force (params: strength, direction)
                - "wind": Directional force (params: strength, direction)
                - "turbulence": Random force (params: strength, scale)
                - "drag": Velocity damping (params: strength)
                - "attraction": Force toward point (params: strength, center)
                - "vortex": Rotational force (params: strength, axis, center)
            **params: Force-specific parameters.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If force_type is invalid.

        Example:
            >>> system.add_force("gravity", strength=0.1)
            >>> system.add_force("wind", strength=0.5, direction=Vector((1, 0, 0)))
        """
        if force_type not in self.FORCE_TYPES:
            raise ValueError(
                f"Invalid force type '{force_type}'. Must be one of: {', '.join(self.FORCE_TYPES)}"
            )

        self.forces.append({"type": force_type, **params})
        return self

    def _build_curl_layer(
        self,
        builder: NodeTreeBuilder,
        position_socket,
        layer: CurlLayer,
        location: tuple[float, float],
    ) -> Node:
        """
        Build nodes for a single curl layer.

        Args:
            builder: NodeTreeBuilder instance.
            position_socket: Socket with position data.
            layer: CurlLayer to build.
            location: Starting location for nodes.

        Returns:
            Node outputting curl velocity for this layer.
        """
        # Apply offset if present
        if layer.offset and layer.offset != Vector((0, 0, 0)):
            offset_node = builder.add_node(
                "ShaderNodeVectorMath",
                location,
                name="LayerOffset",
            )
            offset_node.operation = "ADD"
            offset_node.inputs[1].default_value = tuple(layer.offset)
            builder.link(position_socket, offset_node.inputs[0])
            pos = offset_node.outputs[0]
        else:
            pos = position_socket

        # Build curl using noise texture
        curl_node, _, _ = CurlNoise.from_noise_texture_gn(
            builder,
            pos,
            scale=layer.scale,
            location=location,
        )

        # Apply strength
        strength_node = builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 700, location[1]),
            name="LayerStrength",
        )
        strength_node.operation = "SCALE"
        strength_node.inputs[1].default_value = layer.strength
        builder.link(curl_node.outputs["Vector"], strength_node.inputs[0])

        return strength_node

    def _build_force(
        self,
        builder: NodeTreeBuilder,
        velocity_socket,
        position_socket,
        force_config: dict,
        location: tuple[float, float],
    ) -> Node:
        """
        Build nodes for a single force.

        Args:
            builder: NodeTreeBuilder instance.
            velocity_socket: Current velocity socket.
            position_socket: Current position socket.
            force_config: Force configuration dict.
            location: Starting location for nodes.

        Returns:
            Node outputting force vector.
        """
        force_type = force_config["type"]
        strength = force_config.get("strength", 1.0)

        if force_type == "gravity":
            # Gravity: force = direction * strength
            direction = force_config.get("direction", Vector((0, 0, -1)))
            force = builder.add_node(
                "GeometryNodeInputVector",
                location,
                name="GravityForce",
                Vector=tuple(direction * strength),
            )
            return force

        elif force_type == "wind":
            # Wind: constant directional force
            direction = force_config.get("direction", Vector((1, 0, 0)))
            force = builder.add_node(
                "GeometryNodeInputVector",
                location,
                name="WindForce",
                Vector=tuple(direction * strength),
            )
            return force

        elif force_type == "drag":
            # Drag: force = -velocity * strength
            drag = builder.add_node(
                "ShaderNodeVectorMath",
                location,
                name="DragForce",
            )
            drag.operation = "SCALE"
            drag.inputs[1].default_value = -strength
            builder.link(velocity_socket, drag.inputs[0])
            return drag

        elif force_type == "attraction":
            # Attraction: force toward center point
            center = force_config.get("center", Vector((0, 0, 0)))

            # direction = center - position
            center_node = builder.add_node(
                "GeometryNodeInputVector",
                (location[0], location[1] + 50),
                name="AttractionCenter",
                Vector=tuple(center),
            )

            direction = builder.add_node(
                "ShaderNodeVectorMath",
                (location[0] + 100, location[1]),
                name="AttractionDir",
            )
            direction.operation = "SUBTRACT"
            builder.link(center_node.outputs["Vector"], direction.inputs[0])
            builder.link(position_socket, direction.inputs[1])

            # Scale by strength
            force = builder.add_node(
                "ShaderNodeVectorMath",
                (location[0] + 200, location[1]),
                name="AttractionForce",
            )
            force.operation = "SCALE"
            force.inputs[1].default_value = strength
            builder.link(direction.outputs[0], force.inputs[0])

            return force

        elif force_type == "vortex":
            # Vortex: tangential force around axis
            axis = force_config.get("axis", Vector((0, 0, 1)))
            center = force_config.get("center", Vector((0, 0, 0)))

            # Cross product of axis and (position - center) gives tangential direction
            center_node = builder.add_node(
                "GeometryNodeInputVector",
                (location[0], location[1] + 100),
                name="VortexCenter",
                Vector=tuple(center),
            )

            axis_node = builder.add_node(
                "GeometryNodeInputVector",
                (location[0], location[1] + 50),
                name="VortexAxis",
                Vector=tuple(axis),
            )

            to_center = builder.add_node(
                "ShaderNodeVectorMath",
                (location[0] + 100, location[1]),
                name="VortexToCenter",
            )
            to_center.operation = "SUBTRACT"
            builder.link(position_socket, to_center.inputs[0])
            builder.link(center_node.outputs["Vector"], to_center.inputs[1])

            tangential = builder.add_node(
                "ShaderNodeVectorMath",
                (location[0] + 200, location[1]),
                name="VortexTangent",
            )
            tangential.operation = "CROSS_PRODUCT"
            builder.link(axis_node.outputs["Vector"], tangential.inputs[0])
            builder.link(to_center.outputs[0], tangential.inputs[1])

            force = builder.add_node(
                "ShaderNodeVectorMath",
                (location[0] + 300, location[1]),
                name="VortexForce",
            )
            force.operation = "SCALE"
            force.inputs[1].default_value = strength
            builder.link(tangential.outputs[0], force.inputs[0])

            return force

        elif force_type == "turbulence":
            # Turbulence: random force from noise
            noise = builder.add_node(
                "ShaderNodeTexNoise",
                location,
                name="TurbulenceNoise",
            )
            noise.inputs["Scale"].default_value = force_config.get("scale", 1.0)

            # Subtract 0.5 to center around zero, scale by strength
            offset = builder.add_node(
                "ShaderNodeVectorMath",
                (location[0] + 100, location[1]),
                name="TurbulenceOffset",
            )
            offset.operation = "SUBTRACT"
            builder.link(noise.outputs["Color"], offset.inputs[0])
            offset.inputs[1].default_value = (0.5, 0.5, 0.5)

            force = builder.add_node(
                "ShaderNodeVectorMath",
                (location[0] + 200, location[1]),
                name="TurbulenceForce",
            )
            force.operation = "SCALE"
            force.inputs[1].default_value = strength
            builder.link(offset.outputs[0], force.inputs[0])

            return force

        # Default: return zero force
        zero = builder.add_node(
            "GeometryNodeInputVector",
            location,
            name="ZeroForce",
            Vector=(0, 0, 0),
        )
        return zero

    def build_node_tree(
        self,
        builder: NodeTreeBuilder,
        location: tuple[float, float] = (0, 0),
    ) -> NodeTree:
        """
        Build the complete particle system node tree.

        Creates a simulation zone with curl noise velocity and forces.

        Args:
            builder: NodeTreeBuilder for node creation.
            location: Starting position for the node tree.

        Returns:
            The completed GeometryNodeTree.

        Flow:
            1. Create initial point cloud with particle_count points
            2. Create simulation zone
            3. For each frame:
               a. Get position and velocity from previous frame
               b. Calculate curl velocity from all layers
               c. Add forces
               d. Integrate: new_pos = pos + vel * dt
               e. Store new position and velocity
        """
        # Create initial particle positions
        # Distribute points in a grid or random distribution
        distribute = builder.add_node(
            "GeometryNodeDistributePointsOnFaces",
            (location[0], location[1] + 200),
            name="DistributeParticles",
        )
        # Note: This needs a mesh input - would typically connect to Group Input

        # Create simulation zone
        sim_in, sim_out = builder.add_simulation_zone(
            (location[0] + 200, location[1]),
            name="CurlParticleSim",
        )

        # Connect initial points
        builder.link(distribute.outputs["Points"], sim_in.inputs["Geometry"])

        # Get delta time
        scene_time = builder.add_node(
            "GeometryNodeInputSceneTime",
            (location[0] + 250, location[1] + 150),
            name="DeltaTime",
        )

        # For substeps, divide delta time
        if self.substeps > 1:
            dt_div = builder.add_node(
                "ShaderNodeMath",
                (location[0] + 350, location[1] + 150),
                name="SubstepDT",
            )
            dt_div.operation = "DIVIDE"
            dt_div.inputs[1].default_value = float(self.substeps)
            builder.link(scene_time.outputs["Delta Time"], dt_div.inputs[0])
            dt_socket = dt_div.outputs[0]
        else:
            dt_socket = scene_time.outputs["Delta Time"]

        # Get current position
        position = builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] + 300, location[1] + 50),
            name="ParticlePosition",
        )
        builder.link(sim_in.outputs["Geometry"], position.inputs[0])

        # Build curl velocity from all layers
        curl_outputs = []
        x_offset = 400

        for i, layer in enumerate(self.layers):
            curl_node = self._build_curl_layer(
                builder,
                position.outputs["Position"],
                layer,
                location=(location[0] + x_offset, location[1] + i * 200),
            )
            curl_outputs.append(curl_node.outputs[0])
            x_offset += 800

        # Sum all curl layers
        if len(curl_outputs) == 1:
            total_curl_socket = curl_outputs[0]
        elif len(curl_outputs) > 1:
            # Add curl outputs together
            current_sum = curl_outputs[0]
            for i, curl_out in enumerate(curl_outputs[1:], 1):
                add_node = builder.add_node(
                    "ShaderNodeVectorMath",
                    (location[0] + x_offset + i * 100, location[1]),
                    name=f"SumCurl_{i}",
                )
                add_node.operation = "ADD"
                builder.link(current_sum, add_node.inputs[0])
                builder.link(curl_out, add_node.inputs[1])
                current_sum = add_node.outputs[0]
            total_curl_socket = current_sum
        else:
            # No curl layers - use zero velocity
            zero_vel = builder.add_node(
                "GeometryNodeInputVector",
                (location[0] + 400, location[1]),
                name="ZeroVelocity",
                Vector=(0, 0, 0),
            )
            total_curl_socket = zero_vel.outputs["Vector"]

        # Add forces
        force_x = location[0] + x_offset + len(curl_outputs) * 100 + 200

        for i, force_config in enumerate(self.forces):
            force_node = self._build_force(
                builder,
                total_curl_socket,
                position.outputs["Position"],
                force_config,
                location=(force_x + i * 300, location[1] - 200),
            )

            # Add force to velocity
            add_force = builder.add_node(
                "ShaderNodeVectorMath",
                (force_x + i * 300 + 150, location[1]),
                name=f"AddForce_{i}",
            )
            add_force.operation = "ADD"
            builder.link(total_curl_socket, add_force.inputs[0])
            builder.link(force_node.outputs[0] if hasattr(force_node, "outputs") else force_node.outputs["Vector"], add_force.inputs[1])
            total_curl_socket = add_force.outputs[0]

        # Integrate: new_position = position + velocity * dt
        scale_vel = builder.add_node(
            "ShaderNodeVectorMath",
            (force_x + len(self.forces) * 300 + 100, location[1] + 50),
            name="ScaleVelocity",
        )
        scale_vel.operation = "SCALE"
        builder.link(total_curl_socket, scale_vel.inputs[0])
        builder.link(dt_socket, scale_vel.inputs[1])

        new_position = builder.add_node(
            "ShaderNodeVectorMath",
            (force_x + len(self.forces) * 300 + 200, location[1] + 50),
            name="IntegratePosition",
        )
        new_position.operation = "ADD"
        builder.link(position.outputs["Position"], new_position.inputs[0])
        builder.link(scale_vel.outputs[0], new_position.inputs[1])

        # Set new position
        set_position = builder.add_node(
            "GeometryNodeSetPosition",
            (force_x + len(self.forces) * 300 + 300, location[1]),
            name="SetParticlePosition",
        )
        builder.link(sim_in.outputs["Geometry"], set_position.inputs["Geometry"])
        builder.link(new_position.outputs[0], set_position.inputs["Position"])

        # Connect to simulation output
        builder.link(set_position.outputs["Geometry"], sim_out.inputs["Geometry"])

        return builder.get_tree()
