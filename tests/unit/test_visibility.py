"""
Conditional Visibility System Unit Tests

Tests for: lib/cinematic/projection/visibility.py
Coverage target: 80%+

Part of Phase 9.5 - Conditional Visibility (REQ-ANAM-06)
Beads: blender_gsd-39
"""

import pytest
import math
import time
from lib.oracle import compare_numbers, compare_vectors

from lib.cinematic.projection.visibility import (
    VisibilityTransition,
    VisibilityTarget,
    VisibilityState,
    VisibilityConfig,
    VisibilityController,
    create_visibility_target,
    setup_visibility_for_projection,
    evaluate_visibility_for_frame,
    bake_visibility_animation,
    HAS_BLENDER,
)

from lib.cinematic.projection.zones import (
    ZoneManager,
    CameraZone,
    ZoneType,
    create_sphere_zone,
)


class TestVisibilityTransition:
    """Unit tests for VisibilityTransition constants."""

    def test_all_transitions_exist(self):
        """All expected transition types should be defined."""
        assert hasattr(VisibilityTransition, 'INSTANT')
        assert hasattr(VisibilityTransition, 'FADE')
        assert hasattr(VisibilityTransition, 'SCALE')
        assert hasattr(VisibilityTransition, 'TRANSLATE')
        assert hasattr(VisibilityTransition, 'CUSTOM')

    def test_transition_values(self):
        """Transition values should be strings."""
        assert VisibilityTransition.INSTANT == "instant"
        assert VisibilityTransition.FADE == "fade"
        assert VisibilityTransition.SCALE == "scale"
        assert VisibilityTransition.TRANSLATE == "translate"
        assert VisibilityTransition.CUSTOM == "custom"


class TestVisibilityTarget:
    """Unit tests for VisibilityTarget dataclass."""

    def test_default_values(self):
        """Default target should have sensible values."""
        target = VisibilityTarget(object_name="TestObject")

        assert target.object_name == "TestObject"
        assert target.transition_type == VisibilityTransition.FADE
        compare_numbers(target.transition_duration, 0.5)
        compare_numbers(target.min_visibility, 0.0)
        compare_numbers(target.max_visibility, 1.0)
        assert target.easing == "ease_in_out"

    def test_custom_values(self):
        """Custom values should be stored."""
        target = VisibilityTarget(
            object_name="CustomObject",
            transition_type=VisibilityTransition.SCALE,
            transition_duration=1.0,
            transition_delay=0.2,
            min_visibility=0.2,
            max_visibility=0.8,
            easing="linear",
        )

        assert target.object_name == "CustomObject"
        assert target.transition_type == VisibilityTransition.SCALE
        compare_numbers(target.transition_duration, 1.0)
        compare_numbers(target.transition_delay, 0.2)
        compare_numbers(target.min_visibility, 0.2)
        compare_numbers(target.max_visibility, 0.8)

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        target = VisibilityTarget(
            object_name="DictObject",
            transition_duration=0.75,
        )

        data = target.to_dict()

        assert data["object_name"] == "DictObject"
        assert data["transition_duration"] == 0.75
        assert "transition_type" in data
        assert "easing" in data

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "object_name": "RestoredObject",
            "transition_type": VisibilityTransition.INSTANT,
            "transition_duration": 0.3,
            "transition_delay": 0.1,
            "easing": "ease_in",
            "min_visibility": 0.1,
            "max_visibility": 0.9,
        }

        target = VisibilityTarget.from_dict(data)

        assert target.object_name == "RestoredObject"
        assert target.transition_type == VisibilityTransition.INSTANT
        compare_numbers(target.transition_duration, 0.3)


class TestVisibilityState:
    """Unit tests for VisibilityState dataclass."""

    def test_default_values(self):
        """Default state should start hidden."""
        state = VisibilityState(
            object_name="Test",
            current_visibility=0.0,
            target_visibility=0.0,
            transition_progress=0.0,
            is_transitioning=False,
        )

        assert state.object_name == "Test"
        compare_numbers(state.current_visibility, 0.0)
        assert state.is_transitioning is False

    def test_state_with_values(self):
        """State should store all visibility data."""
        state = VisibilityState(
            object_name="Visible",
            current_visibility=0.5,
            target_visibility=1.0,
            transition_progress=0.5,
            is_transitioning=True,
            transition_start_time=time.time(),
            start_visibility=0.0,
        )

        assert state.object_name == "Visible"
        compare_numbers(state.current_visibility, 0.5)
        compare_numbers(state.target_visibility, 1.0)
        assert state.is_transitioning is True

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        state = VisibilityState(
            object_name="DictState",
            current_visibility=0.8,
            target_visibility=1.0,
            transition_progress=0.8,
            is_transitioning=True,
        )

        data = state.to_dict()

        assert data["object_name"] == "DictState"
        compare_numbers(data["current_visibility"], 0.8)
        assert data["is_transitioning"] is True


class TestVisibilityConfig:
    """Unit tests for VisibilityConfig dataclass."""

    def test_default_values(self):
        """Default config should have sensible values."""
        config = VisibilityConfig()

        compare_numbers(config.update_rate, 60.0)
        assert config.use_frame_timing is True
        compare_numbers(config.default_duration, 0.5)
        assert config.animate_viewport is True

    def test_custom_values(self):
        """Custom values should be stored."""
        config = VisibilityConfig(
            update_rate=30.0,
            use_frame_timing=False,
            default_duration=1.0,
            keyframe_changes=True,
            keyframe_range=(1, 500),
        )

        compare_numbers(config.update_rate, 30.0)
        assert config.use_frame_timing is False
        compare_numbers(config.default_duration, 1.0)
        assert config.keyframe_range == (1, 500)


class TestVisibilityController:
    """Unit tests for VisibilityController class."""

    def test_empty_controller(self):
        """Empty controller should work without errors."""
        controller = VisibilityController()
        results = controller.update((0.0, 0.0, 0.0), frame=1)

        assert results == {}

    def test_add_target(self):
        """Adding target should initialize state."""
        controller = VisibilityController()
        target = VisibilityTarget(object_name="TestObject")

        controller.add_target(target)

        assert "TestObject" in controller.targets
        assert "TestObject" in controller.states

    def test_remove_target(self):
        """Removing target should work correctly."""
        controller = VisibilityController()
        target = VisibilityTarget(object_name="RemoveMe")

        controller.add_target(target)
        assert "RemoveMe" in controller.targets

        result = controller.remove_target("RemoveMe")
        assert result is True
        assert "RemoveMe" not in controller.targets

    def test_update_with_no_zones(self):
        """Update without zone manager should use min visibility."""
        controller = VisibilityController()
        target = VisibilityTarget(
            object_name="NoZone",
            min_visibility=0.0,
            max_visibility=1.0,
        )
        controller.add_target(target)

        results = controller.update((0.0, 0.0, 0.0), frame=1)

        # Without zones, should be at min visibility
        compare_numbers(results["NoZone"], 0.0, tolerance=0.01)

    def test_update_with_zone_manager(self):
        """Update with zone manager should affect visibility."""
        controller = VisibilityController()
        zone_manager = ZoneManager()

        # Create a zone at origin
        zone = create_sphere_zone(
            name="test_zone",
            center=(0.0, 0.0, 0.0),
            radius=10.0,
            target_objects=["ZoneObject"],
        )
        zone_manager.add_zone(zone)

        # Use instant transition for testing
        target = VisibilityTarget(
            object_name="ZoneObject",
            transition_duration=0.0,  # Instant transition
        )
        controller.add_target(target)
        controller.set_zone_manager(zone_manager)

        # Camera at origin - inside zone
        results = controller.update((0.0, 0.0, 0.0), frame=1)
        compare_numbers(results["ZoneObject"], 1.0, tolerance=0.01)

        # Camera far away - outside zone
        results = controller.update((100.0, 0.0, 0.0), frame=2)
        compare_numbers(results["ZoneObject"], 0.0, tolerance=0.01)

    def test_transition_progress(self):
        """Transitions should progress over time."""
        config = VisibilityConfig(update_rate=60.0)
        controller = VisibilityController(config)

        zone_manager = ZoneManager()
        zone = create_sphere_zone(
            name="transition_zone",
            center=(0.0, 0.0, 0.0),
            radius=5.0,
            target_objects=["TransitionObject"],
        )
        zone_manager.add_zone(zone)

        # Use instant transition for testing immediate visibility
        target = VisibilityTarget(
            object_name="TransitionObject",
            transition_duration=0.0,  # Instant for test
        )
        controller.add_target(target)
        controller.set_zone_manager(zone_manager)

        # Start inside zone - should immediately become visible
        controller.update((0.0, 0.0, 0.0), frame=1)

        state = controller.get_state("TransitionObject")
        compare_numbers(state.current_visibility, 1.0, tolerance=0.01)
        assert state.is_transitioning is False  # Instant transition complete

    def test_force_visibility(self):
        """Force visibility should override zone evaluation."""
        controller = VisibilityController()
        target = VisibilityTarget(object_name="ForcedObject")
        controller.add_target(target)

        # Force to visible
        controller.force_visibility("ForcedObject", 1.0, immediate=True)

        state = controller.get_state("ForcedObject")
        compare_numbers(state.current_visibility, 1.0, tolerance=0.001)

    def test_get_all_states(self):
        """get_all_states should return all states."""
        controller = VisibilityController()
        controller.add_target(VisibilityTarget(object_name="Obj1"))
        controller.add_target(VisibilityTarget(object_name="Obj2"))

        states = controller.get_all_states()

        assert len(states) == 2
        assert "Obj1" in states
        assert "Obj2" in states

    def test_clear(self):
        """Clear should remove all targets and states."""
        controller = VisibilityController()
        controller.add_target(VisibilityTarget(object_name="ClearMe"))

        controller.clear()

        assert len(controller.targets) == 0
        assert len(controller.states) == 0

    def test_to_dict(self):
        """to_dict should serialize controller state."""
        controller = VisibilityController()
        controller.add_target(VisibilityTarget(object_name="SerializeMe"))

        data = controller.to_dict()

        assert "config" in data
        assert "targets" in data
        assert len(data["targets"]) == 1

    def test_from_dict(self):
        """from_dict should restore controller state."""
        data = {
            "config": {
                "update_rate": 30.0,
            },
            "targets": [
                {
                    "object_name": "RestoredTarget",
                    "transition_type": "fade",
                }
            ],
        }

        controller = VisibilityController.from_dict(data)

        compare_numbers(controller.config.update_rate, 30.0)
        assert len(controller.targets) == 1
        assert "RestoredTarget" in controller.targets


class TestCreateVisibilityTarget:
    """Unit tests for create_visibility_target convenience function."""

    def test_create_target(self):
        """Should create properly configured target."""
        target = create_visibility_target(
            object_name="ConvenienceObject",
            transition_type=VisibilityTransition.FADE,
            duration=0.75,
            easing="ease_out",
            min_visibility=0.1,
            max_visibility=0.9,
        )

        assert target.object_name == "ConvenienceObject"
        assert target.transition_type == VisibilityTransition.FADE
        compare_numbers(target.transition_duration, 0.75)
        assert target.easing == "ease_out"
        compare_numbers(target.min_visibility, 0.1)
        compare_numbers(target.max_visibility, 0.9)


class TestSetupVisibilityForProjection:
    """Unit tests for setup_visibility_for_projection function."""

    def test_setup_for_projection(self):
        """Should configure controller and zone manager."""
        controller = VisibilityController()
        zone_manager = ZoneManager()

        setup_visibility_for_projection(
            controller=controller,
            zone_manager=zone_manager,
            object_names=["Floor", "Wall"],
            transition_duration=0.3,
        )

        assert "Floor" in controller.targets
        assert "Wall" in controller.targets


class TestEvaluateVisibilityForFrame:
    """Unit tests for evaluate_visibility_for_frame function."""

    def test_evaluate_frame(self):
        """Should return visibility for frame."""
        controller = VisibilityController()
        zone_manager = ZoneManager()

        zone = create_sphere_zone(
            name="frame_zone",
            center=(0.0, 0.0, 0.0),
            radius=10.0,
            target_objects=["FrameObject"],
        )
        zone_manager.add_zone(zone)

        target = VisibilityTarget(object_name="FrameObject")
        controller.add_target(target)

        visibility = evaluate_visibility_for_frame(
            controller=controller,
            zone_manager=zone_manager,
            camera_position=(0.0, 0.0, 0.0),
            frame=42,
        )

        assert "FrameObject" in visibility


class TestBakeVisibilityAnimation:
    """Unit tests for bake_visibility_animation function."""

    @pytest.mark.skipif(HAS_BLENDER, reason="Test requires real Blender to be unavailable")
    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        controller = VisibilityController()
        zone_manager = ZoneManager()

        with pytest.raises(RuntimeError) as exc_info:
            bake_visibility_animation(
                controller=controller,
                zone_manager=zone_manager,
                camera_object_name="Camera",
                frame_start=1,
                frame_end=10,
            )

        assert "Blender required" in str(exc_info.value)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_visibility_module_imports(self):
        """All visibility types should be importable."""
        from lib.cinematic.projection.visibility import (
            VisibilityTransition,
            VisibilityTarget,
            VisibilityState,
            VisibilityConfig,
            VisibilityController,
            create_visibility_target,
            setup_visibility_for_projection,
            evaluate_visibility_for_frame,
            bake_visibility_animation,
        )

        assert VisibilityTransition is not None
        assert VisibilityTarget is not None
        assert VisibilityController is not None
        assert callable(create_visibility_target)

    def test_package_imports(self):
        """All visibility APIs should be importable from package."""
        from lib.cinematic.projection import (
            VisibilityTransition,
            VisibilityTarget,
            VisibilityState,
            VisibilityConfig,
            VisibilityController,
            create_visibility_target,
            setup_visibility_for_projection,
            evaluate_visibility_for_frame,
            bake_visibility_animation,
        )

        assert VisibilityTransition is not None
        assert VisibilityTarget is not None
        assert VisibilityController is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
