# Full Production System Architecture
## One-Shot Movie Production: From Hollywood to Double Dragon

This document maps out the complete film production system - every department, role, and capability needed to generate entire productions from specifications.

---

## 🎬 The Vision: One-Shot Production

**Goal**: If you know all the answers ahead of time, you should be able to generate an entire movie in one command.

**Input**:
- Script/Story beats
- Character descriptions
- Location requirements
- Shot list (or auto-generated)
- Style references (Hollywood → 8-bit, anywhere in between)

**Output**:
- Complete rendered footage
- Character models, costumes, animations
- All environments, lighting, cameras
- Post-processing (color grade, bit-crunch, etc.)

---

## 🏢 Film Production Departments

### 1. DEVELOPMENT DEPARTMENT
**Purpose**: Story, script, creative vision

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Producer** | Overall vision, budget, schedule | Production Orchestrator |
| **Writer** | Script, dialogue, story beats | Script Parser |
| **Script Doctor** | Refine dialogue, pacing | Dialogue Optimizer |
| **Story Editor** | Continuity, arc consistency | Story State Manager |
| **Creative Director** | Visual style, tone | Style Preset System |

**Data Structures Needed**:
```
Script {
    acts: List[Act]
    scenes: List[Scene]
    characters: List[Character]
    locations: List[Location]
    timeline: Timeline
}
```

---

### 2. PRE-VISUALIZATION DEPARTMENT
**Purpose**: Plan every shot before production

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Previs Supervisor** | Overall previs quality | Previs Orchestrator |
| **Previs Artist** | Block scenes, camera moves | Shot Blocker |
| **Story Artist** | Storyboards | Storyboard Generator |
| **Animatic Editor** | Timing, pacing | Animatic Builder |

**Data Structures Needed**:
```
Previs {
    storyboards: List[StoryboardFrame]
    animatic: VideoSequence
    camera_blocking: List[CameraMove]
    timing: TimingSheet
}
```

---

### 3. ART DEPARTMENT
**Purpose**: Visual design of everything on screen

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Production Designer** | Overall visual concept | Design Director |
| **Art Director** | Sets, props, dressings | Asset Coordinator |
| **Set Designer** | Build physical structures | Set Builder |
| **Prop Master** | All hand props | Prop Library |
| **Set Decorator** | Dress the sets | Scene Populator |
| **Concept Artist** | Visual development | Concept Generator |
| **Graphic Designer** | On-screen graphics | Screen Graphics |

**Data Structures Needed**:
```
ArtDepartment {
    concept_art: List[Image]
    set_designs: List[SetDesign]
    props: List[Prop]
    dressings: List[Dressing]
    graphics: List[ScreenGraphic]
}
```

---

### 4. CAMERA DEPARTMENT ✅ (PARTIALLY BUILT)
**Purpose**: Capture the image

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Director of Photography** | Visual look, lighting | Shot Config System |
| **Camera Operator** | Frame and move camera | Camera Controller |
| **1st AC** | Focus, lens changes | Focus Puller |
| **2nd AC** | Camera prep, media | Camera Setup |
| **DIT** | Data management, looks | Render Settings |
| **Steadicam Op** | Smooth camera moves | Stabilization System |
| **Drone Operator** | Aerial shots | Aerial Rig |

**Already Built**:
- ✅ CameraConfig
- ✅ PlumbBobConfig (targeting)
- ✅ RigConfig (dolly, crane, steadicam)
- ✅ Lens presets
- ✅ Composition rules

**Still Needed**:
- ❌ Camera movement paths
- ❌ Multi-camera sync
- ❌ Focus pull automation

---

### 5. GRIP DEPARTMENT
**Purpose**: Camera support and movement

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Key Grip** | Rigging supervision | Grip Supervisor |
| **Best Boy Grip** | Equipment management | Equipment Tracker |
| **Dolly Grip** | Camera dolly movement | Dolly Controller |
| **Rigging Grip** | Mount cameras anywhere | Rig Builder |

**Data Structures Needed**:
```
GripDepartment {
    dollies: List[Dolly]
    cranes: List[Crane]
    stabilizers: List[Stabilizer]
    mounts: List[Mount]
    tracks: List[Track]
}
```

---

### 6. ELECTRICAL DEPARTMENT ✅ (PARTIALLY BUILT)
**Purpose**: Power and lighting power distribution

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Gaffer** | Lighting design execution | Lighting Director |
| **Best Boy Electric** | Equipment, scheduling | Equipment Manager |
| **Electrician** | Set lights | Light Placer |
| **Generator Operator** | Power | Power System |

**Already Built**:
- ✅ LightConfig
- ✅ LightRigConfig
- ✅ Lighting presets
- ✅ GelConfig

---

### 7. LIGHTING DEPARTMENT ✅ (PARTIALLY BUILT)
**Purpose**: Shape light for mood and story

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Gaffer** | Overall lighting | Light Director |
| **Lighting Designer** | Design light plots | Light Plot Generator |
| **Board Operator** | Control dimmers | Light Controller |
| **Rigging Electrician** | Hang and focus | Light Rigger |

**Already Built**:
- ✅ Three-point lighting
- ✅ Area lights, spots, HDRIs
- ✅ Lighting ratios
- ✅ Gels and diffusion

**Still Needed**:
- ❌ Practical lights (in-scene lamps, etc.)
- ❌ Light animation (day to night)
- ❌ Volumetric lighting presets

---

### 8. WARDROBE DEPARTMENT
**Purpose**: Character costumes

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Costume Designer** | Overall costume look | Wardrobe Director |
| **Costume Supervisor** | Manage costume crew | Wardrobe Manager |
| **Costume Maker** | Build costumes | Costume Generator |
| **Costume Buyer** | Source items | Asset Finder |
| **Dresser** | Help actors dress | Dressing System |
| **Costume Illustrator** | Costume concepts | Concept Generator |

**Data Structures Needed**:
```
WardrobeDepartment {
    costumes: List[Costume]
    costume_changes: List[CostumeChange]
    accessories: List[Accessory]
    fabrics: List[Fabric]
    color_palette: ColorPalette
}

Costume {
    character: CharacterID
    scene_range: SceneRange
    pieces: List[CostumePiece]
    materials: List[Material]
    colors: List[Color]
    condition: str  # pristine, worn, dirty, damaged
}
```

---

### 9. HAIR & MAKEUP DEPARTMENT
**Purpose**: Character appearance

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Makeup Designer** | Overall makeup looks | Makeup Director |
| **Key Makeup Artist** | Apply makeup | Makeup Applier |
| **Hair Stylist** | Character hair | Hair Styler |
| **Prosthetics Artist** | Special effects makeup | Prosthetic Builder |
| **Body Painter** | Full body makeup | Body Painter |

**Data Structures Needed**:
```
MakeupDepartment {
    makeup_designs: List[MakeupDesign]
    hair_styles: List[HairStyle]
    prosthetics: List[Prosthetic]
    aging_effects: List[AgingEffect]
}
```

---

### 10. LOCATION DEPARTMENT
**Purpose**: Find, secure, manage locations

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Location Manager** | Find and secure locations | Location Director |
| **Location Scout** | Search for locations | Location Finder |
| **Assistant Location Manager** | Logistics | Location Coordinator |
| **Site Rep** | Location liaison | Site Handler |

**Data Structures Needed**:
```
LocationDepartment {
    locations: List[Location]
    scouts: List[ScoutReport]
    permits: List[Permit]
    logistics: List[Logistics]
}

Location {
    name: str
    type: str  # studio, practical, vfx_extension
    address: str
    gps: GPSCoords
    time_zone: str
    sun_path: SunPath
    weather_patterns: WeatherData
    interior: bool
    features: List[Feature]
    restrictions: List[Restriction]
}
```

---

### 11. PRODUCTION DEPARTMENT
**Purpose**: Schedule and coordinate

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Line Producer** | Budget and schedule | Production Manager |
| **Unit Production Manager** | Day-to-day operations | Operations Manager |
| **Production Coordinator** | Communication hub | Coordinator |
| **1st AD** | Set control, schedule | Schedule Manager |
| **2nd AD** | Call sheets, background | Call Sheet Generator |
| **Script Supervisor** | Continuity | Continuity Tracker |

**Data Structures Needed**:
```
ProductionDepartment {
    schedule: ProductionSchedule
    budget: Budget
    call_sheets: List[CallSheet]
    day_out_of_days: DayOutOfDays
    production_report: ProductionReport
}
```

---

### 12. SOUND DEPARTMENT
**Purpose**: Production sound recording

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Production Sound Mixer** | Overall sound | Sound Director |
| **Boom Operator** | Capture dialogue | Boom Positioner |
| **Sound Utility** | Cables, wireless | Audio Router |

**Data Structures Needed**:
```
SoundDepartment {
    dialogue: List[DialogueTrack]
    ambience: List[AmbienceTrack]
    foley: List[FoleyTrack]
    room_tone: List[RoomTone]
}
```

---

### 13. VFX DEPARTMENT
**Purpose**: Visual effects

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **VFX Supervisor** | Overall VFX | VFX Director |
| **VFX Producer** | Budget, schedule | VFX Manager |
| **Compositor** | Combine elements | Compositor |
| **CG Supervisor** | 3D elements | CG Director |
| **FX Artist** | Simulations | FX Simulator |
| **Matte Painter** | Environments | Matte Generator |
| **Roto Artist** | Isolation | Roto System |
| **Matchmover** | Camera tracking | Camera Tracker |

**Data Structures Needed**:
```
VFXDepartment {
    shots: List[VFXShot]
    elements: List[VFXElement]
    renders: List[Render]
    comps: List[Composite]
}
```

---

### 14. EDITORIAL DEPARTMENT
**Purpose**: Assemble the final cut

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Editor** | Assemble footage | Edit System |
| **Assistant Editor** | Organize, sync | Media Manager |
| **Online Editor** | Final conform | Conform System |
| **Colorist** | Color grade | Color System |

**Data Structures Needed**:
```
EditorialDepartment {
    timeline: Timeline
    cuts: List[Cut]
    transitions: List[Transition]
    color_grade: ColorGrade
}
```

---

### 15. POST-PRODUCTION SOUND
**Purpose**: Final soundtrack

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Supervising Sound Editor** | Overall sound design | Sound Director |
| **Dialogue Editor** | Clean dialogue | Dialogue Processor |
| **Sound Designer** | Create sounds | Sound Designer |
| **Re-Recording Mixer** | Final mix | Mixer |
| **Music Editor** | Music sync | Music Editor |
| **Composer** | Original score | Score Generator |

**Data Structures Needed**:
```
PostSoundDepartment {
    dialogue: DialogueMix
    sfx: SFXMix
    music: MusicMix
    ambience: AmbienceMix
    final_mix: FinalMix
}
```

---

## 🎮 NEW: RETRO/STYLIZED GRAPHICS DEPARTMENT
**Purpose**: Non-photorealistic rendering - Hollywood to Double Dragon

| Role | Responsibility | System Equivalent |
|------|---------------|-------------------|
| **Style Director** | Overall visual style | Style Orchestrator |
| **Pixel Artist** | 8/16-bit graphics | Pixel Converter |
| **Quantizer** | Color reduction | Color Quantizer |
| **Ditherer** | Retro dither patterns | Dither Engine |
| **Scanline Artist** | CRT effects | Scanline System |
| **Isometric Designer** | Isometric views | Iso Converter |
| **Sprite Animator** | Sprite sheets | Sprite System |

**Data Structures Needed**:
```
RetroDepartment {
    pixel_style: PixelStyle
    color_depth: int  # 2, 4, 8, 16, 256 colors
    resolution: Resolution  # native output res
    dither_pattern: DitherPattern
    scanlines: ScanlineConfig
    crt_effects: CRTEffects
    palette: ColorPalette
}

PixelStyle {
    mode: str  # "photorealistic", "stylized", "16bit", "8bit", "1bit"
    pixel_size: int
    color_limit: int
    dither_mode: str  # "none", "ordered", "error_diffusion", "pattern"
    edge_detection: bool
    posterize_levels: int
}

IsometricConfig {
    enabled: bool
    angle: float  # typically 30 or 45 degrees
    tile_width: int
    tile_height: int
    depth_sorting: bool
    layer_count: int
}
```

---

## 📊 DEPARTMENT SUMMARY

| Department | Status | Priority |
|------------|--------|----------|
| Development | ❌ Not started | Phase 7 |
| Pre-visualization | ❌ Not started | Phase 7 |
| Art Department | ❌ Not started | Phase 8 |
| Camera | ✅ Phase 6.1 | COMPLETE |
| Grip | ❌ Not started | Phase 8 |
| Electrical | ✅ Partial | COMPLETE |
| Lighting | ✅ Partial | COMPLETE |
| Wardrobe | ❌ Not started | Phase 9 |
| Hair & Makeup | ❌ Not started | Phase 9 |
| Location | ❌ Not started | Phase 8 |
| Production | ❌ Not started | Phase 7 |
| Sound | ❌ Not started | Phase 10 |
| VFX | ❌ Not started | Phase 11 |
| Editorial | ❌ Not started | Phase 10 |
| Post Sound | ❌ Not started | Phase 10 |
| Retro Graphics | ❌ Not started | Phase 12 |

---

## 🔄 ONE-SHOT PRODUCTION WORKFLOW

```
SCRIPT
    ↓
┌─────────────────────────────────────────────────────────┐
│                    DEVELOPMENT                           │
│  Parse script → Extract characters → Extract locations  │
│  Generate shot list → Assign style presets              │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                    PRE-VISUALIZATION                     │
│  Generate storyboards → Block all shots                 │
│  Time animatic → Plan camera moves                      │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                    ASSET GENERATION                      │
│  Characters → Costumes → Props → Sets → Locations       │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                    PRODUCTION                            │
│  For each scene:                                         │
│    Set up location/lighting → Place characters          │
│    Execute camera moves → Render shots                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                    POST-PRODUCTION                       │
│  Edit assembly → Color grade → Add sound                │
│  Apply retro effects (if needed) → Final export         │
└─────────────────────────────────────────────────────────┘
    ↓
FINAL OUTPUT
```

---

## 🎯 KEY DATA STRUCTURES FOR ONE-SHOT

### Master Production Config
```python
@dataclass
class ProductionConfig:
    """Complete production specification - one file = one movie"""

    # Identity
    title: str
    version: str
    created: datetime

    # Development
    script: Script
    characters: List[Character]
    locations: List[Location]

    # Style
    visual_style: str  # "photorealistic", "stylized", "16bit", "8bit"
    target_format: str  # "cinema", "tv", "web", "game"
    aspect_ratio: str  # "2.39:1", "16:9", "4:3", "1:1"

    # Production
    shots: List[ShotConfig]
    schedule: ProductionSchedule

    # Post
    color_grade: str
    sound_design: SoundDesign
    retro_settings: Optional[RetroConfig] = None

    def render_all(self):
        """One command to render entire production"""
        pass
```

### Character Tracking
```python
@dataclass
class Character:
    """Complete character specification"""

    name: str
    actor_reference: str  # For likeness

    # Physical
    body_type: str
    height: float
    age: int
    ethnicity: str
    hair_color: str
    eye_color: str

    # Costumes per scene
    wardrobe: Dict[SceneID, Costume]

    # Appearance changes over time
    aging_curve: Optional[AgingCurve]
    injury_progression: Optional[InjuryProgression]

    # Performance
    voice: VoiceConfig
    mannerisms: List[Mannerism]

    # Tracking
    first_appearance: SceneID
    last_appearance: SceneID
    total_screen_time: float
```

---

## 📋 NEXT PHASES ROADMAP

### Phase 6.2: Motion Tracking (IN PROGRESS)
- Object tracking
- Camera tracking
- Character tracking

### Phase 6.3: Follow Camera
- Subject following
- Look-ahead
- Obstacle avoidance

### Phase 7: Development Department
- Script parser
- Character extractor
- Location extractor
- Shot list generator

### Phase 8: Art & Location
- Set builder
- Prop library
- Location manager
- Environment generator

### Phase 9: Character Department
- Wardrobe system
- Costume changes
- Hair/makeup tracking
- Character state manager

### Phase 10: Sound & Editorial
- Timeline system
- Cut list
- Sound design
- Music sync

### Phase 11: VFX Pipeline
- Compositor
- CG integration
- FX simulation

### Phase 12: Retro Graphics
- Pixel converter
- Dither engine
- Isometric view
- Sprite system

---

*This document provides the complete skeleton for a one-shot movie production system.*
