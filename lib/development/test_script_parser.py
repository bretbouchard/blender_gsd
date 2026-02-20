"""
Tests for Script Parser Module.

Tests for:
- Script types (REQ-SCRIPT-03)
- Fountain parser (REQ-SCRIPT-01)
- FDX parser (REQ-SCRIPT-02)
- Beat generator (REQ-SCRIPT-04)
- Script analysis (REQ-SCRIPT-05)
"""

import unittest
import tempfile
import os
from pathlib import Path

from lib.development.script_types import (
    Script,
    Scene,
    Character,
    Location,
    ActionBlock,
    DialogueLine,
    Transition,
    Beat,
    BeatSheet,
    ScriptAnalysis,
)

from lib.development.fountain_parser import (
    FountainParser,
    parse_fountain,
    parse_fountain_file,
)

from lib.development.fdx_parser import (
    FdxParser,
    parse_fdx,
)

from lib.development.beat_generator import (
    generate_beat_sheet,
    identify_act_breaks,
    calculate_pacing,
    identify_emotional_peaks,
    create_beat_summary,
)

from lib.development.script_analysis import (
    analyze_script,
    get_character_network,
    get_location_schedule,
    get_cast_list,
    get_daily_breakdown,
    compare_characters,
    export_analysis_report,
)


class TestScriptTypes(unittest.TestCase):
    """Test script type dataclasses."""

    def test_action_block_creation(self):
        """Test creating an action block."""
        action = ActionBlock(text="The door opens.", page=1.5)
        self.assertEqual(action.text, "The door opens.")
        self.assertEqual(action.page, 1.5)

    def test_action_block_serialization(self):
        """Test action block serialization."""
        action = ActionBlock(text="The door opens.", page=1.5)
        data = action.to_dict()
        restored = ActionBlock.from_dict(data)
        self.assertEqual(restored.text, action.text)
        self.assertEqual(restored.page, action.page)

    def test_dialogue_line_creation(self):
        """Test creating a dialogue line."""
        dialogue = DialogueLine(
            character="JOHN",
            text="Hello, world!",
            extension="V.O.",
            parenthetical="quietly",
            page=2.0
        )
        self.assertEqual(dialogue.character, "JOHN")
        self.assertEqual(dialogue.text, "Hello, world!")
        self.assertEqual(dialogue.extension, "V.O.")
        self.assertEqual(dialogue.word_count(), 2)

    def test_dialogue_line_serialization(self):
        """Test dialogue line serialization."""
        dialogue = DialogueLine(
            character="JOHN",
            text="Hello, world!",
            extension="V.O."
        )
        data = dialogue.to_dict()
        restored = DialogueLine.from_dict(data)
        self.assertEqual(restored.character, dialogue.character)
        self.assertEqual(restored.text, dialogue.text)

    def test_transition_creation(self):
        """Test creating a transition."""
        trans = Transition(type="CUT TO:", page=5.0)
        self.assertEqual(trans.type, "CUT TO:")
        self.assertEqual(trans.page, 5.0)

    def test_scene_creation(self):
        """Test creating a scene."""
        scene = Scene(
            number=1,
            heading="INT. WAREHOUSE - NIGHT",
            location="WAREHOUSE",
            interior=True,
            time_of_day="NIGHT"
        )
        self.assertEqual(scene.number, 1)
        self.assertEqual(scene.location, "WAREHOUSE")
        self.assertTrue(scene.interior)

    def test_scene_with_elements(self):
        """Test scene with action and dialogue."""
        scene = Scene(
            number=1,
            heading="INT. OFFICE - DAY",
            location="OFFICE"
        )
        scene.action.append(ActionBlock(text="A man enters.", page=1.0))
        scene.dialogue.append(DialogueLine(character="MAN", text="Hello.", page=1.0))

        self.assertEqual(len(scene.action), 1)
        self.assertEqual(len(scene.dialogue), 1)
        self.assertIn("MAN", scene.get_characters_in_scene())

    def test_scene_duration_estimate(self):
        """Test scene duration estimation."""
        scene = Scene(
            number=1,
            heading="INT. OFFICE - DAY",
            location="OFFICE"
        )
        scene.action.append(ActionBlock(text="The door opens slowly.", page=1.0))
        scene.dialogue.append(DialogueLine(
            character="JOHN",
            text="Hello there, how are you doing today?",
            page=1.0
        ))

        duration = scene.estimate_duration()
        self.assertGreater(duration, 0)

    def test_scene_serialization(self):
        """Test scene serialization."""
        scene = Scene(
            number=1,
            heading="INT. OFFICE - DAY",
            location="OFFICE",
            interior=True,
            time_of_day="DAY",
            page_start=1.0,
            page_end=2.0
        )
        data = scene.to_dict()
        restored = Scene.from_dict(data)
        self.assertEqual(restored.number, scene.number)
        self.assertEqual(restored.heading, scene.heading)
        self.assertEqual(restored.location, scene.location)

    def test_character_creation(self):
        """Test creating a character."""
        char = Character(name="JOHN")
        char.add_dialogue(scene_number=1, word_count=10)
        char.add_dialogue(scene_number=2, word_count=20)

        self.assertEqual(char.dialogue_count, 2)
        self.assertEqual(char.dialogue_word_count, 30)
        self.assertEqual(char.first_appearance, 1)
        self.assertEqual(char.last_appearance, 2)

    def test_character_with_extension(self):
        """Test character with voice-over extension."""
        char = Character(name="JOHN")
        char.add_dialogue(scene_number=1, word_count=10, extension="V.O.")

        self.assertIn("V.O.", char.aliases)

    def test_character_serialization(self):
        """Test character serialization."""
        char = Character(
            name="JOHN",
            dialogue_count=5,
            dialogue_word_count=100,
            first_appearance=1,
            last_appearance=10,
            scenes_appearing=[1, 5, 10]
        )
        data = char.to_dict()
        restored = Character.from_dict(data)
        self.assertEqual(restored.name, char.name)
        self.assertEqual(restored.dialogue_count, char.dialogue_count)

    def test_location_creation(self):
        """Test creating a location."""
        loc = Location(name="WAREHOUSE", interior=False)
        loc.add_scene(scene_number=1, time_of_day="NIGHT")
        loc.add_scene(scene_number=5, time_of_day="DAY")

        self.assertEqual(loc.scene_count, 2)
        self.assertIn("NIGHT", loc.time_variants)
        self.assertIn("DAY", loc.time_variants)

    def test_location_serialization(self):
        """Test location serialization."""
        loc = Location(
            name="WAREHOUSE",
            scene_count=3,
            scenes=[1, 5, 10],
            interior=False,
            time_variants=["DAY", "NIGHT"]
        )
        data = loc.to_dict()
        restored = Location.from_dict(data)
        self.assertEqual(restored.name, loc.name)
        self.assertEqual(restored.scene_count, loc.scene_count)

    def test_beat_creation(self):
        """Test creating a beat."""
        beat = Beat(
            scene_number=10,
            beat_type="midpoint",
            description="Stakes are raised",
            emotional_value=0.8,
            pages=2.5
        )
        self.assertEqual(beat.scene_number, 10)
        self.assertEqual(beat.beat_type, "midpoint")

    def test_beat_sheet_creation(self):
        """Test creating a beat sheet."""
        sheet = BeatSheet(
            beats=[
                Beat(scene_number=1, beat_type="setup"),
                Beat(scene_number=10, beat_type="midpoint"),
            ],
            act_breaks=[10, 25]
        )
        self.assertEqual(len(sheet.beats), 2)
        self.assertEqual(len(sheet.act_breaks), 2)

    def test_beat_sheet_get_beat(self):
        """Test finding beat by type."""
        sheet = BeatSheet(
            beats=[
                Beat(scene_number=1, beat_type="setup"),
                Beat(scene_number=10, beat_type="midpoint"),
            ]
        )
        midpoint = sheet.get_beat_by_type("midpoint")
        self.assertIsNotNone(midpoint)
        self.assertEqual(midpoint.scene_number, 10)

    def test_script_creation(self):
        """Test creating a script."""
        script = Script(
            title="Test Script",
            author="Test Author",
            draft="First Draft",
            total_pages=10.0,
            estimated_runtime=10.0
        )
        self.assertEqual(script.title, "Test Script")
        self.assertEqual(script.author, "Test Author")

    def test_script_with_scenes(self):
        """Test script with scenes."""
        script = Script(title="Test")
        script.scenes.append(Scene(number=1, heading="INT. A - DAY", location="A"))
        script.scenes.append(Scene(number=2, heading="EXT. B - NIGHT", location="B"))

        self.assertEqual(len(script.scenes), 2)

    def test_script_get_scene_by_number(self):
        """Test finding scene by number."""
        script = Script(title="Test")
        script.scenes.append(Scene(number=1, heading="INT. A - DAY", location="A"))
        script.scenes.append(Scene(number=2, heading="EXT. B - NIGHT", location="B"))

        scene = script.get_scene_by_number(2)
        self.assertIsNotNone(scene)
        self.assertEqual(scene.location, "B")

    def test_script_get_character_by_name(self):
        """Test finding character by name."""
        script = Script(title="Test")
        script.characters.append(Character(name="JOHN"))
        script.characters.append(Character(name="JANE"))

        char = script.get_character_by_name("jane")  # Case-insensitive
        self.assertIsNotNone(char)
        self.assertEqual(char.name, "JANE")

    def test_script_get_interior_scenes(self):
        """Test filtering interior scenes."""
        script = Script(title="Test")
        script.scenes.append(Scene(number=1, heading="INT. A - DAY", location="A", interior=True))
        script.scenes.append(Scene(number=2, heading="EXT. B - NIGHT", location="B", interior=False))
        script.scenes.append(Scene(number=3, heading="INT. C - DAY", location="C", interior=True))

        interior = script.get_interior_scenes()
        self.assertEqual(len(interior), 2)

    def test_script_serialization(self):
        """Test script serialization to JSON."""
        script = Script(
            title="Test",
            author="Author",
            total_pages=5.0
        )
        script.scenes.append(Scene(number=1, heading="INT. A - DAY", location="A"))

        json_str = script.to_json()
        restored = Script.from_json(json_str)

        self.assertEqual(restored.title, script.title)
        self.assertEqual(restored.author, script.author)
        self.assertEqual(len(restored.scenes), 1)


class TestFountainParser(unittest.TestCase):
    """Test Fountain format parsing."""

    def setUp(self):
        """Set up parser."""
        self.parser = FountainParser()

    def test_parse_scene_heading(self):
        """Test parsing scene heading."""
        interior, location, time = self.parser._parse_heading("INT. WAREHOUSE - NIGHT")
        self.assertTrue(interior)
        self.assertEqual(location, "WAREHOUSE")
        self.assertEqual(time, "NIGHT")

    def test_parse_scene_heading_exterior(self):
        """Test parsing exterior scene heading."""
        interior, location, time = self.parser._parse_heading("EXT. BEACH - DAY")
        self.assertFalse(interior)
        self.assertEqual(location, "BEACH")
        self.assertEqual(time, "DAY")

    def test_parse_scene_heading_complex(self):
        """Test parsing complex scene heading."""
        interior, location, time = self.parser._parse_heading("INT./EXT. CAR - CONTINUOUS")
        self.assertTrue(interior)  # INT/EXT defaults to INT
        self.assertEqual(time, "CONTINUOUS")

    def test_parse_character_name(self):
        """Test parsing character name."""
        name, ext = self.parser._parse_character("JOHN")
        self.assertEqual(name, "JOHN")
        self.assertEqual(ext, "")

    def test_parse_character_with_extension(self):
        """Test parsing character with extension."""
        name, ext = self.parser._parse_character("JOHN (V.O.)")
        self.assertEqual(name, "JOHN")
        self.assertEqual(ext, "V.O.")

    def test_parse_simple_script(self):
        """Test parsing simple script."""
        fountain = """Title: Test Script
Author: Test Author

INT. OFFICE - DAY

A man sits at a desk.

JOHN
Hello there.

JANE
(cheerfully)
Hi! How are you?

EXT. PARK - DAY

The two walk together.
"""
        script = self.parser.parse(fountain)

        self.assertEqual(script.title, "Test Script")
        self.assertEqual(script.author, "Test Author")
        self.assertEqual(len(script.scenes), 2)

    def test_parse_scene_with_multiple_dialogue(self):
        """Test parsing scene with multiple dialogue."""
        fountain = """
INT. OFFICE - DAY

JOHN
Hello.

JANE
Hi there.

JOHN
How are you?

JANE
I'm fine, thanks.
"""
        script = self.parser.parse(fountain)

        self.assertEqual(len(script.scenes), 1)
        scene = script.scenes[0]
        self.assertEqual(len(scene.dialogue), 4)

    def test_parse_transitions(self):
        """Test parsing transitions."""
        fountain = """
INT. A - DAY

Some action.

CUT TO:

INT. B - NIGHT

More action.
"""
        script = self.parser.parse(fountain)

        # First scene should have a transition
        self.assertGreaterEqual(len(script.scenes[0].transitions), 1)

    def test_character_extraction(self):
        """Test character extraction from script."""
        fountain = """
INT. A - DAY

JOHN
Hello.

JANE
Hi!

JOHN
Goodbye.
"""
        script = self.parser.parse(fountain)

        self.assertEqual(len(script.characters), 2)

        john = script.get_character_by_name("JOHN")
        self.assertIsNotNone(john)
        self.assertEqual(john.dialogue_count, 2)

    def test_location_extraction(self):
        """Test location extraction from script."""
        fountain = """
INT. OFFICE - DAY

Action.

EXT. PARK - NIGHT

Action.

INT. OFFICE - DAY

More action.
"""
        script = self.parser.parse(fountain)

        self.assertEqual(len(script.locations), 2)

        office = script.get_location_by_name("OFFICE")
        self.assertIsNotNone(office)
        self.assertEqual(office.scene_count, 2)

    def test_parse_file(self):
        """Test parsing from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fountain', delete=False) as f:
            f.write("Title: File Test\n\nINT. A - DAY\n\nAction.\n")
            f.flush()

            try:
                script = self.parser.parse_file(f.name)
                self.assertEqual(script.title, "File Test")
                self.assertEqual(len(script.scenes), 1)
            finally:
                os.unlink(f.name)

    def test_convenience_function(self):
        """Test convenience parse function."""
        script = parse_fountain("Title: Test\n\nINT. A - DAY\n\nAction.")
        self.assertEqual(script.title, "Test")


class TestFdxParser(unittest.TestCase):
    """Test Final Draft XML parsing."""

    def setUp(self):
        """Set up parser."""
        self.parser = FdxParser()

    def test_parse_heading(self):
        """Test parsing FDX scene heading."""
        interior, location, time = self.parser._parse_heading("INT. WAREHOUSE - NIGHT")
        self.assertTrue(interior)
        self.assertEqual(location, "WAREHOUSE")
        self.assertEqual(time, "NIGHT")

    def test_parse_character(self):
        """Test parsing FDX character."""
        name, ext = self.parser._parse_character("JOHN (V.O.)")
        self.assertEqual(name, "JOHN")
        self.assertEqual(ext, "V.O.")

    def test_parse_simple_fdx(self):
        """Test parsing simple FDX XML."""
        xml = """<?xml version="1.0"?>
<FinalDraft>
  <Content>
    <Paragraph Type="Scene Heading">
      <Text>INT. OFFICE - DAY</Text>
    </Paragraph>
    <Paragraph Type="Action">
      <Text>A man enters.</Text>
    </Paragraph>
    <Paragraph Type="Character">
      <Text>JOHN</Text>
    </Paragraph>
    <Paragraph Type="Dialogue">
      <Text>Hello there.</Text>
    </Paragraph>
  </Content>
</FinalDraft>
"""
        script = self.parser.parse(xml)

        self.assertEqual(len(script.scenes), 1)
        self.assertEqual(len(script.scenes[0].action), 1)
        self.assertEqual(len(script.scenes[0].dialogue), 1)

    def test_parse_multiple_scenes(self):
        """Test parsing multiple scenes."""
        xml = """<?xml version="1.0"?>
<FinalDraft>
  <Content>
    <Paragraph Type="Scene Heading">
      <Text>INT. A - DAY</Text>
    </Paragraph>
    <Paragraph Type="Action">
      <Text>Action A.</Text>
    </Paragraph>
    <Paragraph Type="Scene Heading">
      <Text>EXT. B - NIGHT</Text>
    </Paragraph>
    <Paragraph Type="Action">
      <Text>Action B.</Text>
    </Paragraph>
  </Content>
</FinalDraft>
"""
        script = self.parser.parse(xml)

        self.assertEqual(len(script.scenes), 2)

    def test_parse_parenthetical(self):
        """Test parsing parenthetical."""
        xml = """<?xml version="1.0"?>
<FinalDraft>
  <Content>
    <Paragraph Type="Scene Heading">
      <Text>INT. A - DAY</Text>
    </Paragraph>
    <Paragraph Type="Character">
      <Text>JOHN</Text>
    </Paragraph>
    <Paragraph Type="Parenthetical">
      <Text>(quietly)</Text>
    </Paragraph>
    <Paragraph Type="Dialogue">
      <Text>Hello.</Text>
    </Paragraph>
  </Content>
</FinalDraft>
"""
        script = self.parser.parse(xml)

        self.assertEqual(len(script.scenes[0].dialogue), 1)
        self.assertEqual(script.scenes[0].dialogue[0].parenthetical, "quietly")

    def test_parse_file(self):
        """Test parsing from FDX file."""
        xml = """<?xml version="1.0"?>
<FinalDraft>
  <Content>
    <Paragraph Type="Scene Heading">
      <Text>INT. A - DAY</Text>
    </Paragraph>
    <Paragraph Type="Action">
      <Text>Action.</Text>
    </Paragraph>
  </Content>
</FinalDraft>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fdx', delete=False) as f:
            f.write(xml)
            f.flush()

            try:
                script = self.parser.parse_file(f.name)
                self.assertEqual(len(script.scenes), 1)
            finally:
                os.unlink(f.name)


class TestBeatGenerator(unittest.TestCase):
    """Test beat sheet generation."""

    def create_test_script(self, num_scenes=20):
        """Create a test script with multiple scenes."""
        script = Script(title="Test Script")

        for i in range(1, num_scenes + 1):
            scene = Scene(
                number=i,
                heading=f"INT. LOCATION {i} - DAY",
                location=f"LOCATION {i}"
            )
            scene.action.append(ActionBlock(text="Action text."))
            scene.dialogue.append(DialogueLine(
                character="JOHN",
                text="Some dialogue here."
            ))
            scene.estimate_duration()
            script.scenes.append(scene)

        script.characters.append(Character(name="JOHN", dialogue_count=num_scenes))
        script.calculate_statistics()

        return script

    def test_generate_save_the_cat_beat_sheet(self):
        """Test generating Save the Cat beat sheet."""
        script = self.create_test_script(20)
        beat_sheet = generate_beat_sheet(script, "save_the_cat")

        self.assertGreater(len(beat_sheet.beats), 0)

        # Check for key beats
        opening = beat_sheet.get_beat_by_type("opening_image")
        self.assertIsNotNone(opening)

        midpoint = beat_sheet.get_beat_by_type("midpoint")
        self.assertIsNotNone(midpoint)

    def test_generate_three_act_beat_sheet(self):
        """Test generating three-act beat sheet."""
        script = self.create_test_script(20)
        beat_sheet = generate_beat_sheet(script, "three_act")

        self.assertGreater(len(beat_sheet.beats), 0)

    def test_identify_act_breaks(self):
        """Test identifying act breaks."""
        script = self.create_test_script(20)
        breaks = identify_act_breaks(script, "save_the_cat")

        self.assertEqual(len(breaks), 2)  # Act 1 and Act 2 ends

    def test_calculate_pacing(self):
        """Test calculating pacing curve."""
        script = self.create_test_script(10)
        pacing = calculate_pacing(script)

        self.assertEqual(len(pacing), 10)
        # All values should be between 0 and 1
        for p in pacing:
            self.assertGreaterEqual(p, 0.0)
            self.assertLessEqual(p, 1.0)

    def test_identify_emotional_peaks(self):
        """Test identifying emotional peaks."""
        script = self.create_test_script(20)
        peaks = identify_emotional_peaks(script)

        # Should find some peaks
        self.assertGreater(len(peaks), 0)

        # All peaks should be valid scene numbers
        for peak in peaks:
            self.assertGreater(peak, 0)
            self.assertLessEqual(peak, 20)

    def test_create_beat_summary(self):
        """Test creating beat summary text."""
        script = self.create_test_script(20)
        beat_sheet = generate_beat_sheet(script, "save_the_cat")
        summary = create_beat_summary(script, beat_sheet)

        self.assertIn("Test Script", summary)
        self.assertIn("Scene", summary)


class TestScriptAnalysis(unittest.TestCase):
    """Test script analysis functions."""

    def create_test_script(self):
        """Create a test script for analysis."""
        script = Script(
            title="Test Script",
            author="Test Author",
            total_pages=10.0,
            estimated_runtime=10.0
        )

        # Add scenes
        for i in range(1, 11):
            interior = i % 2 == 0
            time = "DAY" if i % 3 == 0 else "NIGHT"
            scene = Scene(
                number=i,
                heading=f"{'INT' if interior else 'EXT'}. LOC {i} - {time}",
                location=f"LOC {i}",
                interior=interior,
                time_of_day=time
            )
            scene.action.append(ActionBlock(text="Action " * 10))
            scene.dialogue.append(DialogueLine(
                character="JOHN" if i % 2 == 0 else "JANE",
                text="Dialogue " * 5
            ))
            scene.estimate_duration()
            script.scenes.append(scene)

        # Add characters
        john = Character(name="JOHN", dialogue_count=5, dialogue_word_count=50)
        john.scenes_appearing = [2, 4, 6, 8, 10]
        script.characters.append(john)

        jane = Character(name="JANE", dialogue_count=5, dialogue_word_count=40)
        jane.scenes_appearing = [1, 3, 5, 7, 9]
        script.characters.append(jane)

        # Add locations
        for i in range(1, 11):
            loc = Location(name=f"LOC {i}")
            loc.add_scene(i, "DAY" if i % 3 == 0 else "NIGHT")
            script.locations.append(loc)

        return script

    def test_analyze_script(self):
        """Test comprehensive script analysis."""
        script = self.create_test_script()
        analysis = analyze_script(script)

        self.assertEqual(analysis.total_scenes, 10)
        self.assertEqual(analysis.character_count, 2)
        self.assertEqual(analysis.location_count, 10)
        self.assertGreater(analysis.estimated_runtime, 0)

    def test_analyze_script_pacing(self):
        """Test that analysis includes pacing curve."""
        script = self.create_test_script()
        analysis = analyze_script(script)

        self.assertEqual(len(analysis.pacing), 10)

    def test_analyze_script_recommendations(self):
        """Test that analysis generates recommendations."""
        script = self.create_test_script()
        analysis = analyze_script(script)

        self.assertGreater(len(analysis.recommendations), 0)

    def test_get_character_network(self):
        """Test character network generation."""
        script = self.create_test_script()
        network = get_character_network(script)

        # Should have entries for JOHN and JANE
        self.assertIn("JOHN", network)
        self.assertIn("JANE", network)

    def test_get_location_schedule(self):
        """Test location schedule generation."""
        script = self.create_test_script()
        schedule = get_location_schedule(script)

        self.assertEqual(len(schedule), 10)  # 10 locations

    def test_get_cast_list(self):
        """Test cast list generation."""
        script = self.create_test_script()
        cast = get_cast_list(script)

        self.assertEqual(len(cast), 2)
        self.assertIn("name", cast[0])
        self.assertIn("dialogue_count", cast[0])

    def test_get_daily_breakdown(self):
        """Test daily breakdown generation."""
        script = self.create_test_script()
        days = get_daily_breakdown(script, pages_per_day=3.0)

        self.assertGreater(len(days), 0)

        # Each day should have scenes and locations
        for day in days:
            self.assertIn("scenes", day)
            self.assertIn("locations", day)
            self.assertIn("pages", day)

    def test_compare_characters(self):
        """Test character comparison."""
        script = self.create_test_script()
        comparison = compare_characters(script, "JOHN", "JANE")

        self.assertIn("character_1", comparison)
        self.assertIn("character_2", comparison)
        self.assertIn("shared_scenes", comparison)

    def test_compare_characters_not_found(self):
        """Test character comparison with invalid character."""
        script = self.create_test_script()
        comparison = compare_characters(script, "JOHN", "NONEXISTENT")

        self.assertIn("error", comparison)

    def test_export_analysis_report(self):
        """Test exporting analysis report."""
        script = self.create_test_script()
        analysis = analyze_script(script)
        report = export_analysis_report(script, analysis)

        self.assertIn("Test Script", report)
        self.assertIn("OVERVIEW", report)
        self.assertIn("RECOMMENDATIONS", report)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow."""

    def test_fountain_to_analysis_workflow(self):
        """Test complete workflow from Fountain to analysis."""
        fountain = """Title: Integration Test
Author: Test

INT. OFFICE - DAY

A busy office. People working.

JOHN
(rushes in)
We have a problem!

JANE
What is it?

JOHN
The deadline is tomorrow.

EXT. PARK - NIGHT

The two colleagues sit on a bench.

JANE
We'll figure it out.

JOHN
I hope so.

INT. OFFICE - DAY

The next morning. Empty desks.

JOHN
We did it!

CUT TO:

THE END
"""
        # Parse
        script = parse_fountain(fountain)

        # Verify parsing
        self.assertEqual(script.title, "Integration Test")
        self.assertGreater(len(script.scenes), 0)

        # Generate beat sheet
        beat_sheet = generate_beat_sheet(script, "save_the_cat")
        self.assertGreater(len(beat_sheet.beats), 0)

        # Analyze
        analysis = analyze_script(script)
        self.assertGreater(analysis.total_scenes, 0)

        # Generate report
        report = export_analysis_report(script, analysis)
        self.assertIn("Integration Test", report)


if __name__ == "__main__":
    unittest.main()
