# How to Animate the Smooth Water Sphere

## Quick Start (Already Animated!)

The blend file already has animation set up:

1. **Open**: `smooth_water_sphere_test.blend`
2. **Press SPACE** to play animation
3. **Scrub timeline** to see waves move

That's it! The sphere will gently ripple with smooth, rolling waves.

---

## Animation Methods

### Method 1: Keyframe Animation (Default)

**What it is**: Simple start-to-end animation with 2 keyframes

**How to use**:
```python
animate_smooth_water_sphere(sphere, start_frame=1, end_frame=250, speed=0.15)
```

**Parameters**:
- `start_frame`: When animation begins (default: 1)
- `end_frame`: When animation ends (default: 250)
- `speed`: How fast waves move (default: 0.15)
  - Lower = slower, calmer
  - Higher = faster, more active

**Manual editing in Blender**:
1. Select sphere
2. Open **Graph Editor**
3. Find the Time curve
4. Adjust keyframes or add new ones

---

### Method 2: Driver Animation (Real-time)

**What it is**: Auto-syncs with timeline, no keyframes needed

**How to use**:
```python
from animate_smooth_water import animate_with_driver
animate_with_driver(sphere, speed=0.2)
```

**Advantages**:
- Always in sync with timeline
- No keyframe management
- Easy to adjust speed

**Manual editing in Blender**:
1. Select sphere
2. Right-click Time value in modifier
3. Choose "Edit Driver"
4. Change expression: `frame * 0.2 / 24.0`

---

### Method 3: Cyclic Animation (Looping)

**What it is**: Seamless loop that repeats

**How to use**:
```python
from animate_smooth_water import animate_with_cycle
animate_with_cycle(sphere, start_frame=1, end_frame=250, speed=0.2, cycles=3)
```

**Parameters**:
- `cycles`: Number of complete loops (default: 3)

**Advantages**:
- Perfect for looping videos
- Seamless repetition
- Good for ambient effects

---

### Method 4: Eased Animation (Smooth Start/Stop)

**What it is**: Smooth acceleration and deceleration

**How to use**:
```python
from animate_smooth_water import animate_with_easing
animate_with_easing(sphere, start_frame=1, end_frame=250, speed=0.2)
```

**Advantages**:
- Natural motion
- No abrupt starts/stops
- Professional feel

---

## Adjusting Animation in Blender

### Change Wave Speed

1. Select the water sphere
2. Go to **Modifiers** tab (wrench icon)
3. Find **GeometryNodes** modifier
4. Adjust **Wind Speed** (Socket_3):
   - Lower = slower wind
   - Higher = faster wind

### Change Wave Height

In the same modifier:
- Adjust **Wave Height** (Socket_2):
  - 0.05 = very subtle
  - 0.1 = moderate
  - 0.2 = pronounced

### Change Wave Scale

- Adjust **Wave Scale** (Socket_1):
  - 0.5 = small, frequent ripples
  - 1.5 = large, rolling waves
  - 3.0 = very wide swells

---

## Creating Custom Animations

### Manual Keyframing

1. Select sphere
2. Go to frame 1
3. In modifier, set Time = 0
4. Hover over Time value, press **I**
5. Go to frame 100
6. Set Time = 4.0 (or any value)
7. Press **I** again

### Adjusting Keyframe Interpolation

1. Open **Graph Editor**
2. Select the Time curve
3. Press **T** to change interpolation:
   - **Linear**: Constant speed
   - **Bezier**: Smooth easing
   - **Constant**: Jump between values

### Adding Variation

Create multiple keyframes at different speeds:

```
Frame 1:   Time = 0.0
Frame 50:  Time = 2.0  (fast)
Frame 100: Time = 3.0  (slow)
Frame 150: Time = 6.0  (fast again)
```

---

## Render Settings for Animation

### Basic Setup

```python
bpy.context.scene.render.fps = 24
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 250
```

### Render Animation

**Command line**:
```bash
blender -b smooth_water_sphere_test.blend -o //render_ -F PNG -a
```

**In Blender**:
1. Set output path in **Output Properties**
2. Set file format (PNG, FFmpeg video, etc.)
3. Press **Ctrl+F12** to render animation

### For Video

```python
# Setup for MP4 video
scene = bpy.context.scene
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
```

---

## Performance Tips

### For Faster Playback

1. Lower subdivision level:
   ```python
   subdiv.inputs['Level'].default_value = 2  # instead of 4
   ```

2. Reduce segments/rings:
   ```python
   segments=32, rings=24  # instead of 80, 60
   ```

3. Use **Viewport Subdivision**:
   - In modifier, set different viewport/render levels

### For Faster Renders

1. Use **Adaptive Subdivision** (Cycles)
2. Lower samples during preview
3. Use **Render Region** for testing

---

## Troubleshooting

### Animation not playing?

- Check frame range is set (1-250)
- Press **Play** button or SPACE
- Check Time value is animated (orange when animated)

### Waves too fast/slow?

- Adjust **Wind Speed** parameter
- Or change animation speed in Graph Editor

### Animation jumps?

- Check keyframe interpolation
- Use **Bezier** for smooth motion
- Add more keyframes for complex motion

---

## Example Scripts

### Super Slow & Calm
```python
sphere = create_smooth_water_sphere(
    wave_scale=0.8,     # Wide waves
    wave_height=0.04,   # Very subtle
    wind_speed=0.15     # Very slow
)
animate_smooth_water_sphere(sphere, speed=0.08)
```

### Gentle Breeze
```python
sphere = create_smooth_water_sphere(
    wave_scale=1.2,     # Medium waves
    wave_height=0.06,   # Moderate
    wind_speed=0.25     # Light wind
)
animate_smooth_water_sphere(sphere, speed=0.15)
```

### Active Water
```python
sphere = create_smooth_water_sphere(
    wave_scale=1.8,     # Smaller waves
    wave_height=0.12,   # More pronounced
    wind_speed=0.5      # Stronger wind
)
animate_smooth_water_sphere(sphere, speed=0.3)
```

---

## Files

- **water_sphere_smooth.py** - Node group definition
- **test_smooth_water_sphere.py** - Basic test with animation
- **animate_smooth_water.py** - Animation methods demo
- **smooth_water_sphere_test.blend** - Ready to use
- **smooth_water_animation_demo.blend** - Shows 4 animation types

---

## Quick Reference

| Action | How |
|--------|-----|
| Play animation | SPACE |
| Pause animation | SPACE |
| Scrub timeline | Drag blue line |
| Add keyframe | Hover value, press I |
| Delete keyframe | Alt+I |
| Change speed | Adjust Wind Speed |
| Change height | Adjust Wave Height |
| Change scale | Adjust Wave Scale |
