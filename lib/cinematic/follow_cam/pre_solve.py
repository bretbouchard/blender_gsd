"""
Follow Camera Pre-Solve Workflow

Pre-compute complex camera moves for deterministic renders:
- Scene analysis stage
- Ideal path computation
- Avoidance adjustment
- Path smoothing
- Keyframe baking

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
class PreSolveResult:
    """
    Result of pre-solve computation.

    Attributes:
        success: Whether pre-solve completed successfully
        stage: Current/last stage completed
        frames_processed: Number of frames processed
        path_points: Computed camera path points
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    stage: PreSolveStage = PreSolveStage.SCENE_ANALYSIS
    frames_processed: int = 0
    path_points: List[Tuple[float, float, float]] = field(default_factory=list)
    rotation_points: List[Tuple[float, float, float]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stage": self.stage.value,
            "frames_processed": self.frames_processed,
            "path_points": self.path_points,
            "rotation_points": self.rotation_points,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class PreSolver:
    """
    Pre-computes camera paths for deterministic rendering.

    Analyzes scene and computes camera path before rendering
    to ensure consistent results.

    Usage:
        presolver = PreSolver(config, target)
        result = presolver.solve(frame_start=1, frame_end=250)

        if result.success:
            # Apply baked keyframes
            presolver.apply_to_camera(camera_name)
    """

    def __init__(
        self,
        config: FollowCameraConfig,
        target: FollowTarget,
    ):
        """
        Initialize pre-solver.

        Args:
            config: Camera configuration
            target: Follow target
        """
        self.config = config
        self.target = target
        self._result = PreSolveResult()
        self._stage_progress = 0.0

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

        self._result.path_points.clear()
        self._result.rotation_points.clear()

        for frame in range(frame_start, frame_end + 1):
            # Get target position at this frame
            target_pos, target_vel = self._get_target_at_frame(frame)

            # Calculate ideal camera position
            target_fwd = get_target_forward_direction(Vector(target_vel))

            pos, yaw, pitch = calculate_ideal_position(
                target_position=target_pos,
                target_forward=tuple(target_fwd._values),
                target_velocity=target_vel,
                config=self.config,
            )

            self._result.path_points.append(tuple(pos._values))
            self._result.rotation_points.append((yaw, pitch, 0.0))

        self._stage_progress = 1.0

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
        if not HAS_BLENDER:
            return (0.0, 0.0, 0.0)

        # This is a simplified version
        # In full implementation, would track target positions during solve
        if index < len(self._result.path_points):
            # Approximate from camera position
            cam_pos = self._result.path_points[index]
            # Assume target is in front of camera at ideal distance
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
) -> PreSolveResult:
    """
    Convenience function to compute pre-solve path.

    Args:
        config: Camera configuration
        target: Follow target
        frame_start: Start frame
        frame_end: End frame

    Returns:
        PreSolveResult with computed path
    """
    presolver = PreSolver(config, target)
    return presolver.solve(frame_start, frame_end)
