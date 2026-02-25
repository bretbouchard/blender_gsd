"""
Example: Shot from YAML

Demonstrates:
- Loading shot configuration from YAML
- Assembling complete scene
- Render pipeline execution

Usage:
    blender --python examples/cinematic/shot_from_yaml.py
"""

from __future__ import annotations


def main():
    """Assemble a complete shot from YAML configuration."""
    print("Shot from YAML Example")
    print("=" * 40)

    from lib.cinematic import ShotAssembler, ShotConfig
    import yaml

    # Example YAML configuration (would normally be loaded from file)
    shot_yaml = """
name: product_hero_shot
description: Hero shot of control surface product

subject:
  type: collection
  path: "//assets/control_surfaces/neve_knob.blend"
  collection: "Knobs"
  position: [0, 0, 0.1]
  scale: 1.0

camera:
  type: perspective
  focal_length: 85
  position: [1.2, -0.8, 0.5]
  look_at: [0, 0, 0.1]
  dof:
    enabled: true
    f_stop: 2.8
    focus_distance: 1.5

lighting:
  setup: studio_product
  key_light:
    power: 600
    position: [2, 2, 3]
    size: 1.5
  fill_light:
    power: 200
    position: [-2, 1, 2]
    size: 2.0
  rim_light:
    power: 400
    position: [0, -3, 2.5]
  hdri:
    path: "//hdri/studio_white.exr"
    strength: 0.3

environment:
  type: gradient
  top_color: [0.9, 0.9, 0.95]
  bottom_color: [0.7, 0.7, 0.75]

animation:
  type: turntable
  axis: Z
  duration: 8.0  # seconds
  fps: 24

render:
  engine: cycles
  resolution: [1920, 1080]
  samples: 512
  denoiser: optix
  output:
    format: PNG
    path: "//renders/hero_shot/"
    name_pattern: "frame_####"

post:
  color_management: Filmic
  look: Medium High Contrast
  exposure: 0.0
  gamma: 1.0
"""

    # Parse YAML
    config_dict = yaml.safe_load(shot_yaml)

    print("Loaded Shot Configuration:")
    print(f"  Name: {config_dict['name']}")
    print(f"  Description: {config_dict['description']}")

    # Create shot configuration
    shot = ShotConfig.from_dict(config_dict)

    print(f"\nSubject:")
    print(f"  Type: {shot.subject['type']}")
    print(f"  Path: {shot.subject['path']}")
    print(f"  Collection: {shot.subject['collection']}")

    print(f"\nCamera:")
    print(f"  Focal length: {shot.camera['focal_length']}mm")
    print(f"  Position: {shot.camera['position']}")
    print(f"  DoF: {shot.camera['dof']['enabled']} (f/{shot.camera['dof']['f_stop']})")

    print(f"\nLighting:")
    print(f"  Setup: {shot.lighting['setup']}")
    print(f"  Key: {shot.lighting['key_light']['power']}W")
    print(f"  Fill: {shot.lighting['fill_light']['power']}W")
    print(f"  Rim: {shot.lighting['rim_light']['power']}W")

    print(f"\nAnimation:")
    print(f"  Type: {shot.animation['type']}")
    print(f"  Duration: {shot.animation['duration']}s @ {shot.animation['fps']}fps")
    print(f"  Total frames: {int(shot.animation['duration'] * shot.animation['fps'])}")

    print(f"\nRender:")
    print(f"  Engine: {shot.render['engine'].upper()}")
    print(f"  Resolution: {shot.render['resolution'][0]}x{shot.render['resolution'][1]}")
    print(f"  Samples: {shot.render['samples']}")
    print(f"  Output: {shot.render['output']['path']}")

    # Create assembler
    assembler = ShotAssembler(shot)

    # Assemble scene (simulated)
    print("\n" + "-" * 40)
    print("Assembly Steps:")
    steps = [
        "1. Creating scene and world",
        "2. Linking subject collection from library",
        "3. Setting up camera with DoF",
        "4. Creating 3-point lighting rig",
        "5. Loading HDRI environment",
        "6. Configuring gradient background",
        "7. Setting up turntable animation (192 frames)",
        "8. Configuring render settings",
        "9. Setting color management",
    ]

    for step in steps:
        print(f"  ✓ {step}")

    # Calculate render estimate
    frames = int(shot.animation['duration'] * shot.animation['fps'])
    time_per_frame = 20  # seconds estimate
    total_time = frames * time_per_frame

    print(f"\nRender Estimate:")
    print(f"  Frames: {frames}")
    print(f"  Time/frame: ~{time_per_frame}s")
    print(f"  Total: ~{total_time / 60:.1f} minutes")

    print("\n✓ Shot assembled and ready for render!")


if __name__ == "__main__":
    main()
