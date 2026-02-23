# Feature Landscape: Charlotte NC Highway Vegetation

**Domain:** 3D Environment Creation - Highway Roadside Vegetation
**Researched:** 2026-02-22

## Table Stakes

Features users expect in realistic Charlotte highway vegetation. Missing = scene feels incorrect.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Green grass in summer** | Default expectation for any US highway scene | Low | Bermudagrass emerald green or Fescue dark green |
| **Trees along highway** | Every highway has trees in NC Piedmont | Medium | Loblolly Pine, Oaks, Sweetgum common |
| **Mowed grass strip near road** | Safety requirement, regularly maintained | Low | 15-foot clear zone from shoulder |
| **Seasonal variation** | NC has distinct seasons, users notice | Medium | Spring green, summer lush, fall color, winter brown |
| **Mixed species** | Monoculture looks artificial | High | Mix of Bermudagrass/Fescue, multiple tree species |
| **Taller vegetation away from road** | Natural progression of mowing zones | Medium | Taller grasses, then shrubs, then trees |

## Differentiators

Features that set apart realistic Charlotte highway scenes from generic environments.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Accurate winter dormant grass** | Tan/brown Bermudagrass Nov-Mar shows attention to detail | Medium | Most 3D scenes show perpetual summer |
| **Native warm-season grasses** | Switchgrass, Little Bluestem in passive zones | High | Adds ecological accuracy, visual texture |
| **Little Bluestem fall color** | Orange-red fall foliage is distinctive to region | Medium | Strong visual impact in autumn scenes |
| **Loblolly Pine dominance** | 3-needle, 6-9" needles, most common NC highway pine | Medium | Distinguish from other pines by needle count |
| **Crape Myrtle at interchanges** | Long-blooming ornamental, Charlotte signature | High | Pink/red/white blooms summer-fall |
| **Zone-based vegetation height** | Short near road → Medium → Tall creates visual layers | High | Mirrors actual DOT management practice |
| **Golden Indiangrass plumes** | Fall seed heads catch light beautifully | Medium | Adds seasonal vertical interest |
| **Sweetgum star leaves** | Distinctive leaf shape, multicolor fall display | Medium | Recognizable silhouette |

## Anti-Features

Features to explicitly NOT build. Common mistakes in highway vegetation scenes.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Perpetually green Bermudagrass** | Bermudagrass goes dormant (brown) Nov-Mar in NC | Implement seasonal color shift to tan/straw |
| **Generic "pine tree"** | Different pines have distinct needle counts and lengths | Use Loblolly Pine (3 needles, 6-9") as dominant species |
| **Kentucky Bluegrass** | Poor heat tolerance, rarely used in Charlotte highway applications | Use Bermudagrass or Tall Fescue instead |
| **Palm trees** | Not native to Charlotte, would break realism | Use native pines, oaks, sweetgum instead |
| **Perfectly uniform grass** | Highway grass has variation, weeds, bare patches | Add noise, variation in height and color |
| **Trees in clear zone** | Safety requirement prevents trees within 15+ feet of road | Keep trees back from roadway edge |
| **Fall color on evergreens** | Loblolly Pine stays green year-round | Only apply fall color to deciduous species |
| **Spring flowers everywhere** | Wildflowers are limited to specific planted areas | Use sparingly, near interchanges or designated areas |
| **Impossibly manicured turf** | Highway grass is not golf-course perfect | Add imperfections, varying mow heights |
| **Non-native invasive species** | Bradford Pear, Tree of Heaven are invasive problems | Use native species from FHWA list |

## Feature Dependencies

```
Base Terrain
    |
    v
Turf Grass System (Bermudagrass + Tall Fescue)
    |
    +---> Seasonal Color Control (summer green / winter brown)
    |
    v
Passive Zone Native Grasses
    |
    +---> Little Bluestem (fall color requires seasonal system)
    +---> Indiangrass (seed heads require geometry)
    |
    v
Shrub Layer
    |
    +---> Sumac, Wax Myrtle, Native Roses
    |
    v
Tree Placement System
    |
    +---> Loblolly Pine (most common, establish first)
    +---> Oaks (Willow, Red, White)
    +---> Sweetgum (distinctive shape)
    +---> Crape Myrtle (interchanges only)
    |
    v
Seasonal Variant Integration
    |
    +---> Spring: Green-up, early bloomers (Redbud, Dogwood)
    +---> Summer: Peak green, Crape Myrtle blooms
    +---> Fall: Deciduous color, Little Bluestem orange-red
    +---> Winter: Dormant Bermudagrass tan, evergreen pines
```

## Visual Zone Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     TREE LAYER (40-100 ft)                      │
│   Loblolly Pine | Oaks | Sweetgum | Tulip Poplar                │
│   (Beyond clear zone, median where width allows)                │
├─────────────────────────────────────────────────────────────────┤
│                    SHRUB LAYER (3-12 ft)                        │
│   Sumac | Wax Myrtle | Native Roses                             │
│   (Transition zone, screening, slope stabilization)             │
├─────────────────────────────────────────────────────────────────┤
│               NATIVE GRASS LAYER (2-6 ft)                       │
│   Switchgrass | Little Bluestem | Indiangrass                   │
│   (Passive zone, 15+ ft from shoulder, naturalized)             │
├─────────────────────────────────────────────────────────────────┤
│                  TURF GRASS LAYER (2-6 in)                      │
│   Bermudagrass (dormant tan in winter)                          │
│   Tall Fescue (green year-round in shade)                       │
│   (Active zone, 0-15 ft from shoulder, regularly mowed)         │
└─────────────────────────────────────────────────────────────────┘
                         │
                    ROADWAY
                         │
                    SHOULDER
```

## MVP Recommendation

For MVP vegetation system, prioritize:

1. **Turf Grass with Seasonal Color** - Covers most visible area
   - Bermudagrass shader with green/tan seasonal blend
   - 15-foot mowed zone from shoulder

2. **Loblolly Pine Trees** - Most common highway tree
   - 3-needle geometry, 6-9" length
   - Place beyond clear zone, in medians

3. **One Native Grass** - Little Bluestem
   - Adds visual interest to passive zone
   - Distinctive fall color option

Defer to post-MVP:
- **Crape Myrtle blooms**: Requires complex shader setup, interchange-specific
- **Full shrub layer**: Detail enhancement, not core visual
- **Wildflower areas**: Limited distribution, specialized planting

## Seasonal Scene Presets

| Season | Grass Color | Tree Status | Special Features |
|--------|-------------|-------------|------------------|
| **Early Spring** (Mar-Apr) | Bermudagrass greening up, Fescue dark green | Deciduous leafing out, Dogwood/Redbud blooms | Pink/white flowering trees |
| **Late Spring** (May) | Full green | Full leaf | Lush green everywhere |
| **Summer** (Jun-Aug) | Bermudagrass emerald, Fescue may fade | Full leaf | Crape Myrtle blooms (pink/red/white) |
| **Early Fall** (Sep) | Green fading | Green, some yellow | Indiangrass golden plumes |
| **Peak Fall** (Oct) | Green to yellow | Red/orange/yellow | Little Bluestem orange-red |
| **Late Fall** (Nov) | Bermudagrass browning | Leaves dropping | Skeleton trees visible |
| **Winter** (Dec-Feb) | Bermudagrass tan/straw | Deciduous bare, evergreens green | Stark, brown grass dominant |
| **Early Spring** (Mar) | Bermudagrass still brown | Buds swelling | Transitional appearance |

## Sources

- NC State Extension Publications
- Wilson's Natural Landscaping - Native Grasses
- FHWA NC Native Plants List
- NCHRP 14-40 Vegetation Management Report
- LawnStarter Charlotte Grass Guide
