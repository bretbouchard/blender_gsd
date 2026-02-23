"""
Import Formats for Editorial System

Provides import from various editing formats:
- EDL (Edit Decision List) - CMX 3600 format
- FCPXML (Final Cut Pro XML)
- OTIO (OpenTimelineIO JSON)

Part of Phase 11.1: Timeline System (REQ-EDIT-04)
Beads: blender_gsd-41
"""

from __future__ import annotations
from typing import Optional, List, Tuple
from pathlib import Path
import re
import json
import xml.etree.ElementTree as ET

from .timeline_types import (
    Timeline,
    Clip,
    Track,
    Transition,
    Timecode,
    TransitionType,
    TrackType,
)


# ==================== EDL Import ====================

def import_edl(path: str, frame_rate: float = 24.0) -> Optional[Timeline]:
    """
    Import timeline from EDL file.

    Args:
        path: Path to EDL file
        frame_rate: Frame rate for the timeline

    Returns:
        Timeline or None if import failed
    """
    try:
        with open(path, 'r') as f:
            content = f.read()
        return parse_edl(content, frame_rate)
    except Exception as e:
        print(f"EDL import failed: {e}")
        return None


def parse_edl(content: str, frame_rate: float = 24.0) -> Optional[Timeline]:
    """
    Parse EDL file content.

    Supports CMX 3600 format.

    Args:
        content: EDL file content
        frame_rate: Frame rate for the timeline

    Returns:
        Timeline or None if parsing failed
    """
    lines = content.strip().split('\n')

    # Extract title
    title = "Imported Timeline"
    for line in lines:
        if line.startswith('TITLE:'):
            title = line[6:].strip()
            break

    timeline = Timeline(name=title, frame_rate=frame_rate)
    video_track = timeline.add_video_track("V1")

    # Parse events
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and headers
        if not line or line.startswith('TITLE:') or line.startswith('FCM:'):
            i += 1
            continue

        # Check for event number (3 digits)
        if re.match(r'^\d{3}$', line):
            event_num = int(line)
            i += 1

            if i >= len(lines):
                break

            # Parse edit line
            edit_line = lines[i].strip()

            # Parse: REEL  TRACK  TYPE  ... SRC_IN SRC_OUT REC_IN REC_OUT
            match = re.match(
                r'(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+'
                r'(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+'
                r'(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+'
                r'(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+'
                r'(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})',
                edit_line,
            )

            if match:
                reel = match.group(1)

                # Source timecode
                src_in = Timecode(
                    hours=int(match.group(5)),
                    minutes=int(match.group(6)),
                    seconds=int(match.group(7)),
                    frames=int(match.group(8)),
                    frame_rate=frame_rate,
                )
                src_out = Timecode(
                    hours=int(match.group(9)),
                    minutes=int(match.group(10)),
                    seconds=int(match.group(11)),
                    frames=int(match.group(12)),
                    frame_rate=frame_rate,
                )

                # Record timecode
                rec_in = Timecode(
                    hours=int(match.group(13)),
                    minutes=int(match.group(14)),
                    seconds=int(match.group(15)),
                    frames=int(match.group(16)),
                    frame_rate=frame_rate,
                )
                rec_out = Timecode(
                    hours=int(match.group(17)),
                    minutes=int(match.group(18)),
                    seconds=int(match.group(19)),
                    frames=int(match.group(20)),
                    frame_rate=frame_rate,
                )

                # Look for clip name in subsequent lines
                clip_name = f"Clip_{event_num:03d}"
                source_path = ""

                i += 1
                while i < len(lines):
                    remark = lines[i].strip()
                    if remark.startswith('* FROM CLIP NAME:'):
                        source_path = remark[17:].strip()
                        clip_name = Path(source_path).stem
                    elif remark.startswith('* COMMENT:'):
                        pass  # Could extract notes
                    elif re.match(r'^\d{3}$', remark) or not remark:
                        break
                    i += 1

                clip = Clip(
                    name=clip_name,
                    source_path=source_path,
                    source_in=src_in,
                    source_out=src_out,
                    record_in=rec_in,
                    record_out=rec_out,
                    track=1,
                )
                video_track.add_clip(clip)
            else:
                i += 1
        else:
            i += 1

    timeline.duration = timeline.calculate_duration()
    return timeline


# ==================== FCPXML Import ====================

def import_fcpxml(path: str) -> Optional[Timeline]:
    """
    Import timeline from FCPXML file.

    Args:
        path: Path to FCPXML file

    Returns:
        Timeline or None if import failed
    """
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        return parse_fcpxml(root)
    except Exception as e:
        print(f"FCPXML import failed: {e}")
        return None


def parse_fcpxml(root: ET.Element) -> Optional[Timeline]:
    """
    Parse FCPXML element tree.

    Args:
        root: XML root element

    Returns:
        Timeline or None if parsing failed
    """
    # Find format for frame rate
    frame_rate = 24.0
    format_elem = root.find('.//format')
    if format_elem is not None:
        frame_duration = format_elem.get('frameDuration', '1/24s')
        # Parse "1/24s" format
        match = re.match(r'1/(\d+)s', frame_duration)
        if match:
            frame_rate = int(match.group(1))

    # Find project name
    project = root.find('.//project')
    name = project.get('name', 'Imported') if project is not None else 'Imported'

    timeline = Timeline(name=name, frame_rate=frame_rate)
    video_track = timeline.add_video_track("V1")

    # Find clips in spine
    spine = root.find('.//spine')
    if spine is None:
        return timeline

    for clip_elem in spine.findall('.//clip'):
        clip_name = clip_elem.get('name', 'Untitled')

        # Parse offset and duration
        offset = _parse_fcpxml_time(clip_elem.get('offset', '0s'), frame_rate)
        duration = _parse_fcpxml_time(clip_elem.get('duration', '0s'), frame_rate)

        # Find asset clip
        asset_clip = clip_elem.find('.//asset-clip')
        source_path = ""
        if asset_clip is not None:
            source_path = asset_clip.get('name', '')

        clip = Clip(
            name=clip_name,
            source_path=source_path,
            source_in=Timecode.from_frames(0, frame_rate),
            source_out=Timecode.from_frames(duration, frame_rate),
            record_in=Timecode.from_frames(offset, frame_rate),
            record_out=Timecode.from_frames(offset + duration, frame_rate),
            track=1,
        )
        video_track.add_clip(clip)

    timeline.duration = timeline.calculate_duration()
    return timeline


def _parse_fcpxml_time(time_str: str, frame_rate: float) -> int:
    """Parse FCPXML time string to frames."""
    # Format: "123.45s" or "123s"
    match = re.match(r'([\d.]+)s', time_str)
    if match:
        seconds = float(match.group(1))
        return int(seconds * frame_rate)
    return 0


# ==================== OTIO Import ====================

def import_otio(path: str) -> Optional[Timeline]:
    """
    Import timeline from OpenTimelineIO JSON file.

    Args:
        path: Path to OTIO JSON file

    Returns:
        Timeline or None if import failed
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return parse_otio(data)
    except Exception as e:
        print(f"OTIO import failed: {e}")
        return None


def parse_otio(data: dict) -> Optional[Timeline]:
    """
    Parse OpenTimelineIO JSON structure.

    Args:
        data: OTIO JSON data

    Returns:
        Timeline or None if parsing failed
    """
    # Check schema
    schema = data.get('OTIO_SCHEMA', '')
    if not schema.startswith('Timeline'):
        print("Not a valid OTIO timeline")
        return None

    name = data.get('name', 'Imported')

    # Get frame rate from metadata
    metadata = data.get('metadata', {})
    frame_rate = metadata.get('frame_rate', 24.0)

    timeline = Timeline(name=name, frame_rate=frame_rate)

    # Parse global start time
    global_start = data.get('global_start_time', {})
    if global_start:
        start_frames = global_start.get('value', 0)
        timeline.starting_timecode = Timecode.from_frames(start_frames, frame_rate)

    # Parse tracks
    tracks_data = data.get('tracks', {})
    children = tracks_data.get('children', [])

    for track_data in children:
        track_schema = track_data.get('OTIO_SCHEMA', '')

        if track_schema.startswith('Track'):
            track_name = track_data.get('name', 'Track')
            track_kind = track_data.get('kind', 'Video')

            if track_kind == 'Video':
                track = timeline.add_video_track(track_name)
            else:
                track = timeline.add_audio_track(track_name)

            # Parse clips
            clip_children = track_data.get('children', [])
            for clip_data in clip_children:
                if clip_data.get('OTIO_SCHEMA', '').startswith('Clip'):
                    clip = _parse_otio_clip(clip_data, track.track_number, frame_rate)
                    if clip:
                        track.add_clip(clip)

    timeline.duration = timeline.calculate_duration()
    return timeline


def _parse_otio_clip(data: dict, track_number: int, frame_rate: float) -> Optional[Clip]:
    """Parse OTIO clip data."""
    name = data.get('name', 'Untitled')

    source_range = data.get('source_range', {})
    start_time = source_range.get('start_time', 0)
    duration = source_range.get('duration', 0)

    # Get media reference
    media_ref = data.get('media_reference', {})
    source_path = media_ref.get('target_url', '')

    metadata = data.get('metadata', {})

    clip = Clip(
        name=name,
        source_path=source_path,
        source_in=Timecode.from_frames(start_time, frame_rate),
        source_out=Timecode.from_frames(start_time + duration, frame_rate),
        record_in=Timecode.from_frames(0, frame_rate),  # Will be set by track position
        record_out=Timecode.from_frames(duration, frame_rate),
        track=track_number,
        scene=metadata.get('scene', 0),
        take=metadata.get('take', 1),
        notes=metadata.get('notes', ''),
    )

    return clip


# ==================== XML Import (Generic) ====================

def import_xml(path: str) -> Optional[Timeline]:
    """
    Import timeline from generic XML file.

    Attempts to detect format (FCPXML or other).

    Args:
        path: Path to XML file

    Returns:
        Timeline or None if import failed
    """
    try:
        tree = ET.parse(path)
        root = tree.getroot()

        # Check for FCPXML
        if root.tag == 'fcpxml':
            return parse_fcpxml(root)

        # Could add other XML format detection here

        print("Unknown XML format")
        return None
    except Exception as e:
        print(f"XML import failed: {e}")
        return None


# ==================== Convenience Functions ====================

def import_timeline(path: str, format: Optional[str] = None) -> Optional[Timeline]:
    """
    Import timeline from file, auto-detecting format.

    Args:
        path: Path to timeline file
        format: Optional format hint (edl, fcpxml, otio, xml)

    Returns:
        Timeline or None if import failed
    """
    path_obj = Path(path)
    extension = format.lower() if format else path_obj.suffix.lower().lstrip('.')

    importers = {
        'edl': import_edl,
        'fcpxml': import_fcpxml,
        'xml': import_xml,
        'otio': import_otio,
        'json': import_otio,
    }

    # For EDL, we need frame rate
    if extension == 'edl':
        return import_edl(path, 24.0)

    importer = importers.get(extension)
    if importer is None:
        print(f"Unknown import format: {extension}")
        return None

    return importer(path)


def detect_format(path: str) -> Optional[str]:
    """
    Detect file format from content.

    Args:
        path: Path to file

    Returns:
        Format string (edl, fcpxml, otio) or None
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            first_line = f.readline()

        # Check for EDL
        if first_line.startswith('TITLE:') or re.match(r'^\d{3}$', first_line.strip()):
            return 'edl'

        # Check for XML
        if first_line.startswith('<?xml'):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '<fcpxml' in content:
                return 'fcpxml'
            return 'xml'

        # Check for JSON/OTIO
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'OTIO_SCHEMA' in data:
            return 'otio'
        return 'json'

    except Exception:
        return None
