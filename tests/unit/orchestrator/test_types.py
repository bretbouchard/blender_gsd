"""
Tests for Orchestrator Types

Tests all data structures and enums in the types module.
"""

import pytest
from lib.orchestrator.types import (
    SceneType,
    SceneStyle,
    LightingMood,
    TimeOfDay,
    WeatherCondition,
    RequirementPriority,
    ApprovalStatus,
    UXTier,
    SceneDimensions,
    AssetRequirement,
    LightingRequirement,
    CameraRequirement,
    SceneOutline,
    AssetSelection,
    GenerationCheckpoint,
    GenerationResult,
    SceneTemplate,
    SCENE_TEMPLATES,
    list_templates,
    get_template,
)


class TestEnums:
    """Tests for enum types."""

    def test_scene_type_values(self):
        """Test SceneType enum values."""
        assert SceneType.INTERIOR.value == "interior"
        assert SceneType.EXTERIOR.value == "exterior"
        assert SceneType.URBAN.value == "urban"
        assert SceneType.PRODUCT.value == "product"
        assert SceneType.PORTRAIT.value == "portrait"
        assert SceneType.ENVIRONMENT.value == "environment"

    def test_scene_style_values(self):
        """Test SceneStyle enum values."""
        assert SceneStyle.PHOTOREALISTIC.value == "photorealistic"
        assert SceneStyle.STYLIZED.value == "stylized"
        assert SceneStyle.CARTOON.value == "cartoon"
        assert SceneStyle.LOW_POLY.value == "low_poly"

    def test_lighting_mood_values(self):
        """Test LightingMood enum values."""
        assert LightingMood.BRIGHT.value == "bright"
        assert LightingMood.MOODY.value == "moody"
        assert LightingMood.DRAMATIC.value == "dramatic"
        assert LightingMood.NEUTRAL.value == "neutral"

    def test_time_of_day_values(self):
        """Test TimeOfDay enum values."""
        assert TimeOfDay.DAWN.value == "dawn"
        assert TimeOfDay.NOON.value == "noon"
        assert TimeOfDay.SUNSET.value == "sunset"
        assert TimeOfDay.NIGHT.value == "night"

    def test_weather_condition_values(self):
        """Test WeatherCondition enum values."""
        assert WeatherCondition.CLEAR.value == "clear"
        assert WeatherCondition.CLOUDY.value == "cloudy"
        assert WeatherCondition.RAIN.value == "rain"

    def test_ux_tier_values(self):
        """Test UXTier enum values."""
        assert UXTier.TEMPLATE.value == 1
        assert UXTier.WIZARD.value == 2
        assert UXTier.YAML.value == 3
        assert UXTier.PYTHON_API.value == 4

    def test_requirement_priority_values(self):
        """Test RequirementPriority enum values."""
        assert RequirementPriority.REQUIRED.value == "required"
        assert RequirementPriority.PREFERRED.value == "preferred"
        assert RequirementPriority.OPTIONAL.value == "optional"

    def test_approval_status_values(self):
        """Test ApprovalStatus enum values."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"


class TestSceneDimensions:
    """Tests for SceneDimensions dataclass."""

    def test_create_default(self):
        """Test creating SceneDimensions with defaults."""
        dims = SceneDimensions()
        assert dims.width == 20.0
        assert dims.height == 4.0
        assert dims.depth == 20.0
        assert dims.unit_scale == 1.0

    def test_create_with_values(self):
        """Test creating SceneDimensions with values."""
        dims = SceneDimensions(width=50.0, height=6.0, depth=40.0, unit_scale=0.5)
        assert dims.width == 50.0
        assert dims.height == 6.0
        assert dims.depth == 40.0
        assert dims.unit_scale == 0.5

    def test_to_dict(self):
        """Test SceneDimensions serialization."""
        dims = SceneDimensions(width=30.0, height=5.0, depth=25.0)
        result = dims.to_dict()
        assert result["width"] == 30.0
        assert result["height"] == 5.0
        assert result["depth"] == 25.0
        assert result["unit_scale"] == 1.0

    def test_volume_property(self):
        """Test volume calculation."""
        dims = SceneDimensions(width=10.0, height=3.0, depth=10.0)
        assert dims.volume == 300.0


class TestAssetRequirement:
    """Tests for AssetRequirement dataclass."""

    def test_create_default(self):
        """Test creating AssetRequirement with defaults."""
        req = AssetRequirement()
        assert req.requirement_id == ""
        assert req.category == "prop"
        assert req.quantity == 1
        assert req.priority == "required"

    def test_create_with_values(self):
        """Test creating AssetRequirement with values."""
        req = AssetRequirement(
            requirement_id="furniture_01",
            category="furniture",
            subcategory="seating",
            description="Modern chair",
            quantity=4,
            priority="preferred",
            style_constraints=["modern", "minimalist"],
            placement_hints=["living_room"],
        )
        assert req.requirement_id == "furniture_01"
        assert req.category == "furniture"
        assert req.subcategory == "seating"
        assert req.quantity == 4
        assert req.priority == "preferred"
        assert len(req.style_constraints) == 2

    def test_to_dict(self):
        """Test AssetRequirement serialization."""
        req = AssetRequirement(
            requirement_id="test_req",
            category="props",
            quantity=10,
        )
        result = req.to_dict()
        assert result["requirement_id"] == "test_req"
        assert result["category"] == "props"
        assert result["quantity"] == 10

    def test_size_constraints_serialization(self):
        """Test size constraints serialization."""
        req = AssetRequirement(
            requirement_id="test",
            size_constraints=(0.5, 2.0),
        )
        result = req.to_dict()
        assert result["size_constraints"] == [0.5, 2.0]


class TestLightingRequirement:
    """Tests for LightingRequirement dataclass."""

    def test_create_default(self):
        """Test creating LightingRequirement with defaults."""
        lighting = LightingRequirement()
        assert lighting.mood == "neutral"
        assert lighting.time_of_day == "noon"
        assert lighting.weather == "clear"
        assert lighting.use_studio_lights is False
        assert lighting.use_natural_light is True

    def test_create_with_values(self):
        """Test creating LightingRequirement with values."""
        lighting = LightingRequirement(
            mood="dramatic",
            time_of_day="sunset",
            weather="cloudy",
            intensity=1.5,
            use_studio_lights=True,
            studio_preset="rembrandt",
            atmospherics=["fog", "haze"],
        )
        assert lighting.mood == "dramatic"
        assert lighting.time_of_day == "sunset"
        assert lighting.weather == "cloudy"
        assert lighting.intensity == 1.5
        assert lighting.use_studio_lights is True
        assert lighting.studio_preset == "rembrandt"
        assert "fog" in lighting.atmospherics

    def test_to_dict(self):
        """Test LightingRequirement serialization."""
        lighting = LightingRequirement(mood="moody", time_of_day="night")
        result = lighting.to_dict()
        assert result["mood"] == "moody"
        assert result["time_of_day"] == "night"


class TestCameraRequirement:
    """Tests for CameraRequirement dataclass."""

    def test_create_default(self):
        """Test creating CameraRequirement with defaults."""
        camera = CameraRequirement()
        assert camera.focal_length == 50.0
        assert camera.sensor_size == (36.0, 24.0)
        assert camera.framing == "medium"
        assert camera.camera_movement == "static"

    def test_create_with_values(self):
        """Test creating CameraRequirement with values."""
        camera = CameraRequirement(
            focal_length=85.0,
            sensor_size=(24.0, 18.0),
            target_subject="character_01",
            framing="close-up",
            camera_movement="orbit",
            look_at_target=(0.0, 0.0, 1.0),
        )
        assert camera.focal_length == 85.0
        assert camera.sensor_size == (24.0, 18.0)
        assert camera.target_subject == "character_01"
        assert camera.framing == "close-up"
        assert camera.look_at_target == (0.0, 0.0, 1.0)

    def test_to_dict(self):
        """Test CameraRequirement serialization."""
        camera = CameraRequirement(focal_length=35.0, framing="wide")
        result = camera.to_dict()
        assert result["focal_length"] == 35.0
        assert result["framing"] == "wide"


class TestSceneOutline:
    """Tests for SceneOutline dataclass."""

    def test_create_default(self):
        """Test creating SceneOutline with defaults."""
        outline = SceneOutline()
        assert outline.name == "Untitled Scene"
        assert outline.scene_type == "interior"
        assert outline.style == "photorealistic"

    def test_create_with_values(self):
        """Test creating SceneOutline with values."""
        outline = SceneOutline(
            name="Test Scene",
            scene_type="urban",
            style="stylized",
            description="A test scene",
        )
        assert outline.name == "Test Scene"
        assert outline.scene_type == "urban"
        assert outline.style == "stylized"
        assert outline.description == "A test scene"

    def test_to_dict(self):
        """Test SceneOutline serialization."""
        outline = SceneOutline(name="My Scene", scene_type="product")
        result = outline.to_dict()
        assert result["name"] == "My Scene"
        assert result["scene_type"] == "product"

    def test_to_json(self):
        """Test JSON serialization."""
        outline = SceneOutline(name="JSON Scene")
        json_str = outline.to_json()
        assert '"name": "JSON Scene"' in json_str

    def test_from_dict(self):
        """Test SceneOutline deserialization."""
        data = {
            "name": "Loaded Scene",
            "scene_type": "exterior",
            "style": "cartoon",
        }
        outline = SceneOutline.from_dict(data)
        assert outline.name == "Loaded Scene"
        assert outline.scene_type == "exterior"
        assert outline.style == "cartoon"

    def test_from_dict_with_dimensions(self):
        """Test deserialization with dimensions."""
        data = {
            "name": "Test",
            "dimensions": {"width": 50.0, "height": 5.0, "depth": 40.0},
        }
        outline = SceneOutline.from_dict(data)
        assert outline.dimensions is not None
        assert outline.dimensions.width == 50.0

    def test_from_dict_with_lighting(self):
        """Test deserialization with lighting."""
        data = {
            "name": "Test",
            "lighting": {"mood": "dramatic", "time_of_day": "sunset"},
        }
        outline = SceneOutline.from_dict(data)
        assert outline.lighting is not None
        assert outline.lighting.mood == "dramatic"

    def test_from_dict_with_camera(self):
        """Test deserialization with camera."""
        data = {
            "name": "Test",
            "camera": {"focal_length": 85.0, "framing": "close-up"},
        }
        outline = SceneOutline.from_dict(data)
        assert outline.camera is not None
        assert outline.camera.focal_length == 85.0

    def test_from_dict_with_asset_requirements(self):
        """Test deserialization with asset requirements."""
        data = {
            "name": "Test",
            "asset_requirements": [
                {"requirement_id": "req_01", "category": "furniture", "quantity": 2}
            ],
        }
        outline = SceneOutline.from_dict(data)
        assert len(outline.asset_requirements) == 1
        assert outline.asset_requirements[0].requirement_id == "req_01"


class TestAssetSelection:
    """Tests for AssetSelection dataclass."""

    def test_create_default(self):
        """Test creating AssetSelection with defaults."""
        selection = AssetSelection()
        assert selection.requirement_id == ""
        assert selection.asset_id == ""
        assert selection.scale_factor == 1.0
        assert selection.position == (0.0, 0.0, 0.0)

    def test_create_with_values(self):
        """Test creating AssetSelection with values."""
        selection = AssetSelection(
            requirement_id="req_01",
            asset_id="chair_modern_01",
            asset_path="/assets/furniture/chairs/chair_modern_01.blend",
            scale_factor=1.2,
            position=(2.0, 3.0, 0.0),
            rotation=(0.0, 0.0, 45.0),
            priority_score=0.95,
        )
        assert selection.requirement_id == "req_01"
        assert selection.asset_id == "chair_modern_01"
        assert selection.scale_factor == 1.2
        assert selection.position == (2.0, 3.0, 0.0)

    def test_to_dict(self):
        """Test AssetSelection serialization."""
        selection = AssetSelection(
            requirement_id="req_02",
            asset_id="table_01",
        )
        result = selection.to_dict()
        assert result["requirement_id"] == "req_02"
        assert result["asset_id"] == "table_01"


class TestGenerationCheckpoint:
    """Tests for GenerationCheckpoint dataclass."""

    def test_create_default(self):
        """Test creating GenerationCheckpoint with defaults."""
        checkpoint = GenerationCheckpoint()
        assert checkpoint.stage == "initialized"
        assert checkpoint.timestamp == ""
        assert checkpoint.data == {}

    def test_create_with_values(self):
        """Test creating GenerationCheckpoint with values."""
        checkpoint = GenerationCheckpoint(
            stage="assets_placed",
            timestamp="2024-01-15T10:30:00",
            data={"assets_placed": 5},
            message="Placed 5 assets",
        )
        assert checkpoint.stage == "assets_placed"
        assert checkpoint.timestamp == "2024-01-15T10:30:00"
        assert checkpoint.data["assets_placed"] == 5

    def test_to_dict(self):
        """Test GenerationCheckpoint serialization."""
        checkpoint = GenerationCheckpoint(stage="complete", message="Done")
        result = checkpoint.to_dict()
        assert result["stage"] == "complete"
        assert result["message"] == "Done"


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_create_default(self):
        """Test creating GenerationResult with defaults."""
        result = GenerationResult()
        assert result.success is False
        assert result.scene_outline is None
        assert result.asset_selections == []
        assert result.validation_errors == []

    def test_create_with_values(self):
        """Test creating GenerationResult with values."""
        outline = SceneOutline(name="Test")
        checkpoint = GenerationCheckpoint(stage="complete")
        result = GenerationResult(
            success=True,
            scene_outline=outline,
            checkpoint=checkpoint,
            blend_path="/output/scene.blend",
            render_path="/output/render.png",
            generation_time=45.5,
        )
        assert result.success is True
        assert result.scene_outline.name == "Test"
        assert result.blend_path == "/output/scene.blend"
        assert result.generation_time == 45.5

    def test_to_dict(self):
        """Test GenerationResult serialization."""
        result = GenerationResult(
            success=True,
            validation_errors=["Warning 1"],
            warnings=["Note 1"],
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["validation_errors"] == ["Warning 1"]


class TestSceneTemplate:
    """Tests for SceneTemplate dataclass."""

    def test_create_default(self):
        """Test creating SceneTemplate with defaults."""
        template = SceneTemplate()
        assert template.template_id == ""
        assert template.name == ""
        assert template.category == "general"
        assert template.tags == []

    def test_create_with_values(self):
        """Test creating SceneTemplate with values."""
        template = SceneTemplate(
            template_id="custom_template",
            name="Custom Template",
            description="A custom template",
            category="studio",
            scene_type="product",
            outline_template={"name": "Custom", "scene_type": "product"},
            tags=["custom", "product"],
        )
        assert template.template_id == "custom_template"
        assert template.category == "studio"
        assert "custom" in template.tags

    def test_to_dict(self):
        """Test SceneTemplate serialization."""
        template = SceneTemplate(
            template_id="test",
            name="Test Template",
        )
        result = template.to_dict()
        assert result["template_id"] == "test"
        assert result["name"] == "Test Template"

    def test_create_outline(self):
        """Test creating outline from template."""
        template = SceneTemplate(
            template_id="test_template",
            name="Test",
            outline_template={
                "name": "Template Scene",
                "scene_type": "interior",
                "style": "photorealistic",
            },
        )
        outline = template.create_outline()
        assert outline.name == "Template Scene"
        assert outline.scene_type == "interior"

    def test_create_outline_with_overrides(self):
        """Test creating outline with overrides."""
        template = SceneTemplate(
            template_id="test_template",
            name="Test",
            outline_template={
                "name": "Template Scene",
                "scene_type": "interior",
                "style": "photorealistic",
            },
        )
        outline = template.create_outline(style="stylized", name="Custom Name")
        assert outline.style == "stylized"
        assert outline.name == "Custom Name"


class TestSceneTemplates:
    """Tests for scene template functions and constants."""

    def test_scene_templates_exist(self):
        """Test that SCENE_TEMPLATES is populated."""
        assert isinstance(SCENE_TEMPLATES, dict)
        assert len(SCENE_TEMPLATES) > 0

    def test_portrait_studio_template(self):
        """Test portrait studio template."""
        template = SCENE_TEMPLATES.get("portrait_studio")
        assert template is not None
        assert template.category == "studio"
        assert template.scene_type == "portrait"

    def test_product_hero_template(self):
        """Test product hero template."""
        template = SCENE_TEMPLATES.get("product_hero")
        assert template is not None
        assert template.category == "studio"
        assert template.scene_type == "product"

    def test_interior_living_template(self):
        """Test interior living template."""
        template = SCENE_TEMPLATES.get("interior_living")
        assert template is not None
        assert template.category == "interior"
        assert template.scene_type == "interior"

    def test_urban_street_template(self):
        """Test urban street template."""
        template = SCENE_TEMPLATES.get("urban_street")
        assert template is not None
        assert template.category == "urban"
        assert template.scene_type == "urban"

    def test_scifi_environment_template(self):
        """Test sci-fi environment template."""
        template = SCENE_TEMPLATES.get("scifi_environment")
        assert template is not None
        assert template.category == "environment"
        assert template.scene_type == "environment"
        assert template.outline_template["style"] == "sci_fi"

    def test_get_template_valid(self):
        """Test getting a valid template."""
        template = get_template("portrait_studio")
        assert template is not None
        assert template.template_id == "portrait_studio"

    def test_get_template_invalid(self):
        """Test getting an invalid template."""
        template = get_template("nonexistent_template")
        assert template is None

    def test_list_templates(self):
        """Test listing templates."""
        templates = list_templates()
        assert isinstance(templates, list)
        assert "portrait_studio" in templates
        assert "product_hero" in templates


class TestSceneOutlineRoundTrip:
    """Tests for complete serialization round trips."""

    def test_json_round_trip(self):
        """Test JSON serialization round trip."""
        import json

        outline = SceneOutline(
            name="Test Scene",
            scene_type="urban",
            style="stylized",
            description="A test scene for round trip",
        )
        outline.dimensions = SceneDimensions(width=50.0, height=10.0, depth=50.0)
        outline.lighting = LightingRequirement(mood="dramatic", time_of_day="sunset")
        outline.camera = CameraRequirement(focal_length=35.0, framing="wide")

        # Serialize
        json_str = outline.to_json()
        data = json.loads(json_str)

        # Deserialize
        loaded_outline = SceneOutline.from_dict(data)

        assert loaded_outline.name == "Test Scene"
        assert loaded_outline.scene_type == "urban"
        assert loaded_outline.style == "stylized"
        assert loaded_outline.description == "A test scene for round trip"
        assert loaded_outline.dimensions.width == 50.0
        assert loaded_outline.lighting.mood == "dramatic"
        assert loaded_outline.camera.focal_length == 35.0
