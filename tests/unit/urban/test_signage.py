"""
Tests for Signage System

Tests sign specs, catalogs, and placement.
"""

import pytest
from lib.urban.signage import (
    SignCategory,
    SignShape,
    SignPurpose,
    SignSpec,
    SignInstance,
    REGULATORY_SIGNS,
    WARNING_SIGNS,
    GUIDE_SIGNS,
    SignLibrary,
    SignPlacer,
    create_sign_library,
)


class TestEnums:
    """Tests for enum types."""

    def test_sign_category_values(self):
        """Test SignCategory enum values."""
        assert SignCategory.REGULATORY.value == "regulatory"
        assert SignCategory.WARNING.value == "warning"
        assert SignCategory.GUIDE.value == "guide"

    def test_sign_shape_values(self):
        """Test SignShape enum values."""
        assert SignShape.CIRCLE.value == "circle"
        assert SignShape.TRIANGLE.value == "triangle"
        assert SignShape.RECTANGLE.value == "rectangle"
        assert SignShape.OCTAGON.value == "octagon"
        assert SignShape.DIAMOND.value == "diamond"

    def test_sign_purpose_values(self):
        """Test SignPurpose enum values."""
        assert SignPurpose.STOP.value == "stop"
        assert SignPurpose.YIELD.value == "yield"
        assert SignPurpose.SPEED_LIMIT.value == "speed_limit"
        assert SignPurpose.STREET_NAME.value == "street_name"


class TestSignSpec:
    """Tests for SignSpec dataclass."""

    def test_create_default(self):
        """Test creating SignSpec with defaults."""
        spec = SignSpec()
        assert spec.sign_id == ""
        assert spec.category == "regulatory"
        assert spec.shape == "rectangle"
        assert spec.width == 0.6

    def test_create_with_values(self):
        """Test creating SignSpec with values."""
        spec = SignSpec(
            sign_id="R1-1",
            name="STOP",
            category="regulatory",
            shape="octagon",
            purpose="stop",
            width=0.75,
            height=0.75,
            background_color="#CC0000",
            text_color="#FFFFFF",
            text_content="STOP",
        )
        assert spec.sign_id == "R1-1"
        assert spec.shape == "octagon"
        assert spec.text_content == "STOP"

    def test_to_dict(self):
        """Test SignSpec serialization."""
        spec = SignSpec(sign_id="test", name="Test Sign")
        result = spec.to_dict()
        assert result["sign_id"] == "test"
        assert result["name"] == "Test Sign"


class TestSignInstance:
    """Tests for SignInstance dataclass."""

    def test_create_default(self):
        """Test creating SignInstance with defaults."""
        instance = SignInstance()
        assert instance.instance_id == ""
        assert instance.position == (0.0, 0.0, 0.0)
        assert instance.rotation == 0.0

    def test_create_with_values(self):
        """Test creating SignInstance with values."""
        spec = SignSpec(sign_id="R1-1", name="STOP")
        instance = SignInstance(
            instance_id="sign_01",
            sign_spec=spec,
            position=(10.0, 5.0, 2.0),
            rotation=180.0,
            direction=180.0,
            pole_type="single",
        )
        assert instance.instance_id == "sign_01"
        assert instance.position == (10.0, 5.0, 2.0)
        assert instance.pole_type == "single"

    def test_to_dict(self):
        """Test SignInstance serialization."""
        instance = SignInstance(instance_id="test")
        result = instance.to_dict()
        assert result["instance_id"] == "test"


class TestRegulatorySigns:
    """Tests for regulatory sign catalog."""

    def test_catalog_exists(self):
        """Test that REGULATORY_SIGNS is populated."""
        assert isinstance(REGULATORY_SIGNS, dict)
        assert len(REGULATORY_SIGNS) > 0

    def test_stop_sign(self):
        """Test STOP sign entry."""
        sign = REGULATORY_SIGNS.get("R1-1")
        assert sign is not None
        assert sign.name == "STOP"
        assert sign.shape == "octagon"

    def test_yield_sign(self):
        """Test YIELD sign entry."""
        sign = REGULATORY_SIGNS.get("R1-2")
        assert sign is not None
        assert sign.name == "YIELD"
        assert sign.shape == "triangle"

    def test_speed_limit_sign(self):
        """Test speed limit sign entry."""
        sign = REGULATORY_SIGNS.get("R2-1")
        assert sign is not None
        assert sign.purpose == "speed_limit"


class TestWarningSigns:
    """Tests for warning sign catalog."""

    def test_catalog_exists(self):
        """Test that WARNING_SIGNS is populated."""
        assert isinstance(WARNING_SIGNS, dict)
        assert len(WARNING_SIGNS) > 0

    def test_curve_sign(self):
        """Test curve warning sign."""
        sign = WARNING_SIGNS.get("W1-1")
        assert sign is not None
        assert sign.shape == "diamond"

    def test_pedestrian_sign(self):
        """Test pedestrian crossing sign."""
        sign = WARNING_SIGNS.get("W11-1")
        assert sign is not None


class TestGuideSigns:
    """Tests for guide sign catalog."""

    def test_catalog_exists(self):
        """Test that GUIDE_SIGNS is populated."""
        assert isinstance(GUIDE_SIGNS, dict)
        assert len(GUIDE_SIGNS) > 0

    def test_street_name_sign(self):
        """Test street name sign entry."""
        sign = GUIDE_SIGNS.get("D3-1")
        assert sign is not None
        assert sign.purpose == "street_name"


class TestSignLibrary:
    """Tests for SignLibrary class."""

    def test_init(self):
        """Test SignLibrary initialization."""
        library = SignLibrary()
        assert library is not None

    def test_get_sign_valid(self):
        """Test getting a valid sign."""
        library = SignLibrary()
        sign = library.get_sign("R1-1")
        assert sign is not None
        assert sign.name == "STOP"

    def test_get_sign_invalid(self):
        """Test getting an invalid sign."""
        library = SignLibrary()
        sign = library.get_sign("INVALID")
        assert sign is None

    def test_get_by_category(self):
        """Test getting signs by category."""
        library = SignLibrary()
        regulatory = library.get_by_category("regulatory")
        assert len(regulatory) > 0
        for sign in regulatory:
            assert sign.category == "regulatory"

    def test_get_by_purpose(self):
        """Test getting signs by purpose."""
        library = SignLibrary()
        stop_signs = library.get_by_purpose("stop")
        assert len(stop_signs) > 0

    def test_create_speed_limit_sign(self):
        """Test creating speed limit sign."""
        library = SignLibrary()
        sign = library.create_speed_limit_sign(50)
        assert sign is not None
        assert sign.purpose == "speed_limit"
        assert "50" in sign.text_content

    def test_create_street_name_sign(self):
        """Test creating street name sign."""
        library = SignLibrary()
        sign = library.create_street_name_sign("Main Street")
        assert sign is not None
        assert sign.purpose == "street_name"


class TestSignPlacer:
    """Tests for SignPlacer class."""

    def test_init(self):
        """Test SignPlacer initialization."""
        placer = SignPlacer()
        assert placer is not None

    def test_place_signs_at_intersection_4way(self):
        """Test placing signs at 4-way intersection."""
        placer = SignPlacer()
        signs = placer.place_signs_at_intersection(
            position=(0, 0, 0),
            intersection_type="intersection_4way",
            road_names=["Main St", "First Ave"],
        )
        assert isinstance(signs, list)

    def test_place_signs_at_intersection_3way(self):
        """Test placing signs at 3-way intersection."""
        placer = SignPlacer()
        signs = placer.place_signs_at_intersection(
            position=(0, 0, 0),
            intersection_type="intersection_3way",
        )
        assert isinstance(signs, list)

    def test_place_speed_limit_signs(self):
        """Test placing speed limit signs."""
        placer = SignPlacer()
        # place_speed_limit_signs expects list of (start, end) tuples
        road_segments = [((0, 0), (100, 0))]
        signs = placer.place_speed_limit_signs(
            road_segments=road_segments,
            speed_limit=50,
        )
        # May have 0 or more signs depending on spacing
        assert isinstance(signs, list)

    def test_place_speed_limit_signs_with_traffic_signal(self):
        """Test placing signs with traffic signal (no stop signs)."""
        placer = SignPlacer()
        signs = placer.place_signs_at_intersection(
            position=(0, 0, 0),
            intersection_type="intersection_4way",
            has_traffic_signal=True,
        )
        # With traffic signal, no stop signs should be placed
        stop_signs = [s for s in signs if s.sign_spec and s.sign_spec.sign_id == "R1-1"]
        assert len(stop_signs) == 0


class TestCreateSignLibrary:
    """Tests for create_sign_library function."""

    def test_create(self):
        """Test creating sign library."""
        library = create_sign_library()
        assert isinstance(library, SignLibrary)


class TestSignageEdgeCases:
    """Edge case tests for signage."""

    def test_custom_speed_limit(self):
        """Test creating custom speed limit."""
        library = SignLibrary()
        for speed in [25, 35, 45, 55, 65, 75]:
            sign = library.create_speed_limit_sign(speed)
            assert sign is not None
            assert str(speed) in sign.text_content

    def test_long_street_name(self):
        """Test creating sign with long street name."""
        library = SignLibrary()
        sign = library.create_street_name_sign(
            "Very Long Street Name That Might Not Fit"
        )
        assert sign is not None

    def test_multiple_intersections(self):
        """Test placing signs at multiple intersections."""
        placer = SignPlacer()
        all_signs = []
        for i in range(5):
            signs = placer.place_signs_at_intersection(
                position=(i * 100, 0, 0),
                intersection_type="intersection_4way",
            )
            all_signs.extend(signs)
        assert len(all_signs) > 0

    def test_roundabout_signs(self):
        """Test placing signs at roundabout."""
        placer = SignPlacer()
        signs = placer.place_signs_at_intersection(
            position=(0, 0, 0),
            intersection_type="roundabout",
        )
        assert isinstance(signs, list)
        # Roundabout should have yield signs
        yield_signs = [s for s in signs if s.sign_spec and s.sign_spec.sign_id == "R1-2"]
        assert len(yield_signs) == 4
