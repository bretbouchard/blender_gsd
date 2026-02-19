"""
Projection Module Unit Tests

Tests for: lib/cinematic/projection/
Coverage target: 80%+

Part of Phase 9.0 - Projection Foundation (REQ-ANAM-01)
Beads: blender_gsd-34
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors

from lib.cinematic.projection.types import (
    SurfaceType,
    ProjectionMode,
    RayHit,
    FrustumConfig,
    ProjectionResult,
    AnamorphicProjectionConfig,
    SurfaceInfo,
)

from lib.cinematic.projection.utils import (
    classify_surface_type,
    is_surface_in_frustum,
    calculate_projection_scale,
    estimate_projection_quality,
)


class TestSurfaceType:
    """Unit tests for SurfaceType enum."""

    def test_all_surface_types_exist(self):
        """All expected surface types should be defined."""
        expected = ["floor", "wall", "ceiling", "custom", "all"]
        for surface in expected:
            assert hasattr(SurfaceType, surface.upper())

    def test_surface_type_values(self):
        """Surface type values should be lowercase strings."""
        assert SurfaceType.FLOOR.value == "floor"
        assert SurfaceType.WALL.value == "wall"
        assert SurfaceType.CEILING.value == "ceiling"
        assert SurfaceType.CUSTOM.value == "custom"
        assert SurfaceType.ALL.value == "all"


class TestProjectionMode:
    """Unit tests for ProjectionMode enum."""

    def test_all_projection_modes_exist(self):
        """All expected projection modes should be defined."""
        expected = ["emission", "diffuse", "decal", "replace"]
        for mode in expected:
            assert hasattr(ProjectionMode, mode.upper())

    def test_projection_mode_values(self):
        """Projection mode values should be lowercase strings."""
        assert ProjectionMode.EMISSION.value == "emission"
        assert ProjectionMode.DIFFUSE.value == "diffuse"
        assert ProjectionMode.DECAL.value == "decal"
        assert ProjectionMode.REPLACE.value == "replace"


class TestRayHit:
    """Unit tests for RayHit dataclass."""

    def test_default_values(self):
        """Default RayHit should be a miss (hit=False)."""
        hit = RayHit()

        assert hit.hit is False
        compare_vectors(hit.position, (0.0, 0.0, 0.0))
        compare_vectors(hit.normal, (0.0, 0.0, 1.0))
        assert hit.distance == 0.0
        assert hit.object_name == ""
        assert hit.face_index == -1

    def test_hit_with_values(self):
        """RayHit should store all intersection data."""
        hit = RayHit(
            hit=True,
            position=(1.0, 2.0, 3.0),
            normal=(0.0, 0.0, 1.0),
            distance=5.5,
            object_name="Floor",
            face_index=42,
            pixel_x=100,
            pixel_y=200,
            color=(0.5, 0.5, 0.5, 1.0),
        )

        assert hit.hit is True
        compare_vectors(hit.position, (1.0, 2.0, 3.0))
        compare_numbers(hit.distance, 5.5)
        assert hit.object_name == "Floor"
        assert hit.pixel_x == 100
        assert hit.pixel_y == 200

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        hit = RayHit(
            hit=True,
            position=(1, 2, 3),
            normal=(0, 0, 1),
            uv=(0.5, 0.5),
            distance=10.0,
            object_name="Wall",
        )

        data = hit.to_dict()

        assert data["hit"] is True
        assert data["position"] == [1, 2, 3]
        assert data["normal"] == [0, 0, 1]
        assert data["uv"] == [0.5, 0.5]
        assert data["distance"] == 10.0
        assert data["object_name"] == "Wall"

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "hit": True,
            "position": [5, 10, 15],
            "normal": [1, 0, 0],
            "uv": [0.25, 0.75],
            "distance": 20.0,
            "object_name": "Ceiling",
            "face_index": 10,
            "pixel_x": 500,
            "pixel_y": 300,
            "color": [0.8, 0.2, 0.4, 1.0],
        }

        hit = RayHit.from_dict(data)

        assert hit.hit is True
        compare_vectors(hit.position, (5, 10, 15))
        compare_vectors(hit.normal, (1, 0, 0))
        compare_vectors(hit.uv, (0.25, 0.75))
        compare_numbers(hit.distance, 20.0)
        assert hit.object_name == "Ceiling"

    def test_serialization_round_trip(self):
        """Round-trip serialization should preserve values."""
        original = RayHit(
            hit=True,
            position=(7.5, -3.2, 1.8),
            normal=(0.707, 0.707, 0.0),
            distance=15.3,
            object_name="TestObject",
        )

        restored = RayHit.from_dict(original.to_dict())

        assert restored.hit == original.hit
        compare_vectors(restored.position, original.position)
        compare_vectors(restored.normal, original.normal)
        compare_numbers(restored.distance, original.distance)


class TestFrustumConfig:
    """Unit tests for FrustumConfig dataclass."""

    def test_default_values(self):
        """Default config should have 1080p with 50mm FOV."""
        config = FrustumConfig()

        assert config.resolution_x == 1920
        assert config.resolution_y == 1080
        compare_numbers(config.fov, 50.0)
        compare_numbers(config.near_clip, 0.1)
        compare_numbers(config.far_clip, 1000.0)
        assert config.subsample == 1

    def test_custom_resolution(self):
        """Custom resolution should be stored."""
        config = FrustumConfig(
            resolution_x=3840,
            resolution_y=2160,
            fov=35.0,
        )

        assert config.resolution_x == 3840
        assert config.resolution_y == 2160
        compare_numbers(config.fov, 35.0)

    def test_region_subset(self):
        """Region should allow partial frustum rendering."""
        config = FrustumConfig(
            region_min_x=0.25,
            region_min_y=0.25,
            region_max_x=0.75,
            region_max_y=0.75,
        )

        assert config.region_min_x == 0.25
        assert config.region_max_x == 0.75

    def test_surface_filter(self):
        """Surface filter should default to ALL."""
        config = FrustumConfig()

        assert config.surface_filter == SurfaceType.ALL

    def test_surface_filter_wall(self):
        """Surface filter can be set to specific type."""
        config = FrustumConfig(surface_filter=SurfaceType.WALL)

        assert config.surface_filter == SurfaceType.WALL

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        config = FrustumConfig(
            resolution_x=1920,
            resolution_y=1080,
            fov=50.0,
            subsample=2,
            surface_filter=SurfaceType.FLOOR,
        )

        data = config.to_dict()

        assert data["resolution_x"] == 1920
        assert data["resolution_y"] == 1080
        assert data["fov"] == 50.0
        assert data["subsample"] == 2
        assert data["surface_filter"] == "floor"

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "resolution_x": 2560,
            "resolution_y": 1440,
            "fov": 42.0,
            "near_clip": 0.5,
            "far_clip": 500.0,
            "subsample": 4,
            "surface_filter": "wall",
        }

        config = FrustumConfig.from_dict(data)

        assert config.resolution_x == 2560
        assert config.resolution_y == 1440
        compare_numbers(config.fov, 42.0)
        compare_numbers(config.near_clip, 0.5)
        assert config.surface_filter == SurfaceType.WALL

    def test_serialization_round_trip(self):
        """Round-trip serialization should preserve values."""
        original = FrustumConfig(
            resolution_x=3840,
            resolution_y=2160,
            fov=28.0,
            near_clip=0.2,
            far_clip=200.0,
            subsample=2,
            region_min_x=0.1,
            region_max_y=0.9,
        )

        restored = FrustumConfig.from_dict(original.to_dict())

        assert restored.resolution_x == original.resolution_x
        assert restored.resolution_y == original.resolution_y
        compare_numbers(restored.fov, original.fov)
        compare_numbers(restored.near_clip, original.near_clip)


class TestProjectionResult:
    """Unit tests for ProjectionResult dataclass."""

    def test_default_values(self):
        """Default result should have empty hits."""
        result = ProjectionResult()

        assert result.hits == []
        assert result.hits_by_object == {}
        assert result.total_rays == 0
        assert result.hit_count == 0
        assert result.miss_count == 0

    def test_hit_rate_empty(self):
        """Hit rate should be 0 when no rays cast."""
        result = ProjectionResult()

        compare_numbers(result.hit_rate, 0.0)

    def test_hit_rate_calculation(self):
        """Hit rate should be calculated correctly."""
        result = ProjectionResult(
            total_rays=100,
            hit_count=75,
            miss_count=25,
        )

        compare_numbers(result.hit_rate, 75.0)

    def test_objects_hit(self):
        """objects_hit should list all hit objects."""
        result = ProjectionResult(
            hits_by_object={
                "Floor": [RayHit(hit=True, object_name="Floor")],
                "Wall": [RayHit(hit=True, object_name="Wall")],
            }
        )

        objects = result.objects_hit

        assert "Floor" in objects
        assert "Wall" in objects
        assert len(objects) == 2

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        result = ProjectionResult(
            total_rays=1000,
            hit_count=800,
            miss_count=200,
            process_time=2.5,
            camera_name="MainCamera",
            source_image="test.png",
        )

        data = result.to_dict()

        assert data["total_rays"] == 1000
        assert data["hit_count"] == 800
        assert data["miss_count"] == 200
        assert data["camera_name"] == "MainCamera"

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "total_rays": 500,
            "hit_count": 400,
            "miss_count": 100,
            "process_time": 1.25,
            "camera_name": "TestCamera",
            "source_image": "image.png",
            "hits": [],
            "hits_by_object": {},
        }

        result = ProjectionResult.from_dict(data)

        assert result.total_rays == 500
        assert result.hit_count == 400
        assert result.camera_name == "TestCamera"


class TestAnamorphicProjectionConfig:
    """Unit tests for AnamorphicProjectionConfig dataclass."""

    def test_default_values(self):
        """Default config should have sensible values."""
        config = AnamorphicProjectionConfig()

        assert config.name == "anamorphic_01"
        assert config.projection_mode == ProjectionMode.EMISSION
        assert config.non_destructive is True
        compare_numbers(config.intensity, 1.0)
        compare_numbers(config.bake_resolution, 2048)

    def test_sweet_spot_settings(self):
        """Sweet spot should define visibility zone."""
        config = AnamorphicProjectionConfig(
            sweet_spot_radius=1.0,
            transition_distance=0.3,
        )

        compare_numbers(config.sweet_spot_radius, 1.0)
        compare_numbers(config.transition_distance, 0.3)

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        config = AnamorphicProjectionConfig(
            name="floor_art",
            source_image="artwork.png",
            camera_name="ViewerCamera",
            target_surfaces=["Floor", "Wall"],
            projection_mode=ProjectionMode.DECAL,
        )

        data = config.to_dict()

        assert data["name"] == "floor_art"
        assert data["source_image"] == "artwork.png"
        assert data["camera_name"] == "ViewerCamera"
        assert data["projection_mode"] == "decal"
        assert "Floor" in data["target_surfaces"]

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "name": "test_projection",
            "source_image": "test.png",
            "camera_name": "Cam",
            "target_surfaces": ["Floor"],
            "surface_types": ["floor", "wall"],
            "projection_mode": "diffuse",
            "sweet_spot_radius": 2.0,
            "transition_distance": 0.5,
            "intensity": 0.8,
            "bake_resolution": 4096,
            "non_destructive": False,
        }

        config = AnamorphicProjectionConfig.from_dict(data)

        assert config.name == "test_projection"
        assert config.projection_mode == ProjectionMode.DIFFUSE
        compare_numbers(config.sweet_spot_radius, 2.0)
        assert config.non_destructive is False


class TestSurfaceInfo:
    """Unit tests for SurfaceInfo dataclass."""

    def test_default_values(self):
        """Default SurfaceInfo should have empty object name."""
        info = SurfaceInfo()

        assert info.object_name == ""
        assert info.surface_type == SurfaceType.CUSTOM
        assert info.in_frustum is False
        assert info.has_uv is False

    def test_surface_detection(self):
        """SurfaceInfo should store detection results."""
        info = SurfaceInfo(
            object_name="Floor",
            surface_type=SurfaceType.FLOOR,
            center=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            area=25.0,
            face_count=100,
            in_frustum=True,
            has_uv=True,
            uv_layer="UVMap",
        )

        assert info.object_name == "Floor"
        assert info.surface_type == SurfaceType.FLOOR
        compare_numbers(info.area, 25.0)
        assert info.in_frustum is True

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        info = SurfaceInfo(
            object_name="Wall",
            surface_type=SurfaceType.WALL,
            center=(5.0, 0.0, 1.5),
            normal=(1.0, 0.0, 0.0),
            area=10.0,
        )

        data = info.to_dict()

        assert data["object_name"] == "Wall"
        assert data["surface_type"] == "wall"
        assert data["center"] == [5.0, 0.0, 1.5]

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "object_name": "Ceiling",
            "surface_type": "ceiling",
            "center": [0, 0, 3],
            "normal": [0, 0, -1],
            "area": 50.0,
            "face_count": 200,
            "in_frustum": True,
            "occluded": False,
            "has_uv": True,
            "uv_layer": "UVMap",
        }

        info = SurfaceInfo.from_dict(data)

        assert info.object_name == "Ceiling"
        assert info.surface_type == SurfaceType.CEILING
        compare_numbers(info.area, 50.0)


class TestClassifySurfaceType:
    """Unit tests for classify_surface_type utility."""

    def test_floor_detection(self):
        """Upward-facing normals should be floor."""
        # Straight up
        normal = (0.0, 0.0, 1.0)
        assert classify_surface_type(normal) == SurfaceType.FLOOR

        # Slightly tilted up
        normal = (0.3, 0.3, 0.9)
        assert classify_surface_type(normal) == SurfaceType.FLOOR

    def test_ceiling_detection(self):
        """Downward-facing normals should be ceiling."""
        # Straight down
        normal = (0.0, 0.0, -1.0)
        assert classify_surface_type(normal) == SurfaceType.CEILING

        # Slightly tilted down
        normal = (0.2, -0.2, -0.95)
        assert classify_surface_type(normal) == SurfaceType.CEILING

    def test_wall_detection(self):
        """Horizontal normals should be wall."""
        # Straight right
        normal = (1.0, 0.0, 0.0)
        assert classify_surface_type(normal) == SurfaceType.WALL

        # Straight forward
        normal = (0.0, 1.0, 0.0)
        assert classify_surface_type(normal) == SurfaceType.WALL

        # Slight vertical tilt
        normal = (0.9, 0.0, 0.2)
        assert classify_surface_type(normal) == SurfaceType.WALL

    def test_custom_detection(self):
        """Angled surfaces should be custom."""
        # 45-degree angle in X-Y plane (z component < 0.7 but > 0.3)
        normal = (0.5, 0.5, 0.5)  # z=0.5 is between 0.3 and 0.7 threshold
        assert classify_surface_type(normal) == SurfaceType.CUSTOM

        # Another angled surface - z between thresholds
        normal = (0.6, 0.4, -0.5)  # z=-0.5 is between -0.7 and -0.3
        assert classify_surface_type(normal) == SurfaceType.CUSTOM


class TestIsSurfaceInFrustum:
    """Unit tests for is_surface_in_frustum utility."""

    def test_surface_in_front_of_camera(self):
        """Surface directly in front should be in frustum."""
        camera_pos = (0.0, 0.0, 0.0)
        camera_forward = (0.0, 1.0, 0.0)  # Looking along +Y
        surface_center = (0.0, 5.0, 0.0)  # 5m in front
        fov = 50.0

        assert is_surface_in_frustum(
            surface_center, camera_pos, camera_forward, fov
        ) is True

    def test_surface_behind_camera(self):
        """Surface behind camera should not be in frustum."""
        camera_pos = (0.0, 0.0, 0.0)
        camera_forward = (0.0, 1.0, 0.0)  # Looking along +Y
        surface_center = (0.0, -5.0, 0.0)  # 5m behind
        fov = 50.0

        assert is_surface_in_frustum(
            surface_center, camera_pos, camera_forward, fov
        ) is False

    def test_surface_at_fov_edge(self):
        """Surface at FOV edge should be in frustum."""
        camera_pos = (0.0, 0.0, 0.0)
        camera_forward = (0.0, 1.0, 0.0)
        fov = 90.0  # 45 degrees each side

        # Surface at 30 degrees - well within 45
        import math
        angle_rad = math.radians(30)
        surface_center = (math.sin(angle_rad) * 10, math.cos(angle_rad) * 10, 0)

        assert is_surface_in_frustum(
            surface_center, camera_pos, camera_forward, fov
        ) is True

    def test_surface_outside_fov(self):
        """Surface outside FOV should not be in frustum."""
        camera_pos = (0.0, 0.0, 0.0)
        camera_forward = (0.0, 1.0, 0.0)
        fov = 30.0  # 15 degrees each side - narrow

        # Surface at 60 degrees - outside 15
        import math
        angle_rad = math.radians(60)
        surface_center = (math.sin(angle_rad) * 10, math.cos(angle_rad) * 10, 0)

        assert is_surface_in_frustum(
            surface_center, camera_pos, camera_forward, fov
        ) is False

    def test_surface_at_camera_position(self):
        """Surface at camera position should return False."""
        camera_pos = (0.0, 0.0, 0.0)
        camera_forward = (0.0, 1.0, 0.0)
        surface_center = (0.0, 0.0, 0.0)  # Same as camera
        fov = 50.0

        assert is_surface_in_frustum(
            surface_center, camera_pos, camera_forward, fov
        ) is False


class TestCalculateProjectionScale:
    """Unit tests for calculate_projection_scale utility."""

    def test_scale_at_one_meter(self):
        """Scale at 1m should match FOV calculation."""
        # At 1m with 50mm FOV
        scale = calculate_projection_scale(
            camera_distance=1.0,
            fov_degrees=50.0,
            image_width=1920,
        )

        # Half FOV = 25 degrees
        # tan(25) * 2 * 1m = width
        expected = 2 * math.tan(math.radians(25.0))
        compare_numbers(scale, expected, tolerance=0.01)

    def test_scale_at_ten_meters(self):
        """Scale should increase linearly with distance."""
        scale_1m = calculate_projection_scale(1.0, 50.0, 1920)
        scale_10m = calculate_projection_scale(10.0, 50.0, 1920)

        # 10x distance = 10x scale
        compare_numbers(scale_10m, scale_1m * 10, tolerance=0.01)

    def test_scale_with_different_fov(self):
        """Wider FOV should give larger scale."""
        scale_narrow = calculate_projection_scale(5.0, 30.0, 1920)
        scale_wide = calculate_projection_scale(5.0, 90.0, 1920)

        # Wide FOV should project larger area
        assert scale_wide > scale_narrow


class TestEstimateProjectionQuality:
    """Unit tests for estimate_projection_quality utility."""

    def test_no_hits(self):
        """No hits should return 'none' quality."""
        result = estimate_projection_quality(hits=[], surface_area=10.0)

        assert result["quality"] == "none"
        assert result["coverage"] == 0.0
        assert result["density"] == 0.0

    def test_excellent_quality(self):
        """High coverage and density should be excellent."""
        # Create 1000 hits, 90% successful
        hits = [RayHit(hit=True) for _ in range(900)] + [RayHit(hit=False) for _ in range(100)]

        result = estimate_projection_quality(hits, surface_area=5.0)

        assert result["quality"] == "excellent"
        assert result["coverage"] == 90.0
        assert result["hit_count"] == 900
        assert result["total_rays"] == 1000

    def test_good_quality(self):
        """Good coverage should be 'good' quality."""
        # 70% coverage
        hits = [RayHit(hit=True) for _ in range(700)] + [RayHit(hit=False) for _ in range(300)]

        result = estimate_projection_quality(hits, surface_area=10.0)

        assert result["quality"] == "good"
        assert result["coverage"] == 70.0

    def test_poor_quality(self):
        """Low coverage should be 'poor' quality."""
        hits = [RayHit(hit=True) for _ in range(25)] + [RayHit(hit=False) for _ in range(75)]

        result = estimate_projection_quality(hits, surface_area=1.0)

        assert result["quality"] == "poor"
        assert result["coverage"] == 25.0

    def test_density_calculation(self):
        """Density should be hits per square meter."""
        hits = [RayHit(hit=True) for _ in range(100)]

        result = estimate_projection_quality(hits, surface_area=2.0)

        # 100 hits / 2 sq meters = 50 per sq meter
        compare_numbers(result["density"], 50.0)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_types_module_imports(self):
        """All types should be importable from types module."""
        from lib.cinematic.projection.types import (
            SurfaceType,
            ProjectionMode,
            RayHit,
            FrustumConfig,
            ProjectionResult,
            AnamorphicProjectionConfig,
            SurfaceInfo,
        )

        assert SurfaceType is not None
        assert ProjectionMode is not None
        assert RayHit is not None
        assert FrustumConfig is not None

    def test_utils_module_imports(self):
        """All utilities should be importable from utils module."""
        from lib.cinematic.projection.utils import (
            classify_surface_type,
            is_surface_in_frustum,
            calculate_projection_scale,
            estimate_projection_quality,
        )

        assert callable(classify_surface_type)
        assert callable(is_surface_in_frustum)
        assert callable(calculate_projection_scale)
        assert callable(estimate_projection_quality)

    def test_package_imports(self):
        """All public APIs should be importable from package."""
        from lib.cinematic.projection import (
            SurfaceType,
            ProjectionMode,
            RayHit,
            FrustumConfig,
            ProjectionResult,
            AnamorphicProjectionConfig,
            SurfaceInfo,
            classify_surface_type,
            is_surface_in_frustum,
            calculate_projection_scale,
            estimate_projection_quality,
        )

        assert SurfaceType is not None
        assert RayHit is not None
        assert callable(classify_surface_type)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
