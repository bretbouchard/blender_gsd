"""
Track Quality Module

Provides track quality analysis and filtering for motion tracking.
Analyzes correlation, track length, and error metrics to identify
problematic tracks that should be cleaned before camera solving.

Key Functions:
- analyze_track_quality: Generate comprehensive quality report
- clean_low_quality_tracks: Remove tracks using Blender's clean_tracks operator
- filter_tracks_by_correlation: Disable tracks below correlation threshold
- get_track_quality_report: Generate human-readable quality report
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .context import tracking_context


@dataclass
class QualityMetrics:
    """
    Quality metrics for a single track.

    Attributes:
        name: Track name
        marker_count: Number of markers
        track_length_percent: Length as percentage of clip duration
        average_correlation: Average correlation across markers
        average_error: Average tracking error in pixels
        is_short: Whether track is considered short
        is_high_error: Whether track has high error
    """
    name: str
    marker_count: int = 0
    track_length_percent: float = 0.0
    average_correlation: float = 1.0
    average_error: float = 0.0
    is_short: bool = False
    is_high_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "marker_count": self.marker_count,
            "track_length_percent": self.track_length_percent,
            "average_correlation": self.average_correlation,
            "average_error": self.average_error,
            "is_short": self.is_short,
            "is_high_error": self.is_high_error,
        }


def analyze_track_quality(clip) -> Dict[str, Any]:
    """
    Generate quality report for all tracks.

    Analyzes correlation, track length, and error metrics.

    Args:
        clip: MovieClip with tracks

    Returns:
        Dict with quality metrics:
        - total_tracks: Number of tracks
        - active_tracks: Number of enabled tracks
        - average_markers: Average markers per track
        - low_correlation_tracks: List of track names with low correlation
        - short_tracks: List of tracks with few markers
        - high_error_tracks: List of tracks with high average error
        - track_metrics: List of QualityMetrics for each track
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    report = {
        "total_tracks": len(clip.tracking.tracks),
        "active_tracks": 0,
        "average_markers": 0.0,
        "low_correlation_tracks": [],
        "short_tracks": [],
        "high_error_tracks": [],
        "track_metrics": [],
    }

    total_markers = 0
    clip_duration = clip.frame_duration
    metrics_list = []

    for track in clip.tracking.tracks:
        if track.mute:
            continue

        report["active_tracks"] += 1
        marker_count = len([m for m in track.markers if not m.mute])
        total_markers += marker_count

        # Calculate track length percentage
        track_length_pct = (marker_count / clip_duration * 100) if clip_duration > 0 else 0

        # Check correlation (track.correlation_min is the threshold, not average)
        # For actual correlation, we'd need to check individual markers
        correlation = track.correlation_min

        # Check average error (if available)
        avg_error = 0.0
        if hasattr(track, "average_error"):
            avg_error = track.average_error

        # Create metrics
        metrics = QualityMetrics(
            name=track.name,
            marker_count=marker_count,
            track_length_percent=track_length_pct,
            average_correlation=correlation,
            average_error=avg_error,
            is_short=marker_count < clip_duration * 0.3,
            is_high_error=avg_error > 2.0,
        )
        metrics_list.append(metrics)

        # Check track length relative to clip duration
        if marker_count < clip_duration * 0.3:
            report["short_tracks"].append(track.name)

        # Check for low correlation tracks
        if correlation < 0.6:
            report["low_correlation_tracks"].append(track.name)

        # Check average error (if available)
        if avg_error > 2.0:
            report["high_error_tracks"].append({
                "name": track.name,
                "error": avg_error,
            })

    if report["active_tracks"] > 0:
        report["average_markers"] = total_markers / report["active_tracks"]

    report["track_metrics"] = metrics_list

    return report


def clean_low_quality_tracks(
    clip,
    frames: int = 5,
    error: float = 2.0,
    action: str = "DELETE",
) -> int:
    """
    Remove tracks with poor quality using Blender's clean_tracks operator.

    Args:
        clip: MovieClip with tracks
        frames: Remove tracks shorter than N frames
        error: Remove tracks with reprojection error > N pixels
        action: DELETE or DELETE_SEGMENTS

    Returns:
        Number of tracks removed
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    track_count_before = len(clip.tracking.tracks)

    try:
        with tracking_context(clip) as ctx:
            bpy.ops.clip.clean_tracks(
                ctx,
                frames=frames,
                error=error,
                action=action,
            )
    except RuntimeError:
        # Context setup failed, return 0
        return 0

    return track_count_before - len(clip.tracking.tracks)


def filter_tracks_by_correlation(
    clip,
    min_correlation: float = 0.6,
) -> int:
    """
    Disable tracks below correlation threshold.

    Args:
        clip: MovieClip with tracks
        min_correlation: Minimum correlation threshold (0-1)

    Returns:
        Number of tracks disabled
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    disabled_count = 0

    for track in clip.tracking.tracks:
        # Skip already muted tracks
        if track.mute:
            continue

        # Calculate average correlation across markers
        total_correlation = 0
        marker_count = 0

        for marker in track.markers:
            if not marker.mute:
                marker_count += 1
                # Note: marker.correlation may not be available in all Blender versions
                if hasattr(marker, "correlation"):
                    total_correlation += marker.correlation

        if marker_count > 0:
            # Use track's correlation_min if marker correlation not available
            if total_correlation > 0:
                avg_correlation = total_correlation / marker_count
            else:
                avg_correlation = track.correlation_min

            if avg_correlation < min_correlation:
                track.mute = True
                disabled_count += 1

    return disabled_count


def filter_short_tracks(
    clip,
    min_frames: int = 5,
) -> int:
    """
    Disable tracks with fewer than minimum frames.

    Args:
        clip: MovieClip with tracks
        min_frames: Minimum number of frames for a valid track

    Returns:
        Number of tracks disabled
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    disabled_count = 0

    for track in clip.tracking.tracks:
        if track.mute:
            continue

        # Count active markers
        marker_count = len([m for m in track.markers if not m.mute])

        if marker_count < min_frames:
            track.mute = True
            disabled_count += 1

    return disabled_count


def get_track_quality_report(clip) -> str:
    """
    Generate human-readable quality report.

    Args:
        clip: MovieClip with tracks

    Returns:
        Formatted string report
    """
    data = analyze_track_quality(clip)

    lines = [
        "Track Quality Report",
        "=" * 40,
        f"Total Tracks: {data['total_tracks']}",
        f"Active Tracks: {data['active_tracks']}",
        f"Average Markers: {data['average_markers']:.1f}",
        "",
    ]

    if data["short_tracks"]:
        lines.append(f"Short Tracks ({len(data['short_tracks'])}):")
        for name in data["short_tracks"][:10]:
            lines.append(f"  - {name}")
        if len(data["short_tracks"]) > 10:
            lines.append(f"  ... and {len(data['short_tracks']) - 10} more")
        lines.append("")

    if data["low_correlation_tracks"]:
        lines.append(f"Low Correlation Tracks ({len(data['low_correlation_tracks'])}):")
        for name in data["low_correlation_tracks"][:10]:
            lines.append(f"  - {name}")
        if len(data["low_correlation_tracks"]) > 10:
            lines.append(f"  ... and {len(data['low_correlation_tracks']) - 10} more")
        lines.append("")

    if data["high_error_tracks"]:
        lines.append(f"High Error Tracks ({len(data['high_error_tracks'])}):")
        for item in data["high_error_tracks"][:10]:
            lines.append(f"  - {item['name']}: {item['error']:.2f}px")
        if len(data["high_error_tracks"]) > 10:
            lines.append(f"  ... and {len(data['high_error_tracks']) - 10} more")

    return "\n".join(lines)


def get_tracks_by_quality(clip) -> Dict[str, List[str]]:
    """
    Categorize tracks by quality level.

    Args:
        clip: MovieClip with tracks

    Returns:
        Dict with 'good', 'acceptable', 'poor' track name lists
    """
    if not BLENDER_AVAILABLE:
        return {"good": [], "acceptable": [], "poor": []}

    clip_duration = clip.frame_duration

    result = {
        "good": [],
        "acceptable": [],
        "poor": [],
    }

    for track in clip.tracking.tracks:
        if track.mute:
            continue

        marker_count = len([m for m in track.markers if not m.mute])
        track_length_pct = (marker_count / clip_duration) if clip_duration > 0 else 0

        # Quality criteria
        is_long = track_length_pct > 0.7
        is_medium = track_length_pct > 0.4
        has_good_correlation = track.correlation_min >= 0.7

        if is_long and has_good_correlation:
            result["good"].append(track.name)
        elif is_medium and track.correlation_min >= 0.5:
            result["acceptable"].append(track.name)
        else:
            result["poor"].append(track.name)

    return result


def get_solve_readiness_score(clip) -> float:
    """
    Calculate a solve readiness score (0-100).

    Higher scores indicate better tracking quality for solving.

    Args:
        clip: MovieClip with tracks

    Returns:
        Score from 0-100
    """
    if not BLENDER_AVAILABLE:
        return 0.0

    report = analyze_track_quality(clip)

    if report["active_tracks"] == 0:
        return 0.0

    score = 100.0

    # Penalize for low track count
    if report["active_tracks"] < 8:
        score -= (8 - report["active_tracks"]) * 10

    # Penalize for short tracks
    short_ratio = len(report["short_tracks"]) / report["active_tracks"]
    score -= short_ratio * 30

    # Penalize for high error tracks
    if report["high_error_tracks"]:
        error_ratio = len(report["high_error_tracks"]) / report["active_tracks"]
        score -= error_ratio * 20

    # Penalize for low correlation tracks
    if report["low_correlation_tracks"]:
        corr_ratio = len(report["low_correlation_tracks"]) / report["active_tracks"]
        score -= corr_ratio * 15

    return max(0.0, min(100.0, score))


def recommend_cleaning_action(clip) -> List[str]:
    """
    Recommend cleaning actions based on track analysis.

    Args:
        clip: MovieClip with tracks

    Returns:
        List of recommended action strings
    """
    if not BLENDER_AVAILABLE:
        return ["Blender not available"]

    report = analyze_track_quality(clip)
    recommendations = []

    # Check track count
    if report["active_tracks"] < 8:
        recommendations.append(
            f"Need more tracks: {report['active_tracks']} active, recommend 8+ for stable solve"
        )

    # Check for short tracks
    if report["short_tracks"]:
        pct = len(report["short_tracks"]) / report["active_tracks"] * 100
        if pct > 30:
            recommendations.append(
                f"Many short tracks ({pct:.0f}%): consider running clean_tracks with frames=5"
            )

    # Check for high error tracks
    if report["high_error_tracks"]:
        recommendations.append(
            f"High error tracks detected: consider running clean_tracks with error=2.0"
        )

    # Check for low correlation
    if report["low_correlation_tracks"]:
        recommendations.append(
            f"Low correlation tracks: consider running filter_tracks_by_correlation with min_correlation=0.6"
        )

    if not recommendations:
        recommendations.append("Track quality looks good for solving")

    return recommendations


__all__ = [
    "QualityMetrics",
    "analyze_track_quality",
    "clean_low_quality_tracks",
    "filter_tracks_by_correlation",
    "filter_short_tracks",
    "get_track_quality_report",
    "get_tracks_by_quality",
    "get_solve_readiness_score",
    "recommend_cleaning_action",
    "BLENDER_AVAILABLE",
]
