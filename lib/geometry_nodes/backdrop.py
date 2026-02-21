"""
Backdrop - Infinite background studio creation.

Based on CGMatter tutorials for infinite studio backdrops. Creates
seamless photo sweep backgrounds perfect for product photography
and studio lighting setups.

Flow Overview:
    Single Sweep:
        Plane -> Extrude edge up -> Bevel edges -> Shade smooth

    Corner Sweep:
        Plane -> Bevel vertex -> Extrude edges -> Bevel -> Smooth

Usage:
    # Create single wall backdrop
    backdrop = InfiniteBackdrop.single_sweep(width=10.0, height=5.0)

    # Create corner backdrop
    corner = InfiniteBackdrop.corner_sweep(width=10.0, height=5.0)

    # Full studio setup
    studio = StudioSetup(backdrop)
    studio.add_key_light(power=3000)
    studio.add_fill_light(power=1500)
    studio.configure_for_subject(product_mesh)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Optional

import bpy
from mathutils import Vector

if TYPE_CHECKING:
    from bpy.types import Light, Material, Node, Object, Scene

    from .node_builder import NodeTreeBuilder


class InfiniteBackdrop:
    """
    Create infinite studio backdrops.

    Creates seamless backgrounds with curved transitions between
    floor and walls, eliminating visible corners and edges.

    Attributes:
        width: Width of the backdrop.
        height: Height of the backdrop.
        depth: Depth (floor length) of the backdrop.
    """

    @staticmethod
    def single_sweep(
        width: float = 10.0,
        height: float = 5.0,
        depth: float = 10.0,
        curve_segments: int = 15,
        curve_radius: float = 1.0,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Create single-wall photo sweep.

        Creates an L-shaped backdrop with a smooth curve connecting
        the floor to the back wall. Perfect for product photography.

        Flow:
            1. Grid (plane) -> Create base mesh
            2. Extrude top edge -> Create wall
            3. Bevel corner edges -> Create smooth curve
            4. Shade Smooth -> Final smooth appearance

        Args:
            width: Width of the backdrop (default 10.0).
            height: Height of the back wall (default 5.0).
            depth: Depth of the floor (default 10.0).
            curve_segments: Number of segments for the curve (default 15).
            curve_radius: Radius of the corner curve (default 1.0).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node with backdrop geometry, or None.

        Example:
            >>> backdrop = InfiniteBackdrop.single_sweep(
            ...     width=15.0, height=6.0, builder=my_builder
            ... )
        """
        if builder is None:
            return None

        # Create base grid
        grid = builder.add_node(
            "GeometryNodeMeshGrid",
            location,
            name="BackdropBase",
        )
        grid.inputs["Vertices X"].default_value = 2
        grid.inputs["Vertices Y"].default_value = 2
        grid.inputs["Size X"].default_value = width
        grid.inputs["Size Y"].default_value = depth

        # Extrude top edge to create wall
        # First, we need to select the top edge
        # In geometry nodes, we use Extrude Mesh with selection

        # Get position for edge selection
        position = builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] + 150, location[1] + 100),
            name="BackdropPosition",
        )

        # Separate Y to select top edge
        separate = builder.add_node(
            "ShaderNodeSeparateXYZ",
            (location[0] + 250, location[1] + 100),
            name="SeparatePosition",
        )
        builder.link(position.outputs["Position"], separate.inputs["Vector"])

        # Compare Y position to select top edge (Y = depth/2)
        compare = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] + 100),
            name="SelectTopEdge",
        )
        compare.operation = "GREATER_THAN"
        compare.inputs[1].default_value = depth / 2 - 0.01  # Small tolerance
        builder.link(separate.outputs["Y"], compare.inputs[0])

        # Extrude to create wall
        extrude = builder.add_node(
            "GeometryNodeExtrudeMesh",
            (location[0] + 550, location[1]),
            name="ExtrudeWall",
        )
        extrude.inputs["Offset"].default_value = (0, 0, height)
        builder.link(grid.outputs["Mesh"], extrude.inputs["Mesh"])
        builder.link(compare.outputs[0], extrude.inputs["Selection"])

        # Bevel the corner edges
        # Select edges at the corner (where floor meets wall)
        bevel = builder.add_node(
            "GeometryNodeMeshBevel",
            (location[0] + 750, location[1]),
            name="BevelCorner",
        )
        bevel.inputs["Amount"].default_value = curve_radius
        bevel.inputs["Segments"].default_value = curve_segments
        builder.link(extrude.outputs["Mesh"], bevel.inputs["Mesh"])

        # Subdivision for smooth curve
        subdivide = builder.add_node(
            "GeometryNodeSubdivisionSurface",
            (location[0] + 950, location[1]),
            name="SmoothBackdrop",
        )
        subdivide.inputs["Level"].default_value = 2
        builder.link(bevel.outputs["Mesh"], subdivide.inputs["Mesh"])

        # Shade smooth
        smooth = builder.add_node(
            "GeometryNodeSetShadeSmooth",
            (location[0] + 1100, location[1]),
            name="ShadeSmoothBackdrop",
        )
        smooth.inputs["Shade Smooth"].default_value = True
        builder.link(subdivide.outputs["Mesh"], smooth.inputs["Geometry"])

        return smooth

    @staticmethod
    def corner_sweep(
        width: float = 10.0,
        height: float = 5.0,
        depth: float = 10.0,
        corner_segments: int = 10,
        curve_segments: int = 15,
        curve_radius: float = 1.0,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Create two-wall corner backdrop.

        Creates an L-shaped floor with two back walls meeting at
        a curved corner. Ideal for 3/4 product shots.

        Flow:
            1. Grid -> Create base
            2. Bevel corner vertex -> Create floor curve
            3. Extrude two edges -> Create walls
            4. Bevel wall corners -> Smooth transitions
            5. Subdivide and smooth

        Args:
            width: Width of each wall section (default 10.0).
            height: Height of the walls (default 5.0).
            depth: Depth of the floor (default 10.0).
            corner_segments: Segments for floor corner curve (default 10).
            curve_segments: Segments for wall curves (default 15).
            curve_radius: Radius of curves (default 1.0).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node with corner backdrop geometry, or None.

        Example:
            >>> corner = InfiniteBackdrop.corner_sweep(
            ...     width=12.0, height=6.0, builder=my_builder
            ... )
        """
        if builder is None:
            return None

        # Create L-shaped base grid
        # Using two grids merged together
        grid_floor = builder.add_node(
            "GeometryNodeMeshGrid",
            location,
            name="FloorBase",
        )
        grid_floor.inputs["Vertices X"].default_value = 2
        grid_floor.inputs["Vertices Y"].default_value = 2
        grid_floor.inputs["Size X"].default_value = width
        grid_floor.inputs["Size Y"].default_value = depth

        # Position for edge selection
        position = builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] + 150, location[1] + 100),
            name="CornerPosition",
        )

        separate = builder.add_node(
            "ShaderNodeSeparateXYZ",
            (location[0] + 250, location[1] + 100),
            name="SeparateCorner",
        )
        builder.link(position.outputs["Position"], separate.inputs["Vector"])

        # Select edges on top AND left (Y = depth/2 OR X = -width/2)
        compare_y = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] + 150),
            name="SelectTopEdge",
        )
        compare_y.operation = "GREATER_THAN"
        compare_y.inputs[1].default_value = depth / 2 - 0.01
        builder.link(separate.outputs["Y"], compare_y.inputs[0])

        compare_x = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 400, location[1] + 50),
            name="SelectLeftEdge",
        )
        compare_x.operation = "LESS_THAN"
        compare_x.inputs[1].default_value = -width / 2 + 0.01
        builder.link(separate.outputs["X"], compare_x.inputs[0])

        # OR the two selections
        or_selection = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 550, location[1] + 100),
            name="CombineSelection",
        )
        or_selection.operation = "ADD"
        builder.link(compare_y.outputs[0], or_selection.inputs[0])
        builder.link(compare_x.outputs[0], or_selection.inputs[1])

        # Extrude to create walls
        extrude = builder.add_node(
            "GeometryNodeExtrudeMesh",
            (location[0] + 700, location[1]),
            name="ExtrudeWalls",
        )
        extrude.inputs["Offset"].default_value = (0, 0, height)
        builder.link(grid_floor.outputs["Mesh"], extrude.inputs["Mesh"])
        builder.link(or_selection.outputs[0], extrude.inputs["Selection"])

        # Bevel all edges for smooth corners
        bevel = builder.add_node(
            "GeometryNodeMeshBevel",
            (location[0] + 900, location[1]),
            name="BevelCorner",
        )
        bevel.inputs["Amount"].default_value = curve_radius
        bevel.inputs["Segments"].default_value = curve_segments
        builder.link(extrude.outputs["Mesh"], bevel.inputs["Mesh"])

        # Subdivide for smoothness
        subdivide = builder.add_node(
            "GeometryNodeSubdivisionSurface",
            (location[0] + 1100, location[1]),
            name="SmoothCornerBackdrop",
        )
        subdivide.inputs["Level"].default_value = 2
        builder.link(bevel.outputs["Mesh"], subdivide.inputs["Mesh"])

        # Shade smooth
        smooth = builder.add_node(
            "GeometryNodeSetShadeSmooth",
            (location[0] + 1250, location[1]),
            name="ShadeSmoothCorner",
        )
        smooth.inputs["Shade Smooth"].default_value = True
        builder.link(subdivide.outputs["Mesh"], smooth.inputs["Geometry"])

        return smooth

    @staticmethod
    def cyc_wall(
        width: float = 20.0,
        height: float = 10.0,
        depth: float = 15.0,
        curve_radius: float = 2.0,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Create a cyclorama wall (full U-shaped backdrop).

        Creates a U-shaped backdrop with curved corners connecting
        floor to side walls and back wall. Commonly used in film
        and large product photography.

        Args:
            width: Total width of the cyc (default 20.0).
            height: Height of the walls (default 10.0).
            depth: Depth of the cyc (default 15.0).
            curve_radius: Radius of all curves (default 2.0).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node with cyc geometry, or None.
        """
        if builder is None:
            return None

        # Create base box mesh
        cube = builder.add_node(
            "GeometryNodeMeshCube",
            location,
            name="CycBase",
        )
        cube.inputs["Size X"].default_value = width
        cube.inputs["Size Y"].default_value = depth
        cube.inputs["Size Y"].default_value = height
        cube.inputs["Vertices X"].default_value = 2
        cube.inputs["Vertices Y"].default_value = 2
        cube.inputs["Vertices Z"].default_value = 2

        # Scale and position
        transform = builder.add_node(
            "GeometryNodeTransform",
            (location[0] + 150, location[1]),
            name="PositionCyc",
        )
        transform.inputs["Translation"].default_value = (0, depth / 2, height / 2)
        builder.link(cube.outputs["Mesh"], transform.inputs["Geometry"])

        # Bevel all edges
        bevel = builder.add_node(
            "GeometryNodeMeshBevel",
            (location[0] + 300, location[1]),
            name="BevelCyc",
        )
        bevel.inputs["Amount"].default_value = curve_radius
        bevel.inputs["Segments"].default_value = 20
        builder.link(transform.outputs["Geometry"], bevel.inputs["Mesh"])

        # Subdivide
        subdivide = builder.add_node(
            "GeometryNodeSubdivisionSurface",
            (location[0] + 500, location[1]),
            name="SmoothCyc",
        )
        subdivide.inputs["Level"].default_value = 2
        builder.link(bevel.outputs["Mesh"], subdivide.inputs["Mesh"])

        # Shade smooth
        smooth = builder.add_node(
            "GeometryNodeSetShadeSmooth",
            (location[0] + 650, location[1]),
            name="ShadeSmoothCyc",
        )
        smooth.inputs["Shade Smooth"].default_value = True
        builder.link(subdivide.outputs["Mesh"], smooth.inputs["Geometry"])

        return smooth

    @staticmethod
    def create_backdrop_material(
        color: tuple[float, float, float, float] = (0.9, 0.9, 0.9, 1.0),
        roughness: float = 0.5,
        material_name: str = "BackdropMaterial",
    ) -> Optional[Material]:
        """
        Create a simple backdrop material.

        Args:
            color: Base color (default light gray).
            roughness: Surface roughness (default 0.5).
            material_name: Name for the material.

        Returns:
            Created Material, or None.
        """
        if not hasattr(bpy, "data"):
            return None

        if material_name in bpy.data.materials:
            return bpy.data.materials[material_name]

        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True

        nodes = material.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")

        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Roughness"].default_value = roughness

        return material


class StudioLight:
    """Configuration for a single studio light."""

    def __init__(
        self,
        name: str,
        light_type: str = "AREA",
        power: float = 1000.0,
        location: tuple[float, float, float] = (0, 0, 5),
        rotation: tuple[float, float, float] = (0, 0, 0),
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
        size: float = 1.0,
    ):
        """
        Initialize studio light configuration.

        Args:
            name: Light name.
            light_type: Light type ("AREA", "POINT", "SPOT", "SUN").
            power: Light power in watts.
            location: World position.
            rotation: Rotation in Euler angles.
            color: Light color.
            size: Light size (for area lights).
        """
        self.name = name
        self.light_type = light_type
        self.power = power
        self.location = location
        self.rotation = rotation
        self.color = color
        self.size = size
        self._light_object: Optional[Light] = None

    def create_light(self) -> Optional[Light]:
        """
        Create the Blender light object.

        Returns:
            Created Light object, or None.
        """
        if not hasattr(bpy, "data"):
            return None

        # Create light data
        light_data = bpy.data.lights.new(name=self.name, type=self.light_type)
        light_data.energy = self.power
        light_data.color = self.color

        if self.light_type == "AREA":
            light_data.size = self.size

        # Create object
        light_obj = bpy.data.objects.new(name=self.name, object_data=light_data)
        light_obj.location = self.location
        light_obj.rotation_euler = self.rotation

        # Link to scene
        bpy.context.collection.objects.link(light_obj)

        self._light_object = light_obj
        return light_obj


class StudioSetup:
    """
    Complete studio lighting setup.

    Provides a fluent interface for building studio lighting
    with key, fill, and rim lights positioned for product
    photography.

    Example:
        >>> studio = StudioSetup(backdrop, builder)
        >>> studio.add_key_light(power=3000)
        >>> studio.add_fill_light(power=1500, angle=45)
        >>> studio.add_rim_light(power=2000)
        >>> studio.configure_for_subject(product)
        >>> studio.set_engine("CYCLES", samples=128)
    """

    # Preset lighting configurations
    LIGHT_PRESETS = {
        "product": {
            "key_power": 3000,
            "fill_power": 1500,
            "rim_power": 2000,
            "key_angle": 45,
            "fill_angle": -45,
        },
        "portrait": {
            "key_power": 2000,
            "fill_power": 1000,
            "rim_power": 1500,
            "key_angle": 30,
            "fill_angle": -30,
        },
        "dramatic": {
            "key_power": 4000,
            "fill_power": 500,
            "rim_power": 3000,
            "key_angle": 60,
            "fill_angle": -20,
        },
        "soft": {
            "key_power": 2000,
            "fill_power": 1800,
            "rim_power": 1000,
            "key_angle": 35,
            "fill_angle": -35,
        },
    }

    def __init__(
        self,
        backdrop: Optional[Object] = None,
        builder: Optional[NodeTreeBuilder] = None,
    ):
        """
        Initialize the studio setup.

        Args:
            backdrop: Backdrop object.
            builder: NodeTreeBuilder for node creation.
        """
        self.backdrop = backdrop
        self.builder = builder
        self._lights: list[StudioLight] = []
        self._subject: Optional[Object] = None
        self._key_distance: float = 10.0
        self._light_height: float = 5.0

    def add_key_light(
        self,
        power: float = 3000.0,
        distance: float = 10.0,
        size: float = 2.0,
        angle: float = 45.0,
        height: Optional[float] = None,
    ) -> "StudioSetup":
        """
        Add key light (main light source).

        Args:
            power: Light power in watts.
            distance: Distance from subject.
            size: Light size (larger = softer).
            angle: Horizontal angle from front (degrees).
            height: Light height (default auto-calculated).

        Returns:
            Self for method chaining.
        """
        angle_rad = math.radians(angle)
        x = distance * math.sin(angle_rad)
        y = -distance * math.cos(angle_rad)
        z = height if height is not None else self._light_height

        # Rotation to point at origin
        rot_x = math.radians(45)  # Tilt down
        rot_z = math.radians(-angle)  # Pan

        light = StudioLight(
            name="KeyLight",
            light_type="AREA",
            power=power,
            location=(x, y, z),
            rotation=(rot_x, 0, rot_z),
            size=size,
        )

        self._lights.append(light)
        self._key_distance = distance
        return self

    def add_fill_light(
        self,
        power: float = 1500.0,
        angle: float = -45.0,
        distance: Optional[float] = None,
        size: float = 3.0,
        height: Optional[float] = None,
    ) -> "StudioSetup":
        """
        Add fill light (secondary, softer light).

        Args:
            power: Light power in watts.
            angle: Horizontal angle from front (degrees, negative = left).
            distance: Distance from subject (default same as key).
            size: Light size.
            height: Light height.

        Returns:
            Self for method chaining.
        """
        distance = distance or self._key_distance
        angle_rad = math.radians(angle)
        x = distance * math.sin(angle_rad)
        y = -distance * math.cos(angle_rad)
        z = height if height is not None else self._light_height * 0.8

        rot_x = math.radians(45)
        rot_z = math.radians(-angle)

        light = StudioLight(
            name="FillLight",
            light_type="AREA",
            power=power,
            location=(x, y, z),
            rotation=(rot_x, 0, rot_z),
            size=size,
        )

        self._lights.append(light)
        return self

    def add_rim_light(
        self,
        power: float = 2000.0,
        angle: float = 180.0,
        distance: Optional[float] = None,
        size: float = 1.5,
        height: Optional[float] = None,
    ) -> "StudioSetup":
        """
        Add rim light (back light for edge definition).

        Args:
            power: Light power in watts.
            angle: Horizontal angle (default behind subject).
            distance: Distance from subject.
            size: Light size.
            height: Light height.

        Returns:
            Self for method chaining.
        """
        distance = distance or self._key_distance
        angle_rad = math.radians(angle)
        x = distance * math.sin(angle_rad)
        y = -distance * math.cos(angle_rad)
        z = height if height is not None else self._light_height * 1.2

        rot_x = math.radians(-30)  # Tilt up
        rot_z = math.radians(-angle)

        light = StudioLight(
            name="RimLight",
            light_type="AREA",
            power=power,
            location=(x, y, z),
            rotation=(rot_x, 0, rot_z),
            size=size,
        )

        self._lights.append(light)
        return self

    def add_top_light(
        self,
        power: float = 1000.0,
        height: float = 8.0,
        size: float = 2.0,
    ) -> "StudioSetup":
        """
        Add overhead fill light.

        Args:
            power: Light power in watts.
            height: Light height.
            size: Light size.

        Returns:
            Self for method chaining.
        """
        light = StudioLight(
            name="TopLight",
            light_type="AREA",
            power=power,
            location=(0, 0, height),
            rotation=(math.radians(90), 0, 0),
            size=size,
        )

        self._lights.append(light)
        return self

    def use_preset(self, preset_name: str) -> "StudioSetup":
        """
        Apply a lighting preset.

        Args:
            preset_name: Name of preset ("product", "portrait", "dramatic", "soft").

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If preset name is invalid.
        """
        if preset_name not in self.LIGHT_PRESETS:
            raise ValueError(
                f"Invalid preset '{preset_name}'. "
                f"Available: {', '.join(self.LIGHT_PRESETS.keys())}"
            )

        preset = self.LIGHT_PRESETS[preset_name]

        self.add_key_light(
            power=preset["key_power"],
            angle=preset["key_angle"],
        )
        self.add_fill_light(
            power=preset["fill_power"],
            angle=preset["fill_angle"],
        )
        self.add_rim_light(power=preset["rim_power"])

        return self

    def configure_for_subject(
        self,
        subject: Object,
        distance_factor: float = 3.0,
    ) -> "StudioSetup":
        """
        Auto-configure lighting based on subject bounds.

        Args:
            subject: Subject object.
            distance_factor: Distance multiplier based on subject size.

        Returns:
            Self for method chaining.
        """
        self._subject = subject

        if subject is not None and hasattr(subject, "bound_box"):
            # Calculate subject bounds
            bbox = subject.bound_box
            min_corner = Vector(bbox[0])
            max_corner = Vector(bbox[6])
            size = (max_corner - min_corner).length

            # Set light distance based on size
            self._key_distance = size * distance_factor
            self._light_height = size * 1.5

        return self

    def set_engine(
        self,
        engine: str,
        samples: int = 128,
        use_denoising: bool = True,
    ) -> "StudioSetup":
        """
        Configure render engine settings.

        Args:
            engine: Render engine ("CYCLES", "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT").
            samples: Render samples.
            use_denoising: Enable denoising.

        Returns:
            Self for method chaining.
        """
        if not hasattr(bpy, "context"):
            return self

        scene = bpy.context.scene
        scene.render.engine = engine

        if engine == "CYCLES":
            scene.cycles.samples = samples
            scene.cycles.use_denoising = use_denoising

        return self

    def build(self) -> list[Light]:
        """
        Create all lights in the scene.

        Returns:
            List of created Light objects.
        """
        created_lights = []

        for light_config in self._lights:
            light_obj = light_config.create_light()
            if light_obj:
                created_lights.append(light_obj)

        return created_lights

    def get_light_positions(self) -> dict[str, Vector]:
        """
        Get calculated light positions.

        Returns:
            Dictionary of light name to position vector.
        """
        positions = {}
        for light in self._lights:
            positions[light.name] = Vector(light.location)
        return positions


def create_studio(
    backdrop_type: str = "single",
    width: float = 10.0,
    height: float = 5.0,
    depth: float = 10.0,
    lighting_preset: str = "product",
    builder: Optional[NodeTreeBuilder] = None,
) -> Optional[Node]:
    """
    Quick studio creation with backdrop and lighting.

    Args:
        backdrop_type: "single", "corner", or "cyc".
        width: Backdrop width.
        height: Backdrop height.
        depth: Backdrop depth.
        lighting_preset: Lighting preset name.
        builder: NodeTreeBuilder for node creation.

    Returns:
        Backdrop geometry node, or None.

    Example:
        >>> studio = create_studio(
        ...     backdrop_type="corner",
        ...     width=15.0,
        ...     lighting_preset="product",
        ...     builder=my_builder
        ... )
    """
    # Create backdrop
    if backdrop_type == "single":
        backdrop = InfiniteBackdrop.single_sweep(
            width=width, height=height, depth=depth, builder=builder
        )
    elif backdrop_type == "corner":
        backdrop = InfiniteBackdrop.corner_sweep(
            width=width, height=height, depth=depth, builder=builder
        )
    elif backdrop_type == "cyc":
        backdrop = InfiniteBackdrop.cyc_wall(
            width=width, height=height, depth=depth, builder=builder
        )
    else:
        raise ValueError(f"Invalid backdrop_type '{backdrop_type}'")

    # Setup lighting
    studio = StudioSetup(builder=builder)
    studio.use_preset(lighting_preset)
    studio.build()

    return backdrop
