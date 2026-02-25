# MSG-1998 Cemetery Research & Recommendations

## Key Finding: Manhattan Has Virtually No Cemeteries

Based on research, **Manhattan has almost no cemeteries in the MSG/Midtown area**. This is historically accurate for 1998 (and today).

### Why Manhattan Has No Cemeteries

1. **Historical Clearing (Mid-19th Century)**
   - Rapid urbanization after the Civil War
   - Public health concerns about disease and groundwater contamination
   - Land values skyrocketed - burial grounds were repurposed
   - Example: Washington Square Park was once a burial ground

2. **Burials Moved to Outer Boroughs**
   - Most Manhattan burials moved to Brooklyn, Queens, Bronx
   - Calvary Cemetery (Queens) - accessible by ferry from 23rd Street
   - Green-Wood Cemetery (Brooklyn) - 500,000+ burials

3. **Remaining Manhattan Cemeteries (None Near MSG)**
   - Trinity Churchyard (Lower Manhattan) - Alexander Hamilton
   - St. Paul's Chapel Graveyard (Lower Manhattan)
   - Trinity Church Cemetery (Uptown, 155th St) - rare active cemetery
   - African Burial Ground (Lower Manhattan) - historic site

## MSG/Midtown Area (31st-33rd St, 7th-8th Ave)

**No cemeteries exist in this area.**

The closest historic burial grounds are:
- **Calvary Cemetery, Queens** - Visible from Manhattan, across East River
- **Trinity Churchyard** - Lower Manhattan (8+ blocks south)

## Recommendations for Scene Accuracy

### Option 1: Remove Any "Cemetery" Objects (RECOMMENDED)
If the scene has any objects labeled as cemeteries in the MSG/Midtown area, they should be removed or renamed for historical accuracy.

### Option 2: Convert to Parks/Green Spaces
If "cemetery" objects exist, consider converting them to:
- Small parks (like Greeley Square)
- Church yards (without graves)
- Plazas

### Option 3: Add Distant Calvary Cemetery (Optional)
For skyline accuracy, Calvary Cemetery in Queens would be visible from elevated points in Manhattan:
- Located across the East River
- Distinctive terraced hillside with headstones
- Would only appear in very wide establishing shots

## Scene Verification Checklist

To verify cemetery accuracy in the scene:

```python
# Run in Blender to check for cemetery objects
import bpy

def find_cemetery_objects():
    """Find any objects that might be cemeteries."""
    cemetery_keywords = [
        'cemetery', 'cemetary', 'grave', 'burial',
        'tomb', 'cemetery', 'memorial park'
    ]

    found = []
    for obj in bpy.data.objects:
        name_lower = obj.name.lower()
        for keyword in cemetery_keywords:
            if keyword in name_lower:
                found.append(obj.name)
                break

    if found:
        print("Potential cemetery objects found:")
        for name in found:
            print(f"  - {name}")
    else:
        print("No cemetery objects found in scene.")

    return found

find_cemetery_objects()
```

## Conclusion

**No action needed for cemetery refinement** - the absence of cemeteries in the MSG/Midtown area is historically accurate for 1998.

If cemetery objects exist in the scene data, they should be:
1. Verified for location accuracy
2. Removed if within Manhattan
3. Kept only if representing distant Queens/Brooklyn views

---

## Files Created

| File | Purpose |
|------|---------|
| `building_materials.py` | Creates and applies architectural materials |
| `CEMETERY_RESEARCH.md` | This document - cemetery accuracy research |
