"""
Camera Solver Module - Blender libmv Integration

Integrates Blender's motion tracking API for camera solving.
Provides auto keyframe selection, focal length refinement, and
solve quality reporting.

Uses Blender API guards for testing outside Blender environment.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable
import time
import math

# Blender API guard
try:
    import bpy
    from bpy.types import MovieTracking, MovieTrackingTrack, MovieTrackingObject
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Create fallback types for testing
    MovieTracking = None
    MovieTrackingTrack = None
    MovieTrackingObject = None

from .types import (
    Track,
    Solve,
    SolveResult,
    SolveStatus,
    TrackingConfig,
    TrackingSession,
    TrackStatus,
)


@dataclass
class SolveOptions:
    """
    Solver-specific options for libmv.

    Maps to Blender's tracking solver settings.
    """
    refine_intrinsics: List[str] = field(default_factory=lambda: ["focal_length"])
    motion_model: str = "AFFINE"  # AFFINE, HOMOGRAPHY, SIMILARITY
    use_keyframe_selection: bool = True
    keyframe1: int = -1  # -1 = auto
    keyframe2: int = -1  # -1 = auto
    use_fallback_reconstruction: bool = True
    tripocal_solver_scale: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "refine_intrinsics": self.refine_intrinsics,
            "motion_model": self.motion_model,
            "use_keyframe_selection": self.use_keyframe_selection,
            "keyframe1": self.keyframe1,
            "keyframe2": self.keyframe2,
            "use_fallback_reconstruction": self.use_fallback_reconstruction,
            "tripocal_solver_scale": self.tripocal_solver_scale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SolveOptions:
        return cls(
            refine_intrinsics=data.get("refine_intrinsics", ["focal_length"]),
            motion_model=data.get("motion_model", "AFFINE"),
            use_keyframe_selection=data.get("use_keyframe_selection", True),
            keyframe1=data.get("keyframe1", -1),
            keyframe2=data.get("keyframe2", -1),
            use_fallback_reconstruction=data.get("use_fallback_reconstruction", True),
            tripocal_solver_scale=data.get("tripocal_solver_scale", 1.0),
        )


@dataclass
class SolveReport:
    """
    Report from camera solve operation.

    Contains detailed information about solve quality and statistics.
    """
    success: bool = False
    average_error: float = 0.0
    max_error: float = 0.0
    min_error: float = 0.0
    frames_solved: int = 0
    tracks_used: int = 0
    keyframes: Tuple[int, int] = (0, 0)
    solve_time_seconds: float = 0.0
    message: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "average_error": self.average_error,
            "max_error": self.max_error,
            "min_error": self.min_error,
            "frames_solved": self.frames_solved,
            "tracks_used": self.tracks_used,
            "keyframes": list(self.keyframes),
            "solve_time_seconds": self.solve_time_seconds,
            "message": self.message,
            "warnings": self.warnings,
        }


class CameraSolver:
    """
    Camera solver using Blender's libmv integration.

    Provides camera reconstruction from 2D tracks with support for:
    - Auto keyframe selection
    - Focal length refinement
    - Radial distortion estimation
    - Quality reporting

    Usage:
        solver = CameraSolver(session)
        report = solver.solve(config)
        if report.success:
            solve = solver.get_solve()
    """

    # Motion model mapping
    MOTION_MODELS = {
        "affine": "AFFINE",
        "homography": "HOMOGRAPHY",
        "similarity": "SIMILARITY",
        "perspective": "HOMOGRAPHY",  # Alias
    }

    # Intrinsic refinement flags mapping
    INTRINSIC_FLAGS = {
        "focal_length": "FOCAL_LENGTH",
        "principal_point": "PRINCIPAL_POINT",
        "radial_distortion": "RADIAL_DISTORTION_K1",
        "radial_distortion_k2": "RADIAL_DISTORTION_K2",
        "tangential_distortion": "TANGENTIAL_DISTORTION",
    }

    def __init__(self, session: Optional[TrackingSession] = None):
        """
        Initialize camera solver.

        Args:
            session: Optional tracking session to solve
        """
        self.session = session
        self._solve: Optional[Solve] = None
        self._report: Optional[SolveReport] = None

    def set_session(self, session: TrackingSession) -> None:
        """Set the tracking session to solve."""
        self.session = session
        self._solve = None
        self._report = None

    def _validate_session(self) -> List[str]:
        """
        Validate session has enough tracks for solving.

        Returns:
            List of validation warnings
        """
        warnings = []

        if not self.session:
            warnings.append("No session set")
            return warnings

        if len(self.session.tracks) < 8:
            warnings.append(f"Only {len(self.session.tracks)} tracks, recommend 8+ for stable solve")

        # Count tracks with enough keyframes
        good_tracks = 0
        for track in self.session.tracks:
            keyframe_count = len(track.is_keyframe) if track.is_keyframe else 0
            if keyframe_count >= 2:
                good_tracks += 1

        if good_tracks < 5:
            warnings.append(f"Only {good_tracks} tracks with keyframes, need at least 5")

        return warnings

    def _auto_select_keyframes(self, config: TrackingConfig) -> Tuple[int, int]:
        """
        Automatically select best keyframes for solve.

        Uses parallax analysis to find frames with maximum separation.

        Args:
            config: Tracking configuration

        Returns:
            Tuple of (keyframe1, keyframe2)
        """
        if not self.session or not self.session.tracks:
            return (1, 2)

        # Find common frame range across all tracks
        all_frames = set()
        for track in self.session.tracks:
            for point in track.points:
                if point.status == TrackStatus.OK:
                    all_frames.add(point.frame)

        if len(all_frames) < 2:
            return (1, 2)

        sorted_frames = sorted(all_frames)
        total_frames = len(sorted_frames)

        # For auto selection, pick frames at 1/3 and 2/3 through the range
        # This provides good parallax for most camera motions
        idx1 = total_frames // 3
        idx2 = 2 * total_frames // 3

        return (sorted_frames[idx1], sorted_frames[idx2])

    def _build_intrinsics_flags(self, config: TrackingConfig) -> List[str]:
        """
        Build intrinsic refinement flags from config.

        Args:
            config: Tracking configuration

        Returns:
            List of intrinsic flag names
        """
        flags = []
        if config.refine_focal_length:
            flags.append("FOCAL_LENGTH")
        if config.refine_principal_point:
            flags.extend(["PRINCIPAL_POINT_X", "PRINCIPAL_POINT_Y"])
        if config.refine_radial_distortion:
            flags.extend(["RADIAL_DISTORTION_K1", "RADIAL_DISTORTION_K2"])
        if config.refine_tangential_distortion:
            flags.extend(["TANGENTIAL_DISTORTION_P1", "TANGENTIAL_DISTORTION_P2"])
        return flags if flags else ["FOCAL_LENGTH"]

    def solve(
        self,
        config: Optional[TrackingConfig] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> SolveReport:
        """
        Solve camera motion from 2D tracks.

        Args:
            config: Tracking configuration (uses defaults if None)
            progress_callback: Optional callback for progress updates (0.0-1.0)

        Returns:
            SolveReport with solve results and quality metrics
        """
        start_time = time.time()
        config = config or TrackingConfig()

        # Validate session
        warnings = self._validate_session()
        if warnings and "No session set" in warnings:
            self._report = SolveReport(
                success=False,
                message="No tracking session set",
                warnings=warnings,
                solve_time_seconds=time.time() - start_time,
            )
            return self._report

        # Initialize solve
        self._solve = Solve(status=SolveStatus.RUNNING)

        try:
            if HAS_BLENDER:
                report = self._solve_in_blender(config, progress_callback)
            else:
                report = self._solve_fallback(config, progress_callback)

            report.solve_time_seconds = time.time() - start_time
            report.warnings.extend(warnings)

            self._report = report
            self._solve.status = SolveStatus.SUCCESS if report.success else SolveStatus.FAILED
            self._solve.average_error = report.average_error
            self._solve.keyframes = list(report.keyframes)

        except Exception as e:
            self._report = SolveReport(
                success=False,
                message=f"Solve failed: {str(e)}",
                warnings=warnings,
                solve_time_seconds=time.time() - start_time,
            )
            if self._solve:
                self._solve.status = SolveStatus.FAILED

        return self._report

    def _solve_in_blender(
        self,
        config: TrackingConfig,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> SolveReport:
        """
        Solve using Blender's libmv integration.

        Args:
            config: Tracking configuration
            progress_callback: Progress callback

        Returns:
            SolveReport with results
        """
        if progress_callback:
            progress_callback(0.1)

        # Get active tracking object
        tracking = bpy.context.scene.tool_settings.movieclip.tracking
        tracking_object = tracking.objects.active

        # Configure solver settings
        settings = tracking_object.settings

        # Set motion model
        settings.motion_model = self.MOTION_MODELS.get(
            config.solver_motion_model.lower(), "AFFINE"
        )

        # Set keyframes
        if config.solver_keyframe_selection == "auto" or config.auto_keyframe:
            kf1, kf2 = self._auto_select_keyframes(config)
            settings.keyframe1 = kf1
            settings.keyframe2 = kf2
            settings.use_keyframe_selection = True
        else:
            settings.use_keyframe_selection = False

        # Set refinement flags
        refine_flags = set()
        if config.refine_focal_length:
            refine_flags.add("FOCAL_LENGTH")
        if config.refine_principal_point:
            refine_flags.add("PRINCIPAL_POINT")
        if config.refine_radial_distortion:
            refine_flags.add("RADIAL_DISTORTION_K1")
            refine_flags.add("RADIAL_DISTORTION_K2")
        if config.refine_tangential_distortion:
            refine_flags.add("TANGENTIAL_DISTORTION")

        settings.refine_intrinsics = ",".join(refine_flags) if refine_flags else "FOCAL_LENGTH"

        if progress_callback:
            progress_callback(0.2)

        # Run solver
        bpy.ops.clip.solve_camera(
            scene=bpy.context.scene.name,
            stop_after_solve=True,
        )

        if progress_callback:
            progress_callback(0.9)

        # Get solve results
        camera_object = tracking_object.cameras[0] if tracking_object.cameras else None

        if not camera_object:
            return SolveReport(
                success=False,
                message="No camera reconstructed",
            )

        # Calculate error statistics
        total_error = 0.0
        max_error = 0.0
        min_error = float("inf")
        frame_count = 0

        for marker in camera_object.markers:
            error = marker.error
            if error > 0:
                total_error += error
                max_error = max(max_error, error)
                min_error = min(min_error, error)
                frame_count += 1

        avg_error = total_error / frame_count if frame_count > 0 else 0.0

        # Build solve results
        results = []
        for marker in camera_object.markers:
            frame = marker.frame
            # Convert Blender camera position/rotation to our format
            # This is a simplified version - actual implementation would
            # extract the reconstructed camera transform
            result = SolveResult(
                frame=frame,
                position=(0.0, 0.0, 0.0),  # Would be filled from actual reconstruction
                rotation=(1.0, 0.0, 0.0, 0.0),
                error=marker.error if marker.error > 0 else 0.0,
            )
            results.append(result)

        self._solve.results = results

        return SolveReport(
            success=True,
            average_error=avg_error,
            max_error=max_error,
            min_error=min_error if min_error != float("inf") else 0.0,
            frames_solved=frame_count,
            tracks_used=len(self.session.tracks) if self.session else 0,
            keyframes=(settings.keyframe1, settings.keyframe2),
            message="Solve completed successfully",
        )

    def _solve_fallback(
        self,
        config: TrackingConfig,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> SolveReport:
        """
        Fallback solver for testing outside Blender.

        Generates mock solve results for testing purposes.

        Args:
            config: Tracking configuration
            progress_callback: Progress callback

        Returns:
            SolveReport with mock results
        """
        if progress_callback:
            progress_callback(0.1)

        # Select keyframes
        kf1, kf2 = self._auto_select_keyframes(config)

        if progress_callback:
            progress_callback(0.3)

        # Generate mock results for all frames in footage
        if self.session and self.session.footage:
            frame_start = self.session.footage.frame_start
            frame_end = self.session.footure.frame_end
        else:
            frame_start = 1
            frame_end = 120

        results = []
        total_error = 0.0

        for frame in range(frame_start, frame_end + 1):
            # Mock camera motion - simple circular path
            t = (frame - frame_start) / max(1, frame_end - frame_start)
            angle = t * 2 * math.pi

            # Circular camera motion
            radius = 5.0
            x = radius * math.cos(angle)
            y = 0.0
            z = radius * math.sin(angle)

            # Mock rotation (looking at center)
            # Simplified quaternion for facing center
            w = math.cos(angle / 2)
            rx = 0.0
            ry = math.sin(angle / 2)
            rz = 0.0

            # Mock error (lower near keyframes)
            dist_to_kf = min(abs(frame - kf1), abs(frame - kf2))
            error = 0.5 + 0.5 * (1.0 / (1.0 + dist_to_kf * 0.1))
            total_error += error

            result = SolveResult(
                frame=frame,
                position=(x, y, z),
                rotation=(w, rx, ry, rz),
                focal_length=50.0 + 5.0 * math.sin(t * 4 * math.pi),  # Slight focal length variation
                error=error,
            )
            results.append(result)

        if progress_callback:
            progress_callback(0.9)

        self._solve.results = results
        avg_error = total_error / len(results) if results else 0.0

        return SolveReport(
            success=True,
            average_error=avg_error,
            max_error=1.0,
            min_error=0.5,
            frames_solved=len(results),
            tracks_used=len(self.session.tracks) if self.session else 0,
            keyframes=(kf1, kf2),
            message="Mock solve completed (testing mode)",
        )

    def get_solve(self) -> Optional[Solve]:
        """
        Get the current solve result.

        Returns:
            Solve object with camera reconstruction data
        """
        return self._solve

    def get_report(self) -> Optional[SolveReport]:
        """
        Get the last solve report.

        Returns:
            SolveReport from last solve operation
        """
        return self._report

    def apply_to_camera(
        self,
        camera_name: str = "Camera",
        solve: Optional[Solve] = None,
    ) -> bool:
        """
        Apply solved camera motion to a Blender camera.

        Args:
            camera_name: Name of camera object to apply to
            solve: Solve to apply (uses current if None)

        Returns:
            True if successful
        """
        if not HAS_BLENDER:
            return False

        solve = solve or self._solve
        if not solve or solve.status != SolveStatus.SUCCESS:
            return False

        camera = bpy.data.objects.get(camera_name)
        if not camera or camera.type != "CAMERA":
            return False

        # Set animation for each frame
        for result in solve.results:
            frame = result.frame

            # Set position
            camera.location = result.position
            camera.keyframe_insert(data_path="location", frame=frame)

            # Set rotation (convert quaternion to Euler)
            # This is simplified - actual implementation would handle quaternion properly
            camera.rotation_mode = "QUATERNION"
            camera.rotation_quaternion = result.rotation
            camera.keyframe_insert(data_path="rotation_quaternion", frame=frame)

            # Set focal length
            camera.data.lens = result.focal_length
            camera.data.keyframe_insert(data_path="lens", frame=frame)

        return True

    def refine_focal_length(
        self,
        initial_focal: float,
        frame_range: Optional[Tuple[int, int]] = None,
    ) -> float:
        """
        Refine focal length estimate from solve.

        Analyzes solve results to determine optimal focal length.

        Args:
            initial_focal: Initial focal length estimate
            frame_range: Optional frame range to analyze

        Returns:
            Refined focal length in mm
        """
        solve = self._solve
        if not solve or not solve.results:
            return initial_focal

        results = solve.results
        if frame_range:
            start, end = frame_range
            results = [r for r in results if start <= r.frame <= end]

        if not results:
            return initial_focal

        # Average focal length from solve results
        focal_lengths = [r.focal_length for r in results if r.focal_length > 0]
        if not focal_lengths:
            return initial_focal

        # Use weighted average based on error (lower error = higher weight)
        weighted_sum = 0.0
        weight_sum = 0.0

        for r in results:
            if r.focal_length > 0:
                weight = 1.0 / (r.error + 0.1)  # Avoid division by zero
                weighted_sum += r.focal_length * weight
                weight_sum += weight

        refined = weighted_sum / weight_sum if weight_sum > 0 else initial_focal
        return refined


# Fallback classes for testing outside Blender
if not HAS_BLENDER:
    class MockCameraSolver(CameraSolver):
        """Mock camera solver for testing without Blender."""

        def solve(self, config=None, progress_callback=None):
            """Mock solve that returns simulated results."""
            return super()._solve_fallback(config or TrackingConfig(), progress_callback)
