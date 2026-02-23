"""
Tests for UX Tier System

Tests wizard flow, handlers, and tier management.
"""

import pytest
from unittest.mock import MagicMock, patch
from lib.orchestrator.ux_tiers import (
    WizardStep,
    WizardQuestion,
    WizardState,
    WIZARD_QUESTIONS,
    WIZARD_FLOW,
    TemplateHandler,
    WizardHandler,
    YAMLHandler,
    APIHandler,
    UXManager,
    create_scene_from_template,
    start_wizard,
    create_scene_api,
)


class TestWizardStep:
    """Tests for WizardStep enum."""

    def test_wizard_step_values(self):
        """Test WizardStep enum values."""
        assert WizardStep.SCENE_TYPE.value == "scene_type"
        assert WizardStep.STYLE.value == "style"
        assert WizardStep.DIMENSIONS.value == "dimensions"
        assert WizardStep.LIGHTING.value == "lighting"
        assert WizardStep.CAMERA.value == "camera"
        assert WizardStep.ASSETS.value == "assets"
        assert WizardStep.REVIEW.value == "review"


class TestWizardQuestion:
    """Tests for WizardQuestion dataclass."""

    def test_create_default(self):
        """Test creating WizardQuestion with defaults."""
        q = WizardQuestion()
        assert q.step == ""
        assert q.question_id == ""
        assert q.prompt == ""
        assert q.options == []
        assert q.default is None
        assert q.required is True

    def test_create_with_values(self):
        """Test creating WizardQuestion with values."""
        q = WizardQuestion(
            step="scene_type",
            question_id="scene_type",
            prompt="What type of scene?",
            options=["interior", "exterior"],
            default="interior",
        )
        assert q.step == "scene_type"
        assert q.question_id == "scene_type"
        assert q.prompt == "What type of scene?"
        assert len(q.options) == 2

    def test_to_dict(self):
        """Test WizardQuestion serialization."""
        q = WizardQuestion(
            question_id="test_q",
            prompt="Test?",
            options=["a", "b"],
        )
        result = q.to_dict()
        assert result["question_id"] == "test_q"
        assert result["options"] == ["a", "b"]


class TestWizardState:
    """Tests for WizardState dataclass."""

    def test_create_default(self):
        """Test creating WizardState with defaults."""
        state = WizardState()
        assert state.current_step == "scene_type"
        assert state.answers == {}
        assert state.valid_steps == []
        assert state.errors == []

    def test_create_with_values(self):
        """Test creating WizardState with values."""
        state = WizardState(
            current_step="style",
            answers={"scene_type": "interior"},
            valid_steps=["scene_type"],
        )
        assert state.current_step == "style"
        assert state.answers["scene_type"] == "interior"
        assert "scene_type" in state.valid_steps

    def test_to_dict(self):
        """Test WizardState serialization."""
        state = WizardState(
            current_step="dimensions",
            answers={"scene_type": "urban"},
        )
        result = state.to_dict()
        assert result["current_step"] == "dimensions"
        assert result["answers"]["scene_type"] == "urban"


class TestWizardQuestions:
    """Tests for predefined wizard questions."""

    def test_wizard_questions_exist(self):
        """Test that WIZARD_QUESTIONS is populated."""
        assert isinstance(WIZARD_QUESTIONS, dict)
        assert len(WIZARD_QUESTIONS) > 0

    def test_scene_type_question(self):
        """Test scene type question."""
        q = WIZARD_QUESTIONS.get("scene_type")
        assert q is not None
        assert q.step == "scene_type"
        assert "interior" in q.options
        assert "exterior" in q.options

    def test_style_question(self):
        """Test style question."""
        q = WIZARD_QUESTIONS.get("style")
        assert q is not None
        assert q.step == "style"
        assert "photorealistic" in q.options

    def test_all_questions_have_required_fields(self):
        """Test all questions have required fields."""
        for qid, q in WIZARD_QUESTIONS.items():
            assert q.question_id == qid
            assert q.prompt != ""
            assert q.step != ""


class TestWizardFlow:
    """Tests for wizard flow definition."""

    def test_wizard_flow_exists(self):
        """Test that WIZARD_FLOW is populated."""
        assert isinstance(WIZARD_FLOW, dict)
        assert len(WIZARD_FLOW) > 0

    def test_flow_starts_at_scene_type(self):
        """Test flow starts with scene_type step."""
        assert "scene_type" in WIZARD_FLOW

    def test_flow_ends_at_review(self):
        """Test flow ends at review step."""
        assert WIZARD_FLOW.get("review") == []

    def test_flow_is_connected(self):
        """Test flow is properly connected."""
        # Each step should lead to another (except review)
        for step, next_steps in WIZARD_FLOW.items():
            assert isinstance(next_steps, list)


class TestTemplateHandler:
    """Tests for TemplateHandler class."""

    def test_init(self):
        """Test TemplateHandler initialization."""
        handler = TemplateHandler()
        assert handler.templates is not None

    def test_get_questions(self):
        """Test getting questions (should be empty)."""
        handler = TemplateHandler()
        questions = handler.get_questions()
        assert questions == []

    def test_list_templates(self):
        """Test listing templates."""
        handler = TemplateHandler()
        templates = handler.list_templates()
        assert isinstance(templates, list)

    def test_list_templates_with_category(self):
        """Test listing templates filtered by category."""
        handler = TemplateHandler()
        # This should not raise
        templates = handler.list_templates(category="studio")
        assert isinstance(templates, list)


class TestWizardHandler:
    """Tests for WizardHandler class."""

    def test_init(self):
        """Test WizardHandler initialization."""
        handler = WizardHandler()
        assert handler.questions is not None
        assert handler.flow is not None

    def test_start(self):
        """Test starting wizard."""
        handler = WizardHandler()
        state = handler.start()
        assert state.current_step == "scene_type"
        assert state.answers == {}

    def test_get_current_question(self):
        """Test getting current question."""
        handler = WizardHandler()
        state = handler.start()
        q = handler.get_current_question(state)
        assert q is not None
        assert q.step == "scene_type"

    def test_get_current_question_at_review(self):
        """Test getting question at review step."""
        handler = WizardHandler()
        state = WizardState(current_step="review")
        q = handler.get_current_question(state)
        assert q is None

    def test_process_answer_valid(self):
        """Test processing valid answer."""
        handler = WizardHandler()
        state = handler.start()
        state = handler.process_answer(state, "scene_type", "interior")
        assert state.answers["scene_type"] == "interior"
        assert len(state.errors) == 0

    def test_process_answer_invalid_question(self):
        """Test processing invalid question ID."""
        handler = WizardHandler()
        state = handler.start()
        state = handler.process_answer(state, "invalid_q", "answer")
        assert len(state.errors) > 0

    def test_process_answer_invalid_option(self):
        """Test processing invalid option."""
        handler = WizardHandler()
        state = handler.start()
        # scene_type has specific options
        state = handler.process_answer(state, "scene_type", "invalid_option")
        assert len(state.errors) > 0

    def test_get_questions(self):
        """Test getting all questions."""
        handler = WizardHandler()
        questions = handler.get_questions()
        assert isinstance(questions, list)
        assert len(questions) > 0

    def test_skip_step(self):
        """Test skipping a step."""
        handler = WizardHandler()
        state = handler.start()
        state = handler.skip_step(state, "scene_type")
        assert "scene_type" in state.valid_steps

    def test_go_back(self):
        """Test going back to previous step."""
        handler = WizardHandler()
        state = handler.start()
        state.valid_steps = ["scene_type"]
        state.current_step = "style"
        state = handler.go_back(state)
        assert state.current_step == "scene_type"


class TestYAMLHandler:
    """Tests for YAMLHandler class."""

    def test_init(self):
        """Test YAMLHandler initialization."""
        handler = YAMLHandler()
        assert handler.parser is not None

    def test_get_questions(self):
        """Test getting questions (should be empty)."""
        handler = YAMLHandler()
        questions = handler.get_questions()
        assert questions == []

    def test_create_outline_missing_params(self):
        """Test creating outline without params."""
        handler = YAMLHandler()
        with pytest.raises(ValueError):
            handler.create_outline()


class TestAPIHandler:
    """Tests for APIHandler class."""

    def test_init(self):
        """Test APIHandler initialization."""
        handler = APIHandler()
        # Should not raise

    def test_get_questions(self):
        """Test getting questions (should be empty)."""
        handler = APIHandler()
        questions = handler.get_questions()
        assert questions == []

    def test_create_outline(self):
        """Test creating outline from kwargs."""
        handler = APIHandler()
        outline = handler.create_outline(
            name="Test",
            scene_type="interior",
            style="photorealistic",
        )
        assert outline.name == "Test"
        assert outline.scene_type == "interior"

    def test_quick_scene(self):
        """Test quick scene creation."""
        handler = APIHandler()
        outline = handler.quick_scene(scene_type="urban", style="stylized")
        assert outline.scene_type == "urban"
        assert outline.style == "stylized"


class TestUXManager:
    """Tests for UXManager class."""

    def test_init(self):
        """Test UXManager initialization."""
        manager = UXManager()
        assert len(manager.handlers) == 4

    def test_get_handler_template(self):
        """Test getting template handler."""
        from lib.orchestrator.types import UXTier
        manager = UXManager()
        handler = manager.get_handler(UXTier.TEMPLATE)
        assert isinstance(handler, TemplateHandler)

    def test_get_handler_wizard(self):
        """Test getting wizard handler."""
        from lib.orchestrator.types import UXTier
        manager = UXManager()
        handler = manager.get_handler(UXTier.WIZARD)
        assert isinstance(handler, WizardHandler)

    def test_get_handler_yaml(self):
        """Test getting YAML handler."""
        from lib.orchestrator.types import UXTier
        manager = UXManager()
        handler = manager.get_handler(UXTier.YAML)
        assert isinstance(handler, YAMLHandler)

    def test_get_handler_api(self):
        """Test getting API handler."""
        from lib.orchestrator.types import UXTier
        manager = UXManager()
        handler = manager.get_handler(UXTier.PYTHON_API)
        assert isinstance(handler, APIHandler)

    def test_get_available_tiers(self):
        """Test getting available tiers."""
        manager = UXManager()
        tiers = manager.get_available_tiers()
        assert "TEMPLATE" in tiers
        assert "WIZARD" in tiers
        assert "YAML" in tiers
        assert "PYTHON_API" in tiers

    def test_recommend_tier_beginner(self):
        """Test tier recommendation for beginner."""
        from lib.orchestrator.types import UXTier
        manager = UXManager()
        tier = manager.recommend_tier({"skill_level": "beginner"})
        assert tier == UXTier.TEMPLATE

    def test_recommend_tier_quick(self):
        """Test tier recommendation for quick use case."""
        from lib.orchestrator.types import UXTier
        manager = UXManager()
        tier = manager.recommend_tier({"skill_level": "intermediate", "use_case": "quick"})
        assert tier == UXTier.TEMPLATE

    def test_recommend_tier_custom(self):
        """Test tier recommendation for custom use case."""
        from lib.orchestrator.types import UXTier
        manager = UXManager()
        tier = manager.recommend_tier({"skill_level": "intermediate", "use_case": "custom"})
        assert tier == UXTier.WIZARD

    def test_recommend_tier_automation(self):
        """Test tier recommendation for automation."""
        from lib.orchestrator.types import UXTier
        manager = UXManager()
        tier = manager.recommend_tier({"skill_level": "advanced", "use_case": "automation"})
        assert tier == UXTier.PYTHON_API


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_start_wizard(self):
        """Test start_wizard function."""
        state = start_wizard()
        assert state.current_step == "scene_type"

    def test_create_scene_api(self):
        """Test create_scene_api function."""
        outline = create_scene_api(name="Test", scene_type="interior")
        assert outline.name == "Test"
        assert outline.scene_type == "interior"


class TestWizardValidation:
    """Tests for wizard answer validation."""

    def test_validate_positive_float_valid(self):
        """Test positive float validation with valid value."""
        handler = WizardHandler()
        state = handler.start()
        # width uses positive_float validator
        state = handler.process_answer(state, "width", 10.0)
        assert len(state.errors) == 0

    def test_validate_positive_float_invalid(self):
        """Test positive float validation with invalid value."""
        handler = WizardHandler()
        state = handler.start()
        state = handler.process_answer(state, "width", -5.0)
        assert len(state.errors) > 0

    def test_validate_required_field(self):
        """Test required field validation."""
        handler = WizardHandler()
        state = handler.start()
        # scene_type is required
        state = handler.process_answer(state, "scene_type", None)
        assert len(state.errors) > 0
