"""
Pole Targets Module

Pole target management for IK constraints.

Phase 13.1: IK/FK System (REQ-ANIM-02)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import math

from .types import PoleTargetConfig

if TYPE_CHECKING:
    import bpy


class PoleTargetManager:
    """
    Manages IK pole targets.

    Pole targets control the direction of joints (elbows, knees)
    in IK chains.
    """

    def __init__(self, armature: Any = None):
        """
        Initialize pole target manager.

        Args:
            armature: Blender armature object (optional)
        """
        self.armature = armature
        self._pole_configs: Dict[str, PoleTargetConfig] = {}
        self._pole_objects: Dict[str, Any] = {}

    def create_pole_target(
        self,
        armature: Any,
        config: PoleTargetConfig
    ) -> Any:
        """
        Create a pole target object for IK.

        Args:
            armature: Blender armature object
            config: Pole target configuration

        Returns:
            Created pole target object
        """
        import bpy

        self.armature = armature

        # Get chain bones for positioning
        bone = armature.pose.bones.get(config.bone_name)
        if bone is None:
            raise ValueError(f"Bone '{config.bone_name}' not found")

        # Calculate pole position
        if config.auto_position:
            position = self.calculate_pole_position(armature, [config.bone_name])
            position = (
                position[0] + config.pole_offset[0],
                position[1] + config.pole_offset[1],
                position[2] + config.pole_offset[2],
            )
        else:
            position = config.pole_offset

        # Create pole target object
        pole_name = config.pole_object or f"pole_{config.bone_name}"

        # Create empty object
        pole_obj = bpy.data.objects.new(pole_name, None)
        pole_obj.empty_display_type = 'SPHERE'
        pole_obj.empty_display_size = 0.1
        pole_obj.location = position

        # Link to scene
        bpy.context.collection.objects.link(pole_obj)

        # Store reference
        self._pole_objects[pole_name] = pole_obj
        self._pole_configs[config.bone_name] = config

        return pole_obj

    def calculate_pole_position(
        self,
        armature: Any,
        chain: List[str],
        distance: float = 0.5,
        direction: str = 'back'
    ) -> Tuple[float, float, float]:
        """
        Calculate optimal pole target position.

        Args:
            armature: Blender armature object
            chain: Bone chain (usually 2 bones)
            distance: Distance from joint
            direction: 'back', 'front', 'left', 'right'

        Returns:
            World position for pole target
        """
        if len(chain) < 2:
            # Single bone - use bone direction
            bone = armature.pose.bones.get(chain[0])
            if bone is None:
                return (0, 0, 0)

            world_matrix = armature.matrix_world @ bone.matrix
            return tuple(world_matrix.translation)

        # Get the first bone in chain (upper arm, thigh)
        root_bone = armature.pose.bones.get(chain[0])
        if root_bone is None:
            return (0, 0, 0)

        # Get world matrix
        world_matrix = armature.matrix_world @ root_bone.matrix
        bone_pos = world_matrix.translation

        # Get bone direction (Y axis in bone space)
        bone_dir = world_matrix.to_3x3() @ mathutils.Vector((0, 1, 0))

        # Calculate perpendicular direction for pole
        # Default is behind the joint
        if direction == 'back':
            perpendicular = bone_dir.cross(mathutils.Vector((0, 0, 1)))
            if perpendicular.length < 0.01:
                perpendicular = bone_dir.cross(mathutils.Vector((1, 0, 0)))
        elif direction == 'front':
            perpendicular = bone_dir.cross(mathutils.Vector((0, 0, -1)))
            if perpendicular.length < 0.01:
                perpendicular = bone_dir.cross(mathutils.Vector((-1, 0, 0)))
        elif direction == 'left':
            perpendicular = world_matrix.to_3x3() @ mathutils.Vector((-1, 0, 0))
        elif direction == 'right':
            perpendicular = world_matrix.to_3x3() @ mathutils.Vector((1, 0, 0))
        else:
            perpendicular = bone_dir.cross(mathutils.Vector((0, 0, 1)))

        # Normalize and scale
        if perpendicular.length > 0.01:
            perpendicular = perpendicular.normalized() * distance
        else:
            perpendicular = mathutils.Vector((distance, 0, 0))

        # Calculate final position
        pole_pos = bone_pos + perpendicular

        return tuple(pole_pos)

    def position_pole_target(
        self,
        armature: Any,
        pole_obj: Any,
        chain: List[str],
        angle: float = 0.0
    ) -> None:
        """
        Position an existing pole target object.

        Args:
            armature: Blender armature object
            pole_obj: Pole target object
            chain: Bone chain
            angle: Rotation angle in radians
        """
        position = self.calculate_pole_position(armature, chain)

        # Apply angle rotation around chain axis
        if angle != 0.0 and len(chain) >= 1:
            bone = armature.pose.bones.get(chain[0])
            if bone:
                world_matrix = armature.matrix_world @ bone.matrix
                bone_pos = world_matrix.translation

                # Rotate position around bone axis
                import mathutils
                axis = world_matrix.to_3x3() @ mathutils.Vector((0, 1, 0))
                rot_matrix = mathutils.Matrix.Rotation(angle, 4, axis)

                offset = mathutils.Vector(position) - bone_pos
                rotated_offset = rot_matrix @ offset
                position = tuple(bone_pos + rotated_offset)

        pole_obj.location = position

    def get_pole_angle(
        self,
        armature: Any,
        bone_name: str
    ) -> float:
        """
        Get current pole angle for a bone's IK constraint.

        Args:
            armature: Blender armature object
            bone_name: Name of bone with IK constraint

        Returns:
            Pole angle in radians
        """
        bone = armature.pose.bones.get(bone_name)
        if bone is None:
            return 0.0

        for constraint in bone.constraints:
            if constraint.type == 'IK' and constraint.pole_target:
                return constraint.pole_angle

        return 0.0

    def set_pole_angle(
        self,
        armature: Any,
        bone_name: str,
        angle: float
    ) -> None:
        """
        Set pole angle for a bone's IK constraint.

        Args:
            armature: Blender armature object
            bone_name: Name of bone with IK constraint
            angle: Pole angle in radians
        """
        bone = armature.pose.bones.get(bone_name)
        if bone is None:
            return

        for constraint in bone.constraints:
            if constraint.type == 'IK' and constraint.pole_target:
                constraint.pole_angle = angle

    def animate_pole_angle(
        self,
        armature: Any,
        bone_name: str,
        start_angle: float,
        end_angle: float,
        start_frame: int,
        end_frame: int
    ) -> None:
        """
        Animate pole angle over time.

        Args:
            armature: Blender armature object
            bone_name: Name of bone with IK constraint
            start_angle: Starting angle in radians
            end_angle: Ending angle in radians
            start_frame: Start frame
            end_frame: End frame
        """
        import bpy

        bone = armature.pose.bones.get(bone_name)
        if bone is None:
            return

        for constraint in bone.constraints:
            if constraint.type == 'IK' and constraint.pole_target:
                # Set start angle and keyframe
                constraint.pole_angle = start_angle
                constraint.keyframe_insert(
                    data_path="pole_angle",
                    frame=start_frame
                )

                # Set end angle and keyframe
                constraint.pole_angle = end_angle
                constraint.keyframe_insert(
                    data_path="pole_angle",
                    frame=end_frame
                )

    def get_config(self, bone_name: str) -> Optional[PoleTargetConfig]:
        """Get stored pole configuration for a bone."""
        return self._pole_configs.get(bone_name)

    def get_pole_object(self, name: str) -> Optional[Any]:
        """Get pole target object by name."""
        return self._pole_objects.get(name)

    def list_poles(self) -> List[str]:
        """List all pole target object names."""
        return list(self._pole_objects.keys())


def create_elbow_pole(
    armature: Any,
    upper_arm: str,
    lower_arm: str,
    side: str = "L",
    distance: float = 0.5
) -> Any:
    """
    Convenience function to create elbow pole target.

    Args:
        armature: Blender armature object
        upper_arm: Upper arm bone name
        lower_arm: Lower arm bone name
        side: "L" or "R"
        distance: Distance from elbow

    Returns:
        Created pole target object
    """
    config = PoleTargetConfig(
        bone_name=lower_arm,
        pole_object=f"pole_elbow_{side}",
        pole_offset=(0, -distance if side == "L" else distance, 0),
        auto_position=True,
    )

    manager = PoleTargetManager()
    return manager.create_pole_target(armature, config)


def create_knee_pole(
    armature: Any,
    thigh: str,
    shin: str,
    side: str = "L",
    distance: float = 0.5
) -> Any:
    """
    Convenience function to create knee pole target.

    Args:
        armature: Blender armature object
        thigh: Thigh bone name
        shin: Shin bone name
        side: "L" or "R"
        distance: Distance from knee

    Returns:
        Created pole target object
    """
    config = PoleTargetConfig(
        bone_name=shin,
        pole_object=f"pole_knee_{side}",
        pole_offset=(0, distance if side == "L" else -distance, 0),
        auto_position=True,
    )

    manager = PoleTargetManager()
    return manager.create_pole_target(armature, config)


def auto_position_poles(armature: Any) -> None:
    """
    Auto-position all pole targets in an armature.

    Finds all IK constraints with pole targets and
    positions them optimally.

    Args:
        armature: Blender armature object
    """
    manager = PoleTargetManager(armature)

    for bone in armature.pose.bones:
        for constraint in bone.constraints:
            if constraint.type == 'IK' and constraint.pole_target:
                # Get chain
                chain = [bone.name]
                current = bone

                for _ in range(constraint.chain_count - 1):
                    parent = current.parent
                    if parent is None:
                        break
                    chain.insert(0, parent.name)
                    current = parent

                # Position the pole target
                if constraint.pole_target:
                    pole = constraint.pole_target
                    manager.position_pole_target(
                        armature,
                        pole,
                        chain,
                        constraint.pole_angle
                    )


# Handle import for mathutils
try:
    import bpy
    from mathutils import Vector, Matrix
    mathutils = type('mathutils', (), {'Vector': Vector, 'Matrix': Matrix})()
except ImportError:
    # Create stub for testing without Blender
    class _StubVector:
        def __init__(self, vals):
            self._vals = list(vals)
        def __iter__(self):
            return iter(self._vals)
        def cross(self, other):
            return _StubVector([0, 0, 0])
        def normalized(self):
            return self
        def __mul__(self, scalar):
            return _StubVector([v * scalar for v in self._vals])
        def __add__(self, other):
            return _StubVector([a + b for a, b in zip(self, other)])

    class _StubMatrix:
        @staticmethod
        def Rotation(angle, size, axis):
            return _StubMatrix()
        def __matmul__(self, other):
            return other

    mathutils = type('mathutils', (), {
        'Vector': _StubVector,
        'Matrix': _StubMatrix
    })()


# Convenience exports
__all__ = [
    'PoleTargetManager',
    'PoleTargetConfig',
    'create_elbow_pole',
    'create_knee_pole',
    'auto_position_poles',
]
