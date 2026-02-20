"""
City Builder - Complete City Generation Orchestrator

Ties together all city systems into a unified builder API.

Usage:
    from lib.animation.city.city_builder import CityBuilder

    # Create Charlotte NC chase scene
    builder = CityBuilder("Charlotte_Chase")
    builder.set_location("charlotte_uptown")
    builder.add_downtown(building_count=50, height_range=(80, 300))
    builder.add_roads(style="urban", lanes=4)
    builder.add_traffic(count=100, style="urban")
    builder.add_hero_car(style="sports", color="red")
    builder.add_pursuit(count=3)
    builder.setup_chase(
        duration=30.0,
        crash_points=[("Trade & Tryon", 0.3), ("I-77", 0.7)]
    )
    builder.setup_cameras(types=["follow", "aerial", "in_car"])
    builder.build()  # Creates all Blender objects

    # Or use quick preset
    builder = CityBuilder.from_preset("hollywood_chase")
    builder.build()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path
import math
import random

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    BLENDER_AVAILABLE = False


@dataclass
class CityConfig:
    """Configuration for city generation."""
    name: str = "City"

    # Location
    geo_bounds: Optional[Tuple[float, float, float, float]] = None  # (s, w, n, e)

    # Roads
    road_grid_size: int = 5
    road_block_size: float = 100.0
    road_lanes: int = 2
    road_style: str = "urban"

    # Buildings
    building_count: int = 30
    building_height_min: float = 30.0
    building_height_max: float = 150.0
    downtown_center: Tuple[float, float] = (0, 0)
    downtown_radius: float = 200.0

    # Traffic
    traffic_count: int = 20
    traffic_style: str = "urban"

    # Chase
    chase_enabled: bool = False
    chase_duration: float = 30.0
    hero_style: str = "sports"
    hero_color: str = "red"
    pursuit_count: int = 3
    crash_points: List[Dict] = field(default_factory=list)

    # Cameras
    camera_types: List[str] = field(default_factory=lambda: ["follow"])
    camera_auto_switch: bool = True

    # Animation
    fps: int = 24
    frame_start: int = 1


# Preset configurations
CITY_PRESETS = {
    "test_city": CityConfig(
        name="Test_City",
        road_grid_size=3,
        building_count=10,
        traffic_count=5,
        chase_enabled=True,
        pursuit_count=2,
        chase_duration=10.0,
    ),
    "charlotte_uptown": CityConfig(
        name="Charlotte_Uptown",
        road_grid_size=6,
        road_lanes=4,
        building_count=50,
        building_height_min=50.0,
        building_height_max=300.0,
        traffic_count=40,
        chase_enabled=True,
        pursuit_count=4,
        chase_duration=45.0,
    ),
    "hollywood_chase": CityConfig(
        name="Hollywood_Chase",
        road_grid_size=8,
        road_lanes=4,
        building_count=80,
        building_height_min=40.0,
        building_height_max=200.0,
        traffic_count=60,
        chase_enabled=True,
        pursuit_count=5,
        chase_duration=60.0,
        crash_points=[
            {"progress": 0.2, "intensity": 0.5},
            {"progress": 0.5, "intensity": 0.8},
            {"progress": 0.8, "intensity": 0.6},
        ],
    ),
    "industrial": CityConfig(
        name="Industrial_Zone",
        road_grid_size=4,
        road_lanes=2,
        building_count=20,
        building_height_min=15.0,
        building_height_max=50.0,
        traffic_count=15,
    ),
}


class CityBuilder:
    """
    Unified city generation orchestrator.

    Provides a fluent API for building complete city scenes.
    """

    def __init__(self, name: str = "City"):
        self.config = CityConfig(name=name)
        self._built = False

        # Built objects
        self.collections: Dict[str, Any] = {}
        self.roads: List[Any] = []
        self.buildings: List[Any] = []
        self.traffic: List[Any] = []
        self.hero_car: Optional[Any] = None
        self.pursuit_cars: List[Any] = []
        self.cameras: List[Any] = []
        self.chase_path: List[Tuple[float, float, float]] = []

        # Callbacks
        self._pre_build_callbacks: List[Callable] = []
        self._post_build_callbacks: List[Callable] = []

    @classmethod
    def from_preset(cls, preset_name: str) -> 'CityBuilder':
        """Create builder from preset configuration."""
        if preset_name not in CITY_PRESETS:
            raise ValueError(
                f"Unknown preset: {preset_name}. "
                f"Available: {list(CITY_PRESETS.keys())}"
            )

        builder = cls()
        builder.config = CityConfig(**{
            k: v for k, v in CITY_PRESETS[preset_name].__dict__.items()
        })
        return builder

    def set_location(
        self,
        preset: Optional[str] = None,
        bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> 'CityBuilder':
        """Set geographic location for city."""
        if preset:
            from .geo_data import GEO_PRESETS
            if preset in GEO_PRESETS:
                bbox = GEO_PRESETS[preset]
                self.config.geo_bounds = (
                    bbox.south, bbox.west, bbox.north, bbox.east
                )
        elif bounds:
            self.config.geo_bounds = bounds
        return self

    def add_roads(
        self,
        grid_size: Optional[int] = None,
        block_size: Optional[float] = None,
        lanes: Optional[int] = None,
        style: Optional[str] = None
    ) -> 'CityBuilder':
        """Configure road network."""
        if grid_size is not None:
            self.config.road_grid_size = grid_size
        if block_size is not None:
            self.config.road_block_size = block_size
        if lanes is not None:
            self.config.road_lanes = lanes
        if style is not None:
            self.config.road_style = style
        return self

    def add_downtown(
        self,
        building_count: Optional[int] = None,
        height_range: Optional[Tuple[float, float]] = None,
        center: Optional[Tuple[float, float]] = None,
        radius: Optional[float] = None
    ) -> 'CityBuilder':
        """Configure downtown area."""
        if building_count is not None:
            self.config.building_count = building_count
        if height_range is not None:
            self.config.building_height_min = height_range[0]
            self.config.building_height_max = height_range[1]
        if center is not None:
            self.config.downtown_center = center
        if radius is not None:
            self.config.downtown_radius = radius
        return self

    def add_traffic(
        self,
        count: Optional[int] = None,
        style: Optional[str] = None
    ) -> 'CityBuilder':
        """Configure traffic."""
        if count is not None:
            self.config.traffic_count = count
        if style is not None:
            self.config.traffic_style = style
        return self

    def add_hero_car(
        self,
        style: Optional[str] = None,
        color: Optional[str] = None
    ) -> 'CityBuilder':
        """Configure hero car."""
        self.config.chase_enabled = True
        if style is not None:
            self.config.hero_style = style
        if color is not None:
            self.config.hero_color = color
        return self

    def add_pursuit(self, count: int) -> 'CityBuilder':
        """Add pursuit vehicles."""
        self.config.chase_enabled = True
        self.config.pursuit_count = count
        return self

    def setup_chase(
        self,
        duration: Optional[float] = None,
        crash_points: Optional[List[Tuple[str, float]]] = None
    ) -> 'CityBuilder':
        """Configure chase sequence."""
        self.config.chase_enabled = True
        if duration is not None:
            self.config.chase_duration = duration
        if crash_points is not None:
            self.config.crash_points = [
                {"location": loc, "progress": prog}
                for loc, prog in crash_points
            ]
        return self

    def setup_cameras(
        self,
        types: Optional[List[str]] = None,
        auto_switch: Optional[bool] = None
    ) -> 'CityBuilder':
        """Configure camera system."""
        if types is not None:
            self.config.camera_types = types
        if auto_switch is not None:
            self.config.camera_auto_switch = auto_switch
        return self

    def on_pre_build(self, callback: Callable) -> 'CityBuilder':
        """Add pre-build callback."""
        self._pre_build_callbacks.append(callback)
        return self

    def on_post_build(self, callback: Callable) -> 'CityBuilder':
        """Add post-build callback."""
        self._post_build_callbacks.append(callback)
        return self

    def build(self) -> 'CityBuilder':
        """
        Execute the build process.

        Creates all Blender objects for the city scene.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender not available")

        if self._built:
            print("Warning: City already built, skipping")
            return self

        # Run pre-build callbacks
        for callback in self._pre_build_callbacks:
            callback(self)

        print(f"\n{'='*60}")
        print(f"Building City: {self.config.name}")
        print(f"{'='*60}\n")

        # Build pipeline
        self._setup_scene()
        self._create_collections()
        self._build_roads()
        self._build_buildings()
        self._build_traffic()
        self._build_chase()
        self._build_cameras()
        self._setup_animation()

        self._built = True

        # Run post-build callbacks
        for callback in self._post_build_callbacks:
            callback(self)

        self._print_summary()

        return self

    def _setup_scene(self) -> None:
        """Configure scene settings."""
        scene = bpy.context.scene
        scene.render.fps = self.config.fps
        scene.frame_start = self.config.frame_start
        scene.frame_end = self.config.frame_start + int(
            self.config.chase_duration * self.config.fps
        )

    def _create_collections(self) -> None:
        """Create collection hierarchy."""
        main = bpy.data.collections.new(self.config.name)
        bpy.context.collection.children.link(main)
        self.collections["main"] = main

        for name in ["Roads", "Buildings", "Traffic", "Hero", "Pursuit", "Cameras"]:
            col = bpy.data.collections.new(name)
            main.children.link(col)
            self.collections[name.lower()] = col

    def _build_roads(self) -> None:
        """Build road network."""
        print("Building roads...")

        from .road_network import create_road_network

        grid = self.config.road_grid_size
        block = self.config.road_block_size

        # Create grid roads
        for i in range(grid + 1):
            # Horizontal
            self._create_road_curve(
                (0, i * block, 0),
                (grid * block, i * block, 0),
                f"H_Road_{i}"
            )
            # Vertical
            self._create_road_curve(
                (i * block, 0, 0),
                (i * block, grid * block, 0),
                f"V_Road_{i}"
            )

        # Generate chase path
        self.chase_path = self._generate_chase_path()

        print(f"  Created {len(self.roads)} road segments")

    def _create_road_curve(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        name: str
    ) -> None:
        """Create road curve object."""
        width = self.config.road_lanes * 3.5

        curve = bpy.data.curves.new(name, type='CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth = width
        curve.fill_mode = 'FULL'

        spline = curve.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (*start, 1.0)
        spline.points[1].co = (*end, 1.0)

        obj = bpy.data.objects.new(name, curve)
        self.collections["roads"].objects.link(obj)
        self.roads.append(obj)

        # Material
        self._apply_asphalt_material(obj)

    def _generate_chase_path(self) -> List[Tuple[float, float, float]]:
        """Generate chase path through city."""
        grid = self.config.road_grid_size
        block = self.config.road_block_size

        # Diagonal path with some variation
        path = [(0, 0, 0)]

        for i in range(1, grid + 1):
            x = i * block
            y = i * block * 0.8 + random.uniform(-20, 20)
            path.append((x, y, 0))

        path.append((grid * block, grid * block, 0))
        return path

    def _build_buildings(self) -> None:
        """Build city buildings."""
        print("Building buildings...")

        grid = self.config.road_grid_size
        block = self.config.road_block_size
        road_width = self.config.road_lanes * 3.5 + 5

        random.seed(42)

        building_idx = 0
        for bx in range(grid):
            for by in range(grid):
                if building_idx >= self.config.building_count:
                    break

                # Block center with offset
                cx = (bx + 0.5) * block
                cy = (by + 0.5) * block

                # Position within block
                x = cx + random.uniform(-block/2 + road_width, block/2 - road_width)
                y = cy + random.uniform(-block/2 + road_width, block/2 - road_width)

                # Height based on distance from downtown center
                dist = math.sqrt(
                    (x - self.config.downtown_center[0])**2 +
                    (y - self.config.downtown_center[1])**2
                )
                height_factor = max(0.3, 1.0 - dist / self.config.downtown_radius)

                width = random.uniform(15, 35)
                depth = random.uniform(15, 35)
                height = random.uniform(
                    self.config.building_height_min,
                    self.config.building_height_max
                ) * height_factor

                building = self._create_building(
                    (x, y, 0),
                    (width, depth, height),
                    f"Building_{building_idx:03d}"
                )
                self.buildings.append(building)
                building_idx += 1

        print(f"  Created {len(self.buildings)} buildings")

    def _create_building(
        self,
        position: Tuple[float, float, float],
        size: Tuple[float, float, float],
        name: str
    ) -> Any:
        """Create single building mesh."""
        import bmesh

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
        bm.faces.new([verts[0], verts[3], verts[2], verts[1]])
        bm.faces.new([verts[4], verts[5], verts[6], verts[7]])
        bm.faces.new([verts[0], verts[1], verts[5], verts[4]])
        bm.faces.new([verts[1], verts[2], verts[6], verts[5]])
        bm.faces.new([verts[2], verts[3], verts[7], verts[6]])
        bm.faces.new([verts[3], verts[0], verts[4], verts[7]])

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(name, mesh)
        self.collections["buildings"].objects.link(obj)

        # Material
        self._apply_building_material(obj)
        return obj

    def _build_traffic(self) -> None:
        """Build traffic vehicles."""
        print("Building traffic...")

        random.seed(123)

        # Try to use ProceduralCarFactory
        try:
            from ..vehicle.procedural_car import ProceduralCarFactory
            factory = ProceduralCarFactory()
            use_factory = True
        except ImportError:
            use_factory = False

        for i in range(self.config.traffic_count):
            if use_factory:
                try:
                    vehicle = factory.create_car(
                        name=f"Traffic_{i:03d}",
                        style=random.choice(["sedan", "suv", "hatchback"]),
                        color=random.choice(["red", "blue", "white", "black", "silver"])
                    )
                except:
                    vehicle = self._create_simple_vehicle(f"Traffic_{i:03d}")
            else:
                vehicle = self._create_simple_vehicle(f"Traffic_{i:03d}")

            # Position on roads
            grid = self.config.road_grid_size
            block = self.config.road_block_size
            vehicle.location = (
                random.uniform(0, grid * block),
                random.uniform(0, grid * block),
                0.6
            )
            vehicle.rotation_euler[2] = random.uniform(0, 2 * math.pi)

            self.collections["traffic"].objects.link(vehicle)
            self.traffic.append(vehicle)

        print(f"  Created {len(self.traffic)} traffic vehicles")

    def _build_chase(self) -> None:
        """Build chase sequence."""
        if not self.config.chase_enabled:
            return

        print("Building chase...")

        # Create hero car
        self.hero_car = self._create_hero_car()
        self.collections["hero"].objects.link(self.hero_car)

        # Create pursuit cars
        for i in range(self.config.pursuit_count):
            pursuit = self._create_pursuit_car(i)
            self.collections["pursuit"].objects.link(pursuit)
            self.pursuit_cars.append(pursuit)

        # Animate along path
        total_frames = int(self.config.chase_duration * self.config.fps)

        if self.hero_car and self.chase_path:
            self._animate_on_path(self.hero_car, self.chase_path, 0)

        for i, pursuit in enumerate(self.pursuit_cars):
            offset = (i + 1) * 15  # Frame offset
            if self.chase_path:
                self._animate_on_path(pursuit, self.chase_path, offset)

        print(f"  Created 1 hero + {len(self.pursuit_cars)} pursuit cars")

    def _create_hero_car(self) -> Any:
        """Create hero vehicle."""
        try:
            from ..vehicle.procedural_car import create_car
            return create_car(
                style=self.config.hero_style,
                color=self.config.hero_color,
                name="Hero_Car"
            )
        except:
            return self._create_simple_vehicle("Hero_Car", (0.9, 0.1, 0.1))

    def _create_pursuit_car(self, index: int) -> Any:
        """Create pursuit vehicle."""
        try:
            from ..vehicle.procedural_car import create_car
            return create_car(
                style="sedan",
                color="black",
                name=f"Pursuit_{index:02d}"
            )
        except:
            return self._create_simple_vehicle(
                f"Pursuit_{index:02d}",
                (0.1, 0.1, 0.3)
            )

    def _animate_on_path(
        self,
        obj: Any,
        path: List[Tuple[float, float, float]],
        frame_offset: int
    ) -> None:
        """Animate object along path using Follow Path constraint."""
        # Create path curve
        curve_data = bpy.data.curves.new(f"{obj.name}_Path", type='CURVE')
        curve_data.dimensions = '3D'

        spline = curve_data.splines.new('POLY')
        spline.points.add(len(path) - 1)
        for i, point in enumerate(path):
            spline.points[i].co = (*point, 1.0)

        path_obj = bpy.data.objects.new(f"{obj.name}_Path", curve_data)
        self.collections["main"].objects.link(path_obj)

        # Add constraint
        constraint = obj.constraints.new('FOLLOW_PATH')
        constraint.target = path_obj
        constraint.use_curve_follow = True
        constraint.use_fixed_location = True

        # Keyframe animation
        curve_data.offset_factor = 0.0
        curve_data.keyframe_insert(
            "offset_factor",
            frame=self.config.frame_start + frame_offset
        )

        curve_data.offset_factor = 1.0
        curve_data.keyframe_insert(
            "offset_factor",
            frame=self.config.frame_start + int(self.config.chase_duration * self.config.fps)
        )

    def _build_cameras(self) -> None:
        """Build camera system."""
        print("Building cameras...")

        for cam_type in self.config.camera_types:
            cam = self._create_camera(cam_type)
            self.cameras.append(cam)

        # Set first camera as active
        if self.cameras:
            bpy.context.scene.camera = self.cameras[0]

        print(f"  Created {len(self.cameras)} cameras")

    def _create_camera(self, cam_type: str) -> Any:
        """Create camera based on type."""
        cam_data = bpy.data.cameras.new(f"{cam_type}_Camera")

        if cam_type == "follow":
            cam_data.lens = 50.0
            position = (-30, 15, 8)
        elif cam_type == "aerial":
            cam_data.lens = 35.0
            position = (0, 0, 150)
        elif cam_type == "in_car":
            cam_data.lens = 24.0
            position = (0.5, -0.3, 1.2)
        else:
            cam_data.lens = 50.0
            position = (0, -50, 10)

        obj = bpy.data.objects.new(cam_data.name, cam_data)
        obj.location = position
        self.collections["cameras"].objects.link(obj)

        # Track to hero if follow camera
        if cam_type == "follow" and self.hero_car:
            track = obj.constraints.new('TRACK_TO')
            track.target = self.hero_car
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'

        return obj

    def _setup_animation(self) -> None:
        """Setup animation timeline."""
        scene = bpy.context.scene
        scene.frame_set(self.config.frame_start)

    def _create_simple_vehicle(
        self,
        name: str,
        color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    ) -> Any:
        """Create simple box vehicle."""
        import bmesh

        bm = bmesh.new()
        mesh = bpy.data.meshes.new(name)

        # Car dimensions
        l, w, h = 4.0, 1.8, 1.2

        verts = [
            bm.verts.new((-l/2, -w/2, 0)),
            bm.verts.new((l/2, -w/2, 0)),
            bm.verts.new((l/2, w/2, 0)),
            bm.verts.new((-l/2, w/2, 0)),
            bm.verts.new((-l/2, -w/2, h)),
            bm.verts.new((l/2, -w/2, h)),
            bm.verts.new((l/2, w/2, h)),
            bm.verts.new((-l/2, w/2, h)),
        ]
        bm.verts.ensure_lookup_table()

        for face in [
            [0, 3, 2, 1], [4, 5, 6, 7],
            [0, 1, 5, 4], [1, 2, 6, 5],
            [2, 3, 7, 6], [3, 0, 4, 7]
        ]:
            bm.faces.new([verts[i] for i in face])

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

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        return obj

    def _apply_asphalt_material(self, obj: Any) -> None:
        """Apply asphalt material to object."""
        if "City_Asphalt" in bpy.data.materials:
            mat = bpy.data.materials["City_Asphalt"]
        else:
            mat = bpy.data.materials.new("City_Asphalt")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
                bsdf.inputs["Roughness"].default_value = 0.9

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    def _apply_building_material(self, obj: Any) -> None:
        """Apply building material to object."""
        styles = ["Glass", "Concrete", "Steel"]
        style = random.choice(styles)
        mat_name = f"City_Building_{style}"

        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")

            colors = {
                "Glass": (0.5, 0.6, 0.7, 0.1, 0.9),
                "Concrete": (0.6, 0.58, 0.55, 0.0, 0.9),
                "Steel": (0.5, 0.52, 0.55, 0.8, 0.4),
            }
            r, g, b, metal, rough = colors[style]

            if bsdf:
                bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
                bsdf.inputs["Metallic"].default_value = metal
                bsdf.inputs["Roughness"].default_value = rough

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    def _print_summary(self) -> None:
        """Print build summary."""
        print(f"\n{'='*60}")
        print(f"Build Complete: {self.config.name}")
        print(f"  Roads: {len(self.roads)}")
        print(f"  Buildings: {len(self.buildings)}")
        print(f"  Traffic: {len(self.traffic)}")
        print(f"  Cameras: {len(self.cameras)}")
        if self.config.chase_enabled:
            print(f"  Chase: {self.config.chase_duration}s @ {self.config.fps} fps")
        print(f"{'='*60}\n")


# Convenience function
def create_city(preset: str = "test_city") -> CityBuilder:
    """Create city from preset."""
    builder = CityBuilder.from_preset(preset)
    return builder.build()
