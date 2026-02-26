"""
Tentacle Spline IK Rig

Spline IK rigging for bone-based tentacle animation.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import math

try:
    import bpy
    from bpy.types import Object, Armature, Curve
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None
    Armature = None
    Curve = None

from .types import (
    SplineIKRig,
    RigConfig,
    RigResult,
    ShapeKeyConfig,
    ShapeKeyPreset,
)


class SplineIKRigGenerator:
    """Generator for spline IK rigs for tentacle animation."""

    def __init__(self, config: RigConfig):
        """Initialize the rig generator.

        Args:
            config: Full rig configuration
        """
        self.config = config

    def generate(self, tentacle_mesh: Optional["Object"] = None) -> RigResult:
        """
        Generate spline IK rig for a tentacle mesh.

        Args:
            tentacle_mesh: The tentacle mesh to rig (Blender Object)

        Returns:
            RigResult with generated rig data
        """
        result = RigResult(
            armature_name=f"{self.config.ik_rig.bone_prefix}_Armature",
            curve_name=self.config.ik_rig.curve_name,
            curve_object=None,
            bone_names=[],
            mesh_object=tentacle_mesh,
            shape_keys=[],
            success=False,
            error=None
        )

        if not BLENDER_AVAILABLE:
            result.error = "Blender not available"
            return result

        if tentacle_mesh is None:
            result.error = "tentacle_mesh required"
            return result

        try:
            # Get mesh data
            mesh = tentacle_mesh.data
            if mesh is None:
                result.error = "Mesh has no data"
                return result

            # Calculate tentacle length from bounding box
            bbox = tentacle_mesh.bound_box
            # bbox is a list of 8 corner points
            min_z = min(p[2] for p in bbox)
            max_z = max(p[2] for p in bbox)
            tentacle_length = max_z - min_z

            # Create armature
            armature_data = bpy.data.armatures.new(
                f"{self.config.ik_rig.bone_prefix}_Armature"
            )
            armature_obj = bpy.data.objects.new(
                f"{self.config.ik_rig.bone_prefix}_Armature",
                object_data=armature_data,
            )

            # Link to scene
            bpy.context.collection.objects.link(armature_obj)

            # Switch to edit mode to add bones
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='EDIT')

            # Generate bone chain
            bone_count = self.config.ik_rig.bone_count
            bone_names = []
            bone_length = tentacle_length / bone_count

            prev_bone = None
            for i in range(bone_count):
                bone_name = f"{self.config.ik_rig.bone_prefix}_{i:02d}"
                bone = armature_data.edit_bones.new(bone_name)
                bone.head = (0, 0, bone_length * i)
                bone.tail = (0, 0, bone_length * (i + 1))
                bone_names.append(bone_name)

                # Parent bones (except first)
                if prev_bone is not None:
                    bone.parent = prev_bone
                prev_bone = bone

            result.bone_names = bone_names

            # Switch back to object mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Create control curve
            curve_data = bpy.data.curves.new(self.config.ik_rig.curve_name, type='CURVE')
            curve_data.dimensions = '3D'
            curve_data.bevel_depth = 0.01

            # Create spline with points
            spline = curve_data.splines.new(type='BEZIER')
            spline.bezier_points.add(self.config.control_curve_points - 1)

            for i, point in enumerate(spline.bezier_points):
                t = i / (self.config.control_curve_points - 1)
                x = 0
                y = 0
                z = t * tentacle_length
                point.co = (x, y, z)
                point.handle_left = (x - 0.05, y, z)
                point.handle_right = (x + 0.05, y, z)
                point.handle_left_type = 'AUTO'
                point.handle_right_type = 'AUTO'

            curve_obj = bpy.data.objects.new(
                self.config.ik_rig.curve_name,
                object_data=curve_data,
            )
            bpy.context.collection.objects.link(curve_obj)

            result.curve_object = curve_obj

            # Add spline IK constraint to the last bone in the chain
            # First, make armature active and switch to pose mode
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='POSE')

            # Get the last bone (pose bone)
            last_bone_name = bone_names[-1]
            pose_bone = armature_obj.pose.bones[last_bone_name]

            # Add Spline IK constraint
            spline_ik = pose_bone.constraints.new(type='SPLINE_IK')
            spline_ik.target = curve_obj
            spline_ik.chain_count = bone_count

            # Switch back to object mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Link armature to mesh via modifier
            modifier = tentacle_mesh.modifiers.new(
                name=f"{self.config.ik_rig.bone_prefix}_ArmatureMod",
                type='ARMATURE',
            )
            modifier.object = armature_obj

            # Auto-weight painting (simplified - in real impl would use with_envelope_weights)
            if self.config.skin_weights == "automatic":
                # Create vertex groups for each bone
                for bone_name in bone_names:
                    if bone_name not in tentacle_mesh.vertex_groups:
                        tentacle_mesh.vertex_groups.new(name=bone_name)

                # Use automatic weights (requires armature to be parent)
                # This is simplified - real impl would use bpy.ops.object.parent_set
                pass

            # Generate shape keys (if requested)
            shape_key_names = []
            if self.config.shape_keys:
                # Ensure mesh has a basis shape key
                if not tentacle_mesh.data.shape_keys:
                    tentacle_mesh.shape_key_add(name='Basis')

                for shape_key_config in self.config.shape_keys:
                    # Create shape key
                    sk = tentacle_mesh.shape_key_add(name=shape_key_config.get_shape_key_name())
                    shape_key_names.append(sk.name)

                    # Note: Actual vertex displacement would be computed by ShapeKeyGenerator
                    # This is just creating the placeholder shape keys

            result.shape_keys = shape_key_names
            result.success = True

        except Exception as e:
            result.error = str(e)

        return result


def generate_spline_ik_rig(
    tentacle_mesh: "Object",
    bone_count: int = 15,
    bone_prefix: str = "Tentacle",
    curve_points: int = 6,
    shape_key_configs: Optional[List[Dict]] = None,
) -> RigResult:
    """
    Convenience function to generate spline IK rig for a tentacle mesh.

    Args:
        tentacle_mesh: The tentacle mesh object
        bone_count: Number of bones in the chain
        bone_prefix: Prefix for bone names
        curve_points: Number of control points on the curve
        shape_key_configs: Optional list of shape key configurations

    Returns:
        RigResult with generated rig data
    """
    # Build shape key configs if not provided
    if shape_key_configs is None:
        shape_key_configs = [
            {"name": "Compress50", "preset": ShapeKeyPreset.COMPRESS_50},
            {"name": "Compress75", "preset": ShapeKeyPreset.COMPRESS_75},
            {"name": "Expand125", "preset": ShapeKeyPreset.EXPAND_125},
            {"name": "CurlTip", "preset": ShapeKeyPreset.CURL_TIP},
        ]

    # Convert dict configs to ShapeKeyConfig objects
    shape_keys = []
    for sk in shape_key_configs:
        shape_keys.append(ShapeKeyConfig(
            name=sk["name"],
            preset=sk["preset"],
        ))

    config = RigConfig(
        ik_rig=SplineIKRig(
            bone_count=bone_count,
            bone_prefix=bone_prefix,
            curve_name=f"{bone_prefix}_Curve",
            chain_length=1.0,  # Will be calculated from mesh
        ),
        shape_keys=shape_keys,
        control_curve_points=curve_points,
    )

    generator = SplineIKRigGenerator(config)
    return generator.generate(tentacle_mesh)
