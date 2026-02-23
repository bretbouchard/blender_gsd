# Research Summary: Charlotte NC Urban Environment Textures

**Domain:** Photorealistic 3D rendering materials for Charlotte Digital Twin
**Researched:** 2026-02-22
**Mode:** Ecosystem Survey
**Overall Confidence:** MEDIUM

---

## Executive Summary

This research surveyed Charlotte NC urban environment textures and materials for photorealistic 3D rendering. Charlotte presents a unique architectural landscape combining historic Victorian brick homes (Fourth Ward district) with modern glass-and-steel skyscrapers (Duke Energy Center, Bank of America Corporate Center). The humid subtropical climate significantly impacts material weathering through high humidity, year-round precipitation, and temperature extremes.

Key findings: Charlotte's building materials reflect its evolution from 19th-century textile town to modern banking center. The Piedmont red clay soils, distinctive weathering patterns from humid climate, and blend of historic and contemporary architecture create specific material requirements for realistic rendering.

---

## Key Findings

**Brick Materials:** Historic Fourth Ward features Victorian red/brown brick with concave or flush mortar joints, weathered by mold/algae growth in the humid climate.

**Glass Curtain Walls:** Duke Energy Center uses "cut crystal" design with 45,000+ LED lights; typical mullion spacing is 1.2-1.5m horizontal, 1.5-2.0m vertical; common tints are blue, green, gray.

**Concrete Infrastructure:** I-77/I-85 highway systems and parking decks show lichen growth, water staining, efflorescence, and cracking patterns from Charlotte's freeze-thaw cycles.

**Ground Cover:** Piedmont region features red clay ultisols with tall fescue/bermudagrass; 75%+ vegetation coverage needed for erosion control; concrete sidewalks with broom finish and 20-30 foot expansion joints.

**Climate Impact:** Humid subtropical (Cfa) with 1105mm annual precipitation, temperatures from -21C to 40C+ causes accelerated weathering on all materials.

---

## Files Created

| File | Purpose |
|------|---------|
| CHARLOTTE_URBAN_TEXTURES.md | Comprehensive material/texture reference with PBR workflow recommendations |

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Climate Data | HIGH | Multiple consistent sources |
| Brick/Mortar Types | HIGH | Standard masonry documentation |
| Glass Curtain Wall Specs | MEDIUM | Industry standards available, Charlotte-specific limited |
| Concrete Weathering | MEDIUM | General knowledge applied, specific photo reference limited |
| Ground/Vegetation | MEDIUM | NC Extension reliable, Charlotte imagery sparse |
| Reference Image URLs | LOW | Site-specific searches yielded limited results |

---

## Implications for Roadmap

### Suggested Phase Structure:

1. **Material Library Foundation** - Establish base PBR materials for brick, concrete, glass, ground
   - Addresses: Core material requirements for all Charlotte scenes
   - Uses: Poliigon/Quixel as base sources

2. **Climate Weathering System** - Implement Charlotte-specific weathering patterns
   - Addresses: Humid subtropical aging effects (algae, efflorescence, water staining)
   - Avoids: Generic weathering that does not match regional characteristics

3. **Building Material Presets** - Create Charlotte-specific building material presets
   - Addresses: Fourth Ward brick, Duke Energy glass, Bank of America granite
   - Uses: Documented specifications from research

4. **Ground Surface System** - Implement Piedmont-specific ground materials
   - Addresses: Red clay soils, regional grass types, concrete sidewalks
   - Uses: NC Extension grass recommendations

### Phase Ordering Rationale:
- Material library first (foundation for all subsequent work)
- Weathering system second (applies to all materials)
- Building presets third (combines materials + weathering)
- Ground system fourth (completes environment)

### Research Flags for Phases:
- **Phase 1 (Material Library):** Standard patterns, unlikely to need deeper research
- **Phase 2 (Weathering):** May need specific Charlotte photo reference collection
- **Phase 3 (Building Presets):** Could benefit from architectural photography of specific Charlotte buildings
- **Phase 4 (Ground System):** NC Extension data sufficient, may want field photography

---

## Open Questions

1. **Photo Reference Collection:** Would benefit from manual photography or Google Street View capture of specific Charlotte locations
2. **Glass Specifications:** Exact tint values and reflectance for Charlotte skyscrapers not documented
3. **Seasonal Variations:** Spring/summer grass appearance vs. winter dormancy needs further study
4. **Building-Specific Details:** Interior lobby materials, specific architectural details not covered

---

## Key Reference URLs

| Category | Source | URL |
|----------|--------|-----|
| Skyscraper Data | CTBUH - Duke Energy Center | https://www.skyscrapercenter.com/building/duke-energy-center/1077 |
| Architecture | e-architect - Bank of America | https://www.e-architect.com/articles/bank-of-america-corporate-center |
| Stock Photos | Wikimedia Commons - BoA | https://commons.wikimedia.org/wiki/Category:Bank_of_America_Corporate_Center |
| Grass/Lawn | NC State Extension | https://content.ces.ncsu.edu/extension-gardener-handbook/9-lawns |
| PBR Textures | Poliigon | https://www.poliigon.com |
| Free PBR | Quixel Megascans (UE free) | https://www.quixel.com/megascans/free |

---

## Ready for Roadmap

Research complete. The CHARLOTTE_URBAN_TEXTURES.md file contains comprehensive material specifications, PBR workflow recommendations, and reference URLs for photorealistic Charlotte digital twin rendering.
