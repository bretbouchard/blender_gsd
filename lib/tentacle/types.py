"""
Tentacle System Types

Core data types for procedural tentacle generation.

Primary use case: Zombie mouth tentacles for horror characters.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class SegmentConfig:
    """Segmentation control for tentacle body.

    Controls how the tentacle is divided into segments along its length.
    Segments are used for procedural animation and organic variation.

    Attributes:
        count: Number of segments along the tentacle (10-50)
        curve_resolution: Points per segment for smooth curve interpolation
        uniform: If True, all segments have equal length; if False, allows variation
        variation: Random variation in segment length (0.0-0.2), only used if uniform=False
    """

    count: int = 20
    curve_resolution: int = 64
    uniform: bool = True
    variation: float = 0.0

    def __post_init__(self):
        """Validate segment configuration."""
        if not 10 <= self.count <= 50:
            raise ValueError(f"Segment count must be between 10 and 50, got {self.count}")
        if not 16 <= self.curve_resolution <= 128:
            raise ValueError(
                f"Curve resolution must be between 16 and 128, got {self.curve_resolution}"
            )
        if not 0.0 <= self.variation <= 0.2:
            raise ValueError(f"Variation must be between 0.0 and 0.2, got {self.variation}")


@dataclass
class TaperProfile:
    """Radius profile along tentacle length.

    Defines how the tentacle's radius changes from base to tip.
    Supports built-in profiles (linear, smooth, organic) or custom point-based profiles.

    Attributes:
        profile_type: Type of taper profile ("linear", "smooth", "organic", "custom")
        points: Custom profile points as [(position_0_to_1, radius_factor), ...].
                Empty list uses built-in profile calculations.
        base_ratio: Ratio of base_diameter to tip_diameter for organic profiles
        mid_point: Position (0-1) where taper starts accelerating for organic profiles
        smoothness: Curve interpolation smoothness (0-1) for organic profiles
    """

    profile_type: str = "organic"
    points: List[Tuple[float, float]] = field(default_factory=list)
    base_ratio: float = 2.5
    mid_point: float = 0.4
    smoothness: float = 0.5

    VALID_PROFILE_TYPES = ("linear", "smooth", "organic", "custom")

    def __post_init__(self):
        """Validate taper profile configuration."""
        if self.profile_type not in self.VALID_PROFILE_TYPES:
            raise ValueError(
                f"Invalid profile_type '{self.profile_type}'. "
                f"Must be one of {self.VALID_PROFILE_TYPES}"
            )
        if not 1.0 <= self.base_ratio <= 10.0:
            raise ValueError(f"base_ratio must be between 1.0 and 10.0, got {self.base_ratio}")
        if not 0.0 <= self.mid_point <= 1.0:
            raise ValueError(f"mid_point must be between 0.0 and 1.0, got {self.mid_point}")
        if not 0.0 <= self.smoothness <= 1.0:
            raise ValueError(f"smoothness must be between 0.0 and 1.0, got {self.smoothness}")

        # Validate custom points if provided
        for i, (pos, radius) in enumerate(self.points):
            if not 0.0 <= pos <= 1.0:
                raise ValueError(f"Point {i} position must be between 0.0 and 1.0, got {pos}")
            if not 0.0 <= radius <= 2.0:
                raise ValueError(f"Point {i} radius must be between 0.0 and 2.0, got {radius}")

    def get_radius_at(self, t: float) -> float:
        """Calculate radius factor at position t (0-1) along the tentacle.

        Args:
            t: Position along tentacle length (0=base, 1=tip)

        Returns:
            Radius factor (1.0 = full base radius, 0.0 = zero radius)
        """
        if not 0.0 <= t <= 1.0:
            raise ValueError(f"Position t must be between 0.0 and 1.0, got {t}")

        # Custom points take precedence
        if self.points:
            # Sort points by position
            sorted_points = sorted(self.points, key=lambda p: p[0])

            # Handle edge cases
            if t <= sorted_points[0][0]:
                return sorted_points[0][1]
            if t >= sorted_points[-1][0]:
                return sorted_points[-1][1]

            # Linear interpolation between points
            for i in range(len(sorted_points) - 1):
                p1_pos, p1_rad = sorted_points[i]
                p2_pos, p2_rad = sorted_points[i + 1]
                if p1_pos <= t <= p2_pos:
                    ratio = (t - p1_pos) / (p2_pos - p1_pos)
                    return p1_rad + ratio * (p2_rad - p1_rad)

        # Built-in profiles
        if self.profile_type == "linear":
            # Linear taper from base to tip
            return 1.0 - t * (1.0 - 1.0 / self.base_ratio)

        elif self.profile_type == "smooth":
            # Smooth ease-in-out taper using hermite interpolation
            # Maps t through a smooth S-curve
            smooth_t = t * t * (3.0 - 2.0 * t)
            return 1.0 - smooth_t * (1.0 - 1.0 / self.base_ratio)

        elif self.profile_type == "organic":
            # Natural bulbous shape with acceleration at mid_point
            # Uses a combination of smooth curves for organic feel
            if t < self.mid_point:
                # Gradual taper in first section
                local_t = t / self.mid_point
                smooth_local = local_t * local_t * (3.0 - 2.0 * local_t)
                mid_radius = 1.0 - self.smoothness * 0.3  # Slight bulge at mid
                return 1.0 - smooth_local * (1.0 - mid_radius) * self.smoothness
            else:
                # Accelerated taper in second section
                local_t = (t - self.mid_point) / (1.0 - self.mid_point)
                smooth_local = local_t * local_t
                mid_radius = 1.0 - self.smoothness * 0.3
                tip_radius = 1.0 / self.base_ratio
                return mid_radius - smooth_local * (mid_radius - tip_radius)

        # Fallback to linear
        return 1.0 - t * (1.0 - 1.0 / self.base_ratio)


@dataclass
class TentacleConfig:
    """Configuration for procedural tentacle generation.

    This is the primary configuration class for creating tentacles.
    All measurements are in meters for consistency with Blender's default units.

    Attributes:
        length: Total tentacle length in meters (0.1 - 3.0)
        base_diameter: Diameter at the base in meters (0.02 - 0.20)
        tip_diameter: Diameter at the tip in meters (0.005 - 0.10)
        segments: Number of segments along length (10 - 50)
        curve_resolution: Points per segment for smooth curve (16 - 128)
        taper_profile: Type of taper profile ("linear", "smooth", "organic", "custom")
        twist: Total twist along length in degrees
        subdivision_levels: Subdivision surface levels for smooth mesh (0 - 4)
        seed: Random seed for reproducible procedural generation
        name: Blender object name
    """

    # Dimensions
    length: float = 1.0
    base_diameter: float = 0.08
    tip_diameter: float = 0.02

    # Segmentation
    segments: int = 20
    curve_resolution: int = 64

    # Shape
    taper_profile: str = "organic"
    twist: float = 0.0

    # Quality
    subdivision_levels: int = 2

    # Determinism
    seed: int = 42

    # Name
    name: str = "Tentacle"

    def __post_init__(self):
        """Validate tentacle configuration."""
        # Validate length range
        if not 0.1 <= self.length <= 3.0:
            raise ValueError(f"Length must be between 0.1 and 3.0 meters, got {self.length}")

        # Validate diameter ranges
        if not 0.02 <= self.base_diameter <= 0.20:
            raise ValueError(
                f"base_diameter must be between 0.02 and 0.20 meters, got {self.base_diameter}"
            )
        if not 0.005 <= self.tip_diameter <= 0.10:
            raise ValueError(
                f"tip_diameter must be between 0.005 and 0.10 meters, got {self.tip_diameter}"
            )

        # Validate tip is smaller than base
        if self.tip_diameter >= self.base_diameter:
            raise ValueError(
                f"tip_diameter ({self.tip_diameter}) must be smaller than "
                f"base_diameter ({self.base_diameter})"
            )

        # Validate segment count
        if not 10 <= self.segments <= 50:
            raise ValueError(f"segments must be between 10 and 50, got {self.segments}")

        # Validate curve resolution
        if not 16 <= self.curve_resolution <= 128:
            raise ValueError(
                f"curve_resolution must be between 16 and 128, got {self.curve_resolution}"
            )

        # Validate taper profile type
        valid_profiles = ("linear", "smooth", "organic", "custom")
        if self.taper_profile not in valid_profiles:
            raise ValueError(
                f"taper_profile must be one of {valid_profiles}, got '{self.taper_profile}'"
            )

        # Validate subdivision levels
        if not 0 <= self.subdivision_levels <= 4:
            raise ValueError(
                f"subdivision_levels must be between 0 and 4, got {self.subdivision_levels}"
            )

    @property
    def taper_ratio(self) -> float:
        """Calculate the taper ratio (base/tip)."""
        return self.base_diameter / self.tip_diameter

    @property
    def segment_length(self) -> float:
        """Calculate the length of each segment."""
        return self.length / self.segments

    def get_diameter_at(self, t: float) -> float:
        """Get the diameter at position t (0-1) along the tentacle.

        Args:
            t: Position along tentacle length (0=base, 1=tip)

        Returns:
            Diameter in meters at position t
        """
        # Create a taper profile for calculation
        profile = TaperProfile(
            profile_type=self.taper_profile,
            base_ratio=self.taper_ratio,
        )
        radius_factor = profile.get_radius_at(t)
        return self.base_diameter * radius_factor


@dataclass
class ZombieMouthConfig:
    """Configuration for zombie mouth tentacle attachment.

    Defines how multiple tentacles are arranged around a zombie's mouth
    opening for horror character effects.

    Attributes:
        tentacle_count: Number of tentacles (1-6)
        distribution: How tentacles are distributed ("uniform", "random", "staggered")
        size_mix: Balance between main and feeler tentacles (0=all thin, 1=all thick)
        spread_angle: Angular spread across the mouth in degrees
        main_tentacle: Configuration for primary/thicker tentacles
        feeler_tentacle: Configuration for thinner feeler tentacles (optional)
    """

    tentacle_count: int = 4
    distribution: str = "staggered"
    size_mix: float = 0.5
    spread_angle: float = 60.0

    # Individual tentacle configs
    main_tentacle: TentacleConfig = field(default_factory=TentacleConfig)
    feeler_tentacle: Optional[TentacleConfig] = None

    VALID_DISTRIBUTIONS = ("uniform", "random", "staggered")

    def __post_init__(self):
        """Validate zombie mouth configuration."""
        if not 1 <= self.tentacle_count <= 6:
            raise ValueError(
                f"tentacle_count must be between 1 and 6, got {self.tentacle_count}"
            )

        if self.distribution not in self.VALID_DISTRIBUTIONS:
            raise ValueError(
                f"distribution must be one of {self.VALID_DISTRIBUTIONS}, "
                f"got '{self.distribution}'"
            )

        if not 0.0 <= self.size_mix <= 1.0:
            raise ValueError(f"size_mix must be between 0.0 and 1.0, got {self.size_mix}")

        if not 10.0 <= self.spread_angle <= 180.0:
            raise ValueError(
                f"spread_angle must be between 10.0 and 180.0 degrees, got {self.spread_angle}"
            )

    def get_tentacle_angles(self) -> List[float]:
        """Calculate the angle for each tentacle based on distribution.

        Returns:
            List of angles in degrees, centered around 0 (forward)
        """
        import random

        angles = []
        half_spread = self.spread_angle / 2.0

        if self.distribution == "uniform":
            # Evenly spaced across the spread
            if self.tentacle_count == 1:
                angles = [0.0]
            else:
                step = self.spread_angle / (self.tentacle_count - 1)
                angles = [-half_spread + i * step for i in range(self.tentacle_count)]

        elif self.distribution == "random":
            # Random positions within the spread
            random.seed(hash((self.main_tentacle.seed, "zombie_mouth_angles")))
            angles = sorted([
                random.uniform(-half_spread, half_spread)
                for _ in range(self.tentacle_count)
            ])

        elif self.distribution == "staggered":
            # Alternating left/right from center
            if self.tentacle_count == 1:
                angles = [0.0]
            else:
                step = self.spread_angle / self.tentacle_count
                angles = []
                for i in range(self.tentacle_count):
                    # Alternate left and right
                    offset = ((i + 1) // 2) * step
                    if i % 2 == 0:
                        angles.append(-offset)
                    else:
                        angles.append(offset)
                angles.sort()

        return angles

    def get_tentacle_configs(self) -> List[TentacleConfig]:
        """Get configurations for each tentacle based on size_mix.

        Returns:
            List of TentacleConfig objects for each tentacle
        """
        import random

        configs = []
        random.seed(hash((self.main_tentacle.seed, "zombie_mouth_sizes")))

        for i in range(self.tentacle_count):
            # Determine if this tentacle is main or feeler based on size_mix
            use_main = random.random() < self.size_mix

            if use_main or self.feeler_tentacle is None:
                # Use main tentacle config with unique name
                config = TentacleConfig(
                    length=self.main_tentacle.length,
                    base_diameter=self.main_tentacle.base_diameter,
                    tip_diameter=self.main_tentacle.tip_diameter,
                    segments=self.main_tentacle.segments,
                    curve_resolution=self.main_tentacle.curve_resolution,
                    taper_profile=self.main_tentacle.taper_profile,
                    twist=self.main_tentacle.twist,
                    subdivision_levels=self.main_tentacle.subdivision_levels,
                    seed=self.main_tentacle.seed + i,
                    name=f"{self.main_tentacle.name}_{i:02d}",
                )
            else:
                # Use feeler tentacle config with unique name
                config = TentacleConfig(
                    length=self.feeler_tentacle.length,
                    base_diameter=self.feeler_tentacle.base_diameter,
                    tip_diameter=self.feeler_tentacle.tip_diameter,
                    segments=self.feeler_tentacle.segments,
                    curve_resolution=self.feeler_tentacle.curve_resolution,
                    taper_profile=self.feeler_tentacle.taper_profile,
                    twist=self.feeler_tentacle.twist,
                    subdivision_levels=self.feeler_tentacle.subdivision_levels,
                    seed=self.feeler_tentacle.seed + i,
                    name=f"{self.feeler_tentacle.name}_{i:02d}",
                )

            configs.append(config)

        return configs
