# Research Summary: Charlotte NC Highway Roadside Vegetation

**Domain:** 3D Environment Creation - Charlotte Digital Twin Highway Vegetation
**Researched:** 2026-02-22
**Overall confidence:** MEDIUM (Ecosystem data solid, specific I-277 imagery limited)

## Executive Summary

Charlotte NC's highway vegetation is defined by the **Piedmont transition zone climate**, creating a unique blend of warm-season and cool-season grasses alongside diverse native tree species. The I-277 inner loop encircling Uptown Charlotte traverses urban highway corridors with maintained grass verges, native shrub plantings, and strategic tree placement.

**Key vegetation characteristics:**
- Grasses dominated by Bermudagrass (brown/tan in winter, emerald green in summer) and Tall Fescue (year-round green)
- Native warm-season grasses including Switchgrass, Little Bluestem, and Indiangrass for erosion control
- Tree species dominated by Loblolly Pine, various Oaks (Willow, Red, White), Sweetgum, and Tulip Poplar
- Crape Myrtles extensively used as urban ornamental trees near highway interchanges

**Seasonal appearance is dramatic:**
- Spring/Summer: Vibrant greens, active growth
- Fall: Little Bluestem turns orange-red, native grasses show golden plumes
- Winter: Bermudagrass/Zoysia turn tan/brown; Tall Fescue remains green

**Vegetation management follows zone-based mowing patterns:**
- Active Zone (15 feet from shoulder): Regularly mowed for safety
- Passive Zone (beyond 15 feet): Naturalized with native vegetation

## Key Findings

**Stack:** Native grasses + Bermudagrass/Tall Fescue turf mix; Loblolly Pine, Oak species, Sweetgum, Tulip Poplar trees; native shrubs (Sumac, Wax Myrtle, native roses)

**Architecture:** Zone-based vegetation management creates visual layers - manicured turf near roadway transitioning to naturalized native grasses and wildflowers, with trees in medians and beyond clear zones

**Critical pitfall:** Bermudagrass goes dormant (tan/brown) November-March. 3D scenes set in winter must show brown grass, not green, unless specifically using Tall Fescue areas.

## Implications for Roadmap

Based on research, suggested phase structure for Charlotte highway vegetation creation:

1. **Base Grass System** - Establish grass shader system with seasonal color control
   - Addresses: Bermudagrass and Tall Fescue seasonal appearance
   - Avoids: Pitfall of incorrect winter grass color

2. **Native Warm-Season Grasses** - Add Switchgrass, Little Bluestem, Indiangrass
   - Addresses: Naturalized vegetation in passive zones beyond mowed areas
   - Provides: Fall color interest (orange-red, golden plumes)

3. **Tree Placement System** - Loblolly Pine, Oaks, Sweetgum, Tulip Poplar
   - Addresses: Highway median and roadside tree species
   - Avoids: Using non-native species that would look incorrect

4. **Shrub Layer** - Native sumac, wax myrtle, native roses
   - Addresses: Groundcover and understory vegetation
   - Provides: Visual transition between grass and trees

5. **Seasonal Variant System** - Spring/Summer/Fall/Winter presets
   - Addresses: Need for accurate seasonal appearance
   - Avoids: One-season-fits-all approach

**Phase ordering rationale:**
- Grass system first (covers most area, sets visual baseline)
- Native grasses second (adds visual interest, fills passive zones)
- Trees third (major vertical elements, species-specific placement)
- Shrubs fourth (transition layer, detail)
- Seasonal system throughout or as final integration pass

**Research flags for phases:**
- Phase 1 (Grass): Standard patterns, well-documented species
- Phase 2 (Native Grasses): May need deeper research into individual species appearance
- Phase 3 (Trees): Well-documented species, but placement patterns need verification
- Phase 4 (Shrubs): Standard native plantings, moderate research depth
- Phase 5 (Seasonal): Critical for realism, needs validation of color timing

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack (Grass) | HIGH | NC State Extension, multiple sources confirm Bermudagrass/Fescue dominance |
| Stack (Trees) | HIGH | FHWA NC Native Plants list, NC State Extension tree guide |
| Features | MEDIUM | General patterns documented, I-277 specific imagery limited |
| Architecture | MEDIUM | Zone-based mowing patterns from general DOT research, not NC-specific |
| Pitfalls | HIGH | Bermudagrass dormancy well-documented, seasonal colors verified |

## Gaps to Address

- **Flickr Reference Images:** Could not find specific I-277 photos on Flickr; recommend direct site search or Google Images with `site:flickr.com`
- **NCDOT Specific Guidelines:** Official NC mowing schedules and vegetation standards not publicly accessible online
- **Median Tree Spacing:** General highway standards found, but NC-specific median planting guidelines need NCDOT contact
- **Wildflower Program:** NC wildflower program details sparse; may need direct NCDOT contact
- **Exact I-277 Vegetation:** No species-by-species breakdown for I-277 specifically found

## Key Reference URLs

### Authoritative Sources
- **NC State Extension - Lawns:** https://content.ces.ncsu.edu/extension-gardener-handbook/9-lawns
- **NC State Extension - Tree ID:** https://content.ces.ncsu.edu/identification-of-common-trees-of-north-carolina
- **FHWA NC Native Plants:** https://www.environment.fhwa.dot.gov/env_topics/ecosystems/roadside_use/vegmgmt_rd_nc.aspx
- **NC Native Grasses (Wilson's):** https://www.wilsonsnaturallandscaping.com/posts/ten-native-grasses-to-use-in-your-charlotte-landscape

### Highway Reference
- **AARoads I-277 Guide:** https://www.aaroads.com/guides/i-277-nc (contains photos of I-277 corridors)
- **Wikipedia I-77:** https://en.wikipedia.org/wiki/Interstate_77
- **Wikipedia I-85 NC:** https://en.wikipedia.org/wiki/Interstate_85_in_North_Carolina

### Vegetation Management Research
- **NCHRP 14-40 Report:** https://www.researchgate.net/publication/358742068 (mowing vs managed succession)
- **Pollinator Habitat Along Roadways:** https://nap.nationalacademies.org/read/27061/chapter/7

---

## Files Created

| File | Purpose |
|------|---------|
| .planning/research/HIGHWAY_VEGETATION_SUMMARY.md | Executive summary with roadmap implications |
| .planning/research/HIGHWAY_VEGETATION_STACK.md | Grass and tree species recommendations |
| .planning/research/HIGHWAY_VEGETATION_FEATURES.md | Feature landscape for highway vegetation |
| .planning/research/HIGHWAY_VEGETATION_ARCHITECTURE.md | Vegetation zones and placement patterns |
| .planning/research/HIGHWAY_VEGETATION_PITFALLS.md | Domain pitfalls and prevention |

## Ready for Roadmap

Research complete. Proceeding to roadmap creation with the above findings documented in detail across the vegetation research files.
