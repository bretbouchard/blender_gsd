"""
Weight Painter

Automatic weight painting for meshes.

Phase 13.0: Rigging Foundation (REQ-ANIM-01)
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import math

from .types import WeightMethod


class AutoWeightPainter:
    """
    Automatic weight painting based on bone proximity.

    Usage:
        painter = AutoWeightPainter(armature, mesh)
        weights = painter.calculate_weights(method="heat")
        painter.apply_weights(weights)
    """

    def __init__(self, armature: Any, mesh: Any):
        """
        Initialize the weight painter.

        Args:
            armature: The armature object
            mesh: The mesh object to weight paint
        """
        self.armature = armature
        self.mesh = mesh
        self.bone_matrices: Dict[str, Any] = {}
        self._armature_matrix = None
        self._mesh_matrix = None

    def calculate_weights(
        self,
        method: str = "heat",
        bones: Optional[List[str]] = None
    ) -> Dict[str, List[float]]:
        """
        Calculate vertex weights for bones.

        Args:
            method: Weighting method ("heat", "distance", "envelope")
            bones: Optional list of bone names (defaults to all deform bones)

        Returns:
            Dict mapping bone names to weight lists
        """
        # Build bone world matrices
        self._build_bone_matrices()

        # Get mesh vertices in world space
        vertices = self._get_world_vertices()

        # Get bones to weight
        if bones is None:
            bones = self._get_deform_bone_names()

        weights = {}
        for bone_name in bones:
            if bone_name in self.armature.data.bones:
                weights[bone_name] = self._calculate_bone_weights(
                    bone_name, vertices, method
                )

        return weights

    def _build_bone_matrices(self) -> None:
        """Build world-space matrices for each bone."""
        self._armature_matrix = self.armature.matrix_world

        for bone in self.armature.data.bones:
            self.bone_matrices[bone.name] = (
                self._armature_matrix @ bone.matrix_local
            )

    def _get_world_vertices(self) -> List[Tuple[float, float, float]]:
        """Get mesh vertices in world space."""
        self._mesh_matrix = self.mesh.matrix_world
        vertices = []

        for v in self.mesh.data.vertices:
            # Apply object transform
            co = self._mesh_matrix @ v.co
            vertices.append((co.x, co.y, co.z))

        return vertices

    def _get_deform_bone_names(self) -> List[str]:
        """Get names of all deform bones."""
        return [b.name for b in self.armature.data.bones if b.use_deform]

    def _calculate_bone_weights(
        self,
        bone_name: str,
        vertices: List[Tuple[float, float, float]],
        method: str
    ) -> List[float]:
        """
        Calculate weights for a single bone.

        Args:
            bone_name: Name of the bone
            vertices: List of vertex positions in world space
            method: Weighting method

        Returns:
            List of weights (one per vertex)
        """
        bone = self.armature.data.bones[bone_name]

        # Get bone head and tail in world space
        bone_matrix = self._armature_matrix @ bone.matrix_local

        try:
            from mathutils import Vector
            bone_head = bone_matrix @ Vector((0, 0, 0))
            bone_tail = bone_matrix @ Vector((0, bone.length, 0))
            head = (bone_head.x, bone_head.y, bone_head.z)
            tail = (bone_tail.x, bone_tail.y, bone_tail.z)
        except ImportError:
            # Fallback without mathutils
            head = (
                bone_matrix[0][3],
                bone_matrix[1][3],
                bone_matrix[2][3]
            )
            tail = head  # Simplified fallback

        weights = []
        for vertex in vertices:
            if method == "distance":
                weight = self._distance_weight(vertex, head, tail)
            elif method == "heat":
                weight = self._heat_weight(vertex, head, tail)
            elif method == "envelope":
                weight = self._envelope_weight(vertex, head, tail, bone)
            else:
                weight = 0.0
            weights.append(weight)

        return weights

    def _distance_weight(
        self,
        vertex: Tuple[float, float, float],
        bone_head: Tuple[float, float, float],
        bone_tail: Tuple[float, float, float]
    ) -> float:
        """
        Calculate weight based on inverse distance to bone.

        Args:
            vertex: Vertex position
            bone_head: Bone head position
            bone_tail: Bone tail position

        Returns:
            Weight value (0-1)
        """
        dist = self._point_to_segment_distance(vertex, bone_head, bone_tail)
        # Inverse distance weighting with falloff
        return 1.0 / (1.0 + dist * 2.0)

    def _heat_weight(
        self,
        vertex: Tuple[float, float, float],
        bone_head: Tuple[float, float, float],
        bone_tail: Tuple[float, float, float]
    ) -> float:
        """
        Calculate weight using heat diffusion approximation.

        Args:
            vertex: Vertex position
            bone_head: Bone head position
            bone_tail: Bone tail position

        Returns:
            Weight value (0-1)
        """
        dist = self._point_to_segment_distance(vertex, bone_head, bone_tail)
        # Exponential falloff (heat equation approximation)
        return max(0.0, math.exp(-dist * 3.0))

    def _envelope_weight(
        self,
        vertex: Tuple[float, float, float],
        bone_head: Tuple[float, float, float],
        bone_tail: Tuple[float, float, float],
        bone: Any
    ) -> float:
        """
        Calculate weight based on bone envelope.

        Args:
            vertex: Vertex position
            bone_head: Bone head position
            bone_tail: Bone tail position
            bone: The bone object for envelope parameters

        Returns:
            Weight value (0-1)
        """
        # Get envelope distance
        dist = self._point_to_segment_distance(vertex, bone_head, bone_tail)

        # Get envelope radius (head and tail)
        head_radius = getattr(bone, 'head_radius', 0.1)
        tail_radius = getattr(bone, 'tail_radius', 0.05)

        # Interpolate radius along bone
        t = self._get_segment_parameter(vertex, bone_head, bone_tail)
        radius = head_radius + (tail_radius - head_radius) * t

        # Calculate weight based on distance to envelope
        if dist < radius:
            return 1.0
        elif dist < radius * 2.0:
            return 1.0 - (dist - radius) / radius
        else:
            return 0.0

    def _point_to_segment_distance(
        self,
        point: Tuple[float, float, float],
        seg_start: Tuple[float, float, float],
        seg_end: Tuple[float, float, float]
    ) -> float:
        """
        Calculate distance from point to line segment.

        Args:
            point: Point position
            seg_start: Segment start position
            seg_end: Segment end position

        Returns:
            Distance from point to segment
        """
        # Line vector
        line_x = seg_end[0] - seg_start[0]
        line_y = seg_end[1] - seg_start[1]
        line_z = seg_end[2] - seg_start[2]
        line_length_sq = line_x*line_x + line_y*line_y + line_z*line_z

        if line_length_sq == 0:
            # Degenerate segment (point)
            dx = point[0] - seg_start[0]
            dy = point[1] - seg_start[1]
            dz = point[2] - seg_start[2]
            return math.sqrt(dx*dx + dy*dy + dz*dz)

        # Project point onto line
        point_x = point[0] - seg_start[0]
        point_y = point[1] - seg_start[1]
        point_z = point[2] - seg_start[2]

        projection = (
            point_x * line_x +
            point_y * line_y +
            point_z * line_z
        ) / line_length_sq

        # Clamp to segment
        projection = max(0.0, min(1.0, projection))

        # Closest point on segment
        closest_x = seg_start[0] + projection * line_x
        closest_y = seg_start[1] + projection * line_y
        closest_z = seg_start[2] + projection * line_z

        # Distance from point to closest
        dx = point[0] - closest_x
        dy = point[1] - closest_y
        dz = point[2] - closest_z

        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def _get_segment_parameter(
        self,
        point: Tuple[float, float, float],
        seg_start: Tuple[float, float, float],
        seg_end: Tuple[float, float, float]
    ) -> float:
        """
        Get parameter t (0-1) for closest point on segment.

        Args:
            point: Point position
            seg_start: Segment start position
            seg_end: Segment end position

        Returns:
            Parameter t (0 = start, 1 = end)
        """
        line_x = seg_end[0] - seg_start[0]
        line_y = seg_end[1] - seg_start[1]
        line_z = seg_end[2] - seg_start[2]
        line_length_sq = line_x*line_x + line_y*line_y + line_z*line_z

        if line_length_sq == 0:
            return 0.0

        point_x = point[0] - seg_start[0]
        point_y = point[1] - seg_start[1]
        point_z = point[2] - seg_start[2]

        projection = (
            point_x * line_x +
            point_y * line_y +
            point_z * line_z
        ) / line_length_sq

        return max(0.0, min(1.0, projection))

    def apply_weights(
        self,
        weights: Dict[str, List[float]],
        normalize: bool = True,
        threshold: float = 0.001
    ) -> None:
        """
        Apply calculated weights to the mesh.

        Args:
            weights: Dict mapping bone names to weight lists
            normalize: Whether to normalize weights per vertex
            threshold: Minimum weight to include
        """
        # Ensure vertex groups exist
        for bone_name in weights.keys():
            if bone_name not in self.mesh.vertex_groups:
                self.mesh.vertex_groups.new(name=bone_name)

        # Apply weights
        for bone_name, bone_weights in weights.items():
            vg = self.mesh.vertex_groups[bone_name]

            # Build list of (vertex_index, weight) for weights above threshold
            for i, weight in enumerate(bone_weights):
                if weight > threshold:
                    vg.add([i], weight, 'REPLACE')

        # Normalize if requested
        if normalize:
            self._normalize_weights()

    def _normalize_weights(self) -> None:
        """Normalize weights so they sum to 1 for each vertex."""
        try:
            import bpy
            bpy.context.view_layer.objects.active = self.mesh
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            bpy.ops.object.vertex_group_normalize_all(lock_active=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            # Manual normalization fallback
            self._manual_normalize()

    def _manual_normalize(self) -> None:
        """Manually normalize weights without bpy.ops."""
        num_vertices = len(self.mesh.data.vertices)

        for v_idx in range(num_vertices):
            # Get all weights for this vertex
            total = 0.0
            vertex_weights = []

            for vg in self.mesh.vertex_groups:
                try:
                    weight = vg.weight(v_idx)
                    if weight > 0:
                        vertex_weights.append((vg, weight))
                        total += weight
                except RuntimeError:
                    pass  # Vertex not in group

            # Normalize
            if total > 0:
                for vg, weight in vertex_weights:
                    vg.add([v_idx], weight / total, 'REPLACE')


def auto_weight_mesh(
    armature: Any,
    mesh: Any,
    method: str = "heat",
    normalize: bool = True
) -> Dict[str, List[float]]:
    """
    Automatically weight paint a mesh to an armature.

    Args:
        armature: The armature object
        mesh: The mesh object
        method: Weighting method ("heat", "distance", "envelope")
        normalize: Whether to normalize weights

    Returns:
        Dict of calculated weights
    """
    painter = AutoWeightPainter(armature, mesh)
    weights = painter.calculate_weights(method=method)
    painter.apply_weights(weights, normalize=normalize)
    return weights


def parent_mesh_to_armature(
    armature: Any,
    mesh: Any,
    with_auto_weights: bool = True
) -> None:
    """
    Parent a mesh to an armature with optional automatic weights.

    Args:
        armature: The armature object
        mesh: The mesh object
        with_auto_weights: Whether to use automatic weights
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("parent_mesh_to_armature requires Blender")

    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    # Select mesh and armature
    mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    # Parent with auto weights or empty
    if with_auto_weights:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    else:
        bpy.ops.object.parent_set(type='ARMATURE')


def transfer_weights(
    source_mesh: Any,
    target_mesh: Any,
    method: str = "nearest"
) -> None:
    """
    Transfer vertex weights from one mesh to another.

    Args:
        source_mesh: Source mesh with weights
        target_mesh: Target mesh to receive weights
        method: Transfer method ("nearest", "projected", "interpolated")
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("transfer_weights requires Blender")

    # Use Blender's data transfer modifier
    modifier = target_mesh.modifiers.new(name="WeightTransfer", type='DATA_TRANSFER')

    modifier.object = source_mesh
    modifier.use_vert_data = True
    modifier.data_types_verts = {'VGROUP_WEIGHTS'}

    if method == "nearest":
        modifier.vert_mapping = 'NEAREST'
    elif method == "projected":
        modifier.vert_mapping = 'POLYINTERP_NEAREST'
    else:
        modifier.vert_mapping = 'TOPOLOGY'

    # Apply modifier
    bpy.context.view_layer.objects.active = target_mesh
    bpy.ops.object.modifier_apply(modifier="WeightTransfer")


def mirror_weights(mesh: Any, axis: str = "X") -> None:
    """
    Mirror vertex weights across an axis.

    Args:
        mesh: The mesh object
        axis: Axis to mirror across ("X", "Y", or "Z")
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("mirror_weights requires Blender")

    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

    # Mirror weights
    bpy.ops.object.vertex_group_mirror(
        mirror_weights=True,
        flip_group_names=True,
        all_groups=True,
        use_topology=False
    )

    bpy.ops.object.mode_set(mode='OBJECT')


def clean_weights(
    mesh: Any,
    threshold: float = 0.01,
    keep_single: bool = False
) -> int:
    """
    Remove weak weights from mesh.

    Args:
        mesh: The mesh object
        threshold: Minimum weight to keep
        keep_single: Keep at least one group per vertex

    Returns:
        Number of weights removed
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("clean_weights requires Blender")

    removed = 0
    num_vertices = len(mesh.data.vertices)

    for v_idx in range(num_vertices):
        weights = []
        max_weight = 0.0
        max_vg = None

        # Collect weights for vertex
        for vg in mesh.vertex_groups:
            try:
                weight = vg.weight(v_idx)
                if weight > 0:
                    weights.append((vg, weight))
                    if weight > max_weight:
                        max_weight = weight
                        max_vg = vg
            except RuntimeError:
                pass

        # Remove below threshold
        for vg, weight in weights:
            if weight < threshold:
                if keep_single and vg == max_vg:
                    continue  # Keep strongest weight
                vg.remove([v_idx])
                removed += 1

    return removed


def limit_influence(mesh: Any, max_groups: int = 4) -> int:
    """
    Limit the number of bone influences per vertex.

    Args:
        mesh: The mesh object
        max_groups: Maximum number of groups per vertex

    Returns:
        Number of weights removed
    """
    removed = 0
    num_vertices = len(mesh.data.vertices)

    for v_idx in range(num_vertices):
        # Collect weights for vertex
        weights = []
        for vg in mesh.vertex_groups:
            try:
                weight = vg.weight(v_idx)
                if weight > 0:
                    weights.append((vg, weight))
            except RuntimeError:
                pass

        # Sort by weight descending
        weights.sort(key=lambda x: x[1], reverse=True)

        # Remove weights beyond limit
        for vg, weight in weights[max_groups:]:
            vg.remove([v_idx])
            removed += 1

    return removed
