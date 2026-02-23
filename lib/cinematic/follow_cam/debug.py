"""
Follow Camera Debug Visualization

Implements visual debug tools for camera behavior:
- Camera frustum visualization
- Target and prediction visualization
- Obstacle detection rays
- Path visualization (ideal vs actual)
- HUD display

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-63
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

from .types import (
    FollowCameraConfig,
    CameraState,
    ObstacleInfo,
)

# Blender API guard for testing outside Blender
try:
    import bpy
    import mathutils
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    from .follow_modes import Vector


@dataclass
class DebugConfig:
    """
    Configuration for debug visualization.

    Attributes:
        show_frustum: Draw camera frustum
        show_target: Draw target marker
        show_prediction: Draw predicted position
        show_obstacles: Draw obstacle rays
        show_path: Draw ideal vs actual path
        show_hud: Show HUD overlay
        frustum_color: RGBA color for frustum
        target_color: RGBA color for target
        prediction_color: RGBA color for prediction
        obstacle_color: RGBA color for obstacles
        path_ideal_color: RGBA color for ideal path
        path_actual_color: RGBA color for actual path
        line_width: Width of debug lines
    """
    show_frustum: bool = True
    show_target: bool = True
    show_prediction: bool = True
    show_obstacles: bool = True
    show_path: bool = True
    show_hud: bool = True

    frustum_color: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 0.3)
    target_color: Tuple[float, float, float, float] = (1.0, 1.0, 0.0, 1.0)
    prediction_color: Tuple[float, float, float, float] = (0.0, 0.5, 1.0, 1.0)
    obstacle_color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.8)
    path_ideal_color: Tuple[float, float, float, float] = (0.0, 1.0, 0.5, 0.5)
    path_actual_color: Tuple[float, float, float, float] = (1.0, 0.5, 0.0, 0.5)

    line_width: float = 2.0


class DebugVisualizer:
    """
    Visualizes camera behavior for debugging.

    Creates Blender objects for debug visualization or stores
    debug data for external rendering.

    Usage:
        visualizer = DebugVisualizer(config)

        # Each frame
        visualizer.update(
            camera_state=current_state,
            target_position=subject_pos,
            predicted_position=predicted_pos,
            obstacles=detected_obstacles,
        )

        # Draw (creates/updates Blender objects)
        visualizer.draw()

        # Clean up when done
        visualizer.cleanup()
    """

    DEBUG_COLLECTION_NAME = "FollowCam_Debug"

    def __init__(self, config: DebugConfig = None):
        """
        Initialize debug visualizer.

        Args:
            config: Debug visualization configuration
        """
        self.config = config or DebugConfig()
        self._debug_objects: Dict[str, Any] = {}
        self._path_history: List[Tuple[float, float, float]] = []
        self._ideal_path_history: List[Tuple[float, float, float]] = []
        self._max_path_length = 300  # 5 seconds at 60fps

    def update(
        self,
        camera_state: CameraState,
        target_position: Tuple[float, float, float],
        predicted_position: Optional[Tuple[float, float, float]] = None,
        obstacles: Optional[List[ObstacleInfo]] = None,
        ideal_position: Optional[Tuple[float, float, float]] = None,
    ) -> None:
        """
        Update debug data for visualization.

        Call this every frame before draw().

        Args:
            camera_state: Current camera state
            target_position: Current target position
            predicted_position: Predicted target position
            obstacles: List of detected obstacles
            ideal_position: Ideal camera position (without collision adjustment)
        """
        # Store current state for drawing
        self._current_state = camera_state
        self._target_position = target_position
        self._predicted_position = predicted_position
        self._obstacles = obstacles or []
        self._ideal_position = ideal_position

        # Update path history
        self._path_history.append(camera_state.position)
        if len(self._path_history) > self._max_path_length:
            self._path_history.pop(0)

        if ideal_position:
            self._ideal_path_history.append(ideal_position)
            if len(self._ideal_path_history) > self._max_path_length:
                self._ideal_path_history.pop(0)

    def draw(self) -> None:
        """
        Draw debug visualization.

        Creates or updates Blender objects for visualization.
        """
        if not HAS_BLENDER:
            return

        # Get or create debug collection
        collection = self._get_debug_collection()

        # Draw each enabled visualization
        if self.config.show_frustum:
            self._draw_frustum(collection)

        if self.config.show_target:
            self._draw_target(collection)

        if self.config.show_prediction and self._predicted_position:
            self._draw_prediction(collection)

        if self.config.show_obstacles and self._obstacles:
            self._draw_obstacles(collection)

        if self.config.show_path:
            self._draw_paths(collection)

    def cleanup(self) -> None:
        """Remove all debug objects."""
        if HAS_BLENDER:
            # Remove debug collection
            collection = bpy.data.collections.get(self.DEBUG_COLLECTION_NAME)
            if collection:
                # Unlink all objects
                for obj in collection.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                # Remove collection
                bpy.data.collections.remove(collection)

            self._debug_objects.clear()

        # Always clear path history
        self._path_history.clear()
        self._ideal_path_history.clear()

    def _get_debug_collection(self):
        """Get or create debug collection."""
        collection = bpy.data.collections.get(self.DEBUG_COLLECTION_NAME)
        if not collection:
            collection = bpy.data.collections.new(self.DEBUG_COLLECTION_NAME)
            bpy.context.scene.collection.children.link(collection)
        return collection

    def _draw_frustum(self, collection) -> None:
        """Draw camera frustum visualization."""
        # Simplified frustum as a cone
        if not hasattr(self, '_current_state'):
            return

        pos = self._current_state.position
        rot = self._current_state.rotation

        # Create or update frustum object
        name = "Debug_Frustum"
        obj = self._debug_objects.get(name)

        if not obj:
            # Create cone for frustum
            bpy.ops.mesh.primitive_cone_add(
                radius1=0.5,
                radius2=2.0,
                depth=3.0,
            )
            obj = bpy.context.active_object
            obj.name = name
            collection.objects.link(obj)
            bpy.context.collection.objects.unlink(obj)
            self._debug_objects[name] = obj

        # Update position
        obj.location = pos
        obj.rotation_euler = [math.radians(r) for r in rot]

        # Set material color
        self._set_object_color(obj, self.config.frustum_color)

    def _draw_target(self, collection) -> None:
        """Draw target marker."""
        if not hasattr(self, '_target_position'):
            return

        name = "Debug_Target"
        obj = self._debug_objects.get(name)

        if not obj:
            # Create sphere for target
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2)
            obj = bpy.context.active_object
            obj.name = name
            collection.objects.link(obj)
            bpy.context.collection.objects.unlink(obj)
            self._debug_objects[name] = obj

        obj.location = self._target_position
        self._set_object_color(obj, self.config.target_color)

    def _draw_prediction(self, collection) -> None:
        """Draw predicted position marker."""
        if not self._predicted_position:
            return

        name = "Debug_Prediction"
        obj = self._debug_objects.get(name)

        if not obj:
            # Create smaller sphere for prediction
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15)
            obj = bpy.context.active_object
            obj.name = name
            collection.objects.link(obj)
            bpy.context.collection.objects.unlink(obj)
            self._debug_objects[name] = obj

        obj.location = self._predicted_position
        self._set_object_color(obj, self.config.prediction_color)

        # Draw line from target to prediction
        self._draw_line(
            "Debug_PredictionLine",
            self._target_position,
            self._predicted_position,
            self.config.prediction_color,
        )

    def _draw_obstacles(self, collection) -> None:
        """Draw obstacle detection rays."""
        if not hasattr(self, '_current_state'):
            return

        cam_pos = self._current_state.position

        for i, obstacle in enumerate(self._obstacles):
            name = f"Debug_Obstacle_{i}"

            # Draw ray from camera to obstacle
            self._draw_line(
                name,
                cam_pos,
                obstacle.position,
                self.config.obstacle_color,
            )

    def _draw_paths(self, collection) -> None:
        """Draw ideal vs actual path."""
        # Draw actual path
        if len(self._path_history) > 1:
            self._draw_path_points(
                "Debug_Path_Actual",
                self._path_history,
                self.config.path_actual_color,
            )

        # Draw ideal path
        if len(self._ideal_path_history) > 1:
            self._draw_path_points(
                "Debug_Path_Ideal",
                self._ideal_path_history,
                self.config.path_ideal_color,
            )

    def _draw_line(
        self,
        name: str,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        color: Tuple[float, float, float, float],
    ) -> None:
        """Draw a line between two points."""
        if not HAS_BLENDER:
            return

        obj = self._debug_objects.get(name)

        if not obj:
            # Create line mesh
            import bmesh
            mesh = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, mesh)

            bm = bmesh.new()
            v1 = bm.verts.new(start)
            v2 = bm.verts.new(end)
            bm.edges.new((v1, v2))
            bm.to_mesh(mesh)
            bm.free()

            collection = self._get_debug_collection()
            collection.objects.link(obj)
            self._debug_objects[name] = obj
        else:
            # Update vertices
            mesh = obj.data
            mesh.vertices[0].co = start
            mesh.vertices[1].co = end
            mesh.update()

        self._set_object_color(obj, color)

    def _draw_path_points(
        self,
        name: str,
        points: List[Tuple[float, float, float]],
        color: Tuple[float, float, float, float],
    ) -> None:
        """Draw a path from list of points."""
        if not HAS_BLENDER or len(points) < 2:
            return

        obj = self._debug_objects.get(name)

        if not obj:
            import bmesh
            mesh = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, mesh)

            bm = bmesh.new()
            verts = [bm.verts.new(p) for p in points]
            for i in range(len(verts) - 1):
                bm.edges.new((verts[i], verts[i + 1]))
            bm.to_mesh(mesh)
            bm.free()

            collection = self._get_debug_collection()
            collection.objects.link(obj)
            self._debug_objects[name] = obj
        else:
            # Update mesh with new points
            import bmesh
            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)

            # Clear existing
            bmesh.ops.delete(bm, geom=bm.verts)

            # Add new points
            verts = [bm.verts.new(p) for p in points]
            for i in range(len(verts) - 1):
                bm.edges.new((verts[i], verts[i + 1]))

            bm.to_mesh(mesh)
            bm.free()

        self._set_object_color(obj, color)

    def _set_object_color(
        self,
        obj,
        color: Tuple[float, float, float, float],
    ) -> None:
        """Set object viewport color."""
        if obj and hasattr(obj, 'color'):
            obj.color = color
            # Also set show_wire for visibility
            obj.show_wire = True


# =============================================================================
# TEXT HUD
# =============================================================================

def generate_hud_text(
    camera_state: CameraState,
    config: FollowCameraConfig,
    fps: float = 60.0,
) -> str:
    """
    Generate HUD text for display.

    Args:
        camera_state: Current camera state
        config: Camera configuration
        fps: Current frames per second

    Returns:
        Formatted HUD text
    """
    lines = [
        "=== Follow Camera Debug ===",
        f"Mode: {camera_state.current_mode.value}",
        f"Position: ({camera_state.position[0]:.1f}, {camera_state.position[1]:.1f}, {camera_state.position[2]:.1f})",
        f"Distance: {camera_state.distance:.2f}m",
        f"Height: {camera_state.height:.2f}m",
        f"Yaw: {camera_state.yaw:.1f} deg",
        f"Pitch: {camera_state.pitch:.1f} deg",
        "",
        f"Target Velocity: ({camera_state.target_velocity[0]:.1f}, {camera_state.target_velocity[1]:.1f}, {camera_state.target_velocity[2]:.1f})",
        f"Obstacles: {len(camera_state.obstacles)}",
        f"Transitioning: {'Yes' if camera_state.is_transitioning else 'No'}",
        "",
        f"FPS: {fps:.1f}",
    ]

    if camera_state.is_transitioning:
        lines.append(f"Transition Progress: {camera_state.transition_progress * 100:.0f}%")

    return "\n".join(lines)


def get_debug_stats(
    camera_state: CameraState,
    config: FollowCameraConfig,
) -> Dict[str, Any]:
    """
    Get debug statistics for external display.

    Args:
        camera_state: Current camera state
        config: Camera configuration

    Returns:
        Dictionary of debug statistics
    """
    return {
        "mode": camera_state.current_mode.value,
        "position": camera_state.position,
        "rotation": camera_state.rotation,
        "distance": camera_state.distance,
        "height": camera_state.height,
        "yaw": camera_state.yaw,
        "pitch": camera_state.pitch,
        "velocity": camera_state.velocity,
        "target_velocity": camera_state.target_velocity,
        "obstacle_count": len(camera_state.obstacles),
        "is_transitioning": camera_state.is_transitioning,
        "transition_progress": camera_state.transition_progress,
        "collision_enabled": config.collision_enabled,
        "prediction_enabled": config.prediction_enabled,
    }


# =============================================================================
# FRAME-BY-FRAME ANALYSIS (Phase 8.4)
# =============================================================================

@dataclass
class FrameAnalysis:
    """
    Analysis data for a single frame.

    Attributes:
        frame: Frame number
        timestamp: Time in seconds
        camera_position: Camera world position
        camera_rotation: Camera Euler rotation
        target_position: Target world position
        target_velocity: Target velocity vector
        mode: Current follow mode
        distance: Distance to target
        framing_quality: Framing quality score (0-1)
        obstacle_count: Number of obstacles detected
        is_occluded: Whether target is occluded
        oscillation_detected: Whether oscillation was detected
        damping_applied: Damping factor applied
        transition_active: Whether in transition
        transition_progress: Transition progress (0-1)
        warnings: List of warning messages
    """
    frame: int = 0
    timestamp: float = 0.0
    camera_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    camera_rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    mode: str = "over_shoulder"
    distance: float = 3.0
    framing_quality: float = 1.0
    obstacle_count: int = 0
    is_occluded: bool = False
    oscillation_detected: bool = False
    damping_applied: float = 0.0
    transition_active: bool = False
    transition_progress: float = 0.0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "frame": self.frame,
            "timestamp": self.timestamp,
            "camera_position": list(self.camera_position),
            "camera_rotation": list(self.camera_rotation),
            "target_position": list(self.target_position),
            "target_velocity": list(self.target_velocity),
            "mode": self.mode,
            "distance": self.distance,
            "framing_quality": self.framing_quality,
            "obstacle_count": self.obstacle_count,
            "is_occluded": self.is_occluded,
            "oscillation_detected": self.oscillation_detected,
            "damping_applied": self.damping_applied,
            "transition_active": self.transition_active,
            "transition_progress": self.transition_progress,
            "warnings": self.warnings,
        }


class FrameAnalyzer:
    """
    Records and analyzes camera behavior frame-by-frame.

    Collects detailed per-frame data for troubleshooting
    and optimization.

    Usage:
        analyzer = FrameAnalyzer()

        # Each frame
        analysis = analyzer.analyze_frame(
            frame=frame_number,
            camera_state=current_state,
            config=config,
            framing_quality=quality,
            damping=damping_factor,
        )

        # Get report
        report = analyzer.generate_report()
        analyzer.save_report("analysis.json")
    """

    def __init__(self, max_frames: int = 10000):
        """
        Initialize frame analyzer.

        Args:
            max_frames: Maximum frames to record
        """
        self._frames: List[FrameAnalysis] = []
        self._max_frames = max_frames

    def analyze_frame(
        self,
        frame: int,
        camera_state: CameraState,
        config: FollowCameraConfig,
        framing_quality: float = 1.0,
        damping: float = 0.0,
        oscillation_detected: bool = False,
        is_occluded: bool = False,
        fps: float = 60.0,
    ) -> FrameAnalysis:
        """
        Analyze a single frame.

        Args:
            frame: Frame number
            camera_state: Current camera state
            config: Camera configuration
            framing_quality: Current framing quality (0-1)
            damping: Damping factor applied
            oscillation_detected: Whether oscillation was detected
            is_occluded: Whether target is occluded
            fps: Frames per second for timestamp calculation

        Returns:
            FrameAnalysis with recorded data
        """
        warnings = []

        # Generate warnings for problematic conditions
        if is_occluded:
            warnings.append("Target occluded")

        if oscillation_detected:
            warnings.append("Oscillation detected")

        if damping > 0.5:
            warnings.append(f"High damping: {damping:.2f}")

        if framing_quality < 0.5:
            warnings.append(f"Low framing quality: {framing_quality:.2f}")

        if camera_state.distance < config.min_distance:
            warnings.append(f"Below min distance: {camera_state.distance:.2f}")

        if camera_state.distance > config.max_distance:
            warnings.append(f"Above max distance: {camera_state.distance:.2f}")

        analysis = FrameAnalysis(
            frame=frame,
            timestamp=frame / fps,
            camera_position=camera_state.position,
            camera_rotation=camera_state.rotation,
            target_position=camera_state.target_position,
            target_velocity=camera_state.target_velocity,
            mode=camera_state.current_mode.value,
            distance=camera_state.distance,
            framing_quality=framing_quality,
            obstacle_count=len(camera_state.obstacles),
            is_occluded=is_occluded,
            oscillation_detected=oscillation_detected,
            damping_applied=damping,
            transition_active=camera_state.is_transitioning,
            transition_progress=camera_state.transition_progress,
            warnings=warnings,
        )

        # Add to history
        self._frames.append(analysis)

        # Trim if needed
        if len(self._frames) > self._max_frames:
            self._frames.pop(0)

        return analysis

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate analysis report.

        Returns:
            Dictionary with statistics and problem frames
        """
        if not self._frames:
            return {"error": "No frames recorded"}

        # Calculate statistics
        avg_quality = sum(f.framing_quality for f in self._frames) / len(self._frames)
        avg_distance = sum(f.distance for f in self._frames) / len(self._frames)
        occluded_frames = sum(1 for f in self._frames if f.is_occluded)
        oscillation_frames = sum(1 for f in self._frames if f.oscillation_detected)
        transition_frames = sum(1 for f in self._frames if f.transition_active)

        # Find problem frames
        problem_frames = [
            f.to_dict() for f in self._frames
            if f.is_occluded or f.oscillation_detected or len(f.warnings) > 0
        ]

        # Calculate mode distribution
        mode_counts: Dict[str, int] = {}
        for f in self._frames:
            mode_counts[f.mode] = mode_counts.get(f.mode, 0) + 1

        return {
            "summary": {
                "total_frames": len(self._frames),
                "duration_seconds": self._frames[-1].timestamp if self._frames else 0,
                "average_framing_quality": avg_quality,
                "average_distance": avg_distance,
                "occluded_frame_count": occluded_frames,
                "occluded_percentage": (occluded_frames / len(self._frames)) * 100,
                "oscillation_frame_count": oscillation_frames,
                "oscillation_percentage": (oscillation_frames / len(self._frames)) * 100,
                "transition_frame_count": transition_frames,
                "problem_frame_count": len(problem_frames),
            },
            "mode_distribution": mode_counts,
            "problem_frames": problem_frames[:100],  # Limit to 100 for report
        }

    def save_report(self, filepath: str) -> bool:
        """
        Save report to JSON file.

        Args:
            filepath: Path to save report

        Returns:
            True if successful
        """
        import json

        try:
            report = self.generate_report()
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save report: {e}")
            return False

    def get_frames(self) -> List[FrameAnalysis]:
        """Get all recorded frames."""
        return self._frames.copy()

    def clear(self) -> None:
        """Clear all recorded frames."""
        self._frames.clear()
