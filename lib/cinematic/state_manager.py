"""
State Persistence for Cinematic System

Provides StateManager for YAML save/load and FrameStore for
versioned frame management with cleanup.

Follows pattern from lib/gsd_io.py for YAML/JSON handling.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import yaml
except ImportError:
    yaml = None

from .types import ShotState, CameraConfig, Transform3D


class StateManager:
    """
    Manager for cinematic state persistence.

    Handles saving and loading ShotState to/from YAML files.
    Provides capture/restore for Blender camera state.

    Usage:
        manager = StateManager()

        # Save state
        state = ShotState(shot_name="hero_01")
        manager.save(state, Path("shots/hero_01.yaml"))

        # Load state
        loaded = manager.load(Path("shots/hero_01.yaml"))

        # Capture current Blender state
        current = manager.capture_current("hero_01")

        # Restore Blender to captured state
        manager.restore(current)
    """

    def __init__(self, state_root: Optional[Path] = None):
        """
        Initialize StateManager.

        Args:
            state_root: Root directory for state files.
                       Defaults to .gsd-state/cinematic
        """
        if state_root is None:
            state_root = Path(".gsd-state/cinematic")
        self.state_root = Path(state_root)

    def save(self, state: ShotState, path: Path) -> None:
        """
        Save state to YAML file.

        Sets timestamp before saving. Creates parent directories
        if needed. Falls back to JSON if PyYAML not available.

        Args:
            state: ShotState to save
            path: Output file path
        """
        # Set timestamp
        state.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Ensure parent directory exists
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        data = state.to_yaml_dict()

        # Write YAML or JSON
        if yaml:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def load(self, path: Path) -> ShotState:
        """
        Load state from YAML file.

        Args:
            path: Input file path

        Returns:
            ShotState loaded from file

        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If YAML file but PyYAML not available
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data_raw = f.read()

        if path.suffix.lower() in [".yaml", ".yml"]:
            if not yaml:
                raise RuntimeError(
                    "PyYAML not available. Use JSON or install PyYAML."
                )
            data = yaml.safe_load(data_raw)
        else:
            import json
            data = json.loads(data_raw)

        return ShotState.from_yaml_dict(data)

    def capture_current(self, shot_name: str) -> ShotState:
        """
        Capture current Blender camera state.

        Creates a ShotState from the current scene's active camera.
        Guards all bpy access to avoid errors when run outside Blender.

        Args:
            shot_name: Name for the captured shot

        Returns:
            ShotState with captured camera configuration
        """
        state = ShotState(shot_name=shot_name)

        try:
            import bpy

            # Check scene exists
            if not hasattr(bpy, "context") or bpy.context.scene is None:
                return state

            scene = bpy.context.scene

            # Get active camera
            if scene.camera is None:
                return state

            cam_obj = scene.camera

            # Extract camera data
            camera = CameraConfig(
                name=cam_obj.name,
                transform=Transform3D(
                    position=tuple(cam_obj.location),
                    rotation=tuple(cam_obj.rotation_euler),
                    scale=tuple(cam_obj.scale),
                ),
            )

            # Get camera settings if camera data exists
            if hasattr(cam_obj, "data") and cam_obj.data is not None:
                cam_data = cam_obj.data
                camera.focal_length = cam_data.lens
                camera.sensor_width = cam_data.sensor_width
                camera.sensor_height = cam_data.sensor_height

                # Focus distance (if available)
                if hasattr(cam_data, "dof") and cam_data.dof is not None:
                    if cam_data.dof.use_dof:
                        camera.focus_distance = cam_data.dof.focus_distance

                # F-stop from aperture (approximate)
                if hasattr(cam_data, "gpu_dof"):
                    camera.f_stop = getattr(cam_data.gpu_dof, "f_stop", 4.0)

            state.camera = camera

        except ImportError:
            # bpy not available, return default state
            pass
        except Exception:
            # Any Blender access error, return state with defaults
            pass

        return state

    def restore(self, state: ShotState) -> None:
        """
        Restore Blender to captured state.

        Finds or creates camera object, applies settings and transform,
        and sets as scene camera.

        Args:
            state: ShotState to restore
        """
        try:
            import bpy

            # Check scene exists
            if not hasattr(bpy, "context") or bpy.context.scene is None:
                return

            scene = bpy.context.scene

            # Find or create camera object
            cam_name = state.camera.name
            if cam_name in bpy.data.objects:
                cam_obj = bpy.data.objects[cam_name]
            else:
                # Create new camera data
                cam_data = bpy.data.cameras.new(name=cam_name)
                cam_obj = bpy.data.objects.new(cam_name, cam_data)
                scene.collection.objects.link(cam_obj)

            # Apply transform
            cam_obj.location = state.camera.transform.position
            cam_obj.rotation_euler = state.camera.transform.rotation
            cam_obj.scale = state.camera.transform.scale

            # Apply camera settings
            if hasattr(cam_obj, "data") and cam_obj.data is not None:
                cam_data = cam_obj.data
                cam_data.lens = state.camera.focal_length
                cam_data.sensor_width = state.camera.sensor_width
                cam_data.sensor_height = state.camera.sensor_height

            # Set as active camera
            scene.camera = cam_obj

        except ImportError:
            # bpy not available, nothing to restore
            pass
        except Exception:
            # Any Blender access error, skip restore
            pass

    def diff(self, state_a: ShotState, state_b: ShotState) -> Dict[str, Any]:
        """
        Compare two states and return differences.

        Args:
            state_a: First state to compare
            state_b: Second state to compare

        Returns:
            Dictionary of differences
        """
        differences = {}

        # Compare camera
        if state_a.camera.focal_length != state_b.camera.focal_length:
            differences["camera.focal_length"] = {
                "a": state_a.camera.focal_length,
                "b": state_b.camera.focal_length,
            }

        if state_a.camera.f_stop != state_b.camera.f_stop:
            differences["camera.f_stop"] = {
                "a": state_a.camera.f_stop,
                "b": state_b.camera.f_stop,
            }

        if state_a.camera.transform.position != state_b.camera.transform.position:
            differences["camera.position"] = {
                "a": state_a.camera.transform.position,
                "b": state_b.camera.transform.position,
            }

        if state_a.camera.transform.rotation != state_b.camera.transform.rotation:
            differences["camera.rotation"] = {
                "a": state_a.camera.transform.rotation,
                "b": state_b.camera.transform.rotation,
            }

        return differences


class FrameStore:
    """
    Versioned frame storage with automatic cleanup.

    Manages numbered frame directories for shot versioning.
    Automatically removes old frames when max_versions is exceeded.

    Usage:
        store = FrameStore(Path(".gsd-state/cinematic/frames"), max_versions=50)

        # Save new frame
        frame_num = store.save_frame("hero_01", state)
        print(f"Saved frame {frame_num}")

        # Load frame
        state = store.load_frame("hero_01", 5)

        # List available frames
        frames = store.list_frames("hero_01")

        # Cleanup old frames
        deleted = store.cleanup_old_frames()
    """

    def __init__(self, base_path: Path, max_versions: int = 50):
        """
        Initialize FrameStore.

        Args:
            base_path: Base directory for frame storage
            max_versions: Maximum frames to keep per shot
        """
        self.base_path = Path(base_path)
        self.max_versions = max_versions

    def save_frame(self, shot_name: str, state: ShotState) -> int:
        """
        Save state as new frame, return frame number.

        Creates shot directory if needed. Finds next frame number
        (001, 002, etc.) and saves state.yaml there.

        Args:
            shot_name: Name of the shot
            state: ShotState to save

        Returns:
            Frame number that was saved
        """
        # Create shot directory
        shot_dir = self.base_path / shot_name
        shot_dir.mkdir(parents=True, exist_ok=True)

        # Find next frame number
        existing = self.list_frames(shot_name)
        if existing:
            next_num = max(existing) + 1
        else:
            next_num = 1

        # Create frame directory
        frame_dir = shot_dir / f"{next_num:03d}"
        frame_dir.mkdir(parents=True, exist_ok=True)

        # Save state
        state.version = next_num
        manager = StateManager(self.base_path)
        manager.save(state, frame_dir / "state.yaml")

        # Cleanup old frames
        self._cleanup_shot_frames(shot_dir)

        return next_num

    def load_frame(self, shot_name: str, frame_num: int) -> ShotState:
        """
        Load frame by number.

        Args:
            shot_name: Name of the shot
            frame_num: Frame number to load

        Returns:
            ShotState loaded from frame

        Raises:
            FileNotFoundError: If frame doesn't exist
        """
        frame_path = self.base_path / shot_name / f"{frame_num:03d}" / "state.yaml"

        if not frame_path.exists():
            raise FileNotFoundError(f"Frame not found: {frame_path}")

        manager = StateManager(self.base_path)
        return manager.load(frame_path)

    def list_frames(self, shot_name: str) -> List[int]:
        """
        List available frame numbers for a shot.

        Args:
            shot_name: Name of the shot

        Returns:
            Sorted list of frame numbers
        """
        shot_dir = self.base_path / shot_name

        if not shot_dir.exists():
            return []

        frames = []
        for item in shot_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                # Check for state.yaml inside
                if (item / "state.yaml").exists():
                    frames.append(int(item.name))

        return sorted(frames)

    def cleanup_old_frames(self) -> int:
        """
        Cleanup old frames across all shots.

        Iterates all shot directories and removes excess frames.

        Returns:
            Total frames deleted across all shots
        """
        if not self.base_path.exists():
            return 0

        total_deleted = 0
        for shot_dir in self.base_path.iterdir():
            if shot_dir.is_dir():
                total_deleted += self._cleanup_shot_frames(shot_dir)

        return total_deleted

    def _cleanup_shot_frames(self, shot_dir: Path) -> int:
        """
        Cleanup a single shot's frames to max_versions.

        Args:
            shot_dir: Path to shot directory

        Returns:
            Number of frames deleted
        """
        # Get all frame numbers
        frames = []
        for item in shot_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                frames.append((int(item.name), item))

        if len(frames) <= self.max_versions:
            return 0

        # Sort by frame number (oldest first)
        frames.sort(key=lambda x: x[0])

        # Calculate how many to delete
        to_delete = len(frames) - self.max_versions

        # Delete oldest frames
        import shutil
        deleted = 0
        for i in range(to_delete):
            frame_num, frame_path = frames[i]
            try:
                shutil.rmtree(frame_path)
                deleted += 1
            except Exception:
                pass  # Ignore deletion errors

        return deleted
