"""
Morphing Engine for Control Surface System

Provides smooth transitions between control styles including:
- Geometry morphing (blend shapes, parameter interpolation)
- Material morphing (property interpolation)
- Color morphing (LAB color space interpolation)
- Animation system with easing curves
- Staggered animation support

Usage:
    from lib.control_system.morphing import (
        MorphEngine, MorphTarget, MorphAnimation,
        EasingType, animate_morph
    )

    # Create morph targets
    source = MorphTarget.from_preset("neve_1073")
    target = MorphTarget.from_preset("ssl_4000_e")

    # Create animation
    animation = MorphAnimation(
        source=source,
        target=target,
        duration=2.0,  # seconds
        easing=EasingType.EASE_IN_OUT_CUBIC
    )

    # Apply morph at time t
    engine = MorphEngine()
    current_state = engine.evaluate(animation, t=0.5)
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
import colorsys


# =============================================================================
# EASING FUNCTIONS
# =============================================================================

class EasingType(Enum):
    """Available easing curve types for morph animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_IN_QUART = "ease_in_quart"
    EASE_OUT_QUART = "ease_out_quart"
    EASE_IN_OUT_QUART = "ease_in_out_quart"
    EASE_IN_QUINT = "ease_in_quint"
    EASE_OUT_QUINT = "ease_out_quint"
    EASE_IN_OUT_QUINT = "ease_in_out_quint"
    EASE_IN_EXPO = "ease_in_expo"
    EASE_OUT_EXPO = "ease_out_expo"
    EASE_IN_OUT_EXPO = "ease_in_out_expo"
    EASE_IN_CIRC = "ease_in_circ"
    EASE_OUT_CIRC = "ease_out_circ"
    EASE_IN_OUT_CIRC = "ease_in_out_circ"
    EASE_IN_BACK = "ease_in_back"
    EASE_OUT_BACK = "ease_out_back"
    EASE_IN_OUT_BACK = "ease_in_out_back"
    EASE_IN_ELASTIC = "ease_in_elastic"
    EASE_OUT_ELASTIC = "ease_out_elastic"
    EASE_IN_OUT_ELASTIC = "ease_in_out_elastic"
    EASE_IN_BOUNCE = "ease_in_bounce"
    EASE_OUT_BOUNCE = "ease_out_bounce"
    EASE_IN_OUT_BOUNCE = "ease_in_out_bounce"


def apply_easing(t: float, easing: EasingType) -> float:
    """
    Apply easing function to normalized time value.

    Args:
        t: Normalized time (0.0 to 1.0)
        easing: Easing curve type

    Returns:
        Eased value (0.0 to 1.0, may overshoot for some curves)
    """
    t = max(0.0, min(1.0, t))  # Clamp to [0, 1]

    if easing == EasingType.LINEAR:
        return t

    elif easing == EasingType.EASE_IN:
        return t * t

    elif easing == EasingType.EASE_OUT:
        return t * (2 - t)

    elif easing == EasingType.EASE_IN_OUT:
        return t * t * (3 - 2 * t) if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

    elif easing == EasingType.EASE_IN_CUBIC:
        return t * t * t

    elif easing == EasingType.EASE_OUT_CUBIC:
        return 1 - pow(1 - t, 3)

    elif easing == EasingType.EASE_IN_OUT_CUBIC:
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

    elif easing == EasingType.EASE_IN_QUART:
        return t * t * t * t

    elif easing == EasingType.EASE_OUT_QUART:
        return 1 - pow(1 - t, 4)

    elif easing == EasingType.EASE_IN_OUT_QUART:
        return 8 * t * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 4) / 2

    elif easing == EasingType.EASE_IN_QUINT:
        return t * t * t * t * t

    elif easing == EasingType.EASE_OUT_QUINT:
        return 1 - pow(1 - t, 5)

    elif easing == EasingType.EASE_IN_OUT_QUINT:
        return 16 * t * t * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 5) / 2

    elif easing == EasingType.EASE_IN_EXPO:
        return 0 if t == 0 else pow(2, 10 * t - 10)

    elif easing == EasingType.EASE_OUT_EXPO:
        return 1 if t == 1 else 1 - pow(2, -10 * t)

    elif easing == EasingType.EASE_IN_OUT_EXPO:
        if t == 0:
            return 0
        elif t == 1:
            return 1
        elif t < 0.5:
            return pow(2, 20 * t - 10) / 2
        else:
            return (2 - pow(2, -20 * t + 10)) / 2

    elif easing == EasingType.EASE_IN_CIRC:
        return 1 - math.sqrt(1 - t * t)

    elif easing == EasingType.EASE_OUT_CIRC:
        return math.sqrt(1 - pow(t - 1, 2))

    elif easing == EasingType.EASE_IN_OUT_CIRC:
        if t < 0.5:
            return (1 - math.sqrt(1 - pow(2 * t, 2))) / 2
        else:
            return (math.sqrt(1 - pow(-2 * t + 2, 2)) + 1) / 2

    elif easing == EasingType.EASE_IN_BACK:
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * t * t * t - c1 * t * t

    elif easing == EasingType.EASE_OUT_BACK:
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

    elif easing == EasingType.EASE_IN_OUT_BACK:
        c1 = 1.70158
        c2 = c1 * 1.525
        if t < 0.5:
            return (pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
        else:
            return (pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2

    elif easing == EasingType.EASE_IN_ELASTIC:
        c4 = (2 * math.pi) / 3
        if t == 0:
            return 0
        elif t == 1:
            return 1
        else:
            return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c4)

    elif easing == EasingType.EASE_OUT_ELASTIC:
        c4 = (2 * math.pi) / 3
        if t == 0:
            return 0
        elif t == 1:
            return 1
        else:
            return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

    elif easing == EasingType.EASE_IN_OUT_ELASTIC:
        c5 = (2 * math.pi) / 4.5
        if t == 0:
            return 0
        elif t == 1:
            return 1
        elif t < 0.5:
            return -(pow(2, 20 * t - 10) * math.sin((20 * t - 11.125) * c5)) / 2
        else:
            return (pow(2, -20 * t + 10) * math.sin((20 * t - 11.125) * c5)) / 2 + 1

    elif easing == EasingType.EASE_IN_BOUNCE:
        return 1 - apply_easing(1 - t, EasingType.EASE_OUT_BOUNCE)

    elif easing == EasingType.EASE_OUT_BOUNCE:
        n1 = 7.5625
        d1 = 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t_ = t - 1.5 / d1
            return n1 * t_ * t_ + 0.75
        elif t < 2.5 / d1:
            t_ = t - 2.25 / d1
            return n1 * t_ * t_ + 0.9375
        else:
            t_ = t - 2.625 / d1
            return n1 * t_ * t_ + 0.984375

    elif easing == EasingType.EASE_IN_OUT_BOUNCE:
        if t < 0.5:
            return (1 - apply_easing(1 - 2 * t, EasingType.EASE_OUT_BOUNCE)) / 2
        else:
            return (1 + apply_easing(2 * t - 1, EasingType.EASE_IN_BOUNCE)) / 2

    return t  # Fallback to linear


# =============================================================================
# COLOR INTERPOLATION
# =============================================================================

def rgb_to_lab(rgb: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """
    Convert RGB (0-1 range) to LAB color space.

    Uses D65 illuminant reference.
    """
    # Convert RGB to linear sRGB
    def srgb_to_linear(c):
        if c <= 0.04045:
            return c / 12.92
        return pow((c + 0.055) / 1.055, 2.4)

    r, g, b = [srgb_to_linear(c) for c in rgb]

    # sRGB to XYZ (D65)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    # Normalize by D65 reference
    x /= 0.95047
    y /= 1.0
    z /= 1.08883

    # XYZ to LAB
    def f(t):
        delta = 6/29
        if t > delta**3:
            return t ** (1/3)
        return t / (3 * delta**2) + 4/29

    L = 116 * f(y) - 16
    a = 500 * (f(x) - f(y))
    b_val = 200 * (f(y) - f(z))

    return (L, a, b_val)


def lab_to_rgb(lab: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """
    Convert LAB to RGB (0-1 range).

    Uses D65 illuminant reference.
    """
    L, a, b_val = lab

    # LAB to XYZ
    def f(t):
        delta = 6/29
        if t > delta:
            return t ** 3
        return 3 * delta**2 * (t - 4/29)

    x = f((L + 16) / 116 + a / 500) * 0.95047
    y = f((L + 16) / 116) * 1.0
    z = f((L + 16) / 116 - b_val / 200) * 1.08883

    # XYZ to linear sRGB
    r = x * 3.2404542 - y * 1.5371385 - z * 0.4985314
    g = -x * 0.9692660 + y * 1.8760108 + z * 0.0415560
    b = x * 0.0556434 - y * 0.2040259 + z * 1.0572252

    # Linear sRGB to sRGB
    def linear_to_srgb(c):
        if c <= 0.0031308:
            return c * 12.92
        return 1.055 * pow(c, 1/2.4) - 0.055

    r = linear_to_srgb(r)
    g = linear_to_srgb(g)
    b = linear_to_srgb(b)

    # Clamp to valid range
    return (
        max(0.0, min(1.0, r)),
        max(0.0, min(1.0, g)),
        max(0.0, min(1.0, b))
    )


def interpolate_color_lab(
    color1: Tuple[float, float, float],
    color2: Tuple[float, float, float],
    t: float
) -> Tuple[float, float, float]:
    """
    Interpolate between two colors in LAB color space.

    LAB interpolation produces perceptually uniform color blends.

    Args:
        color1: Start color (RGB, 0-1 range)
        color2: End color (RGB, 0-1 range)
        t: Interpolation factor (0.0 to 1.0)

    Returns:
        Interpolated color (RGB, 0-1 range)
    """
    lab1 = rgb_to_lab(color1)
    lab2 = rgb_to_lab(color2)

    # Linear interpolation in LAB space
    lab_result = (
        lab1[0] + t * (lab2[0] - lab1[0]),
        lab1[1] + t * (lab2[1] - lab1[1]),
        lab1[2] + t * (lab2[2] - lab1[2])
    )

    return lab_to_rgb(lab_result)


# =============================================================================
# MORPH TARGETS
# =============================================================================

@dataclass
class GeometryParams:
    """Geometry parameters for morphing."""
    profile: str = "cylindrical"
    cap_height: float = 0.015
    cap_diameter: float = 0.020
    skirt_height: float = 0.006
    skirt_diameter: float = 0.020
    skirt_style: int = 0
    edge_radius_top: float = 0.002
    edge_radius_bottom: float = 0.002
    segments: int = 64

    def interpolate(self, other: "GeometryParams", t: float) -> "GeometryParams":
        """Create interpolated geometry params."""
        return GeometryParams(
            profile=self.profile if t < 0.5 else other.profile,
            cap_height=self.cap_height + t * (other.cap_height - self.cap_height),
            cap_diameter=self.cap_diameter + t * (other.cap_diameter - self.cap_diameter),
            skirt_height=self.skirt_height + t * (other.skirt_height - self.skirt_height),
            skirt_diameter=self.skirt_diameter + t * (other.skirt_diameter - self.skirt_diameter),
            skirt_style=self.skirt_style if t < 0.5 else other.skirt_style,
            edge_radius_top=self.edge_radius_top + t * (other.edge_radius_top - self.edge_radius_top),
            edge_radius_bottom=self.edge_radius_bottom + t * (other.edge_radius_bottom - self.edge_radius_bottom),
            segments=int(self.segments + t * (other.segments - self.segments)),
        )


@dataclass
class MaterialParams:
    """Material parameters for morphing."""
    type: str = "plastic"
    metallic: float = 0.0
    roughness: float = 0.35
    clearcoat: float = 0.2
    base_color: Tuple[float, float, float] = (0.5, 0.5, 0.5)

    def interpolate(self, other: "MaterialParams", t: float, use_lab: bool = True) -> "MaterialParams":
        """Create interpolated material params."""
        if use_lab:
            color = interpolate_color_lab(self.base_color, other.base_color, t)
        else:
            color = (
                self.base_color[0] + t * (other.base_color[0] - self.base_color[0]),
                self.base_color[1] + t * (other.base_color[1] - self.base_color[1]),
                self.base_color[2] + t * (other.base_color[2] - self.base_color[2])
            )

        return MaterialParams(
            type=self.type if t < 0.5 else other.type,
            metallic=self.metallic + t * (other.metallic - self.metallic),
            roughness=self.roughness + t * (other.roughness - self.roughness),
            clearcoat=self.clearcoat + t * (other.clearcoat - self.clearcoat),
            base_color=color
        )


@dataclass
class SurfaceParams:
    """Surface feature parameters for morphing."""
    knurling_count: int = 0
    knurling_depth: float = 0.0005
    indicator_enabled: bool = False
    indicator_type: str = "line"

    def interpolate(self, other: "SurfaceParams", t: float) -> "SurfaceParams":
        """Create interpolated surface params."""
        return SurfaceParams(
            knurling_count=int(self.knurling_count + t * (other.knurling_count - self.knurling_count)),
            knurling_depth=self.knurling_depth + t * (other.knurling_depth - self.knurling_depth),
            indicator_enabled=self.indicator_enabled if t < 0.5 else other.indicator_enabled,
            indicator_type=self.indicator_type if t < 0.5 else other.indicator_type,
        )


@dataclass
class MorphTarget:
    """
    Complete morph target containing all parameters for a control surface style.

    Can be created from presets or manually configured.
    """
    name: str = "Default"
    geometry: GeometryParams = field(default_factory=GeometryParams)
    material: MaterialParams = field(default_factory=MaterialParams)
    surface: SurfaceParams = field(default_factory=SurfaceParams)
    custom_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_preset(cls, preset_name: str) -> "MorphTarget":
        """
        Create a morph target from a preset name.

        Args:
            preset_name: Name of preset (e.g., "neve_1073", "ssl_4000_e")

        Returns:
            MorphTarget instance with preset values
        """
        # Import here to avoid circular imports
        from .profiles import get_profile
        from .surface_features import get_preset

        # Get profile (geometry)
        try:
            profile = get_profile(preset_name.replace("_", "-"))
            geometry = GeometryParams(
                profile=profile.profile_type.value if hasattr(profile, 'profile_type') else "cylindrical",
                cap_height=profile.cap_height,
                cap_diameter=profile.cap_diameter,
                skirt_height=profile.skirt_height,
                skirt_diameter=profile.skirt_diameter,
                skirt_style=profile.skirt_style,
            )
        except (KeyError, AttributeError):
            geometry = GeometryParams()

        # Get surface features
        try:
            surface_features = get_preset(preset_name)
            surface = SurfaceParams(
                knurling_count=surface_features.knurling.count if surface_features.knurling else 0,
                knurling_depth=surface_features.knurling.depth if surface_features.knurling else 0,
                indicator_enabled=surface_features.indicator.enabled if surface_features.indicator else False,
            )
        except (KeyError, AttributeError):
            surface = SurfaceParams()

        return cls(
            name=preset_name,
            geometry=geometry,
            surface=surface,
        )

    def interpolate(
        self,
        other: "MorphTarget",
        t: float,
        use_lab_color: bool = True
    ) -> "MorphTarget":
        """
        Interpolate between this target and another.

        Args:
            other: Target morph target
            t: Interpolation factor (0.0 = this, 1.0 = other)
            use_lab_color: Use LAB color space for color interpolation

        Returns:
            New MorphTarget with interpolated values
        """
        return MorphTarget(
            name=f"{self.name}_to_{other.name}_{t:.2f}",
            geometry=self.geometry.interpolate(other.geometry, t),
            material=self.material.interpolate(other.material, t, use_lab_color),
            surface=self.surface.interpolate(other.surface, t),
            custom_params={
                k: self._interpolate_value(
                    self.custom_params.get(k),
                    other.custom_params.get(k),
                    t
                )
                for k in set(self.custom_params) | set(other.custom_params)
            }
        )

    @staticmethod
    def _interpolate_value(a: Any, b: Any, t: float) -> Any:
        """Interpolate between two values."""
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a + t * (b - a)
        if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b) == 3:
            return interpolate_color_lab(a, b, t)
        return a if t < 0.5 else b


# =============================================================================
# MORPH ANIMATION
# =============================================================================

@dataclass
class MorphKeyframe:
    """A single keyframe in a morph animation."""
    time: float  # Normalized time (0.0 to 1.0)
    value: float  # Morph factor (0.0 to 1.0)
    easing: EasingType = EasingType.LINEAR


@dataclass
class MorphAnimation:
    """
    Animation definition for morphing between two targets.

    Supports:
    - Duration control
    - Easing curves
    - Keyframe-based animation
    - Loop modes
    """
    source: MorphTarget
    target: MorphTarget
    duration: float = 1.0  # Duration in seconds
    easing: EasingType = EasingType.EASE_IN_OUT_CUBIC
    keyframes: List[MorphKeyframe] = field(default_factory=list)
    loop: bool = False
    ping_pong: bool = False

    def __post_init__(self):
        """Initialize default keyframes if not provided."""
        if not self.keyframes:
            self.keyframes = [
                MorphKeyframe(0.0, 0.0, self.easing),
                MorphKeyframe(1.0, 1.0, self.easing),
            ]
        else:
            # Sort keyframes by time
            self.keyframes.sort(key=lambda k: k.time)

    def evaluate(self, time: float) -> float:
        """
        Evaluate morph factor at given time.

        Args:
            time: Animation time (0.0 to duration)

        Returns:
            Morph factor (0.0 to 1.0)
        """
        # Normalize time
        t = time / self.duration if self.duration > 0 else 1.0

        # Handle looping
        if self.loop:
            t = t % 1.0
        elif self.ping_pong:
            cycle = int(t)
            t = t % 1.0
            if cycle % 2 == 1:
                t = 1.0 - t

        # Clamp to keyframe range
        t = max(0.0, min(1.0, t))

        # Find surrounding keyframes
        prev_kf = self.keyframes[0]
        next_kf = self.keyframes[-1]

        for i, kf in enumerate(self.keyframes):
            if kf.time <= t:
                prev_kf = kf
            if kf.time >= t and (next_kf.time < t or kf.time < next_kf.time):
                next_kf = kf
                break

        # Interpolate between keyframes
        if prev_kf.time == next_kf.time:
            local_t = 0.0
        else:
            local_t = (t - prev_kf.time) / (next_kf.time - prev_kf.time)

        # Apply easing to local interpolation
        eased_t = apply_easing(local_t, prev_kf.easing)

        # Interpolate value
        return prev_kf.value + eased_t * (next_kf.value - prev_kf.value)


# =============================================================================
# STAGGERED ANIMATION
# =============================================================================

@dataclass
class StaggerConfig:
    """Configuration for staggered animation."""
    stagger_type: str = "linear"  # linear, ease, random
    stagger_amount: float = 0.1  # Delay between items (normalized)
    stagger_direction: str = "forward"  # forward, backward, center, random
    random_seed: Optional[int] = None


@dataclass
class StaggeredMorph:
    """
    Staggered morph animation for multiple controls.

    Applies the same morph animation to multiple controls with
    staggered timing for a wave-like effect.
    """
    animation: MorphAnimation
    control_count: int
    stagger: StaggerConfig = field(default_factory=StaggerConfig)

    def get_control_times(self) -> List[float]:
        """
        Calculate start times for each control.

        Returns:
            List of start times (normalized, 0.0 to 1.0)
        """
        import random
        if self.stagger.random_seed is not None:
            random.seed(self.stagger.random_seed)

        n = self.control_count
        base_delays = []

        if self.stagger.stagger_direction == "forward":
            indices = list(range(n))
        elif self.stagger.stagger_direction == "backward":
            indices = list(range(n - 1, -1, -1))
        elif self.stagger.stagger_direction == "center":
            half = n // 2
            indices = [abs(i - half) for i in range(n)]
        elif self.stagger.stagger_direction == "random":
            indices = list(range(n))
            random.shuffle(indices)
        else:
            indices = list(range(n))

        # Calculate delays
        for i, idx in enumerate(indices):
            if self.stagger.stagger_type == "linear":
                delay = idx * self.stagger.stagger_amount
            elif self.stagger.stagger_type == "ease":
                delay = (idx / max(1, n - 1)) ** 2 * self.stagger.stagger_amount * (n - 1)
            elif self.stagger.stagger_type == "random":
                delay = random.random() * self.stagger.stagger_amount * (n - 1)
            else:
                delay = idx * self.stagger.stagger_amount

            base_delays.append((i, delay))

        # Sort back to original order
        base_delays.sort(key=lambda x: x[0])
        return [d[1] for d in base_delays]

    def evaluate_control(self, control_index: int, time: float) -> float:
        """
        Evaluate morph factor for a specific control at given time.

        Args:
            control_index: Index of control (0 to control_count - 1)
            time: Animation time (seconds)

        Returns:
            Morph factor (0.0 to 1.0)
        """
        delays = self.get_control_times()
        delay = delays[control_index] * self.animation.duration
        adjusted_time = time - delay
        return self.animation.evaluate(max(0, adjusted_time))


# =============================================================================
# MORPH ENGINE
# =============================================================================

class MorphEngine:
    """
    Main morphing engine for evaluating and applying morphs.

    Provides:
    - Real-time morph evaluation
    - Batch morphing of multiple controls
    - Per-group and per-control morph factors
    """

    def __init__(self):
        self.active_morphs: Dict[str, MorphAnimation] = {}
        self.group_factors: Dict[str, float] = {}

    def evaluate(
        self,
        animation: MorphAnimation,
        time: float,
        use_lab_color: bool = True
    ) -> MorphTarget:
        """
        Evaluate morph at given time.

        Args:
            animation: Morph animation to evaluate
            time: Animation time (seconds)
            use_lab_color: Use LAB color interpolation

        Returns:
            Interpolated MorphTarget
        """
        factor = animation.evaluate(time)
        return animation.source.interpolate(animation.target, factor, use_lab_color)

    def evaluate_staggered(
        self,
        staggered: StaggeredMorph,
        time: float
    ) -> List[MorphTarget]:
        """
        Evaluate staggered morph for all controls.

        Args:
            staggered: Staggered morph configuration
            time: Animation time (seconds)

        Returns:
            List of MorphTargets for each control
        """
        results = []
        for i in range(staggered.control_count):
            factor = staggered.evaluate_control(i, time)
            target = staggered.animation.source.interpolate(
                staggered.animation.target, factor
            )
            results.append(target)
        return results

    def set_group_factor(self, group_name: str, factor: float):
        """Set morph factor for a control group."""
        self.group_factors[group_name] = max(0.0, min(1.0, factor))

    def get_group_factor(self, group_name: str) -> float:
        """Get morph factor for a control group."""
        return self.group_factors.get(group_name, 0.0)

    def apply_group_factor(
        self,
        base_factor: float,
        group_name: str
    ) -> float:
        """
        Apply group-specific morph factor to base factor.

        Args:
            base_factor: Base morph factor (0.0 to 1.0)
            group_name: Name of control group

        Returns:
            Adjusted morph factor
        """
        group_factor = self.get_group_factor(group_name)
        return base_factor * group_factor


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def animate_morph(
    source: Union[str, MorphTarget],
    target: Union[str, MorphTarget],
    duration: float = 1.0,
    easing: EasingType = EasingType.EASE_IN_OUT_CUBIC
) -> MorphAnimation:
    """
    Create a morph animation between two presets or targets.

    Args:
        source: Source preset name or MorphTarget
        target: Target preset name or MorphTarget
        duration: Animation duration in seconds
        easing: Easing curve type

    Returns:
        MorphAnimation instance
    """
    if isinstance(source, str):
        source = MorphTarget.from_preset(source)
    if isinstance(target, str):
        target = MorphTarget.from_preset(target)

    return MorphAnimation(
        source=source,
        target=target,
        duration=duration,
        easing=easing
    )


def quick_morph(
    source: Union[str, MorphTarget],
    target: Union[str, MorphTarget],
    factor: float = 0.5,
    use_lab_color: bool = True
) -> MorphTarget:
    """
    Quick single morph evaluation without animation.

    Args:
        source: Source preset name or MorphTarget
        target: Target preset name or MorphTarget
        factor: Morph factor (0.0 = source, 1.0 = target)
        use_lab_color: Use LAB color interpolation

    Returns:
        Interpolated MorphTarget
    """
    if isinstance(source, str):
        source = MorphTarget.from_preset(source)
    if isinstance(target, str):
        target = MorphTarget.from_preset(target)

    return source.interpolate(target, factor, use_lab_color)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "EasingType",

    # Functions
    "apply_easing",
    "rgb_to_lab",
    "lab_to_rgb",
    "interpolate_color_lab",
    "animate_morph",
    "quick_morph",

    # Classes
    "GeometryParams",
    "MaterialParams",
    "SurfaceParams",
    "MorphTarget",
    "MorphKeyframe",
    "MorphAnimation",
    "StaggerConfig",
    "StaggeredMorph",
    "MorphEngine",
]
