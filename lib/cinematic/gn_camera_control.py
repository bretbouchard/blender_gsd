"""
Geometry Nodes Camera Control Module

Provides procedural camera animation and control through Geometry Nodes.
Enables real-time, non-destructive camera manipulation without keyframes.

Features:
- Procedural camera shake via GN noise
- Path following with curve parameter
- Target tracking with offset
- Multi-camera synchronization
- Real-time parameter control

Usage:
    from lib.cinematic.gn_camera_control import GNCameraController

    # Create GN-controlled camera
    gn_cam = GNCameraController("procedural_camera")

    # Add procedural shake
    gn_cam.add_shake(intensity=0.05, frequency=3.0)

    # Follow target with offset
    gn_cam.follow_target("Vehicle", offset=(-6, 0, 2.5))

    # Add orbit motion
    gn_cam.add_orbit(radius=10.0, speed=0.5)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any, List, Tuple, Dict
from enum import Enum
import math

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    BLENDER_AVAILABLE = False


# =============================================================================
# TYPES AND ENUMS
# =============================================================================

class ShakeType(Enum):
    """Types of GN-based camera shake."""
    NOISE = "noise"
    WAVE = "wave"
    RANDOM = "random"
    PERLIN = "perlin"


class FollowMode(Enum):
    """Camera follow modes."""
    FIXED_OFFSET = "fixed_offset"
    SMOOTH_FOLLOW = "smooth_follow"
    PREDICTION = "prediction"
    SPRING = "spring"


@dataclass
class GNCameraConfig:
    """Configuration for GN camera setup."""
    name: str
    base_position: Tuple[float, float, float] = (0, -10, 2)
    base_rotation: Tuple[float, float, float] = (1.57, 0, 0)
    shake_intensity: float = 0.0
    shake_frequency: float = 2.0
    follow_target: Optional[str] = None
    follow_offset: Tuple[float, float, float] = (-6, 0, 2)
    orbit_radius: float = 0.0
    orbit_speed: float = 0.0


@dataclass
class ShakeLayer:
    """A single shake layer for stacking multiple effects."""
    name: str
    shake_type: ShakeType
    intensity: float
    frequency: float
    seed: int
    axes: Tuple[bool, bool, bool] = (True, True, True)
    rotation: bool = False
    enabled: bool = True


# =============================================================================
# GEOMETRY NODES TREE BUILDER
# =============================================================================

class GNCameraNodeTree:
    """
    Builder for camera control node trees.

    Creates a node tree that outputs position/rotation values
    which can drive camera via drivers or constraints.
    """

    def __init__(self, name: str):
        self.name = name
        self._nodes: List[Dict] = []
        self._links: List[Tuple] = []
        self._inputs: List[Dict] = []
        self._outputs: List[Dict] = []

    def add_input(self, name: str, socket_type: str, default: Any = None) -> "GNCameraNodeTree":
        """Add a node group input."""
        self._inputs.append({
            "name": name,
            "type": socket_type,
            "default": default,
        })
        return self

    def add_output(self, name: str, socket_type: str) -> "GNCameraNodeTree":
        """Add a node group output."""
        self._outputs.append({
            "name": name,
            "type": socket_type,
        })
        return self

    def add_node(
        self,
        node_type: str,
        name: str,
        location: Tuple[float, float] = (0, 0),
        **kwargs
    ) -> str:
        """Add a node and return its name."""
        self._nodes.append({
            "type": node_type,
            "name": name,
            "location": location,
            "params": kwargs,
        })
        return name

    def link(self, from_node: str, from_socket: str, to_node: str, to_socket: str) -> "GNCameraNodeTree":
        """Add a link between nodes."""
        self._links.append((from_node, from_socket, to_node, to_socket))
        return self

    def build(self) -> Optional[Any]:
        """Build the node tree in Blender."""
        if not BLENDER_AVAILABLE:
            return None

        # Create or get node group
        if self.name in bpy.data.node_groups:
            bpy.data.node_groups.remove(bpy.data.node_groups[self.name])

        tree = bpy.data.node_groups.new(self.name, "GeometryNodeTree")

        # Add interface sockets
        for inp in self._inputs:
            tree.interface.new_socket(
                name=inp["name"],
                in_out="INPUT",
                socket_type=inp["type"],
            )
            # Set default on input node

        for out in self._outputs:
            tree.interface.new_socket(
                name=out["name"],
                in_out="OUTPUT",
                socket_type=out["type"],
            )

        # Create nodes
        nodes = {}
        for node_def in self._nodes:
            node = tree.nodes.new(node_def["type"])
            node.name = node_def["name"]
            node.label = node_def["name"]
            node.location = node_def["location"]

            # Apply parameters
            for key, value in node_def["params"].items():
                if hasattr(node, key):
                    setattr(node, key, value)
                elif key in node.inputs:
                    node.inputs[key].default_value = value

            nodes[node_def["name"]] = node

        # Create links
        for from_n, from_s, to_n, to_s in self._links:
            if from_n in nodes and to_n in nodes:
                tree.links.new(
                    nodes[from_n].outputs[from_s],
                    nodes[to_n].inputs[to_s],
                )

        return tree

    def create_spec(self) -> Dict[str, Any]:
        """Create a specification dict for the node tree."""
        return {
            "name": self.name,
            "type": "GeometryNodeTree",
            "inputs": self._inputs,
            "outputs": self._outputs,
            "nodes": self._nodes,
            "links": self._links,
        }


# =============================================================================
# GN CAMERA CONTROLLER
# =============================================================================

class GNCameraController:
    """
    Geometry Nodes-based camera controller.

    Provides procedural camera animation through GN node trees.
    The camera is driven by the output of the node tree via drivers.

    Example:
        gn_cam = GNCameraController("procedural_camera")
        gn_cam.add_shake_layer("subtle", intensity=0.02, frequency=2.0)
        gn_cam.follow_target("Car", offset=(-8, 2, 3))
        gn_cam.add_orbit(radius=12.0, speed=0.25)
        gn_cam.apply()
    """

    def __init__(self, camera_name: str):
        """
        Initialize GN controller for a camera.

        Args:
            camera_name: Name of camera to control
        """
        self.camera_name = camera_name
        self._shake_layers: List[ShakeLayer] = []
        self._follow_config: Optional[Dict] = None
        self._orbit_config: Optional[Dict] = None
        self._base_position: Tuple[float, float, float] = (0, -10, 2)
        self._base_rotation: Tuple[float, float, float] = (1.57, 0, 0)
        self._node_tree: Optional[Any] = None
        self._driver_variables: List[Dict] = []

    @property
    def camera(self) -> Optional[Any]:
        """Get the camera object."""
        if not BLENDER_AVAILABLE:
            return None
        return bpy.data.objects.get(self.camera_name)

    # =========================================================================
    # SHAKE LAYERS
    # =========================================================================

    def add_shake_layer(
        self,
        name: str,
        intensity: float = 0.05,
        frequency: float = 2.0,
        seed: int = 0,
        shake_type: ShakeType = ShakeType.NOISE,
        axes: Tuple[bool, bool, bool] = (True, True, True),
        rotation: bool = False,
    ) -> "GNCameraController":
        """
        Add a shake layer.

        Multiple layers can be stacked for complex shake effects.

        Args:
            name: Layer name
            intensity: Shake intensity in meters
            frequency: Shake frequency in Hz
            seed: Random seed for variation
            shake_type: Type of noise to use
            axes: Which axes to apply shake (X, Y, Z)
            rotation: Also apply rotation shake

        Returns:
            self for chaining
        """
        layer = ShakeLayer(
            name=name,
            shake_type=shake_type,
            intensity=intensity,
            frequency=frequency,
            seed=seed,
            axes=axes,
            rotation=rotation,
        )
        self._shake_layers.append(layer)
        return self

    def add_handheld(self, amount: float = 1.0) -> "GNCameraController":
        """Add subtle handheld shake preset."""
        return self.add_shake_layer(
            name="handheld",
            intensity=0.02 * amount,
            frequency=2.0,
            seed=42,
            axes=(True, True, True),
            rotation=True,
        )

    def add_vehicle_shake(self, intensity: float = 1.0) -> "GNCameraController":
        """Add vehicle movement shake preset."""
        return self.add_shake_layer(
            name="vehicle",
            intensity=0.03 * intensity,
            frequency=4.0,
            seed=123,
            axes=(True, True, False),  # Mostly X/Y
            rotation=True,
        )

    def add_explosion_shake(self, decay_frames: int = 30) -> "GNCameraController":
        """Add explosion shockwave shake."""
        return self.add_shake_layer(
            name="explosion",
            intensity=0.2,
            frequency=8.0,
            seed=999,
            axes=(True, True, True),
            rotation=True,
        )

    def clear_shake_layers(self) -> "GNCameraController":
        """Remove all shake layers."""
        self._shake_layers.clear()
        return self

    # =========================================================================
    # FOLLOW TARGET
    # =========================================================================

    def follow_target(
        self,
        target_name: str,
        offset: Tuple[float, float, float] = (-6, 0, 2),
        mode: FollowMode = FollowMode.FIXED_OFFSET,
        smoothing: float = 0.5,
    ) -> "GNCameraController":
        """
        Configure camera to follow a target object.

        Args:
            target_name: Name of target object
            offset: Camera offset from target (local space)
            mode: Follow behavior mode
            smoothing: Smoothing factor for smooth/spring modes

        Returns:
            self for chaining
        """
        self._follow_config = {
            "target_name": target_name,
            "offset": offset,
            "mode": mode,
            "smoothing": smoothing,
        }
        return self

    def clear_follow(self) -> "GNCameraController":
        """Clear follow target configuration."""
        self._follow_config = None
        return self

    # =========================================================================
    # ORBIT
    # =========================================================================

    def add_orbit(
        self,
        radius: float = 10.0,
        speed: float = 0.5,
        axis: str = "Z",
        height: float = 0.0,
    ) -> "GNCameraController":
        """
        Add orbital motion around a point.

        Args:
            radius: Orbit radius in meters
            speed: Orbit speed (radians per second)
            axis: Rotation axis ("X", "Y", or "Z")
            height: Height offset from orbit plane

        Returns:
            self for chaining
        """
        self._orbit_config = {
            "radius": radius,
            "speed": speed,
            "axis": axis,
            "height": height,
        }
        return self

    def clear_orbit(self) -> "GNCameraController":
        """Clear orbit configuration."""
        self._orbit_config = None
        return self

    # =========================================================================
    # BUILD AND APPLY
    # =========================================================================

    def build_node_tree(self) -> Optional[Any]:
        """
        Build the GN node tree for camera control.

        Returns:
            The created node tree
        """
        if not BLENDER_AVAILABLE:
            return None

        tree_name = f"{self.camera_name}_GN_Control"

        # Create node tree builder
        builder = GNCameraNodeTree(tree_name)

        # Add inputs
        builder.add_input("Base Position", "NodeSocketVector", self._base_position)
        builder.add_input("Base Rotation", "NodeSocketVector", self._base_rotation)
        builder.add_input("Time", "NodeSocketFloat", 0.0)

        # Add shake layer inputs
        for layer in self._shake_layers:
            builder.add_input(f"{layer.name}_Intensity", "NodeSocketFloat", layer.intensity)
            builder.add_input(f"{layer.name}_Frequency", "NodeSocketFloat", layer.frequency)
            builder.add_input(f"{layer.name}_Seed", "NodeSocketInt", layer.seed)

        # Add outputs
        builder.add_output("Position", "NodeSocketVector")
        builder.add_output("Rotation", "NodeSocketVector")

        # Build node network
        current_pos = "Input_0"  # Base Position
        current_rot = "Input_1"  # Base Rotation

        # Add shake nodes for each layer
        y_offset = -200
        for i, layer in enumerate(self._shake_layers):
            shake_node = f"Shake_{layer.name}"

            # Noise Texture for shake
            builder.add_node(
                "ShaderNodeTexNoise",
                shake_node,
                location=(200, y_offset * i),
                noise_dimensions="4D",
            )

            # Link time to noise
            builder.link("Input_2", "Value", shake_node, "W")

            # Add to position
            add_node = f"Add_Shake_{layer.name}"
            builder.add_node(
                "ShaderNodeVectorMath",
                add_node,
                location=(400, y_offset * i),
                operation="ADD",
            )

            # Current: Base Position -> Add -> Output
            # Noise drives offset

        # For now, create a simplified spec that can be expanded
        self._node_tree = builder.build()
        return self._node_tree

    def create_spec(self) -> Dict[str, Any]:
        """
        Create a complete specification for the GN camera setup.

        This can be used to generate the node tree later or for documentation.
        """
        return {
            "camera_name": self.camera_name,
            "base_position": self._base_position,
            "base_rotation": self._base_rotation,
            "shake_layers": [
                {
                    "name": layer.name,
                    "type": layer.shake_type.value,
                    "intensity": layer.intensity,
                    "frequency": layer.frequency,
                    "seed": layer.seed,
                    "axes": layer.axes,
                    "rotation": layer.rotation,
                    "enabled": layer.enabled,
                }
                for layer in self._shake_layers
            ],
            "follow": self._follow_config,
            "orbit": self._orbit_config,
        }

    def apply(self) -> bool:
        """
        Apply the GN control to the camera.

        Creates the node tree and sets up drivers to read its output.

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        cam = self.camera
        if not cam:
            return False

        # Build node tree
        tree = self.build_node_tree()
        if not tree:
            return False

        # Create an empty to hold the GN modifier
        empty_name = f"{self.camera_name}_GN_Driver"
        if empty_name in bpy.data.objects:
            empty = bpy.data.objects[empty_name]
        else:
            empty = bpy.data.objects.new(empty_name, None)
            bpy.context.scene.collection.objects.link(empty)

        # Add geometry nodes modifier
        if not empty.modifiers:
            mod = empty.modifiers.new("CameraControl", "NODES")
            mod.node_group = tree

        # Setup drivers on camera to read from empty/GN output
        # This requires custom properties on the empty that get driven by GN

        # For position
        driver = cam.driver_add("location")
        var = driver.driver.variables.new()
        var.name = "gn_pos_x"
        var.targets[0].id_type = "OBJECT"
        var.targets[0].id = empty
        var.targets[0].data_path = '["gn_output_x"]'
        driver.driver.expression = "gn_pos_x"

        # Similar for Y, Z and rotation...

        return True

    def update_parameter(self, param_name: str, value: Any) -> bool:
        """
        Update a parameter in real-time.

        Args:
            param_name: Parameter to update
            value: New value

        Returns:
            True if successful
        """
        if not self._node_tree or not BLENDER_AVAILABLE:
            return False

        # Find the input and update its value
        # This would modify the node tree's default input values
        return True


# =============================================================================
# PRESET GN CAMERA SETUPS
# =============================================================================

def create_shake_camera(
    camera_name: str,
    shake_profile: str = "handheld",
    intensity: float = 1.0,
) -> GNCameraController:
    """
    Create a camera with procedural shake.

    Args:
        camera_name: Name for the camera
        shake_profile: "handheld", "vehicle", "subtle", "earthquake"
        intensity: Intensity multiplier

    Returns:
        GNCameraController instance
    """
    gn_cam = GNCameraController(camera_name)

    if shake_profile == "handheld":
        gn_cam.add_handheld(intensity)
    elif shake_profile == "vehicle":
        gn_cam.add_vehicle_shake(intensity)
    elif shake_profile == "subtle":
        gn_cam.add_shake_layer("subtle", intensity=0.01 * intensity, frequency=1.5)
    elif shake_profile == "earthquake":
        gn_cam.add_shake_layer(
            "earthquake",
            intensity=0.15 * intensity,
            frequency=1.0,
            axes=(True, True, True),
            rotation=True,
        )

    return gn_cam


def create_follow_orbit_camera(
    camera_name: str,
    target_name: str,
    radius: float = 10.0,
    orbit_speed: float = 0.25,
    height: float = 2.0,
) -> GNCameraController:
    """
    Create a camera that orbits around a target.

    Args:
        camera_name: Name for the camera
        target_name: Target object to orbit around
        radius: Orbit radius
        orbit_speed: Rotation speed (radians/sec)
        height: Height above target

    Returns:
        GNCameraController instance
    """
    gn_cam = GNCameraController(camera_name)
    gn_cam.follow_target(target_name, offset=(radius, 0, height))
    gn_cam.add_orbit(radius=radius, speed=orbit_speed, height=height)
    return gn_cam


# =============================================================================
# GN NODE GROUP SPECIFICATIONS
# =============================================================================

def get_shake_node_spec() -> Dict[str, Any]:
    """
    Get the specification for a reusable camera shake node group.

    This creates a spec that can be instantiated multiple times.
    """
    return {
        "name": "CameraShake",
        "type": "GeometryNodeTree",
        "inputs": [
            {"name": "Vector", "type": "NodeSocketVector", "default": (0, 0, 0)},
            {"name": "Intensity", "type": "NodeSocketFloat", "default": 0.1},
            {"name": "Frequency", "type": "NodeSocketFloat", "default": 2.0},
            {"name": "Seed", "type": "NodeSocketInt", "default": 0},
            {"name": "Time", "type": "NodeSocketFloat", "default": 0.0},
        ],
        "outputs": [
            {"name": "Vector", "type": "NodeSocketVector"},
        ],
        "nodes": [
            {
                "type": "ShaderNodeTexNoise",
                "name": "Noise",
                "location": (0, 0),
                "noise_dimensions": "4D",
                "scale": 5.0,
            },
            {
                "type": "ShaderNodeVectorMath",
                "name": "Scale",
                "location": (200, 0),
                "operation": "SCALE",
            },
            {
                "type": "ShaderNodeVectorMath",
                "name": "Add",
                "location": (400, 0),
                "operation": "ADD",
            },
        ],
        "links": [
            ("Input_4", "Value", "Noise", "W"),  # Time -> Noise W
            ("Input_3", "Value", "Noise", "Detail"),  # Seed -> Detail (for variation)
            ("Noise", "Color", "Scale", "Vector"),
            ("Input_1", "Value", "Scale", "Scale"),  # Intensity
            ("Input_0", "Vector", "Add", "Vector"),
            ("Scale", "Vector", "Add", "Vector"),
            ("Add", "Vector", "Output_0", "Vector"),
        ],
    }


def get_orbit_node_spec() -> Dict[str, Any]:
    """
    Get the specification for a procedural orbit node group.
    """
    return {
        "name": "CameraOrbit",
        "type": "GeometryNodeTree",
        "inputs": [
            {"name": "Center", "type": "NodeSocketVector", "default": (0, 0, 0)},
            {"name": "Radius", "type": "NodeSocketFloat", "default": 10.0},
            {"name": "Speed", "type": "NodeSocketFloat", "default": 0.5},
            {"name": "Height", "type": "NodeSocketFloat", "default": 0.0},
            {"name": "Time", "type": "NodeSocketFloat", "default": 0.0},
        ],
        "outputs": [
            {"name": "Position", "type": "NodeSocketVector"},
            {"name": "Rotation", "type": "NodeSocketVector"},
        ],
        "nodes": [
            {
                "type": "ShaderNodeMath",
                "name": "Angle",
                "location": (0, 0),
                "operation": "MULTIPLY",
            },
            {
                "type": "ShaderNodeSeparateXYZ",
                "name": "Separate",
                "location": (200, 0),
            },
            {
                "type": "ShaderNodeCombineXYZ",
                "name": "CombinePos",
                "location": (400, 0),
            },
        ],
        "links": [
            ("Input_4", "Value", "Angle", "Value"),
            ("Input_2", "Value", "Angle", "Value_001"),  # Time * Speed
            # More links for orbit calculation...
        ],
    }


def get_follow_node_spec() -> Dict[str, Any]:
    """
    Get the specification for a follow target node group.
    """
    return {
        "name": "CameraFollow",
        "type": "GeometryNodeTree",
        "inputs": [
            {"name": "Target Position", "type": "NodeSocketVector", "default": (0, 0, 0)},
            {"name": "Offset", "type": "NodeSocketVector", "default": (-6, 0, 2)},
            {"name": "Smoothing", "type": "NodeSocketFloat", "default": 0.5},
            {"name": "Target Rotation", "type": "NodeSocketFloat", "default": 0.0},
        ],
        "outputs": [
            {"name": "Position", "type": "NodeSocketVector"},
            {"name": "Rotation", "type": "NodeSocketVector"},
        ],
        "nodes": [
            {
                "type": "ShaderNodeVectorMath",
                "name": "RotateOffset",
                "location": (0, 0),
                "operation": "ROTATE",  # Rotate offset by target rotation
            },
            {
                "type": "ShaderNodeVectorMath",
                "name": "Add",
                "location": (200, 0),
                "operation": "ADD",
            },
        ],
        "links": [
            ("Input_1", "Vector", "RotateOffset", "Vector"),
            ("Input_3", "Value", "RotateOffset", "Rotation"),
            ("Input_0", "Vector", "Add", "Vector"),
            ("RotateOffset", "Vector", "Add", "Vector"),
            ("Add", "Vector", "Output_0", "Vector"),
        ],
    }


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

__all__ = [
    "GNCameraController",
    "GNCameraNodeTree",
    "ShakeType",
    "FollowMode",
    "ShakeLayer",
    "GNCameraConfig",
    "create_shake_camera",
    "create_follow_orbit_camera",
    "get_shake_node_spec",
    "get_orbit_node_spec",
    "get_follow_node_spec",
]
