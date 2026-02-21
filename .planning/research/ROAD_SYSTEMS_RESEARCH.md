# Road and Urban Infrastructure Generation Research

**Researched:** 2026-02-21
**Domain:** Procedural road network generation, urban infrastructure, Geometry Nodes
**Confidence:** MEDIUM (Based on web research and existing Blender ecosystem analysis)

## Summary

This research covers procedural road network generation for Blender using Geometry Nodes, including all associated urban infrastructure elements. The domain encompasses L-system road generation, grid-based layouts, organic curved paths, intersections, and the complete ecosystem of street furniture, signage, lighting, and pavement materials.

**Primary recommendation:** Use a **curve-based hierarchical system** where road curves drive all downstream geometry. Build modular Geometry Node groups for each component (road surface, markings, curbs, sidewalks, signs, lights, furniture) that can be combined and instanced along curves.

---

## 1. Road Network Generation

### 1.1 L-System Road Generation

**What:** Lindenmayer Systems (L-systems) use grammar rules to iteratively generate road networks from simple starting conditions.

**Core Algorithm:**
```
Axiom: Start with main road segment
Rules:
  - F (forward): Create road segment
  - + (turn right): Rotate by angle
  - - (turn left): Rotate by angle
  - [ (push): Save current position/angle
  - ] (pop): Return to saved position

Example Rule: F -> F[+F]F[-F]F
```

**Geometry Nodes Implementation:**
```python
# Conceptual node structure
# 1. Start with seed point
# 2. For each iteration:
#    - Evaluate L-system rules
#    - Generate curve segments
#    - Apply angle/length variations (randomness)
#    - Handle branch points with curve splitting
# 3. Convert curves to road geometry
```

**Key Parameters:**
| Parameter | Range | Purpose |
|-----------|-------|---------|
| Iterations | 3-8 | Network complexity |
| Branch Angle | 30-90 deg | Organic vs grid feel |
| Length Variation | 0-30% | Natural appearance |
| Branch Probability | 0.1-0.5 | Density control |
| Snap to Grid | On/Off | Grid vs organic layouts |

**Confidence:** MEDIUM - L-system theory is well-established; Geometry Nodes implementation requires custom node groups.

### 1.2 Grid-Based Street Layouts

**What:** Regular grid patterns with configurable block sizes and street hierarchies.

**Standard Grid Parameters:**
| Road Type | Width | Block Spacing |
|-----------|-------|---------------|
| Arterial | 30-40m | 400-800m |
| Collector | 20-30m | 200-400m |
| Local | 12-20m | 100-200m |
| Alley | 6-10m | 50-100m |

**Geometry Nodes Implementation:**
```python
# Grid generation approach
# 1. Create grid of points based on block dimensions
# 2. Generate horizontal and vertical curves at grid lines
# 3. Apply road width profiles via Curve to Mesh
# 4. Handle intersections as special cases

# Node flow:
Grid Points -> Curve Line (H/V) -> Resample Curve -> Set Curve Radius -> Curve to Mesh
```

**Hierarchical Road Types:**
- Primary roads: Wider, through-traffic
- Secondary roads: Medium width, local traffic
- Tertiary/Alleys: Narrow, access only

### 1.3 Organic/Curved Road Paths

**What:** Natural, flowing road curves that follow terrain or avoid obstacles.

**Geometry Nodes Implementation:**
```python
# Bezier curve input with:
# - Control point positions
# - Handle types (aligned, free, vector)
# - Radius variation along curve (for width changes)

# Processing:
Input Curve -> Resample Curve -> Smooth (optional) -> Set Curve Radius -> Curve to Mesh
```

**Key Techniques:**
- Use Bézier curves as input for artistic control
- Apply noise/displacement for organic variation
- Terrain-following: Project curves onto terrain mesh

### 1.4 Intersection Handling

**Intersection Types:**

| Type | Description | Use Case |
|------|-------------|----------|
| 4-Way | Standard cross intersection | Grid layouts |
| 3-Way (T) | Three-road junction | End of streets |
| Roundabout | Circular flow | Traffic calming |
| Highway Interchange | Grade-separated | High-speed roads |

**4-Way Intersection Geometry:**
```
    |   |
----+---+----
    | X |  <- Center junction area
----+---+----
    |   |
```

**Geometry Nodes Implementation:**
```python
# Intersection detection and generation
# 1. Find curve intersection points
# 2. Create intersection zone geometry
# 3. Blend road surfaces at junction
# 4. Add appropriate markings/signage

# Node structure:
Curves -> Curve Intersections (detect points)
       -> Create Junction Geometry (squares/rounded)
       -> Boolean Union with roads
       -> Apply junction materials
```

**Roundabout Dimensions (Standards):**
| Parameter | Value |
|-----------|-------|
| Central Island Diameter | 25-65m (varies by design speed) |
| Circulatory Roadway Width | 6m minimum (2 lanes) |
| Lane Width | 5.5m for large vehicles |
| Entry/Exit Width | 4-5m per lane |
| Design Speed | 20-40 km/h |

**Roundabout Geometry Nodes:**
```python
# Roundabout generation
# 1. Center point + radius parameters
# 2. Create central island (circle, flat top)
# 3. Create circulatory roadway (ring)
# 4. Create entry/exit legs (tangent to ring)
# 5. Add splitter islands at entries

Radius Input -> Circle Curve -> Curve to Mesh (island)
            -> Ring (roadway) -> Curve to Mesh
Entry Curves -> Connect tangentially
```

### 1.5 Highway/Freeway Generation

**What:** Multi-lane, high-speed roads with median, shoulders, and on/off ramps.

**Standard Highway Dimensions:**
| Component | Width |
|-----------|-------|
| Lane | 3.5-3.75m |
| Left Shoulder | 1.0-3.0m |
| Right Shoulder | 2.5-3.0m |
| Median | 2.0-20m+ |
| Total (2x3 lanes) | 25-35m |

**Geometry Nodes Structure:**
```python
# Highway cross-section profile
Profile Curve = [
  right_edge,           # 0
  right_shoulder_edge,  # shoulder width
  lane_1_edge,          # 3.5m
  lane_2_edge,          # 3.5m
  lane_3_edge,          # 3.5m
  median_edge,          # median width
  lane_4_edge,          # opposite direction
  lane_5_edge,
  lane_6_edge,
  left_shoulder_edge,
  left_edge
]

# Apply via Curve to Mesh with this profile
```

### 1.6 Alley/Side Street Generation

**What:** Narrow access roads, typically single-lane, service-oriented.

**Dimensions:**
| Type | Width | Surface |
|------|-------|---------|
| Residential Alley | 6-8m | Asphalt/gravel |
| Commercial Alley | 8-12m | Concrete |
| Service Lane | 4-6m | Various |

---

## 2. Road Geometry Components

### 2.1 Lane Markings

**Types and Dimensions:**

| Marking Type | Width | Length | Spacing |
|--------------|-------|--------|---------|
| Solid Line | 10-15cm | Continuous | - |
| Dashed Line | 10-15cm | 3m | 6m gaps |
| Double Yellow | 10cm each | Continuous | 10-20cm gap |
| Crosswalk | 30-60cm | 3-4m | 60cm spacing |
| Stop Line | 30-60cm | Full lane | - |

**Geometry Nodes Implementation:**
```python
# Lane marking generator
# 1. Get road center curve
# 2. Offset curve by lane position
# 3. Apply marking pattern (solid/dashed)

# For dashed lines:
Centerline Curve -> Offset (lane position) -> Resample
                -> Select points (dash pattern)
                -> Instance rectangles on selected points

# Pattern control:
Dash Length -> Float
Gap Length -> Float
Marking Width -> Float
Marking Height -> Float (0.5-2mm, slight extrusion)
```

**Material for Markings:**
- White: Retroreflective, high visibility
- Yellow: Center lines, no-passing zones
- Use emission for visibility at night

### 2.2 Shoulder/Bike Lanes

**Dimensions:**
| Type | Width | Surface |
|------|-------|---------|
| Paved Shoulder | 1.5-3.0m | Asphalt |
| Bike Lane | 1.2-2.0m | Asphalt/painted |
| Buffered Bike | 1.5-2.5m | Painted buffer |

**Geometry Nodes:**
```python
# Bike lane as road extension
Road Mesh -> Extrude edges (shoulder width)
          -> Set separate material (often painted green)
          -> Add bike lane symbols (instance on points)
```

### 2.3 Curbs and Gutters

**Standard Profiles:**

| Type | Height | Width | Use |
|------|--------|-------|-----|
| Vertical Curb | 15-20cm | 15-30cm | Urban streets |
| Rolled Curb | 10cm | 30cm | Residential |
| Mountable Curb | 5-10cm | 30cm | Parking areas |
| Combination (Curb+Gutter) | 15-20cm | 45-60cm | Standard |

**Geometry Nodes Profile:**
```python
# Curb profile curve (vertical curb + gutter)
CurbProfile = [
  (0, 0),        # road surface
  (0, 0.15),     # curb face top
  (0.15, 0.15),  # curb top
  (0.15, 0.05),  # gutter slope
  (0.45, 0.05),  # gutter bottom
  (0.45, 0)      # sidewalk start
]

# Instance along road edges:
Road Edge -> Curve to Mesh with CurbProfile
```

### 2.4 Sidewalks

**Dimensions:**
| Location | Width | Notes |
|----------|-------|-------|
| Commercial | 2.5-4.0m | High pedestrian traffic |
| Residential | 1.5-2.5m | Standard |
| Minimum | 1.2m | ADA compliance |

**Geometry Nodes:**
```python
# Sidewalk generation
# 1. Offset road curve by (road_width/2 + curb_width)
# 2. Create sidewalk width profile
# 3. Apply surface material (concrete, brick)

Road Center -> Offset (road + curb width) -> Curve to Mesh (sidewalk profile)
            -> Subdivide -> Apply texture coordinates
```

### 2.5 Medians/Center Islands

**Dimensions:**
| Type | Width | Length |
|------|-------|--------|
| Painted Median | 0.3-1.0m | Variable |
| Raised Median | 1.5-6.0m | Variable |
| Turn Lane | 3.0-4.0m | 30-100m |

**Geometry Nodes:**
```python
# Median on multi-lane roads
# 1. Get center curve
# 2. Create median profile (flat or raised)
# 3. Apply median material (grass, concrete, pavers)

Centerline -> Curve to Mesh (median profile)
           -> Add landscaping instances (plants, trees)
```

### 2.6 Speed Bumps

**Dimensions:**
| Type | Height | Width | Length |
|------|--------|-------|--------|
| Speed Hump | 7-10cm | 3.0-4.0m | Full lane |
| Speed Table | 7-10cm | 6.5m | Full lane |
| Speed Bump | 5-7cm | 0.9m | Full lane |

**Profile Shapes:**
- Sinusoidal (smoothest)
- Parabolic
- Circular
- Flat-top (speed table)

**Geometry Nodes:**
```python
# Speed bump placement
# 1. Define positions along road curve
# 2. Instance bump profile at each position
# 3. Boolean union with road surface

BumpPositions = [50, 100, 150]  # meters along road
RoadCurve -> Sample Curve at positions
          -> Instance bump geometry
          -> Rotate to align with road tangent
          -> Boolean union
```

### 2.7 Crosswalks

**Types:**
| Type | Description | Visibility |
|------|-------------|------------|
| Standard (Zebra) | White stripes | High |
| Continental | Wide bars | Very High |
| Ladder | Bars + outline | High |
| Decorative | Brick/stamped | Medium |

**Dimensions:**
- Stripe width: 30-60cm
- Stripe gap: 30-60cm
- Crosswalk width: 3-4m (typical)

**Geometry Nodes:**
```python
# Crosswalk at intersection
# 1. Define crosswalk center point (at intersection)
# 2. Create perpendicular lines
# 3. Instance stripe geometry

CrosswalkPosition -> Create perpendicular line
                  -> Distribute stripe instances
                  -> Set white material
```

---

## 3. Street Signage

### 3.1 Regulatory Signs (Stop, Yield)

**MUTCD Dimensions:**

| Sign | Shape | Size (Conventional) | Size (Freeway) |
|------|-------|---------------------|----------------|
| STOP | Octagon | 30" (76cm) | 36" (91cm) |
| YIELD | Triangle | 36" (91cm) | 48" (122cm) |
| Speed Limit | Rectangle | 24"x30" | 36"x48" |

**Pole Height:**
- Roadside: 2.1m (7ft) minimum to bottom of sign
- Overhead: 5.2m (17ft) minimum

**Geometry Nodes Implementation:**
```python
# Sign generation
# 1. Create sign face mesh (shape based on type)
# 2. Add pole (cylinder)
# 3. Apply material (retroreflective shader)

SignTypes = {
  'stop': {'shape': 'octagon', 'size': 0.76, 'color': 'red'},
  'yield': {'shape': 'triangle', 'size': 0.91, 'color': 'red'},
  'speed_limit': {'shape': 'rectangle', 'size': (0.6, 0.75), 'color': 'white'}
}

# Instancing signs at positions
SignPositions -> Instance on Points
              -> Pick Instances (random or by type)
              -> Apply rotation (face traffic)
```

### 3.2 Speed Limit Signs

**Standard Sizes:**
- Conventional roads: 24" x 30" (61cm x 76cm)
- Expressways: 36" x 48" (91cm x 122cm)
- Minimum sizes for low-speed roads: 18" x 24"

**Geometry Nodes:**
```python
# Speed limit sign with number
# Option 1: Use image textures with numbers
# Option 2: Use text objects (convert to mesh)
# Option 3: Pre-modeled sign collection

SpeedSign -> Instance
          -> Set material (white/black text)
          -> Random speed values via texture index
```

### 3.3 Directional Signs

**Types:**
- Street name signs (blade signs)
- Highway guide signs (green)
- Distance markers

**Dimensions:**
| Type | Height | Variable Width |
|------|--------|----------------|
| Street Name | 15-20cm | Based on text |
| Highway Guide | 90-180cm | Based on content |

### 3.4 Traffic Signals

**Dimensions:**
| Component | Height | Width |
|-----------|--------|-------|
| Signal Head | 30-40cm | 30-40cm |
| Pole (overhead) | 5.5-7m | - |
| Pole (roadside) | 3-4.5m | - |
| Mast Arm | - | 3-12m |

**Pedestrian Signals:**
| Component | Height |
|-----------|--------|
| Signal Head | 2.0-3.0m above ground |
| Push Button | 1.0-1.4m above ground |

**Geometry Nodes:**
```python
# Traffic signal assembly
# 1. Pole (cylinder)
# 2. Mast arm (box/cylinder)
# 3. Signal heads (boxes with lens mesh)
# 4. Wiring conduit (small cylinder)

TrafficSignalPole -> Cylinder (height based on type)
MastArm -> Box (length based on road width)
SignalHeads -> Instance at end of mast arm
            -> Set emissive material for lights
```

---

## 4. Street Lighting

### 4.1 Pole Types

| Type | Description | Height | Use |
|------|-------------|--------|-----|
| Cobra Head | Standard street light | 8-12m | Arterial roads |
| Decorative | Ornate, period style | 4-6m | Downtown |
| Modern/Sleek | Contemporary design | 6-10m | New development |
| Twin-Arm | Two lights | 8-12m | Median |
| Pedestrian | Short, bollard-style | 3-4m | Walkways |

### 4.2 Spacing Calculations

**Formula:**
```
Spacing = (Height x Coefficient) + Adjustments

Where Coefficient:
- Single-sided: 3-4x pole height
- Staggered: 4-5x pole height
- Opposite: 4-5x pole height
```

**Standard Spacing by Road Type:**
| Road Type | Pole Height | Spacing | Arrangement |
|-----------|-------------|---------|-------------|
| Arterial | 12m | 35-50m | Opposite or staggered |
| Collector | 10m | 30-40m | Staggered |
| Local | 8m | 25-35m | Single-sided |
| Pedestrian | 4-6m | 15-20m | Single-sided |

**Geometry Nodes:**
```python
# Street light placement
# 1. Sample road curve at spacing intervals
# 2. Offset to road edge
# 3. Instance light pole with luminaire

Spacing = 40  # meters
RoadCurve -> Resample (Spacing)
          -> Offset to roadside
          -> Instance LightPole
          -> Rotate to face road
          -> Random height variation (0-5%)
```

### 4.3 Light Distribution

**IES Profiles (for realistic lighting):**
- Type II: Wide, one-sided (roadside)
- Type III: Forward throw (intersections)
- Type V: Symmetrical (parking lots)

**Blender Setup:**
```
Light Object -> Point/Area light
            -> Use IES texture for distribution
            -> Set appropriate wattage/lumens
            -> Color temperature: 3000-5000K (LED)
```

---

## 5. Urban Furniture

### 5.1 Benches

**Dimensions:**
| Type | Length | Depth | Height |
|------|--------|-------|--------|
| 2-Person | 120cm | 50-60cm | 40-45cm seat |
| 3-Person | 180cm | 50-60cm | 40-45cm seat |
| With Backrest | +15cm depth | | 80-90cm total |

**Geometry Nodes Placement:**
```python
# Bench placement along sidewalk
SidewalkEdge -> Distribute Points (density parameter)
             -> Selection (avoid driveways, intersections)
             -> Instance Bench
             -> Rotate perpendicular to road
```

### 5.2 Trash Cans

**Dimensions:**
| Type | Width | Height | Capacity |
|------|-------|--------|----------|
| Standard | 50cm | 90-100cm | 50-60L |
| Large | 60cm | 100cm | 100-120L |

**Spacing:** Every 50-100m in commercial areas

### 5.3 Bollards

**Types and Dimensions:**
| Type | Height | Diameter | Spacing |
|------|--------|----------|---------|
| Standard | 90-100cm | 10-15cm | 1.0-1.5m |
| Removable | 90cm | 10cm | Variable |
| Decorative | 80-120cm | 15-30cm | Variable |

### 5.4 Planters

**Dimensions:**
| Type | Width | Height |
|------|-------|--------|
| Small | 40-60cm | 40-50cm |
| Medium | 60-90cm | 50-60cm |
| Large | 90-150cm | 60-80cm |

### 5.5 Bus Stops

**Shelter Dimensions:**
| Component | Dimension |
|-----------|-----------|
| Overall Height | 2.6-2.8m |
| Canopy Width | 1.6-2.0m |
| Length | 5-8m |
| Platform Height | 15-20cm |

**Placement:** 400-800m spacing in urban areas

### 5.6 Bike Racks

**Dimensions:**
| Configuration | Space per Bike | Rack Depth |
|---------------|----------------|------------|
| Perpendicular | 0.6m x 2.0m | 2.0m |
| 45-degree | 0.5m x 1.4m | 1.4m |
| 30-degree | 0.5m x 1.0m | 1.0m |

### 5.7 Fire Hydrants

**Dimensions:**
| Component | Height | Width |
|-----------|--------|-------|
| Barrel | 60-90cm | 15-20cm dia |
| Bonnet | +15cm | 20-25cm |
| Nozzles | - | 2-3 outlets |

**Placement:** 100-150m spacing in urban areas

### 5.8 Mailboxes

**Dimensions:**
| Type | Width | Height | Depth |
|------|-------|--------|-------|
| Collection Box | 40-50cm | 100-120cm | 50-60cm |
| Residential | 20cm | 45cm | 20cm |

---

## 6. Pavement Materials

### 6.1 Asphalt

**Properties:**
| State | Color | Roughness | Notes |
|-------|-------|-----------|-------|
| Fresh | Dark gray/black | 0.85-0.95 | Uniform |
| Weathered | Light gray | 0.8-0.9 | Faded |
| Cracked | Gray + crack lines | 0.85 | Stress patterns |
| Patched | Mixed gray tones | 0.8-0.9 | Repair marks |

**Procedural Shader Approach:**
```python
# Asphalt material nodes
Base Color: Dark gray (0.05-0.15)
Roughness: 0.85 + noise variation
Normal: Multiple noise layers (fine + coarse)
Detail: Cracks via voronoi/noise texture
        Patches via masked color variation
```

### 6.2 Concrete

**Properties:**
| State | Color | Surface |
|-------|-------|---------|
| Fresh | Light gray | Smooth |
| Aged | Gray/white | Textured |
| Stamped | Various | Pattern imprinted |
| Exposed Aggregate | Gray | Rough, pebbled |

### 6.3 Brick Pavers

**Dimensions:**
| Type | Size | Pattern |
|------|------|---------|
| Standard | 20x10x6cm | Herringbone, running bond |
| Large | 30x15x6cm | Staggered |
| Square | 20x20x6cm | Grid |

**Shader Considerations:**
- Color variation between bricks
- Mortar joints (recessed)
- Weathering on edges
- Moss/grass in joints

### 6.4 Cobblestone

**Properties:**
| Type | Stone Size | Gap |
|------|------------|-----|
| Traditional | 10-20cm | 1-2cm |
| Sett | 15-25cm | 1cm |
| Modern | 10-15cm | Tight |

### 6.5 Gravel

**Properties:**
- Base color: Tan, gray, brown
- Particle size: 5-20mm
- Roughness: High
- Displacement: Strong

---

## 7. Drainage

### 7.1 Storm Drains

**Dimensions:**
| Type | Grate Size | Depth |
|------|------------|-------|
| Curb Inlet | 60x30cm | Variable |
| Gutter Grate | 40x60cm | 30-60cm |
| Catch Basin | 60x60cm | 1-2m |

### 7.2 Gutters

**Dimensions:**
| Type | Width | Slope |
|------|-------|-------|
| Standard | 30-45cm | 2% toward drain |
| Valley Gutter | 45-60cm | 2-4% |

### 7.3 Manhole Covers

**Standard Sizes:**
| Load Class | Diameter | Use |
|------------|----------|-----|
| A15 | 60cm | Pedestrian |
| B125 | 60cm | Sidewalk |
| C250 | 60cm | Roadway |
| D400 | 60cm | Heavy traffic |

---

## 8. Geometry Nodes Architecture Patterns

### 8.1 Recommended Node Group Structure

```
road_system/
├── core/
│   ├── road_curve_to_mesh.blend     # Curve -> Road geometry
│   ├── lane_markings.blend          # Marking generator
│   ├── intersection_handler.blend   # Junction logic
│   └── terrain_projection.blend     # Terrain following
├── components/
│   ├── curb_generator.blend         # Curb profiles
│   ├── sidewalk_generator.blend     # Sidewalk geometry
│   ├── median_generator.blend       # Center islands
│   └── crosswalk_generator.blend    # Crosswalk stripes
├── furniture/
│   ├── sign_instancer.blend         # Traffic signs
│   ├── light_instancer.blend        # Street lights
│   ├── bench_instancer.blend        # Seating
│   └── misc_instancer.blend         # Trash, bollards, etc.
└── materials/
    ├── asphalt.blend                # Asphalt shader
    ├── concrete.blend               # Concrete shader
    └── marking_paint.blend          # Paint shader
```

### 8.2 Core Road Generation Pattern

```python
# Primary node flow
Input: Curve (road path)

1. Resample Curve
   - Count: Based on length and resolution
   - Output: Evenly spaced points

2. Set Curve Radius
   - Radius: Road width / 2
   - Can vary along curve for tapers

3. Curve to Mesh
   - Profile Curve: Rectangle (flat road surface)
   - Output: Road surface mesh

4. Set Material
   - Material: Asphalt shader

5. Additional layers (curb, sidewalk, markings)
   - Each as separate geometry
   - Joined at end
```

### 8.3 Instance on Points Pattern

```python
# For scattering elements along roads
Input: Road curve

1. Resample Curve (spacing parameter)
2. Curve to Points
   - Mode: Evaluated or Count
3. Instance on Points
   - Instance: Collection of objects
   - Pick Instances: True
   - Instance Index: Random or weighted
4. Align Rotation to Vector
   - Vector: Curve tangent
5. Scale Instances
   - Random variation if desired
```

### 8.4 Boolean Intersection Pattern

```python
# For creating holes in road surface (drains, etc.)
1. Road Mesh
2. Instance cutout geometry at positions
3. Mesh Boolean (Difference)
4. Result: Road with holes
```

---

## 9. Common Pitfalls

### 9.1 UV Mapping Issues

**Problem:** Road markings and textures stretch or distort on curved roads.

**Solution:**
- Use `Store Named Attribute` to capture curve parameter (0-1 along curve)
- Pass to shader for procedural UV mapping
- Or use `UV Unwrap` node in Geometry Nodes (Blender 4.0+)

### 9.2 Intersection Overlap

**Problem:** Roads at intersections create overlapping geometry.

**Solution:**
- Detect intersection points
- Create junction geometry separately
- Use Boolean operations to merge cleanly
- Or trim road curves at intersection boundaries

### 9.3 Scale Consistency

**Problem:** Real-world dimensions vs Blender units.

**Solution:**
- Set Blender units to meters (Scene Properties > Units)
- Use real-world dimensions for all components
- Scale imported assets consistently

### 9.4 Instance Performance

**Problem:** Too many instances cause performance issues.

**Solution:**
- Use instancing for repeating elements (signs, lights)
- Realize instances only when necessary
- Use LOD (Level of Detail) for distant objects
- Limit instance count with density parameters

### 9.5 Material Assignment

**Problem:** Multiple materials on single road mesh.

**Solution:**
- Use `Set Material` node with selection masks
- Store material index as attribute
- Or use vertex colors for material zones

---

## 10. Code Examples

### 10.1 Basic Road Generator (Python)

```python
import bpy
from lib.nodekit import NodeKit

def create_road_system(curve_obj, width=10.0):
    """
    Create procedural road from curve.

    Args:
        curve_obj: Blender curve object
        width: Road width in meters
    """
    # Create Geometry Nodes modifier
    mod = curve_obj.modifiers.new("RoadGenerator", "NODES")

    # Get or create node tree
    tree = bpy.data.node_groups.new("RoadTree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create node layout
    input_node = nk.group_input(0, 0)

    # Resample curve
    resample = nk.n("GeometryNodeResampleCurve", "Resample", 200, 0)

    # Set curve radius
    set_radius = nk.n("GeometryNodeSetCurveRadius", "SetRadius", 400, 0)

    # Create road profile (rectangle)
    profile = nk.n("GeometryNodeCurvePrimitiveQuadrilateral", "Profile", 400, -200)
    profile.inputs["Width"].default_value = width
    profile.inputs["Height"].default_value = 0.01  # Thin for road

    # Curve to mesh
    curve_to_mesh = nk.n("GeometryNodeCurveToMesh", "ToMesh", 600, 0)

    # Set material
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 800, 0)

    # Output
    output_node = nk.group_output(1000, 0)

    # Link nodes
    nk.link(input_node.outputs["Geometry"], resample.inputs["Curve"])
    nk.link(resample.outputs["Curve"], set_radius.inputs["Curve"])
    nk.link(set_radius.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    nk.link(profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
    nk.link(curve_to_mesh.outputs["Mesh"], set_mat.inputs["Geometry"])
    nk.link(set_mat.outputs["Geometry"], output_node.inputs["Geometry"])

    # Set radius input
    set_radius.inputs["Radius"].default_value = width / 2

    return mod
```

### 10.2 Lane Marking Generator (Python)

```python
def create_lane_markings(road_curve, offset=0, dash_length=3.0, gap_length=6.0):
    """
    Create dashed lane markings along road curve.

    Args:
        road_curve: Input road curve object
        offset: Lateral offset from center
        dash_length: Length of each dash
        gap_length: Length of gap between dashes
    """
    # This would be a separate Geometry Nodes tree
    # that takes road curve as input and outputs marking geometry

    pass  # Implementation follows same pattern as above
```

### 10.3 Street Light Instancer (Python)

```python
def create_street_light_instancer(road_curve, spacing=40.0, offset=6.0):
    """
    Instance street lights along road at specified spacing.

    Args:
        road_curve: Road curve object
        spacing: Distance between lights (meters)
        offset: Distance from road edge (meters)
    """
    # Node flow:
    # 1. Resample curve to get points at spacing
    # 2. Offset points perpendicular to curve
    # 3. Instance light pole collection on points
    # 4. Align rotation to curve normal

    pass  # Implementation follows same pattern
```

---

## 11. Existing Blender Tools Reference

### Commercial/Community Tools:

| Tool | Type | Features |
|------|------|----------|
| The Roads Must Roll | Geometry Nodes | 160+ settings, 12 intersections, car animation |
| ICity V1.7.1 | Addon | Complete city builder, roads, buildings |
| City Road Builder Pro | Addon | Road + intersection creation |
| Procedural Road Generator | Geometry Nodes | Basic road generation |
| Curvify | Geometry Nodes | Curve-based generators including roads |

### Blender Native Nodes Used:

| Node | Purpose |
|------|---------|
| Curve to Mesh | Core road surface generation |
| Resample Curve | Control point density |
| Set Curve Radius | Variable road width |
| Instance on Points | Scatter furniture/signs/lights |
| Align Rotation to Vector | Orient instances to curve |
| Boolean | Intersections, cutouts |
| Set Material | Material assignment |
| UV Unwrap | Procedural UV mapping |

---

## 12. Open Questions

### Cannot be fully resolved without further research:

1. **Terrain-Road Integration**
   - How to best project roads onto terrain mesh?
   - Cut vs. fill road profiles
   - Recommendation: Use Raycast node + terrain mesh

2. **Procedural Crack Patterns**
   - Realistic asphalt cracking requires advanced shader work
   - May need texture baking for performance
   - Recommendation: Start with voronoi + noise combinations

3. **Traffic Simulation Data**
   - Integrating traffic flow for road width optimization
   - Lane configuration based on traffic patterns
   - Recommendation: Out of scope, focus on static geometry

4. **Real-time Performance**
   - Large city scenes may need optimization
   - LOD systems for distant geometry
   - Recommendation: Implement LOD switches in node tree

---

## Sources

### Primary (HIGH confidence)
- Blender 5.0 Manual - Instance on Points Node (official docs)
- Blender 5.0 Manual - Geometry Nodes (official docs)

### Secondary (MEDIUM confidence)
- MUTCD Traffic Sign Standards (verified via FHWA)
- EN 124/EN 1433 Drainage Standards (European)
- City road design manuals (multiple sources)
- Commercial tool documentation (The Roads Must Roll, ICity)

### Tertiary (LOW confidence)
- Web search results for specific dimensions
- Community tutorials and forums
- Product listings (dimensions may vary by manufacturer)

---

## Metadata

**Confidence breakdown:**
- Road network algorithms: MEDIUM - L-system theory established, GN implementation requires custom work
- Geometry components: HIGH - Dimensions from official standards
- Street furniture: MEDIUM - Dimensions from product listings and general standards
- Materials: MEDIUM - PBR approach standard, specific shaders need development
- Geometry Nodes patterns: HIGH - Based on official Blender documentation

**Research date:** 2026-02-21
**Valid until:** 6 months (Blender development active)
