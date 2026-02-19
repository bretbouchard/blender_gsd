"""
Audio Sync Module (REQ-CINE-AUDIO)

Audio track support for animation timing and synchronization.
Supports loading audio files, placing beat markers, and BPM detection.

Usage:
    from lib.cinematic.audio_sync import load_audio, place_beat_markers, detect_bpm

    # Load audio file
    load_audio("soundtrack.wav")

    # Place beat markers
    place_beat_markers(bpm=120, fps=24)

    # Auto-detect BPM
    bpm = detect_bpm("music.mp3")
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List
import math

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .types import AudioSyncConfig


def load_audio(
    audio_file: str,
    scene: Optional[Any] = None,
    offset_frames: int = 0
) -> bool:
    """
    Load audio file into scene.

    Adds audio to the VSE (Video Sequence Editor) for playback
    and waveform visualization.

    Args:
        audio_file: Path to audio file
        scene: Optional scene (uses context if None)
        offset_frames: Frame offset for audio start

    Returns:
        True on success
    """
    if not BLENDER_AVAILABLE:
        return False

    if scene is None:
        scene = bpy.context.scene

    path = Path(audio_file)
    if not path.exists():
        return False

    try:
        # Ensure scene has VSE data
        if not scene.sequence_editor:
            scene.sequence_editor_create()

        seq = scene.sequence_editor

        # Check if audio already loaded
        for strip in seq.sequences:
            if strip.type == "SOUND" and strip.sound:
                if strip.sound.filepath == str(path.absolute()):
                    return True

        # Load audio
        sound = bpy.data.sounds.load(str(path.absolute()))
        strip = seq.sequences.new_sound(
            name=path.stem,
            sound=sound,
            channel=1,
            frame_start=scene.frame_start + offset_frames
        )

        return True

    except Exception:
        return False


def place_beat_markers(
    bpm: float,
    fps: float = 24.0,
    start_frame: int = 1,
    duration_frames: int = 250,
    scene: Optional[Any] = None,
    marker_prefix: str = "Beat"
) -> List[int]:
    """
    Place timeline markers on beat intervals.

    Args:
        bpm: Beats per minute
        fps: Frames per second
        start_frame: First frame for markers
        duration_frames: Total duration to place markers
        scene: Optional scene
        marker_prefix: Prefix for marker names

    Returns:
        List of frame numbers where markers were placed
    """
    if not BLENDER_AVAILABLE:
        return []

    if scene is None:
        scene = bpy.context.scene

    if bpm <= 0:
        return []

    # Calculate frames per beat
    beats_per_second = bpm / 60.0
    frames_per_beat = fps / beats_per_second

    marker_frames = []
    beat = 0

    frame = start_frame
    while frame <= start_frame + duration_frames:
        # Create marker
        marker_name = f"{marker_prefix}_{beat:03d}"

        # Add marker to timeline
        if not hasattr(scene, "timeline_markers"):
            return marker_frames

        # Check if marker exists
        existing = None
        for m in scene.timeline_markers:
            if m.frame == frame:
                existing = m
                break

        if existing:
            existing.name = marker_name
        else:
            marker = scene.timeline_markers.new(marker_name, frame=frame)

        marker_frames.append(int(frame))
        beat += 1
        frame = start_frame + (beat * frames_per_beat)

    return marker_frames


def detect_bpm(
    audio_file: str
) -> float:
    """
    Detect BPM from audio file.

    This is a placeholder - full implementation would use audio analysis
    libraries like librosa or aubio.

    Args:
        audio_file: Path to audio file

    Returns:
        Detected BPM or 0 if detection fails
    """
    # Placeholder - returns 0 (auto-detect not implemented)
    # Full implementation would:
    # 1. Load audio samples
    # 2. Compute onset strength
    # 3. Find tempo via autocorrelation
    # 4. Return most likely BPM

    return 0.0


def create_animation_markers(
    config: AudioSyncConfig,
    scene: Optional[Any] = None
) -> List[int]:
    """
    Create timeline markers from audio sync configuration.

    Combines audio loading with beat marker placement.

    Args:
        config: Audio sync configuration
        scene: Optional scene

    Returns:
        List of created marker frame numbers
    """
    if not BLENDER_AVAILABLE:
        return []

    if scene is None:
        scene = bpy.context.scene

    marker_frames = []

    # Load audio if specified
    if config.audio_file:
        load_audio(config.audio_file, scene, config.offset_frames)

    # Determine BPM
    bpm = config.bpm
    if bpm <= 0 and config.auto_detect_bpm:
        bpm = detect_bpm(config.audio_file)

    if bpm <= 0:
        bpm = 120.0  # Default fallback

    # Place beat markers
    if config.beat_markers:
        # Use explicit beat frames
        for i, frame in enumerate(config.beat_markers):
            frame = frame + config.offset_frames
            marker_name = f"Beat_{i:03d}"
            if hasattr(scene, "timeline_markers"):
                scene.timeline_markers.new(marker_name, frame=frame)
            marker_frames.append(frame)
    else:
        # Auto-generate from BPM
        fps = scene.render.fps / scene.render.fps_base
        marker_frames = place_beat_markers(
            bpm=bpm,
            fps=fps,
            start_frame=scene.frame_start,
            duration_frames=scene.frame_end - scene.frame_start,
            scene=scene
        )

    # Add named markers
    if config.markers:
        for name, frame in config.markers.items():
            frame = frame + config.offset_frames
            if hasattr(scene, "timeline_markers"):
                scene.timeline_markers.new(name, frame=frame)
            marker_frames.append(frame)

    return marker_frames


def get_frame_at_beat(
    beat_number: int,
    bpm: float,
    fps: float = 24.0,
    start_frame: int = 1
) -> int:
    """
    Calculate frame number for a specific beat.

    Args:
        beat_number: Beat number (0-indexed)
        bpm: Beats per minute
        fps: Frames per second
        start_frame: First frame

    Returns:
        Frame number for the beat
    """
    if bpm <= 0:
        return start_frame

    beats_per_second = bpm / 60.0
    frames_per_beat = fps / beats_per_second

    return int(start_frame + (beat_number * frames_per_beat))


def get_beat_at_frame(
    frame: int,
    bpm: float,
    fps: float = 24.0,
    start_frame: int = 1
) -> int:
    """
    Calculate beat number for a specific frame.

    Args:
        frame: Frame number
        bpm: Beats per minute
        fps: Frames per second
        start_frame: First frame

    Returns:
        Beat number at frame
    """
    if bpm <= 0:
        return 0

    beats_per_second = bpm / 60.0
    frames_per_beat = fps / beats_per_second

    return int((frame - start_frame) / frames_per_beat)
