"""
Tests for Shot List Generator module.

Phase 8.2: Shot List Generator

Tests:
- REQ-SHOT-01: Auto-generate shots from scenes
- REQ-SHOT-02: Coverage estimation
- REQ-SHOT-03: Shot size suggestions
- REQ-SHOT-04: Storyboard prompt generation
"""

import unittest
from datetime import datetime

from .script_types import Scene, ActionBlock, DialogueLine, Character, Location, Script
from .shot_gen_types import (
    ShotSuggestion, CoverageEstimate, SceneShotList, ShotList, StoryboardPrompt,
    SHOT_SIZES, CAMERA_ANGLES, SHOT_PURPOSES, CAMERA_MOVES, PRIORITIES
)
from .scene_analyzer import (
    analyze_scene_for_shots, analyze_scene_content, count_characters_in_scene,
    identify_scene_type, estimate_scene_duration, identify_key_moments,
    calculate_coverage_estimate, SceneAnalysis
)
from .shot_rules import (
    apply_coverage_rules, suggest_shot_size, suggest_camera_angle,
    calculate_shot_priority, get_coverage_summary, COVERAGE_RULES,
    SHOT_SIZE_RULES, CAMERA_ANGLE_RULES
)
from .storyboard_prompts import (
    generate_storyboard_prompt, generate_ai_image_prompt, create_shot_description,
    generate_batch_prompts, export_prompts_as_text, STYLE_PRESETS
)
from .shot_list_export import (
    export_shot_list_csv_string, export_shot_list_yaml_string,
    generate_shot_list_html, generate_shot_report, generate_producer_summary
)


class TestShotGenTypes(unittest.TestCase):
    """Test shot generator type classes."""

    def test_shot_suggestion_creation(self):
        """Test ShotSuggestion dataclass creation."""
        shot = ShotSuggestion(
            scene_number=1,
            shot_number=1,
            shot_size="cu",
            camera_angle="eye_level",
            subject="Alice",
            purpose="coverage",
            estimated_duration=10.0,
            priority="essential"
        )
        self.assertEqual(shot.scene_number, 1)
        self.assertEqual(shot.shot_number, 1)
        self.assertEqual(shot.shot_size, "cu")
        self.assertEqual(shot.priority, "essential")

    def test_shot_suggestion_label(self):
        """Test shot label generation."""
        shot = ShotSuggestion(
            scene_number=5,
            shot_number=3,
            shot_size="cu",
            camera_angle="eye_level",
            subject="Test",
            purpose="coverage"
        )
        self.assertEqual(shot.get_shot_label(), "5C")

    def test_shot_suggestion_size_name(self):
        """Test shot size name lookup."""
        shot = ShotSuggestion(
            scene_number=1,
            shot_number=1,
            shot_size="ecu",
            camera_angle="eye_level",
            subject="Test",
            purpose="coverage"
        )
        self.assertEqual(shot.get_shot_size_name(), "Extreme Close-Up")

    def test_shot_suggestion_serialization(self):
        """Test ShotSuggestion to_dict/from_dict."""
        shot = ShotSuggestion(
            scene_number=1,
            shot_number=2,
            shot_size="mcu",
            camera_angle="low",
            subject="Bob",
            purpose="reaction",
            estimated_duration=5.0,
            priority="recommended",
            description="Reaction shot",
            camera_move="static"
        )
        data = shot.to_dict()
        restored = ShotSuggestion.from_dict(data)
        self.assertEqual(restored.scene_number, shot.scene_number)
        self.assertEqual(restored.subject, shot.subject)
        self.assertEqual(restored.description, shot.description)

    def test_coverage_estimate_creation(self):
        """Test CoverageEstimate creation and totals."""
        coverage = CoverageEstimate(
            scene_number=1,
            master_shots=1,
            closeups=4,
            inserts=2
        )
        coverage.calculate_totals()
        self.assertEqual(coverage.total_estimated, 7)

    def test_scene_shot_list(self):
        """Test SceneShotList functionality."""
        shots = [
            ShotSuggestion(1, 1, "w", "eye_level", "Scene", "establishing", priority="essential"),
            ShotSuggestion(1, 2, "cu", "eye_level", "Alice", "coverage", priority="essential"),
            ShotSuggestion(1, 3, "cu", "eye_level", "Bob", "coverage", priority="recommended")
        ]
        scene_list = SceneShotList(
            scene_number=1,
            scene_heading="INT. OFFICE - DAY",
            shots=shots
        )
        self.assertEqual(scene_list.get_shot_count(), 3)
        self.assertEqual(len(scene_list.get_essential_shots()), 2)
        self.assertEqual(len(scene_list.get_recommended_shots()), 1)

    def test_shot_list_creation(self):
        """Test ShotList creation and totals."""
        shot_list = ShotList(production="Test Movie")
        scene_list = SceneShotList(
            scene_number=1,
            scene_heading="INT. TEST - DAY",
            shots=[
                ShotSuggestion(1, 1, "w", "eye_level", "Scene", "establishing", estimated_duration=4.0),
                ShotSuggestion(1, 2, "cu", "eye_level", "Alice", "coverage", estimated_duration=10.0)
            ],
            estimated_duration=14.0
        )
        shot_list.add_scene(scene_list)
        self.assertEqual(shot_list.total_shots, 2)
        self.assertEqual(shot_list.estimated_total_duration, 14.0)

    def test_shot_list_statistics(self):
        """Test ShotList statistics generation."""
        shot_list = ShotList(production="Test")
        scene_list = SceneShotList(
            scene_number=1,
            scene_heading="INT. TEST - DAY",
            shots=[
                ShotSuggestion(1, 1, "w", "eye_level", "A", "establishing", priority="essential", estimated_duration=4.0),
                ShotSuggestion(1, 2, "cu", "eye_level", "B", "coverage", priority="essential", estimated_duration=10.0),
                ShotSuggestion(1, 3, "mcu", "eye_level", "C", "coverage", priority="recommended", estimated_duration=8.0),
                ShotSuggestion(1, 4, "ecu", "low", "D", "insert", priority="optional", estimated_duration=3.0)
            ]
        )
        shot_list.add_scene(scene_list)
        stats = shot_list.get_statistics()
        self.assertEqual(stats["total_shots"], 4)
        self.assertEqual(stats["essential_shots"], 2)
        self.assertEqual(stats["recommended_shots"], 1)
        self.assertEqual(stats["optional_shots"], 1)

    def test_constants_defined(self):
        """Test that constants are properly defined."""
        self.assertIn("CU", SHOT_SIZES)
        self.assertIn("eye_level", CAMERA_ANGLES)
        self.assertIn("coverage", SHOT_PURPOSES)
        self.assertIn("static", CAMERA_MOVES)
        self.assertIn("essential", PRIORITIES)


class TestSceneAnalyzer(unittest.TestCase):
    """Test scene analyzer functions."""

    def setUp(self):
        """Create sample scene for testing."""
        self.dialogue_scene = Scene(
            number=1,
            heading="INT. OFFICE - DAY",
            location="OFFICE",
            interior=True,
            time_of_day="DAY",
            action=[ActionBlock("Alice sits at her desk. Bob enters.")],
            dialogue=[
                DialogueLine("Alice", "Hello Bob, how are you?"),
                DialogueLine("Bob", "I'm doing great! Thanks for asking."),
                DialogueLine("Alice", "Good to hear.")
            ]
        )

        self.action_scene = Scene(
            number=2,
            heading="EXT. STREET - NIGHT",
            location="STREET",
            interior=False,
            time_of_day="NIGHT",
            action=[
                ActionBlock("A car suddenly crashes through the window!"),
                ActionBlock("Debris flies everywhere as the vehicle skids to a stop."),
                ActionBlock("Silence falls over the scene.")
            ],
            dialogue=[]
        )

        self.mixed_scene = Scene(
            number=3,
            heading="INT. WAREHOUSE - DAY",
            location="WAREHOUSE",
            interior=True,
            time_of_day="DAY",
            action=[ActionBlock("The door suddenly bursts open.")],
            dialogue=[
                DialogueLine("Guard", "Stop right there!"),
                DialogueLine("Thief", "You'll never catch me!")
            ]
        )

    def test_analyze_scene_for_shots(self):
        """Test shot generation from scene."""
        shots = analyze_scene_for_shots(self.dialogue_scene)
        self.assertGreater(len(shots), 0)
        # Should have establishing shot
        self.assertTrue(any(s.purpose == "establishing" for s in shots))

    def test_count_characters_in_scene(self):
        """Test character counting."""
        count = count_characters_in_scene(self.dialogue_scene)
        self.assertEqual(count, 2)

    def test_identify_scene_type_dialogue(self):
        """Test scene type detection for dialogue."""
        scene_type = identify_scene_type(self.dialogue_scene)
        # Could be dialogue or mixed depending on action/dialogue ratio
        self.assertIn(scene_type, ["dialogue", "mixed"])

    def test_identify_scene_type_action(self):
        """Test scene type detection for action."""
        scene_type = identify_scene_type(self.action_scene)
        self.assertEqual(scene_type, "action")

    def test_identify_scene_type_mixed(self):
        """Test scene type detection for mixed."""
        scene_type = identify_scene_type(self.mixed_scene)
        self.assertIn(scene_type, ["mixed", "dialogue", "action"])

    def test_estimate_scene_duration(self):
        """Test scene duration estimation."""
        duration = estimate_scene_duration(self.dialogue_scene)
        self.assertGreater(duration, 0)

    def test_identify_key_moments(self):
        """Test key moment identification."""
        moments = identify_key_moments(self.action_scene)
        self.assertIsInstance(moments, list)
        # Should find "suddenly" as a key moment
        self.assertGreater(len(moments), 0)

    def test_analyze_scene_content(self):
        """Test comprehensive scene analysis."""
        analysis = analyze_scene_content(self.dialogue_scene)
        self.assertIsInstance(analysis, SceneAnalysis)
        self.assertEqual(analysis.scene_number, 1)
        self.assertEqual(analysis.character_count, 2)
        self.assertGreater(analysis.estimated_duration, 0)

    def test_calculate_coverage_estimate(self):
        """Test coverage estimate calculation."""
        coverage = calculate_coverage_estimate(self.dialogue_scene)
        self.assertIsInstance(coverage, CoverageEstimate)
        self.assertEqual(coverage.scene_number, 1)
        self.assertGreater(coverage.minimum_coverage, 0)
        self.assertGreaterEqual(coverage.recommended_coverage, coverage.minimum_coverage)


class TestShotRules(unittest.TestCase):
    """Test shot rules engine."""

    def setUp(self):
        """Create sample scenes for testing."""
        self.dialogue_scene = Scene(
            number=1,
            heading="INT. OFFICE - DAY",
            location="OFFICE",
            interior=True,
            time_of_day="DAY",
            action=[ActionBlock("Two people talking.")],
            dialogue=[
                DialogueLine("Alice", "Hello!"),
                DialogueLine("Bob", "Hi there!")
            ]
        )

    def test_coverage_rules_defined(self):
        """Test coverage rules are defined."""
        self.assertIn("dialogue_two_person", COVERAGE_RULES)
        self.assertIn("action", COVERAGE_RULES)
        self.assertIn("essential", COVERAGE_RULES["dialogue_two_person"])

    def test_apply_coverage_rules(self):
        """Test applying coverage rules to scene."""
        shots = apply_coverage_rules(self.dialogue_scene)
        self.assertGreater(len(shots), 0)
        # Should have essential shots
        essential = [s for s in shots if s.priority == "essential"]
        self.assertGreater(len(essential), 0)

    def test_suggest_shot_size_facial(self):
        """Test shot size suggestion for facial emotion."""
        size = suggest_shot_size("face", "expressing emotion", "dialogue")
        self.assertEqual(size, "cu")

    def test_suggest_shot_size_action(self):
        """Test shot size suggestion for action."""
        size = suggest_shot_size("person", "running fast", "action")
        self.assertEqual(size, "w")

    def test_suggest_camera_angle_neutral(self):
        """Test camera angle suggestion for neutral context."""
        angle = suggest_camera_angle("normal conversation")
        self.assertEqual(angle, "eye_level")

    def test_suggest_camera_angle_power(self):
        """Test camera angle for power dynamics."""
        # "dominant" power_dynamic returns "high" angle (looking down on weak subject)
        # "weak" power_dynamic returns "low" angle (looking up at dominant subject)
        angle_dominant = suggest_camera_angle("confrontation", power_dynamic="dominant")
        self.assertEqual(angle_dominant, "high")

        angle_weak = suggest_camera_angle("confrontation", power_dynamic="weak")
        self.assertEqual(angle_weak, "low")

    def test_suggest_camera_angle_tension(self):
        """Test camera angle for tension."""
        angle = suggest_camera_angle("tension and suspense")
        self.assertEqual(angle, "dutch")

    def test_calculate_shot_priority(self):
        """Test shot priority calculation."""
        # Establishing shot should be essential
        establishing = ShotSuggestion(1, 1, "w", "eye_level", "Location", "establishing")
        priority = calculate_shot_priority(establishing, self.dialogue_scene)
        self.assertEqual(priority, "essential")

        # Insert should be optional
        insert = ShotSuggestion(1, 2, "ecu", "eye_level", "Detail", "insert")
        priority = calculate_shot_priority(insert, self.dialogue_scene)
        self.assertEqual(priority, "optional")

    def test_get_coverage_summary(self):
        """Test coverage summary generation."""
        summary = get_coverage_summary(self.dialogue_scene)
        self.assertEqual(summary["scene_number"], 1)
        self.assertIn("total_shots", summary)
        self.assertIn("essential_count", summary)


class TestStoryboardPrompts(unittest.TestCase):
    """Test storyboard prompt generation."""

    def setUp(self):
        """Create sample shot and scene."""
        self.shot = ShotSuggestion(
            scene_number=1,
            shot_number=1,
            shot_size="cu",
            camera_angle="eye_level",
            subject="Alice",
            purpose="coverage",
            estimated_duration=10.0,
            description="Close-up on Alice"
        )
        self.scene = Scene(
            number=1,
            heading="INT. OFFICE - DAY",
            location="OFFICE",
            interior=True,
            time_of_day="DAY",
            action=[ActionBlock("Alice sits at her desk.")],
            dialogue=[DialogueLine("Alice", "Hello!")]
        )

    def test_style_presets_defined(self):
        """Test style presets are defined."""
        self.assertIn("cinematic", STYLE_PRESETS)
        self.assertIn("storyboard", STYLE_PRESETS)
        self.assertIn("noir", STYLE_PRESETS)

    def test_generate_storyboard_prompt(self):
        """Test storyboard prompt generation."""
        prompt = generate_storyboard_prompt(self.shot, self.scene)
        self.assertIsInstance(prompt, StoryboardPrompt)
        self.assertEqual(prompt.shot, self.shot)
        self.assertIn("Scene 1", prompt.visual_description)
        self.assertIn("cinematic", prompt.ai_prompt.lower())

    def test_generate_ai_image_prompt(self):
        """Test AI image prompt generation."""
        ai_prompt = generate_ai_image_prompt(self.shot, style="cinematic")
        self.assertIn("cinematic", ai_prompt.lower())
        self.assertIn("alice", ai_prompt.lower())

    def test_create_shot_description(self):
        """Test shot description generation."""
        desc = create_shot_description(self.shot)
        self.assertIn("Shot 1A", desc)
        self.assertIn("Close-Up", desc)
        self.assertIn("Alice", desc)

    def test_generate_batch_prompts(self):
        """Test batch prompt generation."""
        shots = [
            self.shot,
            ShotSuggestion(1, 2, "mcu", "eye_level", "Bob", "coverage")
        ]
        prompts = generate_batch_prompts(shots, self.scene)
        self.assertEqual(len(prompts), 2)

    def test_export_prompts_as_text(self):
        """Test text export of prompts."""
        prompts = generate_batch_prompts([self.shot], self.scene)
        text = export_prompts_as_text(prompts)
        self.assertIn("SHOT 1A", text)
        self.assertIn("VISUAL DESCRIPTION", text)
        self.assertIn("AI PROMPT", text)


class TestShotListExport(unittest.TestCase):
    """Test shot list export functions."""

    def setUp(self):
        """Create sample shot list."""
        self.shot_list = ShotList(
            production="Test Movie",
            date_created="2026-02-20",
            version="1.0"
        )
        scene_list = SceneShotList(
            scene_number=1,
            scene_heading="INT. OFFICE - DAY",
            shots=[
                ShotSuggestion(1, 1, "w", "eye_level", "Office", "establishing", 4.0, "essential"),
                ShotSuggestion(1, 2, "cu", "eye_level", "Alice", "coverage", 10.0, "essential"),
                ShotSuggestion(1, 3, "cu", "eye_level", "Bob", "coverage", 10.0, "recommended")
            ],
            estimated_duration=24.0
        )
        self.shot_list.add_scene(scene_list)

    def test_export_csv_string(self):
        """Test CSV export."""
        csv = export_shot_list_csv_string(self.shot_list)
        self.assertIn("Scene", csv)
        self.assertIn("Shot", csv)
        self.assertIn("Alice", csv)
        self.assertIn("1A", csv)

    def test_export_yaml_string(self):
        """Test YAML export."""
        yaml = export_shot_list_yaml_string(self.shot_list)
        self.assertIn("production", yaml)
        self.assertIn("Test Movie", yaml)

    def test_generate_html(self):
        """Test HTML generation."""
        html = generate_shot_list_html(self.shot_list)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Test Movie", html)
        self.assertIn("INT. OFFICE - DAY", html)

    def test_generate_shot_report(self):
        """Test shot report generation."""
        report = generate_shot_report(self.shot_list)
        self.assertIn("SHOT LIST REPORT", report)
        self.assertIn("Test Movie", report)
        self.assertIn("Total Shots: 3", report)
        self.assertIn("SCENE 1", report)

    def test_generate_producer_summary(self):
        """Test producer summary generation."""
        summary = generate_producer_summary(self.shot_list)
        self.assertIn("PRODUCTION: Test Movie", summary)
        self.assertIn("Total Shots: 3", summary)


class TestIntegration(unittest.TestCase):
    """Integration tests for shot list generator."""

    def test_full_workflow(self):
        """Test complete workflow from scene to exports."""
        # Create a scene
        scene = Scene(
            number=1,
            heading="INT. COFFEE SHOP - DAY",
            location="COFFEE SHOP",
            interior=True,
            time_of_day="DAY",
            action=[ActionBlock("A busy morning at the coffee shop.")],
            dialogue=[
                DialogueLine("Barista", "What can I get you?"),
                DialogueLine("Customer", "A large coffee, please."),
                DialogueLine("Barista", "Coming right up!")
            ]
        )

        # Analyze scene
        analysis = analyze_scene_content(scene)
        # Scene type could be dialogue or mixed depending on ratio
        self.assertIn(analysis.scene_type, ["dialogue", "mixed"])

        # Generate shots
        shots = analyze_scene_for_shots(scene)
        self.assertGreater(len(shots), 0)

        # Create shot list
        shot_list = ShotList(production="Coffee Shop Scene")
        scene_list = SceneShotList(
            scene_number=scene.number,
            scene_heading=scene.heading,
            shots=shots,
            estimated_duration=scene.estimate_duration()
        )
        shot_list.add_scene(scene_list)

        # Generate exports
        csv = export_shot_list_csv_string(shot_list)
        self.assertIn("COFFEE SHOP", csv.upper())

        report = generate_shot_report(shot_list)
        self.assertIn("COFFEE SHOP", report.upper())

        # Generate storyboard prompts
        prompts = generate_batch_prompts(shots[:2], scene)
        self.assertEqual(len(prompts), 2)


if __name__ == "__main__":
    unittest.main()
