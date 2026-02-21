"""
Suspension Physics System for Launch Control

Physics-based suspension simulation with configurable spring rates,
damping curves, and animation baking.

Features:
- Multiple suspension types (double wishbone, MacPherson, etc.)
- Configurable spring stiffness and damping
- Linear, progressive, and digressive damping curves
- Physics simulation with automatic or manual substeps
- Animation baking for rendered output
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

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

if TYPE_CHECKING:
    from .auto_rig import LaunchControlRig


class DampingMode(Enum):
    """Damping curve types for suspension."""

    LINEAR = "linear"
    PROGRESSIVE = "progressive"
    DIGRESSIVE = "digressive"
    CUSTOM = "custom"


class PhysicsMode(Enum):
    """Physics simulation modes."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
    BAKED = "baked"
    OFF = "off"


@dataclass
class SuspensionConfig:
    """Configuration for a suspension system."""

    travel: float = 0.3  # meters
    spring_stiffness: float = 25000.0  # N/m
    damping: float = 1500.0  # Ns/m
    preload: float = 0.0  # meters (positive = compressed at rest)
    damping_mode: DampingMode = DampingMode.LINEAR
    progressive_factor: float = 1.5  # For progressive damping
    digressive_threshold: float = 0.1  # m/s for digressive damping
    anti_roll: float = 0.0  # Anti-roll bar stiffness ratio
    bump_stop: float = 0.02  # Bump stop compression distance
    rebound_ratio: float = 1.0  # Rebound/compression ratio


@dataclass
class WheelSpringData:
    """Spring data for a single wheel."""

    wheel_name: str
    current_displacement: float = 0.0
    velocity: float = 0.0
    force: float = 0.0
    config: SuspensionConfig = field(default_factory=SuspensionConfig)

    def get_compression_ratio(self) -> float:
        """Get current compression as ratio of total travel."""
        return self.current_displacement / self.config.travel if self.config.travel > 0 else 0


class DampingCurve:
    """Damping curve calculations for suspension systems.

    Provides static methods for calculating damping force based on
    velocity using different curve types.

    Example:
        # Linear damping
        force = DampingCurve.linear(velocity=0.5, coefficient=1500)

        # Progressive damping (increases with velocity)
        force = DampingCurve.progressive(velocity=0.5, base=1500, factor=1.5)

        # Digressive damping (decreases above threshold)
        force = DampingCurve.digressive(velocity=0.5, base=1500, threshold=0.1)
    """

    @staticmethod
    def linear(velocity: float, coefficient: float) -> float:
        """Calculate linear damping force.

        F = -c * v

        Args:
            velocity: Current velocity (m/s)
            coefficient: Damping coefficient (Ns/m)

        Returns:
            Damping force (N)
        """
        return -coefficient * velocity

    @staticmethod
    def progressive(
        velocity: float, base: float, factor: float = 1.5
    ) -> float:
        """Calculate progressive damping force.

        Damping increases with velocity. Good for sport suspensions
        where you want more control at higher speeds.

        F = -c * |v|^factor * sign(v)

        Args:
            velocity: Current velocity (m/s)
            base: Base damping coefficient (Ns/m)
            factor: Progressive exponent (1.0 = linear, >1.0 = progressive)

        Returns:
            Damping force (N)
        """
        sign = 1 if velocity >= 0 else -1
        return -base * (abs(velocity) ** factor) * sign

    @staticmethod
    def digressive(
        velocity: float, base: float, threshold: float = 0.1
    ) -> float:
        """Calculate digressive damping force.

        Damping is high at low velocities for control, but decreases
        relative to velocity at higher speeds. Good for comfort over
        sharp bumps while maintaining cornering stability.

        Args:
            velocity: Current velocity (m/s)
            base: Base damping coefficient (Ns/m)
            threshold: Velocity threshold for digressive behavior (m/s)

        Returns:
            Damping force (N)
        """
        abs_vel = abs(velocity)
        sign = 1 if velocity >= 0 else -1

        if abs_vel <= threshold:
            # Linear region
            return -base * velocity
        else:
            # Digressive region: damping rate decreases
            excess = abs_vel - threshold
            digressive_factor = 1.0 / (1.0 + excess * 2.0)
            return -base * (threshold + excess * digressive_factor) * sign

    @staticmethod
    def custom(
        velocity: float,
        curve_points: list[tuple[float, float]],
        interpolate: bool = True,
    ) -> float:
        """Calculate custom damping force from curve points.

        Args:
            velocity: Current velocity (m/s)
            curve_points: List of (velocity, force) tuples defining the curve
            interpolate: Whether to interpolate between points

        Returns:
            Damping force (N)
        """
        if not curve_points:
            return 0.0

        # Sort by velocity
        sorted_points = sorted(curve_points, key=lambda p: abs(p[0]))

        # Find surrounding points
        abs_vel = abs(velocity)
        sign = 1 if velocity >= 0 else -1

        lower = None
        upper = None

        for i, (v, f) in enumerate(sorted_points):
            if abs(v) >= abs_vel:
                upper = (v, f)
                if i > 0:
                    lower = sorted_points[i - 1]
                break
            lower = (v, f)

        if upper is None:
            # Beyond curve, use last point
            return sorted_points[-1][1] * sign
        if lower is None:
            # Before curve, use first point
            return sorted_points[0][1] * sign

        if not interpolate:
            return lower[1] * sign

        # Linear interpolation
        t = (abs_vel - abs(lower[0])) / (abs(upper[0]) - abs(lower[0]))
        force = lower[1] + t * (upper[1] - lower[1])
        return force * sign


class SuspensionSystem:
    """Physics-based suspension simulation.

    Manages suspension physics for all wheels with configurable
    spring rates, damping curves, and simulation modes.

    Example:
        rig = LaunchControlRig(vehicle_body)
        rig.one_click_rig()

        suspension = SuspensionSystem(rig)
        suspension.configure(
            travel=0.3,
            spring_stiffness=25000,
            damping=1500,
            damping_mode=DampingMode.PROGRESSIVE
        )

        # Enable physics simulation
        suspension.enable_physics(mode="automatic", substeps=10)

        # Get current wheel displacement
        displacement = suspension.get_displacement(wheel_index=0)

        # Bake animation for rendering
        suspension.bake_animation(frame_start=1, frame_end=120)
    """

    TYPES = {
        "double_wishbone",
        "macpherson",
        "solid_axle",
        "torsion_beam",
        "air_suspension",
        "multi_link",
    }

    def __init__(self, rig: "LaunchControlRig"):
        """Initialize suspension system.

        Args:
            rig: The LaunchControlRig instance to manage
        """
        self.rig = rig
        self.configs: dict[str, SuspensionConfig] = {}
        self.wheel_data: dict[str, WheelSpringData] = {}
        self.physics_mode = PhysicsMode.OFF
        self.substeps = 10
        self._physics_handler: Optional[Any] = None

        # Initialize wheel data from detected components
        self._initialize_wheel_data()

    def _initialize_wheel_data(self) -> None:
        """Initialize wheel spring data from rig components."""
        if not self.rig.detected_components:
            return

        default_config = SuspensionConfig()

        for wheel in self.rig.detected_components.wheels:
            wheel_name = wheel.name if hasattr(wheel, "name") else str(id(wheel))
            self.wheel_data[wheel_name] = WheelSpringData(
                wheel_name=wheel_name,
                config=default_config,
            )
            self.configs[wheel_name] = default_config

    def configure(
        self,
        travel: float = 0.3,
        spring_stiffness: float = 25000.0,
        damping: float = 1500.0,
        preload: float = 0.0,
        damping_mode: DampingMode = DampingMode.LINEAR,
        progressive_factor: float = 1.5,
        digressive_threshold: float = 0.1,
        anti_roll: float = 0.0,
        wheel_specific: Optional[dict[str, SuspensionConfig]] = None,
    ) -> None:
        """Configure suspension parameters for all wheels.

        Args:
            travel: Maximum suspension travel in meters
            spring_stiffness: Spring rate in N/m
            damping: Damping coefficient in Ns/m
            preload: Initial compression at rest (meters)
            damping_mode: Type of damping curve
            progressive_factor: Exponent for progressive damping
            digressive_threshold: Threshold for digressive damping
            anti_roll: Anti-roll bar stiffness ratio (0-1)
            wheel_specific: Optional wheel-specific configurations
        """
        default_config = SuspensionConfig(
            travel=travel,
            spring_stiffness=spring_stiffness,
            damping=damping,
            preload=preload,
            damping_mode=damping_mode,
            progressive_factor=progressive_factor,
            digressive_threshold=digressive_threshold,
            anti_roll=anti_roll,
        )

        # Apply default to all wheels
        for wheel_name in self.wheel_data:
            self.configs[wheel_name] = default_config
            self.wheel_data[wheel_name].config = default_config

        # Apply wheel-specific overrides
        if wheel_specific:
            for wheel_name, config in wheel_specific.items():
                if wheel_name in self.wheel_data:
                    self.configs[wheel_name] = config
                    self.wheel_data[wheel_name].config = config

    def enable_physics(
        self,
        mode: str = "automatic",
        substeps: int = 10,
    ) -> None:
        """Enable physics simulation for suspension.

        Args:
            mode: Physics mode - "automatic", "manual", or "baked"
            substeps: Number of physics substeps per frame
        """
        try:
            self.physics_mode = PhysicsMode(mode.lower())
        except ValueError:
            self.physics_mode = PhysicsMode.AUTOMATIC

        self.substeps = substeps

        if self.physics_mode == PhysicsMode.AUTOMATIC:
            self._setup_automatic_physics()
        elif self.physics_mode == PhysicsMode.BAKED:
            # Bake mode just sets flag, actual baking is separate
            pass

    def _setup_automatic_physics(self) -> None:
        """Setup automatic physics using frame change handlers."""
        if not BLENDER_AVAILABLE:
            return

        # Remove existing handler if any
        self.disable_physics()

        # Create physics handler
        def physics_handler(scene: Any) -> None:
            self._update_physics(scene)

        # Register handler
        bpy.app.handlers.frame_change_post.append(physics_handler)
        self._physics_handler = physics_handler

    def disable_physics(self) -> None:
        """Disable physics simulation."""
        if BLENDER_AVAILABLE and self._physics_handler is not None:
            try:
                bpy.app.handlers.frame_change_post.remove(self._physics_handler)
            except ValueError:
                pass
        self._physics_handler = None
        self.physics_mode = PhysicsMode.OFF

    def _update_physics(self, scene: Any) -> None:
        """Update physics for current frame.

        Called automatically by frame change handler.
        """
        if not self.rig.detected_components:
            return

        dt = 1.0 / (scene.render.fps * self.substeps)

        for _ in range(self.substeps):
            self._simulate_step(dt)

    def _simulate_step(self, dt: float) -> None:
        """Simulate one physics step.

        Args:
            dt: Time step in seconds
        """
        for wheel_name, data in self.wheel_data.items():
            config = data.config

            # Calculate spring force (Hooke's law)
            spring_force = -config.spring_stiffness * (
                data.current_displacement - config.preload
            )

            # Calculate damping force based on mode
            damping_force = self._calculate_damping(data)

            # Total force
            total_force = spring_force + damping_force

            # Update velocity and displacement (simple Euler integration)
            # Assuming unit mass for wheel assembly
            data.velocity += total_force * dt
            data.current_displacement += data.velocity * dt

            # Clamp to travel limits
            if data.current_displacement < 0:
                data.current_displacement = 0
                data.velocity = abs(data.velocity) * 0.5  # Bump
            elif data.current_displacement > config.travel:
                data.current_displacement = config.travel
                data.velocity = -abs(data.velocity) * 0.5  # Rebound

            data.force = total_force

    def _calculate_damping(self, data: WheelSpringData) -> float:
        """Calculate damping force based on configuration.

        Args:
            data: Wheel spring data

        Returns:
            Damping force in Newtons
        """
        config = data.config
        velocity = data.velocity

        # Apply rebound ratio for asymmetric damping
        if velocity < 0:  # Rebound
            coefficient = config.damping * config.rebound_ratio
        else:  # Compression
            coefficient = config.damping

        if config.damping_mode == DampingMode.LINEAR:
            return DampingCurve.linear(velocity, coefficient)
        elif config.damping_mode == DampingMode.PROGRESSIVE:
            return DampingCurve.progressive(
                velocity, coefficient, config.progressive_factor
            )
        elif config.damping_mode == DampingMode.DIGRESSIVE:
            return DampingCurve.digressive(
                velocity, coefficient, config.digressive_threshold
            )
        else:
            return DampingCurve.linear(velocity, coefficient)

    def bake_animation(
        self,
        frame_start: int,
        frame_end: int,
        sample_rate: int = 1,
    ) -> None:
        """Bake suspension animation to keyframes.

        Pre-calculates and bakes suspension motion for rendering.

        Args:
            frame_start: Start frame for baking
            frame_end: End frame for baking
            sample_rate: Frames between samples (1 = every frame)
        """
        if not BLENDER_AVAILABLE:
            return

        # Store current frame
        current_frame = bpy.context.scene.frame_current

        try:
            # Temporarily disable physics for manual calculation
            original_mode = self.physics_mode
            self.physics_mode = PhysicsMode.MANUAL

            # Get armature
            armature = self.rig.rig_objects.get("armature")
            if not armature:
                return

            # Bake each wheel
            for wheel_name, data in self.wheel_data.items():
                # Find corresponding pose bone
                bone_name = None
                for key, val in self.rig.rig_objects.items():
                    if key.startswith("wheel_") and wheel_name.lower() in val.lower():
                        bone_name = val
                        break

                if not bone_name:
                    continue

                # Animate for each frame
                for frame in range(frame_start, frame_end + 1, sample_rate):
                    bpy.context.scene.frame_set(frame)

                    # Update physics
                    dt = 1.0 / bpy.context.scene.render.fps
                    self._simulate_step(dt)

                    # Set keyframe on bone Z location
                    if armature.pose and bone_name in armature.pose.bones:
                        bone = armature.pose.bones[bone_name]
                        bone.location.z = data.current_displacement
                        bone.keyframe_insert(
                            data_path="location",
                            index=2,  # Z axis
                            frame=frame,
                        )

            self.physics_mode = original_mode

        finally:
            # Restore frame
            bpy.context.scene.frame_set(current_frame)

    def get_displacement(self, wheel_index: int) -> float:
        """Get current displacement for a wheel.

        Args:
            wheel_index: Index of wheel (0-3 for typical car)

        Returns:
            Current displacement in meters (0 = fully extended)
        """
        if not self.wheel_data:
            return 0.0

        wheel_names = list(self.wheel_data.keys())
        if 0 <= wheel_index < len(wheel_names):
            return self.wheel_data[wheel_names[wheel_index]].current_displacement
        return 0.0

    def get_displacement_by_name(self, wheel_name: str) -> float:
        """Get current displacement for a wheel by name.

        Args:
            wheel_name: Name of the wheel

        Returns:
            Current displacement in meters
        """
        if wheel_name in self.wheel_data:
            return self.wheel_data[wheel_name].current_displacement
        return 0.0

    def set_displacement(
        self,
        wheel_name: str,
        displacement: float,
        animate: bool = False,
        frame: Optional[int] = None,
    ) -> None:
        """Manually set wheel displacement.

        Args:
            wheel_name: Name of the wheel
            displacement: Target displacement in meters
            animate: Whether to keyframe the change
            frame: Frame for keyframe (uses current if None)
        """
        if wheel_name not in self.wheel_data:
            return

        config = self.configs.get(wheel_name, SuspensionConfig())
        clamped = max(0, min(displacement, config.travel))
        self.wheel_data[wheel_name].current_displacement = clamped

        if animate and BLENDER_AVAILABLE:
            armature = self.rig.rig_objects.get("armature")
            if not armature:
                return

            # Find bone
            bone_name = None
            for key, val in self.rig.rig_objects.items():
                if key.startswith("wheel_") and wheel_name.lower() in val.lower():
                    bone_name = val
                    break

            if bone_name and armature.pose and bone_name in armature.pose.bones:
                bone = armature.pose.bones[bone_name]
                bone.location.z = clamped
                target_frame = frame if frame is not None else bpy.context.scene.frame_current
                bone.keyframe_insert(
                    data_path="location",
                    index=2,
                    frame=target_frame,
                )

    def apply_impulse(
        self,
        wheel_name: str,
        impulse: float,
    ) -> None:
        """Apply an impulse to a wheel.

        Args:
            wheel_name: Name of the wheel
            impulse: Impulse magnitude (affects velocity)
        """
        if wheel_name in self.wheel_data:
            self.wheel_data[wheel_name].velocity += impulse

    def get_wheel_data(self, wheel_name: str) -> Optional[WheelSpringData]:
        """Get spring data for a specific wheel.

        Args:
            wheel_name: Name of the wheel

        Returns:
            WheelSpringData or None if not found
        """
        return self.wheel_data.get(wheel_name)

    def get_all_wheel_data(self) -> dict[str, WheelSpringData]:
        """Get spring data for all wheels.

        Returns:
            Dictionary mapping wheel names to their data
        """
        return dict(self.wheel_data)

    def reset(self) -> None:
        """Reset all wheels to rest position."""
        for data in self.wheel_data.values():
            data.current_displacement = data.config.preload
            data.velocity = 0.0
            data.force = 0.0
