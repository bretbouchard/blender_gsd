"""
Shot Generator Types - Data structures for shot list generation.

Implements REQ-SHOT-01, REQ-SHOT-02, REQ-SHOT-03
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json


@dataclass
class ShotSuggestion:
    """Suggested shot configuration.

    Represents a single shot suggestion derived from scene analysis.
    """
    scene_number: int
    shot_number: int
    shot_size: str  # ecu, cu, mcu, m, mf, f, w, ew
    camera_angle: str  # eye_level, high, low, dutch, birds_eye, worms_eye
    subject: str
    purpose: str  # coverage, reaction, insert, establishing, transition
    estimated_duration: float = 0.0  # seconds
    priority: str = "recommended"  # essential, recommended, optional
    description: str = ""
    camera_move: str = ""  # static, pan, tilt, dolly, crane, handheld
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scene_number": self.scene_number,
            "shot_number": self.shot_number,
            "shot_size": self.shot_size,
            "camera_angle": self.camera_angle,
            "subject": self.subject,
            "purpose": self.purpose,
            "estimated_duration": self.estimated_duration,
            "priority": self.priority,
            "description": self.description,
            "camera_move": self.camera_move,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShotSuggestion":
        """Deserialize from dictionary."""
        return cls(
            scene_number=data["scene_number"],
            shot_number=data["shot_number"],
            shot_size=data["shot_size"],
            camera_angle=data["camera_angle"],
            subject=data["subject"],
            purpose=data["purpose"],
            estimated_duration=data.get("estimated_duration", 0.0),
            priority=data.get("priority", "recommended"),
            description=data.get("description", ""),
            camera_move=data.get("camera_move", ""),
            notes=data.get("notes", "")
        )

    def get_shot_label(self) -> str:
        """Get human-readable shot label (e.g., '1A', '2B')."""
        return f"{self.scene_number}{chr(65 + self.shot_number - 1)}"

    def get_shot_size_name(self) -> str:
        """Get full name of shot size."""
        shot_size_names = {
            "ecu": "Extreme Close-Up",
            "cu": "Close-Up",
            "mcu": "Medium Close-Up",
            "m": "Medium Shot",
            "mf": "Medium Full Shot",
            "f": "Full Shot",
            "w": "Wide Shot",
            "ew": "Extreme Wide Shot"
        }
        return shot_size_names.get(self.shot_size.lower(), self.shot_size)


@dataclass
class CoverageEstimate:
    """Coverage analysis for a scene.

    Provides shot counts for different coverage types.
    """
    scene_number: int
    master_shots: int = 0
    closeups: int = 0
    inserts: int = 0
    reactions: int = 0
    two_shots: int = 0
    establishing_shots: int = 0
    total_estimated: int = 0
    minimum_coverage: int = 0
    recommended_coverage: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scene_number": self.scene_number,
            "master_shots": self.master_shots,
            "closeups": self.closeups,
            "inserts": self.inserts,
            "reactions": self.reactions,
            "two_shots": self.two_shots,
            "establishing_shots": self.establishing_shots,
            "total_estimated": self.total_estimated,
            "minimum_coverage": self.minimum_coverage,
            "recommended_coverage": self.recommended_coverage
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoverageEstimate":
        """Deserialize from dictionary."""
        return cls(
            scene_number=data["scene_number"],
            master_shots=data.get("master_shots", 0),
            closeups=data.get("closeups", 0),
            inserts=data.get("inserts", 0),
            reactions=data.get("reactions", 0),
            two_shots=data.get("two_shots", 0),
            establishing_shots=data.get("establishing_shots", 0),
            total_estimated=data.get("total_estimated", 0),
            minimum_coverage=data.get("minimum_coverage", 0),
            recommended_coverage=data.get("recommended_coverage", 0)
        )

    def calculate_totals(self):
        """Calculate total shot counts."""
        self.total_estimated = (
            self.master_shots + self.closeups + self.inserts +
            self.reactions + self.two_shots + self.establishing_shots
        )


@dataclass
class SceneShotList:
    """Shot list for a single scene.

    Contains all shots and coverage estimates for a scene.
    """
    scene_number: int
    scene_heading: str
    shots: List[ShotSuggestion] = field(default_factory=list)
    coverage: Optional[CoverageEstimate] = None
    estimated_duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scene_number": self.scene_number,
            "scene_heading": self.scene_heading,
            "shots": [s.to_dict() for s in self.shots],
            "coverage": self.coverage.to_dict() if self.coverage else None,
            "estimated_duration": self.estimated_duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneShotList":
        """Deserialize from dictionary."""
        return cls(
            scene_number=data["scene_number"],
            scene_heading=data["scene_heading"],
            shots=[ShotSuggestion.from_dict(s) for s in data.get("shots", [])],
            coverage=CoverageEstimate.from_dict(data["coverage"]) if data.get("coverage") else None,
            estimated_duration=data.get("estimated_duration", 0.0)
        )

    def get_shot_count(self) -> int:
        """Get total number of shots."""
        return len(self.shots)

    def get_essential_shots(self) -> List[ShotSuggestion]:
        """Get essential priority shots."""
        return [s for s in self.shots if s.priority == "essential"]

    def get_recommended_shots(self) -> List[ShotSuggestion]:
        """Get recommended priority shots."""
        return [s for s in self.shots if s.priority == "recommended"]

    def get_optional_shots(self) -> List[ShotSuggestion]:
        """Get optional priority shots."""
        return [s for s in self.shots if s.priority == "optional"]


@dataclass
class ShotList:
    """Complete shot list for a production.

    Contains all scene shot lists and overall statistics.
    """
    production: str
    scenes: Dict[int, SceneShotList] = field(default_factory=dict)
    total_shots: int = 0
    estimated_total_duration: float = 0.0
    date_created: str = ""
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "production": self.production,
            "scenes": {str(k): v.to_dict() for k, v in self.scenes.items()},
            "total_shots": self.total_shots,
            "estimated_total_duration": self.estimated_total_duration,
            "date_created": self.date_created,
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShotList":
        """Deserialize from dictionary."""
        scenes = {}
        for k, v in data.get("scenes", {}).items():
            scenes[int(k)] = SceneShotList.from_dict(v)

        return cls(
            production=data["production"],
            scenes=scenes,
            total_shots=data.get("total_shots", 0),
            estimated_total_duration=data.get("estimated_total_duration", 0.0),
            date_created=data.get("date_created", ""),
            version=data.get("version", "1.0")
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "ShotList":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def calculate_totals(self):
        """Calculate total shots and duration."""
        self.total_shots = sum(s.get_shot_count() for s in self.scenes.values())
        self.estimated_total_duration = sum(
            s.estimated_duration for s in self.scenes.values()
        )

    def get_all_shots(self) -> List[ShotSuggestion]:
        """Get all shots across all scenes."""
        shots = []
        for scene in sorted(self.scenes.keys()):
            shots.extend(self.scenes[scene].shots)
        return shots

    def get_scene(self, scene_number: int) -> Optional[SceneShotList]:
        """Get shot list for a specific scene."""
        return self.scenes.get(scene_number)

    def add_scene(self, scene_shot_list: SceneShotList):
        """Add a scene shot list."""
        self.scenes[scene_shot_list.scene_number] = scene_shot_list
        self.calculate_totals()

    def get_statistics(self) -> Dict[str, Any]:
        """Get shot list statistics."""
        stats = {
            "total_scenes": len(self.scenes),
            "total_shots": self.total_shots,
            "estimated_duration_minutes": self.estimated_total_duration / 60.0,
            "essential_shots": 0,
            "recommended_shots": 0,
            "optional_shots": 0,
            "shots_by_size": {},
            "shots_by_purpose": {}
        }

        for scene in self.scenes.values():
            for shot in scene.shots:
                # Count by priority
                if shot.priority == "essential":
                    stats["essential_shots"] += 1
                elif shot.priority == "recommended":
                    stats["recommended_shots"] += 1
                else:
                    stats["optional_shots"] += 1

                # Count by size
                size = shot.shot_size
                stats["shots_by_size"][size] = stats["shots_by_size"].get(size, 0) + 1

                # Count by purpose
                purpose = shot.purpose
                stats["shots_by_purpose"][purpose] = stats["shots_by_purpose"].get(purpose, 0) + 1

        return stats


@dataclass
class StoryboardPrompt:
    """Prompt for storyboard or AI image generation.

    Contains detailed visual description for a shot.
    """
    shot: ShotSuggestion
    visual_description: str
    ai_prompt: str = ""
    style_hints: str = ""
    composition_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "shot": self.shot.to_dict(),
            "visual_description": self.visual_description,
            "ai_prompt": self.ai_prompt,
            "style_hints": self.style_hints,
            "composition_notes": self.composition_notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoryboardPrompt":
        """Deserialize from dictionary."""
        return cls(
            shot=ShotSuggestion.from_dict(data["shot"]),
            visual_description=data["visual_description"],
            ai_prompt=data.get("ai_prompt", ""),
            style_hints=data.get("style_hints", ""),
            composition_notes=data.get("composition_notes", "")
        )


# Shot size constants
SHOT_SIZES = {
    "ECU": "Extreme Close-Up",
    "CU": "Close-Up",
    "MCU": "Medium Close-Up",
    "MS": "Medium Shot",
    "MFS": "Medium Full Shot",
    "FS": "Full Shot",
    "WS": "Wide Shot",
    "EWS": "Extreme Wide Shot"
}

# Camera angle constants
CAMERA_ANGLES = {
    "eye_level": "Eye Level",
    "high": "High Angle",
    "low": "Low Angle",
    "dutch": "Dutch Angle",
    "birds_eye": "Bird's Eye",
    "worms_eye": "Worm's Eye"
}

# Shot purpose constants
SHOT_PURPOSES = {
    "coverage": "Coverage",
    "reaction": "Reaction Shot",
    "insert": "Insert/Detail",
    "establishing": "Establishing Shot",
    "transition": "Transition",
    "cutaway": "Cutaway",
    "point_of_view": "Point of View",
    "over_shoulder": "Over the Shoulder"
}

# Camera move constants
CAMERA_MOVES = {
    "static": "Static",
    "pan": "Pan",
    "tilt": "Tilt",
    "dolly": "Dolly",
    "crane": "Crane",
    "handheld": "Handheld",
    "steadicam": "Steadicam",
    "zoom": "Zoom"
}

# Priority constants
PRIORITIES = ["essential", "recommended", "optional"]


# Export all types
__all__ = [
    "ShotSuggestion",
    "CoverageEstimate",
    "SceneShotList",
    "ShotList",
    "StoryboardPrompt",
    "SHOT_SIZES",
    "CAMERA_ANGLES",
    "SHOT_PURPOSES",
    "CAMERA_MOVES",
    "PRIORITIES",
]
