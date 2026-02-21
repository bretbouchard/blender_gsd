"""
Auto-Rigging System for Launch Control

One-click vehicle rigging with automatic component detection,
constraint application, and driver setup.

Features:
- Automatic wheel detection by name, geometry, or position
- Multiple suspension types (independent, solid axle, etc.)
- Front/rear/all-wheel steering configurations
- Constraint-based rigging for animation
- Driver setup for procedural control
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Union

# Type hints for Blender API (runtime optional)
try:
    import bpy
    from mathutils import Vector, Matrix

    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    bpy = None  # type: ignore
    Vector = Any  # type: ignore
    Matrix = Any  # type: ignore


class SuspensionType(Enum):
    """Available suspension types for vehicle rigging."""

    INDEPENDENT = "independent"
    DOUBLE_WISHBONE = "double_wishbone"
    MACPHERSON = "macpherson"
    SOLID_AXLE = "solid_axle"
    TORSION_BEAM = "torsion_beam"
    AIR_SUSPENSION = "air_suspension"
    MULTI_LINK = "multi_link"


class SteeringType(Enum):
    """Available steering configurations."""

    FRONT = "front"
    REAR = "rear"
    FOUR_WHEEL = "four_wheel"
    CRAB = "crab"
    NONE = "none"


@dataclass
class ComponentDetectionResult:
    """Results from automatic component detection."""

    wheels: list[Any] = field(default_factory=list)
    axles: list[Any] = field(default_factory=list)
    body: Optional[Any] = None
    steering_column: Optional[Any] = None
    wheel_positions: dict[str, Vector] = field(default_factory=dict)
    wheel_radii: dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.0
    detection_method: str = "auto"
    warnings: list[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if detection found valid components."""
        return len(self.wheels) >= 2 and self.body is not None

    def get_wheel_by_position(self, position: str) -> Optional[Any]:
        """Get wheel by position identifier (FL, FR, RL, RR)."""
        position_map = {
            "front_left": ["FL", "front_left", "front_left_wheel"],
            "front_right": ["FR", "front_right", "front_right_wheel"],
            "rear_left": ["RL", "rear_left", "rear_left_wheel"],
            "rear_right": ["RR", "rear_right", "rear_right_wheel"],
        }
        for key, aliases in position_map.items():
            if position in aliases:
                for wheel in self.wheels:
                    wheel_name = wheel.name.lower() if hasattr(wheel, "name") else ""
                    if any(alias.lower() in wheel_name for alias in aliases):
                        return wheel
        return None


@dataclass
class RigConfiguration:
    """Configuration for vehicle rig generation."""

    suspension_type: SuspensionType = SuspensionType.INDEPENDENT
    steering_type: SteeringType = SteeringType.FRONT
    create_steering_controller: bool = True
    controller_location: tuple[float, float, float] = (0, -0.3, 0.8)
    controller_shape: str = "steering_wheel"
    wheel_naming_pattern: str = "auto"
    axle_naming_pattern: str = "auto"
    auto_parent: bool = True
    create_suspension_bones: bool = True
    suspension_travel: float = 0.3
    spring_stiffness: float = 25000.0
    damping: float = 1500.0
    max_steering_angle: float = 35.0
    ackermann_enabled: bool = True
    four_wheel_steering_ratio: float = 0.0
    create_custom_properties: bool = True
    rig_name: str = "vehicle_rig"


class WheelDetector:
    """Automatic wheel detection utility class.

    Provides multiple detection strategies:
    - By name pattern matching
    - By geometry analysis (cylindrical shapes)
    - By expected position matching

    Example:
        # Detect wheels by name pattern
        wheels = WheelDetector.by_name(vehicle, r".*wheel.*")

        # Detect by geometry (cylindrical objects within radius range)
        wheels = WheelDetector.by_geometry(vehicle, (0.2, 0.5))

        # Detect by expected positions
        expected = [(1, 1.5, 0.4), (1, -1.5, 0.4), (-1, 1.5, 0.4), (-1, -1.5, 0.4)]
        wheels = WheelDetector.by_position(vehicle, expected)
    """

    # Common wheel naming patterns
    DEFAULT_PATTERNS = [
        r".*wheel.*",
        r".*_wh_.*",
        r".*_whe?el.*",
        r".*tire.*",
        r".*tyre.*",
        r".*(fl|fr|rl|rr).*wheel.*",
        r".*wheel.*(fl|fr|rl|rr).*",
        r".*(front|rear|left|right).*wheel.*",
    ]

    @staticmethod
    def by_name(
        obj: Any, pattern: Union[str, list[str], None] = None
    ) -> list[Any]:
        """Detect wheels by name pattern matching.

        Args:
            obj: Parent object or collection to search within
            pattern: Regex pattern(s) to match wheel names.
                    If None, uses default patterns.

        Returns:
            List of detected wheel objects

        Example:
            wheels = WheelDetector.by_name(chassis, r".*wheel_.*")
        """
        if not BLENDER_AVAILABLE:
            return []

        patterns = (
            [pattern]
            if isinstance(pattern, str)
            else pattern if pattern else WheelDetector.DEFAULT_PATTERNS
        )
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

        wheels = []

        # Search in object children or collection objects
        objects_to_search = []
        if hasattr(obj, "children"):
            objects_to_search.extend(_get_all_children(obj))
        elif hasattr(obj, "objects"):
            objects_to_search = list(obj.objects)

        for child in objects_to_search:
            if not hasattr(child, "name"):
                continue
            name = child.name
            if any(p.search(name) for p in compiled_patterns):
                wheels.append(child)

        return wheels

    @staticmethod
    def by_geometry(
        obj: Any, radius_range: tuple[float, float] = (0.15, 0.6)
    ) -> list[Any]:
        """Detect wheels by geometric analysis.

        Analyzes mesh objects to find cylindrical shapes that
        match wheel geometry within the specified radius range.

        Args:
            obj: Parent object to search within
            radius_range: (min_radius, max_radius) for wheel detection

        Returns:
            List of detected wheel objects

        Example:
            wheels = WheelDetector.by_geometry(chassis, (0.2, 0.5))
        """
        if not BLENDER_AVAILABLE:
            return []

        min_radius, max_radius = radius_range
        wheels = []

        objects_to_search = []
        if hasattr(obj, "children"):
            objects_to_search.extend(_get_all_children(obj))
        elif hasattr(obj, "objects"):
            objects_to_search = list(obj.objects)

        for child in objects_to_search:
            if not hasattr(child, "data") or child.data is None:
                continue
            if not hasattr(child.data, "vertices"):
                continue

            # Get bounding box dimensions
            bbox = child.bound_box
            if not bbox:
                continue

            # Calculate approximate radius from bounding box
            xs = [v[0] for v in bbox]
            ys = [v[1] for v in bbox]
            zs = [v[2] for v in bbox]

            # For wheels, expect roughly equal X and Y dimensions (circular)
            # and smaller Z (width)
            dx = max(xs) - min(xs)
            dy = max(ys) - min(ys)
            dz = max(zs) - min(zs)

            avg_diameter = (dx + dy) / 2
            radius = avg_diameter / 2

            # Check if dimensions suggest a wheel shape
            aspect_ratio = min(dx, dy) / max(dx, dy) if max(dx, dy) > 0 else 0

            # Wheel criteria:
            # 1. Radius within range
            # 2. Roughly circular (X and Y similar)
            # 3. Width (Z) typically less than diameter
            if (
                min_radius <= radius <= max_radius
                and aspect_ratio > 0.7  # Fairly circular
                and dz < avg_diameter  # Not too thick
            ):
                wheels.append(child)

        return wheels

    @staticmethod
    def by_position(
        obj: Any, expected_positions: list[tuple[float, float, float]],
        tolerance: float = 0.5
    ) -> list[Any]:
        """Detect wheels by expected positions.

        Matches objects to expected wheel positions based on
        typical vehicle layouts.

        Args:
            obj: Parent object to search within
            expected_positions: List of (x, y, z) world positions for wheels
            tolerance: Maximum distance from expected position

        Returns:
            List of detected wheel objects in order of expected positions

        Example:
            # Standard car layout
            positions = [
                (1, 1.5, 0.4),   # Front left
                (1, -1.5, 0.4),  # Front right
                (-1, 1.5, 0.4),  # Rear left
                (-1, -1.5, 0.4), # Rear right
            ]
            wheels = WheelDetector.by_position(chassis, positions)
        """
        if not BLENDER_AVAILABLE:
            return []

        wheels = []
        used_objects = set()

        objects_to_search = []
        if hasattr(obj, "children"):
            objects_to_search.extend(_get_all_children(obj))
        elif hasattr(obj, "objects"):
            objects_to_search = list(obj.objects)

        for expected_pos in expected_positions:
            expected_vec = Vector(expected_pos)
            best_match = None
            best_distance = tolerance

            for child in objects_to_search:
                if child in used_objects:
                    continue
                if not hasattr(child, "matrix_world"):
                    continue

                # Get world position
                world_pos = child.matrix_world.translation
                distance = (world_pos - expected_vec).length

                if distance < best_distance:
                    best_distance = distance
                    best_match = child

            if best_match:
                wheels.append(best_match)
                used_objects.add(best_match)

        return wheels

    @staticmethod
    def detect_all(
        obj: Any,
        name_pattern: Optional[str] = None,
        radius_range: tuple[float, float] = (0.15, 0.6),
        expected_positions: Optional[list[tuple[float, float, float]]] = None,
    ) -> ComponentDetectionResult:
        """Comprehensive wheel detection using multiple strategies.

        Combines name, geometry, and position detection for
        most reliable results.

        Args:
            obj: Parent object to search
            name_pattern: Optional name pattern override
            radius_range: Radius range for geometry detection
            expected_positions: Optional expected wheel positions

        Returns:
            ComponentDetectionResult with detected components
        """
        result = ComponentDetectionResult()

        # Try name detection first
        by_name_wheels = WheelDetector.by_name(obj, name_pattern)

        # Try geometry detection
        by_geometry_wheels = WheelDetector.by_geometry(obj, radius_range)

        # Merge results - prefer name matches, add geometry matches not already found
        name_set = set(id(w) for w in by_name_wheels)
        all_wheels = list(by_name_wheels)
        for wheel in by_geometry_wheels:
            if id(wheel) not in name_set:
                all_wheels.append(wheel)

        # If we have expected positions, try to match and order
        if expected_positions:
            by_position_wheels = WheelDetector.by_position(obj, expected_positions)
            if len(by_position_wheels) == len(expected_positions):
                all_wheels = by_position_wheels
                result.detection_method = "position"

        result.wheels = all_wheels
        result.body = obj

        # Calculate wheel positions and radii
        for wheel in all_wheels:
            if hasattr(wheel, "matrix_world"):
                result.wheel_positions[wheel.name] = wheel.matrix_world.translation.copy()

            if hasattr(wheel, "bound_box") and wheel.bound_box:
                bbox = wheel.bound_box
                xs = [v[0] for v in bbox]
                ys = [v[1] for v in bbox]
                diameter = (max(xs) - min(xs) + max(ys) - min(ys)) / 2
                result.wheel_radii[wheel.name] = diameter / 2

        # Calculate confidence score
        result.confidence_score = WheelDetector._calculate_confidence(result)

        # Add warnings
        if len(result.wheels) < 2:
            result.warnings.append("Less than 2 wheels detected")
        if len(result.wheels) % 2 != 0:
            result.warnings.append("Odd number of wheels detected")
        if result.confidence_score < 0.5:
            result.warnings.append("Low confidence in wheel detection")

        return result

    @staticmethod
    def _calculate_confidence(result: ComponentDetectionResult) -> float:
        """Calculate confidence score for detection results."""
        score = 0.0

        # Number of wheels (expect 4 for cars, 2 for motorcycles)
        wheel_count = len(result.wheels)
        if wheel_count == 4:
            score += 0.4
        elif wheel_count == 2:
            score += 0.3
        elif wheel_count >= 4:
            score += 0.25

        # Position symmetry check
        if len(result.wheel_positions) >= 4:
            positions = list(result.wheel_positions.values())
            # Check front axle symmetry
            front_y_diff = abs(positions[0].y - positions[1].y) if len(positions) > 1 else 0
            if front_y_diff < 0.1:
                score += 0.2
            # Check rear axle symmetry
            rear_y_diff = abs(positions[2].y - positions[3].y) if len(positions) > 3 else 0
            if rear_y_diff < 0.1:
                score += 0.2

        # Consistent radii
        if len(result.wheel_radii) >= 2:
            radii = list(result.wheel_radii.values())
            avg_radius = sum(radii) / len(radii)
            variance = sum((r - avg_radius) ** 2 for r in radii) / len(radii)
            if variance < 0.01:
                score += 0.2

        return min(score, 1.0)


def _get_all_children(obj: Any) -> list[Any]:
    """Recursively get all children of an object."""
    children = list(obj.children) if hasattr(obj, "children") else []
    all_children = list(children)
    for child in children:
        all_children.extend(_get_all_children(child))
    return all_children


class LaunchControlRig:
    """One-click vehicle rigging system.

    Main entry point for vehicle rigging. Handles automatic component
    detection, rig generation, constraint application, and driver setup.

    Example:
        # Simple one-click rig
        rig = LaunchControlRig(vehicle_body)
        rig.one_click_rig()

        # With configuration
        config = RigConfiguration(
            suspension_type=SuspensionType.DOUBLE_WISHBONE,
            steering_type=SteeringType.FRONT,
            max_steering_angle=40.0
        )
        rig = LaunchControlRig(vehicle_body, config)
        rig.detect_components()
        rig.generate_rig()
        rig.apply_constraints()
        rig.setup_drivers()
    """

    def __init__(
        self,
        vehicle_body: Any,
        config: Optional[RigConfiguration] = None
    ):
        """Initialize the rig system.

        Args:
            vehicle_body: The main body object of the vehicle
            config: Optional rig configuration
        """
        self.vehicle_body = vehicle_body
        self.config = config or RigConfiguration()
        self.detected_components: Optional[ComponentDetectionResult] = None
        self.rig_objects: dict[str, Any] = {}
        self.controllers: dict[str, Any] = {}
        self.constraints: dict[str, list[Any]] = {}
        self.drivers: dict[str, Any] = {}
        self._is_rigged = False

    def detect_components(
        self,
        wheel_naming: str = "auto",
        axle_naming: str = "auto",
        expected_positions: Optional[list[tuple[float, float, float]]] = None,
    ) -> ComponentDetectionResult:
        """Automatically detect vehicle components.

        Args:
            wheel_naming: Pattern for wheel name matching, or "auto"
            axle_naming: Pattern for axle name matching, or "auto"
            expected_positions: Optional expected wheel positions

        Returns:
            ComponentDetectionResult with detected components
        """
        pattern = None if wheel_naming == "auto" else wheel_naming

        self.detected_components = WheelDetector.detect_all(
            self.vehicle_body,
            name_pattern=pattern,
            expected_positions=expected_positions,
        )

        # Detect axles if pattern provided
        if axle_naming != "auto" and BLENDER_AVAILABLE:
            axle_pattern = re.compile(axle_naming, re.IGNORECASE)
            for child in _get_all_children(self.vehicle_body):
                if hasattr(child, "name") and axle_pattern.search(child.name):
                    self.detected_components.axles.append(child)

        return self.detected_components

    def generate_rig(
        self,
        suspension_type: str = "independent",
        steering_type: str = "front",
    ) -> dict[str, Any]:
        """Generate the rig hierarchy and control objects.

        Creates armature, control bones, and helper objects for
        the vehicle rig.

        Args:
            suspension_type: Type of suspension system
            steering_type: Type of steering configuration

        Returns:
            Dictionary of created rig objects
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender API not available")

        if not self.detected_components:
            self.detect_components()

        if not self.detected_components.is_valid():
            raise ValueError(
                f"Invalid component detection: {len(self.detected_components.wheels)} wheels found"
            )

        # Convert string types to enums
        try:
            self.config.suspension_type = SuspensionType(suspension_type)
        except ValueError:
            self.config.suspension_type = SuspensionType.INDEPENDENT

        try:
            self.config.steering_type = SteeringType(steering_type)
        except ValueError:
            self.config.steering_type = SteeringType.FRONT

        # Create armature
        armature_name = f"{self.config.rig_name}_armature"
        armature_data = bpy.data.armatures.new(armature_name)
        armature_obj = bpy.data.objects.new(armature_name, armature_data)

        # Link to scene
        bpy.context.collection.objects.link(armature_obj)
        self.rig_objects["armature"] = armature_obj

        # Create wheel bone controls
        self._create_wheel_bones(armature_obj)

        # Create steering controller if enabled
        if self.config.create_steering_controller:
            self._create_steering_controller()

        # Create custom properties
        if self.config.create_custom_properties:
            self._create_custom_properties()

        self._is_rigged = True
        return self.rig_objects

    def _create_wheel_bones(self, armature: Any) -> None:
        """Create bone controls for each wheel."""
        if not self.detected_components:
            return

        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="EDIT")

        wheel_positions = [
            ("FL", "front_left"),
            ("FR", "front_right"),
            ("RL", "rear_left"),
            ("RR", "rear_right"),
        ]

        for pos_code, pos_name in wheel_positions:
            wheel = self.detected_components.get_wheel_by_position(pos_name)
            if not wheel:
                continue

            wheel_world_pos = wheel.matrix_world.translation

            # Create main control bone
            bone_name = f"wheel_{pos_code}_ctrl"
            bone = armature.data.edit_bones.new(bone_name)
            bone.head = wheel_world_pos
            bone.tail = wheel_world_pos + Vector((0, 0, 0.3))
            bone.length = 0.3

            self.rig_objects[f"wheel_{pos_code}"] = bone_name

        bpy.ops.object.mode_set(mode="OBJECT")

    def _create_steering_controller(self) -> None:
        """Create steering wheel controller object."""
        if not BLENDER_AVAILABLE:
            return

        # Create empty controller
        controller_name = f"{self.config.rig_name}_steering_ctrl"
        controller = bpy.data.objects.new(controller_name, None)
        controller.empty_display_type = "CIRCLE"
        controller.empty_display_size = 0.15
        controller.location = self.config.controller_location

        bpy.context.collection.objects.link(controller)
        self.controllers["steering"] = controller

        # Parent to armature if exists
        if "armature" in self.rig_objects:
            controller.parent = self.rig_objects["armature"]

    def _create_custom_properties(self) -> None:
        """Create custom properties for rig control."""
        if not BLENDER_AVAILABLE or "armature" not in self.rig_objects:
            return

        armature = self.rig_objects["armature"]

        # Steering angle property
        armature["steering_angle"] = 0.0
        armature.id_properties_ui("steering_angle").update(
            min=-self.config.max_steering_angle,
            max=self.config.max_steering_angle,
            soft_min=-self.config.max_steering_angle,
            soft_max=self.config.max_steering_angle,
        )

        # Suspension properties
        armature["suspension_travel"] = self.config.suspension_travel
        armature["spring_stiffness"] = self.config.spring_stiffness
        armature["damping"] = self.config.damping

    def apply_constraints(self) -> None:
        """Apply constraints to rig components.

        Sets up Copy Location, Copy Rotation, and other constraints
        for wheel and body control.
        """
        if not BLENDER_AVAILABLE or not self.detected_components:
            return

        armature = self.rig_objects.get("armature")
        if not armature:
            return

        self.constraints["wheels"] = []

        for wheel in self.detected_components.wheels:
            # Find corresponding bone
            wheel_name = wheel.name.lower()
            bone_name = None
            for key in self.rig_objects:
                if key.startswith("wheel_") and any(
                    pos in wheel_name
                    for pos in ["fl", "fr", "rl", "rr", "front", "rear", "left", "right"]
                ):
                    if any(pos in key for pos in ["fl", "fr", "rl", "rr"]):
                        # More specific matching
                        pos_in_wheel = (
                            ("fl" in wheel_name or "front_left" in wheel_name)
                            and "fl" in key
                        ) or (
                            ("fr" in wheel_name or "front_right" in wheel_name)
                            and "fr" in key
                        ) or (
                            ("rl" in wheel_name or "rear_left" in wheel_name)
                            and "rl" in key
                        ) or (
                            ("rr" in wheel_name or "rear_right" in wheel_name)
                            and "rr" in key
                        )
                        if pos_in_wheel:
                            bone_name = self.rig_objects[key]
                            break

            if bone_name:
                # Add Copy Transform constraint
                constraint = wheel.constraints.new("COPY_TRANSFORMS")
                constraint.target = armature
                constraint.subtarget = bone_name
                constraint.mix_mode = "REPLACE"
                self.constraints["wheels"].append(constraint)

    def setup_drivers(self) -> None:
        """Setup drivers for procedural rig control.

        Creates drivers for:
        - Steering angle to wheel rotation
        - Ackermann geometry compensation
        - Suspension compression
        """
        if not BLENDER_AVAILABLE:
            return

        armature = self.rig_objects.get("armature")
        if not armature:
            return

        # Setup steering drivers on front wheels
        if self.config.steering_type in [SteeringType.FRONT, SteeringType.FOUR_WHEEL]:
            self._setup_steering_drivers(armature)

    def _setup_steering_drivers(self, armature: Any) -> None:
        """Setup steering angle drivers on wheel bones."""
        # This would set up drivers using bpy.data.driver_add()
        # Implementation depends on specific rigging requirements
        pass

    def one_click_rig(self) -> dict[str, Any]:
        """Execute complete one-click rigging workflow.

        Performs all steps in sequence:
        1. Detect components
        2. Generate rig
        3. Apply constraints
        4. Setup drivers

        Returns:
            Dictionary of all created rig objects

        Raises:
            RuntimeError: If rigging fails at any step
        """
        try:
            # Step 1: Detect components
            detection = self.detect_components()
            if not detection.is_valid():
                raise RuntimeError(
                    f"Component detection failed: {', '.join(detection.warnings)}"
                )

            # Step 2: Generate rig
            rig_objects = self.generate_rig(
                suspension_type=self.config.suspension_type.value,
                steering_type=self.config.steering_type.value,
            )

            # Step 3: Apply constraints
            self.apply_constraints()

            # Step 4: Setup drivers
            self.setup_drivers()

            return rig_objects

        except Exception as e:
            raise RuntimeError(f"One-click rigging failed: {e}") from e

    def get_rig_info(self) -> dict[str, Any]:
        """Get information about the current rig state.

        Returns:
            Dictionary with rig information
        """
        return {
            "is_rigged": self._is_rigged,
            "vehicle_body": self.vehicle_body.name if hasattr(self.vehicle_body, "name") else None,
            "config": {
                "suspension_type": self.config.suspension_type.value,
                "steering_type": self.config.steering_type.value,
                "max_steering_angle": self.config.max_steering_angle,
                "ackermann_enabled": self.config.ackermann_enabled,
            },
            "detected_components": {
                "wheel_count": len(self.detected_components.wheels) if self.detected_components else 0,
                "confidence": self.detected_components.confidence_score if self.detected_components else 0,
            },
            "rig_objects": list(self.rig_objects.keys()),
            "controllers": list(self.controllers.keys()),
        }
