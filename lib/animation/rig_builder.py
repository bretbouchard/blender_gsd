"""
Rig Builder

Build Blender armatures from configuration.

Phase 13.0: Rigging Foundation (REQ-ANIM-01)
"""

from __future__ import annotations
from typing import Optional, Dict, List, Any
import uuid
from datetime import datetime

from .types import RigConfig, BoneConfig, RigInstance


class RigBuilder:
    """
    Build Blender armatures from RigConfig.

    Usage:
        config = load_rig_preset("human_biped")
        builder = RigBuilder(config)
        armature = builder.build("MyRig")
    """

    def __init__(self, config: RigConfig):
        self.config = config
        self.armature: Optional[Any] = None  # bpy.types.Object when in Blender
        self.bones: Dict[str, Any] = {}  # bone name -> edit bone
        self._instance_id: str = str(uuid.uuid4())[:8]

    def build(self, name: Optional[str] = None) -> Any:
        """
        Build the armature from config.

        Args:
            name: Optional name for the armature object

        Returns:
            The created armature object
        """
        try:
            import bpy
        except ImportError:
            raise ImportError("RigBuilder requires Blender (bpy module)")

        armature_name = name or f"rig_{self.config.id}"

        # Create armature data
        armature_data = bpy.data.armatures.new(armature_name)
        self.armature = bpy.data.objects.new(armature_name, armature_data)

        # Link to scene
        bpy.context.collection.objects.link(self.armature)
        bpy.context.view_layer.objects.active = self.armature

        # Store reference for undo
        armature_data['rig_config_id'] = self.config.id
        armature_data['rig_instance_id'] = self._instance_id

        # Enter edit mode to add bones
        bpy.ops.object.mode_set(mode='EDIT')

        try:
            # Build bones in order (parents first)
            self._build_bones()
            self._setup_hierarchy()
            self._apply_constraints()
            self._create_bone_groups()
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        return self.armature

    def _build_bones(self) -> None:
        """Build all bones from config."""
        import bpy

        # Sort bones by dependency (parents first)
        sorted_bones = self._sort_bones_by_dependency()

        for bone_config in sorted_bones:
            bone = self.armature.data.edit_bones.new(bone_config.id)

            # Set head and tail
            bone.head = bone_config.head
            bone.tail = bone_config.tail
            bone.roll = bone_config.roll

            # Set layers
            layers = [i in bone_config.layers for i in range(32)]
            bone.layers = layers

            # Set bone properties
            bone.use_deform = bone_config.use_deform
            bone.use_envelope_multiply = bone_config.use_envelope_multiply
            bone.head_radius = bone_config.head_radius
            bone.tail_radius = bone_config.tail_radius
            bone.hide = bone_config.hide

            # Store reference
            self.bones[bone_config.id] = bone

    def _sort_bones_by_dependency(self) -> List[BoneConfig]:
        """Sort bones so parents come before children."""
        bone_map = {b.id: b for b in self.config.bones}
        sorted_bones = []
        visited = set()

        def visit(bone_id: str):
            if bone_id in visited or bone_id not in bone_map:
                return
            visited.add(bone_id)
            bone = bone_map[bone_id]
            if bone.parent:
                visit(bone.parent)
            sorted_bones.append(bone)

        for bone in self.config.bones:
            visit(bone.id)

        return sorted_bones

    def _setup_hierarchy(self) -> None:
        """Setup parent-child relationships."""
        for bone_config in self.config.bones:
            if bone_config.parent is None:
                continue

            bone = self.bones.get(bone_config.id)
            parent = self.bones.get(bone_config.parent)

            if bone and parent:
                bone.parent = parent
                if bone_config.use_connect:
                    bone.use_connect = True
                    bone.head = parent.tail

    def _apply_constraints(self) -> None:
        """Apply bone constraints."""
        import bpy

        # Switch to pose mode for constraints
        bpy.ops.object.mode_set(mode='POSE')

        for constraint in self.config.constraints:
            if constraint.bone not in self.armature.pose.bones:
                continue

            pose_bone = self.armature.pose.bones[constraint.bone]

            # Create constraint
            con_type = constraint.type.upper()
            if not hasattr(pose_bone.constraints, con_type.lower()):
                continue

            con = pose_bone.constraints.new(con_type.lower())

            # Set target
            if constraint.target:
                if constraint.target == "SELF":
                    con.target = self.armature
                else:
                    # Try to find object in scene
                    import bpy
                    if constraint.target in bpy.data.objects:
                        con.target = bpy.data.objects[constraint.target]
                    elif constraint.target in self.bones:
                        con.target = self.armature
                        con.subtarget = constraint.target

            if constraint.subtarget:
                con.subtarget = constraint.subtarget

            con.influence = constraint.influence

            # Apply additional properties
            for key, value in constraint.properties.items():
                if hasattr(con, key):
                    try:
                        setattr(con, key, value)
                    except (AttributeError, TypeError):
                        pass

    def _create_bone_groups(self) -> None:
        """Create bone groups for organization."""
        import bpy

        # Ensure we're in pose mode
        if self.armature.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        for group_config in self.config.groups:
            bg = self.armature.pose.bone_groups.new(name=group_config.name)

            # Set color set
            color_set = group_config.color_set.upper()
            if hasattr(bg, 'color_set') and color_set in [
                'DEFAULT', 'THEME01', 'THEME02', 'THEME03',
                'THEME04', 'THEME05', 'THEME06', 'THEME07',
                'THEME08', 'THEME09', 'THEME10', 'THEME11',
                'THEME12', 'THEME13', 'THEME14', 'THEME15',
                'THEME16', 'THEME17', 'THEME18', 'THEME19', 'THEME20',
                'CUSTOM'
            ]:
                bg.color_set = color_set

            # Assign bones to group
            for bone_name in group_config.bones:
                if bone_name in self.armature.pose.bones:
                    self.armature.pose.bones[bone_name].bone_group = bg

    def create_mirror_bones(self) -> Dict[str, str]:
        """
        Create mirrored bones for _L/_R naming convention.

        Returns:
            Dict mapping original bone names to mirror bone names
        """
        import bpy

        bpy.ops.object.mode_set(mode='EDIT')

        mirror_map = {}

        for bone_config in self.config.bones:
            if not bone_config.mirror:
                continue

            original = self.bones.get(bone_config.id)
            if not original:
                continue

            mirror_name = bone_config.mirror

            # Check if mirror already exists
            if mirror_name in self.armature.data.edit_bones:
                continue

            # Create mirrored bone
            mirror_bone = self.armature.data.edit_bones.new(mirror_name)

            # Mirror the head and tail positions (X axis)
            mirror_bone.head = (-original.head[0], original.head[1], original.head[2])
            mirror_bone.tail = (-original.tail[0], original.tail[1], original.tail[2])
            mirror_bone.roll = -original.roll

            # Copy properties
            mirror_bone.use_deform = original.use_deform
            mirror_bone.layers = original.layers

            # Setup parent (mirror of original parent)
            if original.parent:
                parent_name = original.parent.name
                if parent_name.endswith('_L'):
                    mirror_parent = parent_name.replace('_L', '_R')
                elif parent_name.endswith('_R'):
                    mirror_parent = parent_name.replace('_R', '_L')
                else:
                    mirror_parent = parent_name

                if mirror_parent in self.bones:
                    mirror_bone.parent = self.bones[mirror_parent]
                    if original.use_connect:
                        mirror_bone.use_connect = True
                        mirror_bone.head = self.bones[mirror_parent].tail

            self.bones[mirror_name] = mirror_bone
            mirror_map[bone_config.id] = mirror_name

        return mirror_map

    def get_instance(self) -> RigInstance:
        """Get a RigInstance representing this built rig."""
        return RigInstance(
            id=self._instance_id,
            config_id=self.config.id,
            armature_name=self.armature.name if self.armature else "",
            created_at=datetime.now().isoformat(),
        )


def build_rig_from_config(config: RigConfig, name: Optional[str] = None) -> Any:
    """
    Convenience function to build a rig from config.

    Args:
        config: RigConfig object
        name: Optional name for the armature

    Returns:
        The created armature object
    """
    builder = RigBuilder(config)
    return builder.build(name)


def build_rig_from_preset(preset_id: str, name: Optional[str] = None) -> Any:
    """
    Build a rig from a preset configuration.

    Args:
        preset_id: The preset identifier
        name: Optional name for the armature

    Returns:
        The created armature object
    """
    from .preset_loader import load_rig_preset
    config = load_rig_preset(preset_id)
    return build_rig_from_config(config, name)


def create_custom_rig(
    name: str,
    bones: List[Dict[str, Any]],
    **kwargs
) -> RigConfig:
    """
    Create a custom rig configuration.

    Args:
        name: Name for the rig
        bones: List of bone configurations (dicts)
        **kwargs: Additional RigConfig fields

    Returns:
        RigConfig object
    """
    from .types import BoneConfig, RigType

    bone_configs = [BoneConfig.from_dict(b) for b in bones]

    return RigConfig(
        id=name.lower().replace(' ', '_'),
        name=name,
        rig_type=kwargs.get('rig_type', RigType.CUSTOM),
        description=kwargs.get('description', ''),
        bones=bone_configs,
        constraints=kwargs.get('constraints', []),
        groups=kwargs.get('groups', []),
        ik_chains=kwargs.get('ik_chains', []),
        custom_properties=kwargs.get('custom_properties', {}),
    )


def duplicate_rig(
    armature: Any,
    new_name: Optional[str] = None,
    prefix: str = "",
    suffix: str = "_copy"
) -> Any:
    """
    Duplicate an existing rig.

    Args:
        armature: The armature object to duplicate
        new_name: Optional new name
        prefix: Optional prefix for the new name
        suffix: Optional suffix for the new name

    Returns:
        The duplicated armature
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("duplicate_rig requires Blender (bpy module)")

    # Duplicate the object
    new_armature = armature.copy()
    new_armature.data = armature.data.copy()

    # Set name
    if new_name:
        new_armature.name = new_name
    else:
        base_name = armature.name
        new_armature.name = f"{prefix}{base_name}{suffix}"

    # Link to collection
    bpy.context.collection.objects.link(new_armature)

    return new_armature


def merge_rigs(
    *armatures: Any,
    name: Optional[str] = None
) -> Any:
    """
    Merge multiple armatures into one.

    Args:
        *armatures: Armature objects to merge
        name: Optional name for the merged armature

    Returns:
        The merged armature
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("merge_rigs requires Blender (bpy module)")

    if not armatures:
        raise ValueError("No armatures provided")

    # Create new armature
    merged_name = name or f"merged_{armatures[0].name}"
    merged_data = bpy.data.armatures.new(merged_name)
    merged = bpy.data.objects.new(merged_name, merged_data)
    bpy.context.collection.objects.link(merged)

    # Enter edit mode
    bpy.context.view_layer.objects.active = merged
    bpy.ops.object.mode_set(mode='EDIT')

    # Copy bones from each armature
    for armature in armatures:
        prefix = armature.name + "_"  # Prefix to avoid name conflicts

        for bone in armature.data.bones:
            new_bone = merged.data.edit_bones.new(prefix + bone.name)
            new_bone.head = bone.head_local
            new_bone.tail = bone.tail_local
            new_bone.roll = bone.roll
            new_bone.layers = bone.layers
            new_bone.use_deform = bone.use_deform

    bpy.ops.object.mode_set(mode='OBJECT')

    return merged
