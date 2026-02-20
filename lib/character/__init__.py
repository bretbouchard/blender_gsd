"""
Character Module

Wardrobe and costume management for productions.

Features:
- Costume definition and storage
- Scene-by-scene costume assignment
- Automatic costume change detection
- Continuity validation
- Costume bible generation
- YAML storage and export

Part of Phase 10.1: Wardrobe System (REQ-WARD-01 to REQ-WARD-05)
Beads: blender_gsd-42

Usage:
    from lib.character import (
        # Types
        CostumePiece,
        Costume,
        CostumeChange,
        CostumeAssignment,
        WardrobeRegistry,
        CostumeCategory,
        CostumeStyle,
        CostumeCondition,
        ChangeReason,
        IssueType,
        IssueSeverity,
        CONDITION_PROGRESSION,
        is_valid_condition_progression,

        # Manager
        CostumeManager,
        CostumeManagerError,
        CostumeNotFoundError,
        DuplicateCostumeError,
        InvalidAssignmentError,

        # Validation
        ContinuityIssue,
        ContinuityReport,
        validate_continuity,
        check_costume_consistency,
        check_condition_progression,
        suggest_costume_changes,
        validate_scene,
        generate_continuity_report_markdown,
        generate_continuity_report_html,

        # Bible
        CostumeBible,
        CharacterWardrobe,
        ShoppingItem,
        generate_costume_bible,
        generate_shopping_list,
        export_bible_yaml,
        export_bible_html,
        export_bible_pdf,
        generate_scene_breakdown_csv,
        generate_costume_summary_csv,

        # Storage
        load_wardrobe_from_yaml,
        save_wardrobe_to_yaml,
        load_character_wardrobe,
        load_wardrobe_from_directory,
        validate_yaml_structure,
        find_wardrobe_files,
    )

    # Create a costume
    costume = Costume(
        name="hero_casual",
        character="Hero",
        pieces=[
            CostumePiece(name="T-Shirt", category="top", color="navy", material="cotton"),
            CostumePiece(name="Jeans", category="bottom", color="blue", material="denim"),
        ],
        colors=["navy", "blue"],
    )

    # Manage costumes
    manager = CostumeManager(production_name="My Movie")
    manager.create_costume(costume)
    manager.assign_costume("Hero", 1, "hero_casual")

    # Validate continuity
    report = validate_continuity(manager.registry)

    # Generate costume bible
    bible = generate_costume_bible(manager.registry, "My Movie")
    export_bible_html(bible, "costume_bible.html")
"""

# Types
from .wardrobe_types import (
    # Enums
    CostumeCategory,
    CostumeStyle,
    CostumeCondition,
    ChangeReason,
    IssueType,
    IssueSeverity,
    # Dataclasses
    CostumePiece,
    Costume,
    CostumeChange,
    CostumeAssignment,
    WardrobeRegistry,
    # Constants and helpers
    CONDITION_PROGRESSION,
    is_valid_condition_progression,
)

# Manager
from .costume_manager import (
    CostumeManager,
    CostumeManagerError,
    CostumeNotFoundError,
    DuplicateCostumeError,
    InvalidAssignmentError,
)

# Validation
from .continuity_validator import (
    ContinuityIssue,
    ContinuityReport,
    validate_continuity,
    check_costume_consistency,
    check_condition_progression,
    suggest_costume_changes,
    validate_scene,
    generate_continuity_report_markdown,
    generate_continuity_report_html,
)

# Bible
from .costume_bible import (
    CostumeBible,
    CharacterWardrobe,
    ShoppingItem,
    generate_costume_bible,
    generate_shopping_list,
    export_bible_yaml,
    export_bible_html,
    export_bible_pdf,
    generate_scene_breakdown_csv,
    generate_costume_summary_csv,
)

# Storage
from .yaml_storage import (
    load_wardrobe_from_yaml,
    save_wardrobe_to_yaml,
    load_character_wardrobe,
    load_wardrobe_from_directory,
    validate_yaml_structure,
    find_wardrobe_files,
)

__all__ = [
    # Enums
    "CostumeCategory",
    "CostumeStyle",
    "CostumeCondition",
    "ChangeReason",
    "IssueType",
    "IssueSeverity",

    # Dataclasses - Types
    "CostumePiece",
    "Costume",
    "CostumeChange",
    "CostumeAssignment",
    "WardrobeRegistry",

    # Constants and helpers
    "CONDITION_PROGRESSION",
    "is_valid_condition_progression",

    # Manager
    "CostumeManager",
    "CostumeManagerError",
    "CostumeNotFoundError",
    "DuplicateCostumeError",
    "InvalidAssignmentError",

    # Validation
    "ContinuityIssue",
    "ContinuityReport",
    "validate_continuity",
    "check_costume_consistency",
    "check_condition_progression",
    "suggest_costume_changes",
    "validate_scene",
    "generate_continuity_report_markdown",
    "generate_continuity_report_html",

    # Bible
    "CostumeBible",
    "CharacterWardrobe",
    "ShoppingItem",
    "generate_costume_bible",
    "generate_shopping_list",
    "export_bible_yaml",
    "export_bible_html",
    "export_bible_pdf",
    "generate_scene_breakdown_csv",
    "generate_costume_summary_csv",

    # Storage
    "load_wardrobe_from_yaml",
    "save_wardrobe_to_yaml",
    "load_character_wardrobe",
    "load_wardrobe_from_directory",
    "validate_yaml_structure",
    "find_wardrobe_files",
]

__version__ = "0.1.0"
