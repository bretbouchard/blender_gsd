"""
Anamorphic billboard display geometry generators.

Creates L-shaped, curved, and flat display surfaces optimized for
3D billboard anamorphic effects.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Any
from enum import Enum
import math


class DisplayType(Enum):
    """Type of billboard display."""
    FLAT = "flat"
    L_SHAPED = "l_shaped"
    CURVED = "curved"
    CYLINDRICAL = "cylindrical"


@dataclass
class DisplayConfig:
    """
    Configuration for billboard display geometry.

    Attributes:
        name: Display object name
        display_type: Type of display (flat, L-shaped, curved)
        width: Display width in meters
        height: Display height in meters
        depth: Depth for L-shaped displays
        curve_radius: Radius for curved displays
        curve_angle: Arc angle for curved displays (degrees)
        resolution_x: Horizontal subdivisions
        resolution_y: Vertical subdivisions
        create_frame: Whether to create display frame/bezel
        bezel_width: Width of display bezel
        emissive_material: Whether to create emissive material
        led_resolution: LED pixel pitch in mm (for reference)
    """
    name: str = "AnamorphicDisplay"
    display_type: DisplayType = DisplayType.L_SHAPED
    width: float = 10.0
    height: float = 8.0
    depth: float = 3.0
    curve_radius: float = 5.0
    curve_angle: float = 90.0
    resolution_x: int = 32
    resolution_y: int = 24
    create_frame: bool = True
    bezel_width: float = 0.1
    emissive_material: bool = True
    led_resolution: float = 2.5  # mm pitch (P2.5 LED)


@dataclass
class DisplayResult:
    """
    Result of display creation.

    Attributes:
        success: Whether creation succeeded
        display_object: Created display mesh object
        frame_object: Created frame object (if any)
        material: Created material (if any)
        uv_layer: UV layer name
        dimensions: Actual dimensions (width, height, depth)
        surface_area: Total surface area in square meters
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    display_object: Any = None
    frame_object: Any = None
    material: Any = None
    uv_layer: str = "UVMap"
    dimensions: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    surface_area: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def create_l_shaped_display(
    config: Optional[DisplayConfig] = None,
) -> DisplayResult:
    """
    Create L-shaped corner display for anamorphic effects.

    L-shaped displays (two planes at 90°) are the most common
    type for anamorphic billboards, providing maximum depth
    illusion when content extends around the corner.

    Args:
        config: Display configuration (uses defaults if not provided)

    Returns:
        DisplayResult with created objects

    Example:
        >>> config = DisplayConfig(
        ...     name="TimesSquareCorner",
        ...     display_type=DisplayType.L_SHAPED,
        ...     width=12.0,
        ...     height=9.0,
        ...     depth=4.0,
        ... )
        >>> result = create_l_shaped_display(config)
        >>> print(f"Created {result.surface_area}m² display")
    """
    if config is None:
        config = DisplayConfig()

    errors = []
    warnings = []

    try:
        import bpy
        import bmesh
        import mathutils
    except ImportError:
        return DisplayResult(
            success=False,
            errors=["Blender (bpy) not available"],
        )

    try:
        # Create new mesh
        mesh = bpy.data.meshes.new(f"{config.name}_mesh")
        obj = bpy.data.objects.new(config.name, mesh)

        # Link to scene
        bpy.context.collection.objects.link(obj)

        # Create L-shaped geometry with bmesh
        bm = bmesh.new()

        w = config.width / 2
        h = config.height
        d = config.depth

        # Vertical plane (front)
        v1 = bm.verts.new((-w, 0, 0))
        v2 = bm.verts.new((0, 0, 0))
        v3 = bm.verts.new((0, 0, h))
        v4 = bm.verts.new((-w, 0, h))

        # Horizontal plane (side)
        v5 = bm.verts.new((0, 0, 0))
        v6 = bm.verts.new((0, d, 0))
        v7 = bm.verts.new((0, d, h))
        v8 = bm.verts.new((0, 0, h))

        bm.verts.ensure_lookup_table()

        # Create faces
        bm.faces.new([v1, v2, v3, v4])  # Front face
        bm.faces.new([v5, v6, v7, v8])  # Side face

        # Subdivide for better UV projection
        bmesh.ops.subdivide_edges(
            bm,
            edges=bm.edges,
            cuts=config.resolution_x // 4,
        )

        # Update mesh
        bm.to_mesh(mesh)
        bm.free()

        # Calculate UVs
        uv_layer = mesh.uv_layers.new(name=config.uv_layer)
        if uv_layer:
            # Simple planar UV mapping
            for loop in mesh.loops:
                vert = mesh.vertices[loop.vertex_index]
                # Front face UVs
                if vert.co.y == 0 and vert.co.x <= 0:
                    u = (vert.co.x + w) / w * 0.5
                    v = vert.co.z / h
                # Side face UVs
                else:
                    u = 0.5 + vert.co.y / d * 0.5
                    v = vert.co.z / h

                uv_layer.data[loop.index].uv = (u, v)

        # Create material if requested
        material = None
        if config.emissive_material:
            material = _create_led_material(config.name, config.led_resolution)
            if material:
                obj.data.materials.append(material)

        # Create frame if requested
        frame_object = None
        if config.create_frame:
            frame_object = _create_display_frame(
                config.name,
                config.width,
                config.height,
                config.depth,
                config.bezel_width,
                DisplayType.L_SHAPED,
            )

        # Calculate dimensions and surface area
        surface_area = (config.width * config.height) + (config.depth * config.height)

        return DisplayResult(
            success=True,
            display_object=obj,
            frame_object=frame_object,
            material=material,
            uv_layer=config.uv_layer,
            dimensions=(config.width, config.height, config.depth),
            surface_area=surface_area,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"Error creating L-shaped display: {e}")
        return DisplayResult(success=False, errors=errors)


def create_curved_display(
    config: Optional[DisplayConfig] = None,
) -> DisplayResult:
    """
    Create curved/convex display for anamorphic effects.

    Curved LED walls provide smoother depth transition than
    L-shaped displays, common in modern installations.

    Args:
        config: Display configuration (uses defaults if not provided)

    Returns:
        DisplayResult with created objects
    """
    if config is None:
        config = DisplayConfig(display_type=DisplayType.CURVED)

    errors = []
    warnings = []

    try:
        import bpy
        import bmesh
        import mathutils
    except ImportError:
        return DisplayResult(
            success=False,
            errors=["Blender (bpy) not available"],
        )

    try:
        # Create new mesh
        mesh = bpy.data.meshes.new(f"{config.name}_mesh")
        obj = bpy.data.objects.new(config.name, mesh)

        bpy.context.collection.objects.link(obj)

        # Create curved geometry
        bm = bmesh.new()

        radius = config.curve_radius
        angle_rad = math.radians(config.curve_angle)
        height = config.height
        segments = config.resolution_x

        # Create arc of vertices
        angle_step = angle_rad / segments
        start_angle = -angle_rad / 2

        verts = []
        for i in range(segments + 1):
            angle = start_angle + i * angle_step
            x = radius * math.sin(angle)
            y = radius * (1 - math.cos(angle))

            # Bottom row
            v_bottom = bm.verts.new((x, y, 0))
            # Top row
            v_top = bm.verts.new((x, y, height))
            verts.append((v_bottom, v_top))

        bm.verts.ensure_lookup_table()

        # Create faces
        for i in range(len(verts) - 1):
            v1_bottom, v1_top = verts[i]
            v2_bottom, v2_top = verts[i + 1]
            bm.faces.new([v1_bottom, v2_bottom, v2_top, v1_top])

        # Subdivide vertically
        bmesh.ops.subdivide_edges(
            bm,
            edges=[e for e in bm.edges if len(list(e.link_faces)) == 1],
            cuts=config.resolution_y // 2,
        )

        bm.to_mesh(mesh)
        bm.free()

        # Calculate UVs
        uv_layer = mesh.uv_layers.new(name=config.uv_layer)
        if uv_layer:
            for loop in mesh.loops:
                vert = mesh.vertices[loop.vertex_index]
                u = (math.atan2(vert.co.x, radius - vert.co.y) + angle_rad / 2) / angle_rad
                v = vert.co.z / height
                uv_layer.data[loop.index].uv = (u, v)

        # Create material
        material = None
        if config.emissive_material:
            material = _create_led_material(config.name, config.led_resolution)
            if material:
                obj.data.materials.append(material)

        # Create frame
        frame_object = None
        if config.create_frame:
            frame_object = _create_display_frame(
                config.name,
                config.width,
                config.height,
                config.depth,
                config.bezel_width,
                DisplayType.CURVED,
            )

        # Calculate arc length as width
        arc_length = radius * angle_rad
        surface_area = arc_length * height

        return DisplayResult(
            success=True,
            display_object=obj,
            frame_object=frame_object,
            material=material,
            uv_layer=config.uv_layer,
            dimensions=(arc_length, height, radius),
            surface_area=surface_area,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"Error creating curved display: {e}")
        return DisplayResult(success=False, errors=errors)


def create_flat_display(
    config: Optional[DisplayConfig] = None,
) -> DisplayResult:
    """
    Create flat display (traditional screen).

    Flat displays have the least depth illusion but are
    simplest to work with.

    Args:
        config: Display configuration

    Returns:
        DisplayResult with created objects
    """
    if config is None:
        config = DisplayConfig(display_type=DisplayType.FLAT)

    errors = []

    try:
        import bpy
    except ImportError:
        return DisplayResult(
            success=False,
            errors=["Blender (bpy) not available"],
        )

    try:
        # Create simple plane
        bpy.ops.mesh.primitive_plane_add(
            size=1.0,
            enter_editmode=False,
            align='WORLD',
            location=(0, 0, config.height / 2),
        )
        obj = bpy.context.active_object
        obj.name = config.name

        # Scale to dimensions
        obj.scale = (config.width, 1.0, config.height)

        # Subdivide
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=config.resolution_x // 2)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Apply scale
        bpy.ops.object.transform_apply(scale=True)

        # Create material
        material = None
        if config.emissive_material:
            material = _create_led_material(config.name, config.led_resolution)
            if material:
                obj.data.materials.append(material)

        surface_area = config.width * config.height

        return DisplayResult(
            success=True,
            display_object=obj,
            material=material,
            uv_layer=config.uv_layer,
            dimensions=(config.width, config.height, 0.0),
            surface_area=surface_area,
        )

    except Exception as e:
        errors.append(f"Error creating flat display: {e}")
        return DisplayResult(success=False, errors=errors)


def _create_led_material(
    name: str,
    led_pitch: float,
) -> Any:
    """Create emissive LED material for display."""
    try:
        import bpy

        mat = bpy.data.materials.new(name=f"{name}_LED")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create emission shader
        output = nodes.new('ShaderNodeOutputMaterial')
        emission = nodes.new('ShaderNodeEmission')

        # Image texture input (for content)
        image = nodes.new('ShaderNodeTexImage')
        image.label = "Content Input"

        # Connect nodes
        links.new(image.outputs['Color'], emission.inputs['Color'])
        links.new(emission.outputs['Emission'], output.inputs['Surface'])

        # Position nodes
        output.location = (400, 0)
        emission.location = (100, 0)
        image.location = (-200, 0)

        # Set emission strength
        emission.inputs['Strength'].default_value = 2.0

        # Material settings for LED look
        mat.blend_method = 'BLEND'
        mat.shadow_method = 'CLIP'

        return mat

    except Exception:
        return None


def _create_display_frame(
    name: str,
    width: float,
    height: float,
    depth: float,
    bezel_width: float,
    display_type: DisplayType,
) -> Any:
    """Create display frame/bezel geometry."""
    try:
        import bpy

        frame_name = f"{name}_Frame"

        if display_type == DisplayType.L_SHAPED:
            # Create corner frame
            bpy.ops.mesh.primitive_cube_add()
            frame = bpy.context.active_object
            frame.name = frame_name
            frame.scale = (width + bezel_width * 2, bezel_width, bezel_width)

            # Additional frame pieces would be added here
            return frame

        elif display_type == DisplayType.CURVED:
            # Create curved frame
            bpy.ops.mesh.primitive_torus_add()
            frame = bpy.context.active_object
            frame.name = frame_name
            return frame

        else:
            # Flat frame
            bpy.ops.mesh.primitive_cube_add()
            frame = bpy.context.active_object
            frame.name = frame_name
            frame.scale = (width + bezel_width * 2, bezel_width, height + bezel_width * 2)
            return frame

    except Exception:
        return None
