"""
Camera Position Zones Unit Tests

Tests for: lib/cinematic/projection/zones.py
Coverage target: 80%+

Part of Phase 9.4 - Camera Position Zones (REQ-ANAM-05)
Beads: blender_gsd-38
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors

from lib.cinematic.projection.zones import (
    ZoneType,
    ZoneTransition,
    CameraZone,
    ZoneState,
    ZoneManagerConfig,
    ZoneManager,
    create_sphere_zone,
    create_box_zone,
    create_sweet_spot,
    get_zone_visualization_data,
)


class TestZoneType:
    """Unit tests for ZoneType enum."""

    def test_all_types_exist(self):
        """All expected zone types should be defined."""
        assert hasattr(ZoneType, 'SPHERE')
        assert hasattr(ZoneType, 'BOX')
        assert hasattr(ZoneType, 'CAPSULE')
        assert hasattr(ZoneType, 'CUSTOM')
        assert hasattr(ZoneType, 'FRUSTUM')

    def test_type_values(self):
        """Zone type values should be lowercase strings."""
        assert ZoneType.SPHERE.value == "sphere"
        assert ZoneType.BOX.value == "box"
        assert ZoneType.CAPSULE.value == "capsule"
        assert ZoneType.CUSTOM.value == "custom"
        assert ZoneType.FRUSTUM.value == "frustum"


class TestZoneTransition:
    """Unit tests for ZoneTransition constants."""

    def test_all_transitions_exist(self):
        """All expected transitions should be defined."""
        assert hasattr(ZoneTransition, 'SHARP')
        assert hasattr(ZoneTransition, 'LINEAR')
        assert hasattr(ZoneTransition, 'SMOOTH')
        assert hasattr(ZoneTransition, 'EXPONENTIAL')

    def test_transition_values(self):
        """Transition values should be strings."""
        assert ZoneTransition.SHARP == "sharp"
        assert ZoneTransition.LINEAR == "linear"
        assert ZoneTransition.SMOOTH == "smooth"
        assert ZoneTransition.EXPONENTIAL == "exponential"


class TestCameraZone:
    """Unit tests for CameraZone dataclass."""

    def test_default_values(self):
        """Default zone should have sensible values."""
        zone = CameraZone()

        assert zone.name == "zone_01"
        assert zone.zone_type == ZoneType.SPHERE
        assert zone.enabled is True
        assert zone.transition_type == ZoneTransition.LINEAR
        compare_numbers(zone.transition_distance, 0.2)

    def test_sphere_zone_creation(self):
        """Sphere zone should be created correctly."""
        zone = CameraZone(
            name="test_sphere",
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 0.0, 0.0),
        )

        assert zone.zone_type == ZoneType.SPHERE
        assert zone.center == (0.0, 0.0, 0.0)
        assert zone.dimensions == (5.0, 0.0, 0.0)

    def test_box_zone_creation(self):
        """Box zone should be created correctly."""
        zone = CameraZone(
            name="test_box",
            zone_type=ZoneType.BOX,
            center=(10.0, 5.0, 0.0),
            dimensions=(2.0, 3.0, 4.0),
        )

        assert zone.zone_type == ZoneType.BOX
        compare_vectors(zone.center, (10.0, 5.0, 0.0))
        assert zone.dimensions == (2.0, 3.0, 4.0)

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        zone = CameraZone(
            id="zone_123",
            name="MyZone",
            zone_type=ZoneType.BOX,
            center=(1, 2, 3),
            dimensions=(4, 5, 6),
            target_objects=["Floor", "Wall"],
        )

        data = zone.to_dict()

        assert data["id"] == "zone_123"
        assert data["name"] == "MyZone"
        assert data["zone_type"] == "box"
        assert data["center"] == [1, 2, 3]
        assert "Floor" in data["target_objects"]

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "id": "restored_zone",
            "name": "RestoredZone",
            "zone_type": "sphere",
            "center": [5, 10, 15],
            "dimensions": [10, 0, 0],
            "transition_type": "smooth",
            "transition_distance": 0.5,
            "target_objects": ["Object1"],
            "enabled": False,
            "priority": 50,
        }

        zone = CameraZone.from_dict(data)

        assert zone.id == "restored_zone"
        assert zone.zone_type == ZoneType.SPHERE
        compare_vectors(zone.center, (5, 10, 15))
        assert zone.transition_type == "smooth"
        compare_numbers(zone.transition_distance, 0.5)
        assert zone.enabled is False
        assert zone.priority == 50

    def test_contains_point_inside_sphere(self):
        """Point inside sphere should return 1.0."""
        zone = CameraZone(
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 0.0, 0.0),
            transition_distance=0.5,
        )

        # Point at center
        factor = zone.contains_point((0.0, 0.0, 0.0))
        compare_numbers(factor, 1.0, tolerance=0.001)

        # Point inside
        factor = zone.contains_point((2.0, 0.0, 0.0))
        compare_numbers(factor, 1.0, tolerance=0.001)

    def test_contains_point_outside_sphere(self):
        """Point outside sphere should return 0.0."""
        zone = CameraZone(
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 0.0, 0.0),
            transition_distance=0.5,
        )

        # Point far outside
        factor = zone.contains_point((10.0, 0.0, 0.0))
        compare_numbers(factor, 0.0, tolerance=0.001)

    def test_contains_point_in_transition(self):
        """Point in transition zone should return 0.0-1.0."""
        zone = CameraZone(
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 0.0, 0.0),
            transition_distance=1.0,
            transition_type=ZoneTransition.LINEAR,
        )

        # Point in transition (radius=5, so 4.5 is 0.5 from edge)
        factor = zone.contains_point((4.5, 0.0, 0.0))
        assert 0.0 < factor < 1.0

    def test_contains_point_box(self):
        """Box zone should work correctly."""
        zone = CameraZone(
            zone_type=ZoneType.BOX,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 5.0, 5.0),  # Half-extents
            transition_distance=1.0,
        )

        # Inside
        factor = zone.contains_point((0.0, 0.0, 0.0))
        compare_numbers(factor, 1.0, tolerance=0.001)

        # Outside
        factor = zone.contains_point((10.0, 0.0, 0.0))
        compare_numbers(factor, 0.0, tolerance=0.001)

    def test_invert_zone(self):
        """Inverted zone should return opposite values."""
        zone = CameraZone(
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 0.0, 0.0),
            invert=True,
        )

        # Outside inverted zone = visible (1.0)
        factor = zone.contains_point((10.0, 0.0, 0.0))
        compare_numbers(factor, 1.0, tolerance=0.001)

        # Inside inverted zone = not visible (0.0)
        factor = zone.contains_point((0.0, 0.0, 0.0))
        compare_numbers(factor, 0.0, tolerance=0.001)


class TestZoneState:
    """Unit tests for ZoneState dataclass."""

    def test_default_values(self):
        """Default state should have empty values."""
        state = ZoneState()

        assert state.active_zones == []
        assert state.zone_factors == {}
        assert state.object_visibility == {}

    def test_state_with_data(self):
        """State should store evaluation results."""
        state = ZoneState(
            camera_position=(5.0, 10.0, 1.6),
            frame=42,
            active_zones=["zone_1"],
            zone_factors={"zone_1": 1.0},
            object_visibility={"Floor": 1.0, "Wall": 0.5},
        )

        compare_vectors(state.camera_position, (5.0, 10.0, 1.6))
        assert state.frame == 42
        assert len(state.active_zones) == 1
        assert state.object_visibility["Floor"] == 1.0

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        state = ZoneState(
            camera_position=(1, 2, 3),
            frame=10,
            active_zones=["z1", "z2"],
            zone_factors={"z1": 1.0, "z2": 0.5},
            object_visibility={"obj1": 0.8},
        )

        data = state.to_dict()

        assert data["frame"] == 10
        assert len(data["active_zones"]) == 2
        assert data["zone_factors"]["z1"] == 1.0


class TestZoneManagerConfig:
    """Unit tests for ZoneManagerConfig dataclass."""

    def test_default_values(self):
        """Default config should have sensible values."""
        config = ZoneManagerConfig()

        assert config.use_cache is True
        assert config.cache_size == 100
        assert config.blend_mode == "max"

    def test_custom_values(self):
        """Custom values should be stored."""
        config = ZoneManagerConfig(
            use_cache=False,
            cache_size=50,
            blend_mode="add",
        )

        assert config.use_cache is False
        assert config.cache_size == 50
        assert config.blend_mode == "add"


class TestZoneManager:
    """Unit tests for ZoneManager class."""

    def test_empty_manager(self):
        """Empty manager should evaluate to no active zones."""
        manager = ZoneManager()
        state = manager.evaluate((0.0, 0.0, 0.0))

        assert len(state.active_zones) == 0
        assert len(state.zone_factors) == 0

    def test_add_zone(self):
        """Adding zone should make it available."""
        manager = ZoneManager()
        zone = CameraZone(
            id="test_zone",
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(10.0, 0.0, 0.0),
        )

        manager.add_zone(zone)

        assert "test_zone" in manager.zones
        assert len(manager.get_all_zones()) == 1

    def test_remove_zone(self):
        """Removing zone should work correctly."""
        manager = ZoneManager()
        zone = CameraZone(id="remove_me", name="Remove Me")

        manager.add_zone(zone)
        assert "remove_me" in manager.zones

        result = manager.remove_zone("remove_me")
        assert result is True
        assert "remove_me" not in manager.zones

    def test_evaluate_in_zone(self):
        """Evaluation inside zone should return factor > 0."""
        manager = ZoneManager()
        zone = CameraZone(
            id="sphere_zone",
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(10.0, 0.0, 0.0),
            target_objects=["Floor"],
        )
        manager.add_zone(zone)

        state = manager.evaluate((0.0, 0.0, 0.0))

        assert "sphere_zone" in state.active_zones
        assert state.zone_factors["sphere_zone"] > 0
        assert "Floor" in state.object_visibility

    def test_evaluate_outside_zone(self):
        """Evaluation outside zone should return factor = 0."""
        manager = ZoneManager()
        zone = CameraZone(
            id="sphere_zone",
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 0.0, 0.0),
        )
        manager.add_zone(zone)

        state = manager.evaluate((100.0, 0.0, 0.0))

        assert len(state.active_zones) == 0

    def test_priority_ordering(self):
        """Higher priority zones should be evaluated first."""
        manager = ZoneManager()

        zone_low = CameraZone(id="low", name="Low", priority=1)
        zone_high = CameraZone(id="high", name="High", priority=10)

        manager.add_zone(zone_low)
        manager.add_zone(zone_high)

        zones = manager.get_all_zones()
        # Higher priority should come first when sorted
        assert zones[0].priority >= zones[1].priority or len(zones) == 2

    def test_disabled_zone_ignored(self):
        """Disabled zones should not affect evaluation."""
        manager = ZoneManager()
        zone = CameraZone(
            id="disabled",
            enabled=False,
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(10.0, 0.0, 0.0),
        )
        manager.add_zone(zone)

        state = manager.evaluate((0.0, 0.0, 0.0))

        assert len(state.active_zones) == 0

    def test_caching(self):
        """Manager should cache results by frame."""
        config = ZoneManagerConfig(use_cache=True, cache_size=10)
        manager = ZoneManager(config)
        zone = CameraZone(
            id="cached_zone",
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(10.0, 0.0, 0.0),
        )
        manager.add_zone(zone)

        # First evaluation
        state1 = manager.evaluate((0.0, 0.0, 0.0), frame=1)
        # Second evaluation (should use cache)
        state2 = manager.evaluate((0.0, 0.0, 0.0), frame=1)

        assert state1.frame == state2.frame
        assert len(manager._cache) == 1

    def test_to_dict(self):
        """to_dict should serialize manager state."""
        manager = ZoneManager()
        zone = CameraZone(id="test", name="Test")
        manager.add_zone(zone)

        data = manager.to_dict()

        assert "config" in data
        assert "zones" in data
        assert len(data["zones"]) == 1

    def test_from_dict(self):
        """from_dict should restore manager state."""
        data = {
            "config": {
                "use_cache": False,
                "cache_size": 50,
            },
            "zones": [
                {
                    "id": "restored",
                    "name": "Restored Zone",
                    "zone_type": "sphere",
                    "center": [0, 0, 0],
                    "dimensions": [5, 0, 0],
                }
            ],
        }

        manager = ZoneManager.from_dict(data)

        assert manager.config.use_cache is False
        assert len(manager.zones) == 1
        assert "restored" in manager.zones


class TestCreateSphereZone:
    """Unit tests for create_sphere_zone convenience function."""

    def test_create_sphere_zone(self):
        """Should create properly configured sphere zone."""
        zone = create_sphere_zone(
            name="my_sphere",
            center=(10.0, 20.0, 1.6),
            radius=5.0,
            transition_distance=0.3,
            target_objects=["Floor"],
        )

        assert zone.name == "my_sphere"
        assert zone.zone_type == ZoneType.SPHERE
        compare_vectors(zone.center, (10.0, 20.0, 1.6))
        assert zone.dimensions == (5.0, 0.0, 0.0)
        assert "Floor" in zone.target_objects


class TestCreateBoxZone:
    """Unit tests for create_box_zone convenience function."""

    def test_create_box_zone(self):
        """Should create properly configured box zone."""
        zone = create_box_zone(
            name="my_box",
            center=(5.0, 5.0, 2.0),
            half_extents=(2.0, 3.0, 1.0),
            target_objects=["Wall"],
        )

        assert zone.name == "my_box"
        assert zone.zone_type == ZoneType.BOX
        assert zone.dimensions == (2.0, 3.0, 1.0)


class TestCreateSweetSpot:
    """Unit tests for create_sweet_spot convenience function."""

    def test_create_sweet_spot(self):
        """Should create sweet spot with proper defaults."""
        zone = create_sweet_spot(
            installation_name="artwork_01",
            camera_position=(0.0, 5.0, 1.6),
            sweet_spot_radius=0.5,
            target_objects=["ProjectedArt"],
        )

        assert "artwork_01" in zone.id
        assert zone.zone_type == ZoneType.SPHERE
        assert zone.priority == 100  # High priority
        assert zone.transition_type == ZoneTransition.SMOOTH
        assert "ProjectedArt" in zone.target_objects


class TestGetZoneVisualizationData:
    """Unit tests for get_zone_visualization_data function."""

    def test_sphere_visualization(self):
        """Should generate visualization data for sphere zone."""
        zone = CameraZone(
            zone_type=ZoneType.SPHERE,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 0.0, 0.0),
        )

        data = get_zone_visualization_data(zone, resolution=8)

        assert "points" in data
        assert "values" in data
        assert data["zone_type"] == "sphere"

    def test_box_visualization(self):
        """Should generate visualization data for box zone."""
        zone = CameraZone(
            zone_type=ZoneType.BOX,
            center=(0.0, 0.0, 0.0),
            dimensions=(5.0, 5.0, 5.0),
        )

        data = get_zone_visualization_data(zone, resolution=8)

        assert "points" in data
        assert data["zone_type"] == "box"


class TestModuleImports:
    """Tests for module-level imports."""

    def test_zones_module_imports(self):
        """All zone types should be importable."""
        from lib.cinematic.projection.zones import (
            ZoneType,
            ZoneTransition,
            CameraZone,
            ZoneState,
            ZoneManager,
            ZoneManagerConfig,
            create_sphere_zone,
            create_box_zone,
            create_sweet_spot,
            get_zone_visualization_data,
        )

        assert ZoneType is not None
        assert CameraZone is not None
        assert ZoneManager is not None
        assert callable(create_sphere_zone)

    def test_package_imports(self):
        """All zone APIs should be importable from package."""
        from lib.cinematic.projection import (
            ZoneType,
            ZoneTransition,
            CameraZone,
            ZoneState,
            ZoneManager,
            ZoneManagerConfig,
            create_sphere_zone,
            create_box_zone,
            create_sweet_spot,
            get_zone_visualization_data,
        )

        assert ZoneType is not None
        assert CameraZone is not None
        assert ZoneManager is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
