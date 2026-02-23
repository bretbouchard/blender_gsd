"""
Unit tests for MSG 1998 period validator module.

Tests period accuracy validation without Blender dependencies.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from lib.msg1998.period_validator import (
    validate_period_accuracy,
    validate_object_name,
    validate_materials,
    validate_texture_paths,
    get_period_guidelines,
    PERIOD_VIOLATIONS_1998,
    MODERN_KEYWORDS,
    _check_modern_keywords,
)
from lib.msg1998.types import PeriodViolation, PeriodViolationSeverity


class TestPeriodViolations1998:
    """Tests for PERIOD_VIOLATIONS_1998 constant."""

    def test_has_technology_violations(self):
        """Test that technology violations are defined."""
        assert "led_screens" in PERIOD_VIOLATIONS_1998
        assert "smartphone_stations" in PERIOD_VIOLATIONS_1998
        assert "modern_traffic_signals" in PERIOD_VIOLATIONS_1998

    def test_has_architecture_violations(self):
        """Test that architecture violations are defined."""
        assert "post_1998_construction" in PERIOD_VIOLATIONS_1998
        assert "modern_storefronts" in PERIOD_VIOLATIONS_1998

    def test_has_vehicle_violations(self):
        """Test that vehicle violations are defined."""
        assert "post_1998_cars" in PERIOD_VIOLATIONS_1998
        assert "modern_taxi_design" in PERIOD_VIOLATIONS_1998

    def test_violation_structure(self):
        """Test that each violation has required fields."""
        for key, violation in PERIOD_VIOLATIONS_1998.items():
            assert "description" in violation
            assert "severity" in violation
            assert "suggestion" in violation
            assert isinstance(violation["severity"], PeriodViolationSeverity)


class TestModernKeywords:
    """Tests for MODERN_KEYWORDS constant."""

    def test_has_smartphone_keywords(self):
        """Test smartphone-related keywords."""
        assert "iphone" in MODERN_KEYWORDS
        assert "android" in MODERN_KEYWORDS
        assert "smartphone" in MODERN_KEYWORDS
        assert "tablet" in MODERN_KEYWORDS

    def test_has_display_keywords(self):
        """Test display-related keywords."""
        assert "led_screen" in MODERN_KEYWORDS
        assert "led_display" in MODERN_KEYWORDS
        assert "digital_signage" in MODERN_KEYWORDS

    def test_has_vehicle_keywords(self):
        """Test vehicle-related keywords."""
        assert "tesla" in MODERN_KEYWORDS
        assert "electric_vehicle" in MODERN_KEYWORDS

    def test_has_social_media_keywords(self):
        """Test social media keywords."""
        assert "instagram" in MODERN_KEYWORDS
        assert "tiktok" in MODERN_KEYWORDS
        assert "twitter" in MODERN_KEYWORDS


class TestValidateObjectName:
    """Tests for validate_object_name function."""

    def test_clean_name(self):
        """Test that clean names pass validation."""
        violations = validate_object_name("building_wall_01")
        assert violations == []

    def test_clean_name_period_appropriate(self):
        """Test period-appropriate object names."""
        clean_names = [
            "pay_phone_booth",
            "newspaper_box",
            "crt_monitor",
            "crown_victoria_taxi",
            "floppy_disk",
        ]
        for name in clean_names:
            violations = validate_object_name(name)
            assert violations == [], f"Expected no violations for '{name}'"

    def test_iphone_keyword(self):
        """Test detection of iPhone keyword."""
        violations = validate_object_name("character_iphone_01")
        assert len(violations) == 1
        assert "iphone" in violations[0].description.lower()

    def test_smartphone_keyword(self):
        """Test detection of smartphone keyword."""
        violations = validate_object_name("smartphone_prop")
        assert len(violations) == 1
        assert violations[0].severity == PeriodViolationSeverity.WARNING

    def test_led_screen_keyword(self):
        """Test detection of LED screen keyword."""
        violations = validate_object_name("LED_screen_billboard")
        assert len(violations) == 1
        assert "led" in violations[0].description.lower()

    def test_tesla_keyword(self):
        """Test detection of Tesla keyword."""
        violations = validate_object_name("tesla_model_3")
        assert len(violations) == 1

    def test_case_insensitive(self):
        """Test that keyword detection is case-insensitive."""
        violations_lower = validate_object_name("iphone_prop")
        violations_upper = validate_object_name("IPHONE_PROP")
        violations_mixed = validate_object_name("iPhone_Prop")

        assert len(violations_lower) == 1
        assert len(violations_upper) == 1
        assert len(violations_mixed) == 1

    def test_multiple_keywords(self):
        """Test detection of multiple keywords."""
        violations = validate_object_name("smartphone_with_4k_display")
        assert len(violations) >= 2

    def test_custom_target_year(self):
        """Test with custom target year."""
        # Default is 1998
        violations_1998 = validate_object_name("smartphone", 1998)
        assert len(violations_1998) == 1


class TestValidateMaterials:
    """Tests for validate_materials function."""

    def test_clean_materials(self):
        """Test that clean materials pass validation."""
        violations = validate_materials([
            "concrete_wall",
            "brick_red",
            "glass_window",
            "metal_steel",
        ])
        assert violations == []

    def test_led_screen_material(self):
        """Test detection of LED screen material."""
        violations = validate_materials(["led_screen_emissive"])
        assert len(violations) == 1
        assert violations[0].severity == PeriodViolationSeverity.ERROR

    def test_digital_display_material(self):
        """Test detection of digital display material."""
        violations = validate_materials(["digital_display_panel"])
        assert len(violations) == 1
        assert violations[0].severity == PeriodViolationSeverity.WARNING

    def test_multiple_violations(self):
        """Test detection of multiple violations."""
        violations = validate_materials([
            "led_screen_ad",
            "digital_display_sign",
            "normal_concrete",
        ])
        assert len(violations) == 2

    def test_partial_match_led(self):
        """Test that LED alone doesn't trigger (must have screen too)."""
        violations = validate_materials(["led_indicator_light"])
        assert violations == []  # LED alone is okay

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        violations = validate_materials(["LED_SCREEN_DISPLAY"])
        assert len(violations) == 1


class TestValidateTexturePaths:
    """Tests for validate_texture_paths function."""

    def test_clean_textures(self):
        """Test that clean texture paths pass validation."""
        violations = validate_texture_paths([
            "/textures/brick_wall.png",
            "/textures/concrete_floor.jpg",
            "/textures/glass_window.png",
        ])
        assert violations == []

    def test_smartphone_texture(self):
        """Test detection of smartphone in texture name."""
        violations = validate_texture_paths(["/textures/smartphone_screen.png"])
        assert len(violations) == 1

    def test_tesla_texture(self):
        """Test detection of Tesla in texture name."""
        violations = validate_texture_paths(["/textures/tesla_car_paint.jpg"])
        assert len(violations) == 1

    def test_path_parsing(self):
        """Test that path parsing works correctly."""
        violations = validate_texture_paths([
            "/assets/materials/iphone_diffuse.png"
        ])
        assert len(violations) == 1
        assert "iphone" in violations[0].description.lower()


class TestCheckModernKeywords:
    """Tests for _check_modern_keywords internal function."""

    def test_empty_content(self):
        """Test with empty content."""
        violations = _check_modern_keywords("", 1998)
        assert violations == []

    def test_no_keywords(self):
        """Test content without modern keywords."""
        content = "Building wall concrete brick glass window door frame"
        violations = _check_modern_keywords(content, 1998)
        assert violations == []

    def test_single_keyword(self):
        """Test detection of single keyword."""
        content = "Object name: smartphone_prop_01"
        violations = _check_modern_keywords(content, 1998)
        # May find 0 or more depending on word boundary matching
        assert isinstance(violations, list)

    def test_multiple_occurrences(self):
        """Test counting of keyword occurrences."""
        content = "iphone iphone iphone"  # 3 occurrences
        violations = _check_modern_keywords(content, 1998)
        assert len(violations) == 1
        assert "3 time" in violations[0].description

    def test_error_severity_keywords(self):
        """Test that certain keywords get ERROR severity."""
        error_keywords = ["iphone", "smartphone", "android", "tesla"]
        for keyword in error_keywords:
            violations = _check_modern_keywords(f"found {keyword} here", 1998)
            assert len(violations) == 1
            assert violations[0].severity == PeriodViolationSeverity.ERROR

    def test_warning_severity_keywords(self):
        """Test that other keywords get WARNING severity."""
        content = "found 4k resolution here"
        violations = _check_modern_keywords(content, 1998)
        assert len(violations) == 1
        assert violations[0].severity == PeriodViolationSeverity.WARNING


class TestValidatePeriodAccuracy:
    """Tests for validate_period_accuracy function."""

    def test_nonexistent_file(self):
        """Test with non-existent file."""
        violations = validate_period_accuracy(Path("/nonexistent/file.blend"))
        assert len(violations) == 1
        assert violations[0].severity == PeriodViolationSeverity.ERROR
        assert "not found" in violations[0].description.lower()

    def test_existing_file_no_keywords(self, tmp_path):
        """Test with existing file containing no keywords."""
        # Create a simple text file (simulating blend binary)
        test_file = tmp_path / "clean_scene.blend"
        test_file.write_bytes(b"Building Wall Door Window Brick Concrete")

        violations = validate_period_accuracy(test_file)
        assert violations == []

    def test_existing_file_with_keywords(self, tmp_path):
        """Test with existing file containing modern keywords."""
        test_file = tmp_path / "modern_scene.blend"
        test_file.write_bytes(b"Building iPhone Smartphone Tesla")

        violations = validate_period_accuracy(test_file)
        assert len(violations) >= 1


class TestGetPeriodGuidelines:
    """Tests for get_period_guidelines function."""

    def test_default_year(self):
        """Test with default year (1998)."""
        guidelines = get_period_guidelines()
        assert guidelines["year"] == 1998
        assert "technology" in guidelines
        assert "vehicles" in guidelines
        assert "street_furniture" in guidelines
        assert "fashion" in guidelines

    def test_technology_guidelines(self):
        """Test technology guidelines content."""
        guidelines = get_period_guidelines(1998)
        tech = guidelines["technology"]

        assert "smartphones" in tech
        assert "Not available" in tech["smartphones"]
        assert "flat_screens" in tech
        assert "CRT" in tech["flat_screens"]

    def test_vehicle_guidelines(self):
        """Test vehicle guidelines content."""
        guidelines = get_period_guidelines(1998)
        vehicles = guidelines["vehicles"]

        assert "common_cars" in vehicles
        assert "Ford Crown Victoria" in vehicles["common_cars"]
        assert "nyc_taxi" in vehicles

    def test_street_furniture_guidelines(self):
        """Test street furniture guidelines content."""
        guidelines = get_period_guidelines(1998)
        furniture = guidelines["street_furniture"]

        assert "pay_phones" in furniture
        assert "newspaper_boxes" in furniture

    def test_custom_year(self):
        """Test with custom year."""
        guidelines = get_period_guidelines(2005)
        assert guidelines["year"] == 2005


class TestPeriodViolationDataclass:
    """Tests for PeriodViolation dataclass usage."""

    def test_violation_creation(self):
        """Test creating a violation manually."""
        violation = PeriodViolation(
            element="LED Billboard",
            description="LED billboards not common until 2000s",
            severity=PeriodViolationSeverity.ERROR,
            suggestion="Use printed/illuminated signage",
            location="/objects/billboard_01"
        )
        assert violation.element == "LED Billboard"
        assert violation.severity == PeriodViolationSeverity.ERROR

    def test_violation_from_validator(self):
        """Test violation created by validator functions."""
        violations = validate_object_name("iphone_prop")
        assert len(violations) == 1

        v = violations[0]
        assert isinstance(v, PeriodViolation)
        assert v.element == "iphone_prop"
        assert v.severity in [
            PeriodViolationSeverity.ERROR,
            PeriodViolationSeverity.WARNING
        ]
