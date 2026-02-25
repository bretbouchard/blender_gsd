"""
Charlotte Race Loop System

Defines the Uptown Charlotte race loop with:
- Route waypoints from real Charlotte streets
- Path highlighting system
- Vehicle spawn with driver camera
- Accurate elevation integration (10.5m variation across loop)

Route:
    Start: Church St & MLK Jr Blvd
    → S Church St south to W Morehead St
    → Right onto Morehead, then ramp to I-277
    → I-277 east to College St exit
    → College St north to E 5th St
    → Right onto E 5th St
    → Right onto N Caldwell St
    → Right onto E Trade St
    → Left onto S Church St (back to start)

Total Distance: ~4.6 km
Elevation: 226m - 236.5m (10.5m variation)
Notable grades: Trade West -1.6% (noticeable downhill)
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))

try:
    import bpy
    from mathutils import Vector, Matrix, Euler
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

# Import enhanced elevation system
try:
    from lib.elevation_real import get_real_elevation_manager
    ELEVATION_AVAILABLE = True
except ImportError:
    ELEVATION_AVAILABLE = False


# =============================================================================
# REAL VEHICLE DIMENSIONS (Meters)
# =============================================================================

@dataclass
class VehicleDimensions:
    """Real-world vehicle dimensions for accurate scale."""
    name: str
    length: float      # meters
    width: float       # meters
    height: float      # meters
    wheelbase: float   # meters (front to rear axle)
    track_width: float # meters (width between wheels)
    ground_clearance: float  # meters
    driver_eye_height: float  # meters from ground
    mass_kg: float     # kg


# Real vehicle specifications
VEHICLE_SPECS = {
    # Compact sedan (Toyota Camry / Honda Accord class)
    'sedan_compact': VehicleDimensions(
        name="Compact Sedan",
        length=4.88,
        width=1.84,
        height=1.45,
        wheelbase=2.82,
        track_width=1.60,
        ground_clearance=0.15,
        driver_eye_height=1.15,  # Eye level from ground
        mass_kg=1500,
    ),

    # Mid-size sedan (BMW 5 series / Mercedes E-Class)
    'sedan_midsize': VehicleDimensions(
        name="Mid-size Sedan",
        length=4.96,
        width=1.87,
        height=1.47,
        wheelbase=2.97,
        track_width=1.63,
        ground_clearance=0.14,
        driver_eye_height=1.20,
        mass_kg=1750,
    ),

    # Sports car (Porsche 911 / Corvette)
    'sports_car': VehicleDimensions(
        name="Sports Car",
        length=4.52,
        width=1.85,
        height=1.30,
        wheelbase=2.45,
        track_width=1.60,
        ground_clearance=0.11,
        driver_eye_height=1.08,  # Lower seating position
        mass_kg=1600,
    ),

    # SUV (Ford Explorer / Chevy Tahoe)
    'suv': VehicleDimensions(
        name="SUV",
        length=5.05,
        width=2.00,
        height=1.78,
        wheelbase=3.03,
        track_width=1.72,
        ground_clearance=0.21,
        driver_eye_height=1.45,  # Higher seating
        mass_kg=2200,
    ),

    # Muscle car (Ford Mustang / Dodge Charger)
    'muscle_car': VehicleDimensions(
        name="Muscle Car",
        length=4.79,
        width=1.92,
        height=1.38,
        wheelbase=2.72,
        track_width=1.65,
        ground_clearance=0.13,
        driver_eye_height=1.12,
        mass_kg=1800,
    ),

    # Supercar (Ferrari / Lamborghini)
    'supercar': VehicleDimensions(
        name="Supercar",
        length=4.58,
        width=1.94,
        height=1.20,
        wheelbase=2.65,
        track_width=1.68,
        ground_clearance=0.10,
        driver_eye_height=1.02,  # Very low
        mass_kg=1550,
    ),
}


# =============================================================================
# RACE LOOP WAYPOINTS
# =============================================================================

@dataclass
class Waypoint:
    """A waypoint on the race loop."""
    name: str
    lat: float
    lon: float
    instruction: str
    segment_type: str  # 'straight', 'turn_left', 'turn_right', 'highway', 'exit'
    speed_limit_kmh: float
    is_checkpoint: bool = False
    elevation: float = 0.0  # Meters above sea level
    grade_percent: float = 0.0  # Grade from previous waypoint


# Charlotte Uptown Race Loop Waypoints
# These are approximate GPS coordinates for the route
RACE_LOOP_WAYPOINTS = [
    Waypoint(
        name="Start_Line",
        lat=35.2235,
        lon=-80.8455,
        instruction="Start - Church St & MLK Jr Blvd",
        segment_type="straight",
        speed_limit_kmh=35,
        is_checkpoint=True,
    ),
    Waypoint(
        name="Church_South",
        lat=35.2210,
        lon=-80.8455,
        instruction="Continue south on S Church St",
        segment_type="straight",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="Morehead_Right",
        lat=35.2178,
        lon=-80.8455,
        instruction="Turn right onto W Morehead St",
        segment_type="turn_right",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="I277_Ramp",
        lat=35.2170,
        lon=-80.8420,
        instruction="Merge onto I-277 East ramp",
        segment_type="highway",
        speed_limit_kmh=55,
    ),
    Waypoint(
        name="I277_East",
        lat=35.2200,
        lon=-80.8350,
        instruction="Continue on I-277 East",
        segment_type="highway",
        speed_limit_kmh=55,
    ),
    Waypoint(
        name="College_Exit",
        lat=35.2250,
        lon=-80.8320,
        instruction="Exit onto College St",
        segment_type="exit",
        speed_limit_kmh=45,
    ),
    Waypoint(
        name="College_North",
        lat=35.2280,
        lon=-80.8325,
        instruction="Continue north on N College St",
        segment_type="straight",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="E5th_Right",
        lat=35.2295,
        lon=-80.8325,
        instruction="Turn right onto E 5th St",
        segment_type="turn_right",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="E5th_East",
        lat=35.2295,
        lon=-80.8380,
        instruction="Continue east on E 5th St",
        segment_type="straight",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="Caldwell_Right",
        lat=35.2295,
        lon=-80.8400,
        instruction="Turn right onto N Caldwell St",
        segment_type="turn_right",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="Caldwell_South",
        lat=35.2275,
        lon=-80.8400,
        instruction="Continue south on N Caldwell St",
        segment_type="straight",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="Trade_Right",
        lat=35.2260,
        lon=-80.8400,
        instruction="Turn right onto E Trade St",
        segment_type="turn_right",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="Trade_West",
        lat=35.2260,
        lon=-80.8430,
        instruction="Continue west on E Trade St",
        segment_type="straight",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="Church_Left",
        lat=35.2260,
        lon=-80.8455,
        instruction="Turn left onto S Church St",
        segment_type="turn_left",
        speed_limit_kmh=35,
    ),
    Waypoint(
        name="Finish_Line",
        lat=35.2235,
        lon=-80.8455,
        instruction="Finish - Complete the loop!",
        segment_type="straight",
        speed_limit_kmh=35,
        is_checkpoint=True,
    ),
]


# =============================================================================
# PATH HIGHLIGHT SYSTEM
# =============================================================================

class PathHighlightType(Enum):
    """Types of path highlights."""
    ARROW = "arrow"           # Directional arrows on road
    CHEVRON = "chevron"       // Chevron markers
    LINE = "line"             # Glowing line along path
    GLOW = "glow"             # Ground glow effect
    CHECKPOINT = "checkpoint" # Checkpoint gate


@dataclass
class PathHighlightConfig:
    """Configuration for path highlighting."""
    highlight_type: PathHighlightType = PathHighlightType.ARROW
    color: Tuple[float, float, float, float] = (1.0, 0.8, 0.0, 1.0)  # Yellow
    emissive_strength: float = 2.0
    spacing: float = 15.0  # meters between markers
    size: float = 2.0      # marker size
    visible_distance: float = 100.0  # meters


def create_path_highlight_material(
    name: str = "PathHighlight",
    color: Tuple[float, float, float, float] = (1.0, 0.8, 0.0, 1.0),
    emissive_strength: float = 2.0
) -> Optional[Any]:
    """Create emissive material for path highlights."""
    if not BLENDER_AVAILABLE:
        return None

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)

    # Set emissive properties
    principled.inputs['Base Color'].default_value = color
    principled.inputs['Emission Color'].default_value = color
    principled.inputs['Emission Strength'].default_value = emissive_strength
    principled.inputs['Roughness'].default_value = 0.3

    # Link nodes
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # Set blend mode for transparency
    mat.blend_method = 'BLEND'
    mat.shadow_method = 'CLIP'

    return mat


def create_arrow_marker(
    location: Tuple[float, float, float],
    rotation: float,
    size: float = 2.0,
    name: str = "PathArrow"
) -> Optional[Any]:
    """Create a directional arrow marker for path guidance."""
    if not BLENDER_AVAILABLE:
        return None

    # Create arrow mesh (simple triangle with tail)
    mesh = bpy.data.meshes.new(f"{name}_mesh")

    # Arrow vertices (pointing in +Y direction)
    half_width = size * 0.4
    length = size
    tail_length = size * 0.5

    verts = [
        (0, length * 0.5, 0.05),           # Tip
        (-half_width, -length * 0.3, 0.05),  # Left corner
        (-half_width * 0.3, -length * 0.3, 0.05),  # Left inner
        (-half_width * 0.3, -length * 0.3 - tail_length, 0.05),  # Left tail
        (half_width * 0.3, -length * 0.3 - tail_length, 0.05),   # Right tail
        (half_width * 0.3, -length * 0.3, 0.05),   # Right inner
        (half_width, -length * 0.3, 0.05),   # Right corner
    ]

    faces = [
        (0, 1, 2, 3, 4, 5, 6),
    ]

    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler[2] = rotation

    return obj


def create_checkpoint_gate(
    location: Tuple[float, float, float],
    rotation: float,
    width: float = 10.0,
    height: float = 5.0,
    name: str = "Checkpoint"
) -> Optional[Any]:
    """Create a checkpoint gate structure."""
    if not BLENDER_AVAILABLE:
        return None

    # Create parent empty
    gate_root = bpy.data.objects.new(f"{name}_Root", None)
    gate_root.empty_display_type = 'PLAIN_AXES'
    gate_root.location = location
    gate_root.rotation_euler[2] = rotation

    # Left pillar
    pillar_size = 0.3
    left_pillar = bpy.data.meshes.new(f"{name}_LeftPillar")
    left_pillar.from_pydata([
        (-width/2, 0, 0),
        (-width/2 + pillar_size, 0, 0),
        (-width/2 + pillar_size, pillar_size, 0),
        (-width/2, pillar_size, 0),
        (-width/2, 0, height),
        (-width/2 + pillar_size, 0, height),
        (-width/2 + pillar_size, pillar_size, height),
        (-width/2, pillar_size, height),
    ], [], [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (0, 3, 7, 4),
        (1, 2, 6, 5),
    ])
    left_pillar_obj = bpy.data.objects.new(f"{name}_LeftPillar", left_pillar)
    left_pillar_obj.parent = gate_root

    # Right pillar
    right_pillar = bpy.data.meshes.new(f"{name}_RightPillar")
    right_pillar.from_pydata([
        (width/2 - pillar_size, 0, 0),
        (width/2, 0, 0),
        (width/2, pillar_size, 0),
        (width/2 - pillar_size, pillar_size, 0),
        (width/2 - pillar_size, 0, height),
        (width/2, 0, height),
        (width/2, pillar_size, height),
        (width/2 - pillar_size, pillar_size, height),
    ], [], [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (0, 3, 7, 4),
        (1, 2, 6, 5),
    ])
    right_pillar_obj = bpy.data.objects.new(f"{name}_RightPillar", right_pillar)
    right_pillar_obj.parent = gate_root

    # Top bar
    top_bar = bpy.data.meshes.new(f"{name}_TopBar")
    top_bar.from_pydata([
        (-width/2, 0, height - pillar_size),
        (width/2, 0, height - pillar_size),
        (width/2, pillar_size, height - pillar_size),
        (-width/2, pillar_size, height - pillar_size),
        (-width/2, 0, height),
        (width/2, 0, height),
        (width/2, pillar_size, height),
        (-width/2, pillar_size, height),
    ], [], [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (0, 3, 7, 4),
        (1, 2, 6, 5),
    ])
    top_bar_obj = bpy.data.objects.new(f"{name}_TopBar", top_bar)
    top_bar_obj.parent = gate_root

    return gate_root


# =============================================================================
# DRIVER CAMERA SYSTEM
# =============================================================================

def create_driver_camera_rig(
    vehicle_spec: VehicleDimensions,
    name: str = "DriverCamera"
) -> Optional[Any]:
    """
    Create a camera rig positioned at driver eye height.

    Args:
        vehicle_spec: Vehicle dimensions for proper positioning
        name: Name for the camera rig

    Returns:
        Camera object
    """
    if not BLENDER_AVAILABLE:
        return None

    # Create camera
    cam_data = bpy.data.cameras.new(f"{name}_Data")
    cam_obj = bpy.data.objects.new(name, cam_data)

    # Position camera at driver eye height
    # Standard driving camera setup:
    # - Behind front axle slightly
    # - At driver eye height
    # - Looking forward and slightly down

    cam_obj.location = (
        0.0,  # Center of vehicle
        vehicle_spec.wheelbase * 0.3,  # Slightly behind front
        vehicle_spec.driver_eye_height,
    )

    # Camera settings for realistic driving view
    cam_data.lens = 28  # Wide angle for peripheral vision
    cam_data.sensor_width = 36
    cam_data.sensor_fit = 'HORIZONTAL'

    # Field of view for driving (slightly wide)
    cam_data.angle = math.radians(75)

    # Clip distances
    cam_data.clip_start = 0.1
    cam_data.clip_end = 2000.0

    # Store metadata
    cam_obj["camera_type"] = "driver_view"
    cam_obj["vehicle_type"] = vehicle_spec.name
    cam_obj["eye_height"] = vehicle_spec.driver_eye_height

    return cam_obj


def create_third_person_camera_rig(
    vehicle_spec: VehicleDimensions,
    distance: float = 8.0,
    height: float = 3.5,
    name: str = "ThirdPersonCamera"
) -> Optional[Any]:
    """Create a third-person follow camera."""
    if not BLENDER_AVAILABLE:
        return None

    cam_data = bpy.data.cameras.new(f"{name}_Data")
    cam_obj = bpy.data.objects.new(name, cam_data)

    # Position behind and above vehicle
    cam_obj.location = (
        0.0,
        -distance,  # Behind vehicle
        height,
    )

    # Camera settings
    cam_data.lens = 50
    cam_data.angle = math.radians(60)
    cam_data.clip_start = 0.5
    cam_data.clip_end = 3000.0

    cam_obj["camera_type"] = "third_person"
    cam_obj["follow_distance"] = distance
    cam_obj["follow_height"] = height

    return cam_obj


# =============================================================================
# RACE LOOP MANAGER
# =============================================================================

class RaceLoopManager:
    """
    Manages the complete race loop including:
    - Waypoint tracking with elevation
    - Path highlighting
    - Vehicle spawning
    - Camera setup

    Elevation data from enhanced system shows 10.5m variation across the loop.
    """

    REF_LAT = 35.226
    REF_LON = -80.843
    BASE_ELEVATION = 220.0  # Base elevation for relative Z coordinates

    def __init__(self, waypoints: List[Waypoint] = None):
        self.waypoints = waypoints or RACE_LOOP_WAYPOINTS
        self.path_objects = []
        self.checkpoints = []
        self.vehicle = None
        self.camera_rig = None

        # Initialize elevation manager
        self.elevation_manager = None
        if ELEVATION_AVAILABLE:
            try:
                self.elevation_manager = create_enhanced_elevation_manager()
                # Populate waypoints with elevation data
                self._populate_elevations()
            except Exception as e:
                print(f"Warning: Could not load elevation manager: {e}")

    def _populate_elevations(self):
        """Populate waypoints with elevation data from enhanced system."""
        if not self.elevation_manager:
            return

        prev_x, prev_y, prev_z = None, None, None

        for wp in self.waypoints:
            # Get elevation for this waypoint
            wp.elevation = self.elevation_manager.get_elevation(wp.lat, wp.lon)

            # Calculate grade from previous
            if prev_x is not None:
                x, y = self.latlon_to_local(wp.lat, wp.lon)
                dx = x - prev_x
                dy = y - prev_y
                horizontal_dist = math.sqrt(dx*dx + dy*dy)

                if horizontal_dist > 0:
                    dz = wp.elevation - prev_z
                    wp.grade_percent = (dz / horizontal_dist) * 100

            prev_x, prev_y = self.latlon_to_local(wp.lat, wp.lon)
            prev_z = wp.elevation

    def latlon_to_local(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert lat/lon to local scene coordinates."""
        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(self.REF_LAT))

        x = (lon - self.REF_LON) * meters_per_deg_lon
        y = (lat - self.REF_LAT) * meters_per_deg_lat

        return (x, y)

    def get_elevation_z(self, lat: float, lon: float) -> float:
        """Get Z coordinate for a lat/lon (relative to base elevation)."""
        if self.elevation_manager:
            elevation = self.elevation_manager.get_elevation(lat, lon)
            # Return relative elevation (makes hills visible)
            return elevation - self.BASE_ELEVATION
        return 0.0

    def create_path_curve(self, name: str = "RaceLoopPath", use_elevation: bool = True) -> Optional[Any]:
        """
        Create a curve following the race loop waypoints.

        Args:
            name: Curve object name
            use_elevation: If True, include elevation data in curve
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create curve
        curve_data = bpy.data.curves.new(name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 4

        spline = curve_data.splines.new('BEZIER')

        # Add waypoints
        spline.bezier_points.add(len(self.waypoints) - 1)

        for i, wp in enumerate(self.waypoints):
            x, y = self.latlon_to_local(wp.lat, wp.lon)

            # Use elevation from waypoint data or calculate
            if use_elevation and wp.elevation > 0:
                z = wp.elevation - self.BASE_ELEVATION
            elif use_elevation:
                z = self.get_elevation_z(wp.lat, wp.lon)
            else:
                z = 0.5  # Flat

            point = spline.bezier_points[i]
            point.co = (x, y, z)
            point.handle_type_left = 'AUTO'
            point.handle_type_right = 'AUTO'

        curve_obj = bpy.data.objects.new(name, curve_data)

        # Store metadata
        curve_obj["path_type"] = "race_loop"
        curve_obj["total_waypoints"] = len(self.waypoints)
        curve_obj["has_elevation"] = use_elevation
        curve_obj["base_elevation"] = self.BASE_ELEVATION

        # Store elevation range
        if self.waypoints:
            elevations = [wp.elevation for wp in self.waypoints if wp.elevation > 0]
            if elevations:
                curve_obj["elevation_min"] = min(elevations)
                curve_obj["elevation_max"] = max(elevations)
                curve_obj["elevation_range"] = max(elevations) - min(elevations)

        return curve_obj

    def create_path_highlights(
        self,
        config: PathHighlightConfig = None
    ) -> List[Any]:
        """Create visual path markers along the route."""
        if not BLENDER_AVAILABLE:
            return []

        if config is None:
            config = PathHighlightConfig()

        highlights = []

        # Create highlight material
        mat = create_path_highlight_material(
            "RacePathHighlight",
            config.color,
            config.emissive_strength
        )

        for i, wp in enumerate(self.waypoints):
            x, y = self.latlon_to_local(wp.lat, wp.lon)
            z = 0.1  # On ground

            # Calculate rotation to next waypoint
            if i < len(self.waypoints) - 1:
                next_wp = self.waypoints[i + 1]
                next_x, next_y = self.latlon_to_local(next_wp.lat, next_wp.lon)
                rotation = math.atan2(next_y - y, next_x - x)
            else:
                # Point back to start
                first_wp = self.waypoints[0]
                first_x, first_y = self.latlon_to_local(first_wp.lat, first_wp.lon)
                rotation = math.atan2(first_y - y, first_x - x)

            # Create appropriate marker
            if wp.is_checkpoint:
                marker = create_checkpoint_gate(
                    (x, y, z),
                    rotation,
                    name=f"Checkpoint_{i}"
                )
            else:
                marker = create_arrow_marker(
                    (x, y, z),
                    rotation,
                    size=config.size,
                    name=f"PathArrow_{i}"
                )

            if marker:
                # Apply material
                if hasattr(marker, 'data') and hasattr(marker.data, 'materials'):
                    marker.data.materials.append(mat)
                elif marker.type == 'EMPTY':
                    for child in marker.children:
                        if hasattr(child, 'data') and hasattr(child.data, 'materials'):
                            child.data.materials.append(mat)

                highlights.append(marker)

                # Store metadata
                marker["waypoint_name"] = wp.name
                marker["instruction"] = wp.instruction
                marker["segment_type"] = wp.segment_type
                marker["speed_limit"] = wp.speed_limit_kmh
                marker["is_checkpoint"] = wp.is_checkpoint

        self.path_objects = highlights
        return highlights

    def spawn_vehicle(
        self,
        vehicle_type: str = 'sedan_midsize',
        at_start: bool = True
    ) -> Optional[Any]:
        """
        Spawn player vehicle at start line with proper elevation.

        Args:
            vehicle_type: Key from VEHICLE_SPECS
            at_start: If True, spawn at start waypoint

        Returns:
            Vehicle root object
        """
        if not BLENDER_AVAILABLE:
            return None

        spec = VEHICLE_SPECS.get(vehicle_type, VEHICLE_SPECS['sedan_midsize'])

        # Create vehicle root
        vehicle_root = bpy.data.objects.new(f"PlayerVehicle_{spec.name}", None)
        vehicle_root.empty_display_type = 'PLAIN_AXES'

        # Position at start
        if at_start and self.waypoints:
            start_wp = self.waypoints[0]
            x, y = self.latlon_to_local(start_wp.lat, start_wp.lon)

            # Use elevation from waypoint or calculate
            if start_wp.elevation > 0:
                z = start_wp.elevation - self.BASE_ELEVATION
            else:
                z = self.get_elevation_z(start_wp.lat, start_wp.lon)

            vehicle_root.location = (x, y, z)

            # Face next waypoint
            if len(self.waypoints) > 1:
                next_wp = self.waypoints[1]
                next_x, next_y = self.latlon_to_local(next_wp.lat, next_wp.lon)
                rotation = math.atan2(next_y - y, next_x - x)
                vehicle_root.rotation_euler[2] = rotation

        # Store vehicle spec
        vehicle_root["vehicle_type"] = vehicle_type
        vehicle_root["vehicle_length"] = spec.length
        vehicle_root["vehicle_width"] = spec.width
        vehicle_root["vehicle_height"] = spec.height
        vehicle_root["driver_eye_height"] = spec.driver_eye_height
        vehicle_root["is_player_vehicle"] = True

        # Store elevation info
        if self.waypoints and self.waypoints[0].elevation > 0:
            vehicle_root["spawn_elevation"] = self.waypoints[0].elevation
            vehicle_root["base_elevation"] = self.BASE_ELEVATION

        # Create driver camera
        self.camera_rig = create_driver_camera_rig(spec, "DriverCamera")
        if self.camera_rig:
            self.camera_rig.parent = vehicle_root

        # Create collision proxy (simplified box)
        collision_box = bpy.data.meshes.new("VehicleCollision")
        hw = spec.width / 2
        hl = spec.length / 2
        hh = spec.height / 2

        collision_box.from_pydata([
            (-hw, -hl, 0),
            (hw, -hl, 0),
            (hw, hl, 0),
            (-hw, hl, 0),
            (-hw, -hl, spec.height),
            (hw, -hl, spec.height),
            (hw, hl, spec.height),
            (-hw, hl, spec.height),
        ], [], [
            (0, 1, 2, 3), (4, 5, 6, 7),
            (0, 1, 5, 4), (2, 3, 7, 6),
            (0, 3, 7, 4), (1, 2, 6, 5),
        ])

        collision_obj = bpy.data.objects.new("VehicleCollision", collision_box)
        collision_obj.parent = vehicle_root
        collision_obj.display_type = 'WIRE'
        collision_obj.hide_render = True
        collision_obj["is_collision_proxy"] = True
        collision_obj["collision_type"] = "box"

        self.vehicle = vehicle_root
        return vehicle_root

    def setup_scene(self) -> Dict[str, Any]:
        """
        Complete scene setup for race loop.

        Returns:
            Stats dict
        """
        if not BLENDER_AVAILABLE:
            return {}

        stats = {
            'waypoints': len(self.waypoints),
            'path_highlights': 0,
            'checkpoints': 0,
            'vehicle_spawned': False,
            'camera_created': False,
        }

        # Create collection
        if "RaceLoop" not in bpy.data.collections:
            coll = bpy.data.collections.new("RaceLoop")
            bpy.context.scene.collection.children.link(coll)
        else:
            coll = bpy.data.collections["RaceLoop"]

        # Create path curve
        path_curve = self.create_path_curve()
        if path_curve:
            bpy.context.collection.objects.link(path_curve)
            coll.objects.link(path_curve)

        # Create path highlights
        highlights = self.create_path_highlights()
        for h in highlights:
            bpy.context.collection.objects.link(h)
            coll.objects.link(h)
            stats['path_highlights'] += 1
            if h.get('is_checkpoint'):
                stats['checkpoints'] += 1

        # Spawn vehicle
        vehicle = self.spawn_vehicle()
        if vehicle:
            bpy.context.collection.objects.link(vehicle)
            coll.objects.link(vehicle)
            stats['vehicle_spawned'] = True

            # Link camera and collision
            if self.camera_rig:
                bpy.context.collection.objects.link(self.camera_rig)
                stats['camera_created'] = True

            for child in vehicle.children:
                bpy.context.collection.objects.link(child)

        # Set scene camera
        if self.camera_rig:
            bpy.context.scene.camera = self.camera_rig

        return stats


# =============================================================================
# MAIN
# =============================================================================

def create_race_loop() -> RaceLoopManager:
    """Create and setup the Charlotte race loop."""
    manager = RaceLoopManager(RACE_LOOP_WAYPOINTS)

    if BLENDER_AVAILABLE:
        stats = manager.setup_scene()
        print(f"\nRace Loop Created:")
        print(f"  Waypoints: {stats['waypoints']}")
        print(f"  Path markers: {stats['path_highlights']}")
        print(f"  Checkpoints: {stats['checkpoints']}")
        print(f"  Vehicle: {stats['vehicle_spawned']}")
        print(f"  Camera: {stats['camera_created']}")

    return manager


if __name__ == '__main__':
    create_race_loop()
