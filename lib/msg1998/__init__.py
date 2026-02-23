"""
MSG 1998 - Cross-Project Integration Module

This module implements the Blender GSD side of the MSG 1998 film pipeline,
consuming production packages from FDX GSD and producing composited shots.

Phases:
- 9.MSG: Location Building (fSpy import, modeling, render layers)
- 12.MSG: SD Compositing (ControlNet, layer composite, output)

Workflow:
1. Receive handoff from FDX GSD
2. Build 3D locations from fSpy + references
3. Render passes for compositing
4. Run SD style transfer with ControlNet
5. Composite layers with 1998 film aesthetic
6. Export for editorial
"""

from .types import (
    FSpyImportResult,
    ReferenceSet,
    FDXHandoffPackage,
    LocationAsset,
    PeriodViolation,
    CompositeLayer,
    ControlNetConfig,
    SDShotConfig,
    FilmLook1998,
    ColorGradeConfig,
    OutputSpec,
    LayerInput,
    QCIssue,
)

from .fspy_import import import_fspy, validate_fspy_camera
from .reference_loader import load_references, setup_reference_plane
from .handoff_receiver import receive_handoff, validate_handoff
from .period_validator import validate_period_accuracy, PERIOD_VIOLATIONS_1998

from .geometry_builders import create_building_base, add_windows, add_doors
from .modeling_pipeline import ModelingStage, LocationBuildState, advance_stage
from .materials_1998 import MATERIALS_1998, create_period_material
from .photo_projection import setup_photo_projection, bake_projection
from .location_asset import create_location_asset, export_location_package

from .render_passes import MSGRenderPasses, configure_render_passes
from .layer_separation import create_composite_layers, LAYER_COLORS
from .render_profile import MSG1998RenderProfile, apply_msg_profile
from .export_compositing import export_for_compositing, generate_metadata

from .controlnet import load_controlnet_models, prepare_depth_map, prepare_normal_map
from .sd_config import load_sd_config, validate_sd_config
from .prompts_1998 import POSITIVE_BASE, NEGATIVE_BASE, SCENE_PROMPTS, build_prompt
from .sd_generate import generate_layer, generate_all_layers
from .seed_verify import verify_seed_reproducibility, compute_image_hash

from .layer_compositor import setup_layer_nodes, composite_layers
from .film_look_1998 import apply_film_grain, apply_lens_effects, apply_vignette
from .color_grade import apply_color_grade, create_kodak_lut_node
from .depth_effects import apply_depth_of_field, apply_atmospheric_haze
from .compositor_graph import build_msg_compositor_graph

from .output_formats import OUTPUT_FORMATS, configure_output
from .color_conversion import convert_to_rec709, convert_to_srgb
from .qc_validator import validate_output, check_period_accuracy, check_technical_specs
from .batch_export import create_export_jobs, run_export_job, batch_export
from .editorial_package import create_editorial_package, generate_shot_metadata

__all__ = [
    # Types
    "FSpyImportResult",
    "ReferenceSet",
    "FDXHandoffPackage",
    "LocationAsset",
    "PeriodViolation",
    "CompositeLayer",
    "ControlNetConfig",
    "SDShotConfig",
    "FilmLook1998",
    "ColorGradeConfig",
    "OutputSpec",
    "LayerInput",
    "QCIssue",
    # Phase 9.MSG-01
    "import_fspy",
    "validate_fspy_camera",
    "load_references",
    "setup_reference_plane",
    "receive_handoff",
    "validate_handoff",
    "validate_period_accuracy",
    "PERIOD_VIOLATIONS_1998",
    # Phase 9.MSG-02
    "create_building_base",
    "add_windows",
    "add_doors",
    "ModelingStage",
    "LocationBuildState",
    "advance_stage",
    "MATERIALS_1998",
    "create_period_material",
    "setup_photo_projection",
    "bake_projection",
    "create_location_asset",
    "export_location_package",
    # Phase 9.MSG-03
    "MSGRenderPasses",
    "configure_render_passes",
    "create_composite_layers",
    "LAYER_COLORS",
    "MSG1998RenderProfile",
    "apply_msg_profile",
    "export_for_compositing",
    "generate_metadata",
    # Phase 12.MSG-01
    "ControlNetConfig",
    "load_controlnet_models",
    "prepare_depth_map",
    "prepare_normal_map",
    "load_sd_config",
    "validate_sd_config",
    "POSITIVE_BASE",
    "NEGATIVE_BASE",
    "SCENE_PROMPTS",
    "build_prompt",
    "generate_layer",
    "generate_all_layers",
    "verify_seed_reproducibility",
    "compute_image_hash",
    # Phase 12.MSG-02
    "setup_layer_nodes",
    "composite_layers",
    "apply_film_grain",
    "apply_lens_effects",
    "apply_vignette",
    "apply_color_grade",
    "create_kodak_lut_node",
    "apply_depth_of_field",
    "apply_atmospheric_haze",
    "build_msg_compositor_graph",
    # Phase 12.MSG-03
    "OUTPUT_FORMATS",
    "configure_output",
    "convert_to_rec709",
    "convert_to_srgb",
    "validate_output",
    "check_period_accuracy",
    "check_technical_specs",
    "create_export_jobs",
    "run_export_job",
    "batch_export",
    "create_editorial_package",
    "generate_shot_metadata",
]
