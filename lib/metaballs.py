"""
SDF Volume Metaballs Module - Codified from Tutorial 13

Implements perfect metaballs using Blender 5.0+ Point to SDF Grid node.
Creates organic blob effects with smooth blending and animation.

Based on Ducky 3D tutorial: https://www.youtube.com/watch?v=MgZsVBVZ3Nc

Usage:
    from lib.metaballs import SDFMetaballs

    # Create SDF metaballs
    metaballs = SDFMetaballs.create("MyMetaballs")
    metaballs.set_container_mesh(icosphere)
    metaballs.set_radius(0.5)
    metaballs.set_voxel_size(0.04)  # 0.002 for final render
    metaballs.set_smooth_iterations(50)
    metaballs.animate_with_noise(scale=1.0, speed=0.3)
    tree = metaballs.build()
"""

from __future__ import annotations
import bpy
from typing import Optional
from pathlib import Path

# Import NodeKit for node building
try:
    from .nodekit import NodeKit
except ImportError:
    from nodekit import NodeKit


class SDFMetaballs:
    """
    SDF volume metaballs using Blender 5.0+ nodes.

    Creates a node tree that:
    - Converts mesh to volume
    - Distributes points in volume
    - Converts points to SDF grid (the key Blender 5.0 node)
    - Converts grid back to mesh
    - Applies smoothing and normal blur

    Cross-references:
    - KB Section 13: SDF Volume Metaballs (Ducky 3D)
    - KB Section 21: Glass flowers (uses similar blur)
    - lib/nodekit.py: For node tree building patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._container_mesh: Optional[bpy.types.Object] = None
        self._radius = 0.5
        self._voxel_size = 0.04  # 0.04 for viewport, 0.002 for render
        self._point_density = 10.0
        self._smooth_iterations = 30
        self._normal_blur_iterations = 30
        self._noise_settings = {
            'enabled': False,
            'scale': 1.0,
            'speed': 0.3,
            'strength': 0.2,
            'detail': 0.0  # 0 for smooth noise
        }
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "SDFMetaballs") -> "SDFMetaballs":
        """
        Create a new geometry node tree for SDF metaballs.

        Args:
            name: Name for the node group

        Returns:
            Configured SDFMetaballs instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "SDFMetaballs"
    ) -> "SDFMetaballs":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to use as container
            name: Name for the node group

        Returns:
            Configured SDFMetaballs instance
        """
        mod = obj.modifiers.new(name=name, type='NODES')
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        mod.node_group = tree

        instance = cls(tree)
        instance._setup_interface()
        instance._container_mesh = obj
        return instance

    def _setup_interface(self) -> None:
        """Set up the node group interface (inputs/outputs)."""
        # Create interface inputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Point Radius", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._radius, min_value=0.01, max_value=5.0
        )
        self.node_tree.interface.new_socket(
            name="Voxel Size", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._voxel_size, min_value=0.001, max_value=0.5
        )
        self.node_tree.interface.new_socket(
            name="Point Density", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._point_density, min_value=1.0, max_value=100.0
        )
        self.node_tree.interface.new_socket(
            name="Smooth Iterations", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._smooth_iterations, min_value=0, max_value=200
        )
        self.node_tree.interface.new_socket(
            name="Normal Blur Iterations", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._normal_blur_iterations, min_value=0, max_value=100
        )
        self.node_tree.interface.new_socket(
            name="Noise Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_settings['scale'], min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Noise Speed", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_settings['speed'], min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Noise Strength", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_settings['strength'], min_value=0.0, max_value=2.0
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_container_mesh(self, obj: bpy.types.Object) -> "SDFMetaballs":
        """Set the container mesh that defines volume bounds."""
        self._container_mesh = obj
        return self

    def set_radius(self, radius: float) -> "SDFMetaballs":
        """
        Set point radius for blob size.

        Args:
            radius: Radius of each point (0.3-1.0 typical)
        """
        self._radius = radius
        return self

    def set_voxel_size(self, size: float) -> "SDFMetaballs":
        """
        Set voxel size for quality.

        Args:
            size: Voxel size (0.04 for viewport, 0.002 for final render)
        """
        self._voxel_size = size
        return self

    def set_point_density(self, density: float) -> "SDFMetaballs":
        """Set point density for blob count."""
        self._point_density = density
        return self

    def set_smooth_iterations(self, iterations: int) -> "SDFMetaballs":
        """
        Set smoothing iterations for "goopiness".

        Args:
            iterations: More = goopier (2-100+)
        """
        self._smooth_iterations = iterations
        return self

    def set_normal_blur(self, iterations: int) -> "SDFMetaballs":
        """
        Set normal blur iterations to fix circular artifacts.

        Args:
            iterations: Typically 30 for smooth normals
        """
        self._normal_blur_iterations = iterations
        return self

    def animate_with_noise(
        self,
        scale: float = 1.0,
        speed: float = 0.3,
        strength: float = 0.2,
        detail: float = 0.0
    ) -> "SDFMetaballs":
        """Add 4D noise animation for blob movement."""
        self._noise_settings = {
            'enabled': True,
            'scale': scale,
            'speed': speed,
            'strength': strength,
            'detail': detail  # 0 for smooth noise
        }
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for SDF metaballs.

        KB Reference: Section 13 - SDF Volume Metaballs

        Returns:
            The configured node tree
        """
        if not self.nk:
            raise RuntimeError("Call create() or from_object() first")

        nk = self.nk
        x = 0

        # === INPUT NODES ===
        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # === MESH TO VOLUME ===
        # KB Reference: Section 13 - Convert container to volume
        mesh_to_vol = nk.n(
            "GeometryNodeMeshToVolume",
            "Mesh to Volume",
            x=x, y=100
        )
        nk.link(group_in.outputs["Geometry"], mesh_to_vol.inputs["Mesh"])
        nk.link(group_in.outputs["Voxel Size"], mesh_to_vol.inputs["Voxel Size"])
        # Set interior volume
        mesh_to_vol.inputs["Fill Volume Only"].default_value = False
        self._created_nodes['mesh_to_volume'] = mesh_to_vol

        x += 250

        # === DISTRIBUTE POINTS IN VOLUME ===
        # KB Reference: Section 13 - Generate blob positions
        distribute = nk.n(
            "GeometryNodeDistributePointsInVolume",
            "Distribute Points",
            x=x, y=100
        )
        nk.link(mesh_to_vol.outputs["Volume"], distribute.inputs["Volume"])
        nk.link(group_in.outputs["Point Density"], distribute.inputs["Density"])
        self._created_nodes['distribute'] = distribute

        x += 250

        # === OPTIONAL: NOISE ANIMATION ===
        if self._noise_settings['enabled']:
            # Scene time for animation
            scene_time = nk.n(
                "GeometryNodeInputSceneTime",
                "Scene Time",
                x=x, y=-100
            )
            self._created_nodes['scene_time'] = scene_time

            # Multiply time by speed
            time_mult = nk.n("ShaderNodeMath", "Time × Speed", x=x + 150, y=-100)
            time_mult.operation = 'MULTIPLY'
            nk.link(group_in.outputs["Noise Speed"], time_mult.inputs[0])
            nk.link(scene_time.outputs["Seconds"], time_mult.inputs[1])

            x_noise = x + 300

            # 4D Noise texture for position offset
            # KB Reference: Section 13 - 4D noise for animation
            noise = nk.n(
                "ShaderNodeTexNoise",
                "Position Noise",
                x=x_noise, y=0
            )
            noise.inputs["Dimensions"].default_value = '4D'
            noise.inputs["Detail"].default_value = self._noise_settings['detail']
            nk.link(group_in.outputs["Noise Scale"], noise.inputs["Scale"])
            nk.link(time_mult.outputs[0], noise.inputs["W"])
            self._created_nodes['noise'] = noise

            # Scale noise output
            noise_scale = nk.n("ShaderNodeMath", "Noise Scale", x=x_noise + 200, y=0)
            noise_scale.operation = 'MULTIPLY'
            nk.link(noise.outputs["Color"], noise_scale.inputs[0])  # Use color for 3D
            # Actually we need vector scale
            noise_vec_scale = nk.n("ShaderNodeVectorMath", "Noise Strength", x=x_noise + 200, y=0)
            noise_vec_scale.operation = 'SCALE'
            # Convert scalar strength to vector for scale
            nk.link(group_in.outputs["Noise Strength"], noise_vec_scale.inputs["Scale"])
            nk.link(noise.outputs["Color"], noise_vec_scale.inputs["Vector"])

            # Set position with noise offset
            set_pos = nk.n(
                "GeometryNodeSetPosition",
                "Animate Points",
                x=x_noise + 400, y=100
            )
            nk.link(distribute.outputs["Points"], set_pos.inputs["Geometry"])
            nk.link(noise_vec_scale.outputs["Vector"], set_pos.inputs["Offset"])

            points_out = set_pos
            x = x_noise + 600
        else:
            points_out = distribute

        self._created_nodes['points_out'] = points_out

        # === POINT TO SDF GRID (Blender 5.0+) ===
        # KB Reference: Section 13 - THE KEY NODE
        sdf_grid = nk.n(
            "GeometryNodePointsToSDFGrid",
            "Point to SDF Grid",
            x=x, y=100
        )
        nk.link(points_out.outputs["Points"], sdf_grid.inputs["Points"])
        nk.link(group_in.outputs["Point Radius"], sdf_grid.inputs["Radius"])
        nk.link(group_in.outputs["Voxel Size"], sdf_grid.inputs["Voxel Size"])
        self._created_nodes['sdf_grid'] = sdf_grid

        x += 250

        # === GRID TO MESH ===
        # KB Reference: Section 13 - Convert back to renderable geometry
        grid_to_mesh = nk.n(
            "GeometryNodeGridToMesh",
            "Grid to Mesh",
            x=x, y=100
        )
        nk.link(sdf_grid.outputs["SDF Grid"], grid_to_mesh.inputs["SDF Grid"])
        nk.link(group_in.outputs["Voxel Size"], grid_to_mesh.inputs["Voxel Size"])
        self._created_nodes['grid_to_mesh'] = grid_to_mesh

        x += 250

        # === SMOOTH GEOMETRY ===
        # KB Reference: Section 13 - Iterations control goopiness
        smooth = nk.n(
            "GeometryNodeSmoothGeometry",
            "Smooth",
            x=x, y=100
        )
        nk.link(group_in.outputs["Smooth Iterations"], smooth.inputs["Iterations"])
        nk.link(grid_to_mesh.outputs["Mesh"], smooth.inputs["Geometry"])
        self._created_nodes['smooth'] = smooth

        x += 250

        # === NORMAL NODE ===
        normal = nk.n(
            "GeometryNodeInputNormal",
            "Normal",
            x=x, y=-50
        )
        nk.link(smooth.outputs["Geometry"], normal.inputs["Geometry"])
        self._created_nodes['normal'] = normal

        x += 200

        # === BLUR ATTRIBUTE (NORMALS) ===
        # KB Reference: Section 13 - Fix circular artifacts
        blur_normal = nk.n(
            "GeometryNodeBlurAttribute",
            "Blur Normals",
            x=x, y=100
        )
        blur_normal.inputs["Data Type"].default_value = 'FLOAT_VECTOR'
        nk.link(group_in.outputs["Normal Blur Iterations"], blur_normal.inputs["Iterations"])
        nk.link(smooth.outputs["Geometry"], blur_normal.inputs["Geometry"])
        nk.link(normal.outputs["Normal"], blur_normal.inputs["Value"])
        self._created_nodes['blur_normal'] = blur_normal

        x += 250

        # === SET MESH NORMAL ===
        # KB Reference: Section 13 - Apply blurred normals
        set_normal = nk.n(
            "GeometryNodeSetMeshNormal",
            "Set Normals",
            x=x, y=100
        )
        set_normal.mode = 'FREE'
        nk.link(blur_normal.outputs["Geometry"], set_normal.inputs["Geometry"])
        nk.link(blur_normal.outputs["Value"], set_normal.inputs["Custom Normal"])
        self._created_nodes['set_normal'] = set_normal

        x += 200

        # === SET SHADE SMOOTH ===
        shade_smooth = nk.n(
            "GeometryNodeSetShadeSmooth",
            "Shade Smooth",
            x=x, y=100
        )
        shade_smooth.inputs["Shade Smooth"].default_value = True
        nk.link(set_normal.outputs["Geometry"], shade_smooth.inputs["Geometry"])
        self._created_nodes['shade_smooth'] = shade_smooth

        x += 200

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=100)
        nk.link(shade_smooth.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class VoxelSizePresets:
    """
    Preset voxel sizes for different quality levels.

    Cross-references:
    - KB Section 13: Voxel size controls quality
    """

    VIEWPORT_FAST = 0.08      # Fast preview
    VIEWPORT_MEDIUM = 0.04    # Default viewport
    VIEWPORT_QUALITY = 0.02   # High quality viewport
    RENDER_PREVIEW = 0.01     # Preview render
    RENDER_FINAL = 0.002      # Production quality
    RENDER_ULTRA = 0.001      # Maximum quality (slow)

    @staticmethod
    def get_recommended(scale: float = 1.0) -> dict:
        """
        Get recommended voxel sizes for a given scene scale.

        Args:
            scale: Scene scale multiplier (1.0 = default)

        Returns:
            Dict with viewport and render recommendations
        """
        return {
            "viewport": 0.04 * scale,
            "render": 0.002 * scale,
            "description": f"For scale {scale}, use viewport={0.04 * scale:.4f}, render={0.002 * scale:.4f}"
        }


class MetaballPresets:
    """
    Preset configurations for common metaball effects.

    Cross-references:
    - KB Section 13: Quality settings
    """

    @staticmethod
    def organic_blobs() -> dict:
        """Configuration for organic, goopy blobs."""
        return {
            "radius": 0.5,
            "density": 10.0,
            "smooth_iterations": 100,
            "normal_blur_iterations": 30,
            "noise_scale": 1.0,
            "noise_detail": 0.0,  # Smooth
        }

    @staticmethod
    def water_droplets() -> dict:
        """Configuration for water droplet effect."""
        return {
            "radius": 0.3,
            "density": 20.0,
            "smooth_iterations": 50,
            "normal_blur_iterations": 30,
            "noise_scale": 0.5,
            "noise_detail": 1.0,
        }

    @staticmethod
    def lava_flow() -> dict:
        """Configuration for lava/magma effect."""
        return {
            "radius": 0.8,
            "density": 5.0,
            "smooth_iterations": 150,
            "normal_blur_iterations": 20,
            "noise_scale": 2.0,
            "noise_detail": 3.0,
        }


# Convenience functions
def create_metaballs(
    obj: bpy.types.Object,
    radius: float = 0.5,
    smooth: int = 50
) -> SDFMetaballs:
    """
    Quick setup for SDF metaballs on an object.

    Args:
        obj: Container mesh object
        radius: Point/blob radius
        smooth: Smoothing iterations

    Returns:
        Configured SDFMetaballs with built node tree
    """
    metaballs = SDFMetaballs.from_object(obj)
    metaballs.set_radius(radius)
    metaballs.set_smooth_iterations(smooth)
    metaballs.build()
    return metaballs


def create_animated_metaballs(
    obj: bpy.types.Object,
    speed: float = 0.3,
    strength: float = 0.2
) -> SDFMetaballs:
    """
    Quick setup for animated SDF metaballs.

    Args:
        obj: Container mesh object
        speed: Animation speed
        strength: Movement strength

    Returns:
        Configured SDFMetaballs with animation
    """
    metaballs = SDFMetaballs.from_object(obj)
    metaballs.set_radius(0.5)
    metaballs.set_smooth_iterations(50)
    metaballs.animate_with_noise(scale=1.0, speed=speed, strength=strength)
    metaballs.build()
    return metaballs


class MetaballHUD:
    """
    Heads-Up Display for SDF metaball visualization.

    Cross-references:
    - KB Section 13: SDF Volume Metaballs
    """

    @staticmethod
    def display_settings(
        radius: float = 0.5,
        voxel_size: float = 0.04,
        point_density: float = 10.0,
        smooth_iterations: int = 30,
        normal_blur_iterations: int = 30,
        noise_scale: float = 1.0,
        noise_speed: float = 0.3,
        noise_strength: float = 0.2
    ) -> str:
        """Display current metaball settings."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        SDF METABALL SETTINGS         ║",
            "╠══════════════════════════════════════╣",
            f"║ Point Radius:  {radius:>20.2f} ║",
            f"║ Voxel Size:    {voxel_size:>20.4f} ║",
            f"║ Point Density: {point_density:>20.1f} ║",
            "╠══════════════════════════════════════╣",
            "║ SMOOTHING                            ║",
            f"║   Iterations:  {smooth_iterations:>20} ║",
            f"║   Normal Blur: {normal_blur_iterations:>20} ║",
            "╠══════════════════════════════════════╣",
            "║ NOISE ANIMATION                      ║",
            f"║   Scale:       {noise_scale:>20.2f} ║",
            f"║   Speed:       {noise_speed:>20.2f} ║",
            f"║   Strength:    {noise_strength:>20.2f} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_voxel_guide() -> str:
        """Display voxel size quality guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║         VOXEL SIZE GUIDE             ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  VIEWPORT (fast preview):            ║",
            "║    0.08  = Fast (low quality)        ║",
            "║    0.04  = Medium (default)          ║",
            "║    0.02  = High quality              ║",
            "║                                      ║",
            "║  RENDER (production):                ║",
            "║    0.01  = Preview render            ║",
            "║    0.002 = Final render              ║",
            "║    0.001 = Ultra quality (slow)      ║",
            "║                                      ║",
            "║  TIP: Use 0.04 while working,        ║",
            "║       switch to 0.002 for render     ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for SDF metaballs."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        METABALL NODE FLOW            ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║  [Mesh to Volume]                    ║",
            "║       │                              ║",
            "║  [Distribute Points in Volume]       ║",
            "║       │                              ║",
            "║  [Optional: Set Position + Noise]    ║",
            "║       │                              ║",
            "║  ╔═══════════════════════════════╗   ║",
            "║  ║  POINT TO SDF GRID (5.0+)    ║   ║",
            "║  ║  THE KEY NODE!               ║   ║",
            "║  ╚═══════════════════════════════╝   ║",
            "║       │                              ║",
            "║  [Grid to Mesh]                      ║",
            "║       │                              ║",
            "║  [Smooth Geometry] ← iterations      ║",
            "║       │                              ║",
            "║  [Input Normal]                      ║",
            "║       │                              ║",
            "║  [Blur Attribute] ← fix artifacts    ║",
            "║       │                              ║",
            "║  [Set Mesh Normal]                   ║",
            "║       │                              ║",
            "║  [Set Shade Smooth]                  ║",
            "║       │                              ║",
            "║  [Group Output]                      ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for metaball setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║     METABALL PRE-FLIGHT CHECKLIST    ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Container mesh created            ║",
            "║    (Icosphere works well)            ║",
            "║                                      ║",
            "║  □ Voxel size set appropriately      ║",
            "║    (0.04 viewport, 0.002 render)     ║",
            "║                                      ║",
            "║  □ Point radius configured           ║",
            "║    (0.3-0.8 for typical blobs)       ║",
            "║                                      ║",
            "║  □ Smooth iterations set             ║",
            "║    (50-100 for goopy, 20-30 clean)   ║",
            "║                                      ║",
            "║  □ Normal blur enabled               ║",
            "║    (30 iterations fixes artifacts)   ║",
            "║                                      ║",
            "║  □ Shade smooth enabled              ║",
            "║                                      ║",
            "║  □ Optional: Noise animation added   ║",
            "║    (4D noise for blob movement)      ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_goopiness_guide() -> str:
        """Display goopiness (smoothing) guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        GOOPINESS GUIDE               ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  Smooth Iterations control blending: ║",
            "║                                      ║",
            "║    2-10   = Minimal blending         ║",
            "║             Distinct blobs           ║",
            "║                                      ║",
            "║    30-50  = Moderate blending        ║",
            "║             Soft transitions         ║",
            "║                                      ║",
            "║    100+   = Maximum blending         ║",
            "║             Very goopy, organic      ║",
            "║                                      ║",
            "║  Normal Blur (30 typical):           ║",
            "║    Fixes circular artifacts          ║",
            "║    Creates smooth shading            ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_metaball_settings(**kwargs) -> None:
    """Print metaball settings to console."""
    print(MetaballHUD.display_settings(**kwargs))
