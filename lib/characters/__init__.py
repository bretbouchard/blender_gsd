"""
Characters Module

Character asset management, rigging, and animation support.
Extends existing wardrobe system with character indexing and rig library.

Implements REQ-CH-01: Character Asset Index.
Implements REQ-CH-02: Rig Library.
Implements REQ-CH-03: Costume/Wardrobe System Extension.

Features:
- Character asset index (humanoid, creatures, NPCs)
- Rig library (biped, quadruped, face rigs)
- Integration with existing wardrobe system
- Blend shape/morph target support
- Animation clip library

Usage:
    from lib.characters import CharacterIndex, RigLibrary

    # Search for characters
    index = CharacterIndex()
    characters = index.search(role="hero", style="realistic")

    # Get rig template
    library = RigLibrary()
    biped = library.get_rig("human_biped")

    # Extend wardrobe (uses existing character/ module)
    from lib.character import CostumeManager, Costume
"""

from __future__ import annotations

__all__ = [
    # Enums
    "CharacterType",
    "CharacterRole",
    "RigType",
    "RigComplexity",
    # Data classes
    "CharacterSpec",
    "RigSpec",
    "BoneSpec",
    "FaceRigConfig",
    # Constants
    "STANDARD_BONE_NAMES",
    "FACE_RIG_BONES",
    "RIG_PRESETS",
    # Classes
    "CharacterIndex",
    "RigLibrary",
    # Functions
    "create_character_index",
    "load_rig_template",
]

__version__ = "1.0.0"
__author__ = "Blender GSD Project"


from .index import (
    # Enums
    CharacterType,
    CharacterRole,
    # Data classes
    CharacterSpec,
    # Classes
    CharacterIndex,
    # Functions
    create_character_index,
)

from .rig_library import (
    # Enums
    RigType,
    RigComplexity,
    # Data classes
    RigSpec,
    BoneSpec,
    FaceRigConfig,
    # Constants
    STANDARD_BONE_NAMES,
    FACE_RIG_BONES,
    RIG_PRESETS,
    # Classes
    RigLibrary,
    # Functions
    load_rig_template,
)
