# Photoshoot and Studio Lighting Styles Research

**Researched:** 2026-02-21
**Domain:** Professional photography lighting setups for Blender simulation
**Confidence:** HIGH (based on established photography industry standards)

## Summary

This research covers comprehensive professional photography lighting styles and their implementation in Blender. The goal is to create a complete system for replicating professional photoshoot setups including studio lighting, product photography styles, equipment simulation, camera presets, and backdrop types.

**Primary recommendation:** Build a layered photoshoot preset system that combines:
1. **Lighting Style Presets** (Rembrandt, butterfly, three-point, etc.)
2. **Product Type Presets** (jewelry, electronics, cosmetics, etc.)
3. **Camera/Lens Presets** (portrait focal lengths, macro setups)
4. **Backdrop Presets** (infinite curve, paper rolls, cyclorama)

This matches the existing pattern in `lib/cinematic/lighting.py` and `lib/cinematic/types.py`.

---

## 1. STUDIO LIGHTING STYLES

### 1.1 Classic Portrait Lighting Patterns

| Style | Light Position | Key Feature | Best For | Blender Implementation |
|-------|---------------|-------------|----------|------------------------|
| **Three-Point (Soft)** | Key: 45deg front, Fill: opposite, Rim: back | Balanced, professional | General product/portrait | 3 area lights: key (2x2m, 1000W), fill (1.5x1.5m, 300W), rim (1x1m, 500W) |
| **Three-Point (Hard)** | Same positions, smaller sources | More contrast, dramatic | Masculine, edgy | Same but smaller sizes: key (0.5x0.5m), fill (0.3x0.3m) |
| **Rembrandt** | 45deg side + above | Triangle on cheek | Drama, men, mood | Single area light at 45deg horizontal, 45deg elevation, 1000W |
| **Butterfly/Paramount** | Directly above/before camera | Butterfly nose shadow | Glamour, beauty, fashion | Area light directly above camera, pointing down at subject |
| **Split** | 90deg to side | Half face in shadow | Mystery, drama, art | Single area light at 90deg to subject |
| **Loop** | 30-45deg, slight elevation | Small shadow loop near nose | General portraits | Area light at 30-45deg, moderate intensity |
| **Broad** | Lit side faces camera | Face appears wider | Thin faces | Light on camera-side of face |
| **Short** | Shadow side faces camera | Face appears slimmer | Round/wide faces | Light on opposite side from camera |
| **Clamshell** | Top + bottom (beauty dish + reflector) | Fills under-eye shadows | Beauty, makeup, cosmetics | Two lights: top beauty dish + bottom fill, 1-1.5 stop difference |

### 1.2 High-Key vs Low-Key Lighting

| Aspect | High-Key | Low-Key |
|--------|----------|---------|
| **Background** | White/bright | Black/dark |
| **Shadows** | Minimal, soft | Prominent, deep |
| **Light Ratio** | 1:1 to 2:1 | 8:1 or higher |
| **Mood** | Bright, happy, optimistic | Dramatic, mysterious, serious |
| **Light Sources** | Multiple fill lights | Single focused light |
| **Genre** | Commercials, beauty, e-commerce | Noir, thriller, luxury products |
| **Blender Setup** | White backdrop + 4+ lights, fill shadows | Black backdrop + 1 key light + minimal fill |

### 1.3 Blender Light Configuration per Style

```python
# Three-Point Lighting (Soft Variant)
THREE_POINT_SOFT = {
    "key_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 2.0,
        "size_y": 2.0,
        "intensity": 1000.0,  # watts
        "position": {"angle": 45, "distance": 3.0, "height": 2.0},
        "color": (1.0, 1.0, 1.0),
        "temperature": 5500  # Kelvin
    },
    "fill_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 1.5,
        "size_y": 1.5,
        "intensity": 300.0,
        "position": {"angle": -45, "distance": 3.0, "height": 1.5},
        "color": (1.0, 1.0, 1.0)
    },
    "rim_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 1.0,
        "size_y": 1.0,
        "intensity": 500.0,
        "position": {"angle": 180, "distance": 2.5, "height": 2.5},
        "color": (1.0, 1.0, 1.0)
    }
}

# Rembrandt Lighting
REMBRANDT = {
    "key_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 1.0,
        "size_y": 1.0,
        "intensity": 1000.0,
        "position": {"angle": 45, "distance": 2.5, "height": 2.5},  # 45deg + elevated
        "color": (1.0, 0.98, 0.95),  # Slight warmth
        "temperature": 5000
    }
}

# Butterfly/Paramount Lighting
BUTTERFLY = {
    "key_light": {
        "light_type": "area",
        "shape": "DISK",  # Beauty dish approximation
        "size": 0.6,  # 60cm beauty dish
        "intensity": 800.0,
        "position": {"angle": 0, "distance": 2.0, "height": 3.0},  # Directly above
        "rotation": (90, 0, 0),  # Pointing down
        "color": (1.0, 1.0, 1.0)
    }
}

# Clamshell Lighting (Beauty)
CLAMSHELL = {
    "top_light": {
        "light_type": "area",
        "shape": "DISK",  # Beauty dish
        "size": 0.55,  # 55cm beauty dish
        "intensity": 600.0,
        "position": {"angle": 0, "distance": 1.5, "height": 2.0},
        "rotation": (45, 0, 0)
    },
    "bottom_fill": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 1.0,
        "size_y": 0.5,
        "intensity": 200.0,  # 1-1.5 stops less
        "position": {"angle": 0, "distance": 1.5, "height": 0.3},
        "rotation": (-30, 0, 0)
    }
}

# Split Lighting
SPLIT = {
    "key_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 1.0,
        "size_y": 1.5,
        "intensity": 800.0,
        "position": {"angle": 90, "distance": 2.0, "height": 1.5},  # 90deg = side
        "color": (1.0, 1.0, 1.0)
    }
}

# High-Key Lighting
HIGH_KEY = {
    "key_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 2.0,
        "size_y": 2.0,
        "intensity": 1000.0,
        "position": {"angle": 30, "distance": 3.0, "height": 2.0}
    },
    "fill_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 2.0,
        "size_y": 2.0,
        "intensity": 800.0,  # 1:1.25 ratio (very close)
        "position": {"angle": -30, "distance": 3.0, "height": 2.0}
    },
    "background_lights": [
        {"position": (0, -3, 2), "intensity": 500},
        {"position": (-2, -3, 1), "intensity": 300},
        {"position": (2, -3, 1), "intensity": 300}
    ]
}

# Low-Key Lighting
LOW_KEY = {
    "key_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 0.5,
        "size_y": 0.5,
        "intensity": 1000.0,
        "position": {"angle": 60, "distance": 3.0, "height": 2.5},
        "spread": 0.5  # More focused
    }
    # No fill - 8:1+ ratio achieved by single light
}
```

---

## 2. PRODUCT PHOTOGRAPHY STYLES

### 2.1 E-Commerce Hero Shots

| Element | Specification |
|---------|---------------|
| **Lighting** | Soft, even, minimal shadows (high-key variant) |
| **Background** | Pure white (255,255,255) or light gray |
| **Camera** | 50-100mm focal length, deep DOF (f/8-f/11) |
| **Light Setup** | 4-light: Key, fill, 2 background lights for pure white |
| **Shadow** | Subtle drop shadow for grounding |

```python
ECOMMERCE_HERO = {
    "lighting": "high_key",
    "backdrop": {"type": "paper_roll", "color": "white"},
    "camera": {"focal_length": 85, "f_stop": 11},
    "shadow_catcher": True,
    "additional_lights": ["background_fill_left", "background_fill_right"]
}
```

### 2.2 Jewelry Photography

| Element | Specification |
|---------|---------------|
| **Lighting** | Soft, diffused with controlled reflections |
| **Equipment** | Light tent/box, multiple soft lights |
| **Setup** | "Triangle lighting": top, left, right |
| **Macro** | 100mm macro lens, focus stacking |
| **Challenge** | Highly reflective surfaces |

```python
JEWELRY_PHOTOGRAPHY = {
    "lighting_rig": "triangle_soft",
    "light_tent": {
        "enabled": True,
        "size": 0.5,  # 50cm light tent
        "diffusion": "heavy"
    },
    "lights": {
        "top": {"shape": "RECTANGLE", "size": 0.4, "intensity": 400, "position": (0, 0, 0.5)},
        "left": {"shape": "RECTANGLE", "size": 0.4, "intensity": 300, "position": (-0.4, 0, 0.3)},
        "right": {"shape": "RECTANGLE", "size": 0.4, "intensity": 300, "position": (0.4, 0, 0.3)}
    },
    "camera": {"focal_length": 100, "f_stop": 16, "focus_distance": 0.3},
    "sparkle_lights": True  # Small point lights for gem reflections
}
```

### 2.3 Electronics/Tech Products

| Element | Specification |
|---------|---------------|
| **Lighting** | 4-light setup (top, bottom, left, right) |
| **Style** | Clean, modern, gradient reflections |
| **Challenge** | Screens, buttons, glossy surfaces |
| **Setup** | Elevated product, gradient background |

```python
ELECTRONICS_PHOTOGRAPHY = {
    "lights": {
        "top": {"intensity": 800, "position": (0, -1, 3)},
        "bottom": {"intensity": 400, "position": (0, -1, -1)},  # For reflection
        "left": {"intensity": 500, "position": (-2, -1, 2)},
        "right": {"intensity": 500, "position": (2, -1, 2)}
    },
    "reflection_plane": True,  # Glossy surface for product reflection
    "gradient_backdrop": {"bottom": (0.9, 0.9, 0.9), "top": (0.6, 0.6, 0.6)},
    "camera": {"focal_length": 100, "f_stop": 8}
}
```

### 2.4 Cosmetics/Beauty Products

| Element | Specification |
|---------|---------------|
| **Lighting** | Soft, glamorous (butterfly/clamshell variant) |
| **Style** | High-end, aspirational, glowing |
| **Background** | White, pink, or brand colors |
| **Details** | Texture emphasis, color accuracy |

```python
COSMETICS_PHOTOGRAPHY = {
    "lighting": "clamshell",
    "backdrop": {"type": "gradient", "colors": [(1.0, 0.95, 0.95), (1.0, 1.0, 1.0)]},
    "accent_lights": {
        "hair_rim": {"intensity": 300, "angle": 160},
        "fill_card": {"position": "left", "reflectivity": 0.8}
    },
    "camera": {"focal_length": 100, "f_stop": 5.6}
}
```

### 2.5 Food Photography

| Element | Specification |
|---------|---------------|
| **Lighting** | Soft window-like, often single source |
| **Style** | Natural, appetizing, fresh |
| **Background** | Textured surfaces, props |
| **Angles** | 45deg overhead, eye-level, macro details |

```python
FOOD_PHOTOGRAPHY = {
    "primary_light": {
        "type": "area",
        "shape": "RECTANGLE",
        "size": 1.5,
        "intensity": 600,
        "position": {"angle": 60, "distance": 2.0, "height": 2.5},
        "color": (1.0, 0.95, 0.9),  # Warm daylight
        "temperature": 5000
    },
    "style": "natural_window",
    "props": ["utensils", "linens", "ingredients"],
    "camera_angles": ["overhead_45", "eye_level", "macro_detail"]
}
```

### 2.6 Automotive Photography

| Element | Specification |
|---------|---------------|
| **Studio Size** | 200+ sqm minimum, cyclorama preferred |
| **Lighting** | 20-30 lights, all indirect/diffused |
| **Key Principle** | All light on car body must be indirect |
| **Technique** | Light painting with large diffuser screens |
| **Detail** | Separate lighting for wheels, grille, interior |

```python
AUTOMOTIVE_PHOTOGRAPHY = {
    "studio": {"type": "cyclorama", "size": (15, 20, 8)},  # meters
    "diffusion_screens": {
        "top": {"size": (3, 5), "position": "above_car"},
        "sides": {"size": (2, 4), "count": 2}
    },
    "lights_behind_diffusion": {
        "count": 20,
        "distribution": "even_across_screens"
    },
    "detail_lights": {
        "wheels": {"type": "strip", "intensity": 200},
        "grille": {"type": "spot", "intensity": 150},
        "interior": {"type": "area", "intensity": 100}
    },
    "light_painting": {
        "enabled": True,
        "rail_length": 10  # meters for moving light
    },
    "black_flags": True,  # For controlling reflections
    "camera": {"focal_length": 100, "f_stop": 11}
}
```

### 2.7 Watch Photography

| Element | Specification |
|---------|---------------|
| **Lighting** | Multi-light for different surfaces |
| **Challenge** | Reflective case, glowing dial, strap texture |
| **Lens** | 100mm macro for details |
| **Post-processing** | Often composite multiple exposures |

```python
WATCH_PHOTOGRAPHY = {
    "lights": {
        "case_light": {"angle": 30, "intensity": 500, "soft": True},
        "dial_light": {"angle": 0, "intensity": 300, "even": True},
        "strap_light": {"angle": 45, "intensity": 200},
        "accent_lights": [
            {"position": "10 o'clock", "intensity": 100},
            {"position": "4 o'clock", "intensity": 100}
        ]
    },
    "camera": {"focal_length": 100, "f_stop": 8, "focus_distance": 0.3},
    "composite_shots": ["case", "dial", "hands", "strap"],
    "background": "gradient_dark"
}
```

### 2.8 Bottle/Beverage Photography

| Element | Specification |
|---------|---------------|
| **Primary Technique** | Backlighting |
| **Effect** | Glowing liquid, edge highlights |
| **Background** | Dark for contrast or light for silhouette |
| **Ice/Condensation** | Acrylic ice, distilled water |

```python
BOTTLE_PHOTOGRAPHY = {
    "primary_light": {
        "type": "backlight",
        "position": "behind_bottle",
        "intensity": 800,
        "diffusion": "heavy"
    },
    "edge_lights": {
        "left": {"angle": 120, "intensity": 300},
        "right": {"angle": -120, "intensity": 300}
    },
    "label_light": {
        "front": {"intensity": 200, "flagged": True}  # Flag to control glass reflections
    },
    "liquid_glow": True,
    "condensation": {
        "enabled": True,
        "type": "procedural"
    },
    "background": {"type": "dark_gradient", "colors": [(0.1, 0.1, 0.1), (0.2, 0.2, 0.2)]},
    "camera": {"focal_length": 85, "f_stop": 8}
}
```

---

## 3. LIGHTING EQUIPMENT SIMULATION

### 3.1 Equipment-to-Blender Mapping

| Real Equipment | Blender Light Type | Parameters |
|----------------|-------------------|------------|
| **Softbox (large)** | Area Light (RECTANGLE) | size: 1.5-2.0m, spread: 1.0, soft shadows |
| **Softbox (small)** | Area Light (RECTANGLE) | size: 0.5-1.0m, spread: 1.0 |
| **Octabox** | Area Light (DISK) | size: 0.9-1.2m diameter |
| **Strip Light** | Area Light (RECTANGLE) | size: 0.3, size_y: 1.5m |
| **Beauty Dish (white)** | Area Light (DISK) | size: 0.4-0.6m, higher contrast |
| **Beauty Dish (silver)** | Area Light (DISK) | size: 0.4-0.6m, harder light, spread: 0.5 |
| **Ring Light** | Area Light (ELLIPSE) or Torus mesh | Inner radius, outer radius, pointing at subject |
| **Umbrella (shoot-through)** | Area Light (DISK) | size: 1.0m, very soft |
| **Umbrella (reflective)** | Area Light (DISK) | size: 1.0m, bounced |
| **Fresnel Light** | Spot Light | spot_size: 30-60deg, spot_blend: 0.3-0.7 |
| **LED Panel** | Area Light (RECTANGLE) | size: 0.3-0.6m, even spread |
| **PAR Can** | Spot Light | spot_size: 15-30deg, hard edge |
| **Reflector/Bounce Card** | Mesh plane with emissive OR white diffuse | Low emission, or just white material |
| **Flag/Gobo** | Mesh plane blocking light | Black material, positioned to cut light |
| **Diffusion Panel** | Scaled area light OR mesh with translucent | Increases effective light size |

### 3.2 Detailed Equipment Presets

```python
LIGHTING_EQUIPMENT_PRESETS = {
    "softbox_large": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 2.0,
        "size_y": 1.5,
        "spread": 1.047,  # 60 degrees
        "shadow_soft_size": 0.5,
        "description": "Large rectangular softbox for soft, wrap-around light"
    },
    "softbox_small": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 0.6,
        "size_y": 0.6,
        "spread": 1.047,
        "shadow_soft_size": 0.2,
        "description": "Small softbox for more directional soft light"
    },
    "octabox": {
        "light_type": "area",
        "shape": "DISK",  # Blender doesn't have octagon, disk is close
        "size": 0.9,
        "spread": 1.047,
        "shadow_soft_size": 0.3,
        "description": "Octagonal softbox with round catchlights"
    },
    "strip_light": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 0.2,
        "size_y": 1.2,
        "spread": 1.047,
        "description": "Narrow strip for rim lighting and automotive"
    },
    "beauty_dish_white": {
        "light_type": "area",
        "shape": "DISK",
        "size": 0.56,  # 56cm standard
        "spread": 0.8,  # More focused
        "shadow_soft_size": 0.1,
        "description": "White interior beauty dish for softer light"
    },
    "beauty_dish_silver": {
        "light_type": "area",
        "shape": "DISK",
        "size": 0.56,
        "spread": 0.6,  # Even more focused
        "shadow_soft_size": 0.05,
        "description": "Silver interior beauty dish for harder, more specular light"
    },
    "ring_light_18": {
        "light_type": "area",
        "shape": "DISK",  # Simplified; could use torus mesh
        "size": 0.46,  # 18 inch diameter
        "spread": 1.57,  # 90 degrees
        "description": "18-inch ring light for even, shadowless beauty lighting"
    },
    "fresnel_1k": {
        "light_type": "spot",
        "spot_size": 1.047,  # 60 degrees max
        "spot_blend": 0.5,
        "shadow_soft_size": 0.1,
        "description": "1000W fresnel spotlight for theatrical/cinematic lighting"
    },
    "led_panel": {
        "light_type": "area",
        "shape": "RECTANGLE",
        "size": 0.3,
        "size_y": 0.3,
        "spread": 1.57,  # 90 degrees
        "description": "LED panel light for video/photography"
    }
}
```

### 3.3 Modifier Simulation

| Modifier | Blender Implementation |
|----------|----------------------|
| **Diffusion Panel** | Increase area light size, reduce intensity proportionally |
| **Grid/Honeycomb** | Reduce spread angle, add flag geometry |
| **Barn Doors** | Add black mesh planes around light |
| **Gel/Color Filter** | Modify light color or use temperature |
| **Snoot** | Spot light with small spot_size + flag geometry |
| **Reflector (white)** | White emissive plane or white diffuse material |
| **Reflector (silver)** | High roughness metallic material |
| **Reflector (gold)** | Warm metallic material |
| **Flag/Black Wrap** | Black mesh plane positioned to block light |
| **Gobo (pattern)** | Mesh with cutout pattern in front of spot light |

---

## 4. CAMERA SETUP PRESETS

### 4.1 Portrait Focal Lengths

| Focal Length | Use Case | DOF Recommendation | Working Distance |
|--------------|----------|-------------------|------------------|
| **85mm** | Classic portrait, headshots | f/1.8 - f/2.8 | 2-3m |
| **105mm** | Beauty, macro portrait | f/2.8 - f/4 | 2-4m |
| **135mm** | Full face, compression | f/2.8 - f/4 | 3-5m |
| **50mm** | Environmental portrait | f/2.0 - f/4 | 1.5-2.5m |

### 4.2 Product Photography Lenses

| Focal Length | Use Case | DOF Recommendation |
|--------------|----------|-------------------|
| **50mm** | General product, larger items | f/8 - f/11 |
| **100mm Macro** | Small products, jewelry, watches | f/8 - f/16 |
| **60mm Macro** | Medium products, food | f/5.6 - f/11 |
| **24-70mm Zoom** | Variable product sizes | f/8 - f/11 |

### 4.3 Full-Body and Fashion

| Focal Length | Use Case | DOF Recommendation |
|--------------|----------|-------------------|
| **35mm** | Full body, environmental | f/4 - f/8 |
| **50mm** | Three-quarter, fashion | f/4 - f/8 |

### 4.4 Blender Camera Presets

```python
CAMERA_PRESETS = {
    "portrait_85mm": {
        "focal_length": 85.0,
        "sensor_width": 36.0,
        "f_stop": 2.8,
        "focus_distance": 2.5,  # meters
        "aperture_blades": 9,
        "description": "Classic portrait lens for flattering compression"
    },
    "portrait_105mm": {
        "focal_length": 105.0,
        "sensor_width": 36.0,
        "f_stop": 2.8,
        "focus_distance": 3.0,
        "aperture_blades": 9,
        "description": "Beauty and fashion portrait lens"
    },
    "portrait_135mm": {
        "focal_length": 135.0,
        "sensor_width": 36.0,
        "f_stop": 2.8,
        "focus_distance": 4.0,
        "aperture_blades": 9,
        "description": "Telephoto portrait for maximum compression"
    },
    "product_50mm": {
        "focal_length": 50.0,
        "sensor_width": 36.0,
        "f_stop": 11.0,
        "focus_distance": 1.0,
        "aperture_blades": 9,
        "description": "General product photography with deep DOF"
    },
    "product_100mm_macro": {
        "focal_length": 100.0,
        "sensor_width": 36.0,
        "f_stop": 16.0,
        "focus_distance": 0.3,  # Macro distance
        "aperture_blades": 9,
        "description": "Macro lens for jewelry, watches, small products"
    },
    "fashion_35mm": {
        "focal_length": 35.0,
        "sensor_width": 36.0,
        "f_stop": 5.6,
        "focus_distance": 3.0,
        "aperture_blades": 9,
        "description": "Full-body fashion and environmental"
    },
    "food_60mm": {
        "focal_length": 60.0,
        "sensor_width": 36.0,
        "f_stop": 5.6,
        "focus_distance": 0.5,
        "aperture_blades": 9,
        "description": "Food photography close-ups"
    },
    "automotive_100mm": {
        "focal_length": 100.0,
        "sensor_width": 36.0,
        "f_stop": 11.0,
        "focus_distance": 6.0,
        "aperture_blades": 9,
        "description": "Automotive hero shots"
    }
}
```

---

## 5. BACKDROP TYPES

### 5.1 Infinite Curve/Sweep

**Description:** Seamless transition from floor to wall, eliminating visible horizon line.

```python
INFINITE_CURVE = {
    "type": "procedural_mesh",
    "radius": 5.0,  # Floor extent
    "curve_radius": 1.5,  # Curve transition radius
    "wall_height": 3.0,  # Vertical wall height
    "depth": 10.0,  # Depth along Y axis
    "segments": 32,  # Curve smoothness
    "material": "gradient",  # Or solid color
    "shadow_catcher": True
}
```

**Implementation:** Already exists in `lib/cinematic/backdrops.py` as `create_infinite_curve()`.

### 5.2 Paper Rolls

**Description:** Seamless paper backdrop in various colors, creates subtle sweep.

```python
PAPER_ROLL = {
    "type": "procedural_mesh",
    "width": 2.72,  # Standard 9ft roll
    "height": 11.0,  # Standard length
    "sweep_radius": 0.5,  # Subtle floor curve
    "colors": {
        "white": (0.98, 0.98, 0.98),
        "black": (0.02, 0.02, 0.02),
        "gray": (0.5, 0.5, 0.5),
        "seamless_gray": (0.7, 0.7, 0.7),
        "thunder_gray": (0.4, 0.4, 0.42),
        "sky_blue": (0.6, 0.75, 0.9)
    },
    "material_properties": {
        "roughness": 0.8,
        "sheen": 0.0
    }
}
```

### 5.3 Muslin/Textured Backdrops

**Description:** Fabric backdrop with visible texture and drape.

```python
MUSLIN_BACKDROP = {
    "type": "procedural_or_mesh",
    "texture": "muslin",  # Procedural fabric noise
    "colors": ["navy", "burgundy", "forest", "charcoal"],
    "drape": True,  # Simulated fabric folds
    "material_properties": {
        "roughness": 0.9,
        "subsurface": 0.1,
        "normal_strength": 0.3
    }
}
```

### 5.4 Chroma Key (Green/Blue Screen)

**Description:** Solid color for compositing/replacement.

```python
CHROMA_KEY = {
    "type": "solid_color",
    "green_screen": (0.0, 0.7, 0.0),  # Standard green
    "blue_screen": (0.0, 0.0, 0.9),   # Standard blue
    "material_properties": {
        "roughness": 0.5,
        "emission": 0.0
    },
    "lighting": "even_illumination"  # Must be evenly lit
}
```

### 5.5 Gradient Backdrops

**Description:** Smooth color transition from bottom to top.

```python
GRADIENT_BACKDROP = {
    "type": "shader_gradient",
    "gradient_type": "linear",  # linear, radial, angular
    "stops": [
        {"position": 0.0, "color": (0.15, 0.15, 0.18)},
        {"position": 1.0, "color": (0.3, 0.3, 0.35)}
    ],
    "popular_presets": {
        "smoke_gray": [(0.2, 0.2, 0.22), (0.4, 0.4, 0.42)],
        "sunset": [(0.9, 0.4, 0.2), (0.2, 0.1, 0.3)],
        "ocean": [(0.1, 0.2, 0.4), (0.2, 0.4, 0.6)],
        "studio_warm": [(0.95, 0.9, 0.85), (1.0, 1.0, 1.0)]
    }
}
```

**Implementation:** Already exists in `lib/cinematic/backdrops.py` as `create_gradient_material()`.

### 5.6 V-Flat Setups

**Description:** Large folding flats for bounce and flag use.

```python
V_FLAT = {
    "type": "mesh_plane",
    "dimensions": (2.4, 1.2),  # Standard 8x4ft
    "sides": {
        "white": {"color": (0.95, 0.95, 0.95), "roughness": 0.8},
        "black": {"color": (0.02, 0.02, 0.02), "roughness": 0.9}
    },
    "foldable": True,
    "positions": ["bounce", "flag", "sided_light"]
}
```

### 5.7 Cyclorama Walls

**Description:** Permanent studio installation with curved corners.

```python
CYCLORAMA = {
    "type": "procedural_mesh",
    "dimensions": {
        "width": 15.0,
        "depth": 20.0,
        "height": 8.0
    },
    "corner_radius": 1.5,  # Curved corners
    "floor_wall_radius": 1.0,  # Floor-to-wall curve
    "material": {
        "type": "painted_surface",
        "color": (0.95, 0.95, 0.95),
        "roughness": 0.7
    }
}
```

---

## 6. CODE EXAMPLES

### 6.1 Applying a Lighting Preset

```python
# From existing lib/cinematic/lighting.py pattern
from lib.cinematic.lighting import apply_lighting_rig
from lib.cinematic.types import LightConfig, Transform3D

# Apply Rembrandt lighting preset
result = apply_lighting_rig(
    "rembrandt_classic",
    target_position=(0, 0, 1),  # Aim at head height
    intensity_scale=1.0
)
```

### 6.2 Creating a Photoshoot Setup

```python
from lib.cinematic.lighting import apply_lighting_rig
from lib.cinematic.backdrops import create_backdrop_from_preset
from lib.cinematic.camera import create_camera

# Setup: Jewelry product photography
def setup_jewelry_photoshoot():
    # 1. Create backdrop
    backdrop = create_backdrop_from_preset("paper_roll_white")

    # 2. Apply lighting
    lights = apply_lighting_rig("jewelry_triangle", target_position=(0, 0, 0.15))

    # 3. Create camera
    camera = create_camera(
        CameraConfig(
            name="jewelry_camera",
            focal_length=100.0,
            f_stop=16.0,
            focus_distance=0.3,
            sensor_width=36.0
        ),
        set_active=True
    )

    return {"backdrop": backdrop, "lights": lights, "camera": camera}
```

### 6.3 Photoshoot Preset YAML Structure

```yaml
# configs/cinematic/photoshoot_presets.yaml
photoshoot_presets:
  # Portrait presets
  portrait_rembRANDT:
    name: "Rembrandt Portrait"
    category: portrait
    lighting_rig: rembrandt_classic
    backdrop: gradient_smoke_gray
    camera:
      focal_length: 85
      f_stop: 2.8
    description: "Classic dramatic portrait with Rembrandt triangle"

  portrait_butterfly:
    name: "Butterfly Beauty"
    category: portrait
    lighting_rig: butterfly_glamour
    backdrop: paper_roll_white
    camera:
      focal_length: 105
      f_stop: 4.0
    description: "Glamorous beauty lighting with butterfly shadow"

  # Product presets
  product_hero_white:
    name: "E-Commerce Hero (White)"
    category: product
    lighting_rig: high_key_product
    backdrop: paper_roll_white
    camera:
      focal_length: 85
      f_stop: 11.0
    shadow_catcher: true
    description: "Clean white background for e-commerce"

  jewelry_diamond:
    name: "Diamond Jewelry"
    category: product
    lighting_rig: jewelry_triangle
    backdrop: gradient_dark
    camera:
      focal_length: 100
      f_stop: 16.0
      focus_distance: 0.3
    description: "Jewelry photography with sparkle emphasis"

  electronics_modern:
    name: "Tech Product Modern"
    category: product
    lighting_rig: tech_4point
    backdrop: gradient_neutral
    camera:
      focal_length: 100
      f_stop: 8.0
    reflection_plane: true
    description: "Modern tech product with gradient reflection"
```

---

## 7. COMMON PITFALLS

### 7.1 Lighting Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Hot spots on reflective products** | Direct light creates specular blowouts | Always diffuse through screens, use indirect lighting |
| **Multiple shadows** | Too many direct lights | Use one key light, fill with reflectors or very soft lights |
| **Flat lighting** | Key/fill ratio too close | Increase ratio to at least 2:1 for dimensionality |
| **Wrong color temperature** | Mixing daylight and tungsten | Use consistent temperature (5500K daylight standard) |
| **Shadow too hard** | Light source too small | Increase light size or add diffusion |
| **Background spill** | Background lights affecting subject | Use barn doors or flags to control light direction |

### 7.2 Camera Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Too shallow DOF** | f/1.4-f/2.8 for products | Use f/8-f/16 for sharp products |
| **Wrong focal length** | Wide angle distortion on faces | Use 85mm+ for portraits |
| **Focus on wrong point** | Autofocus misses in macro | Set explicit focus_distance for macro work |
| **Perspective distortion** | Camera too close to subject | Increase distance, use longer lens |

### 7.3 Backdrop Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Visible horizon line** | Sharp floor-wall junction | Use infinite curve with smooth radius |
| **Paper creases** | Poor sweep installation | Increase curve radius, use fresh paper |
| **Color cast on backdrop** | Colored light contamination | Use neutral lighting, check white balance |
| **Uneven backdrop lighting** | Hot spots or dark areas | Use dedicated background lights |

---

## 8. INTEGRATION WITH EXISTING CODE

### 8.1 Files to Extend

| File | Extension |
|------|-----------|
| `lib/cinematic/types.py` | Add `PhotoshootConfig` dataclass |
| `lib/cinematic/lighting.py` | Add photoshoot-specific presets |
| `lib/cinematic/backdrops.py` | Add paper roll, v-flat creation |
| `lib/cinematic/camera.py` | Add photoshoot camera presets |
| `lib/cinematic/preset_loader.py` | Add photoshoot preset loader |

### 8.2 New Files to Create

| File | Purpose |
|------|---------|
| `lib/cinematic/photoshoot.py` | Photoshoot orchestration functions |
| `lib/cinematic/lighting_equipment.py` | Equipment simulation helpers |
| `configs/cinematic/photoshoot_presets.yaml` | Photoshoot preset definitions |
| `configs/cinematic/equipment_presets.yaml` | Equipment preset definitions |

---

## 9. SOURCES

### Primary (HIGH confidence)
- Blender Official Documentation - Tri-Lighting Add-on
- Digital Photography School - 6 Portrait Lighting Patterns
- Magic Studio Blog - E-commerce Lighting Techniques
- Existing codebase: `lib/cinematic/lighting.py`, `lib/cinematic/backdrops.py`

### Secondary (MEDIUM confidence)
- Broncolor - Mastering Beer Photography
- StudioBinder - Portrait Lighting Setup Guide
- Professional photographers' techniques from Chinese photography tutorials
- Alibaba product listings for equipment specifications

### Tertiary (LOW confidence)
- Various blog posts on specific techniques
- Product photography forums and discussions

---

## 10. METADATA

**Confidence breakdown:**
- Studio lighting styles: HIGH - Based on established photography industry standards
- Product photography styles: HIGH - Well-documented professional techniques
- Equipment simulation: MEDIUM - Blender approximations may not perfectly match real equipment
- Camera presets: HIGH - Standard focal length and DOF recommendations
- Backdrop types: HIGH - Common studio equipment specifications
- Pitfalls: HIGH - Common mistakes well-documented in photography education

**Research date:** 2026-02-21
**Valid until:** 2027-02-21 (stable photography techniques, but Blender features may evolve)
