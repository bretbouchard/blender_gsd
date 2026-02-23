"""
Assembly Functions for Editorial System

Provides timeline assembly utilities:
- Shot list to timeline
- Auto-sequencing clips
- Conforming
- Runtime calculation

Part of Phase 11.1: Timeline System (REQ-EDIT-05)
Beads: blender_gsd-41
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any
from pathlib import Path

from .timeline_types import (
    Timeline,
    Clip,
    Track,
    Timecode,
    Transition,
    TransitionType,
    TrackType,
)
from .transitions import create_cut, create_dissolve
from .timeline_manager import TimelineManager


def assemble_from_shot_list(
    shots: List[Dict[str, Any]],
    timeline_name: str = "Sequence",
    frame_rate: float = 24.0,
    transition_type: str = "cut",
    transition_duration: int = 12,
) -> Timeline:
    """
    Create a timeline from a shot list.

    Args:
        shots: List of shot dictionaries with:
            - name: Shot name
            - source_path: Path to source media
            - source_in: Start frame in source
            - source_out: End frame in source
            - (optional) scene, take, notes
        timeline_name: Name for the timeline
        frame_rate: Frames per second
        transition_type: "cut" or "dissolve"
        transition_duration: Duration for dissolves (frames)

    Returns:
        Assembled timeline
    """
    timeline = Timeline(name=timeline_name, frame_rate=frame_rate)
    video_track = timeline.add_video_track("V1")

    current_frame = 0
    prev_clip_name = None

    for i, shot in enumerate(shots):
        source_in = shot.get('source_in', 0)
        source_out = shot.get('source_out', 0)

        # Create timecodes
        src_in_tc = Timecode.from_frames(source_in, frame_rate)
        src_out_tc = Timecode.from_frames(source_out, frame_rate)
        rec_in_tc = Timecode.from_frames(current_frame, frame_rate)
        duration = source_out - source_in
        rec_out_tc = Timecode.from_frames(current_frame + duration, frame_rate)

        clip = Clip(
            name=shot.get('name', f'Shot_{i + 1:03d}'),
            source_path=shot.get('source_path', ''),
            source_in=src_in_tc,
            source_out=src_out_tc,
            record_in=rec_in_tc,
            record_out=rec_out_tc,
            track=1,
            scene=shot.get('scene', 0),
            take=shot.get('take', 1),
            notes=shot.get('notes', ''),
        )

        video_track.add_clip(clip)

        # Add transition
        if prev_clip_name and transition_type != "cut":
            trans = create_dissolve(
                duration=transition_duration,
                from_clip=prev_clip_name,
                to_clip=clip.name,
            )
            timeline.transitions.append(trans)

        prev_clip_name = clip.name
        current_frame += duration

    timeline.duration = timeline.calculate_duration()
    return timeline


def auto_sequence_clips(
    clip_paths: List[str],
    timeline_name: str = "Auto Sequence",
    frame_rate: float = 24.0,
    default_duration: int = 72,  # 3 seconds at 24fps
    transition_type: str = "cut",
) -> Timeline:
    """
    Automatically sequence clips from file paths.

    Creates a timeline with clips in order, using default duration
    for each clip.

    Args:
        clip_paths: List of source file paths
        timeline_name: Name for the timeline
        frame_rate: Frames per second
        default_duration: Duration for each clip (frames)
        transition_type: "cut" or "dissolve"

    Returns:
        Auto-sequenced timeline
    """
    timeline = Timeline(name=timeline_name, frame_rate=frame_rate)
    video_track = timeline.add_video_track("V1")

    current_frame = 0

    for i, path in enumerate(clip_paths):
        path_obj = Path(path)
        clip_name = path_obj.stem or f"Clip_{i + 1:03d}"

        rec_in_tc = Timecode.from_frames(current_frame, frame_rate)
        rec_out_tc = Timecode.from_frames(current_frame + default_duration, frame_rate)

        clip = Clip(
            name=clip_name,
            source_path=path,
            source_in=Timecode.from_frames(0, frame_rate),
            source_out=Timecode.from_frames(default_duration, frame_rate),
            record_in=rec_in_tc,
            record_out=rec_out_tc,
            track=1,
        )

        video_track.add_clip(clip)
        current_frame += default_duration

    timeline.duration = timeline.calculate_duration()
    return timeline


def conform_timeline(
    timeline: Timeline,
    source_clips: Dict[str, str],
) -> Timeline:
    """
    Relink timeline clips to new source files.

    Useful for conforming an offline edit to online media.

    Args:
        timeline: Timeline to conform
        source_clips: Dict mapping clip names to new source paths

    Returns:
        Conformed timeline (new instance)
    """
    # Create a copy
    new_timeline = Timeline.from_dict(timeline.to_dict())

    # Relink clips
    for clip in new_timeline.get_all_clips():
        if clip.name in source_clips:
            clip.source_path = source_clips[clip.name]

    return new_timeline


def create_sequence_from_scenes(
    scenes: List[Dict[str, Any]],
    frame_rate: float = 24.0,
) -> Timeline:
    """
    Create timeline from script scenes.

    Each scene becomes a marker, and shots within scenes
    become clips.

    Args:
        scenes: List of scene dictionaries with:
            - name: Scene name/number
            - shots: List of shot dictionaries
            - (optional) location, time_of_day
        frame_rate: Frames per second

    Returns:
        Timeline with scenes and shots
    """
    timeline = Timeline(name="Scene Sequence", frame_rate=frame_rate)
    video_track = timeline.add_video_track("V1")

    current_frame = 0
    scene_number = 1

    for scene in scenes:
        scene_name = scene.get('name', f'Scene {scene_number}')

        # Add scene marker
        marker = timeline.markers.append(
            type('Marker', (), {
                'name': scene_name,
                'position': Timecode.from_frames(current_frame, frame_rate),
                'color': 'blue',
                'note': f"Location: {scene.get('location', 'Unknown')}",
            })()
        )

        shots = scene.get('shots', [])
        for shot in shots:
            source_in = shot.get('source_in', 0)
            source_out = shot.get('source_out', source_in + 72)  # Default 3 sec
            duration = source_out - source_in

            clip = Clip(
                name=shot.get('name', f'{scene_name}_Shot_{len(video_track.clips) + 1}'),
                source_path=shot.get('source_path', ''),
                source_in=Timecode.from_frames(source_in, frame_rate),
                source_out=Timecode.from_frames(source_out, frame_rate),
                record_in=Timecode.from_frames(current_frame, frame_rate),
                record_out=Timecode.from_frames(current_frame + duration, frame_rate),
                track=1,
                scene=scene_number,
                take=shot.get('take', 1),
                notes=shot.get('notes', ''),
            )

            video_track.add_clip(clip)
            current_frame += duration

        scene_number += 1

    timeline.duration = timeline.calculate_duration()
    return timeline


# ==================== Runtime Calculation ====================

def calculate_total_runtime(timeline: Timeline) -> float:
    """
    Calculate total runtime in seconds.

    Args:
        timeline: Timeline to measure

    Returns:
        Runtime in seconds
    """
    duration = timeline.calculate_duration()
    return duration.to_seconds()


def calculate_runtime_formatted(timeline: Timeline) -> str:
    """
    Calculate runtime as formatted string.

    Args:
        timeline: Timeline to measure

    Returns:
        Runtime as MM:SS or HH:MM:SS
    """
    seconds = calculate_total_runtime(timeline)

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def calculate_runtime_frames(timeline: Timeline) -> int:
    """
    Calculate total runtime in frames.

    Args:
        timeline: Timeline to measure

    Returns:
        Total frames
    """
    return timeline.calculate_duration().to_frames()


def calculate_runtime_timecode(timeline: Timeline) -> Timecode:
    """
    Calculate runtime as timecode.

    Args:
        timeline: Timeline to measure

    Returns:
        Timecode of duration
    """
    return timeline.calculate_duration()


# ==================== Cut List Generation ====================

def generate_cut_list(timeline: Timeline) -> List[Dict[str, Any]]:
    """
    Generate a cut list for online editing.

    A cut list contains all edit points and source information.

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
            "notes": clip.notes,
        }
        cut_list.append(entry)

    return cut_list


# ==================== Utility Functions ====================

def fill_gaps(timeline: Timeline, fill_color: tuple = (0.0, 0.0, 0.0, 1.0)) -> Timeline:
    """
    Fill gaps in timeline with slug/filler.

    Args:
        timeline: Timeline to fill
        fill_color: RGBA color for filler

    Returns:
        Timeline with gaps filled
    """
    manager = TimelineManager(timeline)
    gaps = manager.find_gaps()

    for i, (start, end) in enumerate(gaps):
        duration = end.to_frames() - start.to_frames()

        filler = Clip(
            name=f"Slug_{i + 1:03d}",
            source_path="",  # No source for slug
            source_in=Timecode.from_frames(0, timeline.frame_rate),
            source_out=Timecode.from_frames(duration, timeline.frame_rate),
            record_in=start,
            record_out=end,
            track=1,
            notes="Auto-generated slug",
        )

        manager.add_clip(filler, track_number=1)

    return timeline


def remove_gaps(timeline: Timeline) -> Timeline:
    """
    Remove gaps by closing up clips.

    Args:
        timeline: Timeline to close up

    Returns:
        Timeline with gaps removed
    """
    manager = TimelineManager(timeline)
    gaps = manager.find_gaps()

    # Process gaps in reverse order to maintain positions
    for start, end in reversed(gaps):
        duration = end.to_frames() - start.to_frames()
        manager.insert_gap(start, -duration, track_number=1)

    return timeline


def get_timeline_statistics(timeline: Timeline) -> Dict[str, Any]:
    """
    Get statistics about a timeline.

    Args:
        timeline: Timeline to analyze

    Returns:
        Dictionary with statistics
    """
    clips = timeline.get_all_clips()
    gaps = timeline.find_gaps()

    total_frames = calculate_runtime_frames(timeline)
    total_seconds = calculate_total_runtime(timeline)

    clip_frames = sum(c.duration for c in clips)
    gap_frames = sum(g[1].to_frames() - g[0].to_frames() for g in gaps)

    return {
        "name": timeline.name,
        "frame_rate": timeline.frame_rate,
        "total_frames": total_frames,
        "total_seconds": total_seconds,
        "runtime_formatted": calculate_runtime_formatted(timeline),
        "clip_count": len(clips),
        "video_track_count": len(timeline.video_tracks),
        "audio_track_count": len(timeline.audio_tracks),
        "transition_count": len(timeline.transitions),
        "marker_count": len(timeline.markers),
        "gap_count": len(gaps),
        "clip_frames": clip_frames,
        "gap_frames": gap_frames,
        "fill_percentage": (clip_frames / total_frames * 100) if total_frames > 0 else 100,
    }
