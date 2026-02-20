"""
Development Module - Script parsing and analysis tools.

This module provides screenplay parsing (Fountain, Final Draft),
beat sheet generation, and comprehensive script analysis.

Phase 8.1: Script Parser

Requirements:
- REQ-SCRIPT-01: Parse Fountain format
- REQ-SCRIPT-02: Parse Final Draft (.fdx)
- REQ-SCRIPT-03: Extract scenes, characters, dialogue
- REQ-SCRIPT-04: Generate beat sheets
- REQ-SCRIPT-05: Calculate timing estimates
"""

# Core types
from .script_types import (
    # Data classes
    Script,
    Scene,
    Character,
    Location,
    ActionBlock,
    DialogueLine,
    Transition,
    Beat,
    BeatSheet,
    ScriptAnalysis,
)

# Parsers
from .fountain_parser import (
    FountainParser,
    parse_fountain,
    parse_fountain_file,
)

from .fdx_parser import (
    FdxParser,
    parse_fdx,
    parse_fdx_file,
)

# Analysis tools
from .beat_generator import (
    generate_beat_sheet,
    identify_act_breaks,
    calculate_pacing,
    identify_emotional_peaks,
    create_beat_summary,
    SAVE_THE_CAT_BEATS,
    THREE_ACT_BEATS,
    STORY_CIRCLE_BEATS,
)

from .script_analysis import (
    analyze_script,
    generate_recommendations,
    get_character_network,
    get_location_schedule,
    get_cast_list,
    get_daily_breakdown,
    compare_characters,
    export_analysis_report,
)


__all__ = [
    # Types
    "Script",
    "Scene",
    "Character",
    "Location",
    "ActionBlock",
    "DialogueLine",
    "Transition",
    "Beat",
    "BeatSheet",
    "ScriptAnalysis",
    # Parsers
    "FountainParser",
    "parse_fountain",
    "parse_fountain_file",
    "FdxParser",
    "parse_fdx",
    "parse_fdx_file",
    # Beat generator
    "generate_beat_sheet",
    "identify_act_breaks",
    "calculate_pacing",
    "identify_emotional_peaks",
    "create_beat_summary",
    "SAVE_THE_CAT_BEATS",
    "THREE_ACT_BEATS",
    "STORY_CIRCLE_BEATS",
    # Analysis
    "analyze_script",
    "generate_recommendations",
    "get_character_network",
    "get_location_schedule",
    "get_cast_list",
    "get_daily_breakdown",
    "compare_characters",
    "export_analysis_report",
]

__version__ = "0.5.0"
