"""
Export Formats for Editorial System

Provides export to various editing formats:
- EDL (Edit Decision List) - CMX 3600 format
- FCPXML (Final Cut Pro XML)
- OTIO (OpenTimelineIO JSON)

Part of Phase 11.1: Timeline System (REQ-EDIT-04)
Beads: blender_gsd-41
"""

from __future__ import annotations
from typing import Optional
from pathlib import Path
import json

from .timeline_types import (
    Timeline,
    Clip,
    Track,
    Transition,
    Timecode,
    TransitionType,
    TrackType,
)


# ==================== EDL Export ====================

def export_edl(timeline: Timeline, path: str) -> bool:
    """
    Export timeline as EDL (Edit Decision List).

    CMX 3600 format - industry standard for online editing.

    Args:
        timeline: Timeline to export
        path: Output file path

    Returns:
        True if export successful
    """
    try:
        content = generate_edl_content(timeline)
        with open(path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"EDL export failed: {e}")
        return False


def generate_edl_content(timeline: Timeline) -> str:
    """
    Generate EDL file content.

    Args:
        timeline: Timeline to export

    Returns:
        EDL content as string
    """
    lines = []

    # Header
    lines.append(f"TITLE: {timeline.name}")
    lines.append("")
    lines.append(f"FCM: NON-DROP FRAME")
    lines.append("")

    # Get all clips in order
    clips = timeline.get_all_clips()
    event_number = 1

    for clip in clips:
        # Event number
        lines.append(f"{event_number:03d}")

        # Source reel (use clip name or "AX" for aux)
        reel = clip.name[:8].upper() if clip.name else "AX"

        # Track (V for video, A for audio)
        track_type = "V" if clip.track > 0 else "A"

        # Edit type (C for cut, D for dissolve, W for wipe)
        edit_type = "C"

        # Source in/out (timecode)
        src_in = _format_edl_timecode(clip.source_in)
        src_out = _format_edl_timecode(clip.source_out)

        # Record in/out (timeline timecode)
        rec_in = _format_edl_timecode(clip.record_in)
        rec_out = _format_edl_timecode(clip.record_out)

        # Main edit line
        lines.append(
            f"{reel:8s} {track_type:6s} {track_type}     {edit_type}        "
            f"{src_in} {src_out} {rec_in} {rec_out}"
        )

        # Source file (optional remark)
        if clip.source_path:
            lines.append(f"* FROM CLIP NAME: {clip.source_path}")

        # Notes
        if clip.notes:
            lines.append(f"* COMMENT: {clip.notes}")

        lines.append("")
        event_number += 1

    return "\n".join(lines)


def _format_edl_timecode(tc: Timecode) -> str:
    """Format timecode for EDL (space-separated)."""
    return f"{tc.hours:02d} {tc.minutes:02d} {tc.seconds:02d} {tc.frames:02d}"


# ==================== FCPXML Export ====================

def export_fcpxml(timeline: Timeline, path: str) -> bool:
    """
    Export timeline as FCPXML (Final Cut Pro XML).

    Args:
        timeline: Timeline to export
        path: Output file path

    Returns:
        True if export successful
    """
    try:
        content = generate_fcpxml_content(timeline)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"FCPXML export failed: {e}")
        return False


def generate_fcpxml_content(timeline: Timeline) -> str:
    """
    Generate FCPXML content.

    Simplified FCPXML 1.9 format.

    Args:
        timeline: Timeline to export

    Returns:
        FCPXML content as string
    """
    lines = []

    # XML declaration and root
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE fcpxml>')
    lines.append('')
    lines.append('<fcpxml version="1.9">')
    lines.append('    <resources>')

    # Format resource
    frame_duration = f"1/{int(timeline.frame_rate)}s"
    lines.append(f'        <format id="r1" name="FFVideoFormat{int(timeline.frame_rate)}p" frameDuration="{frame_duration}" width="1920" height="1080"/>')

    lines.append('    </resources>')
    lines.append('')
    lines.append('    <library>')
    lines.append(f'        <event name="{timeline.name}">')
    lines.append(f'            <project name="{timeline.name}">')
    lines.append('                <sequence duration="0s" format="r1">')
    lines.append('                    <spine>')

    # Add clips
    for clip in timeline.get_all_clips():
        duration_frames = clip.duration
        duration_time = duration_frames / timeline.frame_rate
        offset_frames = clip.record_in.to_frames()
        offset_time = offset_frames / timeline.frame_rate

        lines.append(f'                        <clip name="{clip.name}" offset="{offset_time}s" duration="{duration_time}s">')
        lines.append(f'                            <video offset="0s" name="{clip.name}">')

        if clip.source_path:
            lines.append(f'                                <asset-clip name="{Path(clip.source_path).stem}" offset="0s" ref="r1" duration="{duration_time}s"/>')

        lines.append('                            </video>')
        lines.append('                        </clip>')

    lines.append('                    </spine>')
    lines.append('                </sequence>')
    lines.append('            </project>')
    lines.append('        </event>')
    lines.append('    </library>')
    lines.append('</fcpxml>')

    return '\n'.join(lines)


# ==================== OTIO Export ====================

def export_otio(timeline: Timeline, path: str) -> bool:
    """
    Export timeline as OpenTimelineIO JSON.

    Args:
        timeline: Timeline to export
        path: Output file path

    Returns:
        True if export successful
    """
    try:
        content = generate_otio_content(timeline)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2)
        return True
    except Exception as e:
        print(f"OTIO export failed: {e}")
        return False


def generate_otio_content(timeline: Timeline) -> dict:
    """
    Generate OpenTimelineIO JSON structure.

    Args:
        timeline: Timeline to export

    Returns:
        OTIO-compatible dictionary
    """
    # Build track data
    tracks = []

    for track in timeline.video_tracks:
        track_data = {
            "OTIO_SCHEMA": "Track.1",
            "name": track.name,
            "source_range": {
                "start_time": 0,
                "duration": timeline.calculate_duration().to_frames(),
                "rate": timeline.frame_rate,
            },
            "kind": "Video",
            "children": [],
        }

        for clip in track.clips:
            clip_data = {
                "OTIO_SCHEMA": "Clip.1",
                "name": clip.name,
                "source_range": {
                    "start_time": clip.source_in.to_frames(),
                    "duration": clip.duration,
                    "rate": timeline.frame_rate,
                },
                "media_reference": {
                    "OTIO_SCHEMA": "ExternalReference.1",
                    "target_url": clip.source_path,
                    "available_range": {
                        "start_time": 0,
                        "duration": clip.source_out.to_frames(),
                        "rate": timeline.frame_rate,
                    },
                },
                "metadata": {
                    "scene": clip.scene,
                    "take": clip.take,
                    "notes": clip.notes,
                },
            }
            track_data["children"].append(clip_data)

        tracks.append(track_data)

    # Build timeline
    otio = {
        "OTIO_SCHEMA": "Timeline.1",
        "name": timeline.name,
        "global_start_time": {
            "value": timeline.starting_timecode.to_frames(),
            "rate": timeline.frame_rate,
        },
        "tracks": {
            "OTIO_SCHEMA": "Stack.1",
            "name": "tracks",
            "children": tracks,
        },
        "metadata": {
            "exporter": "blender_gsd",
            "frame_rate": timeline.frame_rate,
        },
    }

    return otio


# ==================== AAF Export ====================

def export_aaf(timeline: Timeline, path: str) -> bool:
    """
    Export timeline as AAF (Advanced Authoring Format).

    Note: AAF requires pyaaf library. This provides a basic structure
    that can be enhanced with pyaaf if available.

    Args:
        timeline: Timeline to export
        path: Output file path

    Returns:
        True if export successful
    """
    try:
        # Try to import pyaaf
        try:
            import aaf  # type: ignore
            HAS_AAF = True
        except ImportError:
            HAS_AAF = False

        if not HAS_AAF:
            # Fall back to JSON representation
            return _export_aaf_json_fallback(timeline, path)

        # Full AAF export would go here
        # This is a placeholder for pyaaf integration
        return _export_aaf_json_fallback(timeline, path)

    except Exception as e:
        print(f"AAF export failed: {e}")
        return False


def _export_aaf_json_fallback(timeline: Timeline, path: str) -> bool:
    """Export AAF-compatible JSON structure."""
    try:
        aaf_data = {
            "format": "AAF",
            "version": "1.0",
            "timeline": timeline.to_dict(),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(aaf_data, f, indent=2)
        return True
    except Exception:
        return False


# ==================== Cut List Export ====================

def generate_cut_list(timeline: Timeline) -> list:
    """
    Generate a cut list for online editing.

    A cut list contains all edit points and source information
    needed for conforming in another system.

    Args:
        timeline: Timeline to export

    Returns:
        List of cut entries
    """
    cut_list = []
    clips = timeline.get_all_clips()

    for i, clip in enumerate(clips):
        entry = {
            "edit_number": i + 1,
            "clip_name": clip.name,
            "source_file": clip.source_path,
            "source_in": str(clip.source_in),
            "source_out": str(clip.source_out),
            "source_in_frames": clip.source_in.to_frames(),
            "source_out_frames": clip.source_out.to_frames(),
            "record_in": str(clip.record_in),
            "record_out": str(clip.record_out),
            "record_in_frames": clip.record_in.to_frames(),
            "record_out_frames": clip.record_out.to_frames(),
            "duration_frames": clip.duration,
            "track": clip.track,
            "scene": clip.scene,
            "take": clip.take,
        }
        cut_list.append(entry)

    return cut_list


def export_cut_list(timeline: Timeline, path: str) -> bool:
    """
    Export cut list as JSON.

    Args:
        timeline: Timeline to export
        path: Output file path

    Returns:
        True if export successful
    """
    try:
        cut_list = generate_cut_list(timeline)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cut_list, f, indent=2)
        return True
    except Exception:
        return False


# ==================== Convenience Functions ====================

def export_timeline(timeline: Timeline, path: str, format: str = "edl") -> bool:
    """
    Export timeline in specified format.

    Args:
        timeline: Timeline to export
        path: Output file path
        format: Export format (edl, fcpxml, otio, aaf, cutlist)

    Returns:
        True if export successful
    """
    format = format.lower()

    exporters = {
        "edl": export_edl,
        "fcpxml": export_fcpxml,
        "xml": export_fcpxml,  # alias
        "otio": export_otio,
        "json": export_otio,  # alias
        "aaf": export_aaf,
        "cutlist": export_cut_list,
    }

    exporter = exporters.get(format)
    if exporter is None:
        print(f"Unknown export format: {format}")
        return False

    return exporter(timeline, path)
