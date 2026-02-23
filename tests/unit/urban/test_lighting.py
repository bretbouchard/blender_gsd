"""
Tests for Street Lighting System

Tests luminaire specs, pole specs, and lighting placement.
"""

import pytest
from lib.urban.lighting import (
    LuminaireType,
    LightSource,
    PoleMaterial,
    LightDistribution,
    PhotometricSpec,
    LuminaireSpec,
    PoleSpec,
    StreetLightInstance,
    LUMINAIRE_CATALOG,
    POLE_CATALOG,
    LightingPlacer,
    create_lighting_placer,
)


class TestEnums:
    """Tests for enum types."""

    def test_luminaire_type_values(self):
        """Test LuminaireType enum values."""
        assert LuminaireType.COBRA_HEAD.value == "cobra_head"
        assert LuminaireType.DECORATIVE.value == "decorative"
        assert LuminaireType.SHOEBOX.value == "shoebox"
        assert LuminaireType.POST_TOP.value == "post_top"
        assert LuminaireType.HIGH_MAST.value == "high_mast"

    def test_light_source_values(self):
        """Test LightSource enum values."""
        assert LightSource.LED.value == "led"
        assert LightSource.HIGH_PRESSURE_SODIUM.value == "hps"
        assert LightSource.METAL_HALIDE.value == "mh"

    def test_pole_material_values(self):
        """Test PoleMaterial enum values."""
        assert PoleMaterial.STEEL.value == "steel"
        assert PoleMaterial.ALUMINUM.value == "aluminum"
        assert PoleMaterial.CONCRETE.value == "concrete"

    def test_light_distribution_values(self):
        """Test LightDistribution enum values."""
        assert LightDistribution.TYPE_I.value == "type_i"
        assert LightDistribution.TYPE_III.value == "type_iii"
        assert LightDistribution.TYPE_V.value == "type_v"


class TestPhotometricSpec:
    """Tests for PhotometricSpec dataclass."""

    def test_create_default(self):
        """Test creating PhotometricSpec with defaults."""
        spec = PhotometricSpec()
        assert spec.initial_lumens == 10000
        assert spec.color_temperature == 4000
        assert spec.cri == 70
        assert spec.beam_angle == 120.0

    def test_create_with_values(self):
        """Test creating PhotometricSpec with values."""
        spec = PhotometricSpec(
            initial_lumens=20000,
            lumen_maintenance=0.95,
            color_temperature=5000,
            cri=80,
            beam_angle=90.0,
            cutoff_type="semi_cutoff",
            distribution_type="type_v",
        )
        assert spec.initial_lumens == 20000
        assert spec.color_temperature == 5000

    def test_maintained_lumens_property(self):
        """Test maintained lumens calculation."""
        spec = PhotometricSpec(
            initial_lumens=10000,
            lumen_maintenance=0.9,
        )
        assert spec.maintained_lumens == 9000.0

    def test_to_dict(self):
        """Test PhotometricSpec serialization."""
        spec = PhotometricSpec(initial_lumens=15000)
        result = spec.to_dict()
        assert result["initial_lumens"] == 15000


class TestLuminaireSpec:
    """Tests for LuminaireSpec dataclass."""

    def test_create_default(self):
        """Test creating LuminaireSpec with defaults."""
        spec = LuminaireSpec()
        assert spec.luminaire_id == ""
        assert spec.luminaire_type == "cobra_head"
        assert spec.light_source == "led"
        assert spec.wattage == 100

    def test_create_with_values(self):
        """Test creating LuminaireSpec with values."""
        photometrics = PhotometricSpec(initial_lumens=15000)
        spec = LuminaireSpec(
            luminaire_id="LED-COBRA-150W",
            name="LED Cobra Head 150W",
            luminaire_type="cobra_head",
            light_source="led",
            photometrics=photometrics,
            wattage=150,
            height=10.0,
        )
        assert spec.luminaire_id == "LED-COBRA-150W"
        assert spec.wattage == 150
        assert spec.photometrics.initial_lumens == 15000

    def test_to_dict(self):
        """Test LuminaireSpec serialization."""
        spec = LuminaireSpec(luminaire_id="test", name="Test Luminaire")
        result = spec.to_dict()
        assert result["luminaire_id"] == "test"
        assert result["name"] == "Test Luminaire"


class TestPoleSpec:
    """Tests for PoleSpec dataclass."""

    def test_create_default(self):
        """Test creating PoleSpec with defaults."""
        spec = PoleSpec()
        assert spec.pole_id == ""
        assert spec.pole_type == "single"
        assert spec.material == "steel"
        assert spec.height == 9.0

    def test_create_with_values(self):
        """Test creating PoleSpec with values."""
        spec = PoleSpec(
            pole_id="POLE-CUSTOM",
            pole_type="double",
            material="aluminum",
            height=12.0,
            base_diameter=0.35,
            arm_length=2.5,
            color="#333333",
        )
        assert spec.pole_id == "POLE-CUSTOM"
        assert spec.height == 12.0
        assert spec.material == "aluminum"

    def test_to_dict(self):
        """Test PoleSpec serialization."""
        spec = PoleSpec(pole_id="test_pole", height=10.0)
        result = spec.to_dict()
        assert result["pole_id"] == "test_pole"
        assert result["height"] == 10.0


class TestStreetLightInstance:
    """Tests for StreetLightInstance dataclass."""

    def test_create_default(self):
        """Test creating StreetLightInstance with defaults."""
        instance = StreetLightInstance()
        assert instance.instance_id == ""
        assert instance.position == (0.0, 0.0, 0.0)
        assert instance.rotation == 0.0
        assert instance.spacing_from_previous == 30.0

    def test_create_with_values(self):
        """Test creating StreetLightInstance with values."""
        luminaire = LuminaireSpec(luminaire_id="LED-100W")
        pole = PoleSpec(pole_id="POLE-9M")
        instance = StreetLightInstance(
            instance_id="light_01",
            luminaire=luminaire,
            pole=pole,
            position=(100.0, 50.0, 0.0),
            rotation=45.0,
            aim_direction=45.0,
            spacing_from_previous=35.0,
            circuit_id="circuit_A",
        )
        assert instance.instance_id == "light_01"
        assert instance.position == (100.0, 50.0, 0.0)
        assert instance.circuit_id == "circuit_A"

    def test_to_dict(self):
        """Test StreetLightInstance serialization."""
        instance = StreetLightInstance(instance_id="test")
        result = instance.to_dict()
        assert result["instance_id"] == "test"


class TestLuminaireCatalog:
    """Tests for luminaire catalog."""

    def test_catalog_exists(self):
        """Test that LUMINAIRE_CATALOG is populated."""
        assert isinstance(LUMINAIRE_CATALOG, dict)
        assert len(LUMINAIRE_CATALOG) > 0

    def test_led_cobra_100w(self):
        """Test LED Cobra 100W entry."""
        luminaire = LUMINAIRE_CATALOG.get("LED-COBRA-100W")
        assert luminaire is not None
        assert luminaire.wattage == 100
        assert luminaire.photometrics is not None

    def test_led_cobra_150w(self):
        """Test LED Cobra 150W entry."""
        luminaire = LUMINAIRE_CATALOG.get("LED-COBRA-150W")
        assert luminaire is not None
        assert luminaire.wattage == 150

    def test_led_shoebox(self):
        """Test LED Shoebox entry."""
        luminaire = LUMINAIRE_CATALOG.get("LED-SHOEBOX-200W")
        assert luminaire is not None
        assert luminaire.luminaire_type == "shoebox"

    def test_led_post_top(self):
        """Test LED Post Top entry."""
        luminaire = LUMINAIRE_CATALOG.get("LED-POSTTOP-60W")
        assert luminaire is not None
        assert luminaire.luminaire_type == "post_top"

    def test_led_high_mast(self):
        """Test LED High Mast entry."""
        luminaire = LUMINAIRE_CATALOG.get("LED-HIGHMAST-400W")
        assert luminaire is not None
        assert luminaire.luminaire_type == "high_mast"

    def test_hps_legacy(self):
        """Test HPS legacy entry."""
        luminaire = LUMINAIRE_CATALOG.get("HPS-COBRA-150W")
        assert luminaire is not None
        assert luminaire.light_source == "hps"


class TestPoleCatalog:
    """Tests for pole catalog."""

    def test_catalog_exists(self):
        """Test that POLE_CATALOG is populated."""
        assert isinstance(POLE_CATALOG, dict)
        assert len(POLE_CATALOG) > 0

    def test_steel_9m_pole(self):
        """Test steel 9m pole entry."""
        pole = POLE_CATALOG.get("POLE-STEEL-9M")
        assert pole is not None
        assert pole.height == 9.0
        assert pole.material == "steel"

    def test_steel_12m_pole(self):
        """Test steel 12m pole entry."""
        pole = POLE_CATALOG.get("POLE-STEEL-12M")
        assert pole is not None
        assert pole.height == 12.0

    def test_double_pole(self):
        """Test double pole entry."""
        pole = POLE_CATALOG.get("POLE-STEEL-DOUBLE-9M")
        assert pole is not None
        assert pole.pole_type == "double"

    def test_high_mast_pole(self):
        """Test high mast pole entry."""
        pole = POLE_CATALOG.get("POLE-HIGH-MAST-25M")
        assert pole is not None
        assert pole.height == 25.0


class TestLightingPlacer:
    """Tests for LightingPlacer class."""

    def test_init(self):
        """Test LightingPlacer initialization."""
        placer = LightingPlacer()
        assert placer.luminaire_catalog is not None
        assert placer.pole_catalog is not None

    def test_place_along_road_empty(self):
        """Test placing along empty road."""
        placer = LightingPlacer()
        lights = placer.place_along_road([], "collector")
        assert len(lights) == 0

    def test_place_along_road_single_segment(self):
        """Test placing along single segment."""
        placer = LightingPlacer()
        segments = [((0, 0), (100, 0))]
        lights = placer.place_along_road(
            segments,
            "collector",
            offset=2.0,
            road_width=10.0,
        )
        assert len(lights) > 0

    def test_place_along_road_stagger(self):
        """Test placing with stagger option."""
        placer = LightingPlacer()
        segments = [((0, 0), (200, 0))]
        lights = placer.place_along_road(
            segments,
            "arterial",
            stagger=True,
        )
        assert len(lights) > 0

    def test_place_along_road_no_stagger(self):
        """Test placing without stagger."""
        placer = LightingPlacer()
        segments = [((0, 0), (200, 0))]
        lights = placer.place_along_road(
            segments,
            "arterial",
            stagger=False,
        )
        assert len(lights) > 0

    def test_place_at_intersection_4way(self):
        """Test placing at 4-way intersection."""
        placer = LightingPlacer()
        lights = placer.place_at_intersection(
            position=(0, 0, 0),
            intersection_type="4way",
        )
        assert len(lights) == 4

    def test_place_at_intersection_3way(self):
        """Test placing at 3-way intersection."""
        placer = LightingPlacer()
        lights = placer.place_at_intersection(
            position=(0, 0, 0),
            intersection_type="3way",
        )
        assert len(lights) == 3

    def test_place_at_intersection_roundabout(self):
        """Test placing at roundabout."""
        placer = LightingPlacer()
        lights = placer.place_at_intersection(
            position=(0, 0, 0),
            intersection_type="roundabout",
        )
        assert len(lights) > 0

    def test_place_pedestrian_lighting(self):
        """Test placing pedestrian lighting."""
        placer = LightingPlacer()
        segments = [((0, 0), (50, 0))]
        lights = placer.place_pedestrian_lighting(
            segments,
            spacing=15.0,
        )
        assert len(lights) > 0


class TestCreateLightingPlacer:
    """Tests for create_lighting_placer function."""

    def test_create(self):
        """Test creating lighting placer."""
        placer = create_lighting_placer()
        assert isinstance(placer, LightingPlacer)


class TestLightingSpacing:
    """Tests for lighting spacing by road type."""

    def test_highway_spacing(self):
        """Test highway spacing."""
        assert LightingPlacer.ROAD_SPACING["highway"] == 60.0

    def test_arterial_spacing(self):
        """Test arterial spacing."""
        assert LightingPlacer.ROAD_SPACING["arterial"] == 45.0

    def test_collector_spacing(self):
        """Test collector spacing."""
        assert LightingPlacer.ROAD_SPACING["collector"] == 35.0

    def test_local_spacing(self):
        """Test local spacing."""
        assert LightingPlacer.ROAD_SPACING["local"] == 30.0


class TestLightingEdgeCases:
    """Edge case tests for lighting."""

    def test_very_long_road(self):
        """Test very long road segment."""
        placer = LightingPlacer()
        segments = [((0, 0), (1000, 0))]
        lights = placer.place_along_road(segments, "arterial")
        assert len(lights) > 0

    def test_curved_road(self):
        """Test curved road (multiple segments)."""
        placer = LightingPlacer()
        segments = [
            ((0, 0), (50, 0)),
            ((50, 0), (100, 25)),
            ((100, 25), (150, 75)),
        ]
        lights = placer.place_along_road(segments, "collector")
        assert len(lights) > 0
