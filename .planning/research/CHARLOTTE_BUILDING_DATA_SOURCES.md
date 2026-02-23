# Charlotte NC Building Data Sources

**Research Date:** 2026-02-22
**Purpose:** Identify sources for real building data to improve Charlotte Digital Twin accuracy

---

## Summary

This document catalogs all available sources for Charlotte building data including:
- Building footprints (2D outlines)
- Building heights and floor counts
- 3D building models
- Architectural details and materials
- LED/lighting systems

---

## 1. Building Footprint Data (Free)

### Microsoft Global ML Building Footprints ⭐ RECOMMENDED
- **URL:** https://github.com/microsoft/GlobalMLBuildingFootprints
- **Coverage:** 777+ million buildings worldwide, includes all Charlotte/Mecklenburg County
- **Format:** GeoJSON/GeoJSONL
- **License:** ODbL (Open Database License) - free to use
- **Data included:**
  - Building polygon footprints
  - Confidence scores
  - Geographic coordinates
- **How to download:**
  ```python
  # Filter by Charlotte bounding box
  bbox = (-80.9, 35.0, -80.5, 35.4)  # (west, south, east, north)
  # Use Azure Open Datasets or direct download
  ```

### OpenStreetMap (OSM)
- **URL:** https://download.geofabrik.de/north-america/us/north-carolina.html
- **Query via Overpass API:**
  ```
  [out:json][timeout:25];
  area["name"="Charlotte"]->.a;
  (
    way["building"](area.a);
    relation["building"](area.a);
  );
  out body;
  ```
- **Tags available:**
  - `building` - building type (office, apartments, retail, etc.)
  - `height` - building height in meters
  - `building:levels` - number of floors
  - `building:material` - exterior material
  - `roof:shape` - roof type
  - `addr:*` - address information
  - `name` - building name

### Google Open Buildings
- **URL:** https://sites.research.google/gr/open-buildings/
- **Coverage:** Global, includes Charlotte
- **Format:** CSV with polygon coordinates
- **Data included:**
  - Building footprints
  - Height estimates (in some regions)
  - Confidence scores

### Mecklenburg County GIS
- **URL:** https://www.mecknc.gov/LandDevelopment/GIS/Pages/default.aspx
- **Data available:**
  - Tax parcels
  - Building permits
  - Land use
  - Potential building footprints
- **Note:** May require request or navigating county portal

---

## 2. Building Height & Floor Data

### CTBUH Skyscraper Center ⭐ BEST FOR HEIGHTS
- **URL:** https://www.skyscrapercenter.com/city/charlotte
- **Data included:**
  - Official building heights
  - Floor counts
  - Year completed
  - Architect/developer
  - Building function (office, residential, hotel)
  - Structural system

### SKYDB (formerly Emporis)
- **URL:** https://www.skydb.net/
- **Note:** Emporis was taken offline September 2022, relaunched as SKYDB
- **Data included:**
  - 174,000+ high-rise buildings
  - Heights, floors, years
  - Architectural details
  - Building diagrams

### SkyscraperPage
- **URL:** http://skyscraperpage.com/cities/?cityID=13 (Charlotte)
- **Data included:**
  - 80,000+ building diagrams
  - Scale drawings (1 pixel = 1 meter)
  - Height comparisons
  - User-contributed photos

### Wikipedia - Tallest Buildings
- **URL:** https://en.wikipedia.org/wiki/List_of_tallest_buildings_in_North_Carolina
- **Data included:**
  - Ranked list of tallest buildings
  - Heights (ft and m)
  - Floor counts
  - Year built
  - References to primary sources

---

## 3. 3D Building Models

### Google Earth / Google Maps 3D
- **Method:** Screenshot or extract 3D building geometry
- **Tools:**
  - Google Earth Pro (free) - export 3D models
  - Blender Google Maps add-ons
- **Coverage:** Most of Charlotte Uptown

### OpenStreetMap 3D (OSM Buildings)
- **URL:** https://osmbuildings.org/
- **Data:** Extruded 3D buildings from OSM data
- **Viewer:** Real-time 3D visualization
- **Export:** GeoJSON with height data

### Cesium OSM Buildings
- **URL:** https://cesium.com/platform/cesium-osm-buildings/
- **Data:** 3D tiles from OSM
- **Coverage:** Global including Charlotte
- **Integration:** Works with CesiumJS

---

## 4. Architectural Details

### NCModernist
- **URL:** https://www.ncmodernist.org/charlotte.htm
- **Focus:** Mid-century modern architecture in Charlotte
- **Data included:**
  - Architect information
  - Construction dates
  - Historical photos
  - Building descriptions

### Charlotte-Mecklenburg Historic Landmarks Commission
- **URL:** https://www.cmhpf.org/
- **Data included:**
  - Historic building surveys
  - Architectural styles
  - Construction dates
  - Historic photos

### Architectural Drawings (Limited)
- **Sources:**
  - Building management companies (contact directly)
  - Architecture firm portfolios
  - University archives (UNC Charlotte)
- **Note:** Commercial floor plans are typically proprietary

---

## 5. LED/Lighting Systems

### Duke Energy Center Research
- **File:** `.planning/research/DUKE_ENERGY_CENTER_LED_FACADE.md`
- **Data included:**
  - ~2,500 programmable LEDs
  - Designer: Gabler-Youngston Architectural Lighting Design
  - Installed: 2009
  - Operating cost: <$2/night
  - Schedule: Sundown to midnight

### Charlotte LED Buildings (Documented)
- **File:** `.planning/research/CHARLOTTE_LED_IMAGE_URLS.md`
- **Buildings with LED systems:**
  1. Duke Energy Center (550 S Tryon)
  2. Bank of America Corporate Center (crown lighting)
  3. Truist Center
  4. One Wells Fargo Center
  5. FNB Tower
  6. Honeywell Tower
  7. Ally Charlotte Center
  8. Carillon Tower
  9. NASCAR Hall of Fame
  10. 200 South Tryon

---

## 6. Automated Data Acquisition

### Overpass API Query (All Charlotte Buildings)
```python
import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

query = """
[out:json][timeout:60];
area["name"="Charlotte"]["admin_level"="8"]->.a;
(
  way["building"](area.a);
  relation["building"](area.a);
);
out body;
"""

response = requests.post(OVERPASS_URL, data={"data": query})
buildings = response.json()
```

### Microsoft Building Footprints Download
```python
# From https://github.com/microsoft/GlobalMLBuildingFootprints

# Option 1: Azure Open Datasets
from azure.storage.blob import BlobServiceClient

# Option 2: Direct GeoJSONL download
# Filter by Charlotte bounding box
import geopandas as gpd

bbox = (-80.9, 35.0, -80.5, 35.4)
buildings = gpd.read_file("path/to/buildings.geojsonl", bbox=bbox)
```

---

## 7. Charlotte Building Reference Table

| Building | Height (m) | Floors | Year | LED | Source |
|----------|-----------|--------|------|-----|--------|
| Bank of America Corporate Center | 265 | 60 | 1992 | Crown | CTBUH |
| Duke Energy Center (550 S Tryon) | 240 | 48 | 2010 | Full | CTBUH + Research |
| Truist Center (Hearst Tower) | 201 | 47 | 2002 | Accent | CTBUH |
| Bank of America Tower | 193 | 33 | 2019 | - | CTBUH |
| Duke Energy Plaza | 192 | 40 | 2023 | - | CTBUH |
| One Wells Fargo Center | 179 | 42 | 1988 | Crown | CTBUH |
| The Vue | 176 | 51 | 2010 | - | CTBUH |
| FNB Tower | 115 | 25 | 2021 | Full | Research |
| Honeywell Tower | 100 | 23 | 2021 | Full | Research |
| Carillon Tower | 120 | 24 | - | Spire | Wikipedia |
| NASCAR Hall of Fame | 30 | 5 | 2010 | Ribbon | Research |
| Ally Charlotte Center | 122 | 26 | - | Full | Research |
| 200 South Tryon | 148 | 34 | - | Accent | Research |

---

## 8. Recommended Workflow

### Step 1: Get Building Footprints
```bash
# Download Microsoft Building Footprints for Charlotte area
# Or query OSM Overpass API
```

### Step 2: Get Heights/Floors
```bash
# Query CTBUH or SKYDB for accurate height/floor data
# Cross-reference with OSM building:levels tags
```

### Step 3: Cross-Reference with LED Research
```bash
# Use documented LED buildings from research
# Apply appropriate materials and lighting
```

### Step 4: Generate 3D Models
```bash
# Extrude footprints to heights
# Apply building-type-specific details
# Add LED facade systems where applicable
```

---

## 9. API Endpoints Summary

| Source | API | Rate Limit | Auth Required |
|--------|-----|------------|---------------|
| Overpass API | overpass-api.de | ~10,000 req/day | No |
| Microsoft Buildings | Azure Blob | Varies | No (public) |
| CTBUH | skyscrapercenter.com | Web scraping | No |
| SKYDB | skydb.net | API key | Yes (free tier) |

---

## 10. Next Steps

1. **Create data acquisition module** (`lib/charlotte_digital_twin/data/building_data.py`)
   - Overpass API client
   - Microsoft footprints loader
   - Height/floor cross-reference

2. **Implement building generator** using real data
   - Read footprints from GeoJSON
   - Extrude to heights from CTBUH/OSM
   - Apply LED materials based on building name

3. **Create Charlotte building database**
   - JSON/YAML file with all known buildings
   - Heights, floors, LED status, materials
   - Auto-update from OSM

---

## Files Created

- **Research Document:** `.planning/research/CHARLOTTE_BUILDING_DATA_SOURCES.md` (this file)
- **LED URLs:** `.planning/research/CHARLOTTE_LED_IMAGE_URLS.md`
- **Duke Energy:** `.planning/research/DUKE_ENERGY_CENTER_LED_FACADE.md`
