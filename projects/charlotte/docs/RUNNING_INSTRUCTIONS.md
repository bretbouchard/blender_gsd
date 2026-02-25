# Charlotte Digital Twin - Running Instructions

This guide explains how to run the Charlotte elevation map visualizations.

## Quick Start

### Option 1: 2D Visualization (No Blender Required)

```bash
cd /Users/bretbouchard/apps/blender_gsd/projects/charlotte

# Install dependencies (if needed)
pip install matplotlib numpy

# Run the 2D visualization
python scripts/elevation_visualize_2d.py
```

**Output:**
- `output/elevation_viz/elevation_heatmap.png` - Color-coded elevation map
- `output/elevation_viz/trade_street_profile.png` - Trade St elevation graph
- `output/elevation_viz/race_loop_profile.png` - Full race loop profile
- `output/elevation_viz/elevation_3d_surface.png` - 3D surface visualization
- `output/elevation_viz/elevation_points.csv` - All elevation data
- `output/elevation_viz/trade_street_profile.csv` - Trade St data
- `output/elevation_viz/race_loop_profile.csv` - Race loop data
- `output/elevation_viz/ELEVATION_REPORT.txt` - Summary report

---

### Option 2: Blender Render (Full 3D)

#### Step 1: Open Blender
```bash
# Open Blender with the Charlotte project
cd /Users/bretbouchard/apps/blender_gsd/projects/charlotte
blender
```

#### Step 2: Run the Elevation Map Builder
1. In Blender, go to **Scripting** tab (top menu)
2. Click **Open** and navigate to `scripts/18_build_elevation_map.py`
3. Click **Run Script** (play button)

This will:
- Create terrain mesh with real elevations
- Add elevation markers at key points
- Create race loop path
- Set up driver camera at race start

#### Step 3: Render
1. Press **F12** to render
2. Or go to **Render → Render Image**

#### Step 4: Save
1. In render window, go to **Image → Save As**
2. Save to `output/renders/`

---

### Option 3: Command Line Render (Background)

```bash
cd /Users/bretbouchard/apps/blender_gsd/projects/charlotte

# Background render (no GUI)
blender --background --python scripts/18_build_elevation_map.py

# The script will save renders to output/renders/
```

---

### Option 4: Render and Email

```bash
# First, set up email credentials
export EMAIL_FROM="your_email@gmail.com"
export EMAIL_TO="bret@example.com"
export EMAIL_PASSWORD="your_app_password"  # Gmail app password

# Run the render and email script
blender --background --python scripts/19_render_and_email.py
```

**Note:** For Gmail, you need an "App Password":
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate a new app password
5. Use that password in EMAIL_PASSWORD

---

## File Locations

```
projects/charlotte/
├── scripts/
│   ├── 18_build_elevation_map.py      # Blender elevation builder
│   ├── 19_render_and_email.py         # Render + email script
│   ├── elevation_visualize_2d.py       # 2D matplotlib viz
│   └── lib/
│       ├── elevation_enhanced.py       # Real elevation data
│       └── race_loop.py                # Race loop system
│
├── output/
│   ├── elevation_viz/                  # 2D visualization outputs
│   │   ├── elevation_heatmap.png
│   │   ├── trade_street_profile.png
│   │   ├── race_loop_profile.png
│   │   ├── elevation_3d_surface.png
│   │   ├── elevation_points.csv
│   │   └── ELEVATION_REPORT.txt
│   │
│   └── renders/                        # Blender render outputs
│       └── charlotte_elevation_*.png
│
└── docs/
    └── DRIVING_GAME_PLAN.md            # Documentation
```

---

## Elevation Data Summary

| Metric | Value |
|--------|-------|
| **Data Source** | SRTM 30m (OpenTopoData API) |
| **Known Points** | 90+ |
| **Elevation Range** | 195m - 295m |
| **Total Variation** | 100m |
| **Trade St Drop** | 43m over 340m |

---

## Troubleshooting

### "matplotlib not found"
```bash
pip install matplotlib numpy
```

### "Blender not found"
Make sure Blender is installed and in your PATH, or use the full path:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --python scripts/18_build_elevation_map.py
```

### "Module not found" in Blender
Blender uses its own Python. Install packages for Blender's Python:
```bash
/Applications/Blender.app/Contents/Resources/4.0/python/bin/python3 -m pip install matplotlib
```

### Email not sending
- Check EMAIL_PASSWORD is set (use app password, not regular password)
- Check SMTP settings match your email provider
- For Gmail, enable "Less secure app access" or use App Passwords

---

## Next Steps

1. Run `elevation_visualize_2d.py` to see the 2D visualizations
2. Check `output/elevation_viz/ELEVATION_REPORT.txt` for the summary
3. Open the PNG files to see the elevation profiles
4. Run the Blender script for full 3D visualization

---

## Contact

For questions about the Charlotte Digital Twin project, check the documentation in `docs/`.
