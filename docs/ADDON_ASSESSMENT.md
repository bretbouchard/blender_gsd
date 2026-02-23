# Blender Add-on Assessment

**Assessment Date**: 2026-02-19
**Blender Versions**: 4.0, 5.0 installed
**Project**: Blender GSD Pipeline

---

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| **Third-Party Add-ons** | 18 | ⚠️ Many outdated, some broken |
| **Built-in Modules** | 15+ | ✅ Project-owned, maintained |
| **Critical Issues** | 5 | 🔴 Need immediate attention |
| **Recommended Removals** | 6 | 🗑️ Unused or broken |

---

## Installed Third-Party Add-ons Inventory

### ✅ RECOMMENDED (Keep & Update)

| Add-on | Version | Blender | Purpose | Status | Action |
|--------|---------|---------|---------|--------|--------|
| **BlenderCAM** | 1.0.23 | 3.6+ | CNC machining, G-code generation | ⚠️ Works | Keep for fabrication workflows |
| **Dream Textures** | 0.2.0 | 3.1+ | AI texture generation with Stable Diffusion | ⚠️ Works | Keep for texture work, heavy deps |
| **SPOCK (Structured Packer)** | 1.0.6 | 3.4+ | UV packing algorithms | ✅ Good | Keep for UV workflows |
| **Light Control** | 1.0.5 | 3.5+ | Fast light creation/adjustment | ✅ Good | Keep for lighting work |
| **Sanctus-Library** | 2.5.0 | 3.0+ | Material/shader library management | ⚠️ Old | Keep, check for updates |
| **KITOPS Pro** | 2.26.4 | - | Kitbashing and asset management | ✅ Good | Keep for kitbashing |
| **fspy-blender** | - | - | Camera matching from photos | ✅ Good | Keep for reference matching |

### ⚠️ CONDITIONAL (Use Sparingly)

| Add-on | Version | Purpose | Issue | Recommendation |
|--------|---------|---------|-------|----------------|
| **SuperImageDenoiser** | BETA | AI denoising | Outdated, BETA | Use Blender's built-in denoiser instead |
| **BY-GEN-public** | - | Procedural generation | Old, limited | Use project's Geometry Nodes instead |
| **curves_to_mesh** | - | Curve conversion | Basic functionality | Blender 4.x has this built-in |
| **ARMORED_Curve_Basher** | - | Curve editing | Specialty tool | Keep if doing heavy curve work |

### 🗑️ RECOMMENDED FOR REMOVAL

| Add-on | Reason | Safe to Remove |
|--------|--------|----------------|
| **dream_textures** (duplicate/old) | Multiple versions, heavy dependencies | ⚠️ Keep one, remove duplicates |
| **__MACOSX** folders | macOS resource forks, not add-ons | ✅ Safe to delete |
| **Corner instancer.blend** | Not an add-on, should be in assets | ✅ Move to assets folder |
| **Procedural_Building_Generator_v1_3_1.blend** | Not an add-on, old version | ✅ Move to assets or delete |
| **Import As Decal** | Limited use case | ✅ Remove if unused |
| **stop_mo** | Stop motion helper, niche use | ✅ Remove if unused |
| **WP_Blender_Free** | Unknown/free version of paid add-on | ⚠️ Evaluate usage |
| **Tiny Eye 1.2** | Old version | ⚠️ Check if needed |
| **design_magic** | Unknown purpose | ⚠️ Check if needed |
| **Holt-Tools** | Unknown purpose | ⚠️ Check if needed |
| **Generator's Lab** | Procedural generation, redundant | ⚠️ Evaluate vs project tools |
| **Align And Distribute** | Basic functionality in Blender | ⚠️ Blender has built-in |

---

## Project Built-in Modules (lib/)

These are YOUR project modules - they are custom-built and maintained:

### Core Modules

| Module | Purpose | Status |
|--------|---------|--------|
| `lib/pipeline.py` | Pipeline orchestration | ✅ Active |
| `lib/oracle.py` | AI/query system | ✅ Active |
| `lib/exports.py` | Export utilities | ✅ Active |
| `lib/gsd_io.py` | GSD I/O operations | ✅ Active |
| `lib/nodekit.py` | Node utilities | ✅ Active |
| `lib/scene_ops.py` | Scene operations | ✅ Active |
| `lib/masks.py` | Mask utilities | ✅ Active |

### Subsystem Modules

| Subsystem | Modules | Purpose | Status |
|-----------|---------|---------|--------|
| **cinematic/** | 50+ files | Camera, lighting, tracking, shots | ✅ Active, well-structured |
| **animation/** | 25+ files | Rigging, poses, IK, blocking | ✅ Active |
| **control_system/** | 15+ files | UI controls, faders, buttons | ✅ Active |
| **editorial/** | 7 files | Timeline, transitions, export | ✅ Active |
| **vfx/** | 5+ files | Compositing, color, layers | ✅ Active |
| **inputs/** | 6 files | Input handling, zones | ✅ Active |
| **utils/** | 4 files | Safety, limits, math, drivers | ✅ Just created |

---

## Critical Issues & Recommendations

### Issue 1: Outdated Add-on Versions
**Severity**: 🟡 Medium

Many add-ons are from 2023 and may not work properly with Blender 5.0.

**Action**:
```bash
# Check for updates
- BlenderCAM: https://github.com/vilemduha/blendercam
- Dream Textures: https://github.com/carson-katri/dream-textures
- Sanctus-Library: Check Gumroad/BlenderMarket
- KITOPS: Already checked (2.26.4 current)
```

### Issue 2: Python Dependencies Missing
**Severity**: 🟡 Medium

BlenderCAM requires external packages:
```
- shapely
- Equation
- opencamlib
```

**Action**:
```bash
# Install for Blender's Python
/Applications/Blender.app/Contents/Resources/4.0/python/bin/python3 -m pip install shapely Equation opencamlib
```

### Issue 3: macOS Resource Forks in Add-ons Folder
**Severity**: 🟢 Low

`__MACOSX` folders are macOS archive artifacts, not add-ons.

**Action**:
```bash
rm -rf ~/Library/Application\ Support/Blender/4.0/scripts/addons/__MACOSX
```

### Issue 4: Blender 4.0 vs 5.0 Compatibility
**Severity**: 🟡 Medium

Add-ons installed for 4.0 may not work with 5.0.

**Action**: Test each add-on in Blender 5.0 and migrate as needed.

### Issue 5: Dream Textures Heavy Dependencies
**Severity**: 🟡 Medium

Dream Textures requires PyTorch and large AI models (~4GB).

**Recommendation**:
- Keep if actively using AI texture generation
- Remove if not needed (saves disk space and load time)

---

## When/Why/How to Use Each Add-on

### For Product Visualization (Your Main Use Case)

| Add-on | When to Use | Why | How |
|--------|-------------|-----|-----|
| **KITOPS** | Kitbashing knobs, panels | Fast asset placement | Drag from KITOPS panel |
| **Light Control** | Setting up studio lighting | Quick light positioning | Shift+E to create, E to adjust |
| **Sanctus-Library** | Material management | Organized shader presets | Browse in library panel |
| **fspy-blender** | Matching real photos | Accurate camera matching | Import fspy project |

### For Animation Workflows

| Add-on | When to Use | Why | How |
|--------|-------------|-----|-----|
| **BlenderCAM** | CNC fabrication | G-code from 3D models | Properties > Render > CAM |
| **Dream Textures** | AI textures | Generate unique textures | Image Editor > Dream panel |

### For UV/Texture Work

| Add-on | When to Use | Why | How |
|--------|-------------|-----|-----|
| **SPOCK** | UV packing | Better packing algorithms | 3D View > N panel > SP |

---

## Configuration Checklist

### Per-Project Setup

```python
# In Blender, enable only needed add-ons:
1. Edit > Preferences > Add-ons
2. Search for add-on name
3. Check the box to enable
4. Configure add-on preferences if needed
```

### Recommended Startup Configuration

```
ALWAYS ENABLE:
- KITOPS (asset management)
- Light Control (lighting)
- Sanctus-Library (materials)

ENABLE WHEN NEEDED:
- Dream Textures (texture generation - heavy)
- BlenderCAM (fabrication - requires deps)
- SPOCK (UV packing)

DISABLE:
- All others unless specifically needed
```

---

## Cleanup Script

Run this to clean up unused add-ons:

```bash
#!/bin/bash
# cleanup_addons.sh

ADDON_DIR="/Users/bretbouchard/Library/Application Support/Blender/4.0/scripts/addons"

# Remove macOS resource forks
rm -rf "$ADDON_DIR/__MACOSX"

# Move blend files to assets (not add-ons)
mkdir -p ~/blender_gsd/assets/addon_blends
mv "$ADDON_DIR/"*.blend ~/blender_gsd/assets/addon_blends/ 2>/dev/null

# List add-ons for review
echo "=== Installed Add-ons ==="
ls -la "$ADDON_DIR"
```

---

## Dependency Installation

For add-ons requiring Python packages:

```bash
# Blender 4.0 Python
BLENDER_PY="/Applications/Blender.app/Contents/Resources/4.0/python/bin/python3"

# BlenderCAM dependencies
$BLENDER_PY -m pip install shapely Equation opencamlib

# Dream Textures (macOS Apple Silicon)
$BLENDER_PY -m pip install -r ~/Library/Application\ Support/Blender/4.0/scripts/addons/dream_textures/requirements/mac-mps-cpu.txt
```

---

## Summary & Next Steps

### Immediate Actions (Do Now)

1. ✅ Remove `__MACOSX` folders
2. ✅ Move `.blend` files from add-ons to assets
3. ⏳ Test add-ons in Blender 5.0
4. ⏳ Install missing Python dependencies

### Short-term Actions (This Week)

1. Update outdated add-ons (check BlenderMarket/Gumroad)
2. Remove unused add-ons (stop_mo, design_magic, etc.)
3. Document which add-ons are needed for which project types

### Long-term Actions

1. Consider consolidating functionality into project's own modules
2. Evaluate if Dream Textures is worth the ~4GB dependency
3. Keep add-on list minimal for faster Blender startup

---

## Your Project vs Third-Party

**Key Insight**: Your `lib/` directory contains 150+ Python files that provide:

- ✅ Camera/cinematic tools
- ✅ Animation system
- ✅ Control system (knobs, faders)
- ✅ VFX/compositing
- ✅ Editorial tools
- ✅ Input handling
- ✅ Utility functions

**You may not need many third-party add-ons** - your project already has robust built-in functionality. Focus on:

1. **KITOPS** - Asset management (your project doesn't have this)
2. **Light Control** - Quick lighting (nice-to-have)
3. **fspy** - Camera matching (specialized)

Everything else could potentially be replaced by your own modules or Blender's built-in tools.
