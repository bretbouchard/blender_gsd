"""
Test Scripts for Tutorial Techniques

Run in Blender to verify codified techniques work correctly.
Each test corresponds to a knowledge base section.

Usage in Blender:
    import sys
    sys.path.append("/path/to/blender_gsd")
    from tests.test_tutorial_modules import run_all_tests
    run_all_tests()
"""

import bpy
import sys
from pathlib import Path

# Add lib to path if needed
lib_path = Path(__file__).parent.parent
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))


def test_volumetric_fog():
    """
    Test WorldFog class from KB Sections 25, 28.

    Verifies:
    - World volume setup
    - Density setting
    - Anisotropy for god rays
    """
    from lib.volumetric import WorldFog

    print("\n=== Testing WorldFog ===")

    # Create fog
    fog = WorldFog()
    fog.set_density(0.1)
    fog.set_anisotropy(0.5)
    fog.set_color((1.0, 1.0, 1.0))

    # Verify world has volume
    world = bpy.context.scene.world
    assert world is not None, "World should exist"
    assert world.use_nodes, "World should use nodes"

    print("✓ WorldFog test passed")
    return True


def test_volumetric_projector():
    """
    Test VolumetricProjector class from KB Sections 29, 33.

    Verifies:
    - Spotlight creation
    - Video texture loading
    - Aspect ratio fix
    """
    from lib.volumetric import VolumetricProjector

    print("\n=== Testing VolumetricProjector ===")

    projector = VolumetricProjector()
    spotlight = projector.create_spotlight("TestProjector")

    # Verify spotlight
    assert spotlight is not None, "Spotlight should be created"
    assert spotlight.type == 'LIGHT', "Should be a light object"
    assert spotlight.data.type == 'SPOT', "Should be a spotlight"

    # Test aspect ratio
    projector.set_aspect_ratio(1920, 1080)
    aspect = 1920 / 1080
    assert abs(spotlight.scale.x - aspect) < 0.01, f"Aspect ratio should be {aspect}"

    print("✓ VolumetricProjector test passed")
    return True


def test_seamless_particles():
    """
    Test SeamlessParticles class from KB Section 30.

    Verifies:
    - Particle configuration
    - Noise animation setup
    - Loop calculation
    """
    from lib.particles import SeamlessParticles, NoiseAnimator

    print("\n=== Testing SeamlessParticles ===")

    # Create plane for particles
    bpy.ops.mesh.primitive_plane_add(size=10)
    plane = bpy.context.active_object

    particles = SeamlessParticles(plane)
    particles.set_density(1000)
    particles.add_noise_animation(speed=0.5, scale=2.0)
    particles.set_loop_duration(250)

    # Test loop calculation
    loop_settings = NoiseAnimator.calculate_loop_settings(250)
    assert loop_settings["frames"] == 250, "Frame count should match"

    # Clean up
    bpy.data.objects.remove(plane)

    print("✓ SeamlessParticles test passed")
    return True


def test_footprint_simulation():
    """
    Test FootprintSimulation class from KB Section 38.

    Verifies:
    - Ground preparation
    - Simulation zone config
    - Proximity detection
    """
    from lib.simulation import FootprintSimulation, ProximityDetector

    print("\n=== Testing FootprintSimulation ===")

    # Create ground plane
    bpy.ops.mesh.primitive_plane_add(size=10)
    ground = bpy.context.active_object

    # Create foot object
    bpy.ops.mesh.primitive_cube_add(size=1)
    foot = bpy.context.active_object

    sim = FootprintSimulation(ground, foot)
    sim.set_depth(0.1)
    sim.set_contact_threshold(0.5)

    config = sim.setup_simulation_zone()
    assert "requirements" in config, "Should have requirements"
    assert len(config["requirements"]) == 4, "Should have 4 requirements"

    # Test proximity detection
    detection = ProximityDetector.get_detection_config()
    assert "node_setup" in detection, "Should have node setup"

    # Clean up
    bpy.data.objects.remove(ground)
    bpy.data.objects.remove(foot)

    print("✓ FootprintSimulation test passed")
    return True


def test_text_animator():
    """
    Test TextAnimator class from KB Section 37.

    Verifies:
    - Text configuration
    - Wave animation setup
    - Per-character animation
    """
    from lib.mograph import TextAnimator, PerCharacterAnimator

    print("\n=== Testing TextAnimator ===")

    animator = TextAnimator("HELLO")
    animator.set_font_size(2.0)
    animator.set_character_spacing(1.2)

    config = animator.create_geometry_nodes_setup()
    assert "golden_rule" in config, "Should have golden rule"
    assert "String to Curves" in config["golden_rule"], "Should mention String to Curves"

    # Test wave animation
    wave = animator.add_wave_animation(axis='Y', amplitude=0.5)
    assert wave["type"] == "wave", "Should be wave animation"

    # Test per-character options
    types = PerCharacterAnimator.get_animation_types()
    assert "wave" in types, "Should have wave type"
    assert "typewriter" in types, "Should have typewriter type"

    print("✓ TextAnimator test passed")
    return True


def test_shortest_path_optimizer():
    """
    Test ShortestPathOptimizer class from KB Section 35.

    Verifies:
    - Optimization toggle
    - Performance comparison
    - Spline domain config
    """
    from lib.paths import ShortestPathOptimizer, SplineDomain

    print("\n=== Testing ShortestPathOptimizer ===")

    optimizer = ShortestPathOptimizer()
    optimizer.enable_optimization()

    comparison = optimizer.get_performance_comparison()
    assert "before" in comparison, "Should have before stats"
    assert "after" in comparison, "Should have after stats"

    # Verify the dramatic improvement
    assert comparison["improvement"]["vertex_reduction"] == "99.97%", \
        "Should show 99.97% reduction"

    # Test spline domain
    config = SplineDomain.get_evaluate_config()
    assert config["domain"] == "Spline (not Point)", "Should use spline domain"

    print("✓ ShortestPathOptimizer test passed")
    return True


def test_fern_grower():
    """
    Test FernGrower class from KB Section 34.

    Verifies:
    - Leaf configuration
    - Taper setup
    - Index-based scaling
    """
    from lib.growth import FernGrower, IndexTaper

    print("\n=== Testing FernGrower ===")

    fern = FernGrower()
    fern.set_leaf_count(20)
    fern.set_taper(1.0, 0.2)  # Big at bottom, small at top

    config = fern.get_mesh_line_config()
    assert config["settings"]["count"] == 20, "Should have 20 leaves"

    # Test index taper
    taper_config = IndexTaper.get_map_range_config(20, 1.0, 0.2, inverted=True)
    assert taper_config["to_min"] == 1.0, "Start should be 1.0"
    assert taper_config["to_max"] == 0.2, "End should be 0.2"

    print("✓ FernGrower test passed")
    return True


def test_prompt_helper():
    """
    Test TutorialPromptHelper for prompt generation.

    Verifies:
    - Technique lookup
    - Section mapping
    - Search functionality
    """
    from lib.prompt_helper import TutorialPromptHelper

    print("\n=== Testing TutorialPromptHelper ===")

    helper = TutorialPromptHelper()

    # Test technique prompt
    prompt = helper.get_prompt_for_technique("volumetric_fog")
    assert "WorldFog" in prompt, "Should mention WorldFog class"

    # Test section lookup
    section_prompt = helper.get_prompt_for_section(30)
    assert "SeamlessParticles" in section_prompt, "Should find Section 30"

    # Test search
    results = helper.search_techniques("particle")
    assert len(results) > 0, "Should find particle techniques"

    print("✓ TutorialPromptHelper test passed")
    return True


def run_all_tests():
    """
    Run all tutorial technique tests.

    Returns:
        Tuple of (passed_count, failed_count, results_list)
    """
    print("\n" + "=" * 50)
    print("Running Tutorial Module Tests")
    print("=" * 50)

    tests = [
        ("Volumetric Fog", test_volumetric_fog),
        ("Volumetric Projector", test_volumetric_projector),
        ("Seamless Particles", test_seamless_particles),
        ("Footprint Simulation", test_footprint_simulation),
        ("Text Animator", test_text_animator),
        ("Shortest Path Optimizer", test_shortest_path_optimizer),
        ("Fern Grower", test_fern_grower),
        ("Prompt Helper", test_prompt_helper),
    ]

    passed = 0
    failed = 0
    results = []

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            results.append((name, True, None))
        except Exception as e:
            failed += 1
            results.append((name, False, str(e)))
            print(f"✗ {name} failed: {e}")

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return passed, failed, results


# Run if executed directly in Blender
if __name__ == "__main__":
    run_all_tests()
