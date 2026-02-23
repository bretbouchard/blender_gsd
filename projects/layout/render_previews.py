"""
Render Layout Previews - Professional Product Photography Style.

Studio lighting setup:
- Key light (main illumination)
- Fill light (shadow softening)
- Rim/Back light (edge definition)
- Softbox overhead (diffuse ambient)
- Gradient backdrop

Renders:
1. Single Neve 1073 channel strip
2. 8-channel console
3. 808-style drum machine
4. 1176-style compressor
"""

import bpy
import sys
import pathlib
from math import radians
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout import (
    ElementSize, KNOB_SIZES, BUTTON_SIZES, DEFAULT_GRID,
    ConsoleType, CONSOLE_CONFIGS,
    PanelLayout, ElementSpec, ElementType,
    ChannelStripBuilder, DrumMachineBuilder, CompressorBuilder,
    create_neve_1073_channel, create_808_drum_machine, create_1176_compressor,
    LayoutRenderer, BatchRenderer,
)


# =============================================================================
# STUDIO LIGHTING SETUP
# =============================================================================

class StudioLighting:
    """
    Professional product photography lighting rig.

    Based on 3-point lighting + softbox technique:
    - Key Light: Main illumination, 45° from subject
    - Fill Light: Softer light from opposite side
    - Rim Light: Back light for edge definition
    - Overhead Softbox: Diffuse top light
    """

    def __init__(self, collection: bpy.types.Collection = None):
        self.collection = collection or bpy.context.scene.collection
        self.lights = []

    def setup(self, subject_center=(0, 0, 0), subject_size=0.5, top_z=0.5):
        """Set up the complete lighting rig.

        Args:
            subject_center: Center point of the subject (x, y, z)
            subject_size: Approximate size of subject for light scaling
            top_z: Z coordinate of the TOP of the subject - lights positioned above this
        """
        x, y, z = subject_center
        scale = subject_size

        # Light Z positions - use top_z to ensure lights are ABOVE the subject
        # The subject's knobs extend UP from the panel surface
        light_height = max(top_z + 0.15, 0.3)  # At least 150mm above top, minimum 300mm

        # Key Light - Main illumination (warm, from front-right-above)
        # Position at POSITIVE Y (in front of panel where camera is)
        key = self._create_light(
            name="KeyLight",
            light_type='AREA',
            location=(x + 2*scale, y + 2*scale, light_height),
            rotation=(radians(50), 0, radians(-45)),  # Point toward subject
            energy=2000,
            color=(1.0, 0.95, 0.9),  # Slightly warm
            size=2*scale,
        )
        self.lights.append(key)

        # Fill Light - Shadow softening (cool, from front-left-above)
        fill = self._create_light(
            name="FillLight",
            light_type='AREA',
            location=(x - 2*scale, y + 1.5*scale, light_height - 0.05),
            rotation=(radians(60), 0, radians(30)),  # Point toward subject
            energy=1000,
            color=(0.9, 0.95, 1.0),  # Slightly cool
            size=3*scale,
        )
        self.lights.append(fill)

        # Rim Light - Edge definition (neutral, from behind the panel)
        # Position at NEGATIVE Y (behind panel)
        rim = self._create_light(
            name="RimLight",
            light_type='AREA',
            location=(x, y - 1*scale, light_height - 0.05),
            rotation=(radians(70), 0, 0),  # Point toward front
            energy=1500,
            color=(1.0, 1.0, 1.0),
            size=2*scale,
        )
        self.lights.append(rim)

        # Overhead Softbox - Diffuse top light (directly above)
        overhead = self._create_light(
            name="OverheadSoftbox",
            light_type='AREA',
            location=(x, y, light_height + 0.2),
            rotation=(radians(0), 0, 0),
            energy=800,
            color=(1.0, 1.0, 1.0),
            size=4*scale,
        )
        self.lights.append(overhead)

        return self.lights

    def _create_light(
        self,
        name: str,
        light_type: str,
        location: tuple,
        rotation: tuple,
        energy: float,
        color: tuple,
        size: float,
    ) -> bpy.types.Object:
        """Create a single light."""
        light_data = bpy.data.lights.new(name, type=light_type)
        light_data.energy = energy
        light_data.color = color
        light_data.size = size
        light_data.shadow_soft_size = 0.5

        light_obj = bpy.data.objects.new(name, light_data)
        light_obj.location = location
        light_obj.rotation_euler = rotation

        self.collection.objects.link(light_obj)
        return light_obj


class StudioBackdrop:
    """
    Professional gradient backdrop for product photography.

    Creates a curved sweep backdrop with gradient material.
    """

    def __init__(self, collection: bpy.types.Collection = None):
        self.collection = collection or bpy.context.scene.collection
        self.backdrop = None

    def create(self, width=2.0, height=1.5, depth=1.0, color_top=(0.15, 0.15, 0.15), color_bottom=(0.05, 0.05, 0.05)):
        """Create a curved backdrop sweep."""
        # Create a plane and deform it into a sweep
        bpy.ops.mesh.primitive_plane_add(size=1)
        self.backdrop = bpy.context.active_object
        self.backdrop.name = "Studio_Backdrop"

        # Scale and position
        self.backdrop.scale = (width, depth, 1)
        self.backdrop.location = (0, depth/2, 0)
        self.backdrop.rotation_euler = (radians(-90), 0, 0)

        # Subdivide for smooth bending
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=32)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Bend into sweep shape using proportional editing concept
        # We'll use a simple curved mesh instead
        bpy.ops.object.delete()

        # Create curved sweep manually
        import bmesh
        mesh = bpy.data.meshes.new("Backdrop_Mesh")
        self.backdrop = bpy.data.objects.new("Studio_Backdrop", mesh)

        bm = bmesh.new()

        # Create sweep vertices
        segments = 32
        radius = depth

        for i in range(segments + 1):
            angle = (radians(90) * i / segments)  # 0 to 90 degrees
            y = -radius * (1 - (1 - 0.707) * i / segments)  # Flatten the curve
            z = radius * (1 - (i / segments)) * 0.3  # Curve up

            # Full width row
            for j in range(2):
                x = -width/2 + j * width
                vert = bm.verts.new((x, y, z))

        bm.verts.ensure_lookup_table()

        # Create faces
        for i in range(segments):
            v1 = bm.verts[i * 2]
            v2 = bm.verts[i * 2 + 1]
            v3 = bm.verts[(i + 1) * 2 + 1]
            v4 = bm.verts[(i + 1) * 2]
            bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        self.collection.objects.link(self.backdrop)

        # Create gradient material
        mat = bpy.data.materials.new("Backdrop_Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        nodes.clear()

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        # Principled BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Roughness"].default_value = 0.9
        bsdf.inputs["Metallic"].default_value = 0.0

        # Color ramp for gradient
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.location = (-400, 0)
        ramp.color_ramp.elements[0].color = (*color_bottom, 1)
        ramp.color_ramp.elements[1].color = (*color_top, 1)
        ramp.color_ramp.elements[1].position = 0.7

        # Separate Z coordinate for gradient
        sep = nodes.new("ShaderNodeSeparateXYZ")
        sep.location = (-600, 0)

        # Texture coordinate
        tex = nodes.new("ShaderNodeTexCoord")
        tex.location = (-800, 0)

        # Math to normalize Z
        math = nodes.new("ShaderNodeMath")
        math.location = (-500, 0)
        math.operation = "DIVIDE"
        math.inputs[1].default_value = height

        # Connect
        links.new(tex.outputs["Generated"], sep.inputs["Vector"])
        links.new(sep.outputs["Z"], math.inputs[0])
        links.new(math.outputs["Value"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self.backdrop.data.materials.append(mat)

        return self.backdrop


# =============================================================================
# RENDER SCENE SETUP
# =============================================================================

def setup_render_scene(
    subject_center=(0, 0, 0),
    subject_size=0.3,
    camera_distance=0.6,
    resolution=(1920, 1080),
):
    """Set up complete render scene with lighting and camera."""
    # Clear existing
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'

    # World background
    world = bpy.data.worlds.new("Studio_World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.02, 1)
    bg.inputs["Strength"].default_value = 0.5
    scene.world = world

    # Camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Position camera
    x, y, z = subject_center
    cam_obj.location = (x, y - camera_distance, z + camera_distance * 0.4)
    direction = (x - cam_obj.location.x, y - cam_obj.location.y, z - cam_obj.location.z)
    cam_obj.rotation_euler = (radians(65), 0, 0)

    # Studio lighting
    lighting = StudioLighting()
    lighting.setup(subject_center, subject_size)

    # Backdrop
    backdrop = StudioBackdrop()
    backdrop.create(
        width=subject_size * 6,
        height=subject_size * 3,
        depth=subject_size * 3,
    )

    return cam_obj


# =============================================================================
# SCENE BUILDER FOR EACH PREVIEW
# =============================================================================

def build_channel_strip_scene():
    """Build and position a single channel strip for rendering."""
    # Create layout
    layout = create_neve_1073_channel()

    # Render
    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    # Center the layout
    min_x = min(obj.location.x for obj in objects)
    max_x = max(obj.location.x for obj in objects)
    center_x = (min_x + max_x) / 2

    for obj in objects:
        obj.location.x -= center_x

    return objects


def build_8channel_scene():
    """Build and position 8 channel strips for rendering."""
    layout = create_neve_1073_channel()

    batch = BatchRenderer("8_Channel_Console")
    batch.add_layout_row(layout, count=8)

    objects = batch.render()

    # Center
    min_x = min(obj.location.x for obj in objects)
    max_x = max(obj.location.x for obj in objects)
    center_x = (min_x + max_x) / 2

    for obj in objects:
        obj.location.x -= center_x

    return objects


def build_drum_machine_scene():
    """Build and position drum machine for rendering."""
    layout = create_808_drum_machine()

    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    # Center
    min_x = min(obj.location.x for obj in objects)
    max_x = max(obj.location.x for obj in objects)
    center_x = (min_x + max_x) / 2

    for obj in objects:
        obj.location.x -= center_x

    return objects


def build_compressor_scene():
    """Build and position compressor for rendering."""
    layout = create_1176_compressor()

    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    # Center
    min_x = min(obj.location.x for obj in objects)
    max_x = max(obj.location.x for obj in objects)
    center_x = (min_x + max_x) / 2

    for obj in objects:
        obj.location.x -= center_x

    return objects


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def get_scene_bounds(objects):
    """
    Calculate the actual bounding box of all objects including their geometry.

    This evaluates Geometry Nodes modifiers to get the real mesh bounds,
    not just the object center points. Uses to_mesh() to get the actual
    evaluated geometry, not the bound_box which doesn't account for Geo Nodes.
    """
    # Get a FRESH depsgraph - this is critical for Geometry Nodes evaluation
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()

    all_verts = []

    for obj in objects:
        # Get evaluated object (with Geometry Nodes applied)
        eval_obj = obj.evaluated_get(depsgraph)

        # Get the actual mesh with geometry nodes evaluated
        try:
            mesh = eval_obj.to_mesh()
            if mesh and mesh.vertices:
                # Transform all vertices to world space
                for v in mesh.vertices:
                    world_v = obj.matrix_world @ v.co
                    all_verts.append((world_v.x, world_v.y, world_v.z))
                eval_obj.to_mesh_clear()
        except:
            pass

    if not all_verts:
        return (0, 0, 0), 0.1, 0.1, 0.1, 0.1

    # Get overall bounds
    min_x = min(v[0] for v in all_verts)
    min_y = min(v[1] for v in all_verts)
    min_z = min(v[2] for v in all_verts)
    max_x = max(v[0] for v in all_verts)
    max_y = max(v[1] for v in all_verts)
    max_z = max(v[2] for v in all_verts)

    center = ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
    width = max_x - min_x if (max_x - min_x) > 0 else 0.1
    height = max_z - min_z if (max_z - min_z) > 0 else 0.1
    depth = max_y - min_y if (max_y - min_y) > 0 else 0.1

    # Return center, width, height, depth, and top_z for lighting positioning
    return center, width, height, depth, max_z


def render_preview(
    name: str,
    build_func,
    output_dir: pathlib.Path,
    camera_distance: float = 0.6,
    subject_size: float = 0.3,
):
    """Render a single preview."""
    print(f"\nRendering: {name}")

    # Clear scene first
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clear data INCLUDING node groups (they might have cached wrong values)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    # Clear node groups to ensure fresh generation
    for ng in bpy.data.node_groups:
        bpy.data.node_groups.remove(ng)

    # Set up render settings first
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'

    # World background
    if scene.world:
        bpy.data.worlds.remove(scene.world)
    world = bpy.data.worlds.new("Studio_World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.02, 1)
    bg.inputs["Strength"].default_value = 0.5
    scene.world = world

    # NOW build the subject (creates objects with Geometry Nodes)
    objects = build_func()

    # Calculate bounds using actual geometry (not just object centers)
    if not objects:
        print(f"  WARNING: No objects created!")
        return None

    subject_center, actual_width, actual_height, actual_depth, top_z = get_scene_bounds(objects)
    print(f"  Subject center: ({subject_center[0]*1000:.1f}, {subject_center[1]*1000:.1f}, {subject_center[2]*1000:.1f}) mm")
    print(f"  Subject size: {actual_width*1000:.1f}mm x {actual_height*1000:.1f}mm x {actual_depth*1000:.1f}mm")
    print(f"  Subject top Z: {top_z*1000:.1f}mm")

    # Add camera - position it to see the console from above-front
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Camera positioning for product photography view
    # The panel is a vertical face at Y≈0, knobs extend in Y direction
    # We want to view the panel from front-above
    x, y, z = subject_center

    # Camera distance based on subject size - include depth (Y extent) in calculation
    cam_distance = max(actual_width, actual_height, actual_depth) * 2.0
    if cam_distance < 0.3:
        cam_distance = 0.3  # Minimum 300mm distance

    # Position camera to view the panel from front-right-above
    # Offset in X for 3/4 view, positive Y for front view, elevated Z
    cam_offset_x = actual_width * 0.3   # Slight angle from right
    cam_offset_y = cam_distance          # In front of panel
    cam_offset_z = cam_distance * 0.5   # Above

    cam_obj.location = (x + cam_offset_x, y + cam_offset_y, z + cam_offset_z)

    # Point camera at subject center using track-to quaternion
    # This is more reliable than manual Euler calculations
    direction = Vector((x, y, z)) - Vector(cam_obj.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # Add studio lighting - pass top_z so lights are positioned ABOVE the subject
    lighting = StudioLighting()
    lighting.setup(subject_center, actual_width * 0.7, top_z)

    # Add backdrop
    backdrop = StudioBackdrop()
    backdrop.create(
        width=actual_width * 4,
        height=actual_width * 2,
        depth=actual_width * 2,
    )

    # Render
    output_path = output_dir / f"{name}.png"
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)

    print(f"  Saved: {output_path}")

    # Save blend file
    blend_path = output_dir / f"{name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    return output_path


def main():
    """Render all previews."""
    print("=" * 60)
    print("Console Layout Previews - Studio Product Photography")
    print("=" * 60)

    output_dir = ROOT / "projects" / "output" / "layout_previews"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Render each preview
    renders = [
        ("01_channel_strip", build_channel_strip_scene, 0.4, 0.15),
        ("02_8channel_console", build_8channel_scene, 1.2, 0.5),
        ("03_drum_machine", build_drum_machine_scene, 1.0, 0.4),
        ("04_compressor", build_compressor_scene, 0.6, 0.25),
    ]

    for name, build_func, cam_dist, subj_size in renders:
        render_preview(name, build_func, output_dir, cam_dist, subj_size)

    print("\n" + "=" * 60)
    print(f"All renders saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
