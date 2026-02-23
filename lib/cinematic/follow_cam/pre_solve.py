"""
Follow Camera Pre-Solve Workflow

Pre-compute complex camera moves for deterministic renders:
- Scene analysis stage
- Ideal path computation
- Avoidance adjustment
- Path smoothing
- Keyframe baking
- One-shot mode/framing changes
- Preview video generation

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-60
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .types import (
    FollowMode,
    FollowCameraConfig,
    CameraState,
    FollowTarget,
    ObstacleInfo,
    TransitionType,
)

# Blender API guard
try:
    import bpy
    import mathutils
    from mathutils import Vector
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    from .follow_modes import Vector


class PreSolveStage(Enum):
    """Stages in pre-solve workflow."""
    SCENE_ANALYSIS = "scene_analysis"
    IDEAL_PATH = "ideal_path"
    AVOIDANCE = "avoidance"
    SMOOTHING = "smoothing"
    BAKING = "baking"
    COMPLETE = "complete"


@dataclass
class ModeChange:
    """
    A mode change event in one-shot configuration.

    Attributes:
        frame: Frame number for the change
        mode: New follow mode
        transition_type: How to transition to new mode
        transition_duration: Duration of transition in frames
    """
    frame: int
    mode: FollowMode
    transition_type: TransitionType = TransitionType.BLEND
    transition_duration: int = 12  # frames (0.5s at 24fps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "mode": self.mode.value,
            "transition_type": self.transition_type.value,
            "transition_duration": self.transition_duration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModeChange":
        return cls(
            frame=data["frame"],
            mode=FollowMode(data["mode"]),
            transition_type=TransitionType(data.get("transition_type", "blend")),
            transition_duration=data.get("transition_duration", 12),
        )


@dataclass
class FramingChange:
    """
    A framing change event in one-shot configuration.

    Attributes:
        frame: Frame number for the change
        distance: New distance from subject
        height: New height offset
        yaw_offset: Additional yaw offset (degrees)
        pitch_offset: Additional pitch offset (degrees)
        blend_duration: Duration to blend to new framing (frames)
    """
    frame: int
    distance: Optional[float] = None
    height: Optional[float] = None
    yaw_offset: float = 0.0
    pitch_offset: float = 0.0
    blend_duration: int = 12  # frames

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "distance": self.distance,
            "height": self.height,
            "yaw_offset": self.yaw_offset,
            "pitch_offset": self.pitch_offset,
            "blend_duration": self.blend_duration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FramingChange":
        return cls(
            frame=data["frame"],
            distance=data.get("distance"),
            height=data.get("height"),
            yaw_offset=data.get("yaw_offset", 0.0),
            pitch_offset=data.get("pitch_offset", 0.0),
            blend_duration=data.get("blend_duration", 12),
        )


@dataclass
class OneShotConfig:
    """
    Configuration for one-shot rendering with mode/framing changes.

    Allows defining complex camera behavior with precise timing
    for deterministic single-pass renders.

    Attributes:
        mode_changes: List of mode change events
        framing_changes: List of framing change events
        preview_enabled: Generate preview video
        preview_quality: Quality preset for preview
        preview_output_path: Path for preview video

    Example:
        config = OneShotConfig(
            mode_changes=[
                ModeChange(frame=1, mode=FollowMode.OVER_SHOULDER),
                ModeChange(frame=100, mode=FollowMode.CHASE,
                          transition_type=TransitionType.ORBIT),
            ],
            framing_changes=[
                FramingChange(frame=50, distance=5.0, height=2.0),
            ],
        )
    """
    mode_changes: List[ModeChange] = field(default_factory=list)
    framing_changes: List[FramingChange] = field(default_factory=list)
    preview_enabled: bool = False
    preview_quality: str = "draft"  # draft, preview, final
    preview_output_path: str = "//previews/follow_cam_preview.mp4"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_changes": [mc.to_dict() for mc in self.mode_changes],
            "framing_changes": [fc.to_dict() for fc in self.framing_changes],
            "preview_enabled": self.preview_enabled,
            "preview_quality": self.preview_quality,
            "preview_output_path": self.preview_output_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OneShotConfig":
        return cls(
            mode_changes=[ModeChange.from_dict(mc) for mc in data.get("mode_changes", [])],
            framing_changes=[FramingChange.from_dict(fc) for fc in data.get("framing_changes", [])],
            preview_enabled=data.get("preview_enabled", False),
            preview_quality=data.get("preview_quality", "draft"),
            preview_output_path=data.get("preview_output_path", "//previews/follow_cam_preview.mp4"),
        )

    def get_mode_at_frame(self, frame: int) -> Tuple[FollowMode, Optional[ModeChange]]:
        """
        Get the active mode at a given frame.

        Returns:
            Tuple of (current_mode, active_change if transitioning)
        """
        active_mode = None
        active_change = None

        for change in sorted(self.mode_changes, key=lambda c: c.frame):
            if change.frame <= frame:
                active_mode = change.mode
                if frame < change.frame + change.transition_duration:
                    active_change = change

        return active_mode, active_change

    def get_framing_at_frame(self, frame: int) -> Dict[str, Any]:
        """
        Get framing parameters at a given frame.

        Returns:
            Dictionary with distance, height, yaw_offset, pitch_offset
        """
        result = {
            "distance": None,
            "height": None,
            "yaw_offset": 0.0,
            "pitch_offset": 0.0,
        }

        for change in sorted(self.framing_changes, key=lambda c: c.frame):
            if change.frame <= frame:
                if change.distance is not None:
                    result["distance"] = change.distance
                if change.height is not None:
                    result["height"] = change.height
                result["yaw_offset"] = change.yaw_offset
                result["pitch_offset"] = change.pitch_offset

        return result


@dataclass
class PreSolveResult:
    """
    Result of pre-solve computation.

    Attributes:
        success: Whether pre-solve completed successfully
        stage: Current/last stage completed
        frames_processed: Number of frames processed
        path_points: Computed camera path points
        rotation_points: Computed camera rotations (yaw, pitch, roll)
        mode_at_frame: Mode active at each frame
        errors: List of error messages
        warnings: List of warning messages
        preview_path: Path to preview video if generated
    """
    success: bool = False
    stage: PreSolveStage = PreSolveStage.SCENE_ANALYSIS
    frames_processed: int = 0
    path_points: List[Tuple[float, float, float]] = field(default_factory=list)
    rotation_points: List[Tuple[float, float, float]] = field(default_factory=list)
    mode_at_frame: List[str] = field(default_factory=list)  # FollowMode value at each frame
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    preview_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stage": self.stage.value,
            "frames_processed": self.frames_processed,
            "path_points": self.path_points,
            "rotation_points": self.rotation_points,
            "mode_at_frame": self.mode_at_frame,
            "errors": self.errors,
            "warnings": self.warnings,
            "preview_path": self.preview_path,
        }


class PreSolver:
    """
    Pre-computes camera paths for deterministic rendering.

    Analyzes scene and computes camera path before rendering
    to ensure consistent results.

    Supports one-shot configuration with mode and framing changes
    at specific frames.

    Usage:
        # Basic usage
        presolver = PreSolver(config, target)
        result = presolver.solve(frame_start=1, frame_end=250)

        if result.success:
            presolver.apply_to_camera(camera_name)

        # With one-shot configuration
        one_shot = OneShotConfig(
            mode_changes=[
                ModeChange(frame=1, mode=FollowMode.OVER_SHOULDER),
                ModeChange(frame=100, mode=FollowMode.CHASE),
            ],
        )
        presolver = PreSolver(config, target, one_shot=one_shot)
        result = presolver.solve(frame_start=1, frame_end=250)
    """

    def __init__(
        self,
        config: FollowCameraConfig,
        target: FollowTarget,
        one_shot: Optional[OneShotConfig] = None,
    ):
        """
        Initialize pre-solver.

        Args:
            config: Camera configuration
            target: Follow target
            one_shot: Optional one-shot configuration for mode/framing changes
        """
        self.config = config
        self.target = target
        self.one_shot = one_shot or OneShotConfig()
        self._result = PreSolveResult()
        self._stage_progress = 0.0
        self._target_positions: List[Tuple[float, float, float]] = []

    def solve(
        self,
        frame_start: int,
        frame_end: int,
        progress_callback: Optional[Callable[[PreSolveStage, float], None]] = None,
    ) -> PreSolveResult:
        """
        Run pre-solve workflow.

        Args:
            frame_start: Start frame
            frame_end: End frame
            progress_callback: Optional callback for progress updates

        Returns:
            PreSolveResult with computed path
        """
        total_frames = frame_end - frame_start + 1
        self._result.frames_processed = total_frames

        try:
            # Stage 1: Scene Analysis
            self._run_stage(
                PreSolveStage.SCENE_ANALYSIS,
                self._analyze_scene,
                progress_callback,
            )

            # Stage 2: Ideal Path Computation
            self._run_stage(
                PreSolveStage.IDEAL_PATH,
                lambda: self._compute_ideal_path(frame_start, frame_end),
                progress_callback,
            )

            # Stage 3: Avoidance Adjustment
            self._run_stage(
                PreSolveStage.AVOIDANCE,
                self._apply_avoidance,
                progress_callback,
            )

            # Stage 4: Path Smoothing
            self._run_stage(
                PreSolveStage.SMOOTHING,
                self._smooth_path,
                progress_callback,
            )

            # Stage 5: Baking
            self._run_stage(
                PreSolveStage.BAKING,
                lambda: self._bake_keyframes(frame_start),
                progress_callback,
            )

            self._result.success = True
            self._result.stage = PreSolveStage.COMPLETE

        except Exception as e:
            self._result.errors.append(str(e))
            self._result.success = False

        return self._result

    def _run_stage(
        self,
        stage: PreSolveStage,
        func: Callable,
        progress_callback: Optional[Callable],
    ) -> None:
        """Run a single pre-solve stage."""
        self._result.stage = stage
        self._stage_progress = 0.0

        if progress_callback:
            progress_callback(stage, 0.0)

        func()

        if progress_callback:
            progress_callback(stage, 1.0)

    def _analyze_scene(self) -> None:
        """Analyze scene for potential obstacles."""
        if not HAS_BLENDER:
            return

        # Get all potential obstacle objects
        scene = bpy.context.scene

        # Count meshes that could be obstacles
        obstacle_count = 0
        for obj in scene.objects:
            if obj.type == 'MESH':
                # Skip ignored objects
                if obj.name not in self.config.ignore_objects:
                    obstacle_count += 1

        self._stage_progress = 1.0

    def _compute_ideal_path(self, frame_start: int, frame_end: int) -> None:
        """Compute ideal camera path without collision avoidance."""
        from .follow_modes import calculate_ideal_position, get_target_forward_direction
        from .transitions import TransitionManager

        self._result.path_points.clear()
        self._result.rotation_points.clear()
        self._result.mode_at_frame.clear()
        self._target_positions.clear()

        # Initialize transition manager for mode changes
        transition_manager = TransitionManager()

        for frame in range(frame_start, frame_end + 1):
            # Get target position at this frame
            target_pos, target_vel = self._get_target_at_frame(frame)
            self._target_positions.append(target_pos)

            # Get mode at this frame (one-shot support)
            current_mode, active_change = self.one_shot.get_mode_at_frame(frame)
            if current_mode is None:
                current_mode = self.config.follow_mode

            # Track mode for result
            self._result.mode_at_frame.append(current_mode.value)

            # Get framing adjustments at this frame
            framing = self.one_shot.get_framing_at_frame(frame)

            # Create frame-specific config with mode/framing adjustments
            frame_config = self._create_frame_config(current_mode, framing)

            # Calculate ideal camera position
            target_fwd = get_target_forward_direction(Vector(target_vel))

            pos, yaw, pitch = calculate_ideal_position(
                target_position=target_pos,
                target_forward=tuple(target_fwd._values),
                target_velocity=target_vel,
                config=frame_config,
            )

            # Handle mode transitions
            if active_change:
                # Apply transition blending
                pos, yaw, pitch = self._apply_transition(
                    frame, active_change, pos, yaw, pitch
                )

            self._result.path_points.append(tuple(pos._values))
            self._result.rotation_points.append((yaw, pitch, 0.0))

        self._stage_progress = 1.0

    def _create_frame_config(
        self,
        mode: FollowMode,
        framing: Dict[str, Any],
    ) -> FollowCameraConfig:
        """Create a frame-specific configuration."""
        # Start with base config
        config_dict = self.config.to_dict()

        # Apply mode
        config_dict["follow_mode"] = mode.value

        # Apply framing adjustments
        if framing.get("distance") is not None:
            config_dict["ideal_distance"] = framing["distance"]
        if framing.get("height") is not None:
            config_dict["ideal_height"] = framing["height"]
        if framing.get("yaw_offset") != 0:
            config_dict["yaw"] = self.config.yaw + framing["yaw_offset"]
        if framing.get("pitch_offset") != 0:
            config_dict["pitch"] = self.config.pitch + framing["pitch_offset"]

        return FollowCameraConfig.from_dict(config_dict)

    def _apply_transition(
        self,
        frame: int,
        change: ModeChange,
        pos: Vector,
        yaw: float,
        pitch: float,
    ) -> Tuple[Vector, float, float]:
        """Apply transition blending for mode changes."""
        # Calculate transition progress
        progress = (frame - change.frame) / change.transition_duration
        progress = max(0.0, min(1.0, progress))

        # For now, just pass through the position
        # Full implementation would blend between old and new mode positions
        return pos, yaw, pitch

    def _apply_avoidance(self) -> None:
        """Apply collision avoidance to path."""
        from .collision import detect_obstacles, calculate_avoidance_position

        if not self._result.path_points:
            return

        adjusted_points = []

        for i, pos in enumerate(self._result.path_points):
            # Get target position at this frame
            target_pos = self._get_target_position_at_index(i)

            # Detect obstacles
            obstacles = detect_obstacles(
                camera_position=pos,
                target_position=target_pos,
                config=self.config,
            )

            if obstacles:
                # Calculate avoidance
                new_pos, _ = calculate_avoidance_position(
                    camera_position=pos,
                    target_position=target_pos,
                    obstacles=obstacles,
                    config=self.config,
                )
                adjusted_points.append(new_pos)
            else:
                adjusted_points.append(pos)

        self._result.path_points = adjusted_points
        self._stage_progress = 1.0

    def _smooth_path(self) -> None:
        """Smooth the computed path."""
        if len(self._result.path_points) < 3:
            return

        # Simple moving average smoothing
        smoothed_points = []
        window_size = 5
        half_window = window_size // 2

        points = self._result.path_points

        for i in range(len(points)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(points), i + half_window + 1)

            # Average position in window
            avg_x = sum(points[j][0] for j in range(start_idx, end_idx)) / (end_idx - start_idx)
            avg_y = sum(points[j][1] for j in range(start_idx, end_idx)) / (end_idx - start_idx)
            avg_z = sum(points[j][2] for j in range(start_idx, end_idx)) / (end_idx - start_idx)

            smoothed_points.append((avg_x, avg_y, avg_z))

        self._result.path_points = smoothed_points
        self._stage_progress = 1.0

    def _bake_keyframes(self, frame_start: int) -> None:
        """Prepare keyframes for baking."""
        # This stage just validates the path is ready
        if not self._result.path_points:
            self._result.warnings.append("No path points to bake")
        self._stage_progress = 1.0

    def apply_to_camera(self, camera_name: str) -> bool:
        """
        Apply computed path to camera as keyframes.

        Args:
            camera_name: Name of camera object

        Returns:
            True if successful
        """
        if not HAS_BLENDER:
            return False

        camera = bpy.data.objects.get(camera_name)
        if not camera or camera.type != 'CAMERA':
            return False

        # Ensure animation data exists
        if not camera.animation_data:
            camera.animation_data_create()
        if not camera.animation_data.action:
            camera.animation_data.action = bpy.data.actions.new(f"{camera_name}_FollowCam")

        action = camera.animation_data.action

        # Create f-curves if needed
        fcurves_loc = []
        fcurves_rot = []

        for i in range(3):
            fc = action.fcurves.find(f"location", index=i)
            if not fc:
                fc = action.fcurves.new(f"location", index=i)
            fcurves_loc.append(fc)

        for i in range(3):
            fc = action.fcurves.find(f"rotation_euler", index=i)
            if not fc:
                fc = action.fcurves.new(f"rotation_euler", index=i)
            fcurves_rot.append(fc)

        # Insert keyframes
        for frame_idx, (pos, rot) in enumerate(zip(
            self._result.path_points,
            self._result.rotation_points
        )):
            frame = frame_idx + 1  # 1-indexed

            # Position
            for i, fc in enumerate(fcurves_loc):
                fc.keyframe_points.insert(frame, pos[i])

            # Rotation (convert to radians)
            for i, fc in enumerate(fcurves_rot):
                fc.keyframe_points.insert(frame, math.radians(rot[i]))

        # Update handles for smooth interpolation
        for fc in fcurves_loc + fcurves_rot:
            fc.update()

        return True

    def _get_target_at_frame(self, frame: int) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Get target position and velocity at frame."""
        if not HAS_BLENDER:
            return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

        obj = bpy.data.objects.get(self.target.object_name)
        if not obj:
            return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

        # Set frame and read position
        stored_frame = bpy.context.scene.frame_current
        try:
            bpy.context.scene.frame_set(frame)
            pos = tuple(obj.matrix_world.translation)

            # Calculate velocity from previous frame
            if frame > 1:
                bpy.context.scene.frame_set(frame - 1)
                prev_pos = Vector(obj.matrix_world.translation)
                vel = (Vector(pos) - prev_pos) * 24.0  # Assume 24fps
                velocity = tuple(vel._values)
            else:
                velocity = (0.0, 0.0, 0.0)

            return pos, velocity

        finally:
            bpy.context.scene.frame_set(stored_frame)

    def _get_target_position_at_index(self, index: int) -> Tuple[float, float, float]:
        """Get target position at path index."""
        if index < len(self._target_positions):
            return self._target_positions[index]

        # Fallback approximation from camera position
        if index < len(self._result.path_points):
            cam_pos = self._result.path_points[index]
            return (
                cam_pos[0],
                cam_pos[1] + self.config.ideal_distance,
                cam_pos[2] - self.config.ideal_height,
            )
        return (0.0, 0.0, 0.0)


def compute_pre_solve_path(
    config: FollowCameraConfig,
    target: FollowTarget,
    frame_start: int,
    frame_end: int,
    one_shot: Optional[OneShotConfig] = None,
) -> PreSolveResult:
    """
    Convenience function to compute pre-solve path.

    Args:
        config: Camera configuration
        target: Follow target
        frame_start: Start frame
        frame_end: End frame
        one_shot: Optional one-shot configuration

    Returns:
        PreSolveResult with computed path
    """
    presolver = PreSolver(config, target, one_shot=one_shot)
    return presolver.solve(frame_start, frame_end)


def create_one_shot_from_yaml(yaml_path: str) -> OneShotConfig:
    """
    Load one-shot configuration from YAML file.

    Args:
        yaml_path: Path to YAML configuration file

    Returns:
        OneShotConfig instance
    """
    import yaml

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    return OneShotConfig.from_dict(data.get("one_shot", {}))
