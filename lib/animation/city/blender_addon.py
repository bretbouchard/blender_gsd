"""
Blender Operators and UI for City Chase System

Provides menu access and panels for the city system in Blender.

Install as addon:
1. Edit → Preferences → Add-ons → Install
2. Select this file or the city_chase folder
3. Enable "City Chase System"

Usage:
    After installation, access via:
    - 3D Viewport → Sidebar (N) → City Chase tab
    - Object → City Chase menu
    - Shift+A → City Chase (add menu)
"""

from __future__ import annotations
import bpy
from bpy.types import (
    Operator, Panel, PropertyGroup,
    UIList, Menu, GizmoGroup
)
from bpy.props import (
    StringProperty, IntProperty, FloatProperty,
    BoolProperty, EnumProperty, PointerProperty,
    FloatVectorProperty, CollectionProperty
)
from bpy.app.handlers import persistent
from typing import Optional, Dict, List, Any
import math
import random

# Try to import city system
try:
    from lib.animation.city import (
        CityBuilder, CityConfig, BUILDER_PRESETS,
        TrafficController, VehicleAgent,
        ChaseDirector, ChaseCameraSystem
    )
    CITY_SYSTEM_AVAILABLE = True
except ImportError:
    CITY_SYSTEM_AVAILABLE = False


# ============================================================================
# PROPERTY GROUPS
# ============================================================================

class CityChaseSettings(PropertyGroup):
    """Settings for city chase generation."""

    # Preset
    preset: EnumProperty(
        name="Preset",
        description="City preset configuration",
        items=[
            ('test_city', "Test City", "Small test scene (3x3 grid, 10 buildings)"),
            ('charlotte_uptown', "Charlotte Uptown", "Charlotte NC downtown chase"),
            ('hollywood_chase', "Hollywood Chase", "Action movie style chase"),
            ('custom', "Custom", "Use custom settings below"),
        ],
        default='test_city'
    )

    # Roads
    grid_size: IntProperty(
        name="Grid Size",
        description="Number of city blocks",
        min=2, max=20,
        default=5
    )
    block_size: FloatProperty(
        name="Block Size",
        description="Size of each block in meters",
        min=50, max=500,
        default=100
    )
    road_lanes: IntProperty(
        name="Lanes",
        description="Number of lanes per road",
        min=1, max=6,
        default=2
    )

    # Buildings
    building_count: IntProperty(
        name="Buildings",
        description="Number of buildings to generate",
        min=0, max=200,
        default=30
    )
    building_height_min: FloatProperty(
        name="Min Height",
        description="Minimum building height",
        min=10, max=100,
        default=30
    )
    building_height_max: FloatProperty(
        name="Max Height",
        description="Maximum building height",
        min=20, max=500,
        default=150
    )

    # Traffic
    traffic_count: IntProperty(
        name="Traffic Vehicles",
        description="Number of traffic vehicles",
        min=0, max=200,
        default=20
    )
    traffic_speed: FloatProperty(
        name="Traffic Speed",
        description="Traffic speed in km/h",
        min=10, max=100,
        default=40
    )

    # Chase
    chase_enabled: BoolProperty(
        name="Enable Chase",
        description="Add chase sequence",
        default=True
    )
    hero_color: FloatVectorProperty(
        name="Hero Color",
        description="Hero car color",
        subtype='COLOR',
        size=3,
        min=0, max=1,
        default=(0.9, 0.1, 0.1)
    )
    pursuit_count: IntProperty(
        name="Pursuit Cars",
        description="Number of pursuit vehicles",
        min=0, max=10,
        default=3
    )
    chase_duration: FloatProperty(
        name="Duration",
        description="Chase duration in seconds",
        min=5, max=120,
        default=30
    )
    crash_points: IntProperty(
        name="Crash Points",
        description="Number of scripted crash points",
        min=0, max=10,
        default=2
    )

    # Cameras
    camera_follow: BoolProperty(
        name="Follow Camera",
        default=True
    )
    camera_aerial: BoolProperty(
        name="Aerial Camera",
        default=True
    )
    camera_in_car: BoolProperty(
        name="In-Car Camera",
        default=False
    )
    camera_static: BoolProperty(
        name="Static Cameras",
        default=False
    )
    camera_auto_switch: BoolProperty(
        name="Auto Switch",
        description="Automatically switch between cameras",
        default=True
    )
    camera_switch_interval: FloatProperty(
        name="Switch Interval",
        description="Seconds between camera switches",
        min=1, max=30,
        default=3
    )

    # Animation
    fps: IntProperty(
        name="FPS",
        min=12, max=60,
        default=24
    )

    # Runtime state
    traffic_controller: PointerProperty(type=bpy.types.Object)
    chase_director: PointerProperty(type=bpy.types.Object)
    camera_system: PointerProperty(type=bpy.types.Object)


class CrashPointItem(PropertyGroup):
    """Single crash point configuration."""
    progress: FloatProperty(
        name="Progress",
        description="Position along chase path (0-1)",
        min=0, max=1,
        default=0.5
    )
    intensity: FloatProperty(
        name="Intensity",
        description="Crash intensity (0-1)",
        min=0, max=1,
        default=0.5
    )
    crash_type: EnumProperty(
        name="Type",
        items=[
            ('collision', "Collision", "Vehicle collision"),
            ('rollover', "Rollover", "Vehicle rollover"),
            ('spin', "Spin Out", "Spin out"),
            ('jump', "Jump", "Vehicle jump"),
        ],
        default='collision'
    )


# ============================================================================
# OPERATORS
# ============================================================================

class CITY_CHASE_OT_create_city(Operator):
    """Create a complete city chase scene"""
    bl_idname = "city_chase.create_city"
    bl_label = "Create City"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.city_chase_settings

        # Get preset or custom config
        if settings.preset != 'custom' and settings.preset in BUILDER_PRESETS:
            builder = CityBuilder.from_preset(settings.preset)
            config = builder.config
        else:
            builder = CityBuilder("Custom_City")
            config = builder.config

        # Apply custom settings if needed
        if settings.preset == 'custom':
            config.road_grid_size = settings.grid_size
            config.road_block_size = settings.block_size
            config.road_lanes = settings.road_lanes
            config.building_count = settings.building_count
            config.building_height_min = settings.building_height_min
            config.building_height_max = settings.building_height_max
            config.traffic_count = settings.traffic_count
            config.chase_enabled = settings.chase_enabled
            config.pursuit_count = settings.pursuit_count
            config.chase_duration = settings.chase_duration

        # Camera types
        camera_types = []
        if settings.camera_follow:
            camera_types.append("follow")
        if settings.camera_aerial:
            camera_types.append("aerial")
        if settings.camera_in_car:
            camera_types.append("in_car")
        if settings.camera_static:
            camera_types.append("static")
        config.camera_types = camera_types if camera_types else ["follow"]
        config.camera_auto_switch = settings.camera_auto_switch

        # Build
        try:
            builder.build()

            # Store references for runtime systems
            settings['builder_name'] = builder.config.name

            self.report({'INFO'}, f"Created city: {len(builder.buildings)} buildings, "
                                  f"{len(builder.traffic)} vehicles, "
                                  f"{len(builder.cameras)} cameras")

        except Exception as e:
            self.report({'ERROR'}, f"Failed to create city: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


class CITY_CHASE_OT_start_traffic(Operator):
    """Start traffic simulation"""
    bl_idname = "city_chase.start_traffic"
    bl_label = "Start Traffic"
    bl_options = {'REGISTER'}

    def execute(self, context):
        settings = context.scene.city_chase_settings

        # Enable frame handler
        context.scene.city_chase_traffic_enabled = True

        self.report({'INFO'}, "Traffic simulation started")
        return {'FINISHED'}


class CITY_CHASE_OT_stop_traffic(Operator):
    """Stop traffic simulation"""
    bl_idname = "city_chase.stop_traffic"
    bl_label = "Stop Traffic"
    bl_options = {'REGISTER'}

    def execute(self, context):
        context.scene.city_chase_traffic_enabled = False
        self.report({'INFO'}, "Traffic simulation stopped")
        return {'FINISHED'}


class CITY_CHASE_OT_start_camera_switching(Operator):
    """Start automatic camera switching"""
    bl_idname = "city_chase.start_camera_switching"
    bl_label = "Start Camera Switching"
    bl_options = {'REGISTER'}

    def execute(self, context):
        context.scene.city_chase_camera_switching = True
        self.report({'INFO'}, "Camera auto-switching started")
        return {'FINISHED'}


class CITY_CHASE_OT_stop_camera_switching(Operator):
    """Stop automatic camera switching"""
    bl_idname = "city_chase.stop_camera_switching"
    bl_label = "Stop Camera Switching"
    bl_options = {'REGISTER'}

    def execute(self, context):
        context.scene.city_chase_camera_switching = False
        self.report({'INFO'}, "Camera auto-switching stopped")
        return {'FINISHED'}


class CITY_CHASE_OT_next_camera(Operator):
    """Switch to next camera"""
    bl_idname = "city_chase.next_camera"
    bl_label = "Next Camera"
    bl_options = {'REGISTER'}

    def execute(self, context):
        cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
        if len(cameras) < 2:
            self.report({'WARNING'}, "Not enough cameras")
            return {'CANCELLED'}

        current = context.scene.camera
        if current in cameras:
            idx = cameras.index(current)
            next_idx = (idx + 1) % len(cameras)
        else:
            next_idx = 0

        context.scene.camera = cameras[next_idx]
        self.report({'INFO'}, f"Switched to: {cameras[next_idx].name}")
        return {'FINISHED'}


class CITY_CHASE_OT_clear_city(Operator):
    """Clear all city objects"""
    bl_idname = "city_chase.clear_city"
    bl_label = "Clear City"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Check if any city collections exist
        for col in bpy.data.collections:
            if any(name in col.name for name in ['City', 'Roads', 'Buildings', 'Traffic', 'Chase']):
                return True
        return False

    def execute(self, context):
        # Remove city collections and objects
        collections_to_remove = []
        for col in bpy.data.collections:
            if any(name in col.name.lower() for name in ['city', 'roads', 'buildings', 'traffic', 'hero', 'pursuit']):
                # Remove objects in collection
                for obj in col.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                collections_to_remove.append(col)

        for col in collections_to_remove:
            bpy.data.collections.remove(col, do_unlink=True)

        self.report({'INFO'}, "City cleared")
        return {'FINISHED'}


class CITY_CHASE_OT_import_osm(Operator):
    """Import OpenStreetMap data for location"""
    bl_idname = "city_chase.import_osm"
    bl_label = "Import OSM Data"
    bl_options = {'REGISTER', 'UNDO'}

    location: StringProperty(
        name="Location",
        description="Location to import (e.g., 'Charlotte, NC')",
        default="Charlotte, NC"
    )

    def execute(self, context):
        try:
            from lib.animation.city import GeoDataBridge, geocode_location

            # Geocode location
            geo_loc = geocode_location(self.location)
            if not geo_loc:
                self.report({'ERROR'}, f"Could not find location: {self.location}")
                return {'CANCELLED'}

            # Create bridge and import
            bridge = GeoDataBridge(origin=geo_loc)

            # Create 1km bounding box around location
            delta = 0.005  # ~500m
            osm_data = bridge.import_area(
                south=geo_loc.latitude - delta,
                west=geo_loc.longitude - delta,
                north=geo_loc.latitude + delta,
                east=geo_loc.longitude + delta
            )

            # Create Blender scene
            bridge.create_blender_scene(osm_data)

            self.report({'INFO'}, f"Imported {osm_data.building_count} buildings, "
                                  f"{osm_data.road_count} roads from {self.location}")

        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class CITY_CHASE_OT_add_crash_point(Operator):
    """Add a crash point to the list"""
    bl_idname = "city_chase.add_crash_point"
    bl_label = "Add Crash Point"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.city_chase_settings
        item = settings.crash_points_list.add()
        item.progress = 0.5
        item.intensity = 0.5
        settings.crash_points_list_index = len(settings.crash_points_list) - 1
        return {'FINISHED'}


class CITY_CHASE_OT_remove_crash_point(Operator):
    """Remove selected crash point"""
    bl_idname = "city_chase.remove_crash_point"
    bl_label = "Remove Crash Point"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.city_chase_settings
        index = settings.crash_points_list_index
        if index >= 0 and index < len(settings.crash_points_list):
            settings.crash_points_list.remove(index)
            settings.crash_points_list_index = min(index, len(settings.crash_points_list) - 1)
        return {'FINISHED'}


# ============================================================================
# PANELS
# ============================================================================

class CITY_CHASE_PT_main(Panel):
    """Main city chase panel"""
    bl_label = "City Chase"
    bl_idname = "CITY_CHASE_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'City Chase'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.city_chase_settings

        # Preset selection
        layout.prop(settings, "preset")

        # Create button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("city_chase.create_city", icon='PLUS')

        # Clear button
        layout.operator("city_chase.clear_city", icon='X')

        layout.separator()


class CITY_CHASE_PT_roads(Panel):
    """Road settings panel"""
    bl_label = "Roads"
    bl_idname = "CITY_CHASE_PT_roads"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'City Chase'
    bl_parent_id = 'CITY_CHASE_PT_main'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.city_chase_settings

        layout.prop(settings, "grid_size")
        layout.prop(settings, "block_size")
        layout.prop(settings, "road_lanes")


class CITY_CHASE_PT_buildings(Panel):
    """Building settings panel"""
    bl_label = "Buildings"
    bl_idname = "CITY_CHASE_PT_buildings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'City Chase'
    bl_parent_id = 'CITY_CHASE_PT_main'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.city_chase_settings

        layout.prop(settings, "building_count")
        row = layout.row()
        row.prop(settings, "building_height_min")
        row.prop(settings, "building_height_max")


class CITY_CHASE_PT_traffic(Panel):
    """Traffic settings panel"""
    bl_label = "Traffic"
    bl_idname = "CITY_CHASE_PT_traffic"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'City Chase'
    bl_parent_id = 'CITY_CHASE_PT_main'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.city_chase_settings

        layout.prop(settings, "traffic_count")
        layout.prop(settings, "traffic_speed")

        # Traffic controls
        row = layout.row()
        if context.scene.city_chase_traffic_enabled:
            row.operator("city_chase.stop_traffic", icon='PAUSE')
        else:
            row.operator("city_chase.start_traffic", icon='PLAY')


class CITY_CHASE_PT_chase(Panel):
    """Chase settings panel"""
    bl_label = "Chase"
    bl_idname = "CITY_CHASE_PT_chase"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'City Chase'
    bl_parent_id = 'CITY_CHASE_PT_main'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.city_chase_settings

        layout.prop(settings, "chase_enabled")

        if settings.chase_enabled:
            layout.prop(settings, "hero_color")
            layout.prop(settings, "pursuit_count")
            layout.prop(settings, "chase_duration")
            layout.prop(settings, "crash_points")


class CITY_CHASE_PT_cameras(Panel):
    """Camera settings panel"""
    bl_label = "Cameras"
    bl_idname = "CITY_CHASE_PT_cameras"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'City Chase'
    bl_parent_id = 'CITY_CHASE_PT_main'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.city_chase_settings

        col = layout.column()
        col.prop(settings, "camera_follow")
        col.prop(settings, "camera_aerial")
        col.prop(settings, "camera_in_car")
        col.prop(settings, "camera_static")

        layout.separator()
        layout.prop(settings, "camera_auto_switch")

        if settings.camera_auto_switch:
            layout.prop(settings, "camera_switch_interval")

        # Camera controls
        row = layout.row()
        if context.scene.city_chase_camera_switching:
            row.operator("city_chase.stop_camera_switching", icon='PAUSE')
        else:
            row.operator("city_chase.start_camera_switching", icon='PLAY')

        row = layout.row()
        row.operator("city_chase.next_camera", icon='CAMERA_DATA')


class CITY_CHASE_PT_tools(Panel):
    """Tools panel"""
    bl_label = "Tools"
    bl_idname = "CITY_CHASE_PT_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'City Chase'

    def draw(self, context):
        layout = self.layout

        layout.operator("city_chase.import_osm", icon='WORLD')

        layout.separator()

        # Status info
        col = layout.column()
        col.label(text="Scene Info:", icon='INFO')
        cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
        col.label(text=f"  Cameras: {len(cameras)}")


# ============================================================================
# MENU
# ============================================================================

class CITY_CHASE_MT_add(Menu):
    """Add menu for city chase"""
    bl_label = "City Chase"
    bl_idname = "CITY_CHASE_MT_add"

    def draw(self, context):
        layout = self.layout
        layout.operator("city_chase.create_city", icon='PLUS')
        layout.operator("city_chase.import_osm", icon='WORLD')


def menu_add_append(self, context):
    """Append to add menu."""
    self.layout.menu("CITY_CHASE_MT_add", icon='SCENE_DATA')


# ============================================================================
# ANIMATION HANDLERS
# ============================================================================

# Scene properties for runtime state
def register_scene_properties():
    bpy.types.Scene.city_chase_traffic_enabled = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.city_chase_camera_switching = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.city_chase_last_camera_switch = bpy.props.IntProperty(default=0)
    bpy.types.Scene.city_chase_current_camera = bpy.props.IntProperty(default=0)


@persistent
def frame_change_handler(scene):
    """Handle per-frame updates for traffic and cameras."""
    if not CITY_SYSTEM_AVAILABLE:
        return

    # Traffic simulation
    if scene.city_chase_traffic_enabled:
        update_traffic(scene)

    # Camera switching
    if scene.city_chase_camera_switching:
        update_camera_switching(scene)


def update_traffic(scene):
    """Update traffic vehicle positions."""
    # Find traffic vehicles
    traffic_col = bpy.data.collections.get("Traffic")
    if not traffic_col:
        return

    vehicles = list(traffic_col.objects)

    for vehicle in vehicles:
        # Simple movement: move forward based on heading
        heading = vehicle.rotation_euler[2]
        speed = 5.0  # meters per frame (adjust based on fps)

        # Move
        vehicle.location.x += math.cos(heading) * speed * 0.1
        vehicle.location.y += math.sin(heading) * speed * 0.1

        # Wrap around (simple bounds check)
        bounds = 500
        if abs(vehicle.location.x) > bounds or abs(vehicle.location.y) > bounds:
            vehicle.location.x = random.uniform(-bounds/2, bounds/2)
            vehicle.location.y = random.uniform(-bounds/2, bounds/2)


def update_camera_switching(scene):
    """Switch active camera based on interval."""
    settings = scene.city_chase_settings
    interval_frames = int(settings.camera_switch_interval * settings.fps)

    # Check if it's time to switch
    frames_since_switch = scene.frame_current - scene.city_chase_last_camera_switch

    if frames_since_switch >= interval_frames:
        # Find all cameras
        cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']

        if len(cameras) > 1:
            # Move to next camera
            scene.city_chase_current_camera = (
                (scene.city_chase_current_camera + 1) % len(cameras)
            )
            scene.camera = cameras[scene.city_chase_current_camera]
            scene.city_chase_last_camera_switch = scene.frame_current


# ============================================================================
# REGISTRATION
# ============================================================================

classes = (
    # Property Groups
    CrashPointItem,
    CityChaseSettings,

    # Operators
    CITY_CHASE_OT_create_city,
    CITY_CHASE_OT_start_traffic,
    CITY_CHASE_OT_stop_traffic,
    CITY_CHASE_OT_start_camera_switching,
    CITY_CHASE_OT_stop_camera_switching,
    CITY_CHASE_OT_next_camera,
    CITY_CHASE_OT_clear_city,
    CITY_CHASE_OT_import_osm,
    CITY_CHASE_OT_add_crash_point,
    CITY_CHASE_OT_remove_crash_point,

    # Panels
    CITY_CHASE_PT_main,
    CITY_CHASE_PT_roads,
    CITY_CHASE_PT_buildings,
    CITY_CHASE_PT_traffic,
    CITY_CHASE_PT_chase,
    CITY_CHASE_PT_cameras,
    CITY_CHASE_PT_tools,

    # Menus
    CITY_CHASE_MT_add,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene properties
    bpy.types.Scene.city_chase_settings = PointerProperty(type=CityChaseSettings)
    register_scene_properties()

    # Add frame handler
    if frame_change_handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(frame_change_handler)

    # Add menu
    bpy.types.VIEW3D_MT_add.append(menu_add_append)


def unregister():
    # Remove menu
    bpy.types.VIEW3D_MT_add.remove(menu_add_append)

    # Remove frame handler
    if frame_change_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(frame_change_handler)

    # Remove scene properties
    del bpy.types.Scene.city_chase_settings
    del bpy.types.Scene.city_chase_traffic_enabled
    del bpy.types.Scene.city_chase_camera_switching
    del bpy.types.Scene.city_chase_last_camera_switch
    del bpy.types.Scene.city_chase_current_camera

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
