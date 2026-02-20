"""
Development Module - Script parsing, analysis, and shot list generation.

This module provides screenplay parsing (Fountain, Final Draft),
beat sheet generation, comprehensive script analysis, and
automatic shot list generation with storyboard prompts.

Phase 8.1: Script Parser
Phase 8.2: Shot List Generator

Requirements:
- REQ-SCRIPT-01: Parse Fountain format
- REQ-SCRIPT-02: Parse Final Draft (.fdx)
- REQ-SCRIPT-03: Extract scenes, characters, dialogue
- REQ-SCRIPT-04: Generate beat sheets
- REQ-SCRIPT-05: Calculate timing estimates
- REQ-SHOT-01: Auto-generate shots from scenes
- REQ-SHOT-02: Coverage estimation
- REQ-SHOT-03: Shot size suggestions
- REQ-SHOT-04: Storyboard prompt generation
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

# Shot List Generator types
from .shot_gen_types import (
    ShotSuggestion,
    CoverageEstimate,
    SceneShotList,
    ShotList,
    StoryboardPrompt,
    SHOT_SIZES,
    CAMERA_ANGLES,
    SHOT_PURPOSES,
    CAMERA_MOVES,
    PRIORITIES,
)

# Scene Analyzer
from .scene_analyzer import (
    SceneAnalysis,
    analyze_scene_for_shots,
    analyze_scene_content,
    count_characters_in_scene,
    identify_scene_type,
    estimate_scene_duration,
    identify_key_moments,
    calculate_coverage_estimate,
)

# Shot Rules Engine
from .shot_rules import (
    COVERAGE_RULES,
    SHOT_SIZE_RULES,
    CAMERA_ANGLE_RULES,
    ShotRule,
    apply_coverage_rules,
    suggest_shot_size,
    suggest_camera_angle,
    calculate_shot_priority,
    get_coverage_summary,
)

# Storyboard Prompts
from .storyboard_prompts import (
    STYLE_PRESETS,
    COMPOSITION_GUIDELINES,
    LIGHTING_PRESETS,
    generate_storyboard_prompt,
    generate_ai_image_prompt,
    create_shot_description,
    generate_batch_prompts,
    export_prompts_as_text,
)

# Shot List Export
from .shot_list_export import (
    export_shot_list_csv,
    export_shot_list_csv_string,
    export_shot_list_yaml,
    export_shot_list_yaml_string,
    export_shot_list_json,
    export_shot_list_pdf,
    export_shot_list_html,
    generate_shot_list_html,
    generate_shot_report,
    generate_producer_summary,
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
    # Shot List Generator
    "ShotSuggestion",
    "CoverageEstimate",
    "SceneShotList",
    "ShotList",
    "StoryboardPrompt",
    "SHOT_SIZES",
    "CAMERA_ANGLES",
    "SHOT_PURPOSES",
    "CAMERA_MOVES",
    "PRIORITIES",
    # Scene Analyzer
    "SceneAnalysis",
    "analyze_scene_for_shots",
    "analyze_scene_content",
    "count_characters_in_scene",
    "identify_scene_type",
    "estimate_scene_duration",
    "identify_key_moments",
    "calculate_coverage_estimate",
    # Shot Rules
    "COVERAGE_RULES",
    "SHOT_SIZE_RULES",
    "CAMERA_ANGLE_RULES",
    "ShotRule",
    "apply_coverage_rules",
    "suggest_shot_size",
    "suggest_camera_angle",
    "calculate_shot_priority",
    "get_coverage_summary",
    # Storyboard Prompts
    "STYLE_PRESETS",
    "COMPOSITION_GUIDELINES",
    "LIGHTING_PRESETS",
    "generate_storyboard_prompt",
    "generate_ai_image_prompt",
    "create_shot_description",
    "generate_batch_prompts",
    "export_prompts_as_text",
    # Shot List Export
    "export_shot_list_csv",
    "export_shot_list_csv_string",
    "export_shot_list_yaml",
    "export_shot_list_yaml_string",
    "export_shot_list_json",
    "export_shot_list_pdf",
    "export_shot_list_html",
    "generate_shot_list_html",
    "generate_shot_report",
    "generate_producer_summary",
]

__version__ = "0.6.0"
