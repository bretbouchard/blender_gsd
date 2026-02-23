# Research Summary: Charlotte NC Downtown Skyline

**Domain:** 3D modeling reference / architectural visualization
**Researched:** 2026-02-22
**Overall confidence:** HIGH

## Executive Summary

Charlotte, North Carolina ("The Queen City") has a concentrated, iconic skyline dominated by banking headquarters towers. As the second-largest banking center in the US after New York City, Charlotte's Uptown district features three particularly distinctive skyscrapers ideal for 3D modeling:

1. **Bank of America Corporate Center** (1992) - The tallest at 265m/871ft with a distinctive illuminated granite crown, designed by renowned architect Cesar Pelli. Postmodern style with rosy beige granite cladding and six setbacks creating an elegant taper.

2. **Duke Energy Center / 550 South Tryon** (2010) - 240m/786ft with a crystalline glass facade and integrated 45,000+ LED lighting system. Features a unique "handlebar" crown structure and hourly light shows. LEED Platinum certified.

3. **One Wells Fargo Center / 301 South College** (1988) - 179m/588ft with a distinctive rounded "jukebox" crown. Charlotte's first postmodern high-rise and tallest building in the 1980s.

The research reveals important naming clarifications: The term "Wells Fargo Capital Center" does not exist as an official building name. The 42-floor Wells Fargo building is "One Wells Fargo Center" at 301 South College Street. The Duke Energy Center (formerly Wachovia Corporate Center) is at 550 South Tryon and has 48 floors, not 42.

## Key Findings

**Stack:** Reference photography from Wikimedia Commons, CTBUH, and e-architect. All three buildings are well-documented with professional photos available.

**Architecture:** Postmodern (BoA Center, One Wells Fargo) and Contemporary Smart Building (Duke Energy). Key features include illuminated crowns, LED facades, and distinctive rooftop structures.

**Critical pitfall:** Naming confusion between multiple Wells Fargo-named buildings in Charlotte and other NC cities. Must use correct addresses and floor counts.

## Implications for Roadmap

Based on research, suggested phase structure for 3D modeling project:

1. **Foundation - Reference Gathering**
   - Download high-res photos from verified sources
   - Capture Google Earth 3D views for proportions
   - Document material references (granite, glass, LED)
   - Addresses: Correct building identification critical

2. **Core Modeling - Bank of America Corporate Center**
   - Priority: Most iconic, tallest, best documented
   - Key features: Six setbacks, 95-foot illuminated crown, granite cladding
   - Material focus: Rosy beige granite, silver-tinted glass

3. **Advanced Modeling - Duke Energy Center**
   - Priority: Complex LED system and handlebar crown
   - Key features: 45,000 LEDs, chiseled upper quadrant, colored glass fins
   - Material focus: Programmable emissive materials, steel frame crown

4. **Supporting Buildings - One Wells Fargo + Context**
   - Priority: Complete skyline trio
   - Key features: Rounded "jukebox" crown
   - Add surrounding context buildings

5. **Integration & Lighting**
   - Day renders with accurate sun position
   - Night renders with LED displays (critical for Duke Energy)
   - Geolocation with correct coordinates

**Phase ordering rationale:**
- Building complexity increases (BoA simpler geometry, Duke Energy complex LED)
- BoA Center is most photographed/iconic - best starting point
- Duke Energy night lighting requires specialized material setup

**Research flags for phases:**
- Phase 2 (BoA): Crown illumination well-documented, material colors verified
- Phase 3 (Duke): LED programming may need custom Blender node setup
- Phase 4 (Wells Fargo): Less documentation available, may need additional reference gathering

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Building identification | HIGH | Verified via Wikipedia, CTBUH databases |
| Heights/floors | HIGH | CTBUH authoritative data |
| Architectural details | HIGH | Professional sources (e-architect, CTBUH) |
| Reference photo availability | HIGH | Wikimedia Commons, CTBUH galleries |
| Material specifications | MEDIUM | Based on descriptions, not technical specs |
| One Wells Fargo details | MEDIUM | Less comprehensive documentation |

## Gaps to Address

- **Technical material specs:** PBR values for granite, glass tint percentages
- **Historical imagery:** Building appearances may have changed (LED installation 2017)
- **Context buildings:** Full skyline would need 8-10 additional buildings
- **Street-level details:** Sidewalk, landscaping, surrounding infrastructure

## Files Created

| File | Purpose |
|------|---------|
| .planning/research/CHARLOTTE_SKYLINE_REFERENCE.md | Comprehensive building reference with photos |
| .planning/research/SUMMARY.md | This summary with roadmap implications |

## Ready for Roadmap

Research complete. Proceeding to roadmap creation with verified building data and reference sources.
