"""
Layout Renderer - Generate Blender geometry from layout specifications.

Renders PanelLayout objects to actual 3D geometry in Blender.
"""

from typing import List, Dict, Any, Optional, Callable
import bpy
from mathutils import Vector
import sys
import pathlib
import os

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout.panel import (
    PanelLayout, ElementSpec, ElementType
)
from lib.layout.standards import (
    ElementSize, KNOB_SIZES, BUTTON_SIZES, FADER_SIZES, LED_SIZES,
    DEFAULT_GRID
)
from lib.inputs import (
    create_knob_node_group,
    create_button_node_group,
    create_fader_node_group,
    create_led_node_group,
)
from lib.nodekit import NodeKit


# =============================================================================
# SANCTUS MATERIAL HELPER
# =============================================================================

SANCTUS_PATH = pathlib.Path.home() / "Library/Application Support/Blender/5.0/scripts/addons/Sanctus-Library/lib/materials"

# Mapping of logical material names to (blend_file, material_name, category)
# Sanctus stores multiple materials in a single blend file
SANCTUS_MATERIAL_MAP = {
    # Panel materials
    "panel_brushed": ("brushed_metal", "brushed_metal_01", "Metals"),
    "panel_anthracite": ("anisotropic_brushed_metal", "anisotropic_brushed_metal_01", "Metals"),

    # Knob materials - Car Paint for glossy colored knobs
    "knob_red": ("car_paint", "car_paint_01", "Car Paint"),
    "knob_blue": ("car_paint", "car_paint_04", "Car Paint"),
    "knob_green": ("car_paint", "car_paint_02", "Car Paint"),
    "knob_yellow": ("car_paint", "car_paint_03", "Car Paint"),

    # Knob materials - Metals for professional look
    "knob_gold": ("gold_pure", "gold_pure", "Metals"),
    "knob_gray": ("anodized_alu", "anodized_alu_01", "Metals"),
    "knob_silver": ("silver_polished", "silver_polished", "Metals"),
    "knob_black": ("anodized_alu", "anodized_alu_04", "Metals"),

    # Other materials
    "button": ("anodized_alu", "anodized_alu_02", "Metals"),
    "fader_track": ("brushed_metal", "brushed_metal_01", "Metals"),
}


def load_sanctus_material(logical_name: str) -> Optional[bpy.types.Material]:
    """
    Load a material from the Sanctus-Library.

    Args:
        logical_name: Logical name like "knob_red", "panel_brushed" (see SANCTUS_MATERIAL_MAP)

    Returns:
        The loaded material or None if not found
    """
    if logical_name not in SANCTUS_MATERIAL_MAP:
        print(f"  WARNING: Unknown Sanctus material: {logical_name}")
        return None

    blend_file, material_name, category = SANCTUS_MATERIAL_MAP[logical_name]
    blend_path = SANCTUS_PATH / category / f"{blend_file}.blend"

    if not blend_path.exists():
        print(f"  WARNING: Sanctus blend file not found: {blend_path}")
        return None

    # Check if already loaded
    if material_name in bpy.data.materials:
        return bpy.data.materials[material_name]

    # Append the material
    try:
        with bpy.data.libraries.load(str(blend_path)) as (data_from, data_to):
            if material_name in data_from.materials:
                data_to.materials = [material_name]
            else:
                print(f"  WARNING: Material '{material_name}' not found in {blend_path}")
                print(f"    Available materials: {list(data_from.materials)[:5]}...")
                return None
    except Exception as e:
        print(f"  WARNING: Error loading Sanctus material: {e}")
        return None

    if material_name in bpy.data.materials:
        mat = bpy.data.materials[material_name]
        mat.use_fake_user = True  # Keep it loaded
        return mat

    return None


def apply_sanctus_material(obj: bpy.types.Object, logical_name: str) -> bool:
    """
    Apply a Sanctus material to an object.

    Args:
        obj: Blender object to apply material to
        logical_name: Logical name like "knob_red", "panel_brushed"

    Returns:
        True if material was applied successfully
    """
    mat = load_sanctus_material(logical_name)
    if mat:
        # Clear existing materials
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        return True
    return False


class LayoutRenderer:
    """
    Renders a PanelLayout to Blender geometry.

    Usage:
        renderer = LayoutRenderer(layout)
        renderer.render()

    Or with custom handlers:
        renderer = LayoutRenderer(layout)
        renderer.render_element = my_custom_renderer
        renderer.render()
    """

    # How much of the knob's Zone B should embed INTO the panel (mm)
    # This creates the realistic look of knobs emerging from holes
    KNOB_PANEL_EMBED_MM = 5.0

    # Neve-style color palette (fallback if Sanctus not available)
    COLORS = {
        # Classic Neve knob colors
        "knob_red": (0.75, 0.18, 0.12),       # Classic Neve red (gain/drive)
        "knob_blue": (0.15, 0.35, 0.65),      # Neve blue (EQ/frequency)
        "knob_gray": (0.45, 0.45, 0.47),      # Neutral gray (output/misc)
        "knob_gold": (0.76, 0.60, 0.30),      # Gold/champagne (vintage)

        # Panel colors
        "panel_anthracite": (0.12, 0.12, 0.13),  # Dark anthracite
        "panel_gray": (0.18, 0.18, 0.19),        # Standard gray

        # Button colors
        "button_red": (0.70, 0.15, 0.10),
        "button_green": (0.15, 0.55, 0.20),
        "button_gray": (0.35, 0.35, 0.37),

        # Fader colors
        "fader_knob": (0.40, 0.40, 0.42),
        "fader_track": (0.10, 0.10, 0.10),
    }

    # Sanctus material mappings are now in SANCTUS_MATERIAL_MAP at module level
    # Use load_sanctus_material(logical_name) to load materials

    # Color assignment rules by element name patterns
    KNOB_COLOR_PATTERNS = {
        # Red knobs (gain, drive, input, output, level)
        "red": ["gain", "drive", "input", "output", "level", "trim", "volume", "master"],
        # Blue knobs (EQ, frequency, filter)
        "blue": ["freq", "frequency", "hf", "mf", "lf", "high", "mid", "low", "filter", "eq", "q"],
        # Gold knobs (vintage style - dynamics)
        "gold": ["attack", "release", "ratio", "threshold", "comp", "compress", "limit"],
    }

    # Whether to use Sanctus materials
    use_sanctus = True

    def __init__(
        self,
        layout: PanelLayout,
        collection: bpy.types.Collection = None,
        base_name: str = None
    ):
        self.layout = layout
        self.collection = collection or bpy.context.scene.collection
        self.base_name = base_name or layout.name.replace(" ", "_")
        self._created_objects: List[bpy.types.Object] = []

        # Node groups (cached)
        self._node_groups: Dict[str, bpy.types.NodeTree] = {}

    def render(self) -> List[bpy.types.Object]:
        """
        Render the complete layout.

        Returns:
            List of created Blender objects.
        """
        # Create panel base
        panel_obj = self._create_panel_base()
        self._created_objects.append(panel_obj)

        # Render all elements
        elements = self.layout.get_all_elements()

        for spec in elements:
            obj = self._render_element(spec)
            if obj:
                # Store world transform before parenting
                world_matrix = obj.matrix_world.copy()

                # Set parent
                obj.parent = panel_obj

                # Restore world transform by setting matrix_parent_inverse
                # This counteracts the parent's transform so the child
                # maintains its original world position and scale
                obj.matrix_parent_inverse = panel_obj.matrix_world.inverted()

                self._created_objects.append(obj)

        return self._created_objects

    def _create_panel_base(self) -> bpy.types.Object:
        """Create the base panel mesh with Neve-style materials."""
        # Convert mm to meters
        width = self.layout.width / 1000
        height = self.layout.height / 1000
        depth = 0.003  # 3mm panel thickness

        # Create panel mesh
        bpy.ops.mesh.primitive_cube_add(size=1)
        panel = bpy.context.active_object
        panel.name = f"{self.base_name}_Panel"
        panel.scale = (width, depth, height)
        panel.location = (width / 2, -depth / 2, -height / 2)

        # Try to use Sanctus material for panel
        if self.use_sanctus:
            if load_sanctus_material("panel_anthracite"):
                apply_sanctus_material(panel, "panel_anthracite")
                self._link_to_collection(panel)
                return panel

        # Fallback: Create simple material with Neve-style anthracite
        mat = bpy.data.materials.new(f"{self.base_name}_Panel_Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            # Neve-style dark anthracite panel
            color = self.COLORS["panel_anthracite"]
            bsdf.inputs["Base Color"].default_value = (*color, 1)
            bsdf.inputs["Roughness"].default_value = 0.4
            bsdf.inputs["Metallic"].default_value = 0.05
        panel.data.materials.append(mat)

        # Link to collection
        self._link_to_collection(panel)

        return panel

    def _render_element(self, spec: ElementSpec) -> Optional[bpy.types.Object]:
        """Render a single element based on its type."""
        if spec.element_type == ElementType.KNOB:
            return self._render_knob(spec)
        elif spec.element_type == ElementType.BUTTON:
            return self._render_button(spec)
        elif spec.element_type == ElementType.FADER:
            return self._render_fader(spec)
        elif spec.element_type == ElementType.LED:
            return self._render_led(spec)
        elif spec.element_type == ElementType.LABEL:
            return self._render_label(spec)
        elif spec.element_type == ElementType.DISPLAY:
            return self._render_display(spec)
        return None

    def _get_knob_color(self, name: str) -> tuple:
        """
        Determine knob color based on element name.

        Neve-style color coding:
        - Red: Gain, drive, input, output, level controls
        - Blue: EQ, frequency, filter controls
        - Gold: Dynamics (attack, release, ratio)
        - Gray: Everything else
        """
        name_lower = name.lower()

        for color_type, patterns in self.KNOB_COLOR_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower:
                    if color_type == "red":
                        return self.COLORS["knob_red"]
                    elif color_type == "blue":
                        return self.COLORS["knob_blue"]
                    elif color_type == "gold":
                        return self.COLORS["knob_gold"]

        return self.COLORS["knob_gray"]

    def _get_knob_sanctus_material(self, name: str) -> Optional[bpy.types.Material]:
        """
        Get the appropriate Sanctus material for a knob based on its name.

        Returns the loaded material or None if Sanctus is disabled/material not found.
        """
        if not self.use_sanctus:
            return None

        name_lower = name.lower()
        mat_key = "knob_gray"  # default

        for color_type, patterns in self.KNOB_COLOR_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower:
                    if color_type == "red":
                        mat_key = "knob_red"
                    elif color_type == "blue":
                        mat_key = "knob_blue"
                    elif color_type == "gold":
                        mat_key = "knob_gold"
                    break
            if mat_key != "knob_gray":
                break

        return load_sanctus_material(mat_key)

    def _get_size_params(self, element_type: ElementType, size: ElementSize) -> Dict[str, float]:
        """Get parameters for an element size."""
        if element_type == ElementType.KNOB:
            s = KNOB_SIZES[size]
            # The knob node group uses multiple diameter parameters
            # Set all to the same value for a uniform knob
            return {
                "Top_Diameter": s.diameter,
                "A_Mid_Top_Diameter": s.diameter,
                "A_Bot_Top_Diameter": s.diameter,
                "AB_Junction_Diameter": s.diameter,
                "B_Mid_Bot_Diameter": s.diameter,
                "Bot_Diameter": s.diameter,
                "A_Top_Height": s.height * 0.15,
                "A_Mid_Height": s.height * 0.25,
                "A_Bot_Height": s.height * 0.1,
                "B_Top_Height": s.height * 0.1,
                "B_Mid_Height": s.height * 0.25,
                "B_Bot_Height": s.height * 0.15,
                "A_Mid_Knurl_Count": s.knurl_count,
                "B_Mid_Knurl_Count": s.knurl_count,
            }
        elif element_type == ElementType.BUTTON:
            s = BUTTON_SIZES[size]
            return {
                "Diameter": s.diameter,
                "Height": s.height,
                "Travel": s.travel,
            }
        elif element_type == ElementType.FADER:
            s = FADER_SIZES[size]
            return {
                "Travel_Length": s.travel_length,
                "Knob_Width": s.knob_width,
                "Knob_Height": s.knob_height,
                "Track_Width": s.track_width,
            }
        elif element_type == ElementType.LED:
            s = LED_SIZES[size]
            return {
                "Size": s.diameter,
                "Height": s.height,
            }
        return {}

    def _apply_node_group(
        self,
        obj: bpy.types.Object,
        node_group_name: str,
        create_func: Callable,
        params: Dict[str, Any]
    ) -> bpy.types.NodeTree:
        """Apply a Geometry Nodes group to an object with parameters."""
        # Get or create node group
        if node_group_name not in self._node_groups:
            self._node_groups[node_group_name] = create_func(node_group_name)

        node_group = self._node_groups[node_group_name]

        # Create modifier
        mod = obj.modifiers.new(name=node_group_name, type='NODES')
        mod.node_group = node_group

        # Set parameters
        for param_name, param_value in params.items():
            # Find the input socket
            found = False
            for item in node_group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == param_name:
                    # Handle color tuples - convert to list with alpha
                    if item.socket_type == 'NodeSocketColor' and isinstance(param_value, tuple):
                        param_value = list(param_value) + [1.0]  # Add alpha channel
                    # Pass values directly - node groups expect mm and convert internally
                    mod[item.identifier] = param_value
                    found = True
                    break
            if not found:
                print(f"  WARNING: Parameter '{param_name}' not found in node group '{node_group_name}'")

        return node_group

    def _render_knob(self, spec: ElementSpec) -> bpy.types.Object:
        """Render a knob element.

        The knob is positioned so that:
        - Zone B (bottom) partially embeds INTO the panel
        - Zone A (top) protrudes from the panel front face

        This creates the realistic look of knobs emerging from holes
        in the faceplate, rather than floating in front of it.

        Knob materials use Sanctus when available:
        - Red (Car Paint): Gain, level, input, output
        - Blue (Car Paint): EQ, frequency
        - Gold (Metal): Dynamics
        - Gray (Anodized Alu): Other
        """
        import math

        # Create empty object
        bpy.ops.mesh.primitive_cube_add(size=0.001)
        knob = bpy.context.active_object
        knob.name = f"{self.base_name}_Knob_{spec.name}"

        # Position (convert mm to meters)
        # Layout: X (right), Y (down from top)
        # Blender: X (right), Y (forward), Z (up)
        # We need to rotate 90° on X to map Layout Y → Blender Z
        x, y = spec.to_meters()

        # Calculate Y offset so knob embeds into panel
        # Panel front face is at Y=0, panel extends in -Y direction
        # We want KNOB_PANEL_EMBED_MM of Zone B to be BEHIND the face (negative Y)
        embed_m = self.KNOB_PANEL_EMBED_MM / 1000  # Convert to meters

        # Position: X stays same, Y goes into panel, Z = -layout_y (up is positive Z)
        knob.location = (x, -embed_m, -y)

        # Rotate 90° on X axis to orient knob correctly
        # This maps: layout Y (down) → Blender Z (up)
        knob.rotation_euler = (math.pi / 2, 0, 0)

        # Get size params and apply node group
        params = self._get_size_params(ElementType.KNOB, spec.size)
        params.update(spec.custom_params)

        # Try to load Sanctus material for this knob
        sanctus_mat = self._get_knob_sanctus_material(spec.name)
        if sanctus_mat:
            # Pass Sanctus material to the node group
            params["Material"] = sanctus_mat
        else:
            # Fallback to procedural colors
            color = self._get_knob_color(spec.name)
            params["Color"] = color  # RGB tuple
            params["Metallic"] = 0.1  # Slight metallic sheen
            params["Roughness"] = 0.35  # Slightly glossy

        self._apply_node_group(
            knob,
            f"Knob_{spec.size.value}",
            create_knob_node_group,
            params
        )

        self._link_to_collection(knob)
        return knob

    def _render_button(self, spec: ElementSpec) -> bpy.types.Object:
        """Render a button element.

        Buttons are positioned similarly to knobs - embedded into the panel
        so they appear to emerge from holes in the faceplate.
        """
        import math

        bpy.ops.mesh.primitive_cube_add(size=0.001)
        button = bpy.context.active_object
        button.name = f"{self.base_name}_Button_{spec.name}"

        x, y = spec.to_meters()

        # Embed button into panel (use same offset as knobs)
        embed_m = self.KNOB_PANEL_EMBED_MM / 1000
        button.location = (x, -embed_m, -y)

        # Rotate 90° on X axis for correct orientation
        button.rotation_euler = (math.pi / 2, 0, 0)

        params = self._get_size_params(ElementType.BUTTON, spec.size)
        params.update(spec.custom_params)
        params["Style"] = spec.style

        self._apply_node_group(
            button,
            f"Button_{spec.size.value}",
            create_button_node_group,
            params
        )

        self._link_to_collection(button)
        return button

    def _render_fader(self, spec: ElementSpec) -> bpy.types.Object:
        """Render a fader element.

        Faders are positioned flush with the panel surface.
        """
        import math

        bpy.ops.mesh.primitive_cube_add(size=0.001)
        fader = bpy.context.active_object
        fader.name = f"{self.base_name}_Fader_{spec.name}"

        x, y = spec.to_meters()

        # Faders sit on the panel surface (not embedded)
        embed_m = self.KNOB_PANEL_EMBED_MM / 1000
        fader.location = (x, -embed_m, -y)

        # Rotate 90° on X axis for correct orientation
        fader.rotation_euler = (math.pi / 2, 0, 0)

        params = self._get_size_params(ElementType.FADER, spec.size)
        params.update(spec.custom_params)
        params["Value"] = spec.value

        self._apply_node_group(
            fader,
            f"Fader_{spec.size.value}",
            create_fader_node_group,
            params
        )

        self._link_to_collection(fader)
        return fader

    def _render_led(self, spec: ElementSpec) -> bpy.types.Object:
        """Render an LED element.

        LEDs are positioned to sit on the panel surface.
        """
        import math

        bpy.ops.mesh.primitive_cube_add(size=0.001)
        led = bpy.context.active_object
        led.name = f"{self.base_name}_LED_{spec.name}"

        x, y = spec.to_meters()

        # LEDs sit on panel surface (not embedded)
        embed_m = self.KNOB_PANEL_EMBED_MM / 1000
        led.location = (x, -embed_m, -y)

        # Rotate 90° on X axis for correct orientation
        led.rotation_euler = (math.pi / 2, 0, 0)

        params = self._get_size_params(ElementType.LED, spec.size)
        params.update(spec.custom_params)
        params["Value"] = spec.value

        self._apply_node_group(
            led,
            f"LED_{spec.size.value}",
            create_led_node_group,
            params
        )

        self._link_to_collection(led)
        return led

    def _render_label(self, spec: ElementSpec) -> Optional[bpy.types.Object]:
        """Render a text label (placeholder - could use text object)."""
        # For now, skip labels - they can be added as text objects later
        return None

    def _render_display(self, spec: ElementSpec) -> Optional[bpy.types.Object]:
        """Render a display element (VU meter, etc.)."""
        # Placeholder for display rendering
        return None

    def _link_to_collection(self, obj: bpy.types.Object):
        """Link object to the target collection."""
        # Remove from all collections first
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        # Add to target
        self.collection.objects.link(obj)


# =============================================================================
# BATCH RENDERER
# =============================================================================

class BatchRenderer:
    """
    Render multiple layouts in a scene.

    Useful for creating complete console views with multiple channel strips.
    """

    def __init__(self, name: str = "Console"):
        self.name = name
        self.layouts: List[PanelLayout] = []
        self.positions: List[tuple] = []  # (x, y) in mm

        # Create main collection
        self.collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(self.collection)

    def add_layout(
        self,
        layout: PanelLayout,
        x: float = 0.0,
        y: float = 0.0
    ) -> 'BatchRenderer':
        """Add a layout at a specific position. Returns self for chaining."""
        self.layouts.append(layout)
        self.positions.append((x, y))
        return self

    def add_layout_row(
        self,
        layout: PanelLayout,
        count: int,
        start_x: float = 0.0,
        y: float = 0.0,
        spacing: float = None
    ) -> 'BatchRenderer':
        """Add multiple copies of a layout in a row."""
        if spacing is None:
            spacing = layout.width + DEFAULT_GRID.channel_spacing

        for i in range(count):
            self.add_layout(layout, start_x + (i * spacing), y)

        return self

    def render(self) -> List[bpy.types.Object]:
        """Render all layouts."""
        objects = []

        for layout, (x, y) in zip(self.layouts, self.positions):
            # Create sub-collection for this layout
            coll_name = f"{layout.name.replace(' ', '_')}"
            sub_coll = bpy.data.collections.new(coll_name)
            self.collection.children.link(sub_coll)

            # Render with offset
            renderer = LayoutRenderer(layout, collection=sub_coll)

            # Temporarily modify layout positions
            orig_width = layout.width
            orig_height = layout.height

            # Render
            layout_objects = renderer.render()

            # Offset all objects
            for obj in layout_objects:
                obj.location.x += x / 1000
                obj.location.z -= y / 1000

            objects.extend(layout_objects)

        return objects


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def render_layout(layout: PanelLayout, collection: bpy.types.Collection = None) -> List[bpy.types.Object]:
    """Quick function to render a single layout."""
    renderer = LayoutRenderer(layout, collection)
    return renderer.render()


def render_console_row(
    layout: PanelLayout,
    count: int,
    spacing: float = None,
    name: str = "Console"
) -> List[bpy.types.Object]:
    """Quick function to render a row of identical channel strips."""
    batch = BatchRenderer(name)
    batch.add_layout_row(layout, count, spacing=spacing)
    return batch.render()
