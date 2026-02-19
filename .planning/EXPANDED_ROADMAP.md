# Expanded Production System Roadmap
## From Cinematic Renders to Full Movie Production

**Version**: 2.0
**Status**: Planning
**Created**: 2026-02-18
**Related**: FULL_PRODUCTION_SYSTEM.md, REQUIREMENTS_RETRO_GRAPHICS.md

---

## Vision: One-Shot Production

**The Goal**: If you know all the answers ahead of time, you can generate an entire movie in one command.

**Input**:
- Script/Story (text or structured)
- Characters (descriptions, references)
- Locations (requirements, presets)
- Style Target (Hollywood → 8-bit, anywhere between)

**Output**:
- Complete rendered footage
- Characters with costumes, animation
- All environments, lighting, cameras
- Post-processing (including retro bit-crunch)
- Organized for editorial

---

## Production Phases Overview

```
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 6.x: CORE CINEMATIC                       │
│  Camera, Lighting, Rendering, Shots, Animation                 │
│  Status: 6.0 ✅ | 6.1 ✅ | 6.2-6.15 🔄                          │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 7.x: MOTION & TRACKING                    │
│  Object Tracking, Camera Tracking, Follow Camera               │
│  Status: Planning                                               │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 8.x: DEVELOPMENT                          │
│  Script Parser, Character Extractor, Shot List Generator       │
│  Story State Manager, Visual Style Director                    │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 9.x: ART & LOCATIONS                      │
│  Set Builder, Prop Library, Location Manager                   │
│  Environment Generator, Concept Art System                     │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 10.x: CHARACTER                           │
│  Wardrobe System, Costume Tracking, Hair/Makeup                │
│  Character State Manager, Aging/Injury Progression             │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 11.x: SOUND & EDITORIAL                   │
│  Timeline System, Cut List, Sound Design                       │
│  Music Sync, Foley Generator, Dialogue Processing              │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 12.x: VFX & COMPOSITING                   │
│  Compositor, CG Integration, FX Simulation                     │
│  Matte Generation, Rotoscoping, Match Moving                   │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 13.x: RETRO & STYLIZED                    │
│  Pixel Converter, Dither Engine, Isometric Views               │
│  Side-Scroller, CRT Effects, Sprite Sheets                     │
│  "Hollywood to Double Dragon" Pipeline                         │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 PHASE 14.x: ONE-SHOT ORCHESTRATION              │
│  Production Orchestrator, Master Config                         │
│  "One command = entire movie"                                   │
└────────────────────────────────────────────────────────────────┘
```

---

## Phase 6.x: Core Cinematic (IN PROGRESS)

### Completed Phases

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 6.0 | Foundation | ✅ COMPLETE | types.py, state_manager.py, config dirs |
| 6.1 | Camera System | ✅ COMPLETE | camera.py, lenses.py, plumb_bob.py, rigs.py, preset_loader.py |

### Remaining Phases (Planned)

| Phase | Name | Priority | Key Deliverables |
|-------|------|----------|------------------|
| 6.2 | Motion Tracking | P0 | Object tracking, camera tracking |
| 6.3 | Follow Camera | P0 | Subject following, look-ahead |
| 6.4 | Lighting System | P0 | Light rigs, HDRI, gels |
| 6.5 | Render System | P0 | Quality profiles, passes, batch |
| 6.6 | Shot Assembly | P0 | Complete shot from YAML |
| 6.7 | Backdrop System | P1 | Infinite curves, gradients |
| 6.8 | Color Pipeline | P1 | LUTs, color management |
| 6.9 | Animation System | P1 | Camera moves, turntable |
| 6.10 | Template System | P1 | Inheritance, overrides |
| 6.11 | Lens Imperfections | P2 | Compositor effects |
| 6.12 | Support Systems | P2 | Shuffler, frame store, depth layers |
| 6.13 | Catalog Generator | P1 | Screenshot automation, GLTF export |

---

## Phase 7.x: Motion & Tracking

### Phase 7.1: Object Tracking
**Priority**: P0 | **Est. Effort**: 3-4 days

**Goal**: Track objects through frame for automated follow-focus and camera moves.

**Deliverables**:
```
lib/cinematic/
└── tracking.py                  # Object tracking, markers

features:
- create_tracking_marker(object, frame_start, frame_end)
- solve_object_motion(marker_data)
- apply_tracking_to_camera(tracking_data, camera)
- export_tracking_data(format)  # AE, Nuke, Blender
```

### Phase 7.2: Camera Tracking
**Priority**: P0 | **Est. Effort**: 4-5 days

**Goal**: Reconstruct camera motion from footage for VFX integration.

**Deliverables**:
```
lib/cinematic/
└── camera_solve.py              # Camera reconstruction

features:
- import_footage(path)
- detect_features(footage)
- solve_camera_motion(features)
- create_camera_from_solve(solve_data)
- set_ground_plane(solve_data, points)
```

### Phase 7.3: Follow Camera
**Priority**: P0 | **Est. Effort**: 3-4 days

**Goal**: Camera that automatically follows subjects with natural movement.

**Deliverables**:
```
lib/cinematic/
└── follow_camera.py             # Intelligent subject following

features:
- create_follow_rig(subject, config)
- set_follow_mode(mode)  # tight, loose, anticipatory
- configure_look_ahead(frames)
- set_obstacle_avoidance(enabled)
- add_dead_zone(area)  # Don't move if subject in zone
- apply_smoothing(amount)
```

---

## Phase 8.x: Development Department

### Phase 8.1: Script Parser
**Priority**: P1 | **Est. Effort**: 5-6 days

**Goal**: Parse screenplay/teleplay formats into structured data.

**Deliverables**:
```
lib/development/
├── __init__.py
├── script_parser.py             # Parse scripts
├── fountain_parser.py           # Fountain format
└── script_types.py              # Script data structures

features:
- parse_fountain(text) → Script
- parse_fdx(file) → Script  # Final Draft
- extract_scenes(script) → List[Scene]
- extract_characters(script) → List[Character]
- extract_dialogue(script) → List[DialogueLine]
- extract_action(script) → List[ActionBlock]
- generate_beatsheet(script) → BeatSheet
```

**Data Structures**:
```python
@dataclass
class Script:
    title: str
    author: str
    scenes: List[Scene]
    characters: List[Character]
    locations: List[Location]
    total_pages: float
    estimated_runtime: float  # minutes

@dataclass
class Scene:
    number: int
    heading: str  # "INT. WAREHOUSE - NIGHT"
    location: str
    time_of_day: str  # DAY, NIGHT, DAWN, DUSK, CONTINUOUS
    action: List[ActionBlock]
    dialogue: List[DialogueLine]
    transitions: List[Transition]
    page_start: float
    page_end: float

@dataclass
class Character:
    name: str
    aliases: List[str]  # (V.O.), (O.S.), etc.
    dialogue_count: int
    first_appearance: int  # scene number
    last_appearance: int
```

### Phase 8.2: Shot List Generator
**Priority**: P1 | **Est. Effort**: 4-5 days

**Goal**: Automatically generate shot lists from parsed scripts.

**Deliverables**:
```
lib/development/
└── shot_list_generator.py       # Generate shots from script

features:
- generate_shot_list(scene) → List[ShotConfig]
- estimate_coverage(scene) → CoverageEstimate
- suggest_shot_sizes(scene) → List[ShotSizeSuggestion]
- generate_storyboard_prompts(scene) → List[str]
```

### Phase 8.3: Visual Style Director
**Priority**: P1 | **Est. Effort**: 3-4 days

**Goal**: Define and apply visual style across entire production.

**Deliverables**:
```
lib/development/
└── style_director.py            # Visual style system

features:
- create_style_preset(name, config) → StylePreset
- apply_style_to_scene(style, scene) → SceneStyle
- generate_color_palette(mood, era) → ColorPalette
- create_look_book(style) → LookBook  # Reference images
```

---

## Phase 9.x: Art & Locations

### Phase 9.1: Set Builder
**Priority**: P1 | **Est. Effort**: 5-6 days

**Goal**: Procedural set construction from specifications.

**Deliverables**:
```
lib/art/
├── __init__.py
├── set_builder.py               # Build sets
├── props.py                     # Prop placement
└── dressing.py                  # Set dressing

features:
- create_set_from_spec(spec) → Set
- add_wall(room, position, config)
- add_door(wall, position, style)
- add_window(wall, position, style)
- populate_with_props(set, prop_list)
- apply_dressing_style(set, style)
```

### Phase 9.2: Location Manager
**Priority**: P1 | **Est. Effort**: 3-4 days

**Goal**: Manage physical and virtual locations.

**Deliverables**:
```
lib/art/
└── location_manager.py          # Location system

features:
- create_location(config) → Location
- calculate_sun_path(location, date) → SunPath
- generate_environment(location, time) → EnvironmentConfig
- match_to_reference(image) → LocationMatch
```

---

## Phase 10.x: Character Department

### Phase 10.1: Wardrobe System
**Priority**: P1 | **Est. Effort**: 4-5 days

**Goal**: Track costumes across all scenes.

**Deliverables**:
```
lib/character/
├── __init__.py
├── wardrobe.py                  # Costume management
├── costume_tracker.py           # Scene-by-scene tracking
└── character_state.py           # Character appearance state

features:
- create_costume(config) → Costume
- assign_costume_to_scene(character, scene, costume)
- track_costume_changes(script) → List[CostumeChange]
- validate_continuity(character) → ContinuityReport
- generate_costume_bible() → CostumeBible
```

**Data Structures**:
```python
@dataclass
class Costume:
    name: str
    pieces: List[CostumePiece]
    colors: List[str]
    materials: List[str]
    condition: str  # pristine, worn, dirty, damaged, bloodied
    accessories: List[Accessory]

@dataclass
class CostumeChange:
    character: str
    scene_before: int
    scene_after: int
    costume_before: Costume
    costume_after: Costume
    reason: str  # "story", "time", "damage", "location"
```

### Phase 10.2: Character State Manager
**Priority**: P1 | **Est. Effort**: 3-4 days

**Goal**: Track character state across timeline.

**Deliverables**:
```
lib/character/
└── character_state.py           # State tracking

features:
- track_aging(character, timeline) → AgingCurve
- track_injuries(character, events) → InjuryProgression
- track_hairstyle(character, scenes) → HairstyleChanges
- generate_continuity_report() → ContinuityReport
```

---

## Phase 11.x: Sound & Editorial

### Phase 11.1: Timeline System
**Priority**: P1 | **Est. Effort**: 4-5 days

**Goal**: Edit decision list and timeline management.

**Deliverables**:
```
lib/editorial/
├── __init__.py
├── timeline.py                  # Timeline management
├── cut_list.py                  # Edit decisions
└── conform.py                   # Final assembly

features:
- create_timeline(config) → Timeline
- add_clip(timeline, shot, position)
- create_cut(from_shot, to_shot, transition)
- generate_edl(timeline) → EDL
- generate_xml(timeline) → FCPXML
- calculate_runtime(timeline) → float
```

### Phase 11.2: Sound Design
**Priority**: P2 | **Est. Effort**: 4-5 days

**Goal**: Automated sound design system.

**Deliverables**:
```
lib/sound/
├── __init__.py
├── sound_design.py              # Sound effects
├── foley.py                     # Foley generation
└── ambience.py                  # Ambient sound

features:
- generate_foley(action, surface) → FoleySound
- create_ambience(location, time) → AmbienceTrack
- auto_duck_music(dialogue, music) → MixedTrack
- generate_room_tone(location) → RoomTone
```

---

## Phase 12.x: VFX & Compositing

### Phase 12.1: Compositor
**Priority**: P1 | **Est. Effort**: 5-6 days

**Goal**: Multi-layer compositing system.

**Deliverables**:
```
lib/vfx/
├── __init__.py
├── compositor.py                # Layer compositing
├── matte.py                     # Matte generation
└── roto.py                      # Rotoscoping

features:
- create_comp(config) → Composite
- add_layer(comp, render_pass, blend_mode)
- apply_matte(layer, matte_type)
- color_correct_layer(layer, cc_data)
- generate_cryptomatte(objects) → Cryptomatte
```

---

## Phase 13.x: Retro & Stylized Graphics

### Phase 13.1: Pixel Converter
**Priority**: P0 | **Est. Effort**: 3-4 days

**Goal**: Convert photorealistic renders to pixel art.

**Deliverables**:
```
lib/retro/
├── __init__.py
├── pixelator.py                 # Pixel conversion
├── palettes.py                  # Color palettes
└── quantizer.py                 # Color reduction

features:
- pixelate(image, config) → Image
- quantize_colors(image, palette) → Image
- apply_palette(image, palette_name) → Image
- create_custom_palette(image, color_count) → Palette
```

### Phase 13.2: Dither Engine
**Priority**: P0 | **Est. Effort**: 3-4 days

**Goal**: Professional dithering for color-limited output.

**Deliverables**:
```
lib/retro/
└── dither.py                    # Dithering algorithms

features:
- dither_ordered(image, pattern) → Image  # Bayer, etc.
- dither_error_diffusion(image, algorithm) → Image  # Floyd-Steinberg
- dither_atkinson(image) → Image  # Macintosh style
- apply_custom_pattern(image, pattern_file) → Image
```

### Phase 13.3: Isometric & Side-Scroller
**Priority**: P1 | **Est. Effort**: 4-5 days

**Goal**: Generate game-ready graphics from 3D scenes.

**Deliverables**:
```
lib/retro/
├── isometric.py                 # Isometric projection
├── side_scroller.py             # Side-scrolling view
└── sprites.py                   # Sprite sheet generation

features:
- create_isometric_camera(angle) → CameraConfig
- render_isometric_tile(scene) → Image
- create_parallax_layers(scene) → List[Image]
- generate_sprite_sheet(animation) → (Image, JSON)
- export_for_engine(sprites, engine) → ExportedAssets
```

### Phase 13.4: CRT & Display Effects
**Priority**: P2 | **Est. Effort**: 3-4 days

**Goal**: Authentic retro display simulation.

**Deliverables**:
```
lib/retro/
└── crt_effects.py               # Display simulation

features:
- apply_scanlines(image, config) → Image
- apply_phosphor_mask(image, pattern) → Image
- apply_screen_curvature(image, amount) → Image
- create_crt_preset(preset_name) → CRTEffectConfig
- combine_crt_effects(image, presets) → Image
```

---

## Phase 14.x: One-Shot Orchestration

### Phase 14.1: Production Orchestrator
**Priority**: P0 | **Est. Effort**: 5-6 days

**Goal**: Single command to execute entire production.

**Deliverables**:
```
lib/production/
├── __init__.py
├── orchestrator.py              # Main orchestration
├── production_config.py         # Master config
└── render_queue.py              # Render management

features:
- load_production(yaml_path) → ProductionConfig
- validate_production(config) → ValidationResult
- execute_production(config) → ProductionResult
- render_all_shots(config) → List[RenderResult]
- assemble_final(config) → FinalOutput
```

### Phase 14.2: Master Production Config
**Priority**: P0 | **Est. Effort**: 3-4 days

**Goal**: Single file that defines entire production.

**Example**:
```yaml
production:
  title: "My Short Film"
  version: "1.0"

  # Source material
  script: "scripts/my_film.fountain"

  # Visual style
  style:
    look: "cinematic_teal_orange"
    era: "present_day"
    mood: "dramatic"

  # Output targets
  outputs:
    - format: "cinema_4k"
      codec: "prores_4444"
    - format: "streaming_1080p"
      codec: "h265"
    - format: "16bit_game"
      retro:
        palette: "snes"
        dither: "error_diffusion"
        resolution: [320, 180]

  # Characters
  characters:
    - name: "Hero"
      model: "characters/hero.blend"
      wardrobe:
        scene_1_5: "casual"
        scene_6_10: "formal"

  # Locations
  locations:
    - name: "Warehouse"
      type: "hdri"
      hdri: "abandoned_warehouse_4k"
```

---

## Data Structures Summary

### Master Types

```python
@dataclass
class Production:
    """Complete production specification."""
    meta: ProductionMeta
    development: DevelopmentDepartment
    art: ArtDepartment
    characters: CharacterDepartment
    camera: CameraDepartment
    lighting: LightingDepartment
    sound: SoundDepartment
    editorial: EditorialDepartment
    vfx: VFXDepartment
    retro: Optional[RetroConfig]

    def execute(self) -> ProductionResult:
        """One command to render everything."""
        pass

@dataclass
class Character:
    """Complete character with tracking."""
    name: str
    model_ref: str  # Path to model
    wardrobe: Dict[SceneRange, Costume]
    aging: Optional[AgingCurve]
    injuries: List[InjuryEvent]
    hairstyles: Dict[SceneRange, Hairstyle]
    screen_time: float

    def get_appearance_for_scene(self, scene: int) -> CharacterAppearance:
        """Get complete appearance for any scene."""
        pass

@dataclass
class Shot:
    """Complete shot with all departments."""
    name: str
    scene: int
    take: int

    # Department configs
    camera: CameraConfig
    lighting: LightingConfig
    backdrop: BackdropConfig
    characters: List[CharacterPlacement]
    props: List[PropPlacement]
    sound: SoundConfig
    vfx: Optional[VFXConfig]
    retro: Optional[RetroConfig]

    def render(self) -> RenderResult:
        """Render this shot."""
        pass
```

---

## Implementation Priority

### Now (Phases 6.x-7.x)
- Complete core cinematic system
- Add motion tracking
- Implement follow camera

### Next (Phases 8.x-10.x)
- Script parsing
- Character/wardrobe tracking
- Set/location management

### Then (Phases 11.x-12.x)
- Sound/editorial
- VFX/compositing

### Finally (Phases 13.x-14.x)
- Retro graphics pipeline
- One-shot orchestration

---

## Success Metrics

**Phase 6.x (Core)**: Single YAML → Single render
**Phase 8.x (Development)**: Script → Shot list → Renders
**Phase 10.x (Characters)**: Characters track through all scenes
**Phase 12.x (VFX)**: Multi-layer compositing works
**Phase 13.x (Retro)**: Same scene renders in 10+ visual styles
**Phase 14.x (One-Shot)**: Production YAML → Complete movie

---

*This roadmap extends the cinematic system to full production capabilities.*
