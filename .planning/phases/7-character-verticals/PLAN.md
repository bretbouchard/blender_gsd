---
phase: 7-character-verticals
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - lib/characters/__init__.py
  - lib/characters/index.py
  - lib/characters/rig_library.py
  - lib/characters/types.py
  - lib/mecha/__init__.py
  - lib/mecha/parts_library.py
  - lib/mecha/assembly.py
  - lib/mecha/types.py
  - lib/character/__init__.py
  - configs/characters/rig_presets.yaml
  - configs/characters/character_index.yaml
  - configs/mecha/parts_index.yaml
  - configs/mecha/assembly_presets.yaml
autonomous: true

must_haves:
  truths:
    - "User can search all humanoid character assets"
    - "User can select and apply rig presets to characters"
    - "User can browse Vitaly Bulgarov mecha parts by category"
    - "User can assemble mecha from parts with constraints"
    - "Wardrobe system extends to character assignments"
  artifacts:
    - path: "lib/characters/index.py"
      provides: "Character asset indexing and search"
      exports: ["CharacterIndex", "CharacterAsset", "search_characters"]
      min_lines: 200
    - path: "lib/characters/rig_library.py"
      provides: "Rig template system"
      exports: ["RigLibrary", "RigPreset", "apply_rig"]
      min_lines: 250
    - path: "lib/mecha/parts_library.py"
      provides: "Mecha parts indexing"
      exports: ["MechaPartsLibrary", "PartCategory", "search_parts"]
      min_lines: 300
    - path: "lib/mecha/assembly.py"
      provides: "Mecha assembly system"
      exports: ["MechaAssembler", "AssemblyConfig", "assemble_mecha"]
      min_lines: 350
  key_links:
    - from: "lib/characters/index.py"
      to: "lib/asset_vault/"
      via: "uses asset vault for indexing"
      pattern: "from lib.asset_vault"
    - from: "lib/mecha/parts_library.py"
      to: "configs/mecha/parts_index.yaml"
      via: "loads parts configuration"
      pattern: "yaml.*parts_index"
    - from: "lib/character/wardrobe_types.py"
      to: "lib/characters/index.py"
      via: "extends for character assignments"
      pattern: "from lib.character"
---

<objective>
Create the Character & Verticals system that organizes and makes accessible all character, mecha, and vehicle parts assets. This phase provides indexing, rig library management, and assembly systems for combining modular parts.

Purpose: Enable rapid character and mecha creation by organizing existing assets (Vitaly Bulgarov packs, personal designs) into searchable, assemblable systems.
Output: Working character index, rig library, mecha parts library, and assembly system.
</objective>

<execution_context>
@/Users/bretbouchard/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bretbouchard/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/SCENE_GENERATION_MASTER_PLAN.md

# Existing character system
@lib/character/__init__.py
@lib/character/wardrobe_types.py

# Existing vehicle system (for parts patterns)
@lib/animation/vehicle/__init__.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Character Index System (REQ-CH-01)</name>
  <files>
    lib/characters/__init__.py
    lib/characters/types.py
    lib/characters/index.py
    configs/characters/character_index.yaml
  </files>
  <action>
    Create the characters module with indexing system for all humanoid assets.

    1. Create `lib/characters/types.py` with:
       - CharacterAsset dataclass (id, name, source_file, category, tags, dimensions, thumbnail)
       - CharacterCategory enum (hero, npc, creature, humanoid, robot)
       - CharacterMetadata dataclass (poly_count, materials, textures, rig_type)
       - IndexConfig dataclass (search_paths, categories, cache_path)

    2. Create `lib/characters/index.py` with:
       - CharacterIndex class with:
         - scan_directory(path: str) method to find character assets
         - index_asset(file_path: str) method to extract metadata
         - search(query: str, filters: dict) method for finding characters
         - get_by_id(asset_id: str) method to retrieve specific asset
         - refresh_index() method to update from source directories
       - Use existing lib/assets/ patterns if available, or create lightweight indexing
       - Support blend, fbx, obj file formats
       - Store index in SQLite at .gsd-state/characters/index.db

    3. Create `configs/characters/character_index.yaml` with:
       - Search paths for character assets
       - Category definitions
       - Tag hierarchies

    4. Create `lib/characters/__init__.py` with clean exports

    DO NOT use bpy.ops for file operations - use Path and direct bpy.data.libraries
    DO NOT create duplicate of existing lib/character/ wardrobe system - this is separate indexing
  </action>
  <verify>
    python -c "from lib.characters import CharacterIndex, CharacterAsset, search_characters; print('imports OK')"
    python -c "from lib.characters import CharacterCategory; print(list(CharacterCategory))"
  </verify>
  <done>
    Character index module imports correctly
    CharacterCategory enum has all required categories
    search_characters function signature defined
  </done>
</task>

<task type="auto">
  <name>Task 2: Rig Library System (REQ-CH-02)</name>
  <files>
    lib/characters/rig_library.py
    configs/characters/rig_presets.yaml
  </files>
  <action>
    Create rig template library for applying standard rigs to characters.

    1. Extend `lib/characters/types.py` with:
       - RigPreset dataclass (name, rig_type, bone_count, features, constraints)
       - RigType enum (biped, quadruped, face, custom, vehicle)
       - BoneDefinition dataclass (name, parent, head, tail, roll, constraints)

    2. Create `lib/characters/rig_library.py` with:
       - RigLibrary class with:
         - load_preset(name: str) method to load from YAML
         - list_presets(rig_type: RigType = None) method
         - apply_rig(armature: bpy.types.Object, preset: RigPreset) method
         - create_rig(preset: RigPreset) -> bpy.types.Object method
         - get_bone_hierarchy(preset: RigPreset) method
       - Presets stored in YAML, not hardcoded
       - Support for IK/FK switching metadata
       - Bone naming conventions for each rig type

    3. Create `configs/characters/rig_presets.yaml` with:
       - Standard biped rig (60+ bones, human skeleton)
       - Quadruped rig (40+ bones, dog/horse style)
       - Face rig template (50+ bones, expressions)
       - Simple rig (20 bones, basic posable)
       - Each preset includes:
         - bone_definitions: list of bone specs
         - ik_chains: list of IK chain configs
         - constraints: list of bone constraints
         - control_shapes: visual bone shapes

    DO NOT require actual armature creation - focus on preset storage and application
    DO use existing Blender armature API (bpy.data.armatures)
  </action>
  <verify>
    python -c "from lib.characters import RigLibrary, RigPreset, RigType; print('imports OK')"
    python -c "from lib.characters import RigLibrary; lib = RigLibrary(); print(lib.list_presets())"
  </verify>
  <done>
    RigLibrary imports and instantiates
    list_presets() returns available rig presets
    RigPreset dataclass has all required fields
  </done>
</task>

<task type="auto">
  <name>Task 3: Mecha Parts Library (REQ-CH-04)</name>
  <files>
    lib/mecha/__init__.py
    lib/mecha/types.py
    lib/mecha/parts_library.py
    configs/mecha/parts_index.yaml
  </files>
  <action>
    Create mecha/robot parts library for Vitaly Bulgarov assets and custom parts.

    1. Create `lib/mecha/types.py` with:
       - MechaPart dataclass (id, name, category, source_pack, file_path, scale, attachment_points)
       - PartCategory enum:
         - ARMOR (ULTRABORG Armor, plates)
         - MUSCLES (Cyber Muscles, pistons)
         - JOINTS (Pistons, Caps, hinges)
         - INTERNALS (Robo Guts, wires)
         - CABLES (Wires, Cables, hoses)
         - WEAPONS (Black Widow, Black Phoenix parts)
         - STRUCTURAL (Crates, Floor Panels, Megastructure)
         - PROPS (Sci-Fi Props, misc)
       - AttachmentPoint dataclass (name, position, rotation, compatible_slots)
       - SourcePack enum for Vitaly Bulgarov packs (ULTRABORG_ARMOR, ULTRABORG_MUSCLES, etc.)

    2. Create `lib/mecha/parts_library.py` with:
       - MechaPartsLibrary class with:
         - scan_packs(base_path: str) method to find all VB packs
         - index_part(file_path: str, pack: SourcePack) method
         - search(query: str, category: PartCategory = None) method
         - get_by_category(category: PartCategory) method
         - get_attachment_points(part_id: str) method
         - list_source_packs() method
       - Auto-detect category from file path patterns
       - Support blend file linking (not appending by default)

    3. Create `configs/mecha/parts_index.yaml` with:
       - Source pack configurations:
         ```yaml
         packs:
           ultraborg_armor:
             name: "ULTRABORG SUBD Armor Pack"
             path: "/Volumes/Storage/3d/animation/Vitaly Bulgarov/ULTRABORG SUBD Armor Pack"
             category: armor
             scale_factor: 1.0
           ultraborg_muscles:
             name: "ULTRABORG SUBD Cyber Muscles Pack"
             path: "/Volumes/Storage/3d/animation/Vitaly Bulgarov/ULTRABORG SUBD Cyber Muscles Pack"
             category: muscles
           black_widow:
             name: "Black Widow Pack"
             path: "/Volumes/Storage/3d/animation/Vitaly Bulgarov/Black Widow Pack"
             category: weapons
         ```
       - Attachment point definitions per part type

    4. Create `lib/mecha/__init__.py` with clean exports

    DO NOT hardcode full file paths in Python - use YAML configuration
    DO handle missing source directories gracefully with warnings
  </action>
  <verify>
    python -c "from lib.mecha import MechaPartsLibrary, MechaPart, PartCategory; print('imports OK')"
    python -c "from lib.mecha import PartCategory; print(list(PartCategory))"
  </verify>
  <done>
    Mecha module imports correctly
    PartCategory enum has all Vitaly Bulgarov categories
    MechaPartsLibrary can be instantiated
  </done>
</task>

<task type="auto">
  <name>Task 4: Mecha Assembly System (REQ-CH-06)</name>
  <files>
    lib/mecha/assembly.py
    configs/mecha/assembly_presets.yaml
  </files>
  <action>
    Create assembly system for combining mecha parts with constraints.

    1. Extend `lib/mecha/types.py` with:
       - AssemblyConfig dataclass (name, parts: List[PartPlacement], constraints)
       - PartPlacement dataclass (part_id, position, rotation, scale, parent_part)
       - AssemblyConstraint dataclass (type, from_part, to_part, offset)
       - ConstraintType enum (fixed, hinged, sliding, ball_joint)

    2. Create `lib/mecha/assembly.py` with:
       - MechaAssembler class with:
         - create_assembly(config: AssemblyConfig) -> bpy.types.Collection
         - add_part(assembly: Collection, part_id: str, placement: PartPlacement) method
         - connect_parts(assembly: Collection, constraint: AssemblyConstraint) method
         - validate_assembly(config: AssemblyConfig) -> List[str] method (returns errors)
         - save_assembly(assembly: Collection, path: str) method
         - load_assembly(path: str) -> AssemblyConfig method
       - Part placement uses attachment points when available
       - Constraints create actual Blender constraints (Copy Location, Copy Rotation)
       - Assembly output as Collection for organization

    3. Create `configs/mecha/assembly_presets.yaml` with:
       - Example assembly presets:
         ```yaml
         presets:
           basic_robot:
             name: "Basic Robot"
             description: "Simple humanoid robot assembly"
             parts:
               - part_id: "torso_armor_01"
                 placement: {position: [0, 0, 1.0]}
               - part_id: "shoulder_joint_l"
                 placement: {parent: "torso_armor_01", attachment_point: "left_shoulder"}
             constraints:
               - type: hinged
                 from_part: "shoulder_joint_l"
                 to_part: "torso_armor_01"
                 axis: "y"
         ```

    DO validate part compatibility before adding to assembly
    DO support both absolute and relative (attachment point) positioning
  </action>
  <verify>
    python -c "from lib.mecha import MechaAssembler, AssemblyConfig, PartPlacement; print('imports OK')"
    python -c "from lib.mecha import MechaAssembler; asm = MechaAssembler(); print(type(asm))"
  </verify>
  <done>
    MechaAssembler imports and instantiates
    AssemblyConfig dataclass has required fields
    PartPlacement supports parent-relative positioning
  </done>
</task>

<task type="auto">
  <name>Task 5: Vehicle Parts Integration (REQ-CH-05)</name>
  <files>
    lib/mecha/vehicle_parts.py
    configs/mecha/vehicle_parts.yaml
  </files>
  <action>
    Extend existing vehicle system with parts library integration for Launch Control and custom vehicle parts.

    1. Create `lib/mecha/vehicle_parts.py` with:
       - VehiclePart dataclass (id, name, category, source, compatible_chassis)
       - VehiclePartCategory enum (chassis, wheel, suspension, body, accessory, engine)
       - VehiclePartsIndex class with:
         - index_launch_control_parts(addon_path: str) method
         - index_custom_parts(path: str) method
         - search(query: str, category: VehiclePartCategory = None) method
         - get_compatible_parts(chassis_type: str) method
       - Integration with existing lib/animation/vehicle/ system

    2. Create `configs/mecha/vehicle_parts.yaml` with:
       - Launch Control v1.9.1 part categories
       - Custom vehicle parts paths
       - Chassis compatibility matrix

    3. Update `lib/mecha/__init__.py` to export vehicle parts

    DO NOT duplicate existing lib/animation/vehicle/ functionality
    DO provide bridge to existing vehicle system
  </action>
  <verify>
    python -c "from lib.mecha import VehiclePartsIndex, VehiclePartCategory; print('imports OK')"
    python -c "from lib.mecha import VehiclePartsIndex; idx = VehiclePartsIndex(); print(type(idx))"
  </verify>
  <done>
    VehiclePartsIndex imports and instantiates
    VehiclePartCategory has all required categories
    Integration with lib/animation/vehicle/ works
  </done>
</task>

<task type="auto">
  <name>Task 6: Wardrobe System Extension (REQ-CH-03)</name>
  <files>
    lib/characters/wardrobe_integration.py
    configs/characters/wardrobe_presets.yaml
  </files>
  <action>
    Extend existing wardrobe system (lib/character/) to work with character index.

    1. Create `lib/characters/wardrobe_integration.py` with:
       - CharacterWardrobeBridge class with:
         - assign_costume_to_character(character_id: str, costume: Costume) method
         - get_character_wardrobe(character_id: str) -> List[Costume] method
         - suggest_costumes(character: CharacterAsset) -> List[Costume] method
       - Uses existing lib/character/wardrobe_types.py types
       - Stores assignments in character metadata

    2. Create `configs/characters/wardrobe_presets.yaml` with:
       - Quick costume presets for common character types
       - Style-based wardrobe suggestions

    3. Update `lib/characters/__init__.py` to include wardrobe integration

    DO NOT duplicate wardrobe_types.py - import from lib.character
    DO maintain backward compatibility with existing wardrobe system
  </action>
  <verify>
    python -c "from lib.characters import CharacterWardrobeBridge; print('imports OK')"
    python -c "from lib.characters import CharacterWardrobeBridge; from lib.character import Costume; print('bridge + costume OK')"
  </verify>
  <done>
    CharacterWardrobeBridge imports correctly
    Integration with lib.character.Costume works
    Wardrobe presets load from YAML
  </done>
</task>

<task type="auto">
  <name>Task 7: Package Exports and Unit Tests</name>
  <files>
    lib/characters/__init__.py
    lib/mecha/__init__.py
    tests/unit/test_characters_index.py
    tests/unit/test_characters_rig_library.py
    tests/unit/test_mecha_parts.py
    tests/unit/test_mecha_assembly.py
  </files>
  <action>
    Create comprehensive package exports and unit tests for the character verticals system.

    1. Update `lib/characters/__init__.py` with all exports:
       - CharacterIndex, CharacterAsset, CharacterCategory, CharacterMetadata
       - RigLibrary, RigPreset, RigType, BoneDefinition
       - CharacterWardrobeBridge
       - search_characters convenience function
       - __version__ = "0.1.0"

    2. Update `lib/mecha/__init__.py` with all exports:
       - MechaPartsLibrary, MechaPart, PartCategory, SourcePack, AttachmentPoint
       - MechaAssembler, AssemblyConfig, PartPlacement, AssemblyConstraint, ConstraintType
       - VehiclePartsIndex, VehiclePart, VehiclePartCategory
       - __version__ = "0.1.0"

    3. Create `tests/unit/test_characters_index.py`:
       - test_character_asset_creation
       - test_character_category_enum
       - test_index_scan_directory
       - test_index_search

    4. Create `tests/unit/test_characters_rig_library.py`:
       - test_rig_preset_creation
       - test_rig_type_enum
       - test_rig_library_list_presets
       - test_rig_library_load_preset

    5. Create `tests/unit/test_mecha_parts.py`:
       - test_mecha_part_creation
       - test_part_category_enum
       - test_parts_library_search
       - test_attachment_points

    6. Create `tests/unit/test_mecha_assembly.py`:
       - test_assembly_config_creation
       - test_part_placement_relative
       - test_assembly_constraint_types
       - test_assembler_validate

    All tests should pass without Blender context (mock bpy where needed)
    Minimum 80% code coverage target
  </action>
  <verify>
    python -m pytest tests/unit/test_characters_index.py -v --tb=short
    python -m pytest tests/unit/test_mecha_parts.py -v --tb=short
    python -c "from lib.characters import *; print(f'{len([x for x in dir() if not x.startswith(\"_\")])} exports')"
    python -c "from lib.mecha import *; print(f'{len([x for x in dir() if not x.startswith(\"_\")])} exports')"
  </verify>
  <done>
    All unit tests pass
    lib.characters exports 15+ items
    lib.mecha exports 15+ items
    Both modules have version strings
  </done>
</task>

</tasks>

<verification>
Overall phase verification:

1. **Character Index**: `python -c "from lib.characters import CharacterIndex; idx = CharacterIndex(); print('index OK')"`
2. **Rig Library**: `python -c "from lib.characters import RigLibrary; lib = RigLibrary(); print(lib.list_presets())"`
3. **Mecha Parts**: `python -c "from lib.mecha import MechaPartsLibrary; lib = MechaPartsLibrary(); print('parts OK')"`
4. **Assembly**: `python -c "from lib.mecha import MechaAssembler; asm = MechaAssembler(); print('assembler OK')"`
5. **All Tests**: `python -m pytest tests/unit/test_characters*.py tests/unit/test_mecha*.py -v`
</verification>

<success_criteria>
Phase 7 complete when:

- [ ] Character index system scans and indexes humanoid assets
- [ ] Rig library provides standard rig presets (biped, quadruped, face)
- [ ] Mecha parts library indexes Vitaly Bulgarov packs by category
- [ ] Assembly system combines parts with attachment point constraints
- [ ] Vehicle parts integrate with existing lib/animation/vehicle/
- [ ] Wardrobe system extended to work with character index
- [ ] All unit tests pass (80%+ coverage)
- [ ] Package exports clean and documented
- [ ] Version bumped to 0.5.0 (Scene Generation milestone)

</success_criteria>

<output>
After completion, create `.planning/phases/7-character-verticals/7-SUMMARY.md` documenting:

1. Modules created (lib/characters/, lib/mecha/)
2. Total exports from each module
3. Configuration files created
4. Test coverage achieved
5. Integration points with existing systems (lib/character/, lib/animation/vehicle/)
6. Known limitations or future work
</output>
