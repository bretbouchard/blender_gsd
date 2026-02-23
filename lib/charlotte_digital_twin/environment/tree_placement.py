"""
Tree Placement System

Generates and places trees along highways:
- Procedural tree geometry
- Species variation (pine, oak, maple)
- Distance-based placement
- LOD system for performance

Optimized for large-scale vegetation scattering.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math
import random

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any


class TreeSpecies(Enum):
    """Types of trees for highway landscaping."""
    PINE = "pine"           # Evergreen, conical
    OAK = "oak"             # Deciduous, round canopy
    MAPLE = "maple"         # Deciduous, spreading
    CEDAR = "cedar"         # Evergreen, narrow
    SWEETGUM = "sweetgum"   # Common in NC
    DOGWOOD = "dogwood"     # NC state flower, smaller
    HOLLY = "holly"         # Evergreen understory
    CREPE_MYRTLE = "crepe"  # Ornamental, small


@dataclass
class TreeConfig:
    """Configuration for tree generation."""
    # Trunk
    trunk_height: float = 8.0
    trunk_radius_base: float = 0.3
    trunk_radius_top: float = 0.1
    trunk_segments: int = 8

    # Canopy
    canopy_radius: float = 4.0
    canopy_height: float = 6.0
    canopy_density: float = 0.8  # 0-1
    canopy_segments: int = 12

    # Color
    trunk_color: Tuple[float, float, float] = (0.35, 0.25, 0.15)
    leaf_color: Tuple[float, float, float] = (0.2, 0.5, 0.2)

    # Variation
    height_variation: float = 0.3  # Random height multiplier range
    canopy_variation: float = 0.2

    # LOD distances
    lod_high_distance: float = 50.0
    lod_medium_distance: float = 150.0
    lod_low_distance: float = 300.0


# Species-specific configurations
TREE_CONFIGS = {
    TreeSpecies.PINE: TreeConfig(
        trunk_height=15.0,
        trunk_radius_base=0.25,
        canopy_radius=3.0,
        canopy_height=12.0,
        leaf_color=(0.15, 0.35, 0.15),  # Dark green
        height_variation=0.4,
    ),
    TreeSpecies.OAK: TreeConfig(
        trunk_height=12.0,
        trunk_radius_base=0.4,
        canopy_radius=6.0,
        canopy_height=8.0,
        leaf_color=(0.2, 0.45, 0.15),
        height_variation=0.25,
    ),
    TreeSpecies.MAPLE: TreeConfig(
        trunk_height=10.0,
        trunk_radius_base=0.3,
        canopy_radius=5.0,
        canopy_height=7.0,
        leaf_color=(0.25, 0.5, 0.2),
        height_variation=0.3,
    ),
    TreeSpecies.CEDAR: TreeConfig(
        trunk_height=10.0,
        trunk_radius_base=0.2,
        canopy_radius=2.0,
        canopy_height=8.0,
        leaf_color=(0.1, 0.3, 0.15),
        height_variation=0.35,
    ),
    TreeSpecies.SWEETGUM: TreeConfig(
        trunk_height=14.0,
        trunk_radius_base=0.3,
        canopy_radius=4.5,
        canopy_height=9.0,
        leaf_color=(0.2, 0.45, 0.18),
        height_variation=0.3,
    ),
    TreeSpecies.DOGWOOD: TreeConfig(
        trunk_height=5.0,
        trunk_radius_base=0.1,
        canopy_radius=3.0,
        canopy_height=3.0,
        leaf_color=(0.25, 0.45, 0.2),
        height_variation=0.2,
    ),
    TreeSpecies.HOLLY: TreeConfig(
        trunk_height=6.0,
        trunk_radius_base=0.12,
        canopy_radius=2.5,
        canopy_height=4.0,
        leaf_color=(0.1, 0.35, 0.15),
        height_variation=0.25,
    ),
    TreeSpecies.CREPE_MYRTLE: TreeConfig(
        trunk_height=4.0,
        trunk_radius_base=0.08,
        canopy_radius=2.0,
        canopy_height=2.5,
        leaf_color=(0.2, 0.4, 0.2),
        height_variation=0.2,
    ),
}


class TreeGenerator:
    """
    Generates procedural tree geometry.

    Creates optimized tree meshes with LOD variants for
    efficient rendering of large vegetation areas.
    """

    def __init__(self):
        """Initialize the tree generator."""
        self._material_cache: Dict[str, Any] = {}
        self._tree_cache: Dict[str, Object] = {}

    def create_tree(
        self,
        species: TreeSpecies = TreeSpecies.OAK,
        config: Optional[TreeConfig] = None,
        name: str = "Tree",
        seed: Optional[int] = None,
    ) -> Optional[Object]:
        """
        Create a procedural tree.

        Args:
            species: Tree species type
            config: Custom configuration
            name: Object name
            seed: Random seed for variation

        Returns:
            Blender object (parent with trunk and canopy children)
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or TREE_CONFIGS.get(species, TreeConfig())

        if seed is not None:
            random.seed(seed)

        # Apply variation
        height_mult = 1.0 + random.uniform(-config.height_variation, config.height_variation)
        canopy_mult = 1.0 + random.uniform(-config.canopy_variation, config.canopy_variation)

        # Create parent
        tree_obj = bpy.data.objects.new(name, None)
        tree_obj.empty_display_type = "PLAIN_AXES"

        # Create trunk
        trunk = self._create_trunk(config, height_mult, f"{name}_Trunk")
        if trunk:
            trunk.parent = tree_obj

        # Create canopy based on species
        if species in [TreeSpecies.PINE, TreeSpecies.CEDAR]:
            canopy = self._create_conifer_canopy(config, height_mult, canopy_mult, f"{name}_Canopy")
        else:
            canopy = self._create_deciduous_canopy(config, height_mult, canopy_mult, f"{name}_Canopy")

        if canopy:
            canopy.location = (0, 0, config.trunk_height * height_mult * 0.7)
            canopy.parent = tree_obj

        return tree_obj

    def _create_trunk(
        self,
        config: TreeConfig,
        height_mult: float,
        name: str,
    ) -> Optional[Object]:
        """Create tree trunk."""
        if not BLENDER_AVAILABLE:
            return None

        height = config.trunk_height * height_mult

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Create tapered cylinder
        segments = config.trunk_segments
        height_steps = 5

        for h in range(height_steps + 1):
            t = h / height_steps
            z = t * height
            radius = config.trunk_radius_base * (1 - t) + config.trunk_radius_top * t

            for i in range(segments):
                angle = (i / segments) * 2 * math.pi
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)

                # Add slight variation
                x += random.uniform(-0.02, 0.02)
                y += random.uniform(-0.02, 0.02)

                bm.verts.new((x, y, z))

        bm.verts.ensure_lookup_table()

        # Create faces
        for h in range(height_steps):
            for i in range(segments):
                next_i = (i + 1) % segments
                v1 = bm.verts[h * segments + i]
                v2 = bm.verts[h * segments + next_i]
                v3 = bm.verts[(h + 1) * segments + next_i]
                v4 = bm.verts[(h + 1) * segments + i]
                bm.faces.new([v1, v2, v3, v4])

        # Cap bottom
        bm.faces.new([bm.verts[i] for i in range(segments - 1, -1, -1)])

        # Cap top
        top_start = height_steps * segments
        bm.faces.new([bm.verts[top_start + i] for i in range(segments)])

        bm.to_mesh(mesh)
        bm.free()

        # Apply material
        mat = self._get_trunk_material(config)
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _create_deciduous_canopy(
        self,
        config: TreeConfig,
        height_mult: float,
        canopy_mult: float,
        name: str,
    ) -> Optional[Object]:
        """Create round/spreading deciduous canopy."""
        if not BLENDER_AVAILABLE:
            return None

        radius = config.canopy_radius * canopy_mult
        height = config.canopy_height * canopy_mult

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Create icosphere-like canopy
        segments = config.canopy_segments
        rings = 6

        # Generate sphere vertices with flattening
        for ring in range(rings + 1):
            phi = (ring / rings) * math.pi
            ring_radius = radius * math.sin(phi)

            # Flatten bottom and top
            z = height * 0.5 * math.cos(phi)
            z *= (1.0 - 0.3 * (1 - abs(math.cos(phi))))  # Flatten factor

            for i in range(segments):
                theta = (i / segments) * 2 * math.pi
                x = ring_radius * math.cos(theta)
                y = ring_radius * math.sin(theta)

                # Add organic variation
                x += random.uniform(-radius * 0.1, radius * 0.1)
                y += random.uniform(-radius * 0.1, radius * 0.1)
                z += random.uniform(-height * 0.05, height * 0.05)

                bm.verts.new((x, y, z))

        bm.verts.ensure_lookup_table()

        # Create faces between rings
        for ring in range(rings):
            for i in range(segments):
                next_i = (i + 1) % segments
                v1 = bm.verts[ring * segments + i]
                v2 = bm.verts[ring * segments + next_i]
                v3 = bm.verts[(ring + 1) * segments + next_i]
                v4 = bm.verts[(ring + 1) * segments + i]
                bm.faces.new([v1, v2, v3, v4])

        # Cap top
        top_start = rings * segments
        center = bm.verts.new((0, 0, height * 0.5))
        bm.verts.ensure_lookup_table()
        for i in range(segments):
            next_i = (i + 1) % segments
            bm.faces.new([center, bm.verts[top_start + i], bm.verts[top_start + next_i]])

        # Cap bottom
        bottom_center = bm.verts.new((0, 0, -height * 0.3))
        bm.verts.ensure_lookup_table()
        for i in range(segments - 1, -1, -1):
            next_i = (i - 1) % segments
            bm.faces.new([bottom_center, bm.verts[i], bm.verts[next_i]])

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_leaf_material(config)
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _create_conifer_canopy(
        self,
        config: TreeConfig,
        height_mult: float,
        canopy_mult: float,
        name: str,
    ) -> Optional[Object]:
        """Create conical conifer canopy (pine/cedar)."""
        if not BLENDER_AVAILABLE:
            return None

        radius = config.canopy_radius * canopy_mult
        height = config.canopy_height * canopy_mult

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Create layered cone (like pine tree)
        layers = 5
        segments = config.canopy_segments

        # Bottom layer vertices
        layer_verts = []
        for layer in range(layers):
            t = layer / (layers - 1)
            layer_radius = radius * (1 - t * 0.8)  # Taper to top
            layer_height = height * t
            layer_segments = segments - layer  # Fewer segments higher up

            verts_in_layer = []
            for i in range(layer_segments):
                angle = (i / layer_segments) * 2 * math.pi
                x = layer_radius * math.cos(angle)
                y = layer_radius * math.sin(angle)

                # Add variation
                x += random.uniform(-radius * 0.05, radius * 0.05)
                y += random.uniform(-radius * 0.05, radius * 0.05)

                vert = bm.verts.new((x, y, layer_height))
                verts_in_layer.append(vert)

            layer_verts.append(verts_in_layer)

            if layer > 0:
                bm.verts.ensure_lookup_table()
                # Connect to previous layer
                prev_layer = layer_verts[layer - 1]
                for i in range(len(verts_in_layer)):
                    next_i = (i + 1) % len(verts_in_layer)
                    # Find corresponding vertices in previous layer
                    prev_i = int(i * len(prev_layer) / len(verts_in_layer))
                    prev_next_i = (prev_i + 1) % len(prev_layer)

                    v1 = prev_layer[prev_i]
                    v2 = prev_layer[prev_next_i]
                    v3 = verts_in_layer[next_i]
                    v4 = verts_in_layer[i]

                    bm.faces.new([v1, v2, v3, v4])

        # Top point
        bm.verts.ensure_lookup_table()
        top = bm.verts.new((0, 0, height))
        bm.verts.ensure_lookup_table()

        top_layer = layer_verts[-1]
        for i in range(len(top_layer)):
            next_i = (i + 1) % len(top_layer)
            bm.faces.new([top, top_layer[i], top_layer[next_i]])

        # Bottom center
        bottom = bm.verts.new((0, 0, 0))
        bm.verts.ensure_lookup_table()
        bottom_layer = layer_verts[0]
        for i in range(len(bottom_layer) - 1, -1, -1):
            next_i = (i - 1) % len(bottom_layer)
            bm.faces.new([bottom, bottom_layer[i], bottom_layer[next_i]])

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_leaf_material(config)
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _get_trunk_material(self, config: TreeConfig) -> Optional[Any]:
        """Get or create trunk material."""
        if not BLENDER_AVAILABLE:
            return None

        if "trunk" in self._material_cache:
            return self._material_cache["trunk"]

        mat = bpy.data.materials.new("Tree_Trunk")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (*config.trunk_color, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
        bsdf.inputs["Metallic"].default_value = 0.0

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache["trunk"] = mat
        return mat

    def _get_leaf_material(self, config: TreeConfig) -> Optional[Any]:
        """Get or create leaf/canopy material."""
        if not BLENDER_AVAILABLE:
            return None

        cache_key = f"leaf_{config.leaf_color}"
        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        mat = bpy.data.materials.new("Tree_Canopy")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Coordinate
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-600, 0)

        # Noise for variation
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-400, 0)
        noise.inputs["Scale"].default_value = 5.0
        noise.inputs["Detail"].default_value = 2
        links.new(tex_coord.outputs["Generated"], noise.inputs["Vector"])

        # Color ramp
        color_ramp = nodes.new("ShaderNodeValToRGB")
        color_ramp.location = (-200, 0)
        color_ramp.color_ramp.elements[0].color = (
            config.leaf_color[0] * 0.8,
            config.leaf_color[1] * 0.8,
            config.leaf_color[2] * 0.8,
            1.0
        )
        color_ramp.color_ramp.elements[1].color = (
            config.leaf_color[0] * 1.2,
            config.leaf_color[1] * 1.2,
            config.leaf_color[2] * 1.2,
            1.0
        )
        links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])

        # BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Roughness"].default_value = 0.7
        bsdf.inputs["Metallic"].default_value = 0.0

        links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache[cache_key] = mat
        return mat


def place_trees_along_road(
    road_points: List[Tuple[float, float, float]],
    offset: float = 15.0,
    side: str = "right",
    spacing: float = 10.0,
    species: TreeSpecies = TreeSpecies.OAK,
    collection: Optional[Collection] = None,
) -> List[Object]:
    """
    Place trees along a road path.

    Args:
        road_points: Center line points of the road
        offset: Distance from road center
        side: "left", "right", or "both"
        spacing: Distance between trees
        species: Tree species to use
        collection: Collection to add objects to

    Returns:
        List of created tree objects
    """
    if not BLENDER_AVAILABLE or len(road_points) < 2:
        return []

    generator = TreeGenerator()
    config = TREE_CONFIGS.get(species, TreeConfig())
    objects = []

    # Determine which sides to place trees
    sides = []
    if side in ["right", "both"]:
        sides.append(1)
    if side in ["left", "both"]:
        sides.append(-1)

    for offset_sign in sides:
        total_length = 0.0
        next_tree_distance = spacing / 2

        for i in range(len(road_points) - 1):
            p1 = Vector(road_points[i])
            p2 = Vector(road_points[i + 1])
            direction = (p2 - p1).normalized()
            segment_length = (p2 - p1).length
            perpendicular = Vector((-direction.y, direction.x, 0))

            while next_tree_distance <= total_length + segment_length:
                t = (next_tree_distance - total_length) / segment_length
                position = p1 + direction * (segment_length * t)

                # Offset with random variation
                actual_offset = offset + random.uniform(-2.0, 2.0)
                tree_pos = position + perpendicular * actual_offset * offset_sign

                # Random species variation (30% chance of different species)
                tree_species = species
                if random.random() < 0.3:
                    tree_species = random.choice(list(TreeSpecies))

                # Create tree
                tree = generator.create_tree(
                    tree_species,
                    seed=int(next_tree_distance * 1000 + offset_sign),
                    name=f"Tree_{len(objects)}"
                )

                if tree:
                    tree.location = tree_pos

                    # Random rotation
                    tree.rotation_euler = (0, 0, random.uniform(0, 2 * math.pi))

                    if collection:
                        collection.objects.link(tree)

                    objects.append(tree)

                next_tree_distance += spacing

            total_length += segment_length

    return objects


def create_tree_cluster(
    center: Tuple[float, float, float],
    radius: float = 20.0,
    count: int = 10,
    species_list: Optional[List[TreeSpecies]] = None,
    collection: Optional[Collection] = None,
) -> List[Object]:
    """
    Create a cluster of trees at a location.

    Args:
        center: Center of cluster
        radius: Cluster radius
        count: Number of trees
        species_list: List of species to use (random selection)
        collection: Collection to add to

    Returns:
        List of created tree objects
    """
    if not BLENDER_AVAILABLE:
        return []

    generator = TreeGenerator()
    objects = []

    if species_list is None:
        species_list = [TreeSpecies.OAK, TreeSpecies.PINE, TreeSpecies.SWEETGUM]

    for i in range(count):
        # Random position within cluster
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, radius)
        x = center[0] + distance * math.cos(angle)
        y = center[1] + distance * math.sin(angle)
        z = center[2]

        # Random species
        species = random.choice(species_list)

        tree = generator.create_tree(
            species,
            seed=i * 1000 + int(distance * 100),
            name=f"ClusterTree_{i}"
        )

        if tree:
            tree.location = (x, y, z)
            tree.rotation_euler = (0, 0, random.uniform(0, 2 * math.pi))

            if collection:
                collection.objects.link(tree)

            objects.append(tree)

    return objects


__all__ = [
    "TreeSpecies",
    "TreeConfig",
    "TREE_CONFIGS",
    "TreeGenerator",
    "place_trees_along_road",
    "create_tree_cluster",
]
