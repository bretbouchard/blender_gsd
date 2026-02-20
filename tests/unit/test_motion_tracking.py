"""
Unit tests for Motion Tracking (Phase 6.2)

Tests tracking types, solver, follow focus, and export modules.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking_types import (
    SolveMethod,
    ExportFormat,
    TrackingMarker,
    TrackingData,
    TrackingConfig,
    FollowFocusRig,
    TrackingExportResult,
)
from cinematic.tracking_solver import (
    solve_tracking_data,
    calculate_velocities,
    calculate_accelerations,
    interpolate_position,
    predict_position,
    apply_smoothing,
    apply_gaussian_smoothing,
)
from cinematic.follow_focus import (
    calculate_focus_distance,
    create_follow_focus_rig,
)
from cinematic.tracking_export import (
    export_tracking_json,
    export_tracking,
)


class TestTrackingMarker:
    """Tests for TrackingMarker dataclass."""

    def test_create_default(self):
        """Test creating marker with defaults."""
        marker = TrackingMarker(name="test_marker")
        assert marker.name == "test_marker"
        assert marker.object_ref == ""
        assert marker.bone_name == ""
        assert marker.offset == (0.0, 0.0, 0.0)
        assert marker.frame_start == 1
        assert marker.frame_end == 250
        assert marker.enabled is True

    def test_create_full(self):
        """Test creating marker with all values."""
        marker = TrackingMarker(
            name="character_hand",
            object_ref="Armature",
            bone_name="Hand_L",
            offset=(0.1, 0.0, 0.0),
            frame_start=10,
            frame_end=100,
            enabled=True,
        )
        assert marker.name == "character_hand"
        assert marker.object_ref == "Armature"
        assert marker.bone_name == "Hand_L"
        assert marker.offset == (0.1, 0.0, 0.0)
        assert marker.frame_start == 10
        assert marker.frame_end == 100

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = TrackingMarker(
            name="prop_marker",
            object_ref="Cube",
            offset=(0.5, -0.3, 1.0),
            frame_start=50,
            frame_end=200,
        )
        data = original.to_dict()
        restored = TrackingMarker.from_dict(data)

        assert restored.name == original.name
        assert restored.object_ref == original.object_ref
        assert restored.offset == original.offset
        assert restored.frame_start == original.frame_start
        assert restored.frame_end == original.frame_end

    def test_validation_valid(self):
        """Test validation with valid marker."""
        marker = TrackingMarker(name="valid", object_ref="Object")
        errors = marker.validate()
        assert len(errors) == 0

    def test_validation_missing_name(self):
        """Test validation catches missing name."""
        marker = TrackingMarker(object_ref="Object")
        errors = marker.validate()
        assert len(errors) == 1
        assert "name" in errors[0].lower()

    def test_validation_invalid_frame_range(self):
        """Test validation catches invalid frame range."""
        marker = TrackingMarker(
            name="test",
            object_ref="Object",
            frame_start=100,
            frame_end=50,  # Invalid: end before start
        )
        errors = marker.validate()
        assert len(errors) == 1
        assert "frame_start" in errors[0].lower()


class TestTrackingData:
    """Tests for TrackingData dataclass."""

    def test_create_default(self):
        """Test creating tracking data with defaults."""
        data = TrackingData(marker_name="test")
        assert data.marker_name == "test"
        assert len(data.positions) == 0
        assert len(data.velocities) == 0
        assert len(data.accelerations) == 0

    def test_with_positions(self):
        """Test creating tracking data with positions."""
        data = TrackingData(
            marker_name="moving",
            positions={
                1: (0.0, 0.0, 0.0),
                2: (1.0, 0.0, 0.0),
                3: (2.0, 0.0, 0.0),
            }
        )
        assert len(data.positions) == 3
        assert data.get_frame_range() == (1, 3)
        assert data.get_position_at_frame(2) == (1.0, 0.0, 0.0)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = TrackingData(
            marker_name="serialize_test",
            positions={1: (0.0, 0.0, 0.0), 2: (1.0, 2.0, 3.0)},
            velocities={1: (0.5, 0.0, 0.0)},
            accelerations={1: (0.1, 0.0, 0.0)},
        )
        data = original.to_dict()
        restored = TrackingData.from_dict(data)

        assert restored.marker_name == original.marker_name
        assert len(restored.positions) == 2
        assert restored.positions[1] == (0.0, 0.0, 0.0)
        assert restored.positions[2] == (1.0, 2.0, 3.0)
        assert restored.velocities[1] == (0.5, 0.0, 0.0)

    def test_get_frame_range(self):
        """Test getting frame range."""
        data = TrackingData(
            marker_name="test",
            positions={5: (0, 0, 0), 10: (1, 1, 1), 3: (2, 2, 2)}
        )
        assert data.get_frame_range() == (3, 10)

    def test_get_position_at_frame(self):
        """Test getting position at specific frame."""
        data = TrackingData(
            marker_name="test",
            positions={1: (0.0, 0.0, 0.0), 3: (1.0, 1.0, 1.0)}
        )
        assert data.get_position_at_frame(1) == (0.0, 0.0, 0.0)
        assert data.get_position_at_frame(2) is None
        assert data.get_position_at_frame(3) == (1.0, 1.0, 1.0)


class TestTrackingConfig:
    """Tests for TrackingConfig dataclass."""

    def test_create_default(self):
        """Test creating config with defaults."""
        config = TrackingConfig()
        assert len(config.markers) == 0
        assert config.solve_method == "automatic"
        assert config.smoothing == 0.5
        assert config.prediction_frames == 5
        assert config.export_format == "blender"

    def test_create_with_markers(self):
        """Test creating config with markers."""
        markers = [
            TrackingMarker(name="m1", object_ref="obj1"),
            TrackingMarker(name="m2", object_ref="obj2"),
        ]
        config = TrackingConfig(markers=markers)
        assert len(config.markers) == 2

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = TrackingConfig(
            markers=[TrackingMarker(name="test", object_ref="obj")],
            solve_method="predictive",
            smoothing=0.8,
            prediction_frames=10,
            export_format="json",
        )
        data = original.to_dict()
        restored = TrackingConfig.from_dict(data)

        assert restored.solve_method == original.solve_method
        assert restored.smoothing == original.smoothing
        assert restored.prediction_frames == original.prediction_frames
        assert restored.export_format == original.export_format
        assert len(restored.markers) == 1

    def test_validation_valid(self):
        """Test validation with valid config."""
        config = TrackingConfig(
            markers=[TrackingMarker(name="test", object_ref="obj")]
        )
        errors = config.validate()
        assert len(errors) == 0

    def test_validation_no_markers(self):
        """Test validation catches missing markers."""
        config = TrackingConfig()
        errors = config.validate()
        assert len(errors) >= 1
        assert "marker" in errors[0].lower()

    def test_validation_invalid_smoothing(self):
        """Test validation catches invalid smoothing value."""
        config = TrackingConfig(
            markers=[TrackingMarker(name="test", object_ref="obj")],
            smoothing=1.5  # Invalid: > 1.0
        )
        errors = config.validate()
        assert len(errors) == 1
        assert "smoothing" in errors[0].lower()


class TestFollowFocusRig:
    """Tests for FollowFocusRig dataclass."""

    def test_create_default(self):
        """Test creating rig with defaults."""
        rig = FollowFocusRig(name="test_rig")
        assert rig.name == "test_rig"
        assert rig.camera_name == ""
        assert rig.target_marker == ""
        assert rig.follow_position is True
        assert rig.follow_focus is True
        assert rig.position_smoothing == 0.5
        assert rig.focus_smoothing == 0.5

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = FollowFocusRig(
            name="follow_test",
            camera_name="Camera",
            target_marker="subject",
            follow_position=False,
            focus_smoothing=0.3,
        )
        data = original.to_dict()
        restored = FollowFocusRig.from_dict(data)

        assert restored.name == original.name
        assert restored.camera_name == original.camera_name
        assert restored.follow_position == original.follow_position
        assert restored.focus_smoothing == original.focus_smoothing


class TestTrackingSolver:
    """Tests for tracking solver functions."""

    def test_calculate_velocities(self):
        """Test velocity calculation."""
        positions = {
            1: (0.0, 0.0, 0.0),
            2: (1.0, 0.0, 0.0),
            3: (2.0, 0.0, 0.0),
        }
        velocities = calculate_velocities(positions)

        # Central difference should give velocity = 1.0 in X
        assert velocities[2] == (1.0, 0.0, 0.0)

    def test_calculate_velocities_forward_diff(self):
        """Test forward difference for first frame."""
        positions = {1: (0.0, 0.0, 0.0), 2: (2.0, 0.0, 0.0)}
        velocities = calculate_velocities(positions)

        # Forward difference: (2-0)/1 = 2.0
        assert velocities[1] == (2.0, 0.0, 0.0)

    def test_calculate_velocities_backward_diff(self):
        """Test backward difference for last frame."""
        positions = {1: (0.0, 0.0, 0.0), 2: (2.0, 0.0, 0.0)}
        velocities = calculate_velocities(positions)

        # Backward difference: (2-0)/1 = 2.0
        assert velocities[2] == (2.0, 0.0, 0.0)

    def test_calculate_accelerations(self):
        """Test acceleration calculation."""
        velocities = {
            1: (0.0, 0.0, 0.0),
            2: (1.0, 0.0, 0.0),
            3: (2.0, 0.0, 0.0),
        }
        accelerations = calculate_accelerations(velocities)

        # Change in velocity = 1.0 per frame
        assert accelerations[2] == (1.0, 0.0, 0.0)

    def test_interpolate_position_exact(self):
        """Test interpolation at exact frame."""
        data = TrackingData(
            marker_name="test",
            positions={1: (0.0, 0.0, 0.0), 2: (1.0, 1.0, 1.0)}
        )
        pos = interpolate_position(data, 1)
        assert pos == (0.0, 0.0, 0.0)

    def test_interpolate_position_between(self):
        """Test interpolation between frames."""
        data = TrackingData(
            marker_name="test",
            positions={1: (0.0, 0.0, 0.0), 3: (2.0, 2.0, 2.0)}
        )
        # At frame 2, should be halfway
        pos = interpolate_position(data, 2)
        assert pos == pytest.approx((1.0, 1.0, 1.0))

    def test_interpolate_position_clamp(self):
        """Test interpolation clamps to range."""
        data = TrackingData(
            marker_name="test",
            positions={5: (5.0, 5.0, 5.0), 10: (10.0, 10.0, 10.0)}
        )
        # Before range - should clamp to first
        pos = interpolate_position(data, 1)
        assert pos == (5.0, 5.0, 5.0)
        # After range - should clamp to last
        pos = interpolate_position(data, 20)
        assert pos == (10.0, 10.0, 10.0)

    def test_predict_position(self):
        """Test position prediction."""
        data = TrackingData(
            marker_name="test",
            positions={
                1: (0.0, 0.0, 0.0),
                2: (1.0, 0.0, 0.0),
                3: (2.0, 0.0, 0.0),
            },
            velocities={
                1: (1.0, 0.0, 0.0),
                2: (1.0, 0.0, 0.0),
                3: (1.0, 0.0, 0.0),
            },
            accelerations={
                1: (0.0, 0.0, 0.0),
                2: (0.0, 0.0, 0.0),
                3: (0.0, 0.0, 0.0),
            }
        )
        # Predict 5 frames ahead from frame 2 (pos=1, vel=1)
        # p_future = 1 + 1*5 + 0.5*0*25 = 6
        predicted = predict_position(data, 2, 5)
        assert predicted is not None
        assert predicted[0] == pytest.approx(6.0)

    def test_apply_smoothing(self):
        """Test exponential smoothing."""
        data = TrackingData(
            marker_name="test",
            positions={
                1: (0.0, 0.0, 0.0),
                2: (10.0, 0.0, 0.0),  # Large jump
                3: (11.0, 0.0, 0.0),
            }
        )
        smoothed = apply_smoothing(data, 0.5)

        # With 50% smoothing, frame 2 position should be smoothed
        # alpha = 1 - 0.5 = 0.5
        # frame 2 = 0.5 * 10 + 0.5 * 0 = 5.0
        assert smoothed.positions[2][0] == pytest.approx(5.0)

    def test_apply_gaussian_smoothing(self):
        """Test Gaussian smoothing."""
        data = TrackingData(
            marker_name="test",
            positions={
                1: (0.0, 0.0, 0.0),
                2: (0.0, 0.0, 0.0),
                3: (10.0, 0.0, 0.0),  # Spike
                4: (0.0, 0.0, 0.0),
                5: (0.0, 0.0, 0.0),
            }
        )
        smoothed = apply_gaussian_smoothing(data, sigma=1.0)

        # The spike at frame 3 should be smoothed
        assert smoothed.positions[3][0] < 10.0


class TestFollowFocus:
    """Tests for follow focus functions."""

    def test_calculate_focus_distance(self):
        """Test focus distance calculation."""
        camera_pos = (0.0, 0.0, 0.0)
        target_pos = (3.0, 4.0, 0.0)  # Distance = 5 (3-4-5 triangle)
        distance = calculate_focus_distance(camera_pos, target_pos)
        assert distance == pytest.approx(5.0)

    def test_calculate_focus_distance_zero(self):
        """Test focus distance at same position."""
        pos = (1.0, 2.0, 3.0)
        distance = calculate_focus_distance(pos, pos)
        assert distance == 0.0

    def test_create_follow_focus_rig(self):
        """Test creating follow focus rig."""
        marker = TrackingMarker(name="subject", object_ref="Cube")
        rig = create_follow_focus_rig("Camera", marker)
        assert rig is not None
        assert rig.camera_name == "Camera"
        assert rig.target_marker == "subject"
        assert rig.follow_focus is True

    def test_create_follow_focus_rig_custom_name(self):
        """Test creating rig with custom name."""
        marker = TrackingMarker(name="subject", object_ref="Cube")
        rig = create_follow_focus_rig("Camera", marker, "custom_rig")
        assert rig.name == "custom_rig"


class TestTrackingExport:
    """Tests for tracking export functions."""

    def test_export_tracking_json(self):
        """Test JSON export."""
        data = {
            "marker1": TrackingData(
                marker_name="marker1",
                positions={1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0)}
            )
        }

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            result = export_tracking_json(data, f.name, 1, 2)

        assert result.success is True
        assert result.format == "json"
        assert result.marker_count == 1
        assert result.frame_count == 2

        # Verify JSON content
        with open(f.name) as jf:
            loaded = json.load(jf)
        assert "markers" in loaded
        assert "marker1" in loaded["markers"]

        Path(f.name).unlink()

    def test_export_tracking_dispatch(self):
        """Test export dispatch function."""
        data = {
            "m1": TrackingData(
                marker_name="m1",
                positions={1: (0.0, 0.0, 0.0)}
            )
        }

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            result = export_tracking(data, f.name, "json", 1, 1)

        assert result.success is True
        Path(f.name).unlink()

    def test_export_tracking_invalid_format(self):
        """Test export with invalid format."""
        data = {"m1": TrackingData(marker_name="m1")}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_tracking(data, tmpdir, "invalid_format", 1, 1)

        assert result.success is False
        assert "Unknown export format" in result.error_message


class TestEnums:
    """Tests for enum types."""

    def test_solve_method_values(self):
        """Test SolveMethod enum values."""
        assert SolveMethod.AUTOMATIC.value == "automatic"
        assert SolveMethod.MANUAL.value == "manual"
        assert SolveMethod.PREDICTIVE.value == "predictive"

    def test_export_format_values(self):
        """Test ExportFormat enum values."""
        assert ExportFormat.BLENDER.value == "blender"
        assert ExportFormat.AFTER_EFFECTS.value == "ae"
        assert ExportFormat.NUKE.value == "nuke"
        assert ExportFormat.JSON.value == "json"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
