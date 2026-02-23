# Charlotte Digital Twin - Complete Reference Guide

**Generated**: 2026-02-22
**Purpose**: Master reference document for all Charlotte photorealism research

---

## Quick Reference: Key URLs

### Building Reference Photos
| Building | Best Source | URL |
|----------|-------------|-----|
| Bank of America Corporate Center | Wikimedia Commons | https://commons.wikimedia.org/wiki/Category:Bank_of_America_Corporate_Center |
| Duke Energy Center | CTBUH | https://www.skyscrapercenter.com/building/duke-energy-center/1077 |
| One Wells Fargo | Wikipedia List | https://en.wikipedia.org/wiki/List_of_tallest_buildings_in_Charlotte |
| BoA Architecture | e-architect | https://www.e-architect.com/articles/bank-of-america-corporate-center |

### Highway Infrastructure Photos
| Topic | Source | URL |
|-------|--------|-----|
| I-277 Photos (25+) | AARoads | https://www.aaroads.com/guides/i-277-nc |
| Barrier Standards | AASHTO M 180-2023 | Technical specification |
| Bridge Design | AASHTO LRFD 9th Ed | Technical specification |

### Texture Resources
| Type | Source | URL |
|------|--------|-----|
| PBR Textures (Free) | Poly Haven | https://polyhaven.com/textures |
| PBR Materials (Free) | AmbientCG | https://ambientcg.com |
| Premium Textures | Poliigon | https://www.poliigon.com |
| Free Scans (UE) | Quixel | https://www.quixel.com/megascans/free |

---

## 1. Charlotte Skyline Buildings

### Bank of America Corporate Center
**Height**: 265m (871 ft) | **Floors**: 60 | **Year**: 1992
**Architect**: Cesar Pelli | **Style**: Postmodern

**Key Visual Features:**
- **Crown**: 95-foot illuminated granite crown (iconic)
- **Cladding**: Rosy beige granite (NOT glass!)
- **Form**: Six setbacks creating elegant taper
- **Lighting**: LED system added 2017, often blue for Panthers games

**Modeling Notes:**
- Create emissive material for crown
- Six distinct setback levels
- Granite texture with rosy/pink undertone

### Duke Energy Center (550 South Tryon)
**Height**: 240m (786 ft) | **Floors**: 48 | **Year**: 2010
**Architect**: tvsdesign | **Style**: Contemporary Smart Building

**Key Visual Features:**
- **Facade**: 45,000+ LED lights, hourly light shows
- **Crown**: "Handlebar" structure 20m+ above roof
- **Glass Fins**: Colored glass by Kenneth von Roenn
- **Design**: "Cut crystal" chiseled upper quadrant

**Modeling Notes:**
- Complex LED facade system (geometry nodes?)
- Distinctive handlebar crown structure
- Multiple glass fin elements

### One Wells Fargo Center (301 South College)
**Height**: 179m (588 ft) | **Floors**: 42 | **Year**: 1988
**Style**: Postmodern | **Nickname**: "The Jukebox"

**Key Visual Features:**
- **Crown**: Distinctive rounded top
- **Form**: Classic postmodern silhouette
- **Material**: Glass curtain wall

---

## 2. Highway Infrastructure

### Concrete Barriers
| Type | Height | Profile | Use Case |
|------|--------|---------|----------|
| **Jersey Barrier** | 90-150cm | Convex | Most common, precast |
| **F-Shape** | 90-150cm | Improved | Newer construction |

**Precast Sections**: 4-6 meters long

### Support Columns
| Type | Dimensions | Features |
|------|------------|----------|
| **A-Type** | 1.4m x 1.2m | Rectangular, chamfered corners |
| **B/C-Type** | Variable | Trumpet-shaped widening upward |

**Vehicle Protection**: Required within 30 ft of roadway

### Road Surface
| Layer | Thickness | Material |
|-------|-----------|----------|
| Surface | 40mm | SBS modified asphalt |
| Middle | 60mm | Asphalt concrete |
| Base | 300mm | Aggregate base |
| **Total** | ~400mm | Multi-layer |

**Design Life**: 12-15 years
**Cross Slope**: 3%
**Shoulder Width**: 3.0-3.5m

### Highway Lighting
- **Pole Height**: 30-50 ft
- **Material**: Steel, hot-dip galvanized
- **Wind Load**: 110 mph design
- **Compliance**: AASHTO LTS, ANSI C136

---

## 3. Urban Textures

### Brick (Fourth Ward Historic District)
| Characteristic | Value |
|----------------|-------|
| **Color** | Red/brown Victorian brick |
| **Mortar** | Concave or flush joints |
| **Weathering** | Algae, efflorescence, mortar erosion |
| **Climate Impact** | Humid subtropical accelerates aging |

### Glass Curtain Walls
| Parameter | Typical Value |
|-----------|---------------|
| **Mullion Spacing (H)** | 1.2-1.5m |
| **Mullion Spacing (V)** | 1.5-2.0m |
| **Common Tints** | Blue, green, gray, bronze |
| **Coating** | Low-E standard |

### Concrete Weathering Patterns
- Water staining (vertical streaks)
- Efflorescence (white salt deposits)
- Lichen/mold growth (humid climate)
- Carbonation surface layer
- Freeze-thaw cracking

### Ground Cover (Piedmont Region)
| Material | Characteristics |
|----------|-----------------|
| **Soil** | Red clay ultisols (iron oxide) |
| **Sidewalk** | Broom finish concrete, 20-30ft expansion joints |
| **Grass** | Tall fescue/bermudagrass, 75%+ coverage |

---

## 4. Roadside Vegetation

### Grass Species (Dominant)
| Species | Coverage | Seasonal Color |
|---------|----------|----------------|
| **Bermudagrass** | 60% | Green (Apr-Oct), TAN/BROWN (Nov-Mar) ⚠️ |
| **Tall Fescue** | 30% | Green most of year |
| **Zoysia** | 10% | Green (May-Oct), Tan (Nov-Apr) |

**CRITICAL**: Bermudagrass MUST be tan/brown in winter scenes!

### Native Grasses (Passive Zones)
| Species | Height | Fall Color |
|---------|--------|------------|
| **Switchgrass** | 3-6 ft | Golden bronze |
| **Little Bluestem** | 2-4 ft | Orange-red |
| **Indiangrass** | 3-5 ft | Golden plumes |

### Tree Species (Highway)
| Species | Needles/Leaves | Notes |
|---------|----------------|-------|
| **Loblolly Pine** | 3 needles, 6-9" | Most common highway pine |
| **Willow Oak** | Narrow leaves | Common urban |
| **Red Oak** | Lobed leaves | Fall color |
| **Sweetgum** | Star-shaped | Fall color, spiky fruit |
| **Tulip Poplar** | Tulip-shaped leaves | Tall, straight |

### Zone-Based Vegetation
| Zone | Distance | Vegetation |
|------|----------|------------|
| **Active** | 0-15 ft | Mowed turf (bermudagrass) |
| **Passive** | 15+ ft | Native grasses → shrubs → trees |

---

## 5. Seasonal Color Reference

### Grass Colors
| Season | Bermudagrass | Tall Fescue | Little Bluestem |
|--------|--------------|-------------|-----------------|
| **Spring** | Light green | Green | Blue-green |
| **Summer** | Emerald green | Dark green | Blue-green |
| **Fall** | Green → tan | Green | Orange-red |
| **Winter** | TAN/BROWN | Green (dormant) | Tan |

### Tree Foliage
| Season | Oaks | Sweetgum | Tulip Poplar |
|--------|------|----------|--------------|
| **Spring** | Light green | Light green | Bright green |
| **Summer** | Dark green | Dark green | Green |
| **Fall** | Red/brown | Red/orange/yellow | Yellow |
| **Winter** | Brown (some hold) | Bare | Bare |

---

## 6. Climate Context

**Charlotte Climate**: Humid Subtropical (Cfa)
| Parameter | Value |
|-----------|-------|
| **Annual Precipitation** | 1105mm (43.5 in) |
| **Summer High** | 33°C (91°F) |
| **Winter Low** | -1°C (30°F) |
| **Extreme Range** | -21°C to 40°C+ |
| **Humidity** | High year-round |

**Material Impact**:
- Accelerated weathering on all surfaces
- Algae/mold growth common
- Efflorescence on concrete/brick
- Lichen on shaded surfaces

---

## 7. Research Files Index

| File | Content |
|------|---------|
| `CHARLOTTE_SKYLINE_REFERENCE.md` | Building details, URLs |
| `CHARLOTTE_I277_HIGHWAY_INFRASTRUCTURE_RESEARCH.md` | Highway specs, barrier types |
| `CHARLOTTE_URBAN_TEXTURES.md` | Material specifications |
| `CHARLOTTE_TEXTURES_SUMMARY.md` | Texture workflow |
| `HIGHWAY_VEGETATION_STACK.md` | Grass/tree species |
| `HIGHWAY_VEGETATION_ARCHITECTURE.md` | Zone placement rules |
| `HIGHWAY_VEGETATION_PITFALLS.md` | Common mistakes to avoid |
| `ASSET_INVENTORY.md` | Existing assets, external resources |

---

## 8. Next Steps

### Immediate Priorities
1. ✅ Research complete - all reference docs created
2. ⬜ Copy Trash Kit textures to project assets
3. ⬜ Download additional PBR textures from Poly Haven
4. ⬜ Update material systems with Charlotte-specific presets

### Texture Downloads Needed
- [ ] Asphalt with wet variant
- [ ] Concrete with weathering
- [ ] Red brick with mortar
- [ ] Glass curtain wall reference
- [ ] Red clay soil texture
- [ ] Bermudagrass (green AND tan variants)

### Material System Updates
- [ ] Add seasonal grass color presets
- [ ] Create Charlotte granite material (BoA)
- [ ] Create LED facade material (Duke Energy)
- [ ] Add humid weathering effects
