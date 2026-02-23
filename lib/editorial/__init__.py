"""
Editorial System

Timeline and editorial tools for assembling shots into sequences.

Features:
- Timeline creation and management
- Clip placement and trimming
- Transitions (cut, dissolve, wipe)
- EDL/XML export
- EDL/XML import
- Runtime calculation

Part of Milestone v0.9 - Production Tracking System
Phase 11.1: Timeline System (REQ-EDIT-01 to REQ-EDIT-05)
Beads: blender_gsd-41

Usage:
    from lib.editorial import (
        # Types
        Timecode,
        Clip,
        Track,
        Timeline,
        Marker,
        Transition,
        TransitionType,
        TrackType,

        # Manager
        TimelineManager,

        # Transitions
        create_cut,
        create_dissolve,
        create_wipe,
        create_fade_to_black,
        create_fade_from_black,
        create_dip_to_color,
        apply_transition_blender,
        create_transition_from_preset,
        get_transition_presets,

        # Export
        export_edl,
        export_fcpxml,
        export_otio,
        export_aaf,
        export_timeline,
        generate_edl_content,
        generate_cut_list,

        # Import
        import_edl,
        import_fcpxml,
        import_otio,
        import_xml,
        import_timeline,
        parse_edl,
        parse_fcpxml,
        parse_otio,
        detect_format,

        # Assembly
        assemble_from_shot_list,
        auto_sequence_clips,
        conform_timeline,
        create_sequence_from_scenes,
        calculate_total_runtime,
        calculate_runtime_formatted,
        get_timeline_statistics,
        fill_gaps,
        remove_gaps,
    )

    # Create a timeline
    timeline = Timeline(name="My Sequence", frame_rate=24.0)
    video_track = timeline.add_video_track("V1")

    # Add a clip
    clip = Clip(
        name="Shot_001",
        source_path="/path/to/media.mp4",
        source_in=Timecode.from_frames(0, 24.0),
        source_out=Timecode.from_frames(100, 24.0),
        record_in=Timecode.from_frames(0, 24.0),
        record_out=Timecode.from_frames(100, 24.0),
    )
    video_track.add_clip(clip)

    # Export as EDL
    export_edl(timeline, "output.edl")
"""

# Types
from .timeline_types import (
    # Enums
    TransitionType,
    TrackType,
    # Dataclasses
    Timecode,
    Marker,
    Transition,
    Clip,
    Track,
    Timeline,
)

# Manager
from .timeline_manager import TimelineManager

# Transitions
from .transitions import (
    create_cut,
    create_dissolve,
    create_wipe,
    create_fade_to_black,
    create_fade_from_black,
    create_dip_to_color,
    apply_transition_blender,
    create_transition_from_preset,
    get_transition_presets,
    TRANSITION_PRESETS,
)

# Export
from .export import (
    export_edl,
    export_fcpxml,
    export_otio,
    export_aaf,
    export_timeline,
    export_cut_list,
    generate_edl_content,
    generate_fcpxml_content,
    generate_otio_content,
    generate_cut_list,
)

# Import
from .timeline_import import (
    import_edl,
    import_fcpxml,
    import_otio,
    import_xml,
    import_timeline,
    parse_edl,
    parse_fcpxml,
    parse_otio,
    detect_format,
)

# Assembly
from .assembly import (
    assemble_from_shot_list,
    auto_sequence_clips,
    conform_timeline,
    create_sequence_from_scenes,
    calculate_total_runtime,
    calculate_runtime_formatted,
    calculate_runtime_frames,
    calculate_runtime_timecode,
    generate_cut_list,
    fill_gaps,
    remove_gaps,
    get_timeline_statistics,
)

__all__ = [
    # Enums
    "TransitionType",
    "TrackType",

    # Dataclasses
    "Timecode",
    "Marker",
    "Transition",
    "Clip",
    "Track",
    "Timeline",

    # Manager
    "TimelineManager",

    # Transitions
    "create_cut",
    "create_dissolve",
    "create_wipe",
    "create_fade_to_black",
    "create_fade_from_black",
    "create_dip_to_color",
    "apply_transition_blender",
    "create_transition_from_preset",
    "get_transition_presets",
    "TRANSITION_PRESETS",

    # Export
    "export_edl",
    "export_fcpxml",
    "export_otio",
    "export_aaf",
    "export_timeline",
    "export_cut_list",
    "generate_edl_content",
    "generate_fcpxml_content",
    "generate_otio_content",
    "generate_cut_list",

    # Import
    "import_edl",
    "import_fcpxml",
    "import_otio",
    "import_xml",
    "import_timeline",
    "parse_edl",
    "parse_fcpxml",
    "parse_otio",
    "detect_format",

    # Assembly
    "assemble_from_shot_list",
    "auto_sequence_clips",
    "conform_timeline",
    "create_sequence_from_scenes",
    "calculate_total_runtime",
    "calculate_runtime_formatted",
    "calculate_runtime_frames",
    "calculate_runtime_timecode",
    "fill_gaps",
    "remove_gaps",
    "get_timeline_statistics",
]

__version__ = "0.1.0"
