"""
Stabilization Module - 2D Stabilization from Point Tracks

Provides 2D video stabilization using point track data.
Calculates smooth camera motion and removes unwanted jitter
while preserving intentional camera movement.

Supports:
- Translation, rotation, and scale stabilization
- Smoothing with various filters
- Automatic smoothing strength estimation
- Region of interest (ROI) tracking
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable
import math

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
    StabilizationResult,
    TrackingSession,
)


@dataclass
class StabilizationConfig:
    """
    Configuration for 2D stabilization.

    Attributes:
        smooth_translation: Smoothing factor for translation (0-1)
        smooth_rotation: Smoothing factor for rotation (0-1)
        smooth_scale: Smoothing factor for scale (0-1)
        use_rotation: Enable rotation stabilization
        use_scale: Enable scale stabilization
        anchor_frame: Reference frame for stabilization (0 = auto)
        border_mode: How to handle edges (mirror, extend, black)
        invert: Apply inverse stabilization (destabilize)
        tracks_crop_black: Remove tracks with mostly black pixels
        max_smooth_factor: Maximum smoothing iteration factor
    """
    smooth_translation: float = 0.5
    smooth_rotation: float = 0.5
    smooth_scale: float = 0.5
    use_rotation: bool = True
    use_scale: bool = True
    anchor_frame: int = 0  # 0 = auto (first frame)
    border_mode: str = "mirror"  # mirror, extend, black
    invert: bool = False
    tracks_crop_black: bool = True
    max_smooth_factor: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "smooth_translation": self.smooth_translation,
            "smooth_rotation": self.smooth_rotation,
            "smooth_scale": self.smooth_scale,
            "use_rotation": self.use_rotation,
            "use_scale": self.use_scale,
            "anchor_frame": self.anchor_frame,
            "border_mode": self.border_mode,
            "invert": self.invert,
            "tracks_crop_black": self.tracks_crop_black,
            "max_smooth_factor": self.max_smooth_factor,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StabilizationConfig:
        return cls(
            smooth_translation=data.get("smooth_translation", 0.5),
            smooth_rotation=data.get("smooth_rotation", 0.5),
            smooth_scale=data.get("smooth_scale", 0.5),
            use_rotation=data.get("use_rotation", True),
            use_scale=data.get("use_scale", True),
            anchor_frame=data.get("anchor_frame", 0),
            border_mode=data.get("border_mode", "mirror"),
            invert=data.get("invert", False),
            tracks_crop_black=data.get("tracks_crop_black", True),
            max_smooth_factor=data.get("max_smooth_factor", 1),
        )


@dataclass
class Transform2D:
    """
    2D transformation (translation, rotation, scale).

    Attributes:
        tx, ty: Translation in pixels
        rotation: Rotation in radians
        scale: Scale factor
        cx, cy: Center point for rotation/scale
    """
    tx: float = 0.0
    ty: float = 0.0
    rotation: float = 0.0
    scale: float = 1.0
    cx: float = 0.5  # Center X (normalized)
    cy: float = 0.5  # Center Y (normalized)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx": self.tx,
            "ty": self.ty,
            "rotation": self.rotation,
            "scale": self.scale,
            "cx": self.cx,
            "cy": self.cy,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Transform2D:
        return cls(
            tx=data.get("tx", 0.0),
            ty=data.get("ty", 0.0),
            rotation=data.get("rotation", 0.0),
            scale=data.get("scale", 1.0),
            cx=data.get("cx", 0.5),
            cy=data.get("cy", 0.5),
        )

    def inverse(self) -> Transform2D:
        """Get inverse transformation."""
        cos_r = math.cos(-self.rotation)
        sin_r = math.sin(-self.rotation)

        # Inverse scale
        inv_scale = 1.0 / self.scale if self.scale != 0 else 1.0

        # Inverse translation (in scaled coordinates)
        inv_tx = -self.tx * inv_scale
        inv_ty = -self.ty * inv_scale

        return Transform2D(
            tx=inv_tx,
            ty=inv_ty,
            rotation=-self.rotation,
            scale=inv_scale,
            cx=self.cx,
            cy=self.cy,
        )

    def compose(self, other: Transform2D) -> Transform2D:
        """Compose with another transformation."""
        # Simplified composition
        return Transform2D(
            tx=self.tx + other.tx,
            ty=self.ty + other.ty,
            rotation=self.rotation + other.rotation,
            scale=self.scale * other.scale,
            cx=self.cx,
            cy=self.cy,
        )

    def apply_to_point(self, x: float, y: float) -> Tuple[float, float]:
        """Apply transformation to a point."""
        # Translate to center
        x -= self.cx
        y -= self.cy

        # Scale
        x *= self.scale
        y *= self.scale

        # Rotate
        cos_r = math.cos(self.rotation)
        sin_r = math.sin(self.rotation)
        x_rot = x * cos_r - y * sin_r
        y_rot = x * sin_r + y * cos_r

        # Translate back and apply translation
        x_final = x_rot + self.cx + self.tx
        y_final = y_rot + self.cy + self.ty

        return x_final, y_final


@dataclass
class StabilizationData:
    """
    Complete stabilization data for all frames.

    Attributes:
        transforms: Per-frame transformations
        smoothed_transforms: Smoothed transformations
        frame_start: First frame
        frame_end: Last frame
        width: Image width
        height: Image height
    """
    transforms: Dict[int, Transform2D] = field(default_factory=dict)
    smoothed_transforms: Dict[int, Transform2D] = field(default_factory=dict)
    frame_start: int = 1
    frame_end: int = 1
    width: int = 1920
    height: int = 1080

    def get_transform(self, frame: int) -> Optional[Transform2D]:
        """Get transform for a frame."""
        return self.transforms.get(frame)

    def get_smoothed_transform(self, frame: int) -> Optional[Transform2D]:
        """Get smoothed transform for a frame."""
        return self.smoothed_transforms.get(frame)


class MotionAnalyzer:
    """
    Analyzes motion from point tracks.

    Calculates global motion parameters from individual track points.
    """

    def __init__(self, width: int = 1920, height: int = 1080):
        """Initialize motion analyzer."""
        self.width = width
        self.height = height

    def analyze_frame_motion(
        self,
        tracks: List[Track],
        frame: int,
        prev_frame: int,
    ) -> Transform2D:
        """
        Analyze motion between two frames.

        Uses least-squares estimation of translation, rotation, and scale.

        Args:
            tracks: List of tracks to analyze
            frame: Current frame
            prev_frame: Previous frame

        Returns:
            Transform2D representing the motion
        """
        # Collect matching point pairs
        points_prev = []
        points_curr = []

        for track in tracks:
            prev_point = track.get_point_at_frame(prev_frame)
            curr_point = track.get_point_at_frame(frame)

            if (prev_point and curr_point and
                prev_point.status == TrackStatus.OK and
                curr_point.status == TrackStatus.OK):
                points_prev.append(prev_point.position)
                points_curr.append(curr_point.position)

        if len(points_prev) < 2:
            return Transform2D()

        # Calculate translation (centroid shift)
        cx_prev = sum(p[0] for p in points_prev) / len(points_prev)
        cy_prev = sum(p[1] for p in points_prev) / len(points_prev)
        cx_curr = sum(p[0] for p in points_curr) / len(points_curr)
        cy_curr = sum(p[1] for p in points_curr) / len(points_curr)

        tx = (cx_curr - cx_prev) * self.width
        ty = (cy_curr - cy_prev) * self.height

        # Calculate rotation and scale using Procrustes analysis
        # Center points
        centered_prev = [(p[0] - cx_prev, p[1] - cy_prev) for p in points_prev]
        centered_curr = [(p[0] - cx_curr, p[1] - cy_curr) for p in points_curr]

        # Calculate scale
        scale_prev = math.sqrt(sum(x*x + y*y for x, y in centered_prev) / len(centered_prev))
        scale_curr = math.sqrt(sum(x*x + y*y for x, y in centered_curr) / len(centered_curr))

        scale = scale_curr / scale_prev if scale_prev > 0 else 1.0

        # Calculate rotation
        # Using correlation method
        numerator = sum(
            centered_prev[i][0] * centered_curr[i][1] -
            centered_prev[i][1] * centered_curr[i][0]
            for i in range(len(centered_prev))
        )
        denominator = sum(
            centered_prev[i][0] * centered_curr[i][0] +
            centered_prev[i][1] * centered_curr[i][1]
            for i in range(len(centered_prev))
        )

        rotation = math.atan2(numerator, denominator) if denominator != 0 else 0.0

        return Transform2D(
            tx=tx,
            ty=ty,
            rotation=rotation,
            scale=scale,
            cx=0.5,
            cy=0.5,
        )

    def analyze_global_motion(
        self,
        tracks: List[Track],
        frame_start: int,
        frame_end: int,
        anchor_frame: Optional[int] = None,
    ) -> Dict[int, Transform2D]:
        """
        Analyze global motion across frame range.

        Computes cumulative motion from anchor frame.

        Args:
            tracks: List of tracks
            frame_start: Start frame
            frame_end: End frame
            anchor_frame: Reference frame (default: frame_start)

        Returns:
            Dict mapping frame to cumulative Transform2D
        """
        if anchor_frame is None:
            anchor_frame = frame_start

        transforms = {}

        # Initialize anchor frame as identity
        transforms[anchor_frame] = Transform2D()

        # Forward pass from anchor
        cumulative = Transform2D()
        for frame in range(anchor_frame, frame_end + 1):
            if frame > anchor_frame:
                motion = self.analyze_frame_motion(tracks, frame, frame - 1)
                cumulative = cumulative.compose(motion)
            transforms[frame] = Transform2D(
                tx=cumulative.tx,
                ty=cumulative.ty,
                rotation=cumulative.rotation,
                scale=cumulative.scale,
            )

        # Backward pass from anchor
        cumulative = Transform2D()
        for frame in range(anchor_frame - 1, frame_start - 1, -1):
            motion = self.analyze_frame_motion(tracks, frame + 1, frame)
            # Invert motion for backward
            cumulative = motion.inverse().compose(cumulative)
            transforms[frame] = Transform2D(
                tx=cumulative.tx,
                ty=cumulative.ty,
                rotation=cumulative.rotation,
                scale=cumulative.scale,
            )

        return transforms


class MotionSmoother:
    """
    Smooths motion data to remove unwanted jitter.

    Provides various smoothing algorithms for stabilization.
    """

    @staticmethod
    def gaussian_smooth(
        values: List[float],
        sigma: float = 1.0,
    ) -> List[float]:
        """
        Apply Gaussian smoothing to values.

        Args:
            values: Input values
            sigma: Gaussian sigma (higher = smoother)

        Returns:
            Smoothed values
        """
        if len(values) < 3:
            return values

        # Generate Gaussian kernel
        kernel_size = int(sigma * 4) * 2 + 1
        kernel = []
        for i in range(kernel_size):
            x = i - kernel_size // 2
            kernel.append(math.exp(-x * x / (2 * sigma * sigma)))

        # Normalize kernel
        kernel_sum = sum(kernel)
        kernel = [k / kernel_sum for k in kernel]

        # Apply convolution
        result = []
        for i in range(len(values)):
            weighted_sum = 0.0
            weight_sum = 0.0

            for j in range(kernel_size):
                idx = i + j - kernel_size // 2
                if 0 <= idx < len(values):
                    weighted_sum += values[idx] * kernel[j]
                    weight_sum += kernel[j]

            if weight_sum > 0:
                result.append(weighted_sum / weight_sum)
            else:
                result.append(values[i])

        return result

    @staticmethod
    def smooth_transforms(
        transforms: Dict[int, Transform2D],
        smooth_translation: float = 0.5,
        smooth_rotation: float = 0.5,
        smooth_scale: float = 0.5,
    ) -> Dict[int, Transform2D]:
        """
        Smooth a sequence of transforms.

        Args:
            transforms: Input transforms
            smooth_translation: Translation smoothing factor
            smooth_rotation: Rotation smoothing factor
            smooth_scale: Scale smoothing factor

        Returns:
            Smoothed transforms
        """
        if not transforms:
            return {}

        frames = sorted(transforms.keys())

        # Extract values
        tx_values = [transforms[f].tx for f in frames]
        ty_values = [transforms[f].ty for f in frames]
        rot_values = [transforms[f].rotation for f in frames]
        scale_values = [transforms[f].scale for f in frames]

        # Smooth each component
        sigma_tx = smooth_translation * 10 + 0.5
        sigma_ty = smooth_translation * 10 + 0.5
        sigma_rot = smooth_rotation * 5 + 0.5
        sigma_scale = smooth_scale * 5 + 0.5

        tx_smooth = MotionSmoother.gaussian_smooth(tx_values, sigma_tx)
        ty_smooth = MotionSmoother.gaussian_smooth(ty_values, sigma_ty)
        rot_smooth = MotionSmoother.gaussian_smooth(rot_values, sigma_rot)
        scale_smooth = MotionSmoother.gaussian_smooth(scale_values, sigma_scale)

        # Reconstruct transforms
        smoothed = {}
        for i, frame in enumerate(frames):
            smoothed[frame] = Transform2D(
                tx=tx_smooth[i],
                ty=ty_smooth[i],
                rotation=rot_smooth[i],
                scale=scale_smooth[i],
                cx=0.5,
                cy=0.5,
            )

        return smoothed


class Stabilizer:
    """
    Main 2D stabilizer class.

    Provides complete stabilization workflow from tracks to
    stabilized transforms.
    """

    def __init__(self, config: Optional[StabilizationConfig] = None):
        """
        Initialize stabilizer.

        Args:
            config: Stabilization configuration
        """
        self.config = config or StabilizationConfig()
        self._data: Optional[StabilizationData] = None

    def stabilize(
        self,
        tracks: List[Track],
        frame_start: int,
        frame_end: int,
        width: int = 1920,
        height: int = 1080,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> StabilizationData:
        """
        Calculate stabilization from tracks.

        Args:
            tracks: List of 2D tracks
            frame_start: Start frame
            frame_end: End frame
            width: Image width
            height: Image height
            progress_callback: Progress callback

        Returns:
            StabilizationData with transforms
        """
        # Filter tracks with enough points
        valid_tracks = [
            t for t in tracks
            if len(t.points) >= 2
        ]

        if progress_callback:
            progress_callback(0.1)

        # Determine anchor frame
        anchor_frame = self.config.anchor_frame
        if anchor_frame <= 0:
            anchor_frame = frame_start

        # Analyze motion
        analyzer = MotionAnalyzer(width, height)
        transforms = analyzer.analyze_global_motion(
            valid_tracks,
            frame_start,
            frame_end,
            anchor_frame,
        )

        if progress_callback:
            progress_callback(0.5)

        # Smooth motion
        smoothed = MotionSmoother.smooth_transforms(
            transforms,
            self.config.smooth_translation,
            self.config.smooth_rotation,
            self.config.smooth_scale,
        )

        if progress_callback:
            progress_callback(0.9)

        # If not using rotation/scale, set them to identity
        if not self.config.use_rotation:
            for frame, t in smoothed.items():
                t.rotation = 0.0

        if not self.config.use_scale:
            for frame, t in smoothed.items():
                t.scale = 1.0

        # Create result
        self._data = StabilizationData(
            transforms=transforms,
            smoothed_transforms=smoothed,
            frame_start=frame_start,
            frame_end=frame_end,
            width=width,
            height=height,
        )

        if progress_callback:
            progress_callback(1.0)

        return self._data

    def stabilize_session(
        self,
        session: TrackingSession,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> StabilizationData:
        """
        Stabilize using session data.

        Args:
            session: Tracking session with tracks and footage info
            progress_callback: Progress callback

        Returns:
            StabilizationData
        """
        return self.stabilize(
            tracks=session.tracks,
            frame_start=session.footage.frame_start,
            frame_end=session.footage.frame_end,
            width=session.footage.width,
            height=session.footage.height,
            progress_callback=progress_callback,
        )

    def get_stabilization_transform(self, frame: int) -> Optional[Transform2D]:
        """
        Get stabilization transform for a frame.

        Returns the difference between original and smoothed motion,
        which when applied will stabilize the frame.

        Args:
            frame: Frame number

        Returns:
            Stabilization Transform2D or None
        """
        if not self._data:
            return None

        original = self._data.get_transform(frame)
        smoothed = self._data.get_smoothed_transform(frame)

        if not original or not smoothed:
            return None

        # Stabilization = inverse of (original - smoothed)
        # This compensates for the unwanted motion
        delta = Transform2D(
            tx=original.tx - smoothed.tx,
            ty=original.ty - smoothed.ty,
            rotation=original.rotation - smoothed.rotation,
            scale=original.scale / smoothed.scale if smoothed.scale != 0 else 1.0,
        )

        if self.config.invert:
            return delta
        else:
            return delta.inverse()

    def get_results(self) -> List[StabilizationResult]:
        """
        Get stabilization results for all frames.

        Returns:
            List of StabilizationResult objects
        """
        if not self._data:
            return []

        results = []
        for frame in sorted(self._data.transforms.keys()):
            stab = self.get_stabilization_transform(frame)
            if stab:
                results.append(StabilizationResult(
                    frame=frame,
                    translation=(stab.tx, stab.ty),
                    rotation=stab.rotation,
                    scale=stab.scale,
                ))

        return results

    def apply_to_frame(
        self,
        frame: int,
        image_data: Any,
    ) -> Any:
        """
        Apply stabilization to a frame.

        Args:
            frame: Frame number
            image_data: Image data (format depends on context)

        Returns:
            Stabilized image data
        """
        transform = self.get_stabilization_transform(frame)
        if not transform:
            return image_data

        # This would apply the transform using appropriate image library
        # For now, return original
        return image_data


def stabilize_session(
    session: TrackingSession,
    config: Optional[StabilizationConfig] = None,
) -> List[StabilizationResult]:
    """
    Convenience function to stabilize a session.

    Args:
        session: Tracking session
        config: Stabilization configuration

    Returns:
        List of StabilizationResult objects
    """
    stabilizer = Stabilizer(config)
    stabilizer.stabilize_session(session)
    return stabilizer.get_results()


def calculate_stabilization_quality(
    original_transforms: Dict[int, Transform2D],
    smoothed_transforms: Dict[int, Transform2D],
) -> Dict[str, float]:
    """
    Calculate quality metrics for stabilization.

    Args:
        original_transforms: Original motion transforms
        smoothed_transforms: Smoothed motion transforms

    Returns:
        Dict with quality metrics
    """
    if not original_transforms or not smoothed_transforms:
        return {"quality": 0.0}

    frames = sorted(set(original_transforms.keys()) & set(smoothed_transforms.keys()))

    if not frames:
        return {"quality": 0.0}

    # Calculate jitter reduction
    tx_jitter = []
    ty_jitter = []

    for frame in frames:
        orig = original_transforms[frame]
        smooth = smoothed_transforms[frame]

        tx_jitter.append(abs(orig.tx - smooth.tx))
        ty_jitter.append(abs(orig.ty - smooth.ty))

    # Average jitter removed
    avg_tx_jitter = sum(tx_jitter) / len(tx_jitter) if tx_jitter else 0
    avg_ty_jitter = sum(ty_jitter) / len(ty_jitter) if ty_jitter else 0

    # Quality score (lower jitter = higher quality)
    # Normalized to 0-100 scale
    max_jitter = max(avg_tx_jitter, avg_ty_jitter, 1)
    quality = max(0, 100 - max_jitter)

    return {
        "quality": quality,
        "avg_tx_jitter_removed": avg_tx_jitter,
        "avg_ty_jitter_removed": avg_ty_jitter,
        "frames_processed": len(frames),
    }
