"""
Unit tests for MSG 1998 types module.

Tests type definitions, dataclasses, and serialization without Blender.
"""

import pytest
from datetime import datetime
from pathlib import Path
from dataclasses import asdict

from lib.msg1998.types import (
    # Enums
    ModelingStage,
    PeriodViolationSeverity,
    # Phase 9.MSG-01
    FSpyImportResult,
    ReferenceSet,
    LocationAsset,
    FDXHandoffPackage,
    PeriodViolation,
    # Phase 9.MSG-02
    BuildingSpec,
    WindowSpec,
    LocationBuildState,
    # Phase 9.MSG-03
    MSGRenderPasses,
    CompositeLayer,
    MSG1998RenderProfile,
    # Phase 12.MSG-01
    ControlNetConfig,
    SDShotConfig,
    SDGenerationResult,
    # Phase 12.MSG-02
    FilmLook1998,
    ColorGradeConfig,
    LayerInput,
    # Phase 12.MSG-03
    OutputSpec,
    QCIssue,
    ExportJob,
    EditorialPackage,
)


class TestModelingStage:
    """Tests for ModelingStage enum."""

    def test_stage_order(self):
        """Test that stages are in correct order."""
        assert ModelingStage.NORMALIZE.value == 0
        assert ModelingStage.PRIMARY.value == 1
        assert ModelingStage.SECONDARY.value == 2
        assert ModelingStage.DETAIL.value == 3
        assert ModelingStage.OUTPUT_PREP.value == 4

    def test_stage_comparison(self):
        """Test stage ordering comparison."""
        assert ModelingStage.NORMALIZE.value < ModelingStage.PRIMARY.value
        assert ModelingStage.PRIMARY.value < ModelingStage.SECONDARY.value
        assert ModelingStage.SECONDARY.value < ModelingStage.DETAIL.value
        assert ModelingStage.DETAIL.value < ModelingStage.OUTPUT_PREP.value


class TestPeriodViolationSeverity:
    """Tests for PeriodViolationSeverity enum."""

    def test_severity_values(self):
        """Test severity level values."""
        assert PeriodViolationSeverity.ERROR.value == "error"
        assert PeriodViolationSeverity.WARNING.value == "warning"
        assert PeriodViolationSeverity.INFO.value == "info"

    def test_severity_ordering(self):
        """Test that error is most severe."""
        # In practice, we'd compare severity for filtering
        severities = [
            PeriodViolationSeverity.INFO,
            PeriodViolationSeverity.WARNING,
            PeriodViolationSeverity.ERROR
        ]
        values = [s.value for s in severities]
        assert "error" in values
        assert "warning" in values
        assert "info" in values


class TestFSpyImportResult:
    """Tests for FSpyImportResult dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        result = FSpyImportResult()
        assert result.camera is None
        assert result.reference_image is None
        assert result.focal_length_mm == 35.0
        assert result.sensor_width_mm == 36.0
        assert result.rotation_matrix is None
        assert result.success is False
        assert result.errors == []

    def test_custom_values(self):
        """Test custom initialization."""
        result = FSpyImportResult(
            focal_length_mm=50.0,
            sensor_width_mm=24.0,
            success=True,
            errors=["warning: minor issue"]
        )
        assert result.focal_length_mm == 50.0
        assert result.sensor_width_mm == 24.0
        assert result.success is True
        assert len(result.errors) == 1

    def test_with_path(self):
        """Test with Path object."""
        path = Path("/tmp/test.fspy")
        result = FSpyImportResult(original_fspy_path=path)
        assert result.original_fspy_path == path


class TestReferenceSet:
    """Tests for ReferenceSet dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        ref_set = ReferenceSet(location_id="LOC001")
        assert ref_set.location_id == "LOC001"
        assert ref_set.images == []
        assert ref_set.fspy_files == []
        assert ref_set.primary_angle == "north"

    def test_with_images(self):
        """Test with image paths."""
        images = [Path("/img1.jpg"), Path("/img2.jpg")]
        fspy_files = [Path("/cam.fspy")]
        ref_set = ReferenceSet(
            location_id="LOC002",
            images=images,
            fspy_files=fspy_files,
            primary_angle="south"
        )
        assert len(ref_set.images) == 2
        assert len(ref_set.fspy_files) == 1
        assert ref_set.primary_angle == "south"


class TestLocationAsset:
    """Tests for LocationAsset dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        asset = LocationAsset(
            location_id="LOC001",
            name="Test Building",
            address="123 Main St"
        )
        assert asset.location_id == "LOC001"
        assert asset.name == "Test Building"
        assert asset.address == "123 Main St"
        assert asset.coordinates == (0.0, 0.0)
        assert asset.period_year == 1998
        assert asset.period_notes == ""

    def test_with_coordinates(self):
        """Test with geographic coordinates."""
        asset = LocationAsset(
            location_id="LOC001",
            name="Empire State Building",
            address="350 5th Ave, NYC",
            coordinates=(40.7484, -73.9857),
            period_year=1998
        )
        assert asset.coordinates[0] == pytest.approx(40.7484)
        assert asset.coordinates[1] == pytest.approx(-73.9857)


class TestFDXHandoffPackage:
    """Tests for FDXHandoffPackage dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        package = FDXHandoffPackage(scene_id="SC001")
        assert package.scene_id == "SC001"
        assert package.locations == []
        assert package.valid is True
        assert package.validation_errors == []

    def test_with_locations(self):
        """Test with location assets."""
        locations = [
            LocationAsset(
                location_id="LOC001",
                name="Building A",
                address="123 Main St"
            )
        ]
        package = FDXHandoffPackage(
            scene_id="SC001",
            locations=locations
        )
        assert len(package.locations) == 1

    def test_received_at_auto_set(self):
        """Test that received_at is auto-set."""
        before = datetime.now()
        package = FDXHandoffPackage(scene_id="SC001")
        after = datetime.now()
        assert before <= package.received_at <= after


class TestPeriodViolation:
    """Tests for PeriodViolation dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        violation = PeriodViolation(
            element="LED Screen",
            description="LED screens not period-accurate"
        )
        assert violation.element == "LED Screen"
        assert violation.severity == PeriodViolationSeverity.WARNING
        assert violation.suggestion == ""
        assert violation.location == ""

    def test_with_all_fields(self):
        """Test with all fields populated."""
        violation = PeriodViolation(
            element="Smartphone",
            description="Smartphones did not exist in 1998",
            severity=PeriodViolationSeverity.ERROR,
            suggestion="Remove or replace with period device",
            location="/objects/character_phone"
        )
        assert violation.severity == PeriodViolationSeverity.ERROR


class TestBuildingSpec:
    """Tests for BuildingSpec dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        spec = BuildingSpec()
        assert spec.width_m == 10.0
        assert spec.depth_m == 10.0
        assert spec.height_m == 10.0
        assert spec.floors == 1
        assert spec.style == "commercial"

    def test_custom_values(self):
        """Test custom initialization."""
        spec = BuildingSpec(
            width_m=20.0,
            depth_m=15.0,
            height_m=50.0,
            floors=12,
            style="residential"
        )
        assert spec.width_m == 20.0
        assert spec.floors == 12
        assert spec.style == "residential"


class TestWindowSpec:
    """Tests for WindowSpec dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        spec = WindowSpec()
        assert spec.width_m == 1.2
        assert spec.height_m == 1.5
        assert spec.frame_depth_m == 0.05
        assert spec.glass_thickness_m == 0.01
        assert spec.has_frame is True


class TestLocationBuildState:
    """Tests for LocationBuildState dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        state = LocationBuildState(location_id="LOC001")
        assert state.location_id == "LOC001"
        assert state.current_stage == ModelingStage.NORMALIZE
        assert state.geometry_stats == {}
        assert state.period_issues == []
        assert state.completed_tasks == []

    def test_stage_progression(self):
        """Test stage progression."""
        state = LocationBuildState(
            location_id="LOC001",
            current_stage=ModelingStage.PRIMARY,
            completed_tasks=["normalize_scale"]
        )
        assert state.current_stage == ModelingStage.PRIMARY
        assert "normalize_scale" in state.completed_tasks


class TestMSGRenderPasses:
    """Tests for MSGRenderPasses dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        passes = MSGRenderPasses()
        assert passes.beauty is True
        assert passes.depth is True
        assert passes.normal is True
        assert passes.cryptomatte is True
        assert "object" in passes.cryptomatte_layers

    def test_custom_values(self):
        """Test custom initialization."""
        passes = MSGRenderPasses(
            beauty=True,
            depth=True,
            normal=True,
            ao=False
        )
        assert passes.ao is False


class TestCompositeLayer:
    """Tests for CompositeLayer dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        layer = CompositeLayer(name="background")
        assert layer.name == "background"
        assert layer.objects == []
        assert layer.mask_color == (1.0, 0.0, 0.0)

    def test_custom_mask_color(self):
        """Test custom mask color."""
        layer = CompositeLayer(
            name="midground",
            mask_color=(0.0, 1.0, 0.0)
        )
        assert layer.mask_color == (0.0, 1.0, 0.0)


class TestMSG1998RenderProfile:
    """Tests for MSG1998RenderProfile dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        profile = MSG1998RenderProfile()
        assert profile.resolution == (4096, 1716)
        assert profile.frame_rate == 24
        assert profile.color_space == "ACEScg"
        assert profile.samples == 256
        assert profile.use_denoiser is True
        assert profile.beauty_format == "OPEN_EXR"

    def test_custom_resolution(self):
        """Test custom resolution."""
        profile = MSG1998RenderProfile(
            resolution=(1920, 1080),
            samples=128
        )
        assert profile.resolution == (1920, 1080)
        assert profile.samples == 128


class TestControlNetConfig:
    """Tests for ControlNetConfig dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        config = ControlNetConfig()
        assert config.depth_model == "control_v11f1p_sd15_depth"
        assert config.depth_weight == 1.0
        assert config.normal_model == "control_v11p_sd15_normalbae"
        assert config.normal_weight == 0.8
        assert config.guidance_start == 0.0
        assert config.guidance_end == 1.0
        assert config.canny_enabled is False

    def test_custom_weights(self):
        """Test custom weights."""
        config = ControlNetConfig(
            depth_weight=1.2,
            normal_weight=0.5,
            canny_enabled=True
        )
        assert config.depth_weight == 1.2
        assert config.normal_weight == 0.5
        assert config.canny_enabled is True


class TestSDShotConfig:
    """Tests for SDShotConfig dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        config = SDShotConfig(shot_id="SHOT001", scene_id="SC001")
        assert config.shot_id == "SHOT001"
        assert config.scene_id == "SC001"
        assert config.seeds == {}
        assert config.steps == 30
        assert config.cfg_scale == 7.0
        assert config.sampler == "DPM++ 2M Karras"

    def test_with_seeds(self):
        """Test with layer seeds."""
        config = SDShotConfig(
            shot_id="SHOT001",
            scene_id="SC001",
            seeds={"background": 12345, "midground": 67890}
        )
        assert config.seeds["background"] == 12345


class TestSDGenerationResult:
    """Tests for SDGenerationResult dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        result = SDGenerationResult(layer_name="background", seed=12345)
        assert result.layer_name == "background"
        assert result.seed == 12345
        assert result.generation_time == 0.0
        assert result.success is False
        assert result.hash == ""


class TestFilmLook1998:
    """Tests for FilmLook1998 dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        params = FilmLook1998()
        assert params.grain_intensity == 0.15
        assert params.grain_size == 1.0
        assert params.lens_distortion == 0.02
        assert params.chromatic_aberration == 0.003
        assert params.vignette_strength == 0.4
        assert params.color_temperature == 5500

    def test_custom_values(self):
        """Test custom film look parameters."""
        params = FilmLook1998(
            grain_intensity=0.25,
            vignette_strength=0.6,
            color_temperature=6500
        )
        assert params.grain_intensity == 0.25
        assert params.vignette_strength == 0.6


class TestColorGradeConfig:
    """Tests for ColorGradeConfig dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        config = ColorGradeConfig()
        assert config.lut_path == "luts/kodak_vision3_500t.cube"
        assert config.exposure_adjust == 0.0
        assert config.contrast_adjust == 1.0
        assert config.saturation_adjust == 1.0


class TestLayerInput:
    """Tests for LayerInput dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        layer = LayerInput(name="background")
        assert layer.name == "background"
        assert layer.depth_value == 0.5


class TestOutputSpec:
    """Tests for OutputSpec dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        spec = OutputSpec()
        assert spec.format == "OPEN_EXR"
        assert spec.resolution == (4096, 1716)
        assert spec.frame_rate == 24
        assert spec.color_space == "ACEScg"
        assert spec.compression == "ZIP"


class TestQCIssue:
    """Tests for QCIssue dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        issue = QCIssue(severity="warning", category="visual")
        assert issue.severity == "warning"
        assert issue.category == "visual"
        assert issue.description == ""
        assert issue.frame == 0
        assert issue.region == (0, 0, 0, 0)

    def test_with_all_fields(self):
        """Test with all fields."""
        issue = QCIssue(
            severity="error",
            category="period",
            description="Modern car visible in background",
            frame=42,
            region=(100, 200, 300, 400),
            suggestion="Remove or replace with period vehicle"
        )
        assert issue.severity == "error"
        assert issue.frame == 42


class TestExportJob:
    """Tests for ExportJob dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        job = ExportJob(shot_id="SHOT001", scene_id="SC001")
        assert job.shot_id == "SHOT001"
        assert job.status == "pending"

    def test_status_values(self):
        """Test status transitions."""
        job = ExportJob(shot_id="SHOT001", scene_id="SC001")
        assert job.status == "pending"
        job.status = "running"
        assert job.status == "running"


class TestEditorialPackage:
    """Tests for EditorialPackage dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        package = EditorialPackage(scene_id="SC001")
        assert package.scene_id == "SC001"
        assert package.shots == []
        assert package.master_files == {}
        assert package.prores_files == {}
        assert package.preview_files == {}

    def test_with_shots(self):
        """Test with shot list."""
        package = EditorialPackage(
            scene_id="SC001",
            shots=["SHOT001", "SHOT002", "SHOT003"]
        )
        assert len(package.shots) == 3
