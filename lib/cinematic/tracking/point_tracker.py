"""
Point Tracker Module - Feature Detection and KLT Optical Flow

Provides feature detection (FAST, Harris, SIFT) and KLT optical flow
tracking for automatic 2D point tracking.

Uses Blender API guards for testing outside Blender environment.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable
import math
import random

# Try to import numpy for calculations
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Try to import OpenCV for feature detection
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# Blender API guard
try:
    import bpy
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False

from .types import (
    Track,
    TrackPoint,
    TrackStatus,
    TrackingConfig,
    TrackingSession,
    FeatureDetector,
)


@dataclass
class FeaturePoint:
    """
    Detected feature point in an image.

    Attributes:
        position: (x, y) position in normalized coordinates (0-1)
        strength: Feature strength/response (0-1)
        scale: Feature scale (for multi-scale detectors)
        angle: Feature orientation angle in radians
        descriptor: Optional feature descriptor vector
    """
    position: Tuple[float, float]
    strength: float = 1.0
    scale: float = 1.0
    angle: float = 0.0
    descriptor: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": list(self.position),
            "strength": self.strength,
            "scale": self.scale,
            "angle": self.angle,
            "descriptor": self.descriptor,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FeaturePoint:
        return cls(
            position=tuple(data.get("position", (0.0, 0.0))),
            strength=data.get("strength", 1.0),
            scale=data.get("scale", 1.0),
            angle=data.get("angle", 0.0),
            descriptor=data.get("descriptor"),
        )


@dataclass
class DetectionResult:
    """
    Result of feature detection operation.

    Attributes:
        features: List of detected features
        frame: Frame number
        detection_time_ms: Time taken for detection
        method: Detection method used
    """
    features: List[FeaturePoint] = field(default_factory=list)
    frame: int = 0
    detection_time_ms: float = 0.0
    method: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "features": [f.to_dict() for f in self.features],
            "frame": self.frame,
            "detection_time_ms": self.detection_time_ms,
            "method": self.method,
        }


@dataclass
class TrackingResult:
    """
    Result of optical flow tracking operation.

    Attributes:
        tracks: Updated track data
        tracked_frames: Number of frames tracked
        lost_tracks: Number of tracks lost during tracking
        tracking_time_ms: Time taken for tracking
    """
    tracks: List[Track] = field(default_factory=list)
    tracked_frames: int = 0
    lost_tracks: int = 0
    tracking_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tracks": [t.to_dict() for t in self.tracks],
            "tracked_frames": self.tracked_frames,
            "lost_tracks": self.lost_tracks,
            "tracking_time_ms": self.tracking_time_ms,
        }


class FeatureDetectorEngine:
    """
    Feature detection engine supporting multiple algorithms.

    Provides unified interface for FAST, Harris, SIFT, ORB, and BRISK
    feature detection algorithms.
    """

    def __init__(self, config: Optional[TrackingConfig] = None):
        """
        Initialize feature detector.

        Args:
            config: Tracking configuration with detector settings
        """
        self.config = config or TrackingConfig()

    def detect(
        self,
        image: Any,  # np.ndarray or equivalent
        mask: Optional[Any] = None,
        max_features: Optional[int] = None,
    ) -> DetectionResult:
        """
        Detect features in an image.

        Args:
            image: Input image (grayscale)
            mask: Optional mask for detection region
            max_features: Override max features from config

        Returns:
            DetectionResult with detected features
        """
        import time
        start_time = time.time()

        max_features = max_features or self.config.max_features

        if HAS_OPENCV:
            features = self._detect_opencv(image, mask, max_features)
        else:
            features = self._detect_fallback(image, mask, max_features)

        detection_time = (time.time() - start_time) * 1000

        return DetectionResult(
            features=features,
            method=self.config.detector.value,
            detection_time_ms=detection_time,
        )

    def _detect_opencv(
        self,
        image: Any,
        mask: Optional[Any],
        max_features: int,
    ) -> List[FeaturePoint]:
        """Detect features using OpenCV."""
        h, w = image.shape[:2]
        features = []

        detector = self.config.detector

        if detector == FeatureDetector.FAST:
            # FAST detector
            fd = cv2.FastFeatureDetector_create(
                threshold=int(self.config.track_threshold * 100),
                nonmaxSuppression=True,
            )
            keypoints = fd.detect(image, mask)

        elif detector == FeatureDetector.HARRIS:
            # Harris corner detection via goodFeaturesToTrack
            corners = cv2.goodFeaturesToTrack(
                image,
                maxCorners=max_features,
                qualityLevel=self.config.track_threshold,
                minDistance=10,
                mask=mask,
                useHarrisDetector=True,
                k=0.04,
            )
            keypoints = [cv2.KeyPoint(x=c[0][0], y=c[0][1], size=10) for c in corners] if corners is not None else []

        elif detector == FeatureDetector.SIFT:
            # SIFT detector
            fd = cv2.SIFT_create(nfeatures=max_features)
            keypoints, descriptors = fd.detectAndCompute(image, mask)
            # Attach descriptors to features

        elif detector == FeatureDetector.ORB:
            # ORB detector
            fd = cv2.ORB_create(nfeatures=max_features)
            keypoints, descriptors = fd.detectAndCompute(image, mask)

        else:  # BRISK or default
            fd = cv2.BRISK_create()
            keypoints = fd.detect(image, mask)

        # Convert keypoints to normalized coordinates
        for kp in keypoints[:max_features]:
            x = kp.pt[0] / w
            y = kp.pt[1] / h
            features.append(FeaturePoint(
                position=(x, y),
                strength=kp.response if hasattr(kp, 'response') else 1.0,
                scale=kp.size / 100.0 if hasattr(kp, 'size') else 1.0,
                angle=kp.angle if hasattr(kp, 'angle') else 0.0,
            ))

        return features

    def _detect_fallback(
        self,
        image: Any,
        mask: Optional[Any],
        max_features: int,
    ) -> List[FeaturePoint]:
        """Fallback detection for testing without OpenCV."""
        # Generate mock features for testing
        features = []

        # Create a grid of mock feature points
        grid_size = int(math.sqrt(max_features))
        for i in range(grid_size):
            for j in range(grid_size):
                x = 0.1 + 0.8 * i / grid_size + random.uniform(-0.02, 0.02)
                y = 0.1 + 0.8 * j / grid_size + random.uniform(-0.02, 0.02)
                strength = random.uniform(0.5, 1.0)

                features.append(FeaturePoint(
                    position=(x, y),
                    strength=strength,
                    scale=random.uniform(0.8, 1.2),
                    angle=random.uniform(0, 2 * math.pi),
                ))

        return features[:max_features]


class KLTTracker:
    """
    Lucas-Kanade optical flow tracker.

    Tracks feature points across video frames using the KLT algorithm.
    """

    def __init__(self, config: Optional[TrackingConfig] = None):
        """
        Initialize KLT tracker.

        Args:
            config: Tracking configuration
        """
        self.config = config or TrackingConfig()
        self._prev_image = None
        self._prev_points = None

    def track(
        self,
        prev_image: Any,
        curr_image: Any,
        prev_points: List[Tuple[float, float]],
    ) -> Tuple[List[Tuple[float, float]], List[bool], List[float]]:
        """
        Track points from previous frame to current frame.

        Args:
            prev_image: Previous frame (grayscale)
            curr_image: Current frame (grayscale)
            prev_points: Points to track in normalized coords

        Returns:
            Tuple of (new_points, status, errors)
        """
        if HAS_OPENCV:
            return self._track_opencv(prev_image, curr_image, prev_points)
        else:
            return self._track_fallback(prev_image, curr_image, prev_points)

    def _track_opencv(
        self,
        prev_image: Any,
        curr_image: Any,
        prev_points: List[Tuple[float, float]],
    ) -> Tuple[List[Tuple[float, float]], List[bool], List[float]]:
        """Track using OpenCV's KLT implementation."""
        h, w = prev_image.shape[:2]

        # Convert normalized coords to pixel coords
        pixel_points = np.array([[p[0] * w, p[1] * h] for p in prev_points], dtype=np.float32)
        pixel_points = pixel_points.reshape(-1, 1, 2)

        # Calculate optical flow
        window_size = (self.config.flow_window_size, self.config.flow_window_size)
        max_level = self.config.flow_max_level

        new_points, status, errors = cv2.calcOpticalFlowPyrLK(
            prev_image,
            curr_image,
            pixel_points,
            None,
            winSize=window_size,
            maxLevel=max_level,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )

        # Convert back to normalized coords
        tracked_points = []
        tracked_status = []
        tracked_errors = []

        for i in range(len(prev_points)):
            if status[i][0] == 1:
                x = new_points[i][0][0] / w
                y = new_points[i][0][1] / h
                tracked_points.append((x, y))
                tracked_status.append(True)
                tracked_errors.append(errors[i][0])
            else:
                tracked_points.append(prev_points[i])
                tracked_status.append(False)
                tracked_errors.append(1.0)

        return tracked_points, tracked_status, tracked_errors

    def _track_fallback(
        self,
        prev_image: Any,
        curr_image: Any,
        prev_points: List[Tuple[float, float]],
    ) -> Tuple[List[Tuple[float, float]], List[bool], List[float]]:
        """Fallback tracking for testing without OpenCV."""
        tracked_points = []
        status = []
        errors = []

        for x, y in prev_points:
            # Simulate some motion and tracking failure
            if random.random() > 0.1:  # 90% success rate
                dx = random.uniform(-0.01, 0.01)
                dy = random.uniform(-0.01, 0.01)
                tracked_points.append((x + dx, y + dy))
                status.append(True)
                errors.append(random.uniform(0.0, 0.5))
            else:
                tracked_points.append((x, y))
                status.append(False)
                errors.append(1.0)

        return tracked_points, status, errors


class PointTracker:
    """
    Main point tracking system combining detection and tracking.

    Provides automatic feature detection and KLT tracking for
    tracking 50+ features across video frames.
    """

    def __init__(self, config: Optional[TrackingConfig] = None):
        """
        Initialize point tracker.

        Args:
            config: Tracking configuration
        """
        self.config = config or TrackingConfig()
        self.detector = FeatureDetectorEngine(self.config)
        self.klt = KLTTracker(self.config)

    def detect_features(
        self,
        frame: int,
        image: Any,
        mask: Optional[Any] = None,
        exclude_existing: Optional[List[Track]] = None,
    ) -> List[Track]:
        """
        Detect new features in a frame and create tracks.

        Args:
            frame: Frame number
            image: Image data
            mask: Optional detection mask
            exclude_existing: Existing tracks to exclude

        Returns:
            List of new tracks from detected features
        """
        # Detect features
        result = self.detector.detect(image, mask, self.config.max_features)

        # Get positions of existing tracks to avoid
        existing_positions = set()
        if exclude_existing:
            for track in exclude_existing:
                point = track.get_point_at_frame(frame)
                if point:
                    # Quantize to grid to allow nearby detection
                    pos = (round(point.position[0], 2), round(point.position[1], 2))
                    existing_positions.add(pos)

        # Create tracks from new features
        new_tracks = []
        for feature in result.features:
            # Skip if too close to existing track
            pos = (round(feature.position[0], 2), round(feature.position[1], 2))
            if pos in existing_positions:
                continue

            track = Track(
                name=f"auto_{frame}_{len(new_tracks)}",
                pattern_size=self.config.pattern_size,
                search_size=self.config.search_size,
                points=[TrackPoint(
                    frame=frame,
                    position=feature.position,
                    status=TrackStatus.OK,
                    error=0.0,
                    weight=feature.strength,
                )],
                color=self._generate_track_color(len(new_tracks)),
            )
            new_tracks.append(track)

        return new_tracks

    def track_forward(
        self,
        tracks: List[Track],
        start_frame: int,
        end_frame: int,
        get_frame_func: Callable[[int], Any],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> TrackingResult:
        """
        Track points forward through frames.

        Args:
            tracks: Tracks to track forward
            start_frame: Starting frame
            end_frame: Ending frame
            get_frame_func: Function to get frame image by frame number
            progress_callback: Progress callback (0.0-1.0)

        Returns:
            TrackingResult with updated tracks
        """
        import time
        start_time = time.time()

        total_frames = end_frame - start_frame
        lost_count = 0
        tracked_frames = 0

        # Get initial frame
        prev_image = get_frame_func(start_frame)

        for frame in range(start_frame + 1, end_frame + 1):
            curr_image = get_frame_func(frame)

            # Get points from previous frame for each track
            prev_points = []
            active_tracks = []
            for track in tracks:
                point = track.get_point_at_frame(frame - 1)
                if point and point.status == TrackStatus.OK:
                    prev_points.append(point.position)
                    active_tracks.append(track)

            if not prev_points:
                break

            # Track points
            new_points, status, errors = self.klt.track(
                prev_image, curr_image, prev_points
            )

            # Update tracks with new positions
            for i, track in enumerate(active_tracks):
                if status[i]:
                    track.points.append(TrackPoint(
                        frame=frame,
                        position=new_points[i],
                        status=TrackStatus.OK,
                        error=errors[i],
                    ))

                    # Mark as keyframe if configured
                    if (self.config.auto_keyframe and
                        frame % self.config.keyframe_interval == 0):
                        if frame not in track.is_keyframe:
                            track.is_keyframe.append(frame)
                else:
                    track.points.append(TrackPoint(
                        frame=frame,
                        position=new_points[i],
                        status=TrackStatus.MISSING,
                        error=errors[i],
                    ))
                    lost_count += 1

            tracked_frames += 1
            prev_image = curr_image

            # Progress callback
            if progress_callback:
                progress = (frame - start_frame) / total_frames
                progress_callback(progress)

        tracking_time = (time.time() - start_time) * 1000

        return TrackingResult(
            tracks=tracks,
            tracked_frames=tracked_frames,
            lost_tracks=lost_count,
            tracking_time_ms=tracking_time,
        )

    def track_backward(
        self,
        tracks: List[Track],
        start_frame: int,
        end_frame: int,
        get_frame_func: Callable[[int], Any],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> TrackingResult:
        """
        Track points backward through frames.

        Args:
            tracks: Tracks to track backward
            start_frame: Starting frame (higher number)
            end_frame: Ending frame (lower number)
            get_frame_func: Function to get frame image by frame number
            progress_callback: Progress callback (0.0-1.0)

        Returns:
            TrackingResult with updated tracks
        """
        import time
        start_time = time.time()

        total_frames = start_frame - end_frame
        lost_count = 0
        tracked_frames = 0

        prev_image = get_frame_func(start_frame)

        for frame in range(start_frame - 1, end_frame - 1, -1):
            curr_image = get_frame_func(frame)

            prev_points = []
            active_tracks = []
            for track in tracks:
                point = track.get_point_at_frame(frame + 1)
                if point and point.status == TrackStatus.OK:
                    prev_points.append(point.position)
                    active_tracks.append(track)

            if not prev_points:
                break

            new_points, status, errors = self.klt.track(
                prev_image, curr_image, prev_points
            )

            for i, track in enumerate(active_tracks):
                if status[i]:
                    track.points.insert(0, TrackPoint(  # Insert at start for backward
                        frame=frame,
                        position=new_points[i],
                        status=TrackStatus.OK,
                        error=errors[i],
                    ))
                else:
                    track.points.insert(0, TrackPoint(
                        frame=frame,
                        position=new_points[i],
                        status=TrackStatus.MISSING,
                        error=errors[i],
                    ))
                    lost_count += 1

            tracked_frames += 1
            prev_image = curr_image

            if progress_callback:
                progress = (start_frame - frame) / total_frames
                progress_callback(progress)

        tracking_time = (time.time() - start_time) * 1000

        return TrackingResult(
            tracks=tracks,
            tracked_frames=tracked_frames,
            lost_tracks=lost_count,
            tracking_time_ms=tracking_time,
        )

    def auto_track(
        self,
        session: TrackingSession,
        get_frame_func: Callable[[int], Any],
        start_frame: Optional[int] = None,
        end_frame: Optional[int] = None,
        min_tracks: Optional[int] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> TrackingResult:
        """
        Automatically detect and track features through session.

        Detects features in start frame and tracks them through
        the entire frame range, adding new tracks as needed.

        Args:
            session: Tracking session
            get_frame_func: Function to get frame image by frame number
            start_frame: Start frame (uses session.footage if None)
            end_frame: End frame (uses session.footure if None)
            min_tracks: Minimum active tracks at any time
            progress_callback: Progress callback (progress, stage_name)

        Returns:
            TrackingResult with all tracks
        """
        # Get frame range
        if start_frame is None:
            start_frame = session.footage.frame_start
        if end_frame is None:
            end_frame = session.footage.frame_end
        if min_tracks is None:
            min_tracks = self.config.min_features

        # Detect initial features
        if progress_callback:
            progress_callback(0.0, "detecting")

        initial_image = get_frame_func(start_frame)
        tracks = self.detect_features(start_frame, initial_image)

        # Track forward with feature replenishment
        all_tracks = list(tracks)

        for frame in range(start_frame + 1, end_frame + 1):
            # Count active tracks
            active_count = sum(
                1 for t in all_tracks
                if t.get_point_at_frame(frame - 1) and
                t.get_point_at_frame(frame - 1).status == TrackStatus.OK
            )

            # Replenish if below minimum
            if active_count < min_tracks:
                image = get_frame_func(frame)
                new_tracks = self.detect_features(
                    frame, image, exclude_existing=all_tracks
                )
                all_tracks.extend(new_tracks)

            # Track existing tracks
            if frame > start_frame:
                prev_image = get_frame_func(frame - 1)
                curr_image = get_frame_func(frame)

                for track in all_tracks:
                    point = track.get_point_at_frame(frame - 1)
                    if point and point.status == TrackStatus.OK:
                        # Track single point
                        new_points, status, errors = self.klt.track(
                            prev_image, curr_image, [point.position]
                        )

                        track.points.append(TrackPoint(
                            frame=frame,
                            position=new_points[0],
                            status=TrackStatus.OK if status[0] else TrackStatus.MISSING,
                            error=errors[0],
                        ))

            if progress_callback:
                progress = (frame - start_frame) / (end_frame - start_frame)
                progress_callback(progress, "tracking")

        return TrackingResult(
            tracks=all_tracks,
            tracked_frames=end_frame - start_frame,
        )

    def _generate_track_color(self, index: int) -> Tuple[float, float, float]:
        """Generate a unique color for a track based on index."""
        # Use HSV color wheel with golden ratio spacing
        hue = (index * 0.618033988749895) % 1.0

        # Convert HSV to RGB (simplified)
        h = hue * 6
        c = 1.0
        x = 1 - abs(h % 2 - 1)

        if h < 1:
            r, g, b = c, x, 0
        elif h < 2:
            r, g, b = x, c, 0
        elif h < 3:
            r, g, b = 0, c, x
        elif h < 4:
            r, g, b = 0, x, c
        elif h < 5:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x

        return (r, g, b)

    def visualize_tracks(
        self,
        tracks: List[Track],
        frame: int,
        image: Any,
        show_trails: bool = True,
        trail_length: int = 10,
    ) -> Any:
        """
        Draw track visualization on an image.

        Args:
            tracks: Tracks to visualize
            frame: Current frame number
            image: Image to draw on
            show_trails: Show motion trails
            trail_length: Number of frames for trail

        Returns:
            Image with visualization overlay
        """
        if HAS_OPENCV:
            return self._visualize_opencv(tracks, frame, image, show_trails, trail_length)
        else:
            return image  # Return unchanged without OpenCV

    def _visualize_opencv(
        self,
        tracks: List[Track],
        frame: int,
        image: Any,
        show_trails: bool,
        trail_length: int,
    ) -> Any:
        """Visualize tracks using OpenCV."""
        h, w = image.shape[:2]
        vis = image.copy()

        if len(vis.shape) == 2:
            vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)

        for track in tracks:
            point = track.get_point_at_frame(frame)
            if not point:
                continue

            x = int(point.position[0] * w)
            y = int(point.position[1] * h)

            # Draw trail
            if show_trails:
                start_frame = max(1, frame - trail_length)
                for f in range(start_frame, frame):
                    prev_point = track.get_point_at_frame(f)
                    if prev_point:
                        px = int(prev_point.position[0] * w)
                        py = int(prev_point.position[1] * h)
                        alpha = (f - start_frame) / trail_length
                        color = tuple(int(c * 255 * alpha) for c in track.color)
                        cv2.line(vis, (px, py), (x, y), color, 1)

            # Draw marker
            color = tuple(int(c * 255) for c in track.color)
            if point.status == TrackStatus.OK:
                cv2.circle(vis, (x, y), 4, color, -1)
            elif point.status == TrackStatus.MISSING:
                cv2.circle(vis, (x, y), 4, (128, 128, 128), 1)
            else:
                cv2.circle(vis, (x, y), 4, (0, 0, 255), 1)

        return vis
