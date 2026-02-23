# Architecture Patterns: Charlotte NC Highway Vegetation

**Domain:** 3D Environment Creation - Highway Roadside Vegetation
**Researched:** 2026-02-22

## Recommended Architecture

### Zone-Based Vegetation Management System

Highway vegetation is structured in distinct zones based on distance from roadway, mirroring actual DOT management practices.

```
                         MEDIAN
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    │   PASSIVE ZONE        │    PASSIVE ZONE       │
    │   (15+ ft from road)  │    (15+ ft from road) │
    │                       │                       │
    │   Native grasses      │    Native grasses     │
    │   Shrubs              │    Shrubs             │
    │   Trees               │    Trees              │
    │                       │                       │
    ├───────────────────────┼───────────────────────┤
    │   ACTIVE ZONE         │    ACTIVE ZONE        │
    │   (0-15 ft from road) │    (0-15 ft from road)│
    │                       │                       │
    │   Maintained turf     │    Maintained turf    │
    │   Bermudagrass/Fescue │    Bermudagrass/Fescue│
    │                       │                       │
    ├───────────────────────┼───────────────────────┤
    │   SHOULDER            │    SHOULDER           │
    │   (Paved)             │    (Paved)            │
    │                       │                       │
    ├───────────────────────┼───────────────────────┤
    │      TRAVEL LANES     │    TRAVEL LANES       │
    │                       │                       │
    └───────────────────────┴───────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **Turf Layer** | 0-15 ft from shoulder, mowed grass | Seasonal system for color |
| **Native Grass Layer** | 15+ ft from shoulder, naturalized grasses | Seasonal system for fall color |
| **Shrub Layer** | Slopes, screening areas, median edges | Terrain system for placement |
| **Tree Layer** | Beyond clear zones, medians (wide) | Terrain system, lighting system |
| **Seasonal Controller** | Time-of-year based color/state changes | All vegetation layers |
| **Placement Rules** | Zone-based asset positioning | All vegetation layers |

### Data Flow

```
1. Terrain Geometry
        │
        v
2. Identify Zones (distance from roadway edge)
        │
        ├──> Active Zone (0-15 ft) ──> Place turf grass
        │
        ├──> Passive Zone (15+ ft) ──> Place native grasses
        │         │
        │         ├──> Slope areas ──> Add shrubs for stabilization
        │         │
        │         └──> Clear zone edge ──> Begin tree placement
        │
        v
3. Median Analysis
        │
        ├──> Width < 5 ft ──> Shrubs/groundcover only
        │
        └──> Width > 5 ft ──> Trees possible (spaced for safety)
        │
        v
4. Seasonal State Application
        │
        ├──> Summer ──> All green, full foliage
        │
        ├──> Fall ──> Deciduous color, Little Bluestem orange-red
        │
        ├──> Winter ──> Bermudagrass tan, deciduous bare
        │
        └──> Spring ──> Green-up, flowering trees
```

## Patterns to Follow

### Pattern 1: Zone-Based Height Gradient

**What:** Vegetation height increases with distance from roadway
**When:** All highway scenes for realism and DOT compliance
**Example:**

```
Distance from shoulder:  0ft      5ft      10ft     15ft     20ft     30ft    50ft
                         │        │        │        │        │        │       │
Grass height:           2-3"    2-3"     2-3"     4-6"     12-24"   24-36"  Native
                         │─────────────────│        │────────────────────────│
                         │   ACTIVE ZONE   │        │     PASSIVE ZONE       │
                         │   (Maintained)  │        │   (Naturalized)        │
```

### Pattern 2: Bermudagrass Dormancy Color Shift

**What:** Bermudagrass color shifts from emerald green to tan/brown November through March
**When:** Any scene set in winter months
**Example:**

```python
# Seasonal color blend factor (0 = full green, 1 = full dormant)
def get_dormancy_blend(month):
    if month in [11, 12, 1, 2, 3]:  # Nov-Mar
        return 1.0  # Fully dormant (tan/brown)
    elif month == 4:  # April - greening up
        return 0.5   # Transitional
    elif month == 10:  # October - starting dormancy
        return 0.3   # Light browning
    else:  # May-September
        return 0.0   # Full green

# Color interpolation
green = RGB(0.2, 0.6, 0.2)   # Emerald green
dormant = RGB(0.6, 0.5, 0.3) # Tan/straw brown
final_color = lerp(green, dormant, get_dormancy_blend(current_month))
```

### Pattern 3: Median Width-Based Planting

**What:** Median planting varies by available width
**When:** All median areas
**Example:**

```
Median Width    | Vegetation Type
---------------|------------------
< 4 ft         | Low groundcover only (juniper)
4-8 ft         | Shrubs allowed, no trees
8-16 ft        | Small trees allowed (Crape Myrtle size)
> 16 ft        | Full tree species allowed with proper spacing
```

### Pattern 4: Tree Species Proximity Rules

**What:** Tree species placement based on context
**When:** All tree placement
**Example:**

```
Location              | Preferred Species           | Avoid
----------------------|------------------------------|------------------
Median (narrow)       | Crape Myrtle, small Oaks     | Large pines
Interchange ramps     | Crape Myrtle, Dogwood,       | Fast-growing
                      | Redbud                       | weak-wooded species
Beyond clear zone     | Loblolly Pine, Oaks,         | Invasive species
                      | Sweetgum, Tulip Poplar       |
Slopes (erosion)      | Trees with deep roots:       | Shallow-rooted
                      | Oaks, Hickories              | species
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Uniform Green Year-Round

**What:** Keeping Bermudagrass green in winter
**Why bad:** Breaks regional authenticity, Charlotte winters show dormant grass
**Instead:** Implement seasonal color shift to tan/straw November-March

### Anti-Pattern 2: Trees in Clear Zone

**What:** Placing trees within 15 feet of roadway shoulder
**Why bad:** Violates safety standards, unrealistic for maintained highway
**Instead:** Enforce minimum 15-foot offset from shoulder to tree trunk

### Anti-Pattern 3: Monoculture Tree Stands

**What:** All same tree species in an area
**Why bad:** Natural highways have mixed species, monoculture looks artificial
**Instead:** Mix Loblolly Pine, Oaks, Sweetgum with natural distribution ratios (40% Pine, 30% Oak, 20% Sweetgum, 10% other)

### Anti-Pattern 4: Perfectly Flat Turf

**What:** Golf-course smooth grass surface
**Why bad:** Highway grass has imperfections, variations, slight undulations
**Instead:** Add subtle height variation, slight thinning, occasional bare patches

### Anti-Pattern 5: Generic "Pine Tree"

**What:** Using a generic pine model without species-specific characteristics
**Why bad:** Loblolly Pine has distinct 3-needle bundles, 6-9" length
**Instead:** Use accurate Loblolly Pine geometry with correct needle count and length

## Scalability Considerations

| Concern | At 100m stretch | At 1km stretch | At 5km stretch |
|---------|-----------------|----------------|----------------|
| **Turf detail** | Full geometry | Geometry + imposters | Imposters dominant |
| **Native grass** | Full geometry | Instanced geometry | LOD with imposters |
| **Trees** | Full geometry | LOD system essential | Aggressive LOD |
| **Seasonal update** | Real-time | Batch updates | Area-based streaming |
| **Draw calls** | Manageable | Instancing critical | GPU instancing required |

## I-277 Specific Considerations

Based on AARoads guide and research, I-277 characteristics:

| Segment | Vegetation Context |
|---------|-------------------|
| **Brookshire Freeway (North)** | Urban corridor, limited median width, Crape Myrtle at interchanges |
| **Belk Freeway (South)** | Stadium-adjacent, maintained landscaping, trees in wider areas |
| **East end** | Connects to Independence Blvd, transitional landscaping |
| **West end** | Connects to I-77/Wilkinson Blvd, mature tree stands |

**Median widths on I-277:** Generally narrower than rural highways due to urban constraints, limiting tree placement in medians.

## Sources

- NCHRP 14-40 Report: Vegetation Management Patterns
- AARoads I-277 Guide: Highway corridor characteristics
- NC State Extension: Grass maintenance patterns
- FHWA NC Native Plants: Species recommendations
- General DOT vegetation management research
