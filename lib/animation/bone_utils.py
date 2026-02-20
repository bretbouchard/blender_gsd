"""
Bone Utilities

Utility functions for working with bones and armatures.

Phase 13.0: Rigging Foundation (REQ-ANIM-01)
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any
import math


def get_bone_chain(armature: Any, start_bone: str, end_bone: str) -> List[str]:
    """
    Get all bones in a chain from start to end.

    Args:
        armature: The armature object
        start_bone: Name of the starting bone
        end_bone: Name of the ending bone

    Returns:
        List of bone names in order from start to end
    """
    chain = []
    current = armature.data.bones.get(end_bone)

    while current:
        chain.insert(0, current.name)
        if current.name == start_bone:
            return chain
        current = current.parent

    return chain


def mirror_bone_name(name: str) -> str:
    """
    Mirror a bone name (L <-> R).

    Supports common naming conventions:
    - _L / _R
    - .L / .R
    - _left / _right
    - Left / Right prefix

    Args:
        name: The bone name to mirror

    Returns:
        The mirrored bone name
    """
    # _L / _R suffix
    if name.endswith('_L'):
        return name[:-2] + '_R'
    elif name.endswith('_R'):
        return name[:-2] + '_L'

    # .L / .R suffix
    elif '.L' in name:
        return name.replace('.L', '.R')
    elif '.R' in name:
        return name.replace('.R', '.L')

    # _left / _right suffix
    elif name.endswith('_left'):
        return name[:-5] + '_right'
    elif name.endswith('_right'):
        return name[:-6] + '_left'

    # Left / Right prefix
    elif name.startswith('Left'):
        return 'Right' + name[4:]
    elif name.startswith('Right'):
        return 'Left' + name[5:]

    # No mirror pattern found
    return name


def get_bone_length(bone: Any) -> float:
    """
    Get the length of a bone.

    Args:
        bone: A bone object

    Returns:
        The bone length
    """
    try:
        from mathutils import Vector
        return (Vector(bone.tail) - Vector(bone.head)).length
    except ImportError:
        # Fallback without mathutils
        dx = bone.tail[0] - bone.head[0]
        dy = bone.tail[1] - bone.head[1]
        dz = bone.tail[2] - bone.head[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)


def get_bone_direction(bone: Any) -> Tuple[float, float, float]:
    """
    Get the normalized direction vector of a bone.

    Args:
        bone: A bone object

    Returns:
        Normalized direction vector as (x, y, z)
    """
    try:
        from mathutils import Vector
        direction = Vector(bone.tail) - Vector(bone.head)
        direction.normalize()
        return tuple(direction)
    except ImportError:
        # Fallback without mathutils
        dx = bone.tail[0] - bone.head[0]
        dy = bone.tail[1] - bone.head[1]
        dz = bone.tail[2] - bone.head[2]
        length = math.sqrt(dx*dx + dy*dy + dz*dz)

        if length == 0:
            return (0.0, 0.0, 1.0)

        return (dx/length, dy/length, dz/length)


def align_bone_to_vector(bone: Any, vector: Tuple[float, float, float], roll: float = 0.0) -> None:
    """
    Align a bone to a direction vector.

    Args:
        bone: An edit bone object
        vector: Target direction vector
        roll: Roll angle in radians
    """
    try:
        from mathutils import Vector, Matrix
    except ImportError:
        return

    # Get current direction
    current_dir = Vector(bone.tail) - Vector(bone.head)
    current_length = current_dir.length

    if current_length == 0:
        return

    current_dir.normalize()
    target_dir = Vector(vector).normalized()

    # Calculate rotation
    rotation = current_dir.rotation_difference(target_dir)

    # Apply rotation
    head = Vector(bone.head)
    bone.transform(rotation.to_matrix().to_4x4())
    bone.head = head
    bone.tail = head + target_dir * current_length
    bone.roll = roll


def scale_bone(bone: Any, scale: float) -> None:
    """
    Scale a bone from its head.

    Args:
        bone: An edit bone object
        scale: Scale factor
    """
    try:
        from mathutils import Vector
        direction = Vector(bone.tail) - Vector(bone.head)
        bone.tail = Vector(bone.head) + direction * scale
    except ImportError:
        dx = bone.tail[0] - bone.head[0]
        dy = bone.tail[1] - bone.head[1]
        dz = bone.tail[2] - bone.head[2]
        bone.tail = (
            bone.head[0] + dx * scale,
            bone.head[1] + dy * scale,
            bone.head[2] + dz * scale
        )


def duplicate_bone_chain(
    armature: Any,
    chain: List[str],
    suffix: str = "_copy"
) -> List[str]:
    """
    Duplicate a chain of bones with a suffix.

    Args:
        armature: The armature object
        chain: List of bone names to duplicate
        suffix: Suffix for new bone names

    Returns:
        List of new bone names
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("duplicate_bone_chain requires Blender")

    new_names = []

    # Switch to edit mode
    current_mode = armature.mode
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    try:
        for bone_name in chain:
            if bone_name in armature.data.edit_bones:
                original = armature.data.edit_bones[bone_name]
                new_name = f"{bone_name}{suffix}"
                new_bone = armature.data.edit_bones.new(new_name)
                new_bone.head = original.head
                new_bone.tail = original.tail
                new_bone.roll = original.roll
                new_bone.layers = original.layers
                new_bone.use_deform = original.use_deform
                new_names.append(new_bone.name)
    finally:
        bpy.ops.object.mode_set(mode=current_mode)

    return new_names


def connect_bone_chain(armature: Any, chain: List[str]) -> None:
    """
    Connect bones in a chain (child head = parent tail).

    Args:
        armature: The armature object
        chain: List of bone names in order
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("connect_bone_chain requires Blender")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    try:
        for i, bone_name in enumerate(chain[1:], 1):
            if bone_name in armature.data.edit_bones:
                bone = armature.data.edit_bones[bone_name]
                parent_name = chain[i - 1]

                if parent_name in armature.data.edit_bones:
                    parent = armature.data.edit_bones[parent_name]
                    bone.parent = parent
                    bone.head = parent.tail
                    bone.use_connect = True
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def clear_bone_constraints(armature: Any, bone_name: str) -> int:
    """
    Remove all constraints from a bone.

    Args:
        armature: The armature object
        bone_name: Name of the bone

    Returns:
        Number of constraints removed
    """
    if bone_name not in armature.pose.bones:
        return 0

    pose_bone = armature.pose.bones[bone_name]
    count = len(pose_bone.constraints)

    for con in list(pose_bone.constraints):
        pose_bone.constraints.remove(con)

    return count


def copy_bone_constraints(
    source_armature: Any,
    source_bone: str,
    target_armature: Any,
    target_bone: str
) -> int:
    """
    Copy constraints from one bone to another.

    Args:
        source_armature: Source armature object
        source_bone: Source bone name
        target_armature: Target armature object
        target_bone: Target bone name

    Returns:
        Number of constraints copied
    """
    if source_bone not in source_armature.pose.bones:
        return 0
    if target_bone not in target_armature.pose.bones:
        return 0

    source_pb = source_armature.pose.bones[source_bone]
    target_pb = target_armature.pose.bones[target_bone]

    count = 0
    for con in source_pb.constraints:
        try:
            new_con = target_pb.constraints.new(con.type)

            # Copy properties
            for prop in dir(con):
                if prop.startswith('_') or prop in ['type', 'is_valid', 'bl_rna', 'rna_type']:
                    continue
                try:
                    value = getattr(con, prop)
                    if not callable(value):
                        setattr(new_con, prop, value)
                except (AttributeError, TypeError):
                    pass

            count += 1
        except TypeError:
            pass  # Constraint type not available

    return count


def get_bone_world_matrix(armature: Any, bone_name: str) -> Optional[Any]:
    """
    Get the world-space matrix of a bone.

    Args:
        armature: The armature object
        bone_name: Name of the bone

    Returns:
        4x4 matrix or None if bone not found
    """
    if bone_name not in armature.pose.bones:
        return None

    pose_bone = armature.pose.bones[bone_name]
    return armature.matrix_world @ pose_bone.matrix


def get_bone_world_head(armature: Any, bone_name: str) -> Optional[Tuple[float, float, float]]:
    """
    Get the world-space head position of a bone.

    Args:
        armature: The armature object
        bone_name: Name of the bone

    Returns:
        (x, y, z) tuple or None if bone not found
    """
    matrix = get_bone_world_matrix(armature, bone_name)
    if matrix is None:
        return None

    try:
        from mathutils import Vector
        head = matrix @ Vector((0, 0, 0, 1))
        return (head.x, head.y, head.z)
    except ImportError:
        # Fallback without mathutils
        return (
            matrix[0][3],
            matrix[1][3],
            matrix[2][3]
        )


def get_bone_world_tail(armature: Any, bone_name: str) -> Optional[Tuple[float, float, float]]:
    """
    Get the world-space tail position of a bone.

    Args:
        armature: The armature object
        bone_name: Name of the bone

    Returns:
        (x, y, z) tuple or None if bone not found
    """
    if bone_name not in armature.data.bones:
        return None

    bone = armature.data.bones[bone_name]
    bone_matrix = armature.matrix_world @ bone.matrix_local

    try:
        from mathutils import Vector
        tail_local = Vector((0, bone.length, 0, 1))
        tail = bone_matrix @ tail_local
        return (tail.x, tail.y, tail.z)
    except ImportError:
        # Fallback
        return (
            bone_matrix[0][3],
            bone_matrix[1][3],
            bone_matrix[2][3]
        )


def select_bone_chain(armature: Any, bone_name: str, extend: bool = False) -> List[str]:
    """
    Select a bone and all its descendants.

    Args:
        armature: The armature object
        bone_name: Starting bone name
        extend: Whether to extend current selection

    Returns:
        List of selected bone names
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("select_bone_chain requires Blender")

    if bone_name not in armature.data.bones:
        return []

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    if not extend:
        bpy.ops.armature.select_all(action='DESELECT')

    selected = []

    def select_recursive(bone_name: str):
        bone = armature.data.edit_bones.get(bone_name)
        if bone:
            bone.select = True
            bone.select_head = True
            bone.select_tail = True
            selected.append(bone_name)

            # Select children
            for child in bone.children:
                select_recursive(child.name)

    select_recursive(bone_name)
    return selected


def hide_bone_chain(armature: Any, bone_name: str, hide: bool = True) -> int:
    """
    Hide/unhide a bone and all its descendants.

    Args:
        armature: The armature object
        bone_name: Starting bone name
        hide: Whether to hide (True) or show (False)

    Returns:
        Number of bones affected
    """
    if bone_name not in armature.data.bones:
        return 0

    count = 0

    def hide_recursive(bone):
        nonlocal count
        bone.hide = hide
        count += 1
        for child in bone.children:
            hide_recursive(child)

    hide_recursive(armature.data.bones[bone_name])
    return count


def get_all_bone_names(armature: Any) -> List[str]:
    """
    Get all bone names in an armature.

    Args:
        armature: The armature object

    Returns:
        List of bone names
    """
    return [bone.name for bone in armature.data.bones]


def get_deform_bones(armature: Any) -> List[str]:
    """
    Get all deform bone names in an armature.

    Args:
        armature: The armature object

    Returns:
        List of deform bone names
    """
    return [bone.name for bone in armature.data.bones if bone.use_deform]


def rename_bone_prefix(
    armature: Any,
    old_prefix: str,
    new_prefix: str
) -> Dict[str, str]:
    """
    Rename all bones with a given prefix.

    Args:
        armature: The armature object
        old_prefix: Prefix to replace
        new_prefix: New prefix

    Returns:
        Dict mapping old names to new names
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("rename_bone_prefix requires Blender")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    renames = {}

    for bone in armature.data.edit_bones:
        if bone.name.startswith(old_prefix):
            old_name = bone.name
            new_name = new_prefix + bone.name[len(old_prefix):]
            bone.name = new_name
            renames[old_name] = bone.name

    return renames
