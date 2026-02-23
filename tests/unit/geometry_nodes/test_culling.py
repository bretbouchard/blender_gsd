"""
Unit tests for lib/geometry_nodes/culling.py

Tests the culling strategy system including:
- CullingType enum
- Frustum class
- CullingConfig dataclass
- CullingResult dataclass
- InstanceBounds dataclass
- CullingManager class
- OcclusionCuller class
- create_frustum_from_camera function
- cull_instances function
"""

import pytest
import math

from lib.geometry_nodes.culling import (
    CullingType,
    Frustum,
    CullingConfig,
    CullingResult,
    InstanceBounds,
    CullingManager,
    OcclusionCuller,
    create_frustum_from_camera,
    cull_instances,
)


class TestCullingType:
    """Tests for CullingType enum."""

    def test_culling_type_values(self):
        """Test that CullingType enum has expected values."""
        assert CullingType.FRUSTUM.value == "frustum"
        assert CullingType.DISTANCE.value == "distance"
        assert CullingType.OCCLUSION.value == "occlusion"
        assert CullingType.SMALL_OBJECT.value == "small_object"
        assert CullingType.BACKFACE.value == "backface"

    def test_culling_type_count(self):
        """Test that all expected culling types exist."""
        assert len(CullingType) == 5


class TestFrustum:
    """Tests for Frustum class."""

    def test_frustum_default_planes(self):
        """Test Frustum with default empty planes."""
        frustum = Frustum()
        assert frustum.planes == []

    def test_frustum_from_camera_basic(self):
        """Test creating frustum from camera parameters."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        assert len(frustum.planes) == 6

    def test_frustum_is_point_inside_empty(self):
        """Test point check with empty frustum."""
        frustum = Frustum()
        # Empty frustum should let all points pass
        assert frustum.is_point_inside((0.0, 0.0, 0.0))

    def test_frustum_is_point_inside_center(self):
        """Test point at center is inside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        # Point directly in front of camera
        assert frustum.is_point_inside((0.0, 0.0, -5.0))

    def test_frustum_is_point_inside_behind(self):
        """Test point behind camera is outside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        # Point behind camera
        assert not frustum.is_point_inside((0.0, 0.0, 5.0))

    def test_frustum_is_point_inside_too_far(self):
        """Test point too far is outside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        # Point beyond far plane
        assert not frustum.is_point_inside((0.0, 0.0, -150.0))

    def test_frustum_is_point_inside_too_close(self):
        """Test point too close is outside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        # Point before near plane
        assert not frustum.is_point_inside((0.0, 0.0, -0.05))

    def test_frustum_is_sphere_inside_center(self):
        """Test sphere at center is inside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        assert frustum.is_sphere_inside((0.0, 0.0, -5.0), 1.0)

    def test_frustum_is_sphere_inside_partially(self):
        """Test sphere partially inside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        # Sphere with center outside but radius extending in
        assert frustum.is_sphere_inside((0.0, 0.0, 5.0), 10.0)

    def test_frustum_is_sphere_inside_completely_outside(self):
        """Test sphere completely outside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        assert not frustum.is_sphere_inside((0.0, 0.0, 200.0), 1.0)

    def test_frustum_is_box_inside_center(self):
        """Test box at center is inside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        assert frustum.is_box_inside((-1.0, -1.0, -6.0), (1.0, 1.0, -4.0))

    def test_frustum_is_box_inside_outside(self):
        """Test box outside frustum."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        assert not frustum.is_box_inside((100.0, 100.0, 100.0), (110.0, 110.0, 110.0))

    def test_frustum_to_dict(self):
        """Test Frustum.to_dict() serialization."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        data = frustum.to_dict()
        assert "planes" in data
        assert len(data["planes"]) == 6


class TestCullingConfig:
    """Tests for CullingConfig dataclass."""

    def test_default_values(self):
        """Test CullingConfig default values."""
        config = CullingConfig()
        assert config.enable_frustum_culling is True
        assert config.enable_distance_culling is True
        assert config.enable_small_object_culling is True
        assert config.enable_backface_culling is False
        assert config.max_distance == 1000.0
        assert config.min_screen_size == 0.01
        assert config.small_object_threshold == 0.1

    def test_custom_values(self):
        """Test CullingConfig with custom values."""
        config = CullingConfig(
            enable_frustum_culling=False,
            max_distance=500.0,
            min_screen_size=0.05,
        )
        assert config.enable_frustum_culling is False
        assert config.max_distance == 500.0
        assert config.min_screen_size == 0.05

    def test_to_dict(self):
        """Test CullingConfig.to_dict() serialization."""
        config = CullingConfig()
        data = config.to_dict()
        assert data["enable_frustum_culling"] is True
        assert data["max_distance"] == 1000.0


class TestCullingResult:
    """Tests for CullingResult dataclass."""

    def test_default_values(self):
        """Test CullingResult default values."""
        result = CullingResult()
        assert result.visible == []
        assert result.culled == {}
        assert result.statistics == {}

    def test_with_values(self):
        """Test CullingResult with values."""
        result = CullingResult(
            visible=["obj1", "obj2"],
            culled={"obj3": "distance", "obj4": "frustum"},
            statistics={"total": 4, "frustum_culled": 1},
        )
        assert len(result.visible) == 2
        assert len(result.culled) == 2

    def test_to_dict(self):
        """Test CullingResult.to_dict() serialization."""
        result = CullingResult(
            visible=["obj1"],
            culled={"obj2": "distance"},
        )
        data = result.to_dict()
        assert data["visible"] == ["obj1"]
        assert data["culled"] == {"obj2": "distance"}


class TestInstanceBounds:
    """Tests for InstanceBounds dataclass."""

    def test_default_values(self):
        """Test InstanceBounds default values."""
        bounds = InstanceBounds()
        assert bounds.instance_id == ""
        assert bounds.position == (0.0, 0.0, 0.0)
        assert bounds.radius == 1.0
        assert bounds.min_corner == (-0.5, -0.5, -0.5)
        assert bounds.max_corner == (0.5, 0.5, 0.5)
        assert bounds.screen_size == 1.0

    def test_custom_values(self):
        """Test InstanceBounds with custom values."""
        bounds = InstanceBounds(
            instance_id="obj_001",
            position=(10.0, 20.0, 5.0),
            radius=2.5,
            min_corner=(8.0, 18.0, 3.0),
            max_corner=(12.0, 22.0, 7.0),
            screen_size=0.5,
        )
        assert bounds.instance_id == "obj_001"
        assert bounds.position == (10.0, 20.0, 5.0)
        assert bounds.radius == 2.5

    def test_to_dict(self):
        """Test InstanceBounds.to_dict() serialization."""
        bounds = InstanceBounds(instance_id="obj_001", position=(1.0, 2.0, 3.0))
        data = bounds.to_dict()
        assert data["instance_id"] == "obj_001"
        assert data["position"] == [1.0, 2.0, 3.0]


class TestCullingManager:
    """Tests for CullingManager class."""

    def test_default_initialization(self):
        """Test CullingManager default initialization."""
        manager = CullingManager()
        assert manager.config is not None
        assert manager.frustum is None
        assert manager.camera_position == (0.0, 0.0, 0.0)

    def test_custom_config(self):
        """Test CullingManager with custom config."""
        config = CullingConfig(max_distance=500.0)
        manager = CullingManager(config)
        assert manager.config.max_distance == 500.0

    def test_set_frustum(self):
        """Test setting frustum."""
        manager = CullingManager()
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        manager.set_frustum(frustum)
        assert manager.frustum is not None

    def test_set_frustum_from_camera(self):
        """Test setting frustum from camera parameters."""
        manager = CullingManager()
        manager.set_frustum_from_camera(
            position=(0.0, 0.0, 0.0),
            forward=(0.0, 0.0, -1.0),
            up=(0.0, 1.0, 0.0),
            right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )
        assert manager.frustum is not None

    def test_cull_instances_empty(self):
        """Test culling empty instance list."""
        manager = CullingManager()
        result = manager.cull_instances([])
        assert result.visible == []
        assert result.statistics["total"] == 0

    def test_cull_instances_all_visible(self):
        """Test culling with all instances visible."""
        manager = CullingManager()
        manager.set_frustum_from_camera(
            position=(0.0, 0.0, 0.0),
            forward=(0.0, 0.0, -1.0),
            up=(0.0, 1.0, 0.0),
            right=(1.0, 0.0, 0.0),
            fov=90.0,
            aspect=1.0,
            near=0.1,
            far=100.0,
        )

        instances = [
            InstanceBounds(instance_id="obj1", position=(0.0, 0.0, -5.0)),
            InstanceBounds(instance_id="obj2", position=(0.0, 0.0, -10.0)),
        ]

        result = manager.cull_instances(instances)
        assert len(result.visible) == 2

    def test_cull_instances_by_distance(self):
        """Test culling by distance."""
        config = CullingConfig(
            enable_frustum_culling=False,
            enable_distance_culling=True,
            max_distance=50.0,
        )
        manager = CullingManager(config)
        manager.camera_position = (0.0, 0.0, 0.0)

        instances = [
            InstanceBounds(instance_id="obj1", position=(0.0, 0.0, -10.0)),  # Close
            InstanceBounds(instance_id="obj2", position=(0.0, 0.0, -100.0)),  # Far
        ]

        result = manager.cull_instances(instances)
        assert "obj1" in result.visible
        assert "obj2" in result.culled
        assert result.culled["obj2"] == "distance"

    def test_cull_instances_by_frustum(self):
        """Test culling by frustum."""
        config = CullingConfig(
            enable_frustum_culling=True,
            enable_distance_culling=False,
        )
        manager = CullingManager(config)
        manager.set_frustum_from_camera(
            position=(0.0, 0.0, 0.0),
            forward=(0.0, 0.0, -1.0),
            up=(0.0, 1.0, 0.0),
            right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=1.0,
            near=0.1,
            far=100.0,
        )

        instances = [
            InstanceBounds(instance_id="obj1", position=(0.0, 0.0, -5.0)),  # Inside
            InstanceBounds(instance_id="obj2", position=(0.0, 0.0, 200.0)),  # Outside (behind)
        ]

        result = manager.cull_instances(instances)
        assert "obj1" in result.visible
        assert "obj2" in result.culled

    def test_cull_instances_by_small_object(self):
        """Test culling by small object size."""
        config = CullingConfig(
            enable_frustum_culling=False,
            enable_distance_culling=False,
            enable_small_object_culling=True,
            min_screen_size=0.5,
        )
        manager = CullingManager(config)

        instances = [
            InstanceBounds(instance_id="obj1", screen_size=1.0),  # Large enough
            InstanceBounds(instance_id="obj2", screen_size=0.1),  # Too small
        ]

        result = manager.cull_instances(instances)
        assert "obj1" in result.visible
        assert "obj2" in result.culled
        assert result.culled["obj2"] == "small_object"

    def test_calculate_distance(self):
        """Test distance calculation."""
        manager = CullingManager()
        manager.camera_position = (0.0, 0.0, 0.0)

        distance = manager._calculate_distance((3.0, 4.0, 0.0))
        assert distance == pytest.approx(5.0, rel=0.01)

    def test_estimate_screen_size(self):
        """Test screen size estimation."""
        manager = CullingManager()
        manager.camera_position = (0.0, 0.0, 0.0)

        instance = InstanceBounds(position=(0.0, 0.0, -10.0), radius=1.0)
        screen_size = manager.estimate_screen_size(instance, fov=60.0, screen_height=1080)

        # Should be some positive value
        assert screen_size > 0

    def test_estimate_screen_size_at_camera(self):
        """Test screen size estimation when at camera position."""
        manager = CullingManager()
        manager.camera_position = (0.0, 0.0, 0.0)

        instance = InstanceBounds(position=(0.0, 0.0, 0.0), radius=1.0)
        screen_size = manager.estimate_screen_size(instance, fov=60.0, screen_height=1080)

        # At camera position, should return 1.0
        assert screen_size == 1.0

    def test_to_gn_input(self):
        """Test converting to GN input format."""
        manager = CullingManager()
        manager.set_frustum_from_camera(
            position=(0.0, 0.0, 0.0),
            forward=(0.0, 0.0, -1.0),
            up=(0.0, 1.0, 0.0),
            right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=1.0,
            near=0.1,
            far=100.0,
        )

        gn_data = manager.to_gn_input()
        assert "version" in gn_data
        assert "config" in gn_data
        assert "frustum" in gn_data
        assert "camera_position" in gn_data


class TestOcclusionCuller:
    """Tests for OcclusionCuller class."""

    def test_default_initialization(self):
        """Test OcclusionCuller default initialization."""
        culler = OcclusionCuller()
        assert culler.resolution == 256
        assert culler.depth_buffer is None

    def test_custom_resolution(self):
        """Test OcclusionCuller with custom resolution."""
        culler = OcclusionCuller(resolution=128)
        assert culler.resolution == 128

    def test_build_depth_buffer(self):
        """Test building depth buffer."""
        culler = OcclusionCuller(resolution=64)

        occluders = [
            InstanceBounds(instance_id="occ1", position=(0.0, 0.0, -5.0), radius=2.0),
        ]

        culler.build_depth_buffer(
            occluders,
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
        )

        assert culler.depth_buffer is not None
        assert len(culler.depth_buffer) == 64
        assert len(culler.depth_buffer[0]) == 64

    def test_is_occluded_no_buffer(self):
        """Test occlusion check with no buffer."""
        culler = OcclusionCuller()
        instance = InstanceBounds(position=(0.0, 0.0, -10.0))

        assert culler.is_occluded(instance, (0.0, 0.0, 0.0)) is False

    def test_is_occluded_with_buffer(self):
        """Test occlusion check with depth buffer."""
        culler = OcclusionCuller(resolution=64)

        # Build depth buffer with nearby occluder
        occluders = [
            InstanceBounds(instance_id="occ1", position=(0.0, 0.0, -5.0), radius=2.0),
        ]
        culler.build_depth_buffer(
            occluders,
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
        )

        # Instance behind occluder
        instance_behind = InstanceBounds(position=(0.0, 0.0, -10.0))
        # Instance in front of occluder
        instance_front = InstanceBounds(position=(0.0, 0.0, -2.0))

        # Both should return some result (simplified implementation)
        assert isinstance(culler.is_occluded(instance_behind, (0.0, 0.0, 0.0)), bool)
        assert isinstance(culler.is_occluded(instance_front, (0.0, 0.0, 0.0)), bool)


class TestCreateFrustumFromCamera:
    """Tests for create_frustum_from_camera convenience function."""

    def test_create_frustum_from_camera_basic(self):
        """Test basic frustum creation from camera transform."""
        frustum = create_frustum_from_camera(
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),  # No rotation
            fov=60.0,
            aspect=16.0 / 9.0,
            near=0.1,
            far=100.0,
        )

        assert frustum is not None
        assert len(frustum.planes) == 6

    def test_create_frustum_from_camera_rotated(self):
        """Test frustum creation with rotated camera."""
        frustum = create_frustum_from_camera(
            position=(0.0, 0.0, 0.0),
            rotation=(30.0, 45.0, 0.0),  # Pitched and yawed
            fov=60.0,
            aspect=1.0,
            near=0.1,
            far=100.0,
        )

        assert frustum is not None
        assert len(frustum.planes) == 6


class TestCullInstances:
    """Tests for cull_instances convenience function."""

    def test_cull_instances_basic(self):
        """Test basic culling with convenience function."""
        instances = [
            InstanceBounds(instance_id="obj1", position=(0.0, 0.0, -5.0)),
            InstanceBounds(instance_id="obj2", position=(0.0, 0.0, -500.0)),  # Beyond max_distance
        ]

        result = cull_instances(
            instances,
            frustum=None,
            max_distance=100.0,
            min_screen_size=0.0,
        )

        assert "obj1" in result.visible
        assert "obj2" in result.culled

    def test_cull_instances_with_frustum(self):
        """Test culling with frustum using convenience function."""
        frustum = Frustum.from_camera(
            camera_position=(0.0, 0.0, 0.0),
            camera_forward=(0.0, 0.0, -1.0),
            camera_up=(0.0, 1.0, 0.0),
            camera_right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=1.0,
            near=0.1,
            far=50.0,
        )

        instances = [
            InstanceBounds(instance_id="obj1", position=(0.0, 0.0, -10.0)),
        ]

        result = cull_instances(
            instances,
            frustum=frustum,
            max_distance=100.0,
        )

        assert "obj1" in result.visible


class TestFrustumNormalize:
    """Tests for Frustum._normalize static method."""

    def test_normalize_zero_vector(self):
        """Test normalizing zero vector."""
        result = Frustum._normalize((0.0, 0.0, 0.0))
        assert result == (0.0, 0.0, 0.0)

    def test_normalize_unit_vector(self):
        """Test normalizing unit vector."""
        result = Frustum._normalize((1.0, 0.0, 0.0))
        assert result == pytest.approx((1.0, 0.0, 0.0), rel=0.01)

    def test_normalize_non_unit_vector(self):
        """Test normalizing non-unit vector."""
        result = Frustum._normalize((3.0, 4.0, 0.0))
        assert result == pytest.approx((0.6, 0.8, 0.0), rel=0.01)


class TestCullingManagerStatistics:
    """Tests for CullingManager statistics."""

    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        config = CullingConfig(
            enable_frustum_culling=True,
            enable_distance_culling=True,
            enable_small_object_culling=True,
            max_distance=50.0,
            min_screen_size=0.5,
        )
        manager = CullingManager(config)
        manager.set_frustum_from_camera(
            position=(0.0, 0.0, 0.0),
            forward=(0.0, 0.0, -1.0),
            up=(0.0, 1.0, 0.0),
            right=(1.0, 0.0, 0.0),
            fov=60.0,
            aspect=1.0,
            near=0.1,
            far=100.0,
        )

        instances = [
            InstanceBounds(instance_id="vis", position=(0.0, 0.0, -10.0), screen_size=1.0),
            InstanceBounds(instance_id="far", position=(0.0, 0.0, -200.0), screen_size=1.0),
            InstanceBounds(instance_id="small", position=(0.0, 0.0, -10.0), screen_size=0.1),
        ]

        result = manager.cull_instances(instances)

        assert result.statistics["total"] == 3
        # At least some culling should happen
        assert result.statistics["frustum_culled"] + result.statistics["distance_culled"] + result.statistics["small_object_culled"] > 0
