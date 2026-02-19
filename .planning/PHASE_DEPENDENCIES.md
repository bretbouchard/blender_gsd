# Phase Dependency Graph

**Last Updated**: 2026-02-18
**Purpose**: Defines execution order and dependencies between all phases

---

## Dependency Notation

| Symbol | Meaning |
|--------|---------|
| `→` | Depends on (must complete first) |
| `↔` | Parallel safe (can run simultaneously) |
| `⊙` | Enables (makes features available to) |
| `⚠` | Critical path |

---

## Phase 6.x: Core Cinematic System

```
6.0 Foundation
    ↓
    ├→ 6.1 Camera System (⚠ CRITICAL PATH)
    │      ↓
    │      ├→ 6.2 Lighting System ⊙ 6.4
    │      │
    │      ├→ 6.2 Motion Tracking ⊙ 7.1
    │      │
    │      └→ 6.3 Follow Camera
    │             ↓
    │             └→ 7.1 Object Tracking
    │
    ├→ 6.3 Backdrop System
    │
    ├→ 6.4 Color Pipeline
    │
    ├→ 6.5 Animation System
    │
    ├→ 6.6 Render System (⚠ CRITICAL PATH)
    │      ↓
    │      └→ 6.7 Support Systems
    │
    └→ 6.7 Support Systems
```

**Parallel Groups in 6.x:**
- Group A: 6.1 Camera, 6.3 Backdrop, 6.5 Animation (↔ parallel after 6.0)
- Group B: 6.2 Lighting, 6.4 Color (↔ parallel after 6.1)
- Group C: 6.6 Render, 6.7 Support (↔ parallel after Groups A+B)

---

## Phase 7.x: Motion & Tracking

```
6.1 Camera System
    ↓
    ├→ 7.1 Object Tracking
    │      ↓
    │      └→ 7.2 Camera Tracking
    │             ↓
    │             └→ 7.3 Follow Camera Advanced
    │
    └→ 6.3 Follow Camera
           ↓
           └→ 7.3 Follow Camera Advanced
```

---

## Phase 8.x: Development Department

```
8.1 Script Parser
    ↓
    └→ 8.2 Shot List Generator
           ↓
           └→ 8.3 Style Director
                  ↓
                  └→ 14.1 Production Orchestrator
```

**Dependencies from other phases:**
- 6.1 Camera → 8.2 (needs camera configs)
- 6.2 Lighting → 8.3 (needs lighting rules)

---

## Phase 9.x: Art & Locations

```
6.3 Backdrop System
    ↓
    └→ 9.1 Set Builder
           ↓
           └→ 9.2 Location Manager
                  ↓
                  └→ 14.1 Production Orchestrator
```

---

## Phase 10.x: Character Department

```
9.1 Set Builder
    ↓
    └→ 10.1 Wardrobe System
           ↓
           └→ 10.2 Character State
                  ↓
                  └→ 14.1 Production Orchestrator
```

---

## Phase 11.x: Sound & Editorial

```
6.5 Animation System
    ↓
    └→ 11.1 Timeline System
           ↓
           ├→ 11.2 Sound Design
           │
           └→ 12.1 Compositor
```

---

## Phase 12.x: VFX & Compositing

```
6.6 Render System
    ↓
    └→ 12.1 Compositor
           ↓
           └→ 12.2 VFX Integration
                  ↓
                  └→ 13.x Retro Graphics
```

---

## Phase 13.x: Retro Graphics (Parallel Pipeline)

```
12.1 Compositor
    ↓
    ├→ 13.1 Pixel Converter
    │      ↓
    │      └→ 13.2 Dither Engine
    │             ↓
    │             └→ 13.3 Isometric & Side-Scroller
    │                    ↓
    │                    └→ 13.4 CRT Effects
    │
    └→ 13.2 Dither Engine (↔ 13.1 parallel start)
```

**Retro Graphics can start early:**
- 13.1 Pixel Converter can start after 6.6 Render
- 13.2 Dither Engine can start parallel with 13.1

---

## Phase 14.x: One-Shot Production (Integration Layer)

```
8.3 Style Director ────┐
9.2 Location Manager ──┤
10.2 Character State ──┼→ 14.1 Production Orchestrator
11.1 Timeline System ──┤        ↓
12.2 VFX Integration ──┤   14.2 Master Config
13.4 CRT Effects ──────┘
```

**14.1 Production Orchestrator requires ALL of:**
- 8.3 Style Director (script → shots)
- 9.2 Location Manager (sets)
- 10.2 Character State (actors)
- 11.1 Timeline System (editing)
- 12.2 VFX Integration (effects)
- 13.4 CRT Effects (retro output)

---

## Critical Path

```
6.0 Foundation
    → 6.1 Camera System
    → 6.6 Render System
    → 12.1 Compositor
    → 14.1 Production Orchestrator
    → 14.2 Master Config
```

**Minimum path for working system:** Phases 6.0 → 6.1 → 6.6 → 12.1 → 14.1 → 14.2

---

## Parallel Execution Strategy

### Wave 1: Foundation
- 6.0 Foundation (MUST complete first)

### Wave 2: Core Systems (parallel after 6.0)
- 6.1 Camera System
- 6.3 Backdrop System
- 6.5 Animation System

### Wave 3: Derived Systems (parallel after Wave 2)
- 6.2 Lighting System (needs 6.1)
- 6.4 Color Pipeline (needs 6.1)
- 6.2 Motion Tracking (needs 6.1)
- 7.1 Object Tracking (needs 6.3)

### Wave 4: Integration (parallel after Wave 3)
- 6.6 Render System
- 8.1 Script Parser
- 9.1 Set Builder
- 10.1 Wardrobe System

### Wave 5: Advanced Features (parallel after Wave 4)
- 12.1 Compositor
- 11.1 Timeline System
- 13.1 Pixel Converter
- 8.2 Shot List Generator

### Wave 6: Final Integration (sequential)
- 14.1 Production Orchestrator (needs ALL Wave 5)
- 14.2 Master Config (needs 14.1)

---

## Dependency Declaration Format

All PLAN.md files MUST include this header:

```markdown
---
phase: 6.1
plan: 01
title: Camera Types & Preset Loader
depends_on:
  - 6.0-01  # Foundation types
  - 6.0-02  # Configuration system
enables:
  - 6.2-01  # Lighting needs camera configs
  - 6.3-01  # Follow camera needs camera builder
  - 7.1-01  # Object tracking needs camera system
parallel_safe: false
universal_stages:
  normalize: Load preset JSON
  primary: Parse into CameraConfig
  secondary: Apply cinematography rules
  detail: Validate constraints
  output: Return configured camera
critical_path: true
---
```

---

## Quick Reference: Dependency Matrix

| Phase | Depends On | Enables |
|-------|------------|---------|
| 6.0 | - | ALL 6.x |
| 6.1 | 6.0 | 6.2, 6.3, 6.4, 7.1 |
| 6.2 Lighting | 6.0, 6.1 | 8.3 |
| 6.2 Motion | 6.0, 6.1 | 7.1 |
| 6.3 Follow | 6.0, 6.1 | 7.1, 7.3 |
| 6.3 Backdrop | 6.0 | 9.1 |
| 6.4 | 6.0, 6.1 | 12.1 |
| 6.5 | 6.0 | 11.1 |
| 6.6 | 6.0, 6.1 | 6.7, 12.1, 13.1 |
| 6.7 | 6.0 | - |
| 7.1 | 6.1, 6.3 | 7.2 |
| 7.2 | 7.1 | 7.3 |
| 7.3 | 7.1, 7.2 | - |
| 8.1 | - | 8.2 |
| 8.2 | 6.1, 8.1 | 8.3 |
| 8.3 | 6.2, 8.2 | 14.1 |
| 9.1 | 6.3 | 9.2, 10.1 |
| 9.2 | 9.1 | 14.1 |
| 10.1 | 9.1 | 10.2 |
| 10.2 | 10.1 | 14.1 |
| 11.1 | 6.5 | 11.2, 12.1, 14.1 |
| 11.2 | 11.1 | - |
| 12.1 | 6.6, 11.1 | 12.2, 13.1 |
| 12.2 | 12.1 | 13.x, 14.1 |
| 13.1 | 6.6, 12.1 | 13.2 |
| 13.2 | 13.1 | 13.3 |
| 13.3 | 13.2 | 13.4 |
| 13.4 | 13.3 | 14.1 |
| 14.1 | 8.3, 9.2, 10.2, 11.1, 12.2, 13.4 | 14.2 |
| 14.2 | 14.1 | - |

---

*This document drives the execution order. Update as phases are added or dependencies change.*
