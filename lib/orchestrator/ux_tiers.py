"""
UX Tier System

Implements 4-tier user experience for scene generation:
- Template: One-click, pre-built scenes
- Wizard: Guided Q&A customization
- YAML: Full YAML configuration
- Python API: Programmatic access

Implements REQ-SO-09: UX Tiers.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod

from .types import (
    SceneOutline,
    SceneTemplate,
    SCENE_TEMPLATES,
    get_template,
    list_templates,
    UXTier,
)


class WizardStep(Enum):
    """Wizard step identifiers."""
    SCENE_TYPE = "scene_type"
    STYLE = "style"
    DIMENSIONS = "dimensions"
    LIGHTING = "lighting"
    CAMERA = "camera"
    ASSETS = "assets"
    REVIEW = "review"


@dataclass
class WizardQuestion:
    """
    Question for wizard mode.

    Attributes:
        step: Wizard step this belongs to
        question_id: Unique question identifier
        prompt: Question text
        options: Available options (if choice-based)
        default: Default value
        required: Whether answer is required
        validator: Validation function name
        help_text: Additional help text
    """
    step: str = ""
    question_id: str = ""
    prompt: str = ""
    options: List[str] = field(default_factory=list)
    default: Any = None
    required: bool = True
    validator: str = ""
    help_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step": self.step,
            "question_id": self.question_id,
            "prompt": self.prompt,
            "options": self.options,
            "default": self.default,
            "required": self.required,
            "validator": self.validator,
            "help_text": self.help_text,
        }


@dataclass
class WizardState:
    """
    Current state of wizard session.

    Attributes:
        current_step: Current wizard step
        answers: Collected answers
        valid_steps: Steps completed successfully
        errors: Validation errors
    """
    current_step: str = "scene_type"
    answers: Dict[str, Any] = field(default_factory=dict)
    valid_steps: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_step": self.current_step,
            "answers": self.answers,
            "valid_steps": self.valid_steps,
            "errors": self.errors,
        }


# =============================================================================
# WIZARD QUESTIONS
# =============================================================================

WIZARD_QUESTIONS: Dict[str, WizardQuestion] = {
    # Scene Type Step
    "scene_type": WizardQuestion(
        step="scene_type",
        question_id="scene_type",
        prompt="What type of scene do you want to create?",
        options=["interior", "exterior", "urban", "product", "portrait", "environment"],
        default="interior",
        required=True,
        help_text="This determines the base structure and default elements.",
    ),

    # Style Step
    "style": WizardQuestion(
        step="style",
        question_id="style",
        prompt="What visual style?",
        options=["photorealistic", "stylized", "cartoon", "low_poly", "retro", "sci_fi", "fantasy", "minimalist"],
        default="photorealistic",
        required=True,
        help_text="Style affects materials, lighting, and post-processing.",
    ),

    # Dimensions Step
    "width": WizardQuestion(
        step="dimensions",
        question_id="width",
        prompt="Scene width (meters)?",
        default=20.0,
        validator="positive_float",
        help_text="Scene width in meters.",
    ),
    "height": WizardQuestion(
        step="dimensions",
        question_id="height",
        prompt="Scene height (meters)?",
        default=4.0,
        validator="positive_float",
        help_text="Vertical extent in meters.",
    ),
    "depth": WizardQuestion(
        step="dimensions",
        question_id="depth",
        prompt="Scene depth (meters)?",
        default=20.0,
        validator="positive_float",
        help_text="Scene depth in meters.",
    ),

    # Lighting Step
    "lighting_mood": WizardQuestion(
        step="lighting",
        question_id="lighting_mood",
        prompt="Lighting mood?",
        options=["bright", "neutral", "moody", "dramatic", "soft", "warm", "cool"],
        default="neutral",
        required=True,
    ),
    "time_of_day": WizardQuestion(
        step="lighting",
        question_id="time_of_day",
        prompt="Time of day?",
        options=["dawn", "morning", "noon", "afternoon", "sunset", "dusk", "night", "midnight"],
        default="noon",
        required=True,
    ),
    "use_studio_lights": WizardQuestion(
        step="lighting",
        question_id="use_studio_lights",
        prompt="Use studio lighting?",
        options=["yes", "no"],
        default="no",
        help_text="Studio lights for product/portrait scenes.",
    ),

    # Camera Step
    "focal_length": WizardQuestion(
        step="camera",
        question_id="focal_length",
        prompt="Camera focal length (mm)?",
        default=50.0,
        validator="positive_float",
        help_text="35mm = wide, 50mm = normal, 85mm = portrait, 200mm = telephoto",
    ),
    "framing": WizardQuestion(
        step="camera",
        question_id="framing",
        prompt="Shot framing?",
        options=["close-up", "medium", "wide", "extreme_wide"],
        default="medium",
    ),

    # Assets Step
    "add_furniture": WizardQuestion(
        step="assets",
        question_id="add_furniture",
        prompt="Add furniture?",
        options=["yes", "no"],
        default="yes",
    ),
    "add_props": WizardQuestion(
        step="assets",
        question_id="add_props",
        prompt="Add decorative props?",
        options=["yes", "no"],
        default="yes",
    ),
    "add_characters": WizardQuestion(
        step="assets",
        question_id="add_characters",
        prompt="Add characters/people?",
        options=["yes", "no"],
        default="no",
    ),
}


# =============================================================================
# WIZARD FLOW
# =============================================================================

WIZARD_FLOW: Dict[str, List[str]] = {
    "scene_type": ["style"],
    "style": ["dimensions"],
    "dimensions": ["lighting"],
    "lighting": ["camera"],
    "camera": ["assets"],
    "assets": ["review"],
    "review": [],  # Final step
}


class UXTierHandler(ABC):
    """Abstract base class for UX tier handlers."""

    @abstractmethod
    def create_outline(self, **kwargs) -> SceneOutline:
        """Create scene outline for this tier."""
        pass

    @abstractmethod
    def get_questions(self) -> List[WizardQuestion]:
        """Get questions for this tier (if applicable)."""
        pass


class TemplateHandler(UXTierHandler):
    """
    Template tier - one-click scene generation.

    Usage:
        handler = TemplateHandler()
        outline = handler.create_outline(template_id="portrait_studio")
    """

    def __init__(self):
        """Initialize template handler."""
        self.templates = SCENE_TEMPLATES

    def create_outline(self, template_id: str, **overrides) -> SceneOutline:
        """
        Create outline from template.

        Args:
            template_id: Template identifier
            **overrides: Optional parameter overrides

        Returns:
            SceneOutline from template
        """
        template = get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        return template.create_outline(**overrides)

    def get_questions(self) -> List[WizardQuestion]:
        """Template tier has no questions - just template selection."""
        return []

    def list_templates(self, category: Optional[str] = None) -> List[SceneTemplate]:
        """
        List available templates.

        Args:
            category: Optional category filter

        Returns:
            List of templates
        """
        templates = list(SCENE_TEMPLATES.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

    def get_template_preview(self, template_id: str) -> Dict[str, Any]:
        """
        Get preview information for template.

        Args:
            template_id: Template identifier

        Returns:
            Preview information
        """
        template = get_template(template_id)
        if not template:
            return {"error": f"Template not found: {template_id}"}

        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "scene_type": template.scene_type,
            "preview_image": template.preview_image,
            "tags": template.tags,
        }


class WizardHandler(UXTierHandler):
    """
    Wizard tier - guided Q&A customization.

    Usage:
        handler = WizardHandler()
        state = handler.start()
        while state.current_step != "review":
            question = handler.get_current_question(state)
            answer = get_user_input(question)
            state = handler.process_answer(state, answer)
        outline = handler.create_outline(state)
    """

    def __init__(self):
        """Initialize wizard handler."""
        self.questions = WIZARD_QUESTIONS
        self.flow = WIZARD_FLOW

    def start(self) -> WizardState:
        """
        Start wizard session.

        Returns:
            Initial wizard state
        """
        return WizardState(current_step="scene_type")

    def get_current_question(self, state: WizardState) -> Optional[WizardQuestion]:
        """
        Get current question for state.

        Args:
            state: Current wizard state

        Returns:
            Current question or None if complete
        """
        if state.current_step == "review":
            return None

        # Get first unanswered question for current step
        step_questions = self._get_step_questions(state.current_step)
        for q in step_questions:
            if q.question_id not in state.answers:
                return q

        return None

    def process_answer(
        self,
        state: WizardState,
        question_id: str,
        answer: Any,
    ) -> WizardState:
        """
        Process user answer.

        Args:
            state: Current wizard state
            question_id: Question being answered
            answer: User's answer

        Returns:
            Updated wizard state
        """
        question = self.questions.get(question_id)
        if not question:
            state.errors.append(f"Unknown question: {question_id}")
            return state

        # Validate answer
        validation_error = self._validate_answer(question, answer)
        if validation_error:
            state.errors.append(validation_error)
            return state

        # Store answer
        state.answers[question_id] = answer
        state.errors = []  # Clear errors on success

        # Check if step complete
        step_questions = self._get_step_questions(state.current_step)
        step_complete = all(
            q.question_id in state.answers
            for q in step_questions
        )

        if step_complete:
            state.valid_steps.append(state.current_step)
            # Advance to next step
            next_steps = self.flow.get(state.current_step, [])
            if next_steps:
                state.current_step = next_steps[0]

        return state

    def create_outline(self, state: WizardState, **kwargs) -> SceneOutline:
        """
        Create outline from wizard answers.

        Args:
            state: Completed wizard state
            **kwargs: Additional parameters

        Returns:
            SceneOutline from answers
        """
        answers = state.answers

        # Build outline from answers
        outline = SceneOutline(
            name=answers.get("name", "Wizard Scene"),
            scene_type=answers.get("scene_type", "interior"),
            style=answers.get("style", "photorealistic"),
            description=answers.get("description", "Generated via wizard"),
        )

        # Add dimensions
        if "width" in answers or "height" in answers or "depth" in answers:
            from .types import SceneDimensions
            outline.dimensions = SceneDimensions(
                width=answers.get("width", 20.0),
                height=answers.get("height", 4.0),
                depth=answers.get("depth", 20.0),
            )

        # Add lighting
        if any(k in answers for k in ["lighting_mood", "time_of_day", "use_studio_lights"]):
            from .types import LightingRequirement
            outline.lighting = LightingRequirement(
                mood=answers.get("lighting_mood", "neutral"),
                time_of_day=answers.get("time_of_day", "noon"),
                use_studio_lights=answers.get("use_studio_lights") == "yes",
            )

        # Add camera
        if any(k in answers for k in ["focal_length", "framing"]):
            from .types import CameraRequirement
            outline.camera = CameraRequirement(
                focal_length=answers.get("focal_length", 50.0),
                framing=answers.get("framing", "medium"),
            )

        return outline

    def get_questions(self) -> List[WizardQuestion]:
        """Get all wizard questions."""
        return list(self.questions.values())

    def skip_step(self, state: WizardState, step: str) -> WizardState:
        """
        Skip a wizard step.

        Args:
            state: Current wizard state
            step: Step to skip

        Returns:
            Updated wizard state
        """
        if state.current_step == step:
            state.valid_steps.append(step)
            next_steps = self.flow.get(step, [])
            if next_steps:
                state.current_step = next_steps[0]

        return state

    def go_back(self, state: WizardState) -> WizardState:
        """
        Go back to previous step.

        Args:
            state: Current wizard state

        Returns:
            Updated wizard state
        """
        if state.valid_steps:
            state.current_step = state.valid_steps.pop()
        return state

    def _get_step_questions(self, step: str) -> List[WizardQuestion]:
        """Get all questions for a step."""
        return [q for q in self.questions.values() if q.step == step]

    def _validate_answer(self, question: WizardQuestion, answer: Any) -> Optional[str]:
        """Validate answer against question constraints."""
        # Check options
        if question.options and answer not in question.options:
            return f"Invalid option. Choose from: {', '.join(question.options)}"

        # Check required
        if question.required and answer is None:
            return f"Answer required for: {question.question_id}"

        # Check validators
        if question.validator:
            if question.validator == "positive_float":
                try:
                    val = float(answer)
                    if val <= 0:
                        return "Value must be positive"
                except (TypeError, ValueError):
                    return "Value must be a number"

            elif question.validator == "positive_int":
                try:
                    val = int(answer)
                    if val <= 0:
                        return "Value must be a positive integer"
                except (TypeError, ValueError):
                    return "Value must be an integer"

        return None


class YAMLHandler(UXTierHandler):
    """
    YAML tier - full configuration control.

    Usage:
        handler = YAMLHandler()
        outline = handler.create_outline(yaml_path="scene.yaml")
        # or
        outline = handler.create_outline(yaml_string="...")
    """

    def __init__(self):
        """Initialize YAML handler."""
        from .outline_parser import OutlineParser
        self.parser = OutlineParser()

    def create_outline(
        self,
        yaml_path: Optional[str] = None,
        yaml_string: Optional[str] = None,
        **kwargs,
    ) -> SceneOutline:
        """
        Create outline from YAML.

        Args:
            yaml_path: Path to YAML file
            yaml_string: YAML string content
            **kwargs: Ignored for YAML tier

        Returns:
            Parsed SceneOutline
        """
        if yaml_path:
            result = self.parser.parse_yaml(yaml_path)
        elif yaml_string:
            result = self.parser.parse_json_string(yaml_string)
        else:
            raise ValueError("Either yaml_path or yaml_string required")

        if not result.success:
            raise ValueError(f"YAML parse errors: {result.errors}")

        return result.outline

    def get_questions(self) -> List[WizardQuestion]:
        """YAML tier has no interactive questions."""
        return []

    def validate_yaml(self, yaml_path: str) -> Dict[str, Any]:
        """
        Validate YAML without creating outline.

        Args:
            yaml_path: Path to YAML file

        Returns:
            Validation result
        """
        result = self.parser.parse_yaml(yaml_path)
        return {
            "valid": result.success,
            "errors": result.errors,
            "warnings": result.warnings,
        }


class APIHandler(UXTierHandler):
    """
    Python API tier - programmatic access.

    Usage:
        handler = APIHandler()
        outline = handler.create_outline(
            name="My Scene",
            scene_type="interior",
            style="photorealistic",
            dimensions={"width": 10, "height": 3, "depth": 10},
        )
    """

    def __init__(self):
        """Initialize API handler."""
        pass

    def create_outline(self, **kwargs) -> SceneOutline:
        """
        Create outline from keyword arguments.

        Args:
            **kwargs: Scene outline parameters

        Returns:
            SceneOutline from parameters
        """
        return SceneOutline.from_dict(kwargs)

    def get_questions(self) -> List[WizardQuestion]:
        """API tier has no interactive questions."""
        return []

    def quick_scene(
        self,
        scene_type: str = "interior",
        style: str = "photorealistic",
        **kwargs,
    ) -> SceneOutline:
        """
        Quick scene creation with minimal parameters.

        Args:
            scene_type: Scene type
            style: Visual style
            **kwargs: Additional parameters

        Returns:
            SceneOutline with defaults filled in
        """
        return SceneOutline(
            scene_type=scene_type,
            style=style,
            **kwargs,
        )


class UXManager:
    """
    Manages UX tier selection and routing.

    Usage:
        manager = UXManager()
        handler = manager.get_handler(UXTier.WIZARD)
        outline = handler.create_outline(...)
    """

    def __init__(self):
        """Initialize UX manager."""
        self.handlers: Dict[UXTier, UXTierHandler] = {
            UXTier.TEMPLATE: TemplateHandler(),
            UXTier.WIZARD: WizardHandler(),
            UXTier.YAML: YAMLHandler(),
            UXTier.PYTHON_API: APIHandler(),
        }

    def get_handler(self, tier: UXTier) -> UXTierHandler:
        """
        Get handler for tier.

        Args:
            tier: UX tier

        Returns:
            Handler for tier
        """
        return self.handlers[tier]

    def get_available_tiers(self) -> List[str]:
        """Get list of available tier names."""
        return [t.name for t in UXTier]

    def recommend_tier(self, user_context: Dict[str, Any]) -> UXTier:
        """
        Recommend tier based on user context.

        Args:
            user_context: User context (skill level, use case, etc.)

        Returns:
            Recommended tier
        """
        skill_level = user_context.get("skill_level", "beginner")
        use_case = user_context.get("use_case", "")

        # Beginner users → Template
        if skill_level == "beginner":
            return UXTier.TEMPLATE

        # Quick generation → Template
        if use_case == "quick":
            return UXTier.TEMPLATE

        # Customization needed → Wizard
        if use_case == "custom":
            return UXTier.WIZARD

        # Automation/scripting → API
        if use_case == "automation":
            return UXTier.PYTHON_API

        # Default to wizard for intermediate
        if skill_level == "intermediate":
            return UXTier.WIZARD

        # Advanced users → YAML
        return UXTier.YAML


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_scene_from_template(template_id: str, **overrides) -> SceneOutline:
    """
    Quick scene creation from template.

    Args:
        template_id: Template identifier
        **overrides: Parameter overrides

    Returns:
        SceneOutline from template
    """
    handler = TemplateHandler()
    return handler.create_outline(template_id, **overrides)


def start_wizard() -> WizardState:
    """
    Start wizard session.

    Returns:
        Initial wizard state
    """
    handler = WizardHandler()
    return handler.start()


def create_scene_from_yaml(path: str) -> SceneOutline:
    """
    Create scene from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        Parsed SceneOutline
    """
    handler = YAMLHandler()
    return handler.create_outline(yaml_path=path)


def create_scene_api(**kwargs) -> SceneOutline:
    """
    Create scene via API.

    Args:
        **kwargs: Scene parameters

    Returns:
        SceneOutline from parameters
    """
    handler = APIHandler()
    return handler.create_outline(**kwargs)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "WizardStep",
    "UXTier",
    # Data classes
    "WizardQuestion",
    "WizardState",
    # Handlers
    "UXTierHandler",
    "TemplateHandler",
    "WizardHandler",
    "YAMLHandler",
    "APIHandler",
    "UXManager",
    # Constants
    "WIZARD_QUESTIONS",
    "WIZARD_FLOW",
    # Functions
    "create_scene_from_template",
    "start_wizard",
    "create_scene_from_yaml",
    "create_scene_api",
]
