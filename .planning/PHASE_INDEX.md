# Phase Plan Index

**Last Updated**: 2026-02-18
**Total Phases**: 30+
**Total Plans**: 60+

---

## Quick Navigation

| Phase Range | Category | Status |
|-------------|----------|--------|
| 6.x | Core Cinematic | 🔄 In Progress |
| 7.x | Motion & Tracking | 📋 Planned |
| 8.x | Development Dept | 📋 Planned |
| 9.x | Art & Locations | 📋 Planned |
| 10.x | Character Dept | 📋 Planned |
| 11.x | Sound & Editorial | 📋 Planned |
| 12.x | VFX & Compositing | 📋 Planned |
| 13.x | Retro Graphics | 📋 Planned |
| 14.x | One-Shot Production | 📋 Planned |

---

## Phase 6.x: Core Cinematic System

### 6.0 Foundation ✅ COMPLETE
- Directory structure
- Types and enums
- State management

### 6.1 Camera System ✅ COMPLETE
- [6.1-01 PLAN](phases/06.1-camera-system/06.1-01-PLAN.md) - Types & Preset Loader
- [6.1-02 PLAN](phases/06.1-camera-system/06.1-02-PLAN.md) - Camera Builder
- [6.1-03 PLAN](phases/06.1-camera-system/06.1-03-PLAN.md) - Plumb Bob Targeting
- [6.1-04 PLAN](phases/06.1-camera-system/06.1-04-PLAN.md) - Lens System
- [6.1-05 PLAN](phases/06.1-camera-system/06.1-05-PLAN.md) - Rig System

### 6.2 Motion Tracking
- [6.2-01 PLAN](phases/6.2-motion-tracking/6.2-01-PLAN.md) - Tracking System

### 6.3 Follow Camera
- [6.3-01 PLAN](phases/6.3-follow-camera/6.3-01-PLAN.md) - Follow Camera System

### 6.4 Lighting System
- [6.4-01 PLAN](phases/6.4-lighting-system/6.4-01-PLAN.md) - Lighting System

### 6.5 Render System 📋 TODO
### 6.6 Shot Assembly 📋 TODO
### 6.7 Backdrop System 📋 TODO
### 6.8 Color Pipeline 📋 TODO
### 6.9 Animation System 📋 TODO
### 6.10 Template System 📋 TODO
### 6.11 Lens Imperfections 📋 TODO
### 6.12 Support Systems 📋 TODO
### 6.13 Catalog Generator 📋 TODO

---

## Phase 7.x: Motion & Tracking

### 7.1 Object Tracking
- [7.1-01 PLAN](phases/7.1-object-tracking/7.1-01-PLAN.md) - Object Tracking

### 7.2 Camera Tracking 📋 TODO
### 7.3 Follow Camera Advanced 📋 TODO

---

## Phase 8.x: Development Department

### 8.1 Script Parser
- [8.1-01 PLAN](phases/8.1-script-parser/8.1-01-PLAN.md) - Script Parser

### 8.2 Shot List Generator
- [8.2-01 PLAN](phases/8.2-shot-list-generator/8.2-01-PLAN.md) - Shot List Generator

### 8.3 Style Director 📋 TODO

---

## Phase 9.x: Art & Locations

### 9.1 Set Builder
- [9.1-01 PLAN](phases/9.1-set-builder/9.1-01-PLAN.md) - Set Builder

### 9.2 Location Manager 📋 TODO

---

## Phase 10.x: Character Department

### 10.1 Wardrobe System
- [10.1-01 PLAN](phases/10.1-wardrobe-system/10.1-01-PLAN.md) - Wardrobe System

### 10.2 Character State 📋 TODO

---

## Phase 11.x: Sound & Editorial

### 11.1 Timeline System
- [11.1-01 PLAN](phases/11.1-timeline-system/11.1-01-PLAN.md) - Timeline System

### 11.2 Sound Design 📋 TODO

---

## Phase 12.x: VFX & Compositing

### 12.1 Compositor
- [12.1-01 PLAN](phases/12.1-compositor/12.1-01-PLAN.md) - Compositor

### 12.2 VFX Integration 📋 TODO

---

## Phase 13.x: Retro Graphics

### 13.1 Pixel Converter
- [13.1-01 PLAN](phases/13.1-pixel-converter/13.1-01-PLAN.md) - Pixel Converter

### 13.2 Dither Engine
- [13.2-01 PLAN](phases/13.2-dither-engine/13.2-01-PLAN.md) - Dither Engine

### 13.3 Isometric & Side-Scroller
- [13.3-01 PLAN](phases/13.3-isometric-side-scroller/13.3-01-PLAN.md) - Isometric & Side-Scroller

### 13.4 CRT Effects
- [13.4-01 PLAN](phases/13.4-crt-effects/13.4-01-PLAN.md) - CRT Effects

---

## Phase 14.x: One-Shot Production

### 14.1 Production Orchestrator
- [14.1-01 PLAN](phases/14.1-production-orchestrator/14.1-01-PLAN.md) - Production Orchestrator

### 14.2 Master Config
- [14.2-01 PLAN](phases/14.2-master-config/14.2-01-PLAN.md) - Master Production Config

---

## Supporting Documents

- [Full Production System](FULL_PRODUCTION_SYSTEM.md) - All departments and roles
- [Expanded Roadmap](EXPANDED_ROADMAP.md) - Complete implementation plan
- [Retro Graphics Requirements](REQUIREMENTS_RETRO_GRAPHICS.md) - Pixel/dither specs
- [Cinematography Rules](CINEMATOGRAPHY_RULES.md) - Professional DP methodology
- [Departments Quick Ref](DEPARTMENTS_QUICK_REF.md) - Department summary

---

## Status Legend

| Status | Meaning |
|--------|---------|
| ✅ COMPLETE | Fully implemented and tested |
| 🔄 In Progress | Currently being worked on |
| 📋 Planned | Plan created, awaiting execution |
| 📋 TODO | Plan needs to be created |

---

## Execution Order

**Recommended execution sequence:**

1. **Phase 6.x** (Core Cinematic) - Foundation for everything
2. **Phase 7.x** (Motion & Tracking) - Build on camera system
3. **Phase 8.x** (Development) - Script parsing for automation
4. **Phase 9.x** (Art & Locations) - Set building
5. **Phase 10.x** (Characters) - Wardrobe and state
6. **Phase 11.x** (Editorial) - Timeline and sound
7. **Phase 12.x** (VFX) - Compositing
8. **Phase 13.x** (Retro) - Pixel art pipeline
9. **Phase 14.x** (One-Shot) - Final orchestration

---

## How to Use

### Execute a Phase
```bash
# Plan a phase (creates detailed plan)
/gsd:plan-phase 6.2

# Execute a phase (runs all plans)
/gsd:execute-phase 6.2
```

### Review Progress
```bash
# Check overall progress
/gsd:progress

# See everything
/bret:overview
```

---

## Files Created

| Category | Count |
|----------|-------|
| Phase Directories | 30+ |
| Plan Files | 25+ |
| Requirements Docs | 5 |
| Roadmap Docs | 3 |

---

*This index is auto-generated. Update as phases are completed.*
