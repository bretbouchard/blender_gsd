"""
City Chase Demo - Executable Blender Script

Run this in Blender to create a complete city chase scene:
    blender --python projects/city_chase/demo_city_chase.py

Or run from Blender's Script tab.

Creates:
- Procedural city grid with roads
- Downtown buildings
- Traffic vehicles
- Hero car with pursuit
- Multi-camera coverage
- Full animation timeline

Usage:
    # Quick test (small city, few cars)
    blender --python demo_city_chase.py -- --preset test

    # Full Charlotte scene
    blender --python demo_city_chase.py -- --preset charlotte

    # Custom parameters
    blender --python demo_city_chase.py -- --buildings 50 --traffic 30 --chase-cars 4
"""

import bpy
import sys
import math
import random
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

# Add lib to path
script_dir = Path(__file__).parent
lib_path = script_dir.parent.parent / "lib"
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))


@dataclass
class DemoConfig:
    """Configuration for demo scene."""
    name: str = "City_Chase_Demo"

    # City settings
    grid_size: int = 5  # Number of blocks
    block_size: float = 100.0  # Meters per block
    road_lanes: int = 2

    # Buildings
    building_count: int = 30
    building_height_min: float = 30.0
    building_height_max: float = 150.0

    # Traffic
    traffic_count: int = 20
    traffic_speed: float = 40.0  # km/h

    # Chase
    chase_duration: float = 30.0  # seconds
    hero_speed: float = 100.0  # km/h
    pursuit_count: int = 3
    crash_points: int = 2

    # Cameras
    camera_types: List[str] = None
    camera_switch_interval: float = 3.0

    # Animation
    fps: int = 24
    frame_start: int = 1

    # Render
    render_enabled: bool = False
    render_path: str = "//output/chase_"


# Preset configurations
PRESETS = {
    "test": DemoConfig(
        name="Test_Chase",
        grid_size=3,
        building_count=10,
        traffic_count=5,
        pursuit_count=2,
        chase_duration=10.0,
    ),
    "quick": DemoConfig(
        name="Quick_Chase",
        grid_size=4,
        building_count=20,
        traffic_count=10,
        pursuit_count=3,
        chase_duration=20.0,
    ),
    "charlotte": DemoConfig(
        name="Charlotte_Chase",
        grid_size=6,
        building_count=50,
        traffic_count=40,
        pursuit_count=4,
        chase_duration=45.0,
        hero_speed=120.0,
    ),
    "hollywood": DemoConfig(
        name="Hollywood_Chase",
        grid_size=8,
        building_count=80,
        traffic_count=60,
        pursuit_count=5,
        chase_duration=60.0,
        hero_speed=140.0,
        crash_points=4,
    ),
}


class CityChaseBuilder:
    """
    Orchestrates the complete city chase scene construction.

    This is the main entry point that ties together:
    - Road network generation
    - Building placement
    - Traffic spawning
    - Chase setup
    - Camera system
    - Animation timeline
    """

    def __init__(self, config: DemoConfig):
        self.config = config
        self.scene = bpy.context.scene

        # Collections
        self.collections: Dict[str, bpy.types.Collection] = {}

        # Scene elements
        self.roads: List[Any] = []
        self.buildings: List[Any] = []
        self.traffic_vehicles: List[Any] = []
        self.hero_car: Optional[Any] = None
        self.pursuit_cars: List[Any] = []
        self.cameras: List[Any] = []

        # Chase data
        self.chase_path: List[Tuple[float, float, float]] = []
        self.crash_points: List[Dict] = []

    def build_all(self) -> None:
        """Execute full build pipeline."""
        print(f"\n{'='*60}")
        print(f"Building City Chase Scene: {self.config.name}")
        print(f"{'='*60}\n")

        # Setup scene
        self._setup_scene()

        # Build in order
        self._create_collections()
        self._build_roads()
        self._build_buildings()
        self._create_vehicles()
        self._setup_chase()
        self._setup_cameras()
        self._setup_animation()

        print(f"\n{'='*60}")
        print(f"Build Complete!")
        print(f"  - Buildings: {len(self.buildings)}")
        print(f"  - Traffic: {len(self.traffic_vehicles)}")
        print(f"  - Cameras: {len(self.cameras)}")
        print(f"  - Duration: {self.config.chase_duration}s @ {self.config.fps} fps")
        print(f"{'='*60}\n")

    def _setup_scene(self) -> None:
        """Configure scene settings."""
        self.scene.render.fps = self.config.fps
        self.scene.frame_start = self.config.frame_start
        self.scene.frame_end = self.config.frame_start + int(
            self.config.chase_duration * self.config.fps
        )

        # Set world background
        world = self.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            self.scene.world = world

        world.use_nodes = True
        bg_node = world.node_tree.nodes.get("Background")
        if bg_node:
            bg_node.inputs["Color"].default_value = (0.5, 0.6, 0.7, 1.0)
            bg_node.inputs["Strength"].default_value = 0.5

    def _create_collections(self) -> None:
        """Create collection hierarchy for scene organization."""
        main_col = bpy.data.collections.new(self.config.name)
        bpy.context.collection.children.link(main_col)
        self.collections["main"] = main_col

        # Sub-collections
        for name in ["Roads", "Buildings", "Traffic", "Hero", "Pursuit", "Cameras", "Lights"]:
            col = bpy.data.collections.new(name)
            main_col.children.link(col)
            self.collections[name.lower()] = col

    def _build_roads(self) -> None:
        """Build road network."""
        print("Building road network...")

        grid = self.config.grid_size
        block = self.config.block_size

        # Create grid roads
        for i in range(grid + 1):
            # Horizontal roads
            self._create_road_segment(
                start=(0, i * block, 0),
                end=(grid * block, i * block, 0),
                name=f"H_Road_{i}"
            )

            # Vertical roads
            self._create_road_segment(
                start=(i * block, 0, 0),
                end=(i * block, grid * block, 0),
                name=f"V_Road_{i}"
            )

        # Generate chase path (diagonal through city)
        self.chase_path = [
            (0, 0, 0),
            (block * 0.5, block * 0.3, 0),
            (block * 1.5, block * 1.2, 0),
            (block * 2.5, block * 2.0, 0),
            (block * 3.5, block * 3.0, 0),
            (grid * block, grid * block, 0),
        ]

        print(f"  Created {len(self.roads)} road segments")

    def _create_road_segment(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        name: str
    ) -> None:
        """Create a single road segment."""
        # Create curve
        curve_data = bpy.data.curves.new(name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = self.config.road_lanes * 1.75  # Road width
        curve_data.fill_mode = 'FULL'

        # Create spline
        spline = curve_data.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (*start, 1.0)
        spline.points[1].co = (*end, 1.0)

        # Create object
        obj = bpy.data.objects.new(name, curve_data)
        self.collections["roads"].objects.link(obj)
        self.roads.append(obj)

        # Apply asphalt material
        mat = self._get_asphalt_material()
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    def _get_asphalt_material(self) -> bpy.types.Material:
        """Get or create asphalt material."""
        if "Road_Asphalt" in bpy.data.materials:
            return bpy.data.materials["Road_Asphalt"]

        mat = bpy.data.materials.new("Road_Asphalt")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.9

        return mat

    def _build_buildings(self) -> None:
        """Place buildings in city blocks."""
        print("Placing buildings...")

        grid = self.config.grid_size
        block = self.config.block_size
        road_width = self.config.road_lanes * 3.5

        random.seed(42)  # Reproducible

        building_idx = 0
        for bx in range(grid):
            for by in range(grid):
                if building_idx >= self.config.building_count:
                    break

                # Block center
                cx = (bx + 0.5) * block
                cy = (by + 0.5) * block

                # Random position within block (avoiding roads)
                margin = road_width + 5
                x = cx + random.uniform(-block/2 + margin, block/2 - margin)
                y = cy + random.uniform(-block/2 + margin, block/2 - margin)

                # Random building size and height
                width = random.uniform(15, 35)
                depth = random.uniform(15, 35)
                height = random.uniform(
                    self.config.building_height_min,
                    self.config.building_height_max
                )

                # Distance from center affects height (taller downtown)
                dist_from_center = math.sqrt(
                    (cx - grid * block / 2)**2 +
                    (cy - grid * block / 2)**2
                )
                height_factor = 1.0 - (dist_from_center / (grid * block)) * 0.5
                height *= height_factor

                building = self._create_building(
                    position=(x, y, 0),
                    size=(width, depth, height),
                    name=f"Building_{building_idx:03d}"
                )

                self.buildings.append(building)
                building_idx += 1

        print(f"  Created {len(self.buildings)} buildings")

    def _create_building(
        self,
        position: Tuple[float, float, float],
        size: Tuple[float, float, float],
        name: str
    ) -> bpy.types.Object:
        """Create a single building mesh."""
        import bmesh

        # Create mesh
        bm = bmesh.new()
        mesh = bpy.data.meshes.new(name)

        w, d, h = size
        x, y, z = position

        # Create box
        verts = [
            bm.verts.new((x - w/2, y - d/2, z)),
            bm.verts.new((x + w/2, y - d/2, z)),
            bm.verts.new((x + w/2, y + d/2, z)),
            bm.verts.new((x - w/2, y + d/2, z)),
            bm.verts.new((x - w/2, y - d/2, z + h)),
            bm.verts.new((x + w/2, y - d/2, z + h)),
            bm.verts.new((x + w/2, y + d/2, z + h)),
            bm.verts.new((x - w/2, y + d/2, z + h)),
        ]

        bm.verts.ensure_lookup_table()

        # Faces
        # Bottom
        bm.faces.new([verts[0], verts[3], verts[2], verts[1]])
        # Top
        bm.faces.new([verts[4], verts[5], verts[6], verts[7]])
        # Sides
        bm.faces.new([verts[0], verts[1], verts[5], verts[4]])
        bm.faces.new([verts[1], verts[2], verts[6], verts[5]])
        bm.faces.new([verts[2], verts[3], verts[7], verts[6]])
        bm.faces.new([verts[3], verts[0], verts[4], verts[7]])

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(name, mesh)
        self.collections["buildings"].objects.link(obj)

        # Random building material
        mat = self._get_building_material(random.choice([
            "glass", "concrete", "steel"
        ]))
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        return obj

    def _get_building_material(self, style: str) -> bpy.types.Material:
        """Get or create building material."""
        name = f"Building_{style}"
        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")

        if style == "glass":
            color = (0.5, 0.6, 0.7)
            metallic = 0.9
            roughness = 0.1
        elif style == "concrete":
            color = (0.6, 0.58, 0.55)
            metallic = 0.0
            roughness = 0.9
        else:  # steel
            color = (0.5, 0.52, 0.55)
            metallic = 0.8
            roughness = 0.4

        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Metallic"].default_value = metallic
            bsdf.inputs["Roughness"].default_value = roughness

        return mat

    def _create_vehicles(self) -> None:
        """Create traffic and chase vehicles."""
        print("Creating vehicles...")

        # Try to use procedural car factory if available
        try:
            from animation.vehicle.procedural_car import ProceduralCarFactory
            self._use_procedural_cars = True
            self._car_factory = ProceduralCarFactory()
        except ImportError:
            self._use_procedural_cars = False
            print("  Note: ProceduralCarFactory not available, using simple boxes")

        # Create traffic vehicles
        for i in range(self.config.traffic_count):
            vehicle = self._create_simple_vehicle(
                name=f"Traffic_{i:03d}",
                color=self._random_traffic_color()
            )
            self.collections["traffic"].objects.link(vehicle)
            self.traffic_vehicles.append(vehicle)

        # Create hero car
        self.hero_car = self._create_simple_vehicle(
            name="Hero_Car",
            color=(0.9, 0.1, 0.1),  # Red
            scale=1.2
        )
        self.collections["hero"].objects.link(self.hero_car)

        # Create pursuit cars
        for i in range(self.config.pursuit_count):
            pursuit = self._create_simple_vehicle(
                name=f"Pursuit_{i:02d}",
                color=(0.1, 0.1, 0.4),  # Dark blue
                is_police=True
            )
            self.collections["pursuit"].objects.link(pursuit)
            self.pursuit_cars.append(pursuit)

        print(f"  Created {len(self.traffic_vehicles)} traffic vehicles")
        print(f"  Created 1 hero car + {len(self.pursuit_cars)} pursuit cars")

    def _create_simple_vehicle(
        self,
        name: str,
        color: Tuple[float, float, float],
        scale: float = 1.0,
        is_police: bool = False
    ) -> bpy.types.Object:
        """Create a simple vehicle mesh (box car)."""
        import bmesh

        bm = bmesh.new()
        mesh = bpy.data.meshes.new(name)

        # Car dimensions (simple box)
        length = 4.0 * scale
        width = 1.8 * scale
        height = 1.2 * scale

        # Create box
        verts = [
            bm.verts.new((-length/2, -width/2, 0)),
            bm.verts.new((length/2, -width/2, 0)),
            bm.verts.new((length/2, width/2, 0)),
            bm.verts.new((-length/2, width/2, 0)),
            bm.verts.new((-length/2, -width/2, height)),
            bm.verts.new((length/2, -width/2, height)),
            bm.verts.new((length/2, width/2, height)),
            bm.verts.new((-length/2, width/2, height)),
        ]

        bm.verts.ensure_lookup_table()

        # Create faces
        bm.faces.new([verts[0], verts[3], verts[2], verts[1]])  # Bottom
        bm.faces.new([verts[4], verts[5], verts[6], verts[7]])  # Top
        bm.faces.new([verts[0], verts[1], verts[5], verts[4]])
        bm.faces.new([verts[1], verts[2], verts[6], verts[5]])
        bm.faces.new([verts[2], verts[3], verts[7], verts[6]])
        bm.faces.new([verts[3], verts[0], verts[4], verts[7]])

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(name, mesh)

        # Material
        mat = bpy.data.materials.new(f"{name}_Mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.8
            bsdf.inputs["Roughness"].default_value = 0.3

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        return obj

    def _random_traffic_color(self) -> Tuple[float, float, float]:
        """Get random traffic vehicle color."""
        colors = [
            (0.8, 0.1, 0.1),   # Red
            (0.1, 0.2, 0.8),   # Blue
            (0.95, 0.95, 0.95),  # White
            (0.1, 0.1, 0.1),   # Black
            (0.7, 0.7, 0.75),  # Silver
            (0.1, 0.5, 0.2),   # Green
            (0.9, 0.8, 0.1),   # Yellow
        ]
        return random.choice(colors)

    def _setup_chase(self) -> None:
        """Setup chase path animation."""
        print("Setting up chase animation...")

        # Calculate total frames
        total_frames = int(self.config.chase_duration * self.config.fps)

        # Animate hero car along path
        if self.hero_car and self.chase_path:
            self._animate_along_path(
                self.hero_car,
                self.chase_path,
                self.config.frame_start,
                total_frames
            )

        # Animate pursuit cars with offset
        for i, pursuit in enumerate(self.pursuit_cars):
            offset_frames = (i + 1) * 12  # Stagger start
            if self.chase_path:
                self._animate_along_path(
                    pursuit,
                    self.chase_path,
                    self.config.frame_start + offset_frames,
                    total_frames - offset_frames
                )

        # Position traffic vehicles randomly
        grid = self.config.grid_size
        block = self.config.block_size
        for i, vehicle in enumerate(self.traffic_vehicles):
            x = random.uniform(0, grid * block)
            y = random.uniform(0, grid * block)
            vehicle.location = (x, y, 0.6)
            vehicle.rotation_euler[2] = random.uniform(0, 2 * math.pi)

        # Generate crash points
        self.crash_points = []
        for i in range(self.config.crash_points):
            progress = (i + 1) / (self.config.crash_points + 1)
            self.crash_points.append({
                "progress": progress,
                "intensity": random.uniform(0.3, 0.8),
            })

        print(f"  Chase duration: {self.config.chase_duration}s ({total_frames} frames)")
        print(f"  Crash points: {len(self.crash_points)}")

    def _animate_along_path(
        self,
        obj: bpy.types.Object,
        path: List[Tuple[float, float, float]],
        frame_start: int,
        frame_count: int
    ) -> None:
        """Animate object along path."""
        if len(path) < 2:
            return

        # Create curve for path
        curve_data = bpy.data.curves.new(f"{obj.name}_Path", type='CURVE')
        curve_data.dimensions = '3D'

        spline = curve_data.splines.new('POLY')
        spline.points.add(len(path) - 1)

        for i, point in enumerate(path):
            spline.points[i].co = (*point, 1.0)

        path_obj = bpy.data.objects.new(f"{obj.name}_Path", curve_data)
        self.collections["main"].objects.link(path_obj)

        # Add Follow Path constraint
        constraint = obj.constraints.new('FOLLOW_PATH')
        constraint.target = path_obj
        constraint.use_curve_follow = True
        constraint.use_fixed_location = True

        # Animate offset factor
        path_data = path_obj.data
        path_data.animation_data_create()
        path_data.animation_data.action = bpy.data.actions.new(f"{obj.name}_PathAction")

        # Keyframe start
        path_data.offset_factor = 0.0
        path_data.keyframe_insert("offset_factor", frame=frame_start)

        # Keyframe end
        path_data.offset_factor = 1.0
        path_data.keyframe_insert("offset_factor", frame=frame_start + frame_count)

    def _setup_cameras(self) -> None:
        """Setup chase cameras."""
        print("Setting up cameras...")

        # Main follow camera
        follow_cam = self._create_camera(
            name="Follow_Camera",
            focal_length=50.0,
            position=(-30, 10, 8)
        )
        self.cameras.append(follow_cam)

        # Wide aerial camera
        aerial_cam = self._create_camera(
            name="Aerial_Camera",
            focal_length=35.0,
            position=(0, 0, 150)
        )
        self.cameras.append(aerial_cam)

        # Track follow camera to hero car
        if self.hero_car:
            track = follow_cam.constraints.new('TRACK_TO')
            track.target = self.hero_car
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'

        # Set follow camera as active
        self.scene.camera = follow_cam

        print(f"  Created {len(self.cameras)} cameras")

    def _create_camera(
        self,
        name: str,
        focal_length: float,
        position: Tuple[float, float, float]
    ) -> bpy.types.Object:
        """Create a camera object."""
        cam_data = bpy.data.cameras.new(name)
        cam_data.lens = focal_length

        obj = bpy.data.objects.new(name, cam_data)
        obj.location = position
        self.collections["cameras"].objects.link(obj)

        return obj

    def _setup_animation(self) -> None:
        """Setup animation timeline and keyframes."""
        print("Setting up animation...")

        # Set frame range
        self.scene.frame_start = self.config.frame_start
        self.scene.frame_end = self.config.frame_start + int(
            self.config.chase_duration * self.config.fps
        )

        # Set current frame to start
        self.scene.frame_set(self.config.frame_start)


def parse_args() -> DemoConfig:
    """Parse command line arguments."""
    config = DemoConfig()

    # Get args after '--'
    try:
        arg_index = sys.argv.index('--')
        args = sys.argv[arg_index + 1:]
    except ValueError:
        args = []

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--preset" and i + 1 < len(args):
            preset = args[i + 1]
            if preset in PRESETS:
                config = PRESETS[preset]
            i += 2

        elif arg == "--buildings" and i + 1 < len(args):
            config.building_count = int(args[i + 1])
            i += 2

        elif arg == "--traffic" and i + 1 < len(args):
            config.traffic_count = int(args[i + 1])
            i += 2

        elif arg == "--chase-cars" and i + 1 < len(args):
            config.pursuit_count = int(args[i + 1])
            i += 2

        elif arg == "--duration" and i + 1 < len(args):
            config.chase_duration = float(args[i + 1])
            i += 2

        elif arg == "--render":
            config.render_enabled = True
            i += 1

        else:
            i += 1

    return config


def main():
    """Main entry point."""
    config = parse_args()

    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Build the scene
    builder = CityChaseBuilder(config)
    builder.build_all()

    # Render if requested
    if config.render_enabled:
        print("\nRendering...")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
