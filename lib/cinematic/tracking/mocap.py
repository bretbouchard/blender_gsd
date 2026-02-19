"""
Motion Capture Import System

Provides mocap import, hand animation extraction, and retargeting
for control surface animations.

Classes:
    MocapImporter - BVH/FBX motion capture import
    MocapRetargeter - Convert hand animation to morph factors
    ButtonPressDetector - Detect button presses from proximity

Quick Start:
    from lib.cinematic.tracking.mocap import (
        MocapImporter, MocapRetargeter, ButtonPressDetector,
        import_move_ai, import_rokoko,
    )

    # Import mocap data
    importer = MocapImporter()
    mocap = importer.import_mocap("animations/hand.bvh")

    # Extract hand animation
    hand = importer.extract_hand_animation(mocap, side="right")

    # Retarget to morph factors
    retargeter = MocapRetargeter()
    morph_factors = retargeter.retarget_to_morph(hand, control_type="knob")
"""

from __future__ import annotations
import math
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List, Optional

from .types import (
    MocapData,
    BoneChannel,
    JointTransform,
    HandAnimation,
    HandFrame,
    FingerData,
)

# Hand bone name mappings for common mocap formats
HAND_BONE_NAMES: Dict[str, Dict[str, List[str]]] = {
    "finger_bones": {
        "thumb": ["thumb", "Thumb", "pollex"],
        "index": ["index", "Index", "pointer"],
        "middle": ["middle", "Middle", "digitus_medius"],
        "ring": ["ring", "Ring", "anularius"],
        "pinky": ["pinky", "Pinky", "little", "minimus"],
    },
    "joint_names": {
        "metacarpal": ["metacarpal", "Meta", "MCP", "0"],
        "proximal": ["proximal", "Prox", "PIP", "1"],
        "intermediate": ["intermediate", "Inter", "DIP", "middle", "2"],
        "distal": ["distal", "Dist", "tip", "3"],
    },
    "wrist": ["wrist", "Wrist", "carpals", "hand"],
}


@dataclass
class PressEvent:
    """
    Detected button press event.

    Attributes:
        frame: Frame number when press occurred
        button_name: Name of pressed button
        finger: Finger that pressed (index, middle, etc.)
        position: Button center position at press time
        confidence: Detection confidence 0-1
    """
    frame: int
    button_name: str = ""
    finger: str = "index"
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "frame": self.frame,
            "button_name": self.button_name,
            "finger": self.finger,
            "position": list(self.position),
            "confidence": self.confidence,
        }


class MocapImporter:
    """
    Motion capture file importer.

    Supports BVH and FBX format import with hand animation extraction
    and bone hierarchy parsing.

    Usage:
        importer = MocapImporter()
        mocap = importer.import_mocap("animations/walk.bvh")
        hand = importer.extract_hand_animation(mocap, side="right")
    """

    SUPPORTED_FORMATS = [".bvh", ".fbx"]

    def __init__(self):
        """Initialize mocap importer."""
        self._format_handlers = {
            ".bvh": self._import_bvh,
            ".fbx": self._import_fbx,
        }

    def import_mocap(self, filepath: str) -> MocapData:
        """
        Import motion capture file.

        Args:
            filepath: Path to BVH or FBX file

        Returns:
            MocapData with bone hierarchy and animation

        Raises:
            ValueError: If file format not supported
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Mocap file not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()
        if ext not in self._format_handlers:
            raise ValueError(
                f"Unsupported format: {ext}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        return self._format_handlers[ext](filepath)

    def _import_bvh(self, filepath: str) -> MocapData:
        """
        Import BVH motion capture file.

        Parses BVH hierarchy and motion data into MocapData structure.

        Args:
            filepath: Path to BVH file

        Returns:
            MocapData with parsed hierarchy and animation
        """
        with open(filepath, "r") as f:
            content = f.read()

        # Parse hierarchy
        bones, hierarchy = self._parse_bvh_hierarchy(content)

        # Parse motion data
        frame_start, frame_end, fps, motion_data = self._parse_bvh_motion(content)

        # Apply motion to bones
        self._apply_motion_to_bones(bones, motion_data, frame_start)

        # Calculate duration
        duration_seconds = (frame_end - frame_start + 1) / fps if fps > 0 else 0.0

        return MocapData(
            name=os.path.splitext(os.path.basename(filepath))[0],
            source_path=filepath,
            source_format="bvh",
            frame_start=frame_start,
            frame_end=frame_end,
            fps=fps,
            duration_seconds=duration_seconds,
            bones=bones,
            hierarchy=hierarchy,
        )

    def _parse_bvh_hierarchy(
        self, content: str
    ) -> Tuple[List[BoneChannel], Dict[str, List[str]]]:
        """Parse BVH HIERARCHY section into bone channels."""
        bones: List[BoneChannel] = []
        hierarchy: Dict[str, List[str]] = {}
        bone_stack: List[str] = []

        lines = content.split("\n")
        i = 0
        current_bone: Optional[BoneChannel] = None

        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("ROOT") or line.startswith("JOINT"):
                # New bone/joint
                parts = line.split()
                bone_name = parts[1] if len(parts) > 1 else f"bone_{len(bones)}"

                current_bone = BoneChannel(name=bone_name)

                # Set parent from stack
                if bone_stack:
                    current_bone.parent = bone_stack[-1]
                    if bone_stack[-1] not in hierarchy:
                        hierarchy[bone_stack[-1]] = []
                    hierarchy[bone_stack[-1]].append(bone_name)

                bone_stack.append(bone_name)

            elif line.startswith("OFFSET"):
                # Bone offset
                if current_bone:
                    parts = line.split()
                    if len(parts) >= 4:
                        current_bone.offset = (
                            float(parts[1]),
                            float(parts[2]),
                            float(parts[3]),
                        )

            elif line.startswith("CHANNELS"):
                # Animation channels
                if current_bone:
                    parts = line.split()
                    channel_count = int(parts[1]) if len(parts) > 1 else 0
                    current_bone.channels = parts[2 : 2 + channel_count]

            elif line == "{" and current_bone:
                # Start of bone block - already handled above
                pass

            elif line == "}":
                # End of bone block
                if current_bone and current_bone not in bones:
                    bones.append(current_bone)

                if bone_stack:
                    bone_stack.pop()

                current_bone = None

            elif line.startswith("End Site"):
                # End site - skip until closing brace
                pass

            elif line.startswith("MOTION"):
                # Done with hierarchy
                break

            i += 1

        return bones, hierarchy

    def _parse_bvh_motion(
        self, content: str
    ) -> Tuple[int, int, float, List[List[float]]]:
        """Parse BVH MOTION section into frame data."""
        lines = content.split("\n")
        i = 0
        frame_count = 0
        frame_time = 0.0
        motion_data: List[List[float]] = []

        # Find MOTION section
        while i < len(lines):
            if lines[i].strip().startswith("MOTION"):
                i += 1
                break
            i += 1

        # Parse motion header
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("Frames:"):
                frame_count = int(line.split()[1])
            elif line.startswith("Frame Time:"):
                frame_time = float(line.split()[2])
            elif line and not line.startswith("Frame"):
                # Motion data line
                try:
                    values = [float(v) for v in line.split()]
                    motion_data.append(values)
                except ValueError:
                    pass

            i += 1

        fps = 1.0 / frame_time if frame_time > 0 else 30.0
        frame_start = 1
        frame_end = frame_count if frame_count > 0 else 1

        return frame_start, frame_end, fps, motion_data

    def _apply_motion_to_bones(
        self,
        bones: List[BoneChannel],
        motion_data: List[List[float]],
        frame_start: int,
    ) -> None:
        """Apply motion data to bone transforms."""
        # Calculate channel offset for each bone
        channel_offset = 0
        for bone in bones:
            bone_channel_count = len(bone.channels)
            for frame_idx, frame_values in enumerate(motion_data):
                frame = frame_start + frame_idx

                # Extract values for this bone's channels
                pos = [0.0, 0.0, 0.0]
                rot = [0.0, 0.0, 0.0]

                for ch_idx, channel in enumerate(bone.channels):
                    data_idx = channel_offset + ch_idx
                    if data_idx < len(frame_values):
                        value = frame_values[data_idx]

                        if "Xposition" in channel:
                            pos[0] = value
                        elif "Yposition" in channel:
                            pos[1] = value
                        elif "Zposition" in channel:
                            pos[2] = value
                        elif "Xrotation" in channel:
                            rot[0] = value
                        elif "Yrotation" in channel:
                            rot[1] = value
                        elif "Zrotation" in channel:
                            rot[2] = value

                transform = JointTransform(
                    frame=frame,
                    position=(pos[0], pos[1], pos[2]),
                    rotation_euler=(rot[0], rot[1], rot[2]),
                )
                bone.transforms.append(transform)

            channel_offset += bone_channel_count

    def _import_fbx(self, filepath: str) -> MocapData:
        """
        Import FBX motion capture file.

        Note: Full FBX parsing requires external library or Blender.
        This is a placeholder that returns empty MocapData.

        Args:
            filepath: Path to FBX file

        Returns:
            MocapData (placeholder implementation)
        """
        # FBX requires binary parsing or external library
        # Return placeholder with file metadata
        return MocapData(
            name=os.path.splitext(os.path.basename(filepath))[0],
            source_path=filepath,
            source_format="fbx",
            frame_start=1,
            frame_end=1,
            fps=30.0,
            duration_seconds=0.0,
            bones=[],
            hierarchy={},
        )

    def extract_hand_animation(
        self, mocap: MocapData, side: str = "right"
    ) -> HandAnimation:
        """
        Extract hand animation from full mocap data.

        Identifies hand bones in the mocap and extracts their
        animation data into HandAnimation structure.

        Args:
            mocap: Full mocap data
            side: Hand side ("left" or "right")

        Returns:
            HandAnimation with extracted hand data
        """
        # Find hand bones
        hand_bones = self._find_hand_bones(mocap, side)

        # Extract frame range
        frames = []
        frame_start = mocap.frame_start
        frame_end = mocap.frame_end

        for frame_num in range(frame_start, frame_end + 1):
            hand_frame = self._extract_hand_frame(hand_bones, frame_num)
            if hand_frame:
                frames.append(hand_frame)

        return HandAnimation(
            name=f"{side}_hand",
            frames=frames,
            frame_start=frame_start,
            frame_end=frame_end,
        )

    def _find_hand_bones(
        self, mocap: MocapData, side: str
    ) -> Dict[str, BoneChannel]:
        """Find hand-related bones in mocap data."""
        hand_bones: Dict[str, BoneChannel] = {}
        side_prefix = side.lower()[:1].upper()  # 'L' or 'R'

        # Build a list of bone name patterns to match
        patterns = []
        for finger_names in HAND_BONE_NAMES["finger_bones"].values():
            patterns.extend(finger_names)
        patterns.extend(HAND_BONE_NAMES["wrist"])

        for bone in mocap.bones:
            bone_lower = bone.name.lower()

            # Check if bone matches hand pattern
            is_hand = any(p.lower() in bone_lower for p in patterns)
            is_correct_side = (
                side_prefix in bone.name or
                side.lower() in bone_lower or
                # If no side specified, include it
                ("L" not in bone.name and "R" not in bone.name and
                 "left" not in bone_lower and "right" not in bone_lower)
            )

            if is_hand and is_correct_side:
                hand_bones[bone.name] = bone

        return hand_bones

    def _extract_hand_frame(
        self, hand_bones: Dict[str, BoneChannel], frame_num: int
    ) -> Optional[HandFrame]:
        """Extract hand data for a single frame."""
        fingers: List[FingerData] = []
        finger_tips: Dict[str, Tuple[float, float, float]] = {}
        wrist_pos = (0.0, 0.0, 0.0)
        wrist_rot = (0.0, 0.0, 0.0)

        # Find wrist bone first
        for bone_name, bone in hand_bones.items():
            if any(w in bone_name.lower() for w in HAND_BONE_NAMES["wrist"]):
                transform = bone.get_transform_at_frame(frame_num)
                if transform:
                    wrist_pos = transform.position
                    wrist_rot = transform.rotation_euler
                break

        # Extract finger data
        for bone_name, bone in hand_bones.items():
            transform = bone.get_transform_at_frame(frame_num)
            if not transform:
                continue

            # Identify finger and joint
            finger_name = self._identify_finger(bone_name)
            joint_name = self._identify_joint(bone_name)

            if finger_name and joint_name:
                finger_data = FingerData(
                    finger_name=finger_name,
                    joint_name=joint_name,
                    rotation=transform.rotation_euler,
                    position=transform.position,
                )
                fingers.append(finger_data)

                # Check if this is a fingertip (distal joint)
                if "distal" in joint_name.lower() or "tip" in joint_name.lower():
                    finger_tips[finger_name] = transform.position

        return HandFrame(
            frame=frame_num,
            wrist_position=wrist_pos,
            wrist_rotation=wrist_rot,
            fingers=fingers,
            finger_tips=finger_tips,
        )

    def _identify_finger(self, bone_name: str) -> Optional[str]:
        """Identify finger name from bone name."""
        bone_lower = bone_name.lower()

        for finger, patterns in HAND_BONE_NAMES["finger_bones"].items():
            for pattern in patterns:
                if pattern.lower() in bone_lower:
                    return finger

        return None

    def _identify_joint(self, bone_name: str) -> Optional[str]:
        """Identify joint name from bone name."""
        bone_lower = bone_name.lower()

        for joint, patterns in HAND_BONE_NAMES["joint_names"].items():
            for pattern in patterns:
                if pattern.lower() in bone_lower:
                    return joint

        return None


class MocapRetargeter:
    """
    Retarget hand animation to control surface morph factors.

    Converts hand animation data (finger rotations, positions) into
    morph factor values suitable for the MorphEngine.

    Usage:
        retargeter = MocapRetargeter()
        morph_factors = retargeter.retarget_to_morph(hand, control_type="knob")
        animation = retargeter.create_morph_animation(morph_factors, target_name="knob_1")
    """

    # Rotation to morph factor mappings
    ROTATION_RANGES = {
        "knob": {"min": -180.0, "max": 180.0},  # Full rotation
        "fader": {"min": -45.0, "max": 45.0},  # Limited range
        "button": {"min": 0.0, "max": 30.0},  # Press depth
    }

    def __init__(self, rotation_axis: str = "Z"):
        """
        Initialize retargeter.

        Args:
            rotation_axis: Primary rotation axis for retargeting (X, Y, or Z)
        """
        self.rotation_axis = rotation_axis

    def retarget_to_morph(
        self,
        hand: HandAnimation,
        control_type: str = "knob",
        finger: str = "index",
    ) -> Dict[int, float]:
        """
        Convert hand animation to morph factors.

        Extracts rotation from specified finger and converts to
        normalized morph factor (0.0 to 1.0).

        Args:
            hand: Hand animation data
            control_type: Control type (knob, fader, button)
            finger: Finger to use for retargeting

        Returns:
            Dictionary mapping frame number to morph factor (0.0-1.0)
        """
        morph_factors: Dict[int, float] = {}
        range_config = self.ROTATION_RANGES.get(control_type, self.ROTATION_RANGES["knob"])

        for frame_data in hand.frames:
            # Get rotation from finger
            rotation = self._get_finger_rotation(frame_data, finger)

            # Normalize rotation to 0-1 range
            axis_idx = {"X": 0, "Y": 1, "Z": 2}.get(self.rotation_axis, 2)
            rot_value = rotation[axis_idx]

            # Map rotation to morph factor
            min_rot = range_config["min"]
            max_rot = range_config["max"]

            # Normalize to 0-1
            morph_factor = (rot_value - min_rot) / (max_rot - min_rot)
            morph_factor = max(0.0, min(1.0, morph_factor))  # Clamp

            morph_factors[frame_data.frame] = morph_factor

        return morph_factors

    def _get_finger_rotation(
        self, frame_data: HandFrame, finger: str
    ) -> Tuple[float, float, float]:
        """Get rotation for a specific finger from frame data."""
        for finger_data in frame_data.fingers:
            if finger_data.finger_name == finger:
                return finger_data.rotation

        # Fall back to wrist rotation
        return frame_data.wrist_rotation

    def create_morph_animation(
        self,
        morph_factors: Dict[int, float],
        target_name: str = "control",
        morph_target: str = "value",
    ) -> Dict[str, Any]:
        """
        Create morph animation data structure.

        Converts morph factors into animation data suitable for
        Blender shape keys or morph targets.

        Args:
            morph_factors: Frame to factor mapping
            target_name: Name of target object
            morph_target: Name of shape key / morph target

        Returns:
            Animation data structure
        """
        frames = sorted(morph_factors.keys())
        if not frames:
            return {
                "target": target_name,
                "morph_target": morph_target,
                "frame_start": 1,
                "frame_end": 1,
                "keyframes": [],
            }

        keyframes = [
            {"frame": frame, "value": morph_factors[frame]}
            for frame in frames
        ]

        return {
            "target": target_name,
            "morph_target": morph_target,
            "frame_start": frames[0],
            "frame_end": frames[-1],
            "keyframes": keyframes,
        }

    def retarget_finger_to_control(
        self,
        hand: HandAnimation,
        finger: str,
        control_type: str = "knob",
    ) -> Dict[int, float]:
        """
        Retarget specific finger to control.

        Convenience method for retargeting a specific finger.

        Args:
            hand: Hand animation data
            finger: Finger name (thumb, index, middle, ring, pinky)
            control_type: Control type (knob, fader, button)

        Returns:
            Frame to morph factor mapping
        """
        return self.retarget_to_morph(hand, control_type, finger)


class ButtonPressDetector:
    """
    Detect button press events from hand animation.

    Analyzes hand animation to detect when fingers approach
    and press virtual buttons based on proximity.

    Usage:
        detector = ButtonPressDetector()
        presses = detector.detect_presses(
            hand, button_center=(0.0, 0.0, 0.5), button_radius=0.02
        )
    """

    def __init__(self, press_threshold: float = 0.015, release_threshold: float = 0.025):
        """
        Initialize press detector.

        Args:
            press_threshold: Distance threshold for press detection (meters)
            release_threshold: Distance threshold for release detection (meters)
        """
        self.press_threshold = press_threshold
        self.release_threshold = release_threshold

    def detect_presses(
        self,
        hand: HandAnimation,
        button_center: Tuple[float, float, float],
        button_name: str = "button",
        button_radius: float = 0.02,
        finger: str = "index",
    ) -> List[PressEvent]:
        """
        Detect button press events from hand animation.

        Uses proximity detection to identify when finger tips
        approach button location.

        Args:
            hand: Hand animation data
            button_center: Button center position (x, y, z)
            button_name: Name of button for events
            button_radius: Button radius for proximity check
            finger: Finger to track for presses

        Returns:
            List of detected press events
        """
        events: List[PressEvent] = []
        is_pressed = False
        press_start_frame = 0

        for frame_data in hand.frames:
            # Get finger tip position
            tip_pos = frame_data.get_finger_tip(finger)
            if tip_pos is None:
                # Calculate from finger joints
                tip_pos = self._estimate_finger_tip(frame_data, finger)

            if tip_pos is None:
                continue

            # Calculate distance to button
            distance = self._calculate_distance(tip_pos, button_center)

            # Hysteresis for press/release detection
            if not is_pressed and distance < self.press_threshold + button_radius:
                # Press detected
                is_pressed = True
                press_start_frame = frame_data.frame

                # Calculate confidence based on distance
                confidence = 1.0 - (distance / (self.press_threshold + button_radius))
                confidence = max(0.5, min(1.0, confidence))

                event = PressEvent(
                    frame=frame_data.frame,
                    button_name=button_name,
                    finger=finger,
                    position=button_center,
                    confidence=confidence,
                )
                events.append(event)

            elif is_pressed and distance > self.release_threshold + button_radius:
                # Release detected
                is_pressed = False

        return events

    def detect_multi_button_presses(
        self,
        hand: HandAnimation,
        buttons: Dict[str, Tuple[float, float, float]],
        button_radius: float = 0.02,
        finger: str = "index",
    ) -> List[PressEvent]:
        """
        Detect presses across multiple buttons.

        Args:
            hand: Hand animation data
            buttons: Dictionary of button_name -> (x, y, z) positions
            button_radius: Button radius for all buttons
            finger: Finger to track

        Returns:
            List of all detected press events
        """
        all_events: List[PressEvent] = []

        for button_name, button_center in buttons.items():
            events = self.detect_presses(
                hand=hand,
                button_center=button_center,
                button_name=button_name,
                button_radius=button_radius,
                finger=finger,
            )
            all_events.extend(events)

        # Sort by frame
        all_events.sort(key=lambda e: e.frame)
        return all_events

    def _estimate_finger_tip(
        self, frame_data: HandFrame, finger: str
    ) -> Optional[Tuple[float, float, float]]:
        """Estimate finger tip position from joint data."""
        # Find the distal joint for this finger
        for finger_data in frame_data.fingers:
            if finger_data.finger_name == finger:
                if "distal" in finger_data.joint_name.lower():
                    return finger_data.position

        # Fall back to any joint of this finger
        for finger_data in frame_data.fingers:
            if finger_data.finger_name == finger:
                return finger_data.position

        return None

    def _calculate_distance(
        self,
        point1: Tuple[float, float, float],
        point2: Tuple[float, float, float],
    ) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt(
            (point1[0] - point2[0]) ** 2 +
            (point1[1] - point2[1]) ** 2 +
            (point1[2] - point2[2]) ** 2
        )


# Convenience functions for specific mocap formats

def import_move_ai(filepath: str) -> MocapData:
    """
    Import Move.ai motion capture data.

    Move.ai uses standard BVH format with additional metadata.

    Args:
        filepath: Path to Move.ai export file

    Returns:
        Imported mocap data
    """
    importer = MocapImporter()
    return importer.import_mocap(filepath)


def import_rokoko(filepath: str) -> MocapData:
    """
    Import Rokoko motion capture data.

    Rokoko exports in BVH format with custom bone naming.

    Args:
        filepath: Path to Rokoko export file

    Returns:
        Imported mocap data
    """
    importer = MocapImporter()
    mocap = importer.import_mocap(filepath)

    # Rokoko-specific bone name normalization could go here
    # For now, just return standard import
    return mocap


# Export list for module
__all__ = [
    # Classes
    "MocapImporter",
    "MocapRetargeter",
    "ButtonPressDetector",
    # Types
    "PressEvent",
    "HAND_BONE_NAMES",
    # Convenience functions
    "import_move_ai",
    "import_rokoko",
]
