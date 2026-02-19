"""
Frame Store Module - State Capture and Comparison

Captures and compares scene states for version control,
undo operations, and A/B comparisons.

Usage:
    from lib.cinematic.frame_store import capture_frame, restore_frame, compare_frames

    # Capture current state
    frame = capture_frame("hero_v1")

    # Restore to captured state
    restore_frame(frame)

    # Compare two frames
    diff = compare_frames(frame_a, frame_b)

    # Save/load to file
    save_state_to_file(frame, "state.json")
    loaded = load_state_from_file("state.json")
"""

from __future__ import annotations
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .types import FrameState, CameraConfig, Transform3D

# Blender availability check
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


def capture_frame(label: str = "") -> FrameState:
    """
    Capture current scene state (camera, lights, selected objects).

    Generates a unique frame_id with UUID and sets timestamp to current time.

    Args:
        label: Optional user-friendly label for the frame

    Returns:
        FrameState with captured data
    """
    state = FrameState(
        frame_number=1,
        camera_transform={},
        camera_settings={},
        light_states=[],
        object_transforms=[],
        render_settings={},
        color_settings={},
        timestamp=datetime.utcnow().isoformat(),
        label=label,
    )

    if not BLENDER_AVAILABLE:
        return state

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return state

        scene = bpy.context.scene

        # Capture active camera
        camera = scene.camera
        if camera:
            state.camera_transform = {
                "location": list(camera.location),
                "rotation": list(camera.rotation_euler),
                "scale": list(camera.scale),
            }
            cam_data = camera.data
            if cam_data is not None:
                state.camera_settings = {
                    "focal_length": cam_data.lens,
                    "f_stop": cam_data.dof.aperture_fstop if hasattr(cam_data.dof, 'use_dof') and cam_data.dof.use_dof else 0.0,
                    "focus_distance": getattr(cam_data.dof, 'focus_distance', 10.0) if hasattr(cam_data, 'dof') else 10.0,
                    "sensor_width": cam_data.sensor_width,
                    "sensor_height": cam_data.sensor_height,
                }

        # Capture frame number
        state.frame_number = scene.frame_current

        # Capture render settings
        render = scene.render
        state.render_settings = {
            "resolution_x": render.resolution_x,
            "resolution_y": render.resolution_y,
            "resolution_percentage": render.resolution_percentage,
            "fps": scene.render.fps,
            "engine": scene.render.engine,
        }

        # Capture color settings
        if hasattr(scene, 'view_settings'):
            state.color_settings = {
                "view_transform": scene.view_settings.view_transform,
                "exposure": scene.view_settings.exposure,
                "gamma": scene.view_settings.gamma,
            }

        # Capture lights
        for obj in scene.objects:
            if obj.type == 'LIGHT':
                light_state = {
                    "name": obj.name,
                    "location": list(obj.location),
                    "rotation": list(obj.rotation_euler),
                    "energy": obj.data.energy if hasattr(obj.data, 'energy') else 0,
                }
                state.light_states.append(light_state)

        # Capture selected objects
        for obj in bpy.context.selected_objects:
            if obj.type not in ('CAMERA', 'LIGHT'):
                obj_state = {
                    "name": obj.name,
                    "location": list(obj.location),
                    "rotation": list(obj.rotation_euler),
                    "scale": list(obj.scale),
                }
                state.object_transforms.append(obj_state)

    except Exception:
        pass

    return state


def capture_frame_state(label: str = "") -> FrameState:
    """Alias for capture_frame() for backward compatibility."""
    return capture_frame(label)


def restore_frame(frame: FrameState) -> bool:
    """
    Restore scene to captured state.

    Applies camera, light transforms and render settings.

    Args:
        frame: FrameState to restore

    Returns:
        True if successful, False if Blender unavailable or error
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        camera = scene.camera

        if camera and frame.camera_transform:
            camera.location = frame.camera_transform.get("location", (0, 0, 0))
            camera.rotation_euler = frame.camera_transform.get("rotation", (0, 0, 0))
            camera.scale = frame.camera_transform.get("scale", (1, 1, 1))

        if camera and frame.camera_settings and hasattr(camera, 'data') and camera.data is not None:
            cam_data = camera.data
            cam_data.lens = frame.camera_settings.get("focal_length", 50.0)
            if "f_stop" in frame.camera_settings and hasattr(cam_data, 'dof'):
                cam_data.dof.aperture_fstop = frame.camera_settings["f_stop"]
            if "focus_distance" in frame.camera_settings and hasattr(cam_data, 'dof'):
                cam_data.dof.focus_distance = frame.camera_settings["focus_distance"]

        # Restore render settings
        if frame.render_settings:
            render = scene.render
            render.resolution_x = frame.render_settings.get("resolution_x", 1920)
            render.resolution_y = frame.render_settings.get("resolution_y", 1080)
            render.resolution_percentage = frame.render_settings.get("resolution_percentage", 100)

        # Set frame number
        scene.frame_set(frame.frame_number)

        return True

    except Exception:
        return False


def restore_frame_state(frame: FrameState) -> bool:
    """Alias for restore_frame() for backward compatibility."""
    return restore_frame(frame)


def compare_frames(frame_a: FrameState, frame_b: FrameState) -> Dict[str, Any]:
    """
    Compare two captured frames and return differences.

    Args:
        frame_a: First frame state
        frame_b: Second frame state

    Returns:
        Dictionary of differences by category
    """
    differences = {
        "camera": {},
        "lights": [],
        "objects": [],
        "render_settings": {},
        "color_settings": {},
        "has_differences": False,
    }

    # Compare camera transforms
    if frame_a.camera_transform != frame_b.camera_transform:
        differences["camera"]["transform"] = {
            "a": frame_a.camera_transform,
            "b": frame_b.camera_transform,
        }
        differences["has_differences"] = True

    # Compare camera settings
    if frame_a.camera_settings != frame_b.camera_settings:
        differences["camera"]["settings"] = {
            "a": frame_a.camera_settings,
            "b": frame_b.camera_settings,
        }
        differences["has_differences"] = True

    # Compare render settings
    if frame_a.render_settings != frame_b.render_settings:
        differences["render_settings"] = {
            "a": frame_a.render_settings,
            "b": frame_b.render_settings,
        }
        differences["has_differences"] = True

    # Compare color settings
    if frame_a.color_settings != frame_b.color_settings:
        differences["color_settings"] = {
            "a": frame_a.color_settings,
            "b": frame_b.color_settings,
        }
        differences["has_differences"] = True

    return differences


def compare_states(frame_a: FrameState, frame_b: FrameState) -> Dict[str, Any]:
    """Alias for compare_frames() for backward compatibility."""
    return compare_frames(frame_a, frame_b)


def get_frame_history(shot_name: str, state_dir: Optional[Path] = None) -> List[FrameState]:
    """
    Load all frames for a shot from state directory.

    Args:
        shot_name: Name of the shot
        state_dir: Optional state directory (defaults to .gsd-state/cinematic/frames)

    Returns:
        List of FrameState sorted by timestamp
    """
    if state_dir is None:
        state_dir = Path(".gsd-state/cinematic/frames")

    shot_dir = state_dir / shot_name
    if not shot_dir.exists():
        return []

    frames = []
    for frame_dir in shot_dir.iterdir():
        if frame_dir.is_dir():
            state_file = frame_dir / "state.json"
            if state_file.exists():
                frame = load_state_from_file(str(state_file))
                if frame:
                    frames.append(frame)

    # Sort by timestamp
    frames.sort(key=lambda f: f.timestamp)
    return frames


def label_frame(frame_id: str, label: str, state_dir: Optional[Path] = None) -> bool:
    """
    Update frame label in storage.

    Args:
        frame_id: Frame identifier
        label: New label text
        state_dir: Optional state directory

    Returns:
        True if successful
    """
    if state_dir is None:
        state_dir = Path(".gsd-state/cinematic/frames")

    # Search for frame by ID
    for shot_dir in state_dir.iterdir():
        if shot_dir.is_dir():
            for frame_dir in shot_dir.iterdir():
                state_file = frame_dir / "state.json"
                if state_file.exists():
                    frame = load_state_from_file(str(state_file))
                    if frame and str(frame.frame_number) == frame_id:
                        frame.label = label
                        return save_state_to_file(frame, str(state_file))

    return False


def save_state_to_file(frame: FrameState, filepath: str) -> bool:
    """
    Save frame state to a JSON file.

    Args:
        frame: FrameState to save
        filepath: Path to save file

    Returns:
        True if successful
    """
    try:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(frame.to_dict(), f, indent=2)
        return True
    except Exception:
        return False


def load_state_from_file(filepath: str) -> Optional[FrameState]:
    """
    Load frame state from a JSON file.

    Args:
        filepath: Path to load file from

    Returns:
        FrameState or None if error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return FrameState.from_dict(data)
    except Exception:
        return None


def save_frame(shot_name: str, frame: FrameState, state_dir: Optional[Path] = None) -> int:
    """
    Save frame to shot directory with auto-numbering.

    Args:
        shot_name: Name of the shot
        frame: FrameState to save
        state_dir: Optional state directory

    Returns:
        Frame number assigned
    """
    if state_dir is None:
        state_dir = Path(".gsd-state/cinematic/frames")

    shot_dir = state_dir / shot_name
    shot_dir.mkdir(parents=True, exist_ok=True)

    # Find next frame number
    existing = list(shot_dir.iterdir())
    frame_numbers = [int(d.name) for d in existing if d.is_dir() and d.name.isdigit()]
    next_num = max(frame_numbers, default=0) + 1

    # Create frame directory
    frame_dir = shot_dir / f"{next_num:03d}"
    frame_dir.mkdir(parents=True, exist_ok=True)

    # Update frame number
    frame.frame_number = next_num

    # Save
    save_state_to_file(frame, str(frame_dir / "state.json"))

    return next_num


def load_frame(shot_name: str, frame_num: int, state_dir: Optional[Path] = None) -> Optional[FrameState]:
    """
    Load frame by shot name and frame number.

    Args:
        shot_name: Name of the shot
        frame_num: Frame number to load
        state_dir: Optional state directory

    Returns:
        FrameState or None if not found
    """
    if state_dir is None:
        state_dir = Path(".gsd-state/cinematic/frames")

    state_file = state_dir / shot_name / f"{frame_num:03d}" / "state.json"
    if state_file.exists():
        return load_state_from_file(str(state_file))

    return None
