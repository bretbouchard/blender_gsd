"""
Object Tracking Module

Provides specialized trackers for control surface elements:
- PlanarTracker: Corner pin tracking for surfaces
- KnobTracker: Rotation extraction from knob footage
- RigidBodyTracker: 6-DOF object solving
- FaderTracker: Linear fader position tracking
- ObjectTracker: Unified interface

Integration with MorphEngine:
    from lib.cinematic.tracking import KnobTracker
    from lib.control_system.morphing import MorphEngine

    # Extract rotation from knob footage
    tracker = KnobTracker()
    rotations = tracker.track_rotation(session)

    # Convert to morph factors for MorphEngine
    morph_factors = tracker.rotation_to_morph(rotations, min_angle=0, max_angle=300)

    # Apply to morph animation
    engine = MorphEngine()
    # morph_factors[frame] -> engine.set_group_factor("knobs", factor)
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from .types import (
        TrackingSession,
        TrackData,
        CornerPinData,
        PlanarTrack,
        RotationCurve,
        RigidBodySolve,
    )

from .types import (
    CornerPinData,
    PlanarTrack,
    RotationCurve,
    RigidBodySolve,
    TrackData,
)


# =============================================================================
# PLANAR TRACKER
# =============================================================================

class PlanarTracker:
    """
    Tracks 4 corners for corner pin effects and planar transformations.

    Provides corner pin data suitable for compositing and Nuke export.

    Usage:
        tracker = PlanarTracker()
        planar = tracker.track_corners(session, corners=[(0,0), (1,0), (1,1), (0,1)])
        nuke_script = tracker.export_corner_pin_nuke(planar)
    """

    def __init__(self):
        self.tracks: List[PlanarTrack] = []

    def track_corners(
        self,
        session: "TrackingSession",
        initial_corners: Optional[Tuple[
            Tuple[float, float], Tuple[float, float],
            Tuple[float, float], Tuple[float, float]
        ]] = None,
        track_name: str = "planar_track"
    ) -> PlanarTrack:
        """
        Track 4 corners across the session frame range.

        Args:
            session: Tracking session with point tracks
            initial_corners: Initial corner positions (normalized 0-1)
            track_name: Name for the planar track

        Returns:
            PlanarTrack with per-frame corner data
        """
        if initial_corners is None:
            initial_corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

        # Create corner pin data from session tracks
        corners: List[CornerPinData] = []

        # Map session tracks to corners (expect 4 tracks named corner_0, corner_1, etc.)
        corner_tracks = [t for t in session.tracks if t.name.startswith("corner_")]

        if len(corner_tracks) >= 4:
            # Sort by corner index
            corner_tracks.sort(key=lambda t: int(t.name.split("_")[-1]))

            for frame in range(session.frame_start, session.frame_end + 1):
                frame_corners = []
                for track in corner_tracks[:4]:
                    if frame in track.markers:
                        frame_corners.append(track.markers[frame])
                    else:
                        # Use last known position or initial
                        frame_corners.append(
                            track.markers.get(frame - 1, initial_corners[corner_tracks.index(track)])
                        )

                if len(frame_corners) == 4:
                    corners.append(CornerPinData(
                        frame=frame,
                        corners=tuple(frame_corners),  # type: ignore
                    ))

        planar = PlanarTrack(
            name=track_name,
            frame_start=session.frame_start,
            frame_end=session.frame_end,
            corners=corners,
            reference_corners=initial_corners,
        )

        self.tracks.append(planar)
        return planar

    def export_corner_pin_nuke(
        self,
        track: PlanarTrack,
        output_path: Optional[str] = None
    ) -> str:
        """
        Export corner pin data to Nuke script format.

        Args:
            track: PlanarTrack to export
            output_path: Optional file path to write

        Returns:
            Nuke script content as string
        """
        lines = [
            "# Nuke Corner Pin Export",
            f"# Track: {track.name}",
            f"# Frame range: {track.frame_start}-{track.frame_end}",
            "",
            "CornerPin2D {",
        ]

        # Add per-frame animation
        for corner_data in track.corners:
            frame = corner_data.frame
            corners = corner_data.corners

            # Nuke uses to1, to2, to3, to4 for corner positions
            lines.append(f"  to1 {{ {corners[0][0]:.6f} {corners[0][1]:.6f} }}")
            lines.append(f"  to2 {{ {corners[1][0]:.6f} {corners[1][1]:.6f} }}")
            lines.append(f"  to3 {{ {corners[2][0]:.6f} {corners[2][1]:.6f} }}")
            lines.append(f"  to4 {{ {corners[3][0]:.6f} {corners[3][1]:.6f} }}")

        lines.append("}")

        nuke_script = "\n".join(lines)

        if output_path:
            with open(output_path, "w") as f:
                f.write(nuke_script)

        return nuke_script

    def get_track(self, track_id: str) -> Optional[PlanarTrack]:
        """Get a planar track by ID."""
        for track in self.tracks:
            if track.id == track_id:
                return track
        return None


# =============================================================================
# KNOB TRACKER
# =============================================================================

class KnobTracker:
    """
    Extracts rotation from knob footage for morph animation integration.

    Provides rotation_to_morph() for direct integration with MorphEngine.

    Usage:
        tracker = KnobTracker()
        rotations = tracker.track_rotation(session)

        # Convert to morph factors (0.0 - 1.0)
        factors = tracker.rotation_to_morph(rotations, min_angle=0, max_angle=300)

        # Apply to morph animation
        for frame, factor in enumerate(factors, start=1):
            engine.set_group_factor("knobs", factor)
    """

    def __init__(self, default_axis: str = "Z"):
        self.default_axis = default_axis
        self.rotation_tracks: Dict[str, List[RotationCurve]] = {}

    def track_rotation(
        self,
        session: "TrackingSession",
        track_name: str = "knob_rotation",
        axis: Optional[str] = None
    ) -> List[RotationCurve]:
        """
        Extract rotation curve from tracking session.

        Analyzes point track motion to extract rotation angle.

        Args:
            session: Tracking session with point tracks
            track_name: Name prefix for rotation tracks
            axis: Rotation axis (default: self.default_axis)

        Returns:
            List of RotationCurve objects per frame
        """
        if axis is None:
            axis = self.default_axis

        rotations: List[RotationCurve] = []

        # Find the center track and edge track for rotation calculation
        center_track = None
        edge_track = None

        for track in session.tracks:
            if "center" in track.name.lower():
                center_track = track
            elif "edge" in track.name.lower() or "marker" in track.name.lower():
                edge_track = track

        if center_track is None or edge_track is None:
            # Fallback: use first two tracks
            if len(session.tracks) >= 2:
                center_track = session.tracks[0]
                edge_track = session.tracks[1]

        if center_track and edge_track:
            # Calculate rotation from vector angle
            ref_angle = None

            for frame in range(session.frame_start, session.frame_end + 1):
                if frame in center_track.markers and frame in edge_track.markers:
                    center_pos = center_track.markers[frame]
                    edge_pos = edge_track.markers[frame]

                    # Calculate angle from center to edge point
                    dx = edge_pos[0] - center_pos[0]
                    dy = edge_pos[1] - center_pos[1]
                    angle = math.degrees(math.atan2(dy, dx))

                    # Use first frame as reference
                    if ref_angle is None:
                        ref_angle = angle

                    # Relative rotation from reference
                    relative_angle = angle - ref_angle

                    # Normalize to -180 to 180 range
                    while relative_angle > 180:
                        relative_angle -= 360
                    while relative_angle < -180:
                        relative_angle += 360

                    rotations.append(RotationCurve(
                        frame=frame,
                        rotation_degrees=relative_angle,
                        rotation_radians=math.radians(relative_angle),
                        axis=axis,
                    ))

        self.rotation_tracks[track_name] = rotations
        return rotations

    def rotation_to_morph(
        self,
        rotations: List[RotationCurve],
        min_angle: float = 0.0,
        max_angle: float = 300.0,
        invert: bool = False
    ) -> List[float]:
        """
        Convert rotation angles to morph factors (0.0 - 1.0).

        Maps rotation range to morph factor for MorphEngine integration.

        Args:
            rotations: List of RotationCurve objects
            min_angle: Minimum rotation angle (maps to 0.0)
            max_angle: Maximum rotation angle (maps to 1.0)
            invert: Invert the mapping (max -> 0, min -> 1)

        Returns:
            List of morph factors (0.0 to 1.0) per frame
        """
        angle_range = max_angle - min_angle
        if angle_range == 0:
            angle_range = 1.0

        morph_factors = []

        for rotation in rotations:
            # Normalize angle to 0-1 range
            factor = (rotation.rotation_degrees - min_angle) / angle_range

            # Clamp to valid range
            factor = max(0.0, min(1.0, factor))

            if invert:
                factor = 1.0 - factor

            morph_factors.append(factor)

        return morph_factors

    def create_morph_animation_data(
        self,
        rotations: List[RotationCurve],
        min_angle: float = 0.0,
        max_angle: float = 300.0,
        fps: float = 24.0
    ) -> Dict[str, Any]:
        """
        Create animation data suitable for MorphEngine keyframes.

        Args:
            rotations: List of RotationCurve objects
            min_angle: Minimum rotation angle
            max_angle: Maximum rotation angle
            fps: Frames per second

        Returns:
            Dictionary with keyframe data for MorphEngine
        """
        from lib.control_system.morphing import MorphKeyframe, EasingType

        morph_factors = self.rotation_to_morph(rotations, min_angle, max_angle)

        keyframes = []
        duration = len(rotations) / fps if rotations else 0.0

        for i, (rotation, factor) in enumerate(zip(rotations, morph_factors)):
            time = i / max(1, len(rotations) - 1) if len(rotations) > 1 else 0.0
            keyframes.append({
                "time": time,
                "value": factor,
                "frame": rotation.frame,
                "rotation_degrees": rotation.rotation_degrees,
            })

        return {
            "duration": duration,
            "fps": fps,
            "frame_count": len(rotations),
            "keyframes": keyframes,
        }


# =============================================================================
# RIGID BODY TRACKER
# =============================================================================

class RigidBodyTracker:
    """
    Solves 6-DOF transform from multiple marker tracks.

    Provides position, rotation, and scale data for object tracking.

    Usage:
        tracker = RigidBodyTracker()
        solve = tracker.track_object(session, marker_names=["m1", "m2", "m3", "m4"])
    """

    def __init__(self):
        self.solves: Dict[str, List[RigidBodySolve]] = {}

    def track_object(
        self,
        session: "TrackingSession",
        marker_names: Optional[List[str]] = None,
        reference_markers: Optional[Dict[str, Tuple[float, float, float]]] = None
    ) -> List[RigidBodySolve]:
        """
        Solve 6-DOF transform from marker tracks.

        Args:
            session: Tracking session with point tracks
            marker_names: Names of markers to use (optional)
            reference_markers: 3D reference positions for markers

        Returns:
            List of RigidBodySolve objects per frame
        """
        solves: List[RigidBodySolve] = []

        # Get marker tracks
        if marker_names:
            tracks = [t for t in session.tracks if t.name in marker_names]
        else:
            tracks = session.tracks

        if len(tracks) < 4:
            # Need at least 4 markers for 6-DOF solve
            return solves

        # Placeholder implementation - full solve requires:
        # 1. Camera calibration (focal length, principal point)
        # 2. 3D reference positions
        # 3. PnP (Perspective-n-Point) algorithm
        # For now, return identity transform with error estimate

        for frame in range(session.frame_start, session.frame_end + 1):
            # Check if all markers have data for this frame
            valid_count = sum(1 for t in tracks if frame in t.markers)

            error = 1.0 - (valid_count / len(tracks)) if tracks else 1.0

            solves.append(RigidBodySolve(
                frame=frame,
                position=(0.0, 0.0, 0.0),
                rotation=(1.0, 0.0, 0.0, 0.0),  # Identity quaternion
                scale=(1.0, 1.0, 1.0),
                error=error,
            ))

        return solves

    def get_solve_at_frame(
        self,
        solves: List[RigidBodySolve],
        frame: int
    ) -> Optional[RigidBodySolve]:
        """Get solve data for a specific frame."""
        for solve in solves:
            if solve.frame == frame:
                return solve
        return None


# =============================================================================
# FADER TRACKER
# =============================================================================

class FaderTracker:
    """
    Tracks linear fader position along a single axis.

    Provides normalized position values (0.0 - 1.0) for fader animation.

    Usage:
        tracker = FaderTracker()
        positions = tracker.track_fader(session, "fader_1")
        # positions[frame] = 0.0 (bottom) to 1.0 (top)
    """

    def __init__(self):
        self.fader_tracks: Dict[str, Dict[int, float]] = {}

    def track_fader(
        self,
        session: "TrackingSession",
        track_name: str,
        min_position: Optional[float] = None,
        max_position: Optional[float] = None
    ) -> Dict[int, float]:
        """
        Track fader position from a single point track.

        Args:
            session: Tracking session
            track_name: Name of the fader track
            min_position: Minimum Y position (auto-detected if None)
            max_position: Maximum Y position (auto-detected if None)

        Returns:
            Dictionary mapping frame to normalized position (0.0 - 1.0)
        """
        # Find the track
        fader_track = None
        for track in session.tracks:
            if track.name == track_name:
                fader_track = track
                break

        if fader_track is None:
            return {}

        # Get all Y positions
        y_positions = [pos[1] for pos in fader_track.markers.values()]

        if not y_positions:
            return {}

        # Auto-detect range
        if min_position is None:
            min_position = min(y_positions)
        if max_position is None:
            max_position = max(y_positions)

        position_range = max_position - min_position
        if position_range == 0:
            position_range = 1.0

        # Normalize positions
        positions: Dict[int, float] = {}
        for frame, pos in fader_track.markers.items():
            normalized = (pos[1] - min_position) / position_range
            positions[frame] = max(0.0, min(1.0, normalized))

        self.fader_tracks[track_name] = positions
        return positions

    def get_position_at_frame(
        self,
        track_name: str,
        frame: int
    ) -> Optional[float]:
        """Get fader position at a specific frame."""
        if track_name in self.fader_tracks:
            return self.fader_tracks[track_name].get(frame)
        return None


# =============================================================================
# UNIFIED OBJECT TRACKER
# =============================================================================

class ObjectTracker:
    """
    Unified interface for all object tracking types.

    Provides convenience methods for tracking different control surface
    elements and integrating with MorphEngine.

    Usage:
        tracker = ObjectTracker()

        # Track a knob
        anim_data = tracker.create_knob_animation(
            session,
            min_angle=0,
            max_angle=300
        )

        # Track a planar surface
        planar = tracker.track_planar(session)

        # Track a fader
        fader_pos = tracker.track_fader(session, "fader_1")
    """

    def __init__(self):
        self.planar_tracker = PlanarTracker()
        self.knob_tracker = KnobTracker()
        self.rigid_body_tracker = RigidBodyTracker()
        self.fader_tracker = FaderTracker()

    def track_planar(
        self,
        session: "TrackingSession",
        initial_corners: Optional[Tuple[
            Tuple[float, float], Tuple[float, float],
            Tuple[float, float], Tuple[float, float]
        ]] = None,
        track_name: str = "planar_surface"
    ) -> PlanarTrack:
        """Track a planar surface with 4 corners."""
        return self.planar_tracker.track_corners(
            session,
            initial_corners=initial_corners,
            track_name=track_name
        )

    def track_knob(
        self,
        session: "TrackingSession",
        track_name: str = "knob_rotation",
        axis: str = "Z"
    ) -> List[RotationCurve]:
        """Track knob rotation from tracking session."""
        return self.knob_tracker.track_rotation(
            session,
            track_name=track_name,
            axis=axis
        )

    def track_rigid_body(
        self,
        session: "TrackingSession",
        marker_names: Optional[List[str]] = None
    ) -> List[RigidBodySolve]:
        """Track 6-DOF object transform."""
        return self.rigid_body_tracker.track_object(
            session,
            marker_names=marker_names
        )

    def track_fader(
        self,
        session: "TrackingSession",
        track_name: str,
        min_position: Optional[float] = None,
        max_position: Optional[float] = None
    ) -> Dict[int, float]:
        """Track fader position."""
        return self.fader_tracker.track_fader(
            session,
            track_name=track_name,
            min_position=min_position,
            max_position=max_position
        )

    def create_knob_animation(
        self,
        session: "TrackingSession",
        min_angle: float = 0.0,
        max_angle: float = 300.0,
        fps: float = 24.0,
        axis: str = "Z"
    ) -> Dict[str, Any]:
        """
        Convenience method to create complete knob animation data.

        Combines rotation tracking with morph factor conversion
        for direct MorphEngine integration.

        Args:
            session: Tracking session
            min_angle: Minimum rotation angle
            max_angle: Maximum rotation angle
            fps: Frames per second
            axis: Rotation axis

        Returns:
            Animation data with morph factors and keyframes
        """
        rotations = self.track_knob(session, axis=axis)
        return self.knob_tracker.create_morph_animation_data(
            rotations,
            min_angle=min_angle,
            max_angle=max_angle,
            fps=fps
        )

    def export_corner_pin(
        self,
        track: PlanarTrack,
        output_path: str
    ) -> str:
        """Export planar track to Nuke corner pin format."""
        return self.planar_tracker.export_corner_pin_nuke(track, output_path)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PlanarTracker",
    "KnobTracker",
    "RigidBodyTracker",
    "FaderTracker",
    "ObjectTracker",
]
