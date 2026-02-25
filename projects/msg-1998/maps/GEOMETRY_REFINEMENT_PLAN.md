# MSG-1998 Geometry Refinement Plan

## Overview

This document outlines the geometry modifications needed to make the MSG-1998 scene buildings more architecturally accurate.

---

## Building Geometry Categories

### 1. Simple Boxes (Need Major Work)
These buildings are basic rectangular prisms and need the most work:

**Tall Buildings (>80m) - Consider Geometry Replacement:**
- Empire State Building (needs Art Deco setbacks)
- PENN 1 (needs modern tower profile)
- Manhattan West towers
- Herald Towers

**Mid-Rise (40-80m) - Add Setbacks:**
- Various office buildings
- Hotels

**Low-Rise (<40m) - Add Window Grid:**
- Retail buildings
- Small offices

### 2. Basic Shapes (Need Refinement)
Buildings with some detail but missing:
- Rooftop mechanical penthouses
- Cornices
- Window patterns

### 3. Special Buildings (Custom Handling)

| Building | Current State | Required Modifications |
|----------|---------------|------------------------|
| Madison Square Garden | Likely boxy | Should be cylindrical with domed roof |
| Empire State Building | Simple box | Needs multiple Art Deco setbacks + spire |
| Macy's | Simple block | Needs large display windows, cornice |
| Churches | Various | Need steeples, Gothic windows |

---

## Architectural Features to Add

### Setbacks (1916 Zoning Style)
```
Height 0-25%:   Full footprint
Height 25-50%:  15% inset
Height 50-75%:  Additional 10% inset
Height 75-90%:  Additional 10% inset
Height 90-100%: Tower portion
```

### Rooftop Details
1. **Mechanical Penthouses** - 2-4m height, inset 10% from edge
2. **Water Tanks** - Classic NYC rooftop feature (wooden cylinders)
3. **Elevator Override** - Small structure on roof

### Facade Details
1. **Window Grid Pattern** - ~4m floor height, windows 1.5m wide
2. **Cornice** - Decorative overhang at roofline
3. **Base Distinction** - Ground floor often different treatment

---

## Scripts Created

| Script | Purpose |
|--------|---------|
| `building_geometry_refinement.py` | Analyze and refine building geometry |
| `building_materials.py` | Apply architectural materials |

---

## Execution Steps

### Step 1: Analyze Current State
```python
exec(open("/Users/bretbouchard/apps/blender_gsd/projects/msg-1998/maps/building_geometry_refinement.py").read())
analysis = analyze_all_buildings()
```

### Step 2: Create Refinement Plan
```python
plan = create_refinement_plan()
```

### Step 3: Apply Basic Refinements
```python
refine_all_buildings(max_complexity='basic_shape')
```

### Step 4: Apply Materials
```python
exec(open("/Users/bretbouchard/apps/blender_gsd/projects/msg-1998/maps/building_materials.py").read())
main()
```

---

## Cemetery Geometry

### Finding: No Cemeteries in Manhattan/Midtown

**Historical accuracy requires NO cemetery geometry in the MSG/Midtown area.**

### Verification Script
Run this to check for any cemetery objects:

```python
import bpy

def find_cemetery_objects():
    """Find any objects that might be cemeteries."""
    keywords = ['cemetery', 'grave', 'burial', 'tomb', 'memorial']

    found = []
    for obj in bpy.data.objects:
        name_lower = obj.name.lower()
        for kw in keywords:
            if kw in name_lower:
                found.append(obj)
                break

    if found:
        print(f"Found {len(found)} potential cemetery objects:")
        for obj in found:
            print(f"  - {obj.name}")
            # Option to delete or rename
            # obj.name = obj.name.replace('Cemetery', 'Park')
    else:
        print("No cemetery objects found - historically accurate!")

    return found

find_cemetery_objects()
```

### Optional: Distant Calvary Cemetery (Queens)
If wide skyline views are needed, Calvary Cemetery in Queens would be visible:
- Location: Across East River from Manhattan
- Features: Terraced hillside with headstones
- Only needed for establishing shots

---

## Priority Buildings for Manual Review

These buildings have distinctive shapes that may need manual modeling:

1. **Madison Square Garden** - Cylindrical arena
2. **Empire State Building** - Art Deco with spire
3. **Penn Station** - Underground, surface structures only
4. **Churches** - Gothic features, steeples

---

## Next Steps

1. Run analysis in Blender
2. Review refinement plan
3. Apply automated refinements
4. Manually adjust landmark buildings
5. Verify cemetery accuracy (should be none)
