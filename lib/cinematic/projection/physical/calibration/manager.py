"""
Calibration workflow manager for physical projector mapping.

Manages calibration workflows for single and multiple surfaces targets.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from .types import (
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
)
from .alignment import (
    compute_alignment_transform,
    AlignmentResult,
    Vector3,
    are_collinear,
)


@dataclass
class CalibrationManager:
    """Manage calibration workflows for projection surfaces."""

    projector_profile: "ProjectorProfile"
    calibrations: Dict[str, SurfaceCalibration] = field(default_factory=dict)

    def create_calibration(
        self,
        name: str,
        calibration_type: CalibrationType,
        points: List[CalibrationPoint]
    ) -> SurfaceCalibration:
        """Create new calibration from points."""
        calibration = SurfaceCalibration(
            name=name,
            calibration_type=calibration_type,
            points=points,
        )
        self.calibrations[name] = calibration
        return calibration

    def align_surface(
        self,
        calibration_name: str,
        auto_apply: bool = True
    ) -> AlignmentResult:
        """
        Align projector to surface using calibration.

        Args:
            calibration_name: Name of calibration to use
            auto_apply: If True, store transform in calibration

        Returns:
            AlignmentResult with transform data
        """
        calibration = self.calibrations.get(calibration_name)
        if not calibration:
            raise ValueError(f"Calibration '{calibration_name}' not found")

        # Get points in format expected by alignment
        projector_pts = [p.projector_uv for p in calibration.points]
        world_pts = [p.world_position for p in calibration.points]

        # Choose algorithm based on type
        if calibration.calibration_type == CalibrationType.THREE_POINT:
            if len(calibration.points) != 3:
                raise ValueError("3-point calibration requires exactly 3 points")
            result = compute_alignment_transform(projector_pts, world_pts)

        elif calibration.calibration_type == CalibrationType.FOUR_POINT_DLT:
            if len(calibration.points) < 4:
                raise ValueError("4-point DLT calibration requires at least 4 points")
            # Use DLT alignment
            from .dlt import four_point_dlt_alignment
            result = four_point_dlt_alignment(projector_pts, world_pts)
        else:
            raise ValueError(f"Unknown calibration type: {calibration.calibration_type}")

        # Store result in calibration
        calibration.calibration_error = result.error
        calibration.is_calibrated = True
        calibration.last_modified = datetime.now()

        # Store transform matrix as list
        if auto_apply and result.transform:
            calibration.transform_matrix = result.transform.to_list()

        return result

    def validate_calibration(
        self,
        calibration_type: CalibrationType,
        points: List[CalibrationPoint]
    ) -> Tuple[bool, List[str]]:
        """Validate calibration points are not degenerate."""
        errors = []

        # Check point count
        if calibration_type == CalibrationType.THREE_POINT:
            if len(points) != 3:
                errors.append("3-point calibration requires exactly 3 points")
        elif calibration_type == CalibrationType.FOUR_POINT_DLT:
            if len(points) < 4:
                errors.append("4-point DLT requires at least 4 points")

        # Check for collinear points (3-point only)
        if calibration_type == CalibrationType.THREE_POINT and len(points) >= 3:
            pts = [
                Vector3(p.world_position[0], p.world_position[1], p.world_position[2])
                for p in points
            ]
            if are_collinear(pts[0], pts[1], pts[2]):
                errors.append("Calibration points are collinear (degenerate)")

        return len(errors) == 0, errors

    def load_calibration_from_yaml(
        self,
        yaml_path: str
    ) -> SurfaceCalibration:
        """Load calibration from YAML file."""
        import yaml

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        calibration = SurfaceCalibration.from_dict(data)
        self.calibrations[calibration.name] = calibration
        return calibration

    def save_calibration_to_yaml(
        self,
        calibration_name: str,
        yaml_path: str
    ) -> None:
        """Save calibration to YAML file."""
        import yaml

        calibration = self.calibrations.get(calibration_name)
        if not calibration:
            raise ValueError(f"Calibration '{calibration_name}' not found")

        data = calibration.to_dict()

        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
