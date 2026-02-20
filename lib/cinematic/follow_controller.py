"""
Follow Camera Controller

Main controller for follow camera rig creation, updates, and baking.
Provides high-level API for managing follow camera systems.

Part of Phase 6.3 - Follow Camera System
Requirements: REQ-FOLLOW-01 through REQ-FOLLOW-05
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path

from .follow_types import (
    FollowConfig,
    FollowState,
    FollowRig,
    FollowResult,
)
from .follow_modes import (
    calculate_follow,
    calculate_look_at_rotation,
    smooth_position,
)
from .follow_deadzone import (
    calculate_dead_zone_result,
    is_in_dead_zone,
)

# Blender API guard for testing outside Blender
try:
    import bpy
    from bpy import types as bpy_types
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    bpy = None


def create_follow_rig(
    camera_name: str,
    target_name: str,
    config: Optional[FollowConfig] = None,
    rig_name: Optional[str] = None,
) -> FollowRig:
    """
    Create a follow rig for camera.

    Sets up a follow camera configuration for the specified camera
    and target object.

    Args:
        camera_name: Name of camera object in Blender
        target_name: Name of target object to follow
        config: Follow configuration (uses defaults if None)
        rig_name: Optional rig name (auto-generated if None)

    Returns:
        FollowRig instance
    """
    if config is None:
        config = FollowConfig()

    if rig_name is None:
        rig_name = f"follow_{camera_name}"

    # Create initial state
    state = FollowState()

    # Create rig
    rig = FollowRig(
        name=rig_name,
        camera=camera_name,
        target=target_name,
        config=config,
        state=state,
    )

    return rig


def update_follow_rig(
    rig: FollowRig,
    frame: int,
    target_position: Optional[Tuple[float, float, float]] = None,
    target_velocity: Optional[Tuple[float, float, float]] = None,
    delta_time: float = 1/24,
    apply_to_blender: bool = True,
) -> FollowResult:
    """
    Update camera position for frame.

    Calculates new camera position based on follow mode and updates
    the rig state. Optionally applies to Blender camera object.

    Args:
        rig: FollowRig to update
        frame: Current frame number
        target_position: Target world position (None to use from Blender)
        target_velocity: Target velocity vector (None to calculate)
        delta_time: Time since last update
        apply_to_blender: Whether to update Blender camera object

    Returns:
        FollowResult with calculated position and metadata
    """
    # Get target position
    if target_position is None and HAS_BLENDER:
        target_obj = bpy.data.objects.get(rig.target)
        if target_obj:
            target_position = tuple(target_obj.location)
        else:
            target_position = (0.0, 0.0, 0.0)
    elif target_position is None:
        target_position = (0.0, 0.0, 0.0)

    # Get or calculate target velocity
    if target_velocity is None:
        # Calculate from position history
        last_pos = rig.state.target_position
        last_vel = rig.state.last_target_velocity
        current_pos = target_position

        # Simple velocity calculation
        velocity = tuple(
            (c - l) / delta_time
            for c, l in zip(current_pos, last_pos)
        )

        # Smooth velocity
        if any(v != 0 for v in last_vel):
            velocity = tuple(
                0.7 * v + 0.3 * lv
                for v, lv in zip(velocity, last_vel)
            )

        target_velocity = velocity

    # Get current camera position
    if rig.state.current_position != (0.0, 0.0, 0.0):
        camera_pos = rig.state.current_position
    elif HAS_BLENDER:
        cam_obj = bpy.data.objects.get(rig.camera)
        if cam_obj:
            camera_pos = tuple(cam_obj.location)
        else:
            camera_pos = (0.0, -rig.config.keep_distance, rig.config.keep_height)
    else:
        camera_pos = (0.0, -rig.config.keep_distance, rig.config.keep_height)

    # Calculate follow result
    result = calculate_follow(
        camera_pos=camera_pos,
        target_pos=target_position,
        target_velocity=target_velocity,
        config=rig.config,
        state=rig.state,
        delta_time=delta_time,
    )

    # Update rig state
    rig.state.current_position = result.position
    rig.state.target_position = target_position
    rig.state.last_target_velocity = target_velocity
    rig.state.current_distance = result.distance
    rig.state.current_height = result.height
    rig.state.current_velocity = tuple(
        (p - c) / delta_time
        for p, c in zip(result.position, camera_pos)
    )

    # Update mode-specific state
    if rig.config.mode == "orbit":
        rig.state.orbit_angle += rig.config.orbit_speed
        if rig.state.orbit_angle >= 360:
            rig.state.orbit_angle -= 360

    # Apply to Blender if requested
    if apply_to_blender and HAS_BLENDER:
        cam_obj = bpy.data.objects.get(rig.camera)
        if cam_obj:
            cam_obj.location = result.position

            # Apply rotation
            rotation_rad = tuple(math.radians(r) for r in result.rotation)
            cam_obj.rotation_euler = rotation_rad

    return result


def bake_follow_animation(
    rig: FollowRig,
    frame_start: int,
    frame_end: int,
    target_positions: Optional[Dict[int, Tuple[float, float, float]]] = None,
    target_velocities: Optional[Dict[int, Tuple[float, float, float]]] = None,
    fps: float = 24.0,
) -> List[FollowResult]:
    """
    Bake follow animation to keyframes.

    Pre-calculates camera path and bakes keyframes for each frame
    in the specified range.

    Args:
        rig: FollowRig to bake
        frame_start: Start frame
        frame_end: End frame (inclusive)
        target_positions: Optional dict of frame -> position
        target_velocities: Optional dict of frame -> velocity
        fps: Frames per second

    Returns:
        List of FollowResult for each frame
    """
    results = []
    delta_time = 1.0 / fps

    for frame in range(frame_start, frame_end + 1):
        # Get target position for this frame
        if target_positions and frame in target_positions:
            target_pos = target_positions[frame]
        elif HAS_BLENDER:
            # Set scene frame and get object position
            bpy.context.scene.frame_set(frame)
            target_obj = bpy.data.objects.get(rig.target)
            if target_obj:
                target_pos = tuple(target_obj.location)
            else:
                target_pos = (0.0, 0.0, 0.0)
        else:
            target_pos = (0.0, 0.0, 0.0)

        # Get or calculate velocity
        if target_velocities and frame in target_velocities:
            target_vel = target_velocities[frame]
        else:
            target_vel = None

        # Update rig (without applying to Blender)
        result = update_follow_rig(
            rig,
            frame,
            target_position=target_pos,
            target_velocity=target_vel,
            delta_time=delta_time,
            apply_to_blender=False,
        )

        results.append(result)

        # Insert keyframes if in Blender
        if HAS_BLENDER:
            cam_obj = bpy.data.objects.get(rig.camera)
            if cam_obj:
                cam_obj.location = result.position
                cam_obj.keyframe_insert(data_path="location", frame=frame)

                # Rotation keyframes
                rotation_rad = tuple(math.radians(r) for r in result.rotation)
                cam_obj.rotation_euler = rotation_rad
                cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    return results


def preview_follow_motion(
    rig: FollowRig,
    frames: int,
    target_positions: Optional[List[Tuple[float, float, float]]] = None,
    fps: float = 24.0,
) -> List[FollowResult]:
    """
    Preview follow motion without baking keyframes.

    Calculates camera path for preview purposes.

    Args:
        rig: FollowRig to preview
        frames: Number of frames to preview
        target_positions: Optional list of positions (one per frame)
        fps: Frames per second

    Returns:
        List of FollowResult for each frame
    """
    results = []
    delta_time = 1.0 / fps

    # Reset state for clean preview
    rig.state = FollowState()

    for frame in range(frames):
        # Get target position
        if target_positions and frame < len(target_positions):
            target_pos = target_positions[frame]
        else:
            target_pos = (0.0, 0.0, 0.0)

        # Update rig
        result = update_follow_rig(
            rig,
            frame,
            target_position=target_pos,
            delta_time=delta_time,
            apply_to_blender=False,
        )

        results.append(result)

    return results


def load_follow_preset(preset_name: str, config_path: Optional[Path] = None) -> FollowConfig:
    """
    Load follow configuration from preset file.

    Args:
        preset_name: Name of preset to load
        config_path: Optional path to preset file

    Returns:
        FollowConfig from preset
    """
    import yaml

    if config_path is None:
        # Default path
        config_path = Path(__file__).parent.parent.parent / "configs" / "cinematic" / "follow" / "follow_presets.yaml"

    if not config_path.exists():
        # Return default config if file not found
        return FollowConfig()

    with open(config_path, 'r') as f:
        presets = yaml.safe_load(f)

    if not presets or "presets" not in presets:
        return FollowConfig()

    preset_data = presets["presets"].get(preset_name)
    if not preset_data:
        return FollowConfig()

    return FollowConfig.from_dict(preset_data)


def save_follow_state(rig: FollowRig, path: Path) -> None:
    """
    Save follow rig state to file.

    Args:
        rig: FollowRig to save
        path: Output file path
    """
    import json

    data = rig.to_dict()

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_follow_state(path: Path) -> FollowRig:
    """
    Load follow rig state from file.

    Args:
        path: Input file path

    Returns:
        FollowRig from file
    """
    import json

    with open(path, 'r') as f:
        data = json.load(f)

    return FollowRig.from_dict(data)


def reset_follow_state(rig: FollowRig) -> None:
    """
    Reset follow rig to initial state.

    Clears all runtime state while keeping configuration.

    Args:
        rig: FollowRig to reset
    """
    rig.state = FollowState()


def get_follow_rig_info(rig: FollowRig) -> Dict[str, Any]:
    """
    Get information about follow rig.

    Returns a summary of rig configuration and current state.

    Args:
        rig: FollowRig to inspect

    Returns:
        Dictionary with rig information
    """
    return {
        "name": rig.name,
        "camera": rig.camera,
        "target": rig.target,
        "mode": rig.config.mode,
        "current_position": rig.state.current_position,
        "target_position": rig.state.target_position,
        "distance": rig.state.current_distance,
        "height": rig.state.current_height,
        "in_dead_zone": rig.state.is_in_dead_zone,
        "config": rig.config.to_dict(),
    }
