# Blender GSD Framework Roadmap

## Milestone: v0.1 - Foundation
**Target**: 2026-02

### Phase 1: Core Infrastructure ✅
- [x] Git repo initialized
- [x] Directory structure created
- [x] Core library modules (pipeline, nodekit, masks, scene_ops)
- [x] Debug material system
- [x] Export utilities
- [x] Task file format
- [x] Task runner script

### Phase 2: Example Implementation ✅
- [x] Example artifact task
- [x] Example artifact script
- [x] Export profiles defined
- [x] Render profiles defined
- [x] Asset library configuration

### Phase 3: Agent System ✅
- [x] geometry-rick
- [x] shader-rick
- [x] compositor-rick
- [x] export-rick
- [x] render-rick
- [x] asset-rick
- [x] pipeline-rick

### Phase 4: Documentation
- [ ] README with quickstart
- [ ] Architecture documentation
- [ ] Claude prompt pack
- [ ] CI/CD setup

---

## Milestone: v0.2 - First Artifacts
**Target**: TBD

### Phase 5: Real Artifacts
- [ ] Panel artifact (full implementation)
- [ ] Knob artifact
- [ ] Enclosure artifact
- [ ] Material system integration

### Phase 6: Asset Integration
- [ ] Runtime asset search
- [ ] KitBash pack indexing
- [ ] Asset extraction from .blend files

---

## Milestone: v0.3 - Production Ready
**Target**: TBD

### Phase 7: Quality Assurance
- [ ] Unit tests for all lib modules
- [ ] Integration tests for pipelines
- [ ] CI pipeline with Blender
- [ ] Regression test suite

### Phase 8: Ergonomics
- [ ] Project template system
- [ ] `blender-gsd init` command
- [ ] VS Code integration
- [ ] Debug dashboard

---

## Milestone: v1.0 - Stable Release
**Target**: TBD

### Phase 9: Polish
- [ ] Complete documentation
- [ ] Example gallery
- [ ] Performance optimization
- [ ] Version migration tools

### Phase 10: Community
- [ ] Public release
- [ ] Contribution guidelines
- [ ] Issue templates
- [ ] Release process documented

---

---

## Milestone: v0.4 - Control Surface Design System
**Target**: TBD

### Phase 5: Core Control System (REQ-CTRL-01, REQ-CTRL-02) ✅
- [x] Parameter hierarchy implementation
- [x] 9 parameter group loaders
- [x] YAML preset system
- [x] Color system with semantic tokens
- [x] Material system with PBR
- [x] Basic geometry generation for knobs

### Phase 5.1: Knob Geometry Profiles (REQ-CTRL-04) ✅
- [x] Chicken head profile
- [x] Cylindrical profile
- [x] Domed profile
- [x] Flattop profile
- [x] Soft-touch profile
- [x] Pointer profile
- [x] Instrument profile
- [x] Collet profile
- [x] Apex profile
- [x] Custom profile loader

### Phase 5.2: Knob Surface Features (REQ-CTRL-04) ✅
- [x] Knurling system (straight, diamond, helical patterns)
- [x] Ribbing system (horizontal rings)
- [x] Groove system (single, multi, spiral)
- [x] Indicator geometry (line, dot, pointer)
- [x] Collet and cap systems
- [x] Backlit indicator support

### Phase 5.3: Fader System (REQ-CTRL-04) ✅
- [x] Channel fader geometry
- [x] Short fader geometry
- [x] Mini fader geometry
- [x] Fader knob styles
- [x] Track/scale generation
- [x] LED meter integration

### Phase 5.4: Button System (REQ-CTRL-04)
- [ ] Momentary button geometry
- [ ] Latching button geometry
- [ ] Illuminated button system
- [ ] Cap switch system
- [ ] Toggle switch geometry

### Phase 5.5: LED/Indicator System (REQ-CTRL-04)
- [ ] Single LED geometry
- [ ] LED bar geometry
- [ ] VU meter geometry
- [ ] 7-segment placeholder
- [ ] Emissive material integration

### Phase 5.6: Style Presets - Consoles (REQ-CTRL-03)
- [ ] Neve 1073 preset
- [ ] Neve 88RS preset
- [ ] SSL 4000 E preset
- [ ] SSL 9000 J preset
- [ ] API 2500 preset

### Phase 5.7: Style Presets - Synths (REQ-CTRL-03)
- [ ] Moog Minimoog preset
- [ ] Roland TR-808 preset
- [ ] Roland TR-909 preset
- [ ] Sequential Prophet-5 preset
- [ ] Korg MS-20 preset

### Phase 5.8: Style Presets - Pedals (REQ-CTRL-03)
- [ ] Boss Compact preset
- [ ] MXR Classic preset
- [ ] Electro-Harmonix Big Muff preset
- [ ] Ibanez Tube Screamer preset
- [ ] Strymon preset

### Phase 5.9: Morphing Engine (REQ-CTRL-05)
- [ ] Geometry morphing
- [ ] Material morphing
- [ ] Color morphing (LAB interpolation)
- [ ] Animation system for transitions
- [ ] Staggered animation support
- [ ] Real-time morph preview

---

## Future Considerations

### Not Yet Scheduled
- Blender 5.x compatibility
- Alternative DCC support (Houdini, Maya)
- Cloud render integration
- Real-time collaboration
- Physical simulation (springs, dampers)
- Audio-reactive visualization
