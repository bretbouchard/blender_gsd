"""
Stunt Course Assembly Module

Build and validate complete stunt courses.

Phase 17.5: Stunt Course Assembly (REQ-STUNT-06)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import math

from .types import (
    StuntElement,
    StuntCourseConfig,
    CourseFlowAnalyzer,
    RampConfig,
    LoopConfig,
    BankedTurnConfig,
)
from .ramps import create_ramp, RAMP_PRESETS
from .loops import create_loop, create_banked_turn, LOOP_PRESETS
from .physics import calculate_optimal_trajectory
from .launch_control import LaunchController, suggest_speed_adjustments


# Predefined course presets
COURSE_PRESETS: Dict[str, Dict[str, Any]] = {
    "beginner_course": {
        "name": "Beginner Stunt Course",
        "difficulty": "easy",
        "elements": [
            {"type": "ramp", "preset": "beginner_kicker", "distance": 5.0},
            {"type": "ramp", "preset": "beginner_table", "distance": 8.0},
            {"type": "turn", "preset": "gentle_turn", "distance": 5.0},
        ],
    },
    "intermediate_course": {
        "name": "Intermediate Stunt Course",
        "difficulty": "medium",
        "elements": [
            {"type": "ramp", "preset": "intermediate_kicker", "distance": 10.0},
            {"type": "turn", "preset": "medium_turn", "distance": 5.0},
            {"type": "ramp", "preset": "intermediate_table", "distance": 12.0},
            {"type": "loop", "preset": "small_loop", "distance": 5.0},
        ],
    },
    "pro_course": {
        "name": "Professional Stunt Course",
        "difficulty": "hard",
        "elements": [
            {"type": "ramp", "preset": "advanced_kicker", "distance": 15.0},
            {"type": "loop", "preset": "medium_loop", "distance": 5.0},
            {"type": "turn", "preset": "tight_turn", "distance": 3.0},
            {"type": "ramp", "preset": "pro_table", "distance": 18.0},
            {"type": "loop", "preset": "large_loop", "distance": 5.0},
        ],
    },
    "extreme_course": {
        "name": "Extreme Stunt Course",
        "difficulty": "extreme",
        "elements": [
            {"type": "ramp", "preset": "advanced_kicker", "distance": 20.0},
            {"type": "loop", "preset": "large_loop", "distance": 5.0},
            {"type": "turn", "preset": "hairpin", "distance": 3.0},
            {"type": "ramp", "preset": "pro_table", "distance": 25.0},
            {"type": "loop", "preset": "clothoid_loop", "distance": 5.0},
            {"type": "ramp", "preset": "spine_double", "distance": 12.0},
        ],
    },
}


class StuntCourseBuilder:
    """
    Builder for creating stunt courses.

    Provides fluent interface for adding elements and
    automatically calculating positions and speeds.
    """

    def __init__(self, course_id: str, name: str = "Untitled Course"):
        """
        Initialize course builder.

        Args:
            course_id: Unique course identifier
            name: Course display name
        """
        self.course_id = course_id
        self.name = name
        self.elements: List[StuntElement] = []
        self.current_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.current_dir: float = 0.0  # degrees
        self.current_speed: float = 20.0  # m/s
        self.launch_controller = LaunchController()
        self._element_counter = 0

    def set_start(
        self,
        position: Tuple[float, float, float],
        direction: float = 0.0,
        speed: float = 20.0,
    ) -> "StuntCourseBuilder":
        """Set starting position and direction.

        Args:
            position: Starting position (x, y, z)
            direction: Initial direction in degrees
            speed: Initial speed in m/s

        Returns:
            Self for chaining
        """
        self.current_pos = position
        self.current_dir = direction
        self.current_speed = speed
        return self

    def add_ramp(
        self,
        preset: Optional[str] = None,
        distance: float = 10.0,
        height_diff: float = 0.0,
        **kwargs,
    ) -> "StuntCourseBuilder":
        """Add a ramp element.

        Args:
            preset: Ramp preset name
            distance: Jump distance
            height_diff: Height difference
            **kwargs: Additional ramp configuration

        Returns:
            Self for chaining
        """
        # Create ramp config
        if preset and preset.lower() in RAMP_PRESETS:
            config = RAMP_PRESETS[preset.lower()]
        else:
            config = create_ramp(
                ramp_type=kwargs.get('ramp_type'),
                width=kwargs.get('width', 4.0),
                height=kwargs.get('height', 2.0),
                length=kwargs.get('length', 6.0),
                angle=kwargs.get('angle', 30.0),
            )

        # Calculate trajectory
        trajectory = calculate_optimal_trajectory(distance, height_diff)
        entry_speed = trajectory['required_speed']
        exit_speed = entry_speed * 0.85  # Landing loss

        # Calculate element position
        element_pos = self._calculate_element_position(distance)

        # Create element
        element = StuntElement(
            element_id=f"{self.course_id}_elem_{self._element_counter}",
            element_type="ramp",
            config=config.to_dict() if hasattr(config, 'to_dict') else {},
            position=element_pos,
            rotation=self.current_dir,
            entry_speed=entry_speed,
            exit_speed=exit_speed,
            duration_frames=int(trajectory['air_time'] * 24),
        )

        self.elements.append(element)
        self._element_counter += 1
        self.current_pos = element_pos
        self.current_speed = exit_speed

        return self

    def add_loop(
        self,
        preset: Optional[str] = None,
        radius: float = 5.0,
        **kwargs,
    ) -> "StuntCourseBuilder":
        """Add a loop element.

        Args:
            preset: Loop preset name
            radius: Loop radius
            **kwargs: Additional loop configuration

        Returns:
            Self for chaining
        """
        # Create loop config
        config = LoopConfig(
            radius=radius,
            width=kwargs.get('width', 5.0),
        )

        # Calculate required speed
        min_speed = config.get_min_speed()
        entry_speed = min_speed * 1.2
        exit_speed = min_speed * 0.9

        # Calculate element position
        element_pos = self._calculate_element_position(radius * 2)

        element = StuntElement(
            element_id=f"{self.course_id}_elem_{self._element_counter}",
            element_type="loop",
            config={'radius': radius, 'width': config.width},
            position=element_pos,
            rotation=self.current_dir,
            entry_speed=entry_speed,
            exit_speed=exit_speed,
            duration_frames=int(2 * math.pi * radius / entry_speed * 24),
        )

        self.elements.append(element)
        self._element_counter += 1
        self.current_pos = element_pos
        self.current_speed = exit_speed

        return self

    def add_turn(
        self,
        angle: float = 90.0,
        radius: float = 15.0,
        bank_angle: float = 35.0,
        **kwargs,
    ) -> "StuntCourseBuilder":
        """Add a banked turn element.

        Args:
            angle: Turn angle in degrees
            radius: Turn radius
            bank_angle: Banking angle
            **kwargs: Additional turn configuration

        Returns:
            Self for chaining
        """
        config = BankedTurnConfig(
            radius=radius,
            angle=bank_angle,
            arc_degrees=angle,
        )

        # Design speed
        design_speed = config.get_design_speed()
        entry_speed = design_speed
        exit_speed = design_speed * 0.95

        # Update direction
        self.current_dir += angle

        # Calculate element position
        arc_length = radius * math.radians(angle)
        element_pos = self._calculate_element_position(arc_length)

        element = StuntElement(
            element_id=f"{self.course_id}_elem_{self._element_counter}",
            element_type="turn",
            config={
                'radius': radius,
                'bank_angle': bank_angle,
                'arc_degrees': angle,
            },
            position=element_pos,
            rotation=self.current_dir - angle,
            entry_speed=entry_speed,
            exit_speed=exit_speed,
            duration_frames=int(arc_length / design_speed * 24),
        )

        self.elements.append(element)
        self._element_counter += 1
        self.current_pos = element_pos
        self.current_speed = exit_speed

        return self

    def add_run(self, distance: float) -> "StuntCourseBuilder":
        """Add a straight run section.

        Args:
            distance: Run distance in meters

        Returns:
            Self for chaining
        """
        element_pos = self._calculate_element_position(distance)

        # Speed loss from coasting (2% per 10m)
        speed_loss = 0.02 * (distance / 10)
        exit_speed = self.current_speed * (1 - speed_loss)

        element = StuntElement(
            element_id=f"{self.course_id}_elem_{self._element_counter}",
            element_type="run",
            config={'distance': distance},
            position=element_pos,
            rotation=self.current_dir,
            entry_speed=self.current_speed,
            exit_speed=exit_speed,
            duration_frames=int(distance / self.current_speed * 24),
        )

        self.elements.append(element)
        self._element_counter += 1
        self.current_pos = element_pos
        self.current_speed = exit_speed

        return self

    def _calculate_element_position(
        self, distance: float
    ) -> Tuple[float, float, float]:
        """Calculate position after moving distance in current direction."""
        dir_rad = math.radians(self.current_dir)
        return (
            self.current_pos[0] + distance * math.cos(dir_rad),
            self.current_pos[1] + distance * math.sin(dir_rad),
            self.current_pos[2],
        )

    def build(self, difficulty: str = "medium") -> StuntCourseConfig:
        """Build the final course configuration.

        Args:
            difficulty: Course difficulty rating

        Returns:
            Complete StuntCourseConfig
        """
        # Link elements
        for i, element in enumerate(self.elements):
            if i > 0:
                element.prev_element = self.elements[i - 1].element_id
            if i < len(self.elements) - 1:
                element.next_element = self.elements[i + 1].element_id

        # Calculate totals
        total_length = sum(
            self._calculate_element_length(e) for e in self.elements
        )
        total_frames = sum(e.duration_frames for e in self.elements)
        total_duration = total_frames / 24  # seconds

        # Find speed range
        speeds = [e.entry_speed for e in self.elements]
        min_speed = min(speeds) if speeds else 15.0
        max_speed = max(speeds) if speeds else 40.0

        return StuntCourseConfig(
            course_id=self.course_id,
            name=self.name,
            elements=self.elements,
            total_length=total_length,
            total_duration=total_duration,
            difficulty=difficulty,
            min_speed=min_speed,
            max_speed=max_speed,
        )

    def _calculate_element_length(self, element: StuntElement) -> float:
        """Calculate approximate length of an element."""
        config = element.config

        if element.element_type == "ramp":
            return config.get("length", 6.0) + config.get("distance", 10.0)
        elif element.element_type == "loop":
            return 2 * math.pi * config.get("radius", 5.0)
        elif element.element_type == "turn":
            return config.get("radius", 15.0) * math.radians(
                config.get("arc_degrees", 90.0)
            )
        elif element.element_type == "run":
            return config.get("distance", 10.0)
        else:
            return 10.0


def add_element_to_course(
    course: StuntCourseConfig,
    element_type: str,
    config: Dict[str, Any],
    position: Optional[Tuple[float, float, float]] = None,
    after_element: Optional[str] = None,
) -> StuntCourseConfig:
    """Add an element to an existing course.

    Args:
        course: Existing course configuration
        element_type: Type of element to add
        config: Element configuration
        position: Optional position (auto-calculated if None)
        after_element: Optional element ID to insert after

    Returns:
        Updated course configuration
    """
    # Create new element
    new_element = StuntElement(
        element_id=f"{course.course_id}_elem_{len(course.elements)}",
        element_type=element_type,
        config=config,
        position=position or (0, 0, 0),
        rotation=0.0,
        entry_speed=config.get("entry_speed", 20.0),
        exit_speed=config.get("exit_speed", 18.0),
        duration_frames=config.get("duration_frames", 48),
    )

    # Insert element
    if after_element:
        insert_idx = None
        for i, elem in enumerate(course.elements):
            if elem.element_id == after_element:
                insert_idx = i + 1
                break
        if insert_idx is not None:
            course.elements.insert(insert_idx, new_element)
        else:
            course.elements.append(new_element)
    else:
        course.elements.append(new_element)

    return course


def analyze_course_flow(course: StuntCourseConfig) -> Dict[str, Any]:
    """Analyze course flow and identify issues.

    Args:
        course: Course configuration

    Returns:
        Analysis results
    """
    analyzer = CourseFlowAnalyzer(course)
    is_safe = analyzer.analyze()

    return {
        "is_safe": is_safe,
        "warnings": analyzer.warnings,
        "speed_profile": analyzer.get_speed_graph(),
        "element_count": len(course.elements),
        "total_duration": course.total_duration,
        "difficulty": course.difficulty,
    }


def validate_course(course: StuntCourseConfig) -> Tuple[bool, List[str]]:
    """Validate course configuration.

    Args:
        course: Course configuration

    Returns:
        Tuple of (is_valid, issues)
    """
    issues = []

    # Check for empty course
    if not course.elements:
        issues.append("Course has no elements")
        return False, issues

    # Check element connections
    for i, element in enumerate(course.elements):
        if i > 0 and element.prev_element != course.elements[i - 1].element_id:
            issues.append(f"Element {element.element_id} has broken previous link")
        if i < len(course.elements) - 1 and element.next_element != course.elements[i + 1].element_id:
            issues.append(f"Element {element.element_id} has broken next link")

    # Check speed continuity
    for i in range(len(course.elements) - 1):
        current = course.elements[i]
        next_elem = course.elements[i + 1]

        speed_gap = next_elem.entry_speed - current.exit_speed
        if speed_gap > 10.0:
            issues.append(
                f"Speed gap between {current.element_id} and {next_elem.element_id}: "
                f"need +{speed_gap:.1f} m/s"
            )
        elif speed_gap < -15.0:
            issues.append(
                f"Excessive speed loss between {current.element_id} and "
                f"{next_elem.element_id}: {abs(speed_gap):.1f} m/s"
            )

    # Check difficulty alignment
    speed_range = course.max_speed - course.min_speed
    if course.difficulty == "easy" and speed_range > 15:
        issues.append("Easy course has wide speed range")
    elif course.difficulty == "extreme" and speed_range < 10:
        issues.append("Extreme course has narrow speed range")

    return len(issues) == 0, issues


def create_course_from_preset(
    preset_name: str,
    course_id: Optional[str] = None,
) -> Optional[StuntCourseConfig]:
    """Create a course from a preset.

    Args:
        preset_name: Name of the preset
        course_id: Optional custom course ID

    Returns:
        StuntCourseConfig or None if preset not found
    """
    preset = COURSE_PRESETS.get(preset_name.lower())
    if preset is None:
        return None

    builder = StuntCourseBuilder(
        course_id=course_id or preset_name,
        name=preset["name"],
    )

    builder.set_start((0, 0, 0), 0, 20)

    for element in preset["elements"]:
        elem_type = element["type"]

        if elem_type == "ramp":
            builder.add_ramp(preset=element.get("preset"), distance=element.get("distance", 10))
        elif elem_type == "loop":
            builder.add_loop(preset=element.get("preset"))
        elif elem_type == "turn":
            builder.add_turn(
                angle=element.get("angle", 90),
                radius=element.get("radius", 15),
            )
        elif elem_type == "run":
            builder.add_run(element.get("distance", 10))

    return builder.build(difficulty=preset.get("difficulty", "medium"))


def export_course_to_dict(course: StuntCourseConfig) -> Dict[str, Any]:
    """Export course configuration to dictionary.

    Args:
        course: Course configuration

    Returns:
        Dictionary representation
    """
    return {
        "course_id": course.course_id,
        "name": course.name,
        "difficulty": course.difficulty,
        "total_length": course.total_length,
        "total_duration": course.total_duration,
        "min_speed": course.min_speed,
        "max_speed": course.max_speed,
        "elements": [
            {
                "element_id": e.element_id,
                "element_type": e.element_type,
                "config": e.config,
                "position": e.position,
                "rotation": e.rotation,
                "entry_speed": e.entry_speed,
                "exit_speed": e.exit_speed,
                "duration_frames": e.duration_frames,
                "prev_element": e.prev_element,
                "next_element": e.next_element,
            }
            for e in course.elements
        ],
    }


def get_course_preset(name: str) -> Optional[Dict[str, Any]]:
    """Get a course preset by name.

    Args:
        name: Preset name

    Returns:
        Preset dictionary or None
    """
    return COURSE_PRESETS.get(name.lower())


def list_course_presets() -> List[str]:
    """List all available course presets.

    Returns:
        List of preset names
    """
    return list(COURSE_PRESETS.keys())
