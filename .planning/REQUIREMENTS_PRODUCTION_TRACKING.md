# Production Tracking System Requirements

## Overview

A unified tracking system for managing production assets with complete visibility,
status tracking, and artifact generation. Everything traceable to source.

---

## REQ-TRACK-01: Production Tracking Board

### Goal
A simple web UI that shows ALL production elements in one place.

### Status States
| Status | Meaning | Visual |
|--------|---------|--------|
| `complete` | Done, approved, shipped | Green |
| `in_progress` | Currently being worked | Yellow |
| `planned` | Scoped, not started | Blue |
| `vague` | Idea exists, needs definition | Gray |
| `blocked` | Cannot proceed | Red |

### Asset Types (Categories)
| Category | Examples | Source |
|----------|----------|--------|
| `character` | Hero, NPC, creature | concept → model → rig |
| `wardrobe` | Costume pieces, accessories | design → model → texture |
| `prop` | Hand props, set dressing | design → model → texture |
| `set` | Environments, locations | concept → build → dress |
| `shot` | Camera shots, sequences | script → storyboard → render |
| `asset` | Control surfaces, products | spec → build → export |
| `audio` | Music, SFX, dialogue | script → record → mix |

### Board Views
1. **Kanban View** - Columns by status
2. **Table View** - Sortable/filterable list
3. **Timeline View** - Ordered by due date/sequence

### Required Fields
```yaml
id: CHAR-001              # Unique identifier
name: "Hero Character"    # Human readable
category: character       # Asset type
status: in_progress       # Status state
source:                   # Where it came from
  spec: specs/characters/hero.md
  created_by: bret
  created_at: 2026-02-19
blockers: []              # What's blocking
depends_on: []            # Dependencies
assigned_to: null         # Who's working on it
notes: ""                 # Free form notes
images: []                # Reference/product shots
1_sheet: null             # Path to generated 1-sheet
```

### Core Features
- [ ] Add/edit/delete items
- [ ] Filter by category
- [ ] Filter by status
- [ ] Search by name/id
- [ ] Show blockers prominently
- [ ] Link to source files
- [ ] Deep link to 1-sheets

---

## REQ-TRACK-02: Coordination & Dependencies

### Goal
Visualize and manage relationships between items.

### Dependency Types
| Type | Meaning |
|------|---------|
| `depends_on` | This item needs that item |
| `blocks` | This item is blocking that item |
| `related_to` | Loose connection |

### Features
- [ ] Show dependency chain
- [ ] Warn on circular dependencies
- [ ] Highlight blocked items
- [ ] Auto-cascade status changes (optional)

---

## REQ-TRACK-03: Source Traceability

### Goal
Every item traces back to its origin. Even if destroyed, can be recreated.

### Trace Fields
```yaml
source:
  spec: path/to/spec.md           # Original spec/requirement
  task: path/to/task.yaml         # GSD task file
  commit: abc123                  # Git commit that created it
  created_by: bret                # Who created it
  created_at: 2026-02-19          # When
  regenerated_from: null          # If regenerated, link to original
```

### Features
- [ ] Click to view source spec
- [ ] Click to view git commit
- [ ] Click to regenerate from source
- [ ] History log of changes

---

## REQ-TRACK-04: Blocker Management

### Goal
Make blockers visible and actionable.

### Blocker Fields
```yaml
blockers:
  - id: BLK-001
    reason: "Waiting on concept art approval"
    blocking_since: 2026-02-15
    blocking_items: [CHAR-001, CHAR-002]
    resolution: null
```

### Features
- [ ] Blockers panel always visible
- [ ] Add/remove blockers
- [ ] Track blocker age
- [ ] Resolve blockers with notes

---

## REQ-ONESHEET-01: Asset 1-Sheet Generator

### Goal
Generate presentable 1-sheets from tracked assets with images and descriptions.

### 1-Sheet Structure
```
+----------------------------------+
|  [Hero Image - Main Product Shot]|
|                                  |
|  ASSET NAME                      |
|  Category: Character | Status: ✓ |
|                                  |
|  Description:                    |
|  Brief description of asset...   |
|                                  |
|  [Thumb 1] [Thumb 2] [Thumb 3]   |
|                                  |
|  Source: specs/characters/hero   |
|  Created: 2026-02-19 by bret     |
|                                  |
|  Dependencies:                   |
|  → WARD-001 (Hero Costume)       |
|  → PROP-015 (Hero Weapon)        |
+----------------------------------+
```

### Output Formats
- HTML (viewable in browser)
- PDF (for sharing/printing)
- PNG (for embedding)

### Features
- [ ] Auto-generate from asset data
- [ ] Template system for different categories
- [ ] Include primary image + thumbnails
- [ ] Include status and metadata
- [ ] Include dependency chain
- [ ] QR code to source (optional)

---

## REQ-ONESHEET-02: Product Shot Integration

### Goal
Integrate with existing render pipeline to generate product shots for 1-sheets.

### Shot Types
| Shot Type | Purpose |
|-----------|---------|
| `hero` | Main hero shot, dramatic |
| `beauty` | Clean product shot on backdrop |
| `detail` | Close-up of details |
| `context` | In-context/environment shot |
| `turntable` | 360° rotation (animated) |

### Pipeline Integration
```yaml
product_shots:
  hero:
    template: hero_shot
    camera: hero_camera_preset
    lighting: dramatic_rim
    resolution: [1920, 1080]
  beauty:
    template: beauty_shot
    backdrop: infinite_curve_white
    resolution: [1920, 1080]
```

### Features
- [ ] Define shot templates per category
- [ ] Batch generate product shots
- [ ] Auto-attach to asset record
- [ ] Trigger from tracking board

---

## Technical Requirements

### Tech Stack
- **Frontend**: TypeScript + Vite (simple, fast, typed)
- **Data**: YAML files (consistent with existing patterns)
- **Styling**: CSS (no framework, keep it simple)
- **No database** - files are the source of truth

### Data Location
```
.planning/
  tracking/
    items/           # Individual item YAML files
      CHAR-001.yaml
      WARD-015.yaml
    blockers.yaml    # Active blockers
    config.yaml      # Categories, statuses, views

.gsd-state/
  onesheets/
    CHAR-001.html    # Generated 1-sheets
    CHAR-001.png     # Preview images
```

### API Design (Simple)
```
GET  /api/items              # List all items
GET  /api/items?status=in_progress
GET  /api/items/CHAR-001     # Get single item
POST /api/items              # Create item
PUT  /api/items/CHAR-001     # Update item
DEL  /api/items/CHAR-001     # Delete item

GET  /api/blockers           # List blockers
POST /api/blockers           # Add blocker

POST /api/onesheet/CHAR-001  # Generate 1-sheet
```

---

## Uniform Tooling Principle

**Everyone gets the same tools, everyone puts data in, everyone sees everything.**

- No special views for different roles
- No hidden fields or private data
- Same interface for all asset types
- Same workflow for all categories
- If you need fancy UI, the system is wrong

---

## Phase Breakdown

### Phase 9.0: Production Tracking Foundation
- Data model and YAML schema
- Simple API server (Vite dev server)
- Basic board UI (Kanban + Table views)
- Status filtering and search
- Source linking

### Phase 9.1: Coordination & Blockers
- Dependency visualization
- Blocker management panel
- Dependency chain view
- Warning system for blocked items

### Phase 10.0: 1-Sheet Generator
- HTML template system
- Asset-to-1-sheet pipeline
- PDF export
- PNG export

### Phase 10.1: Product Shot Integration
- Shot template definitions
- Blender render pipeline integration
- Batch generation workflow
- Auto-attach to assets
