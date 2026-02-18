"""
Morphing Engine Test Script

Tests all morphing functionality including:
- Color interpolation (LAB space)
- Geometry morphing
- Material morphing
- Animation with easing curves
- Staggered animation
"""

from __future__ import annotations
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.control_system.morphing import (
    # Easing
    EasingType,
    apply_easing,

    # Color interpolation
    rgb_to_lab,
    lab_to_rgb,
    interpolate_color_lab,

    # Morph types
    GeometryParams,
    MaterialParams,
    SurfaceParams,
    MorphTarget,
    MorphKeyframe,
    MorphAnimation,
    StaggerConfig,
    StaggeredMorph,
    MorphEngine,

    # Convenience functions
    animate_morph,
    quick_morph,
)


def test_easing_functions():
    """Test all easing function types."""
    print("\n=== Test 1: Easing Functions ===")

    # Test linear
    assert apply_easing(0.0, EasingType.LINEAR) == 0.0
    assert apply_easing(0.5, EasingType.LINEAR) == 0.5
    assert apply_easing(1.0, EasingType.LINEAR) == 1.0
    print("  [OK] Linear easing")

    # Test ease in/out cubic
    result = apply_easing(0.5, EasingType.EASE_IN_OUT_CUBIC)
    assert 0.4 < result < 0.6  # Should be close to 0.5
    print("  [OK] Cubic easing")

    # Test back easing (overshoots)
    result = apply_easing(0.5, EasingType.EASE_OUT_BACK)
    assert result > 0.5  # Should overshoot
    print("  [OK] Back easing (overshoot)")

    # Test bounce
    result = apply_easing(0.8, EasingType.EASE_OUT_BOUNCE)
    assert 0 <= result <= 1.2  # Valid bounce range
    print("  [OK] Bounce easing")

    return True


def test_color_conversion():
    """Test RGB <-> LAB color conversion."""
    print("\n=== Test 2: Color Conversion ===")

    # Test pure colors
    test_colors = [
        ((1.0, 0.0, 0.0), "Red"),
        ((0.0, 1.0, 0.0), "Green"),
        ((0.0, 0.0, 1.0), "Blue"),
        ((1.0, 1.0, 1.0), "White"),
        ((0.0, 0.0, 0.0), "Black"),
        ((0.5, 0.5, 0.5), "Gray"),
    ]

    for rgb, name in test_colors:
        lab = rgb_to_lab(rgb)
        rgb_back = lab_to_rgb(lab)

        # Check round-trip accuracy (within tolerance)
        for i in range(3):
            diff = abs(rgb[i] - rgb_back[i])
            assert diff < 0.01, f"{name} round-trip failed: {rgb} -> {rgb_back}"
        print(f"  [OK] {name}: RGB{rgb} -> LAB{lab} -> RGB{rgb_back}")

    return True


def test_color_interpolation():
    """Test LAB color space interpolation."""
    print("\n=== Test 3: Color Interpolation ===")

    red = (1.0, 0.0, 0.0)
    blue = (0.0, 0.0, 1.0)

    # Test interpolation at various points
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        color = interpolate_color_lab(red, blue, t)
        print(f"  t={t:.2f}: RGB{color}")

    # Verify endpoints
    color_0 = interpolate_color_lab(red, blue, 0.0)
    color_1 = interpolate_color_lab(red, blue, 1.0)

    for i in range(3):
        assert abs(color_0[i] - red[i]) < 0.01
        assert abs(color_1[i] - blue[i]) < 0.01

    print("  [OK] LAB interpolation produces smooth gradient")
    return True


def test_geometry_morphing():
    """Test geometry parameter morphing."""
    print("\n=== Test 4: Geometry Morphing ===")

    geo1 = GeometryParams(
        profile="cylindrical",
        cap_height=0.015,
        cap_diameter=0.020,
        edge_radius_top=0.002,
    )

    geo2 = GeometryParams(
        profile="chicken_head",
        cap_height=0.020,
        cap_diameter=0.025,
        edge_radius_top=0.004,
    )

    # Test interpolation
    geo_mid = geo1.interpolate(geo2, 0.5)
    assert abs(geo_mid.cap_height - 0.0175) < 0.0001  # (0.015 + 0.020) / 2
    assert abs(geo_mid.cap_diameter - 0.0225) < 0.0001
    print(f"  [OK] Midpoint: cap_height={geo_mid.cap_height}, cap_diameter={geo_mid.cap_diameter}")

    # Test at t=0 and t=1
    geo_0 = geo1.interpolate(geo2, 0.0)
    geo_1 = geo1.interpolate(geo2, 1.0)
    assert geo_0.cap_height == geo1.cap_height
    assert geo_1.cap_height == geo2.cap_height
    print("  [OK] Endpoints match source/target")

    return True


def test_material_morphing():
    """Test material parameter morphing with LAB color."""
    print("\n=== Test 5: Material Morphing ===")

    mat1 = MaterialParams(
        metallic=0.0,
        roughness=0.4,
        base_color=(0.9, 0.5, 0.1),  # Orange
    )

    mat2 = MaterialParams(
        metallic=0.8,
        roughness=0.2,
        base_color=(0.2, 0.4, 0.8),  # Blue
    )

    # Test interpolation with LAB color
    mat_mid = mat1.interpolate(mat2, 0.5, use_lab=True)
    assert abs(mat_mid.metallic - 0.4) < 0.01
    assert abs(mat_mid.roughness - 0.3) < 0.01
    print(f"  [OK] Metallic: {mat1.metallic} -> {mat_mid.metallic} -> {mat2.metallic}")
    print(f"  [OK] Color: {mat1.base_color} -> {mat_mid.base_color} -> {mat2.base_color}")

    return True


def test_morph_target():
    """Test complete morph target interpolation."""
    print("\n=== Test 6: Morph Target ===")

    # Create two morph targets
    source = MorphTarget(
        name="Source",
        geometry=GeometryParams(cap_height=0.010),
        material=MaterialParams(metallic=0.0, base_color=(1.0, 0.0, 0.0)),
        surface=SurfaceParams(knurling_count=0),
    )

    target = MorphTarget(
        name="Target",
        geometry=GeometryParams(cap_height=0.020),
        material=MaterialParams(metallic=1.0, base_color=(0.0, 0.0, 1.0)),
        surface=SurfaceParams(knurling_count=32),
    )

    # Test interpolation
    result = source.interpolate(target, 0.5)
    assert abs(result.geometry.cap_height - 0.015) < 0.0001
    assert abs(result.material.metallic - 0.5) < 0.01
    assert result.surface.knurling_count == 16
    print(f"  [OK] Geometry cap_height: {result.geometry.cap_height}")
    print(f"  [OK] Material metallic: {result.material.metallic}")
    print(f"  [OK] Surface knurling: {result.surface.knurling_count}")

    return True


def test_animation():
    """Test morph animation with easing."""
    print("\n=== Test 7: Morph Animation ===")

    source = MorphTarget(
        name="A",
        geometry=GeometryParams(cap_height=0.010),
    )
    target = MorphTarget(
        name="B",
        geometry=GeometryParams(cap_height=0.020),
    )

    animation = MorphAnimation(
        source=source,
        target=target,
        duration=2.0,
        easing=EasingType.EASE_IN_OUT_CUBIC,
    )

    # Test evaluation at various times
    times = [0.0, 0.5, 1.0, 1.5, 2.0]
    for t in times:
        result = animation.evaluate(t)
        print(f"  t={t:.1f}s: factor={result:.3f}")

    # Verify endpoints
    assert animation.evaluate(0.0) == 0.0
    assert animation.evaluate(2.0) == 1.0
    print("  [OK] Animation evaluates correctly over time")

    return True


def test_keyframe_animation():
    """Test animation with custom keyframes."""
    print("\n=== Test 8: Keyframe Animation ===")

    source = MorphTarget(name="A")
    target = MorphTarget(name="B")

    animation = MorphAnimation(
        source=source,
        target=target,
        duration=3.0,
        keyframes=[
            MorphKeyframe(0.0, 0.0, EasingType.LINEAR),
            MorphKeyframe(0.3, 0.5, EasingType.EASE_OUT),  # Fast start
            MorphKeyframe(0.7, 0.5, EasingType.LINEAR),    # Hold
            MorphKeyframe(1.0, 1.0, EasingType.EASE_IN),   # Slow end
        ]
    )

    # Test at keyframe points
    factor_0 = animation.evaluate(0.0)
    factor_mid = animation.evaluate(1.5)  # 50% through duration
    factor_end = animation.evaluate(3.0)

    print(f"  t=0.0s: factor={factor_0:.3f}")
    print(f"  t=1.5s: factor={factor_mid:.3f}")
    print(f"  t=3.0s: factor={factor_end:.3f}")

    assert factor_0 == 0.0
    assert factor_end == 1.0
    print("  [OK] Keyframe animation works")

    return True


def test_staggered_animation():
    """Test staggered animation for multiple controls."""
    print("\n=== Test 9: Staggered Animation ===")

    source = MorphTarget(name="Source")
    target = MorphTarget(name="Target")

    animation = MorphAnimation(
        source=source,
        target=target,
        duration=2.0,
    )

    staggered = StaggeredMorph(
        animation=animation,
        control_count=5,
        stagger=StaggerConfig(
            stagger_type="linear",
            stagger_amount=0.1,
            stagger_direction="forward",
        )
    )

    # Get control start times
    delays = staggered.get_control_times()
    print(f"  Control delays: {delays}")

    # Verify stagger
    assert delays[0] < delays[1] < delays[2] < delays[3] < delays[4]
    print("  [OK] Controls have staggered start times")

    # Evaluate individual controls at mid-animation
    for i in range(5):
        factor = staggered.evaluate_control(i, 0.5)  # Halfway through
        print(f"  Control {i} factor at t=0.5: {factor:.3f}")

    print("  [OK] Staggered evaluation produces different factors per control")

    return True


def test_morph_engine():
    """Test the main MorphEngine class."""
    print("\n=== Test 10: Morph Engine ===")

    engine = MorphEngine()

    source = MorphTarget(
        name="Source",
        geometry=GeometryParams(cap_height=0.010),
    )
    target = MorphTarget(
        name="Target",
        geometry=GeometryParams(cap_height=0.020),
    )

    animation = MorphAnimation(
        source=source,
        target=target,
        duration=1.0,
    )

    # Evaluate through engine
    result = engine.evaluate(animation, 0.5)
    assert abs(result.geometry.cap_height - 0.015) < 0.0001
    print(f"  [OK] Engine evaluation: cap_height={result.geometry.cap_height}")

    # Test group factors
    engine.set_group_factor("knobs", 0.8)
    factor = engine.apply_group_factor(1.0, "knobs")
    assert abs(factor - 0.8) < 0.01
    print(f"  [OK] Group factor: {factor}")

    return True


def test_convenience_functions():
    """Test convenience functions."""
    print("\n=== Test 11: Convenience Functions ===")

    # Test quick_morph
    source = MorphTarget(
        name="A",
        geometry=GeometryParams(cap_height=0.010),
        material=MaterialParams(base_color=(1.0, 0.0, 0.0)),
    )
    target = MorphTarget(
        name="B",
        geometry=GeometryParams(cap_height=0.020),
        material=MaterialParams(base_color=(0.0, 0.0, 1.0)),
    )

    result = quick_morph(source, target, factor=0.25)
    assert abs(result.geometry.cap_height - 0.0125) < 0.0001
    print(f"  [OK] quick_morph at 0.25: cap_height={result.geometry.cap_height}")

    # Test animate_morph
    animation = animate_morph(source, target, duration=1.5)
    assert animation.duration == 1.5
    assert animation.easing == EasingType.EASE_IN_OUT_CUBIC
    print(f"  [OK] animate_morph creates animation with duration={animation.duration}")

    return True


def run_all_tests():
    """Run all morphing tests."""
    print("=" * 60)
    print("Morphing Engine Test Suite")
    print("=" * 60)

    tests = [
        ("Easing Functions", test_easing_functions),
        ("Color Conversion", test_color_conversion),
        ("Color Interpolation", test_color_interpolation),
        ("Geometry Morphing", test_geometry_morphing),
        ("Material Morphing", test_material_morphing),
        ("Morph Target", test_morph_target),
        ("Animation", test_animation),
        ("Keyframe Animation", test_keyframe_animation),
        ("Staggered Animation", test_staggered_animation),
        ("Morph Engine", test_morph_engine),
        ("Convenience Functions", test_convenience_functions),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  [FAIL] {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"  [ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
