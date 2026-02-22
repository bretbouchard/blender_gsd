---
phase: 8-quality-review
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - lib/review/__init__.py
  - lib/review/validation.py
  - lib/review/comparison.py
  - lib/review/checklists.py
  - lib/review/reports.py
  - lib/review/workflow.py
  - lib/compositing/__init__.py
  - lib/compositing/cryptomatte.py
  - lib/compositing/multi_pass.py
  - lib/compositing/post_process.py
  - configs/review/validation_rules.yaml
  - configs/review/checklist_templates.yaml
  - configs/compositing/cryptomatte_presets.yaml
  - configs/compositing/multi_pass_presets.yaml
autonomous: true
must_haves:
  truths:
    - "Automated validation detects scale, material, and lighting issues"
    - "Visual comparison shows before/after and reference alignment"
    - "Checklists verify scene completion requirements"
    - "Reports generate HTML and PDF outputs"
    - "Approval workflow tracks pending/approved/revision states"
    - "Version history preserves all iterations"
    - "Cryptomatte passes enable object/material isolation"
    - "Multi-pass pipeline produces compositable EXR layers"
    - "Post-processing chain applies final color corrections"
  artifacts:
    - path: "lib/review/validation.py"
      provides: "Automated scene validation"
      exports: ["validate_scene", "ValidationResult", "ValidationConfig"]
    - path: "lib/review/comparison.py"
      provides: "Visual comparison tools"
      exports: ["compare_renders", "ComparisonResult", "ComparisonConfig"]
    - path: "lib/review/checklists.py"
      provides: "Completion verification"
      exports: ["ChecklistManager", "ChecklistItem", "verify_checklist"]
    - path: "lib/review/reports.py"
      provides: "Report generation"
      exports: ["generate_report", "ReportConfig", "ReportFormat"]
    - path: "lib/review/workflow.py"
      provides: "Approval workflow"
      exports: ["ApprovalWorkflow", "ReviewState", "VersionHistory"]
    - path: "lib/compositing/cryptomatte.py"
      provides: "Cryptomatte configuration and manifest management"
      exports: ["CryptomatteConfig", "configure_cryptomatte", "CryptomatteLayerConfig"]
    - path: "lib/compositing/multi_pass.py"
      provides: "Multi-pass render pipeline"
      exports: ["MultiPassConfig", "ViewLayerConfig", "setup_multi_pass"]
    - path: "lib/compositing/post_process.py"
      provides: "Post-processing chain"
      exports: ["PostProcessChain", "PostProcessConfig", "apply_post_process"]
  key_links:
    - from: "lib/review/validation.py"
      to: "lib/cinematic/render.py"
      via: "get_render_metadata"
      pattern: "get_render_metadata"
    - from: "lib/review/comparison.py"
      to: "lib/vfx/color_correction.py"
      via: "color comparison functions"
      pattern: "apply_color_correction"
    - from: "lib/compositing/cryptomatte.py"
      to: "lib/cinematic/render.py"
      via: "setup_cryptomatte"
      pattern: "setup_cryptomatte"
    - from: "lib/compositing/multi_pass.py"
      to: "lib/cinematic/render.py"
      via: "configure_render_passes"
      pattern: "configure_render_passes"
---

<objective>
Quality & Review System for the Scene Generation System.

Purpose: Provide automated validation, visual comparison, approval workflows, and professional compositing pipeline for production rendering.

Output: Complete quality assurance system with cryptomatte integration, multi-pass rendering, and post-processing capabilities.
</objective>

<execution_context>
@/Users/bretbouchard/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bretbouchard/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md

# Existing modules for integration
@lib/cinematic/render.py
@lib/vfx/__init__.py
@lib/vfx/cryptomatte.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create Review System Foundation</name>
  <files>
    - lib/review/__init__.py
    - lib/review/validation.py
    - lib/review/comparison.py
    - configs/review/validation_rules.yaml
  </files>
  <action>
Create the review package foundation with validation and comparison modules.

1. Create `lib/review/__init__.py`:
   - Package docstring referencing REQ-QA-01 through REQ-QA-06
   - Version 0.1.0
   - Re-exports from all modules

2. Create `lib/review/validation.py` with:
   - `ValidationRule` dataclass: name, category, severity, check_function, threshold, description
   - `ValidationResult` dataclass: rule_name, passed, actual_value, expected_value, message, severity
   - `ValidationConfig` dataclass: rules (List[ValidationRule]), fail_on_error, generate_report
   - `ValidationCategory` enum: SCALE, MATERIAL, LIGHTING, GEOMETRY, COMPOSITION, OUTPUT
   - `ValidationSeverity` enum: INFO, WARNING, ERROR, CRITICAL
   - `validate_scene()` function: runs all validation rules against current scene
   - `validate_scale()`: check object dimensions within expected ranges (uses bounding box analysis)
   - `validate_materials()`: verify all objects have materials, check for missing textures
   - `validate_lighting()`: check light count, intensity ranges, shadow coverage
   - `validate_geometry()`: check for non-manifold meshes, degenerate faces, UV coverage
   - `validate_composition()`: check frame composition using rule of thirds, safe areas
   - `validate_output()`: verify render settings, output paths, file formats
   - All functions should work without bpy when possible for unit testing

3. Create `lib/review/comparison.py` with:
   - `ComparisonConfig` dataclass: mode (side_by_side, overlay, difference), tolerance, highlight_differences
   - `ComparisonResult` dataclass: similarity_score, difference_mask, differences (List[DifferenceRegion])
   - `DifferenceRegion` dataclass: bounds, type (color, geometry, missing), severity
   - `ComparisonMode` enum: SIDE_BY_SIDE, OVERLAY, DIFFERENCE, A_B_SPLIT
   - `compare_renders()`: compare two render outputs (paths or image data)
   - `compare_with_reference()`: compare current render against reference image
   - `generate_comparison_image()`: create visual comparison output
   - `calculate_ssim()`: structural similarity index calculation (simple implementation)
   - `calculate_psnr()`: peak signal-to-noise ratio calculation
   - Handle cases where images differ in size by resizing to match

4. Create `configs/review/validation_rules.yaml` with:
   - Default validation rule presets
   - Categories: scale_rules, material_rules, lighting_rules, geometry_rules, composition_rules, output_rules
   - Each rule has: name, category, threshold, description, severity
   - Example rules:
     - scale_within_bounds: objects 0.1m-10m
     - all_materials_assigned: no unassigned slots
     - light_intensity_range: 10-1000W for key lights
     - no_non_manifold: all meshes manifold
     - output_format_valid: PNG/EXR/JPEG

Reference existing patterns from lib/cinematic/types.py for dataclass style.
Reference lib/vfx/color_correction.py for color comparison utilities.
  </action>
  <verify>
    - pytest tests/unit/test_review_validation.py passes
    - pytest tests/unit/test_review_comparison.py passes
    - All imports resolve: from lib.review import ValidationResult, compare_renders
  </verify>
  <done>
    - lib/review/__init__.py exports all public types
    - validate_scene() returns List[ValidationResult]
    - compare_renders() returns ComparisonResult with similarity_score
    - validation_rules.yaml loads correctly with 6+ categories
  </done>
</task>

<task type="auto">
  <name>Task 2: Create Checklists and Reports</name>
  <files>
    - lib/review/checklists.py
    - lib/review/reports.py
    - configs/review/checklist_templates.yaml
  </files>
  <action>
Create checklist system and report generation modules.

1. Create `lib/review/checklists.py` with:
   - `ChecklistItem` dataclass: id, name, description, category, required, completed, notes, verified_by
   - `ChecklistCategory` enum: PRE_RENDER, POST_RENDER, QUALITY, DELIVERY, DOCUMENTATION
   - `Checklist` dataclass: name, version, items (List[ChecklistItem]), created_at, updated_at
   - `ChecklistTemplate` dataclass: name, description, categories (Dict[str, List[str]]), default_items
   - `ChecklistManager` class:
     - `__init__(self, template_path: Optional[str] = None)`
     - `create_checklist(template_name: str, overrides: Optional[Dict] = None) -> Checklist`
     - `load_checklist(path: str) -> Checklist`
     - `save_checklist(checklist: Checklist, path: str) -> bool`
     - `verify_checklist(checklist: Checklist, auto_verify: bool = True) -> List[ChecklistItem]`
     - `get_completion_percentage(checklist: Checklist) -> float`
     - `get_missing_items(checklist: Checklist) -> List[ChecklistItem]`
     - `mark_complete(item_id: str, verified_by: str = "system") -> bool`
   - `verify_render_checklist()`: automatically verify render-related items
   - `verify_quality_checklist()`: automatically verify quality-related items using validation results
   - Use JSON for checklist serialization (human-readable, easy to edit)

2. Create `lib/review/reports.py` with:
   - `ReportFormat` enum: HTML, PDF, JSON, MARKDOWN
   - `ReportSection` dataclass: title, content (str or List), subsections, collapsible
   - `ReportConfig` dataclass: title, format, include_thumbnails, include_metadata, sections, output_path
   - `ReportData` dataclass: validation_results, comparison_results, checklist, metadata, timestamp
   - `generate_report(data: ReportData, config: ReportConfig) -> str`:
     - Returns path to generated report
     - Handles HTML, PDF (via HTML to PDF), JSON, Markdown formats
   - `generate_html_report(data: ReportData, config: ReportConfig) -> str`:
     - Creates styled HTML report with embedded images (base64)
     - Includes validation summary, comparison images, checklist status
     - Responsive design with dark theme (match tracking-ui style)
     - Sections: Summary, Validation Results, Comparisons, Checklist, Metadata
   - `generate_pdf_report(data: ReportData, config: ReportConfig) -> str`:
     - Uses weasyprint or pdfkit for HTML to PDF conversion
     - Falls back to HTML if PDF generation unavailable
     - Print-optimized CSS
   - `generate_json_report(data: ReportData, config: ReportConfig) -> str`:
     - Machine-readable format for automation
   - `generate_markdown_report(data: ReportData, config: ReportConfig) -> str`:
     - For documentation integration
   - `embed_image_base64(image_path: str) -> str`: helper for embedding images

3. Create `configs/review/checklist_templates.yaml` with:
   - Template definitions for common workflows
   - Templates:
     - `production_render`: Full production checklist (30+ items)
     - `quick_preview`: Fast preview checklist (10 items)
     - `product_shot`: Product photography checklist (15 items)
     - `animation_delivery`: Animation delivery checklist (20 items)
   - Each template has: name, description, version, categories with items
   - Items have: id, name, required (bool), auto_verify (bool)

Reference lib/production/production_types.py for dataclass patterns.
Reference tracking-ui/src/onesheet/ for report styling patterns.
  </action>
  <verify>
    - pytest tests/unit/test_review_checklists.py passes
    - pytest tests/unit/test_review_reports.py passes
    - HTML report generates with embedded images
    - Checklist loads/saves correctly
  </verify>
  <done>
    - ChecklistManager creates checklists from templates
    - verify_checklist() returns unverified items
    - generate_report() creates HTML with validation/comparison/checklist sections
    - PDF generation works (or falls back to HTML gracefully)
    - checklist_templates.yaml has 4+ templates
  </done>
</task>

<task type="auto">
  <name>Task 3: Create Approval Workflow and Version History</name>
  <files>
    - lib/review/workflow.py
  </files>
  <action>
Create approval workflow and version history system.

1. Create `lib/review/workflow.py` with:
   - `ReviewState` enum: PENDING, IN_REVIEW, APPROVED, REVISION, REJECTED, ARCHIVED
   - `ReviewPriority` enum: LOW, MEDIUM, HIGH, CRITICAL
   - `ReviewComment` dataclass: id, author, content, timestamp, action_required
   - `ReviewDecision` dataclass: reviewer, decision (ReviewState), timestamp, comments, conditions
   - `VersionInfo` dataclass: version_number, created_at, author, description, changes, file_path, thumbnail_path
   - `ReviewItem` dataclass:
     - id, name, description, state, priority
     - current_version (int), versions (List[VersionInfo])
     - validation_results, comparison_results, checklist
     - review_history (List[ReviewDecision])
     - created_at, updated_at, due_date
     - metadata (Dict[str, Any])
   - `ApprovalWorkflow` class:
     - `__init__(self, storage_path: str = ".gsd-state/review")`
     - `create_item(name: str, description: str, priority: ReviewPriority = MEDIUM) -> ReviewItem`
     - `load_item(item_id: str) -> Optional[ReviewItem]`
     - `save_item(item: ReviewItem) -> bool`
     - `submit_for_review(item_id: str) -> bool`: PENDING -> IN_REVIEW
     - `approve(item_id: str, reviewer: str, comments: Optional[List[str]] = None, conditions: Optional[List[str]] = None) -> bool`
     - `request_revision(item_id: str, reviewer: str, comments: List[str]) -> bool`: IN_REVIEW -> REVISION
     - `reject(item_id: str, reviewer: str, reason: str) -> bool`: IN_REVIEW -> REJECTED
     - `archive(item_id: str) -> bool`: APPROVED -> ARCHIVED
     - `add_version(item_id: str, description: str, file_path: str, changes: List[str]) -> VersionInfo`
     - `get_version_history(item_id: str) -> List[VersionInfo]`
     - `compare_versions(item_id: str, version_a: int, version_b: int) -> ComparisonResult`
     - `get_items_by_state(state: ReviewState) -> List[ReviewItem]`
     - `get_pending_items() -> List[ReviewItem]`
     - `get_overdue_items() -> List[ReviewItem]`
   - `generate_review_report(item: ReviewItem) -> ReportData`: create report data for review item
   - Storage: JSON files in .gsd-state/review/{item_id}/
     - item.json: ReviewItem data
     - versions/{n}/: Version files and thumbnails
     - reports/: Generated reports

2. Add to `lib/review/__init__.py`:
   - Export all workflow types and ApprovalWorkflow class

Reference lib/cinematic/state_manager.py for state persistence patterns.
Reference lib/production/execution_engine.py for checkpoint patterns.
  </action>
  <verify>
    - pytest tests/unit/test_review_workflow.py passes
    - ApprovalWorkflow creates and persists items
    - State transitions work correctly
    - Version history tracks all versions
  </verify>
  <done>
    - ApprovalWorkflow manages full approval lifecycle
    - Items persist to .gsd-state/review/
    - Version comparison uses existing compare_renders()
    - get_pending_items() returns items in PENDING/IN_REVIEW state
  </done>
</task>

<task type="auto">
  <name>Task 4: Create Cryptomatte System</name>
  <files>
    - lib/compositing/__init__.py
    - lib/compositing/cryptomatte.py
    - configs/compositing/cryptomatte_presets.yaml
  </files>
  <action>
Create enhanced cryptomatte system for compositing pipeline.

1. Create `lib/compositing/__init__.py`:
   - Package docstring referencing REQ-CP-01 through REQ-CP-04
   - Re-exports from cryptomatte.py, multi_pass.py, post_process.py
   - Version 0.1.0

2. Create `lib/compositing/cryptomatte.py` with:
   - Note: lib/vfx/cryptomatte.py already has basic manifest/matte extraction
   - This module extends for production compositing workflows
   - `CryptomatteLayerType` enum: OBJECT, MATERIAL, ASSET
   - `CryptomatteLayerConfig` dataclass:
     - layer_type: CryptomatteLayerType
     - name: str (e.g., "characters", "metals")
     - objects: List[str] (object names to include)
     - collections: List[str] (collection names to include)
     - manifest_path: Optional[str]
   - `CryptomatteConfig` dataclass:
     - object_id_layers: List[CryptomatteLayerConfig]
     - material_id_layers: List[CryptomatteLayerConfig]
     - levels: int (default 6)
     - accurate_mode: bool (default True)
   - `CryptomatteManifest` extension (inherit from vfx version):
     - Add layer_name, layer_type, created_at
     - Add `get_objects_by_material(material_name: str) -> List[str]`
     - Add `get_materials_for_object(object_name: str) -> List[str]`
   - `configure_cryptomatte(config: CryptomatteConfig) -> bool`:
     - Sets up cryptomatte passes in Blender view layer
     - Enables object/material/asset passes based on config
     - Calls lib/cinematic/render.py setup_cryptomatte()
   - `create_layer_manifest(layer_config: CryptomatteLayerConfig) -> CryptomatteManifest`:
     - Creates manifest for specific layer
     - Scans scene for objects/collections in config
   - `extract_layer_matte(layer_name: str, manifest: CryptomatteManifest, exr_path: str) -> MatteResult`:
     - Extract matte for entire layer (combined objects)
     - Uses vfx/cryptomatte.py extract_matte_for_objects()
   - `create_comp_layers(config: CryptomatteConfig) -> List[CompLayer]`:
     - Creates CompLayer objects for each cryptomatte layer
     - Integrates with lib/vfx/layer_compositor.py
   - Default layer configurations:
     - Object layers: characters, vehicles, environment, props
     - Material layers: metals, glass, fabric, plastic, emission

3. Create `configs/compositing/cryptomatte_presets.yaml` with:
   - Preset definitions for common workflows
   - Presets:
     - `product_shot`: Object layer for product, material layers for finishes
     - `character_shot`: Object layer for character, material layers for skin/clothing
     - `environment_shot`: Object layers for foreground/mid/background
     - `full_production`: All object and material layers
   - Each preset has: name, description, object_id_layers, material_id_layers, levels

Reference lib/vfx/cryptomatte.py for existing manifest/matte functions.
Reference lib/cinematic/render.py setup_cryptomatte() for Blender integration.
  </action>
  <verify>
    - pytest tests/unit/test_compositing_cryptomatte.py passes
    - CryptomatteConfig creates correct Blender view layer settings
    - Layer manifests generated correctly
    - Presets load from YAML
  </verify>
  <done>
    - lib/compositing/__init__.py exports all cryptomatte types
    - configure_cryptomatte() enables correct passes in Blender
    - create_layer_manifest() generates manifest for layer objects
    - cryptomatte_presets.yaml has 4+ presets with object/material layers
  </done>
</task>

<task type="auto">
  <name>Task 5: Create Multi-Pass Render Pipeline</name>
  <files>
    - lib/compositing/multi_pass.py
    - configs/compositing/multi_pass_presets.yaml
  </files>
  <action>
Create multi-pass render pipeline configuration.

1. Create `lib/compositing/multi_pass.py` with:
   - `PassType` enum: BEAUTY, DIFFUSE, SPECULAR, SHADOW, AO, VOLUME, CRYPTOMATTE, EMISSION, DEPTH, NORMAL, VECTOR
   - `PassConfig` dataclass:
     - pass_type: PassType
     - enabled: bool
     - include_direct: bool (for diffuse/specular)
     - include_indirect: bool (for diffuse/specular)
     - include_color: bool (for diffuse/specular/transmission)
   - `ViewLayerConfig` dataclass:
     - name: str
     - passes: List[PassConfig]
     - crypto_config: Optional[CryptomatteConfig]
     - solo: bool (only render this layer)
   - `EXROutputConfig` dataclass:
     - bit_depth: int (16 or 32)
     - compression: str (ZIP, DWAA, PIZ, NONE)
     - layer_naming: str (e.g., "{scene}_{pass}_{frame}.exr")
     - separate_files: bool (one file per pass)
   - `MultiPassConfig` dataclass:
     - view_layers: List[ViewLayerConfig]
     - exr_output: EXROutputConfig
     - quality_tier: str (references quality_profiles.yaml)
   - `setup_multi_pass(config: MultiPassConfig) -> bool`:
     - Creates view layers in Blender
     - Configures passes per layer
     - Sets up EXR output settings
     - Calls lib/cinematic/render.py functions
   - `create_pass_preset(preset_name: str) -> MultiPassConfig`:
     - Returns preset configuration from YAML
   - `get_enabled_passes(view_layer: ViewLayerConfig) -> List[PassType]`:
     - Returns list of enabled passes
   - `validate_pass_config(config: MultiPassConfig) -> List[str]`:
     - Validates configuration, returns list of issues
   - Default pass groups:
     - Beauty only: combined
     - Data passes: depth, normal, vector
     - Material passes: diffuse, specular, transmission, emission
     - Compositing: all above + cryptomatte + shadow + ao
   - EXR naming convention:
     - 16-bit half-float for preview
     - 32-bit float for production
     - Layer naming: {scene}_{pass}_{frame}.exr

2. Create `configs/compositing/multi_pass_presets.yaml` with:
   - Preset definitions
   - Presets:
     - `beauty_only`: Just combined pass, PNG output
     - `preview`: Beauty + depth, 16-bit EXR
     - `compositing`: Full pass set, 32-bit EXR, cryptomatte
     - `archive`: All passes, 32-bit EXR, no compression
     - `product_shot`: Beauty + shadow + AO + cryptomatte
   - Each preset has: name, description, view_layers, exr_output, quality_tier
   - Hardware tier recommendations:
     - preview: M1 MacBook Pro, 16GB, <30s/frame
     - compositing: M2 Pro, 32GB, <5min/frame
     - archive: M2 Ultra/Render farm, <30min/frame

Reference lib/cinematic/render.py PASS_MAPPING for pass attribute names.
Reference lib/cinematic/preset_loader.py for YAML preset loading.
  </action>
  <verify>
    - pytest tests/unit/test_compositing_multi_pass.py passes
    - MultiPassConfig creates correct view layers in Blender
    - Pass enable/disable works correctly
    - EXR output settings applied correctly
  </verify>
  <done>
    - setup_multi_pass() configures Blender view layers
    - Presets load from multi_pass_presets.yaml
    - EXR naming follows {scene}_{pass}_{frame} convention
    - Hardware tier recommendations documented in presets
  </done>
</task>

<task type="auto">
  <name>Task 6: Create Post-Processing Chain</name>
  <files>
    - lib/compositing/post_process.py
    - lib/compositing/__init__.py (update)
  </files>
  <action>
Create post-processing chain for final output assembly.

1. Create `lib/compositing/post_process.py` with:
   - `PostProcessType` enum: COLOR_CORRECT, LUT, GRAIN, VIGNETTE, BLOOM, SHARPEN, DENOISE
   - `PostProcessStep` dataclass:
     - step_type: PostProcessType
     - enabled: bool
     - order: int
     - params: Dict[str, Any]
   - `PostProcessConfig` dataclass:
     - steps: List[PostProcessStep]
     - input_path: str
     - output_path: str
     - preserve_alpha: bool
   - `PostProcessChain` class:
     - `__init__(self, config: PostProcessConfig)`
     - `add_step(step: PostProcessStep) -> None`
     - `remove_step(step_type: PostProcessType) -> None`
     - `reorder_steps(order: List[PostProcessType]) -> None`
     - `apply(input_data: Any, output_path: str) -> bool`:
       - Applies all steps in order
       - Returns success status
     - `apply_step(step: PostProcessStep, input_data: Any) -> Any`:
       - Apply single step
     - `preview_step(step_type: PostProcessType) -> Any`:
       - Generate preview of single step
   - `create_blender_compositor_nodes(config: PostProcessConfig) -> bool`:
     - Creates compositor nodes in Blender scene
     - Integrates with lib/vfx/compositor_blender.py
   - Pipeline order (CRITICAL):
     1. Geometric distortions (lens distortion, chromatic aberration)
     2. Luminance (vignette, exposure)
     3. Glow/Bloom effects
     4. Color grading (LUTs, color correction)
     5. Film effects (grain)
   - Default step configurations:
     - color_correct: exposure, gamma, contrast, saturation
     - lut: path to .cube file, intensity
     - grain: scale, intensity, animated
     - vignette: intensity, radius, roundness
     - bloom: threshold, intensity, radius
     - sharpen: amount, radius
   - Integration with lib/vfx/color_correction.py for color operations
   - Integration with lib/cinematic/lens_fx.py for lens effects

2. Update `lib/compositing/__init__.py`:
   - Add all post_process exports
   - Create convenience exports for common workflows
   - Add `create_production_composite()` function that combines:
     - Multi-pass setup
     - Cryptomatte configuration
     - Post-processing chain

Reference lib/vfx/color_correction.py for color operations.
Reference lib/cinematic/lens_fx.py for lens imperfection effects.
Reference lib/vfx/compositor_blender.py for node creation.
  </action>
  <verify>
    - pytest tests/unit/test_compositing_post_process.py passes
    - PostProcessChain applies steps in correct order
    - Blender compositor nodes created correctly
    - Pipeline order enforced (geometric -> luminance -> glow -> color -> film)
  </verify>
  <done>
    - PostProcessChain manages step ordering
    - create_blender_compositor_nodes() creates compositor tree
    - Integration with vfx/color_correction.py works
    - Pipeline order enforced programmatically
  </done>
</task>

</tasks>

<verification>
## Phase Verification Checklist

### Review System (REQ-QA-01 through REQ-QA-06)
- [ ] validate_scene() detects scale/material/lighting issues
- [ ] compare_renders() produces similarity scores and difference masks
- [ ] ChecklistManager creates and verifies completion checklists
- [ ] generate_report() outputs HTML and PDF formats
- [ ] ApprovalWorkflow tracks pending/approved/revision states
- [ ] Version history preserves all iterations with thumbnails

### Compositing System (REQ-CP-01 through REQ-CP-04)
- [ ] Cryptomatte passes configured for object/material isolation
- [ ] Multi-pass pipeline produces Beauty, Diffuse, Specular, Shadow, AO, Volume, Cryptomatte, Emission
- [ ] EXR output supports 16-bit half-float and 32-bit float
- [ ] Layer naming follows {scene}_{pass}_{frame}.exr convention
- [ ] Post-processing chain applies effects in correct order

### Integration
- [ ] Review system integrates with cinematic render pipeline
- [ ] Compositing system integrates with existing vfx module
- [ ] All modules work without bpy for unit testing

### Tests
- [ ] pytest tests/unit/test_review_*.py passes (5 test files)
- [ ] pytest tests/unit/test_compositing_*.py passes (3 test files)
- [ ] Total tests: 60+ (10+ per module)
</verification>

<success_criteria>
## Phase 8 Success Criteria

1. **Automated Validation**: validate_scene() runs 6+ validation categories with configurable thresholds
2. **Visual Comparison**: compare_renders() produces SSIM and PSNR scores with difference visualization
3. **Checklists**: ChecklistManager supports 4+ templates with auto-verification
4. **Reports**: HTML and PDF reports include validation, comparison, and checklist sections
5. **Approval Workflow**: Full state machine with PENDING -> IN_REVIEW -> APPROVED/REVISION/REJECTED -> ARCHIVED
6. **Version History**: All versions tracked with thumbnails and comparison capability
7. **Cryptomatte**: Object and material ID passes configured with manifest management
8. **Multi-Pass**: View layer configuration for 10+ pass types with EXR output
9. **Post-Processing**: Chain with 6+ effect types in correct pipeline order

**Hardware Tier Support**:
- Preview tier: M1 MacBook Pro, 16GB RAM, <30s/frame
- Standard tier: M2 Pro, 32GB RAM, <5min/frame
- Production tier: M2 Ultra, 64GB RAM OR Multi-GPU, <30min/frame
</success_criteria>

<output>
After completion, create `.planning/phases/8/8-SUMMARY.md` with:
- Modules created: 6 Python modules, 4 YAML configs
- Exports: 80+ (30 review, 30 compositing, 20 shared types)
- Tests: 60+ unit tests
- Version: 0.1.0
</output>
