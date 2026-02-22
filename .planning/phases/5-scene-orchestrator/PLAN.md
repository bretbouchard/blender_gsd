# Phase 5: Scene Orchestrator

**Phase**: 5
**Priority**: P0
**Dependencies**: Phase 4 (Control Surface System), Phase 6 (Cinematic System)
**Est. Duration**: 10-12 days

---

## Goal

Implement the high-level Scene Orchestrator that enables one-command scene generation from outlines with progressive UX (Templates, Wizard, YAML, Python API) and full CLI support for headless execution.

---

## Requirements

| ID | Requirement | Priority | Plan |
|----|-------------|----------|------|
| REQ-SO-01 | Scene Outline Parser (YAML/JSON) | P0 | 5-01 |
| REQ-SO-02 | Requirement Resolver (what assets needed) | P0 | 5-02 |
| REQ-SO-03 | Asset Selection Engine (best match) | P0 | 5-03 |
| REQ-SO-04 | Placement Orchestrator (coordinate all systems) | P0 | 5-04 |
| REQ-SO-05 | Scale Coordinator (maintain proportions) | P0 | 5-04 |
| REQ-SO-06 | Style Consistency (realistic vs stylized) | P0 | 5-05 |
| REQ-SO-07 | Review/Approval Workflow | P1 | 5-06 |
| REQ-SO-08 | Variation Generator (multiple takes) | P1 | 5-06 |
| REQ-SO-09 | UX Tiers (Templates/Wizard/YAML/API) | P0 | 5-07 |
| REQ-SO-10 | CLI Interface | P0 | 5-08 |
| REQ-SO-11 | Headless Execution | P0 | 5-08 |
| REQ-SO-12 | Checkpoint/Resume | P0 | 5-09 |

---

## Plans

### Plan 5-01: Scene Outline Parser

**Deliverable**: `lib/orchestrator/outline_parser.py`

```python
@dataclass
class SceneOutline:
    """Parsed scene outline from YAML/JSON."""
    name: str
    type: str  # interior, exterior, product, portrait, environment
    description: str = ""

    # Scene structure
    rooms: int = 1
    style: str = "modern"  # modern, victorian, scifi, cyberpunk, etc.
    mood: str = "neutral"  # neutral, dramatic, warm, cold, etc.

    # Asset requirements (resolved later)
    required_assets: List[AssetRequirement] = field(default_factory=list)

    # Composition
    camera_setup: Optional[CameraSetup] = None
    lighting_setup: Optional[LightingSetup] = None

    # Metadata
    source_path: str = ""
    created: datetime = field(default_factory=datetime.now)

@dataclass
class AssetRequirement:
    """Required asset specification."""
    category: str  # furniture, prop, character, vehicle, plant, etc.
    name: str = ""
    tags: List[str] = field(default_factory=list)
    count: int = 1
    placement: str = "auto"  # auto, manual, scatter
    position: Optional[Tuple[float, float, float]] = None
    rotation: Optional[Tuple[float, float, float]] = None

@dataclass
class CameraSetup:
    """Camera configuration from outline."""
    preset: str = "default"
    focal_length: float = 50.0
    position: Optional[Tuple[float, float, float]] = None
    target: Optional[Tuple[float, float, float]] = None

@dataclass
class LightingSetup:
    """Lighting configuration from outline."""
    preset: str = "studio"
    intensity: float = 1.0
    temperature: int = 6500
    hdri: Optional[str] = None

def parse_scene_outline(source: str) -> SceneOutline:
    """Parse scene outline from YAML or JSON file."""
    pass

def parse_scene_outline_from_dict(data: Dict) -> SceneOutline:
    """Parse scene outline from dictionary."""
    pass

def validate_outline(outline: SceneOutline) -> ValidationResult:
    """Validate scene outline for completeness."""
    pass

# YAML Example:
"""
scene:
  name: "Living Room"
  type: interior
  description: "Modern living room with city view"

  structure:
    rooms: 1
    style: modern
    mood: warm

  assets:
    - category: furniture
      name: sofa
      tags: [modern, fabric, gray]
      placement: center
    - category: prop
      name: coffee_table
      tags: [wood, rectangular]
    - category: prop
      tags: [plant, indoor]
      count: 3
      placement: scatter

  camera:
    preset: wide_establishing
    focal_length: 24

  lighting:
    preset: natural_daylight
    hdri: apartment_balcony
"""
```

**Tasks**:
1. Create SceneOutline dataclass hierarchy
2. Implement YAML parser with validation
3. Implement JSON parser with validation
4. Implement outline validation
5. Add example outlines to configs/

---

### Plan 5-02: Requirement Resolver

**Deliverable**: `lib/orchestrator/requirement_resolver.py`

```python
@dataclass
class ResolvedRequirement:
    """Resolved asset requirement with all dependencies."""
    original: AssetRequirement
    asset_candidates: List[AssetCandidate]
    selected: Optional[AssetCandidate] = None
    dependencies: List[str] = field(default_factory=list)
    materials_needed: List[str] = field(default_factory=list)

@dataclass
class AssetCandidate:
    """Candidate asset from library."""
    path: str
    name: str
    score: float  # Match score 0-1
    tags_matched: List[str]
    tags_missing: List[str]
    metadata: Dict = field(default_factory=dict)

@dataclass
class ResolvedScene:
    """Fully resolved scene with all requirements."""
    outline: SceneOutline
    resolved_assets: List[ResolvedRequirement]
    missing_assets: List[AssetRequirement]
    total_asset_count: int
    estimated_memory: float  # MB estimate

class RequirementResolver:
    """Resolve asset requirements against library."""

    def __init__(self, asset_library_path: str):
        self.library_path = asset_library_path
        self.index = None

    def load_index(self) -> None:
        """Load or build asset index."""
        pass

    def resolve(self, outline: SceneOutline) -> ResolvedScene:
        """Resolve all requirements in outline."""
        pass

    def resolve_requirement(self, req: AssetRequirement) -> ResolvedRequirement:
        """Resolve single requirement."""
        pass

    def find_candidates(self, req: AssetRequirement) -> List[AssetCandidate]:
        """Find candidate assets matching requirement."""
        pass

    def score_candidate(self, candidate: Dict, req: AssetRequirement) -> float:
        """Score how well candidate matches requirement."""
        pass

def resolve_dependencies(asset_path: str) -> List[str]:
    """Find all dependencies (textures, linked libraries) for asset."""
    pass

def estimate_memory_requirement(resolved: ResolvedScene) -> float:
    """Estimate memory needed to load scene."""
    pass
```

**Tasks**:
1. Implement RequirementResolver class
2. Implement candidate scoring algorithm
3. Implement dependency resolution
4. Implement memory estimation
5. Add caching for resolved requirements

---

### Plan 5-03: Asset Selection Engine

**Deliverable**: `lib/orchestrator/asset_selector.py`

```python
from enum import Enum
from typing import Optional, List, Dict

class SelectionStrategy(Enum):
    """Asset selection strategies."""
    BEST_MATCH = "best_match"      # Highest score
    RANDOM_VARIETY = "random"       # Random from top matches
    DETERMINISTIC = "deterministic" # Same seed = same result
    DIVERSITY = "diversity"         # Maximize visual variety

@dataclass
class SelectionConfig:
    """Asset selection configuration."""
    strategy: SelectionStrategy = SelectionStrategy.BEST_MATCH
    min_score: float = 0.3
    max_candidates: int = 10
    diversity_weight: float = 0.2
    seed: Optional[int] = None

@dataclass
class SelectionResult:
    """Result of asset selection."""
    selected: AssetCandidate
    alternatives: List[AssetCandidate]
    score: float
    strategy_used: SelectionStrategy

class AssetSelector:
    """Select best assets from candidates."""

    def __init__(self, config: SelectionConfig = None):
        self.config = config or SelectionConfig()

    def select(self, candidates: List[AssetCandidate]) -> SelectionResult:
        """Select best asset from candidates."""
        pass

    def select_batch(self,
                     requirements: List[ResolvedRequirement],
                     config: SelectionConfig = None) -> Dict[str, SelectionResult]:
        """Select assets for multiple requirements with diversity."""
        pass

    def calculate_diversity(self, selections: List[SelectionResult]) -> float:
        """Calculate diversity score for a set of selections."""
        pass

def select_for_style(candidates: List[AssetCandidate],
                     style: str) -> List[AssetCandidate]:
    """Filter and rank candidates by style compatibility."""
    pass

def select_for_mood(candidates: List[AssetCandidate],
                    mood: str) -> List[AssetCandidate]:
    """Filter and rank candidates by mood compatibility."""
    pass
```

**Tasks**:
1. Implement AssetSelector class
2. Implement all selection strategies
3. Implement diversity calculation
4. Implement style/mood filtering
5. Add selection result caching

---

### Plan 5-04: Placement Orchestrator & Scale Coordinator

**Deliverable**: `lib/orchestrator/placement.py`

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

class PlacementMode(Enum):
    """Asset placement modes."""
    AUTO = "auto"           # Automatic intelligent placement
    GRID = "grid"           # Grid-based placement
    SCATTER = "scatter"     # Random scatter with rules
    CLUSTER = "cluster"     # Grouped placement
    MANUAL = "manual"       # Use provided positions

@dataclass
class PlacementRule:
    """Rule for automatic placement."""
    category: str
    min_distance: float = 0.5
    max_distance: float = 5.0
    avoid_walls: bool = True
    avoid_windows: bool = True
    floor_aligned: bool = True
    wall_aligned: bool = False
    group_with: List[str] = field(default_factory=list)

@dataclass
class ScaleConfig:
    """Scale coordination configuration."""
    reference_height: float = 1.8  # Human reference in meters
    scale_mode: str = "realistic"  # realistic, stylized, miniature
    uniform_scale: bool = True
    min_scale: float = 0.1
    max_scale: float = 10.0

@dataclass
class PlacedAsset:
    """Asset with placement information."""
    asset_path: str
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    scale: Tuple[float, float, float]
    original_scale: Tuple[float, float, float]

@dataclass
class PlacementResult:
    """Result of scene placement."""
    placed_assets: List[PlacedAsset]
    placement_map: Dict[str, int]  # asset_id -> placed index
    collisions: List[Tuple[int, int]]  # Pairs of colliding assets
    warnings: List[str]

class PlacementOrchestrator:
    """Orchestrate asset placement in scene."""

    def __init__(self,
                 rules: List[PlacementRule] = None,
                 scale_config: ScaleConfig = None):
        self.rules = rules or []
        self.scale_config = scale_config or ScaleConfig()

    def place(self,
              selections: Dict[str, SelectionResult],
              outline: SceneOutline,
              room_bounds: Tuple[float, float, float]) -> PlacementResult:
        """Place all selected assets in scene."""
        pass

    def place_asset(self,
                    asset: AssetCandidate,
                    mode: PlacementMode,
                    bounds: Tuple[float, float, float],
                    existing: List[PlacedAsset] = None) -> PlacedAsset:
        """Place single asset."""
        pass

    def auto_position(self,
                      asset: AssetCandidate,
                      bounds: Tuple[float, float, float],
                      category: str) -> Tuple[float, float, float]:
        """Calculate automatic position for asset."""
        pass

    def check_collisions(self,
                         placed: List[PlacedAsset]) -> List[Tuple[int, int]]:
        """Check for collisions between placed assets."""
        pass

    def resolve_collisions(self,
                           result: PlacementResult) -> PlacementResult:
        """Resolve detected collisions."""
        pass

class ScaleCoordinator:
    """Coordinate scales across all assets."""

    def __init__(self, config: ScaleConfig = None):
        self.config = config or ScaleConfig()

    def calculate_scale(self,
                        asset: AssetCandidate,
                        reference_height: float = None) -> Tuple[float, float, float]:
        """Calculate appropriate scale for asset."""
        pass

    def normalize_scales(self,
                         assets: List[PlacedAsset]) -> List[PlacedAsset]:
        """Normalize scales relative to each other."""
        pass

    def apply_style_scaling(self,
                            assets: List[PlacedAsset],
                            style: str) -> List[PlacedAsset]:
        """Apply style-specific scaling adjustments."""
        pass
```

**Tasks**:
1. Implement PlacementOrchestrator class
2. Implement all placement modes
3. Implement collision detection and resolution
4. Implement ScaleCoordinator class
5. Implement style-based scaling

---

### Plan 5-05: Style Manager

**Deliverable**: `lib/orchestrator/style_manager.py`

```python
from enum import Enum
from dataclasses import dataclass, field

class StyleCategory(Enum):
    """Visual style categories."""
    REALISTIC = "realistic"
    STYLIZED = "stylized"
    CARTOON = "cartoon"
    LOW_POLY = "low_poly"
    RETRO = "retro"
    MINIMALIST = "minimalist"

@dataclass
class StyleProfile:
    """Complete style profile."""
    name: str
    category: StyleCategory

    # Material settings
    roughness_range: Tuple[float, float] = (0.0, 1.0)
    metallic_range: Tuple[float, float] = (0.0, 0.3)
    saturation: float = 1.0
    contrast: float = 1.0

    # Lighting settings
    lighting_softness: float = 0.5
    shadow_intensity: float = 0.5
    ambient_occlusion: float = 0.5

    # Geometry settings
    edge_sharpness: float = 0.5
    detail_level: float = 1.0

    # Color palette
    primary_colors: List[str] = field(default_factory=list)
    accent_colors: List[str] = field(default_factory=list)

    # Overrides
    material_overrides: Dict[str, Dict] = field(default_factory=dict)
    lighting_overrides: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StyleApplication:
    """Result of applying style."""
    modified_materials: List[str]
    modified_lights: List[str]
    modified_objects: List[str]
    warnings: List[str]

class StyleManager:
    """Manage style consistency across scene."""

    # Built-in style profiles
    BUILTIN_STYLES = {
        "realistic": StyleProfile(
            name="realistic",
            category=StyleCategory.REALISTIC,
            roughness_range=(0.1, 0.9),
            metallic_range=(0.0, 0.9),
        ),
        "stylized": StyleProfile(
            name="stylized",
            category=StyleCategory.STYLIZED,
            roughness_range=(0.3, 0.7),
            saturation=1.2,
            edge_sharpness=0.8,
        ),
        "low_poly": StyleProfile(
            name="low_poly",
            category=StyleCategory.LOW_POLY,
            roughness_range=(0.4, 0.6),
            detail_level=0.3,
        ),
        "retro_80s": StyleProfile(
            name="retro_80s",
            category=StyleCategory.RETRO,
            saturation=1.5,
            contrast=1.3,
            primary_colors=["#ff00ff", "#00ffff", "#ffff00"],
        ),
    }

    def __init__(self, custom_profiles_path: str = None):
        self.custom_profiles = {}
        if custom_profiles_path:
            self.load_custom_profiles(custom_profiles_path)

    def load_custom_profiles(self, path: str) -> None:
        """Load custom style profiles from YAML."""
        pass

    def get_profile(self, name: str) -> StyleProfile:
        """Get style profile by name."""
        pass

    def apply_style(self,
                    scene,
                    style: str,
                    selective: bool = False,
                    categories: List[str] = None) -> StyleApplication:
        """Apply style to scene."""
        pass

    def apply_to_material(self, material, profile: StyleProfile) -> bool:
        """Apply style to single material."""
        pass

    def apply_to_light(self, light, profile: StyleProfile) -> bool:
        """Apply style to single light."""
        pass

    def ensure_consistency(self, scene, profile: StyleProfile) -> List[str]:
        """Check and report style inconsistencies."""
        pass

    def create_style_from_scene(self, scene, name: str) -> StyleProfile:
        """Extract style profile from existing scene."""
        pass
```

**Tasks**:
1. Implement StyleManager class
2. Implement all built-in style profiles
3. Implement material style application
4. Implement lighting style application
5. Implement consistency checking
6. Add YAML profile loading

---

### Plan 5-06: Review Workflow & Variation Generator

**Deliverable**: `lib/orchestrator/review.py`, `lib/orchestrator/variation.py`

```python
# review.py

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

class ReviewStatus(Enum):
    """Review status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

@dataclass
class ReviewCheckpoint:
    """Checkpoint for review."""
    id: str
    stage: str
    timestamp: datetime
    scene_path: str
    thumbnail_path: str
    notes: str = ""
    status: ReviewStatus = ReviewStatus.PENDING

@dataclass
class ReviewFeedback:
    """Feedback from review."""
    checkpoint_id: str
    reviewer: str
    timestamp: datetime
    approved: bool
    comments: str = ""
    revision_requests: List[str] = field(default_factory=list)

class ReviewWorkflow:
    """Manage review and approval workflow."""

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoints: List[ReviewCheckpoint] = []

    def create_checkpoint(self,
                          stage: str,
                          scene,
                          notes: str = "") -> ReviewCheckpoint:
        """Create checkpoint for review."""
        pass

    def submit_for_review(self, checkpoint: ReviewCheckpoint) -> str:
        """Submit checkpoint for review."""
        pass

    def approve(self, checkpoint_id: str, comment: str = "") -> None:
        """Approve checkpoint."""
        pass

    def reject(self,
               checkpoint_id: str,
               reason: str,
               revision_requests: List[str] = None) -> None:
        """Reject checkpoint with feedback."""
        pass

    def get_pending_reviews(self) -> List[ReviewCheckpoint]:
        """Get all pending reviews."""
        pass

    def generate_review_report(self, checkpoint_id: str) -> str:
        """Generate HTML review report."""
        pass

# variation.py

@dataclass
class VariationConfig:
    """Configuration for variation generation."""
    count: int = 3
    vary_camera: bool = True
    vary_lighting: bool = True
    vary_placement: bool = False
    vary_materials: bool = False

    camera_angle_range: float = 15.0  # degrees
    camera_distance_range: float = 0.2  # relative
    lighting_angle_range: float = 30.0  # degrees
    lighting_intensity_range: float = 0.3

    seed_base: Optional[int] = None

@dataclass
class Variation:
    """Single scene variation."""
    id: int
    seed: int
    scene_path: str
    thumbnail_path: str
    changes: Dict[str, Any]
    score: float = 0.0

@dataclass
class VariationSet:
    """Set of variations for a scene."""
    original_scene: str
    variations: List[Variation]
    config: VariationConfig
    created: datetime

class VariationGenerator:
    """Generate scene variations."""

    def __init__(self, config: VariationConfig = None):
        self.config = config or VariationConfig()

    def generate(self,
                 scene,
                 config: VariationConfig = None) -> VariationSet:
        """Generate variations of scene."""
        pass

    def vary_camera(self,
                    camera,
                    seed: int) -> Tuple[float, float, float, float, float, float]:
        """Generate camera variation."""
        pass

    def vary_lighting(self,
                      lights: List,
                      seed: int) -> List[Dict]:
        """Generate lighting variations."""
        pass

    def vary_placement(self,
                       assets: List[PlacedAsset],
                       seed: int) -> List[PlacedAsset]:
        """Generate placement variations."""
        pass

    def score_variation(self,
                        variation: Variation,
                        criteria: Dict[str, float] = None) -> float:
        """Score variation quality."""
        pass

    def rank_variations(self,
                        variation_set: VariationSet) -> VariationSet:
        """Rank variations by score."""
        pass
```

**Tasks**:
1. Implement ReviewWorkflow class
2. Implement checkpoint creation with thumbnails
3. Implement review submission and approval
4. Implement VariationGenerator class
5. Implement all variation types
6. Implement variation scoring

---

### Plan 5-07: UX Tiers System

**Deliverable**: `lib/orchestrator/ux_tiers.py`

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

class UXTier(Enum):
    """UX complexity tiers."""
    TEMPLATE = 1      # One-click, pre-built
    WIZARD = 2        # Guided Q&A
    YAML = 3          # Full configuration
    PYTHON_API = 4    # Programmatic

# ============================================================
# TIER 1: Templates
# ============================================================

@dataclass
class SceneTemplate:
    """Pre-built scene template."""
    name: str
    description: str
    category: str  # portrait, product, interior, street, environment
    preview_image: str

    # Pre-configured scene
    outline: SceneOutline
    style: str
    lighting_preset: str
    camera_preset: str

    # Customization options (limited)
    customizable: List[str] = field(default_factory=list)
    presets: Dict[str, Dict] = field(default_factory=dict)

# Built-in templates
BUILTIN_TEMPLATES = {
    "Portrait Studio": SceneTemplate(
        name="Portrait Studio",
        description="Professional portrait lighting setup",
        category="portrait",
        outline=SceneOutline(name="Portrait", type="portrait"),
        style="realistic",
        lighting_preset="portrait_three_point",
        camera_preset="portrait_85mm",
        presets={"rembrandt": {...}, "butterfly": {...}, "split": {...}},
    ),
    "Product Shot": SceneTemplate(
        name="Product Shot",
        description="Clean product photography setup",
        category="product",
        style="realistic",
        lighting_preset="product_hero",
        presets={"hero": {...}, "catalog": {...}, "dramatic": {...}},
    ),
    "Interior Scene": SceneTemplate(
        name="Interior Scene",
        description="Interior room with natural lighting",
        category="interior",
        presets={"modern": {...}, "victorian": {...}, "minimalist": {...}},
    ),
    "Street Scene": SceneTemplate(
        name="Street Scene",
        description="Urban street environment",
        category="street",
        presets={"day": {...}, "night": {...}, "golden_hour": {...}},
    ),
    "Full Environment": SceneTemplate(
        name="Full Environment",
        description="Complete environment with multiple areas",
        category="environment",
        presets={"forest": {...}, "city": {...}, "interior_complex": {...}},
    ),
}

class TemplateEngine:
    """One-click template execution."""

    def list_templates(self, category: str = None) -> List[SceneTemplate]:
        """List available templates."""
        pass

    def get_template(self, name: str) -> SceneTemplate:
        """Get template by name."""
        pass

    def generate_from_template(self,
                               template_name: str,
                               preset: str = None,
                               customizations: Dict = None) -> str:
        """Generate scene from template."""
        pass

# ============================================================
# TIER 2: Wizard
# ============================================================

@dataclass
class WizardQuestion:
    """Wizard question definition."""
    id: str
    question: str
    type: str  # choice, text, number, color, file
    options: List[str] = field(default_factory=list)
    default: Any = None
    required: bool = True
    help_text: str = ""

@dataclass
class WizardStep:
    """Single wizard step."""
    title: str
    description: str
    questions: List[WizardQuestion]

class SceneWizard:
    """Guided Q&A scene creation."""

    WIZARD_STEPS = [
        WizardStep(
            title="Scene Type",
            description="What type of scene are you creating?",
            questions=[
                WizardQuestion(
                    id="scene_type",
                    question="Scene Type",
                    type="choice",
                    options=["portrait", "product", "interior", "exterior", "environment"],
                ),
            ],
        ),
        WizardStep(
            title="Mood & Style",
            description="What's the mood and style?",
            questions=[
                WizardQuestion(
                    id="mood",
                    question="Mood",
                    type="choice",
                    options=["neutral", "dramatic", "warm", "cold", "mysterious", "cheerful"],
                ),
                WizardQuestion(
                    id="style",
                    question="Visual Style",
                    type="choice",
                    options=["realistic", "stylized", "low_poly", "retro"],
                ),
            ],
        ),
        WizardStep(
            title="Assets",
            description="What assets to include?",
            questions=[
                WizardQuestion(
                    id="asset_categories",
                    question="Asset Categories",
                    type="choice",
                    options=["furniture", "props", "plants", "characters", "vehicles"],
                    required=False,
                ),
                WizardQuestion(
                    id="asset_tags",
                    question="Asset Tags (comma-separated)",
                    type="text",
                    required=False,
                ),
            ],
        ),
        WizardStep(
            title="Preview",
            description="Preview your scene",
            questions=[
                WizardQuestion(
                    id="preview",
                    question="Generate Preview?",
                    type="choice",
                    options=["yes", "no"],
                    default="yes",
                ),
            ],
        ),
    ]

    def __init__(self):
        self.responses: Dict[str, Any] = {}
        self.current_step = 0

    def start(self) -> WizardStep:
        """Start wizard, return first step."""
        pass

    def next_step(self, responses: Dict[str, Any]) -> Optional[WizardStep]:
        """Process responses, return next step or None if complete."""
        pass

    def get_outline(self) -> SceneOutline:
        """Generate outline from wizard responses."""
        pass

    def generate(self) -> str:
        """Generate scene from wizard responses."""
        pass

# ============================================================
# TIER 3: YAML Configuration
# ============================================================

# Uses outline_parser.py directly

# Example comprehensive YAML:
"""
scene:
  name: "Modern Office"
  type: interior

  structure:
    rooms: 3
    style: modern
    mood: professional

  assets:
    furniture:
      - name: desk
        tags: [modern, wood]
        count: 4
      - name: office_chair
        tags: [ergonomic, black]
        count: 4
      - name: meeting_table
        placement:
          position: [5, 5, 0]
          rotation: [0, 0, 45]

    props:
      - tags: [computer, monitor]
        count: 4
      - tags: [plant, indoor]
        count: 6
        placement: scatter

    lighting:
      - type: area
        position: [5, 5, 3]
        size: [4, 4]
        intensity: 0.8
      - type: hdri
        name: office_window

  camera:
    preset: establishing
    focal_length: 28
    position: [10, 10, 2]
    target: [5, 5, 1]

  style: realistic

  output:
    resolution: [1920, 1080]
    samples: 128
"""

# ============================================================
# TIER 4: Python API
# ============================================================

class SceneBuilder:
    """Fluent Python API for scene building."""

    def __init__(self, name: str = "Untitled"):
        self.outline = SceneOutline(name=name)

    def type(self, scene_type: str) -> "SceneBuilder":
        """Set scene type."""
        self.outline.type = scene_type
        return self

    def style(self, style: str) -> "SceneBuilder":
        """Set visual style."""
        self.outline.style = style
        return self

    def mood(self, mood: str) -> "SceneBuilder":
        """Set mood."""
        self.outline.mood = mood
        return self

    def rooms(self, count: int) -> "SceneBuilder":
        """Set number of rooms."""
        self.outline.rooms = count
        return self

    def asset(self,
              category: str,
              name: str = None,
              tags: List[str] = None,
              count: int = 1,
              placement: str = "auto") -> "SceneBuilder":
        """Add asset requirement."""
        self.outline.required_assets.append(
            AssetRequirement(
                category=category,
                name=name or "",
                tags=tags or [],
                count=count,
                placement=placement,
            )
        )
        return self

    def camera(self,
               preset: str = None,
               focal_length: float = None,
               position: Tuple[float, float, float] = None,
               target: Tuple[float, float, float] = None) -> "SceneBuilder":
        """Configure camera."""
        self.outline.camera_setup = CameraSetup(
            preset=preset or "default",
            focal_length=focal_length or 50.0,
            position=position,
            target=target,
        )
        return self

    def lighting(self,
                 preset: str = None,
                 hdri: str = None,
                 intensity: float = None) -> "SceneBuilder":
        """Configure lighting."""
        self.outline.lighting_setup = LightingSetup(
            preset=preset or "studio",
            intensity=intensity or 1.0,
            hdri=hdri,
        )
        return self

    def build(self) -> SceneOutline:
        """Build and return outline."""
        return self.outline

    def generate(self,
                 output_path: str = None,
                 preview: bool = False) -> str:
        """Generate scene from builder."""
        pass

# API Usage Example:
"""
from blender_gsd import SceneBuilder

scene = (SceneBuilder("My Scene")
    .type("interior")
    .style("modern")
    .mood("warm")
    .rooms(2)
    .asset("furniture", "sofa", tags=["modern", "fabric"])
    .asset("furniture", "coffee_table", tags=["wood"])
    .asset("prop", tags=["plant"], count=3)
    .camera(preset="wide", focal_length=24)
    .lighting(preset="natural", hdri="apartment")
    .generate("my_scene.blend")
)
"""
```

**Tasks**:
1. Implement TemplateEngine with all templates
2. Implement SceneWizard with all steps
3. Implement SceneBuilder fluent API
4. Create YAML example files
5. Add preview generation for all tiers

---

### Plan 5-08: CLI Interface & Headless Execution

**Deliverable**: `lib/orchestrator/cli.py`

```python
#!/usr/bin/env python3
"""
Blender GSD Scene Orchestrator CLI

Usage:
    blender-gsd scene-generate --template "Portrait Studio" --preset "rembrandt" --output scene.blend
    blender-gsd asset-index --path /Volumes/Storage/3d/ --update
    blender-gsd validate --scene scene.blend --check scale,materials,lighting
    blender-gsd render --scene scene.blend --frames 1-120 --background --json-output
"""

import click
import json
import sys
from typing import Optional, List

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Blender GSD Scene Orchestrator - High-level scene generation."""
    pass

# ============================================================
# Scene Generation Commands
# ============================================================

@cli.command("scene-generate")
@click.option("--template", "-t", help="Template name (Tier 1)")
@click.option("--preset", "-p", help="Template preset")
@click.option("--wizard", "-w", is_flag=True, help="Start wizard (Tier 2)")
@click.option("--yaml", "-y", "yaml_file", type=click.Path(), help="YAML config file (Tier 3)")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output .blend file")
@click.option("--preview", is_flag=True, help="Generate preview image")
@click.option("--style", "-s", help="Visual style override")
@click.option("--seed", type=int, help="Random seed for deterministic output")
def scene_generate(template, preset, wizard, yaml_file, output, preview, style, seed):
    """Generate scene from template, wizard, or YAML."""
    pass

@cli.command("scene-list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def scene_list(category, format):
    """List available templates and presets."""
    pass

# ============================================================
# Asset Management Commands
# ============================================================

@cli.command("asset-index")
@click.option("--path", "-p", type=click.Path(), required=True, help="Asset library path")
@click.option("--update", "-u", is_flag=True, help="Update existing index")
@click.option("--recursive", "-r", is_flag=True, default=True, help="Scan recursively")
@click.option("--output", "-o", type=click.Path(), help="Output index file")
def asset_index(path, update, recursive, output):
    """Build or update asset library index."""
    pass

@cli.command("asset-search")
@click.argument("query")
@click.option("--category", "-c", help="Filter by category")
@click.option("--tags", "-t", help="Filter by tags (comma-separated)")
@click.option("--limit", "-l", type=int, default=10, help="Max results")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def asset_search(query, category, tags, limit, format):
    """Search asset library."""
    pass

@cli.command("asset-info")
@click.argument("asset_path", type=click.Path())
@click.option("--dependencies", "-d", is_flag=True, help="Show dependencies")
def asset_info(asset_path, dependencies):
    """Show asset information."""
    pass

# ============================================================
# Validation Commands
# ============================================================

@cli.command("validate")
@click.argument("scene_path", type=click.Path())
@click.option("--check", "-c", help="Comma-separated checks: scale,materials,lighting,assets,composition")
@click.option("--strict", is_flag=True, help="Fail on warnings")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def validate(scene_path, check, strict, format):
    """Validate scene for issues."""
    pass

@cli.command("validate-outline")
@click.argument("yaml_path", type=click.Path())
@click.option("--resolve", "-r", is_flag=True, help="Resolve and check asset availability")
def validate_outline(yaml_path, resolve):
    """Validate scene outline YAML."""
    pass

# ============================================================
# Rendering Commands
# ============================================================

@cli.command("render")
@click.argument("scene_path", type=click.Path())
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--frames", "-f", help="Frame range (e.g., 1-120 or 1,5,10)")
@click.option("--background", "-b", is_flag=True, help="Run Blender in background")
@click.option("--samples", "-s", type=int, help="Override samples")
@click.option("--resolution", "-r", help="Resolution (e.g., 1920x1080)")
@click.option("--engine", "-e", type=click.Choice(["eevee", "cycles"]), help="Render engine")
@click.option("--json-output", is_flag=True, help="Output progress as JSON")
def render(scene_path, output, frames, background, samples, resolution, engine, json_output):
    """Render scene."""
    pass

# ============================================================
# Variation Commands
# ============================================================

@cli.command("variations")
@click.argument("scene_path", type=click.Path())
@click.option("--count", "-c", type=int, default=3, help="Number of variations")
@click.option("--vary", "-v", multiple=True, help="What to vary: camera,lighting,placement")
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory")
@click.option("--seed", type=int, help="Random seed")
def variations(scene_path, count, vary, output_dir, seed):
    """Generate scene variations."""
    pass

# ============================================================
# Review Commands
# ============================================================

@cli.command("review-create")
@click.argument("scene_path", type=click.Path())
@click.option("--stage", "-s", required=True, help="Review stage name")
@click.option("--notes", "-n", help="Review notes")
def review_create(scene_path, stage, notes):
    """Create review checkpoint."""
    pass

@cli.command("review-list")
@click.option("--pending", is_flag=True, help="Show only pending")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def review_list(pending, format):
    """List review checkpoints."""
    pass

@cli.command("review-approve")
@click.argument("checkpoint_id")
@click.option("--comment", "-c", help="Approval comment")
def review_approve(checkpoint_id, comment):
    """Approve checkpoint."""
    pass

@cli.command("review-reject")
@click.argument("checkpoint_id")
@click.option("--reason", "-r", required=True, help="Rejection reason")
@click.option("--revision", help="Revision request")
def review_reject(checkpoint_id, reason, revision):
    """Reject checkpoint with feedback."""
    pass

# ============================================================
# Utility Commands
# ============================================================

@cli.command("wizard")
def wizard():
    """Start interactive scene wizard."""
    pass

@cli.command("convert")
@click.argument("input_path", type=click.Path())
@click.option("--format", "-f", type=click.Choice(["yaml", "json", "python"]), help="Output format")
@click.option("--output", "-o", type=click.Path(), help="Output file")
def convert(input_path, format, output):
    """Convert between outline formats."""
    pass

@cli.command("info")
def info():
    """Show system information."""
    pass

# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    cli()
```

**Tasks**:
1. Implement all CLI commands
2. Implement JSON output mode for all commands
3. Implement background execution with progress reporting
4. Implement signal handling for graceful shutdown
5. Add shell completion support

---

### Plan 5-09: Checkpoint/Resume System

**Deliverable**: `lib/orchestrator/checkpoint.py`

```python
import os
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from pathlib import Path

@dataclass
class CheckpointData:
    """Checkpoint data structure."""
    id: str
    stage: str
    timestamp: str
    status: str  # pending, completed, failed

    # Scene state
    outline_json: str
    selections_json: str
    placement_json: str

    # Progress
    total_steps: int
    completed_steps: int
    current_step: str

    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Metadata
    seed: Optional[int] = None
    version: str = "1.0"

class Checkpoint:
    """Checkpoint management for scene generation."""

    CHECKPOINT_DIR = ".checkpoints"

    def __init__(self, checkpoint_dir: str = None):
        self.checkpoint_dir = Path(checkpoint_dir or self.CHECKPOINT_DIR)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, stage: str, data: Dict[str, Any]) -> str:
        """Save checkpoint for stage."""
        checkpoint_id = f"{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        checkpoint = CheckpointData(
            id=checkpoint_id,
            stage=stage,
            timestamp=datetime.now().isoformat(),
            status="pending",
            outline_json=json.dumps(data.get("outline", {})),
            selections_json=json.dumps(data.get("selections", {})),
            placement_json=json.dumps(data.get("placement", {})),
            total_steps=data.get("total_steps", 0),
            completed_steps=data.get("completed_steps", 0),
            current_step=data.get("current_step", ""),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            seed=data.get("seed"),
        )

        path = self.checkpoint_dir / f"{checkpoint_id}.json"
        with open(path, 'w') as f:
            json.dump(asdict(checkpoint), f, indent=2)

        return checkpoint_id

    def load(self, checkpoint_id: str) -> Optional[CheckpointData]:
        """Load checkpoint by ID."""
        path = self.checkpoint_dir / f"{checkpoint_id}.json"
        if not path.exists():
            # Try partial match
            matches = list(self.checkpoint_dir.glob(f"{checkpoint_id}*.json"))
            if matches:
                path = matches[0]
            else:
                return None

        with open(path, 'r') as f:
            data = json.load(f)
            return CheckpointData(**data)

    def resume(self, checkpoint_id: str) -> Dict[str, Any]:
        """Resume from checkpoint, return state dict."""
        checkpoint = self.load(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        return {
            "outline": json.loads(checkpoint.outline_json),
            "selections": json.loads(checkpoint.selections_json),
            "placement": json.loads(checkpoint.placement_json),
            "stage": checkpoint.stage,
            "completed_steps": checkpoint.completed_steps,
            "current_step": checkpoint.current_step,
            "errors": checkpoint.errors,
            "warnings": checkpoint.warnings,
            "seed": checkpoint.seed,
        }

    def update(self, checkpoint_id: str, updates: Dict[str, Any]) -> None:
        """Update existing checkpoint."""
        checkpoint = self.load(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        for key, value in updates.items():
            if hasattr(checkpoint, key):
                if key in ("outline", "selections", "placement"):
                    setattr(checkpoint, f"{key}_json", json.dumps(value))
                else:
                    setattr(checkpoint, key, value)

        path = self.checkpoint_dir / f"{checkpoint_id}.json"
        with open(path, 'w') as f:
            json.dump(asdict(checkpoint), f, indent=2)

    def complete(self, checkpoint_id: str) -> None:
        """Mark checkpoint as completed."""
        self.update(checkpoint_id, {"status": "completed"})

    def fail(self, checkpoint_id: str, error: str) -> None:
        """Mark checkpoint as failed with error."""
        checkpoint = self.load(checkpoint_id)
        if checkpoint:
            errors = checkpoint.errors + [error]
            self.update(checkpoint_id, {"status": "failed", "errors": errors})

    def list(self,
             stage: str = None,
             status: str = None) -> List[CheckpointData]:
        """List checkpoints, optionally filtered."""
        checkpoints = []
        for path in self.checkpoint_dir.glob("*.json"):
            with open(path, 'r') as f:
                data = json.load(f)
                checkpoint = CheckpointData(**data)
                if stage and checkpoint.stage != stage:
                    continue
                if status and checkpoint.status != status:
                    continue
                checkpoints.append(checkpoint)
        return sorted(checkpoints, key=lambda c: c.timestamp, reverse=True)

    def delete(self, checkpoint_id: str) -> bool:
        """Delete checkpoint."""
        path = self.checkpoint_dir / f"{checkpoint_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def cleanup(self, keep_last: int = 10) -> int:
        """Clean up old checkpoints, keep last N."""
        checkpoints = self.list()
        deleted = 0
        for checkpoint in checkpoints[keep_last:]:
            self.delete(checkpoint.id)
            deleted += 1
        return deleted

class ResumableGenerator:
    """Scene generator with checkpoint/resume support."""

    STAGES = [
        "parse_outline",
        "resolve_requirements",
        "select_assets",
        "place_assets",
        "apply_style",
        "setup_lighting",
        "setup_camera",
        "finalize",
    ]

    def __init__(self, checkpoint: Checkpoint = None):
        self.checkpoint = checkpoint or Checkpoint()
        self.state: Dict[str, Any] = {}
        self.current_checkpoint_id: Optional[str] = None

    def generate(self,
                 outline: SceneOutline,
                 resume_from: str = None,
                 checkpoint_interval: int = 1) -> str:
        """Generate scene with checkpointing."""
        if resume_from:
            self.state = self.checkpoint.resume(resume_from)
            self.current_checkpoint_id = resume_from
            start_stage = self.state.get("stage", self.STAGES[0])
            start_index = self.STAGES.index(start_stage)
        else:
            self.state = {
                "outline": outline,
                "total_steps": len(self.STAGES),
                "completed_steps": 0,
                "current_step": "",
                "errors": [],
                "warnings": [],
            }
            start_index = 0

        for i, stage in enumerate(self.STAGES[start_index:], start_index):
            self.state["current_step"] = stage
            self._save_checkpoint(stage)

            try:
                result = self._execute_stage(stage)
                self.state[stage] = result
                self.state["completed_steps"] = i + 1

                if (i + 1) % checkpoint_interval == 0:
                    self._save_checkpoint(stage)

            except Exception as e:
                self.checkpoint.fail(self.current_checkpoint_id, str(e))
                raise

        self.checkpoint.complete(self.current_checkpoint_id)
        return self.state.get("output_path", "")

    def _execute_stage(self, stage: str) -> Any:
        """Execute single generation stage."""
        # Dispatch to stage handlers
        handlers = {
            "parse_outline": self._stage_parse_outline,
            "resolve_requirements": self._stage_resolve_requirements,
            "select_assets": self._stage_select_assets,
            "place_assets": self._stage_place_assets,
            "apply_style": self._stage_apply_style,
            "setup_lighting": self._stage_setup_lighting,
            "setup_camera": self._stage_setup_camera,
            "finalize": self._stage_finalize,
        }
        return handlers[stage]()

    def _save_checkpoint(self, stage: str) -> None:
        """Save current state as checkpoint."""
        self.current_checkpoint_id = self.checkpoint.save(stage, self.state)

    # Stage handlers (stubs - implement in full version)
    def _stage_parse_outline(self) -> Dict:
        return {}

    def _stage_resolve_requirements(self) -> Dict:
        return {}

    def _stage_select_assets(self) -> Dict:
        return {}

    def _stage_place_assets(self) -> Dict:
        return {}

    def _stage_apply_style(self) -> Dict:
        return {}

    def _stage_setup_lighting(self) -> Dict:
        return {}

    def _stage_setup_camera(self) -> Dict:
        return {}

    def _stage_finalize(self) -> str:
        return ""
```

**Tasks**:
1. Implement Checkpoint class with all methods
2. Implement ResumableGenerator class
3. Implement all stage handlers
4. Add checkpoint cleanup utilities
5. Add CLI integration for resume

---

## Acceptance Criteria

- [ ] Scene outlines parse from YAML and JSON
- [ ] Requirements resolve against asset library
- [ ] Assets selected with scoring and diversity
- [ ] Placement works for all modes (auto, scatter, grid)
- [ ] Scales coordinated across assets
- [ ] Style consistency maintained
- [ ] Review workflow functional
- [ ] Variations generated correctly
- [ ] All 4 UX tiers work
- [ ] CLI commands functional
- [ ] Headless execution works
- [ ] Checkpoint/resume works

---

## Files

```
lib/orchestrator/
├── __init__.py              # Package exports
├── outline_parser.py        # REQ-SO-01
├── requirement_resolver.py  # REQ-SO-02
├── asset_selector.py        # REQ-SO-03
├── placement.py             # REQ-SO-04, REQ-SO-05
├── style_manager.py         # REQ-SO-06
├── review.py                # REQ-SO-07
├── variation.py             # REQ-SO-08
├── ux_tiers.py              # REQ-SO-09
├── cli.py                   # REQ-SO-10, REQ-SO-11
└── checkpoint.py            # REQ-SO-12

configs/orchestrator/
├── templates/
│   ├── portrait_studio.yaml
│   ├── product_shot.yaml
│   ├── interior_scene.yaml
│   ├── street_scene.yaml
│   └── full_environment.yaml
├── styles/
│   ├── realistic.yaml
│   ├── stylized.yaml
│   ├── low_poly.yaml
│   └── retro_80s.yaml
├── placement_rules.yaml
├── selection_strategies.yaml
└── wizard_steps.yaml

.checkpoints/                # Checkpoint storage (gitignored)
```

---

## Usage Examples

### Tier 1: Template
```bash
blender-gsd scene-generate --template "Portrait Studio" --preset "rembrandt" --output portrait.blend
```

### Tier 2: Wizard
```bash
blender-gsd wizard
# Interactive Q&A follows
```

### Tier 3: YAML
```bash
blender-gsd scene-generate --yaml my_scene.yaml --output scene.blend
```

### Tier 4: Python API
```python
from blender_gsd import SceneBuilder

scene = (SceneBuilder("My Scene")
    .type("interior")
    .style("modern")
    .asset("furniture", "sofa", tags=["modern"])
    .camera(focal_length=24)
    .generate("scene.blend")
)
```

### Headless Render
```bash
blender-gsd render --scene scene.blend --frames 1-120 --background --json-output
```

### Resume from Checkpoint
```bash
blender-gsd scene-generate --yaml scene.yaml --resume parse_outline_20260221_143052
```

---

## Dependencies

| Requirement | Depends On |
|-------------|------------|
| REQ-SO-01 (Parser) | None |
| REQ-SO-02 (Resolver) | REQ-SO-01, Asset Library |
| REQ-SO-03 (Selector) | REQ-SO-02 |
| REQ-SO-04 (Placement) | REQ-SO-03, Control Surface System |
| REQ-SO-05 (Scale) | REQ-SO-04 |
| REQ-SO-06 (Style) | Cinematic System (Phase 6) |
| REQ-SO-07 (Review) | REQ-SO-04 |
| REQ-SO-08 (Variation) | REQ-SO-04, REQ-SO-05, REQ-SO-06 |
| REQ-SO-09 (UX Tiers) | REQ-SO-01 through REQ-SO-08 |
| REQ-SO-10 (CLI) | REQ-SO-09 |
| REQ-SO-11 (Headless) | REQ-SO-10 |
| REQ-SO-12 (Checkpoint) | REQ-SO-09 |
