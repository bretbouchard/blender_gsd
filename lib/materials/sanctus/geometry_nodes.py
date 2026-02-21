"""
Sanctus Geometry Nodes - GN-Based Procedural Generators
=======================================================

Geometry Nodes-based procedural generators for creating
damage geometry, wear patterns, and surface imperfections
directly on mesh geometry.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
import math

try:
    import bpy
    from bpy.types import GeometryNode, NodeTree, Object
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    GeometryNode = Any
    NodeTree = Any
    Object = Any
    Vector = Any


class GNDamageType(Enum):
    """Types of geometry-based damage."""
    DENTS = "dents"
    SCRATCHES = "scratches"
    BULLETS = "bullets"
    IMPACTS = "impacts"
    CRACKS = "cracks"
    CHIPS = "chips"
    PEELING = "peeling"


class GNWearType(Enum):
    """Types of geometry-based wear."""
    EDGE = "edge"
    SURFACE = "surface"
    CORNER = "corner"
    UNIFORM = "uniform"
    DIRECTIONAL = "directional"


@dataclass
class GNGeneratorSettings:
    """Settings for geometry node generators."""
    seed: int = 0
    intensity: float = 0.5
    scale: float = 1.0

    # Damage settings
    damage_size: float = 0.05
    damage_depth: float = 0.01
    damage_count: int = 10

    # Surface settings
    affect_normals: bool = True
    affect_positions: bool = True
    preserve_volume: bool = True

    # Edge settings
    edge_threshold: float = 30.0  # degrees
    edge_inset: float = 0.01


class SanctusGNGenerator:
    """
    Geometry Nodes-based procedural generators.

    Provides methods for creating damage and wear effects
    directly on mesh geometry using Blender's Geometry Nodes system.
    """

    # Node group names
    DAMAGE_NODE_GROUP = "Sanctus_Damage"
    WEAR_NODE_GROUP = "Sanctus_Wear"
    IMPERFECTIONS_NODE_GROUP = "Sanctus_Imperfections"

    @staticmethod
    def create_damage_geometry(
        base_mesh: Object,
        damage_type: Union[GNDamageType, str] = "dents",
        intensity: float = 0.5,
        seed: int = 0,
        preserve_original: bool = True,
    ) -> Optional[Object]:
        """
        Create damage geometry on a base mesh using Geometry Nodes.

        Args:
            base_mesh: Base mesh object to damage
            damage_type: Type of damage to apply
            intensity: Damage intensity (0.0 - 1.0)
            seed: Random seed for reproducibility
            preserve_original: Keep original mesh intact

        Returns:
            Modified mesh object or None on failure
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for Geometry Nodes")

        if isinstance(damage_type, str):
            damage_type = GNDamageType(damage_type.lower())

        # Create or get damage node group
        node_group = SanctusGNGenerator._get_or_create_damage_node_group(damage_type)

        # Create target object
        if preserve_original:
            damaged_mesh = base_mesh.copy()
            damaged_mesh.data = base_mesh.data.copy()
            bpy.context.collection.objects.link(damaged_mesh)
        else:
            damaged_mesh = base_mesh

        # Add geometry nodes modifier
        gn_modifier = damaged_mesh.modifiers.new(
            name="SanctusDamage",
            type='NODES'
        )
        gn_modifier.node_group = node_group

        # Set parameters
        SanctusGNGenerator._set_damage_parameters(
            gn_modifier, damage_type, intensity, seed
        )

        return damaged_mesh

    @staticmethod
    def _get_or_create_damage_node_group(
        damage_type: GNDamageType,
    ) -> Optional[NodeTree]:
        """Get or create the Geometry Node group for damage."""
        if not BLENDER_AVAILABLE:
            return None

        group_name = f"{SanctusGNGenerator.DAMAGE_NODE_GROUP}_{damage_type.value}"

        # Check if group exists
        if group_name in bpy.data.node_groups:
            return bpy.data.node_groups[group_name]

        # Create new node group
        node_group = bpy.data.node_groups.new(
            name=group_name,
            type='GeometryNodeTree'
        )

        # Create interface
        node_group.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        node_group.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        node_group.interface.new_socket(
            name="Intensity", in_out='INPUT', socket_type='NodeSocketFloat'
        )
        node_group.interface.new_socket(
            name="Seed", in_out='INPUT', socket_type='NodeSocketInt'
        )
        node_group.interface.new_socket(
            name="Size", in_out='INPUT', socket_type='NodeSocketFloat'
        )

        # Build node network based on damage type
        SanctusGNGenerator._build_damage_nodes(node_group, damage_type)

        return node_group

    @staticmethod
    def _build_damage_nodes(
        node_group: NodeTree,
        damage_type: GNDamageType,
    ) -> None:
        """Build the node network for a specific damage type."""
        if not BLENDER_AVAILABLE:
            return

        nodes = node_group.nodes
        links = node_group.links

        # Input/Output nodes
        input_node = nodes.new('NodeGroupInput')
        input_node.location = (-400, 0)

        output_node = nodes.new('NodeGroupOutput')
        output_node.location = (400, 0)

        if damage_type == GNDamageType.DENTS:
            # Create dent effect using displacement
            # Distribute points on surface
            distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
            distribute.distribute_method = 'RANDOM'
            links.new(input_node.outputs['Geometry'], distribute.inputs['Mesh'])

            # Set random seed
            random_node = nodes.new('FunctionNodeRandomValue')
            links.new(input_node.outputs['Seed'], random_node.inputs['Seed'])

            # Create displacement
            position = nodes.new('GeometryNodeInputPosition')
            normal = nodes.new('GeometryNodeInputNormal')

            # Scale normals by intensity (inward for dents)
            scale = nodes.new('ShaderNodeVectorMath')
            scale.operation = 'SCALE'
            links.new(normal.outputs['Normal'], scale.inputs['Vector'])
            links.new(input_node.outputs['Intensity'], scale.inputs['Scale'])

            # Apply displacement
            set_position = nodes.new('GeometryNodeSetPosition')
            links.new(input_node.outputs['Geometry'], set_position.inputs['Geometry'])
            links.new(scale.outputs['Vector'], set_position.inputs['Offset'])

            # Output
            links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

        elif damage_type == GNDamageType.SCRATCHES:
            # Create scratch patterns using curve and boolean
            # This is a simplified version

            # Subdivide mesh for detail
            subdivide = nodes.new('GeometryNodeSubdivideMesh')
            subdivide.inputs['Level'].default_value = 3
            links.new(input_node.outputs['Geometry'], subdivide.inputs['Mesh'])

            # Store original position
            store_named = nodes.new('GeometryNodeStoreNamedAttribute')
            store_named.inputs['Name'].default_value = 'original_position'
            links.new(subdivide.outputs['Mesh'], store_named.inputs['Geometry'])

            # Add noise-based displacement along scratches
            # (simplified - real implementation would be more complex)

            links.new(store_named.outputs['Geometry'], output_node.inputs['Geometry'])

        elif damage_type == GNDamageType.BULLETS:
            # Create bullet holes using boolean difference

            # Store named selection for bullet positions
            # Create cylinder for boolean
            # (simplified placeholder)

            links.new(input_node.outputs['Geometry'], output_node.inputs['Geometry'])

        elif damage_type == GNDamageType.IMPACTS:
            # Create impact craters using displacement

            # Add subdivision
            subdivide = nodes.new('GeometryNodeSubdivideMesh')
            subdivide.inputs['Level'].default_value = 4
            links.new(input_node.outputs['Geometry'], subdivide.inputs['Mesh'])

            # Get normal and position
            normal = nodes.new('GeometryNodeInputNormal')
            position = nodes.new('GeometryNodeInputPosition')

            # Create displacement based on voronoi
            voronoi = nodes.new('ShaderNodeTexVoronoi')
            voronoi.inputs['Scale'].default_value = 10.0
            links.new(position.outputs['Position'], voronoi.inputs['Vector'])

            # Invert and scale displacement
            math_node = nodes.new('ShaderNodeMath')
            math_node.operation = 'MULTIPLY'
            links.new(voronoi.outputs['Distance'], math_node.inputs[0])
            links.new(input_node.outputs['Intensity'], math_node.inputs[1])

            # Apply to position
            set_position = nodes.new('GeometryNodeSetPosition')
            links.new(subdivide.outputs['Mesh'], set_position.inputs['Geometry'])
            links.new(math_node.outputs['Value'], set_position.inputs['Offset Z'])

            links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

        else:
            # Default pass-through
            links.new(input_node.outputs['Geometry'], output_node.inputs['Geometry'])

    @staticmethod
    def _set_damage_parameters(
        modifier: Any,
        damage_type: GNDamageType,
        intensity: float,
        seed: int,
    ) -> None:
        """Set parameters on the geometry nodes modifier."""
        if not BLENDER_AVAILABLE:
            return

        # Set socket values by identifier
        for item in modifier.node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name == 'Intensity':
                    modifier[item.identifier] = intensity
                elif item.name == 'Seed':
                    modifier[item.identifier] = seed
                elif item.name == 'Size':
                    modifier[item.identifier] = intensity * 0.1

    @staticmethod
    def create_wear_pattern(
        surface: Object,
        wear_type: Union[GNWearType, str] = "edge",
        amount: float = 0.5,
        edge_threshold: float = 30.0,
        seed: int = 0,
    ) -> Optional[Object]:
        """
        Create wear patterns on a surface using Geometry Nodes.

        Args:
            surface: Surface object to apply wear to
            wear_type: Type of wear pattern
            amount: Wear amount (0.0 - 1.0)
            edge_threshold: Angle threshold for edge detection
            seed: Random seed for reproducibility

        Returns:
            Modified surface object or None on failure
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for Geometry Nodes")

        if isinstance(wear_type, str):
            wear_type = GNWearType(wear_type.lower())

        # Create or get wear node group
        node_group = SanctusGNGenerator._get_or_create_wear_node_group(wear_type)

        # Add geometry nodes modifier
        gn_modifier = surface.modifiers.new(
            name="SanctusWear",
            type='NODES'
        )
        gn_modifier.node_group = node_group

        # Set parameters
        SanctusGNGenerator._set_wear_parameters(
            gn_modifier, wear_type, amount, edge_threshold, seed
        )

        return surface

    @staticmethod
    def _get_or_create_wear_node_group(
        wear_type: GNWearType,
    ) -> Optional[NodeTree]:
        """Get or create the Geometry Node group for wear."""
        if not BLENDER_AVAILABLE:
            return None

        group_name = f"{SanctusGNGenerator.WEAR_NODE_GROUP}_{wear_type.value}"

        if group_name in bpy.data.node_groups:
            return bpy.data.node_groups[group_name]

        node_group = bpy.data.node_groups.new(
            name=group_name,
            type='GeometryNodeTree'
        )

        # Create interface
        node_group.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        node_group.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        node_group.interface.new_socket(
            name="Amount", in_out='INPUT', socket_type='NodeSocketFloat'
        )
        node_group.interface.new_socket(
            name="Edge Threshold", in_out='INPUT', socket_type='NodeSocketFloat'
        )
        node_group.interface.new_socket(
            name="Seed", in_out='INPUT', socket_type='NodeSocketInt'
        )

        # Build node network
        SanctusGNGenerator._build_wear_nodes(node_group, wear_type)

        return node_group

    @staticmethod
    def _build_wear_nodes(
        node_group: NodeTree,
        wear_type: GNWearType,
    ) -> None:
        """Build the node network for wear patterns."""
        if not BLENDER_AVAILABLE:
            return

        nodes = node_group.nodes
        links = node_group.links

        # Input/Output nodes
        input_node = nodes.new('NodeGroupInput')
        input_node.location = (-400, 0)

        output_node = nodes.new('NodeGroupOutput')
        output_node.location = (400, 0)

        if wear_type == GNWearType.EDGE:
            # Edge wear using edge angle detection

            # Get edge angles
            edge_angle = nodes.new('GeometryNodeInputEdgeAngle')

            # Compare with threshold
            compare = nodes.new('FunctionNodeCompare')
            compare.operation = 'GREATER_THAN'
            links.new(edge_angle.outputs['Unsigned Angle'], compare.inputs['A'])
            links.new(input_node.outputs['Edge Threshold'], compare.inputs['B'])

            # Subdivide for detail
            subdivide = nodes.new('GeometryNodeSubdivideMesh')
            subdivide.inputs['Level'].default_value = 3
            links.new(input_node.outputs['Geometry'], subdivide.inputs['Mesh'])

            # Get normal
            normal = nodes.new('GeometryNodeInputNormal')

            # Scale normal by wear amount
            scale = nodes.new('ShaderNodeVectorMath')
            scale.operation = 'SCALE'
            links.new(normal.outputs['Normal'], scale.inputs['Vector'])
            links.new(input_node.outputs['Amount'], scale.inputs['Scale'])

            # Invert for wear (push inward)
            invert = nodes.new('ShaderNodeVectorMath')
            invert.operation = 'SCALE'
            invert.inputs['Scale'].default_value = -1.0
            links.new(scale.outputs['Vector'], invert.inputs['Vector'])

            # Apply position offset
            set_position = nodes.new('GeometryNodeSetPosition')
            links.new(subdivide.outputs['Mesh'], set_position.inputs['Geometry'])
            links.new(invert.outputs['Vector'], set_position.inputs['Offset'])

            links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

        elif wear_type == GNWearType.SURFACE:
            # Surface wear using noise-based displacement

            # Subdivide
            subdivide = nodes.new('GeometryNodeSubdivideMesh')
            subdivide.inputs['Level'].default_value = 4
            links.new(input_node.outputs['Geometry'], subdivide.inputs['Mesh'])

            # Get position for noise
            position = nodes.new('GeometryNodeInputPosition')

            # Create noise
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 50.0
            links.new(position.outputs['Position'], noise.inputs['Vector'])

            # Get normal
            normal = nodes.new('GeometryNodeInputNormal')

            # Scale by amount and noise
            multiply = nodes.new('ShaderNodeMath')
            multiply.operation = 'MULTIPLY'
            links.new(noise.outputs['Fac'], multiply.inputs[0])
            links.new(input_node.outputs['Amount'], multiply.inputs[1])

            # Scale normal
            scale_normal = nodes.new('ShaderNodeVectorMath')
            scale_normal.operation = 'SCALE'
            links.new(normal.outputs['Normal'], scale_normal.inputs['Vector'])
            links.new(multiply.outputs['Value'], scale_normal.inputs['Scale'])

            # Invert
            invert = nodes.new('ShaderNodeVectorMath')
            invert.operation = 'SCALE'
            invert.inputs['Scale'].default_value = -1.0
            links.new(scale_normal.outputs['Vector'], invert.inputs['Vector'])

            # Apply
            set_position = nodes.new('GeometryNodeSetPosition')
            links.new(subdivide.outputs['Mesh'], set_position.inputs['Geometry'])
            links.new(invert.outputs['Vector'], set_position.inputs['Offset'])

            links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

        elif wear_type == GNWearType.CORNER:
            # Corner wear - detect corners and apply more wear

            # Get edge vertices
            # This is simplified - real implementation would use vertex weights

            links.new(input_node.outputs['Geometry'], output_node.inputs['Geometry'])

        else:
            # Default pass-through
            links.new(input_node.outputs['Geometry'], output_node.inputs['Geometry'])

    @staticmethod
    def _set_wear_parameters(
        modifier: Any,
        wear_type: GNWearType,
        amount: float,
        edge_threshold: float,
        seed: int,
    ) -> None:
        """Set parameters on the wear geometry nodes modifier."""
        if not BLENDER_AVAILABLE:
            return

        for item in modifier.node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name == 'Amount':
                    modifier[item.identifier] = amount
                elif item.name == 'Edge Threshold':
                    modifier[item.identifier] = edge_threshold
                elif item.name == 'Seed':
                    modifier[item.identifier] = seed

    @staticmethod
    def create_surface_imperfections(
        mesh: Object,
        imperfection_type: str = "scratches",
        density: float = 50.0,
        depth: float = 0.001,
        seed: int = 0,
        use_vertex_colors: bool = True,
    ) -> Optional[Object]:
        """
        Create surface imperfections using Geometry Nodes.

        Args:
            mesh: Mesh object to add imperfections to
            imperfection_type: Type of imperfection ("scratches", "bumps", "waviness")
            density: Imperfection density
            depth: Imperfection depth/height
            seed: Random seed for reproducibility
            use_vertex_colors: Store imperfection mask in vertex colors

        Returns:
            Modified mesh object or None on failure
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for Geometry Nodes")

        # Create or get imperfections node group
        node_group = SanctusGNGenerator._get_or_create_imperfections_node_group(
            imperfection_type
        )

        if not node_group:
            return mesh

        # Add geometry nodes modifier
        gn_modifier = mesh.modifiers.new(
            name="SanctusImperfections",
            type='NODES'
        )
        gn_modifier.node_group = node_group

        # Set parameters
        for item in node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name == 'Density':
                    gn_modifier[item.identifier] = density
                elif item.name == 'Depth':
                    gn_modifier[item.identifier] = depth
                elif item.name == 'Seed':
                    gn_modifier[item.identifier] = seed

        # Optionally store in vertex colors
        if use_vertex_colors:
            SanctusGNGenerator._store_imperfection_mask(mesh, imperfection_type)

        return mesh

    @staticmethod
    def _get_or_create_imperfections_node_group(
        imperfection_type: str,
    ) -> Optional[NodeTree]:
        """Get or create imperfections node group."""
        if not BLENDER_AVAILABLE:
            return None

        group_name = f"{SanctusGNGenerator.IMPERFECTIONS_NODE_GROUP}_{imperfection_type}"

        if group_name in bpy.data.node_groups:
            return bpy.data.node_groups[group_name]

        node_group = bpy.data.node_groups.new(
            name=group_name,
            type='GeometryNodeTree'
        )

        # Create interface
        node_group.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        node_group.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        node_group.interface.new_socket(
            name="Density", in_out='INPUT', socket_type='NodeSocketFloat'
        )
        node_group.interface.new_socket(
            name="Depth", in_out='INPUT', socket_type='NodeSocketFloat'
        )
        node_group.interface.new_socket(
            name="Seed", in_out='INPUT', socket_type='NodeSocketInt'
        )

        # Build node network
        nodes = node_group.nodes
        links = node_group.links

        input_node = nodes.new('NodeGroupInput')
        input_node.location = (-400, 0)

        output_node = nodes.new('NodeGroupOutput')
        output_node.location = (400, 0)

        if imperfection_type == "scratches":
            # Create scratch pattern using wave texture
            subdivide = nodes.new('GeometryNodeSubdivideMesh')
            subdivide.inputs['Level'].default_value = 2
            links.new(input_node.outputs['Geometry'], subdivide.inputs['Mesh'])

            position = nodes.new('GeometryNodeInputPosition')
            normal = nodes.new('GeometryNodeInputNormal')

            # Wave texture for scratches
            wave = nodes.new('ShaderNodeTexWave')
            wave.inputs['Scale'].default_value = 100.0
            links.new(position.outputs['Position'], wave.inputs['Vector'])

            # Scale by depth
            multiply = nodes.new('ShaderNodeMath')
            multiply.operation = 'MULTIPLY'
            links.new(wave.outputs['Fac'], multiply.inputs[0])
            links.new(input_node.outputs['Depth'], multiply.inputs[1])

            # Apply to normal
            scale_normal = nodes.new('ShaderNodeVectorMath')
            scale_normal.operation = 'SCALE'
            links.new(normal.outputs['Normal'], scale_normal.inputs['Vector'])
            links.new(multiply.outputs['Value'], scale_normal.inputs['Scale'])

            set_position = nodes.new('GeometryNodeSetPosition')
            links.new(subdivide.outputs['Mesh'], set_position.inputs['Geometry'])
            links.new(scale_normal.outputs['Vector'], set_position.inputs['Offset'])

            links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

        elif imperfection_type == "bumps":
            # Random bumps using noise
            subdivide = nodes.new('GeometryNodeSubdivideMesh')
            subdivide.inputs['Level'].default_value = 3
            links.new(input_node.outputs['Geometry'], subdivide.inputs['Mesh'])

            position = nodes.new('GeometryNodeInputPosition')
            normal = nodes.new('GeometryNodeInputNormal')

            # Noise for bumps
            noise = nodes.new('ShaderNodeTexNoise')
            links.new(position.outputs['Position'], noise.inputs['Vector'])

            # Scale by depth
            multiply = nodes.new('ShaderNodeMath')
            multiply.operation = 'MULTIPLY'
            links.new(noise.outputs['Fac'], multiply.inputs[0])
            links.new(input_node.outputs['Depth'], multiply.inputs[1])

            # Apply
            scale_normal = nodes.new('ShaderNodeVectorMath')
            scale_normal.operation = 'SCALE'
            links.new(normal.outputs['Normal'], scale_normal.inputs['Vector'])
            links.new(multiply.outputs['Value'], scale_normal.inputs['Scale'])

            set_position = nodes.new('GeometryNodeSetPosition')
            links.new(subdivide.outputs['Mesh'], set_position.inputs['Geometry'])
            links.new(scale_normal.outputs['Vector'], set_position.inputs['Offset'])

            links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

        else:
            # Default pass-through
            links.new(input_node.outputs['Geometry'], output_node.inputs['Geometry'])

        return node_group

    @staticmethod
    def _store_imperfection_mask(
        mesh: Object,
        imperfection_type: str,
    ) -> None:
        """Store imperfection mask in vertex colors."""
        if not BLENDER_AVAILABLE:
            return

        # Create or get vertex color layer
        color_layer_name = f"imperfection_{imperfection_type}"

        if not mesh.data.vertex_colors:
            mesh.data.vertex_colors.new()

        # Find or create the layer
        color_layer = None
        for layer in mesh.data.vertex_colors:
            if layer.name == color_layer_name:
                color_layer = layer
                break

        if not color_layer:
            color_layer = mesh.data.vertex_colors.new(name=color_layer_name)

    @staticmethod
    def create_bevel_wear(
        mesh: Object,
        radius: float = 0.01,
        wear_intensity: float = 0.5,
        segments: int = 4,
        seed: int = 0,
    ) -> Optional[Object]:
        """
        Create bevel-based edge wear using Geometry Nodes.

        Args:
            mesh: Mesh object to apply bevel wear to
            radius: Bevel radius
            wear_intensity: Wear intensity on beveled edges
            segments: Number of bevel segments
            seed: Random seed for reproducibility

        Returns:
            Modified mesh object
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required for Geometry Nodes")

        # Add bevel modifier first
        bevel = mesh.modifiers.new(name="SanctusBevel", type='BEVEL')
        bevel.width = radius
        bevel.segments = segments
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = 30.0

        # Then add wear using existing wear pattern
        return SanctusGNGenerator.create_wear_pattern(
            mesh,
            wear_type=GNWearType.EDGE,
            amount=wear_intensity,
            edge_threshold=30.0,
            seed=seed,
        )

    @staticmethod
    def create_procedural_damage_mask(
        mesh: Object,
        damage_type: GNDamageType,
        output_attribute: str = "damage_mask",
    ) -> str:
        """
        Create a procedural damage mask stored as an attribute.

        Args:
            mesh: Mesh object
            damage_type: Type of damage mask to create
            output_attribute: Name of output attribute

        Returns:
            Name of the created attribute
        """
        if not BLENDER_AVAILABLE:
            return ""

        # Ensure mesh has geometry nodes modifier
        gn_modifier = None
        for mod in mesh.modifiers:
            if mod.type == 'NODES' and 'Damage' in mod.name:
                gn_modifier = mod
                break

        if not gn_modifier:
            # Create new modifier
            node_group = SanctusGNGenerator._get_or_create_damage_node_group(damage_type)
            gn_modifier = mesh.modifiers.new(name="SanctusDamageMask", type='NODES')
            gn_modifier.node_group = node_group

        # Store mask in named attribute
        # This would require specific node setup for attribute output

        return output_attribute

    @staticmethod
    def remove_all_sanctus_modifiers(mesh: Object) -> None:
        """
        Remove all Sanctus Geometry Nodes modifiers from a mesh.

        Args:
            mesh: Mesh object to clean up
        """
        if not BLENDER_AVAILABLE:
            return

        modifiers_to_remove = []
        for mod in mesh.modifiers:
            if mod.type == 'NODES' and 'Sanctus' in mod.name:
                modifiers_to_remove.append(mod.name)

        for mod_name in modifiers_to_remove:
            mesh.modifiers.remove(mesh.modifiers[mod_name])

    @staticmethod
    def list_available_generators() -> List[str]:
        """
        List all available Geometry Node generators.

        Returns:
            List of generator names
        """
        generators = []

        # Damage types
        for damage_type in GNDamageType:
            generators.append(f"damage_{damage_type.value}")

        # Wear types
        for wear_type in GNWearType:
            generators.append(f"wear_{wear_type.value}")

        # Imperfection types
        generators.extend(["imperfection_scratches", "imperfection_bumps"])

        return generators
