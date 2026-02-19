# Requirements: Retro & Stylized Graphics System

## Overview

Enable the cinematic system to render in any visual style from photorealistic Hollywood to 8-bit retro games. One production pipeline, infinite visual outputs.

---

## REQ-RETRO-01: Pixel Style Modes

**Priority**: P0
**Phase**: 12

### Requirement
Support multiple pixelation/quantization modes for retro graphics output.

### Specifications

| Mode | Description | Color Limit | Pixel Size |
|------|-------------|-------------|------------|
| `photorealistic` | No processing | Unlimited | 1:1 |
| `stylized` | Posterized, smooth | 256-4096 | Variable |
| `32bit` | Game console quality | 16.7M | 1:1 |
| `16bit` | SNES/Genesis era | 32768-65536 | 1:1 |
| `8bit` | NES/Master System | 256 | 2x-4x |
| `4bit` | Game Boy | 16 | 4x |
| `2bit` | Game & Watch | 4 | 4x-8x |
| `1bit` | LCD/Mono | 2 | 8x |

### Acceptance Criteria
- [ ] Can switch between all modes via config
- [ ] Pixel size automatically calculated based on output resolution
- [ ] Color quantization respects target palette

---

## REQ-RETRO-02: Dithering Engine

**Priority**: P0
**Phase**: 12

### Requirement
Implement professional dithering patterns for color-limited output.

### Dithering Modes

| Mode | Use Case | Quality |
|------|----------|---------|
| `none` | Solid color regions | N/A |
| `ordered_2x2` | Basic pattern | Low |
| `ordered_4x4` | Bayer matrix | Medium |
| `bayer_8x8` | High quality ordered | High |
| `error_diffusion` | Floyd-Steinberg | Very High |
| `atkinson` | Macintosh style | Retro |
| `sierra` | Sierra Lite | High |
| `checkerboard` | Classic newspaper | Retro |
| `horizontal_lines` | Scanline effect | Retro |

### Acceptance Criteria
- [ ] All dither modes produce correct patterns
- [ ] Dither strength adjustable (0-100%)
- [ ] Can combine dither with pixelation

---

## REQ-RETRO-03: Color Palette System

**Priority**: P0
**Phase**: 12

### Requirement
Support for predefined and custom color palettes.

### Built-in Palettes

| Palette | Colors | Era/Platform |
|---------|--------|--------------|
| `nes` | 54 | NES (usable colors) |
| `gameboy` | 4 | Original Game Boy |
| `gameboy_color` | 32768 | GBC |
| `snes` | 32768 | SNES |
| `genesis` | 512 | Sega Genesis |
| `cga` | 4 | IBM CGA |
| `ega` | 16 | IBM EGA |
| `vga` | 256 | IBM VGA |
| `pico8` | 16 | PICO-8 fantasy console |
| `monokai` | 16 | Modern retro |
| `solarized` | 16 | Terminal classic |
| `gruvbox` | 16 | Vintage terminal |
| `1bit_mbp` | 2 | Original Macintosh |
| `gamegear` | 4096 | Sega Game Gear |
| `amiga_ocs` | 4096 | Amiga OCS |
| `amiga_aga` | 262144 | Amiga AGA |

### Custom Palettes
- Load from PNG (extract unique colors)
- Load from GPL (GIMP palette)
- Load from HEX list
- Auto-generate from source image

### Acceptance Criteria
- [ ] All built-in palettes match original hardware
- [ ] Custom palettes load correctly
- [ ] Palette enforcement happens before dithering

---

## REQ-RETRO-04: Isometric Projection

**Priority**: P1
**Phase**: 12

### Requirement
Convert 3D scenes to isometric 2D views for game asset generation.

### Isometric Types

| Type | Angle | Tile Ratio | Use Case |
|------|-------|------------|----------|
| `true_isometric` | 30° | 1:√3 | Technical |
| `pixel_isometric` | 26.565° | 2:1 | Classic games |
| `military` | 45° | 1:1 | Strategy games |
| `dimetric` | Custom | Custom | Flexible |

### Features
- Orthographic camera setup
- Depth sorting (painter's algorithm)
- Tile grid snapping
- Layer separation (ground, objects, characters)

### Acceptance Criteria
- [ ] Camera automatically positioned for isometric view
- [ ] Objects snap to tile grid
- [ ] Render layers separate correctly

---

## REQ-RETRO-05: Side-Scroller View

**Priority**: P1
**Phase**: 12

### Requirement
Generate side-scrolling game views from 3D scenes.

### Features
- Fixed orthographic side view
- Parallax layer generation (up to 8 layers)
- Sprite sheet export
- Animation frame generation
- Background/foreground separation

### Acceptance Criteria
- [ ] Camera locked to side view
- [ ] Parallax layers render correctly
- [ ] Sprite sheets generated with metadata

---

## REQ-RETRO-06: CRT & Display Effects

**Priority**: P2
**Phase**: 12

### Requirement
Simulate vintage display technologies.

### Effects

| Effect | Description | Adjustable |
|--------|-------------|------------|
| `scanlines` | Horizontal lines | Strength, spacing |
| `phosphor` | RGB subpixels | Pattern type |
| `curvature` | Screen curve | Amount |
| `vignette` | Edge darkening | Amount |
| `chromatic_aberration` | Color fringing | Amount |
| `bloom` | Light bleed | Intensity |
| `flicker` | Refresh flicker | Frequency |
| `interlace` | Interlaced display | Pattern |
| `pixel_jitter` | Slight movement | Amount |

### Presets

| Preset | Effects | Target |
|--------|---------|--------|
| `crt_arcade` | Scanlines + curvature + bloom | 80s arcade |
| `crt_tv` | Scanlines + phosphor + noise | CRT TV |
| `lcd_gameboy` | Ghosting + low refresh | Game Boy |
| `cga_monitor` | Scanlines + phosphor | IBM CGA |
| `pvm` | Professional CRT | Sony PVM |

### Acceptance Criteria
- [ ] All effects render correctly in compositing
- [ ] Effects can be combined
- [ ] Presets produce authentic looks

---

## REQ-RETRO-07: Sprite Sheet Generation

**Priority**: P1
**Phase**: 12

### Requirement
Export animated characters/objects as sprite sheets.

### Features
- Automatic animation detection
- Configurable sheet layout (horizontal, vertical, grid)
- Metadata export (JSON, XML)
- Trim/crop to content
- Pivot point definition
- Hitbox definition

### Output Formats
- PNG (with transparency)
- JSON metadata (Phaser, Unity, Godot formats)

### Acceptance Criteria
- [ ] Sprite sheets correctly tile all frames
- [ ] Metadata matches frame positions
- [ ] Transparency preserved

---

## REQ-RETRO-08: Bit-Crunch Pipeline

**Priority**: P0
**Phase**: 12

### Requirement
Full pipeline to convert photorealistic renders to retro graphics.

### Pipeline Stages

```
Photorealistic Render
       ↓
┌─────────────────────┐
│ 1. RESOLUTION       │ Downscale to target
└─────────────────────┘
       ↓
┌─────────────────────┐
│ 2. COLOR QUANTIZE   │ Reduce to palette
└─────────────────────┘
       ↓
┌─────────────────────┐
│ 3. DITHER           │ Apply pattern
└─────────────────────┘
       ↓
┌─────────────────────┐
│ 4. POSTERIZE        │ Reduce gradients
└─────────────────────┘
       ↓
┌─────────────────────┐
│ 5. PIXELATE         │ Final pixel sizing
└─────────────────────┘
       ↓
┌─────────────────────┐
│ 6. CRT EFFECTS      │ Optional display sim
└─────────────────────┘
       ↓
Final Retro Output
```

### Acceptance Criteria
- [ ] Each stage independently controllable
- [ ] Can skip stages
- [ ] Stage order can be customized

---

## Data Structures

```python
@dataclass
class RetroConfig:
    """Complete retro graphics configuration"""

    # Mode
    style: str = "photorealistic"  # photorealistic, stylized, 16bit, 8bit, 4bit, 2bit, 1bit

    # Resolution
    target_resolution: Tuple[int, int] = (320, 240)
    pixel_size: int = 1  # 1 = native, 2 = 2x pixels, 4 = chunky

    # Color
    palette: str = "native"  # native, nes, gameboy, pico8, custom
    custom_palette: List[str] = field(default_factory=list)  # hex colors
    color_limit: int = 256

    # Dither
    dither_mode: str = "none"  # none, ordered_4x4, bayer_8x8, error_diffusion, atkinson
    dither_strength: float = 1.0  # 0.0 - 1.0

    # Posterize
    posterize_levels: int = 0  # 0 = off, 2-256

    # View mode
    view_mode: str = "perspective"  # perspective, isometric, side_scroll, top_down
    isometric_angle: float = 26.565  # degrees

    # CRT effects
    crt_effects: List[str] = field(default_factory=list)
    scanline_strength: float = 0.0
    screen_curvature: float = 0.0
    phosphor_pattern: str = "none"  # none, rgb, bgr

    # Sprite export
    sprite_sheet: bool = False
    sprite_layout: str = "grid"  # horizontal, vertical, grid
    sprite_trim: bool = True

    def to_compositor_nodes(self) -> List[Dict]:
        """Generate Blender compositor node setup"""
        pass

    def estimate_color_count(self, image_path: str) -> int:
        """Count unique colors in output"""
        pass


@dataclass
class SpriteSheetConfig:
    """Sprite sheet export configuration"""

    # Layout
    columns: int = 8
    rows: int = 8
    padding: int = 0
    trim: bool = True

    # Frames
    frame_width: int = 32
    frame_height: int = 32
    start_frame: int = 1
    end_frame: int = 64

    # Metadata
    output_json: bool = True
    json_format: str = "phaser"  # phaser, unity, godot, generic

    # Pivot
    pivot_x: float = 0.5  # 0-1
    pivot_y: float = 0.5  # 0-1

    # Hitbox
    generate_hitbox: bool = False
    hitbox_padding: int = 2
```

---

## Integration Points

### With Shot System
```python
shot = CompleteShotConfig(
    name="game_hero",
    camera=CameraConfig(focal_length=35),
    composition=CompositionConfig(shot_size="f"),
    retro=RetroConfig(
        style="16bit",
        palette="snes",
        dither_mode="error_diffusion",
        view_mode="side_scroll"
    )
)
```

### With Compositor
- Generate node tree from RetroConfig
- Apply in post-process pass
- Non-destructive (original render preserved)

---

## File Locations

```
configs/cinematic/retro/
├── palettes/
│   ├── nes.json
│   ├── gameboy.json
│   ├── pico8.json
│   └── ...
├── presets/
│   ├── nes.yaml
│   ├── snes.yaml
│   ├── gameboy.yaml
│   ├── arcade_crt.yaml
│   └── ...
└── dither_patterns/
    ├── bayer_4x4.png
    ├── bayer_8x8.png
    └── ...

lib/cinematic/
├── retro/
│   ├── __init__.py
│   ├── pixelator.py
│   ├── dither.py
│   ├── palettes.py
│   ├── isometric.py
│   ├── sprites.py
│   └── crt_effects.py
```

---

## Success Metrics

- Can render same scene in 10+ visual styles
- Conversion pipeline completes in <5s per frame
- Sprite sheets export with correct metadata
- Isometric views render with proper depth sorting
- CRT effects indistinguishable from real hardware
