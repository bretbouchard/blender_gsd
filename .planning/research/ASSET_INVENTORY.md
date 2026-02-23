# Charlotte Digital Twin - Asset & Texture Research

**Research Date**: 2026-02-22
**Purpose**: Document available assets, textures, and resources for photorealistic rendering

---

## 1. Existing Asset Inventory

### 1.1 Downloaded HDRI Files ✅
**Location**: `/assets/hdri/`

| File | Size | Use Case |
|------|------|----------|
| `blue_lagoon_1k.hdr` | 1.5MB | Clear blue sky, midday lighting |
| `autumn_park_1k.hdr` | 1.5MB | Warm sunrise/golden hour tones |
| `mossy_forest_1k.hdr` | 1.8MB | Overcast diffuse lighting |
| `music_hall_01_1k.hdr` | 1.6MB | Night/indoor ambient |

**Download Script**: `lib/charlotte_digital_twin/assets/download_hdri.py`

### 1.2 External 3D Asset Library ✅
**Location**: `/Volumes/Storage/3d/`

#### Trash Kit Asset Pack (Blender Market)
**Path**: `animation/plugins/Blender Market – Trash Kit - 3d Assetkit/textures_including_8k/`

| Category | Contents |
|----------|----------|
| **ENV/Asphalt** | Basecolor, Roughness, Wet Normal |
| **ENV/Bricks** | Basecolor, Graffiti variant, Displacement, Normal GL/DX, Roughness |
| **ENV/Concrete** | Basecolor, Graffiti variant, Normal, Roughness |
| **ENV/Metal** | Various metal textures |
| **Foliage** | Grass A, Grass B, Half-Dry Grass (1k/2k/4k variants) |

#### KitBash3D Packs
**Path**: `kitbash/`

| Pack | Relevance for Charlotte |
|------|-------------------------|
| **Americana** | ⭐⭐⭐ Suburban US buildings, signage |
| **Brooklyn** | ⭐⭐⭐ Urban brick buildings, storefronts |
| **Art Deco** | ⭐⭐ Historic buildings |
| **Brutalist** | ⭐⭐⭐ Concrete highway structures, overpasses |
| **CyberPunk** | ⭐ Futuristic elements |
| **Neo Shanghai** | ⭐⭐ Modern glass towers |

#### Plugins/Addons Available
| Plugin | Use Case |
|--------|----------|
| **Auto-Building 1.1.4** | Procedural building generation |
| **Plating Generator** | Panel/greeble details |
| **Quick Snow** | Weather variation |
| **Natural Lighting 2.5** | Alternative lighting presets |
| **Procedural Traffic** | Vehicle generation |

### 1.3 Project Blender Files
| File | Contents |
|------|----------|
| `assets/vehicles/procedural_car_wired.blend` | Procedural car model with drivers |
| `assets/addon_blends/Procedural_Building_Generator_v1_3_1.blend` | Building generator |
| `projects/charlotte/scenes/charlotte_osm_scene.blend` | Charlotte OSM scene |

---

## 2. Ground Cover & Vegetation Research

### 2.1 North Carolina Native Roadside Vegetation

**Common Highway Grass Species:**
| Species | Characteristics | Texture Notes |
|---------|-----------------|---------------|
| **Bermudagrass** | Dense, drought-tolerant | Short, manicured look |
| **Tall Fescue** | Cool-season, clumping | Coarse texture, darker green |
| **Zoysia** | Low-growing, traffic-tolerant | Very short, carpet-like |
| **Bahia Grass** | Low maintenance | Coarse, lighter green |
| **White Clover** | Flowers, nitrogen-fixing | Variegated, small leaves |

**NC Native Trees (Already in tree_placement.py):**
- Sweetgum (Liquidambar styraciflua) - Very common, star-shaped leaves
- Dogwood (Cornus florida) - NC state flower, spring blooms
- Loblolly Pine - Most common NC pine, long needles
- Willow Oak - Common urban tree, narrow leaves
- Red Maple - Widespread, brilliant fall color
- Eastern Red Cedar - Evergreen, conical
- American Holly - Evergreen understory
- Crepe Myrtle - Very common ornamental

### 2.2 Available Grass Textures (Trash Kit)
```
Foliage/1k/
├── Grass_A_Basecolor.png        # Fresh green grass
├── Grass_A_HalfDry_Basecolor.png # Semi-brown grass
├── Grass_B_Basecolor.png        # Alternative variety
├── Grass_Ambient.png            # AO map
├── Grass_AO.png                 # Ambient occlusion
├── Grass_NormalGL.png           # Surface detail
├── Grass_Roughness.png          # Surface roughness
└── Grass_Mask.png               # Alpha mask
```

---

## 3. Building Material Research

### 3.1 Charlotte Downtown Architecture Characteristics

**Dominant Building Types:**
1. **Glass Curtain Wall Towers**
   - Bank of America Corporate Center (312m, 60 floors)
   - Duke Energy Center (240m, 48 floors)
   - Reflective blue-tinted glass
   - White/gray aluminum mullions

2. **Concrete Brutalist Structures**
   - Highway overpasses
   - Parking decks
   - Government buildings

3. **Brick Historic Buildings**
   - Uptown historic district
   - Red brick with mortar joints
   - Some painted brick facades

4. **Modern Mixed Materials**
   - Ceramic panel cladding (new library)
   - Bronze/steel accents
   - Perforated metal screens

### 3.2 Available Building Textures (Trash Kit)

**Asphalt:**
- `Asphalt_Basecolor.jpg` - Road surface color
- `Asphalt_Roughness.jpg` - Weathering variation
- `Asphalt_Wet_NormalGL.jpg` - Wet road surface

**Bricks:**
- `Bricks_Basecolor.jpg` - Standard red brick
- `Bricks_Basecolor_Graffiti.jpg` - Urban weathered
- `Bricks_Displace.jpg` - 3D depth
- `Bricks_NormalGL.jpg` - Surface detail
- `Bricks_Roughness.jpg` - Weathering

**Concrete:**
- `Concrete_BaseColor.jpg/png` - Standard gray
- `Concrete_Graffiti_BaseColor.jpg` - Urban variant
- `Concrete_NormalGL.jpg` - Surface texture
- `Concrete_Roughness.jpg` - Weathering

---

## 4. Free Online PBR Texture Resources

### 4.1 Poly Haven (CC0 License)
**URL**: https://polyhaven.com/textures

**Recommended Downloads for Charlotte:**
| Search Term | Use Case |
|-------------|----------|
| `asphalt` | Road surfaces |
| `concrete` | Buildings, overpasses |
| `brick` | Historic buildings |
| `grass` | Ground cover |
| `gravel` | Shoulder areas |
| `metal` | Guardrails, signage |

### 4.2 AmbientCG (CC0 License)
**URL**: https://ambientcg.com

**Features:**
- 210+ PBR materials
- Up to 8K resolution
- Includes all PBR maps

### 4.3 Other Free Sources
| Site | URL | Notes |
|------|-----|-------|
| 3D Textures | 3dtextures.me | Good ground covers |
| ShareTextures | sharetextures.com | Architectural materials |
| CGBookcase | cgbookcase.com | Miscellaneous materials |
| FreePBR | freepbr.com | Mixed quality |

---

## 5. Recommendations

### 5.1 Immediate Actions

1. **Copy Grass Textures** from Trash Kit to project:
   ```bash
   cp "/Volumes/Storage/3d/animation/plugins/Blender Market – Trash Kit - 3d Assetkit/textures_including_8k/Foliage/2k/"* assets/textures/grass/
   ```

2. **Copy Building Textures** from Trash Kit:
   ```bash
   cp "/Volumes/Storage/3d/animation/plugins/Blender Market – Trash Kit - 3d Assetkit/textures_including_8k/ENV/"* assets/textures/building/
   ```

3. **Download Additional HDRI** from Poly Haven:
   - Sunny afternoon with strong sun
   - Sunset/warm golden hour

### 5.2 Tree/Plant Asset Options

**Option A: Use Procedural Trees** (Already implemented)
- 8 NC native species
- Procedural geometry
- Works without external assets

**Option B: Purchase botaniq addon**
- Professional tree library
- $50-100 for full version
- Includes NC-appropriate species

**Option C: Use KitBash3D Environment packs**
- Already have some in library
- Mix procedural with hero assets

### 5.3 Building Texture Integration

Update `building_materials.py` to load from:
1. Trash Kit textures (local, high quality)
2. Procedural fallback (no external assets)
3. Downloaded Poly Haven textures

---

## 6. File Structure Recommendation

```
assets/
├── hdri/
│   ├── blue_lagoon_1k.hdr
│   ├── autumn_park_1k.hdr
│   ├── mossy_forest_1k.hdr
│   └── music_hall_01_1k.hdr
├── textures/
│   ├── asphalt/
│   │   └── (from Trash Kit)
│   ├── concrete/
│   │   └── (from Trash Kit)
│   ├── brick/
│   │   └── (from Trash Kit)
│   └── grass/
│       └── (from Trash Kit Foliage)
├── vehicles/
│   └── procedural_car_wired.blend
└── buildings/
    └── Procedural_Building_Generator.blend
```

---

## 7. External Asset Paths Configuration

The `config/asset_library.yaml` already points to `/Volumes/Storage/3d`:

```yaml
library_path: "/Volumes/Storage/3d"

categories:
  kitbash:
    packs:
      - name: "Americana"
        path: "kitbash/KitBash3D - Americana"
      - name: "Brooklyn"
        path: "kitbash/Kitbash3D - Brooklyn"
      - name: "Brutalist"
        path: "kitbash/Kitbash3D - Brutalist"
```

Use `asset-rick` to access these via the Asset Vault system.
