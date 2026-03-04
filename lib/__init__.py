"""
Blender GSD Framework Library

Core modules for procedural artifact generation.

Note: Blender-dependent modules are imported lazily to allow
testing of non-Blender code (oracle, cinematic types) without
requiring Blender to be installed.

## Tutorial Knowledge Codification

The following modules codify techniques from the Blender tutorial knowledge base:
- volumetric.py - KB Sections 25, 28, 29, 33 (World fog, god rays, video projection)
- particles.py - KB Section 30 (Seamless looping particle animation)
- simulation.py - KB Section 38 (Footprint/track simulations)
- mograph.py - KB Section 37 (After Effects-style text animation)
- paths.py - KB Section 35 (Shortest path node optimization)
- growth.py - KB Section 34 (Procedural fern/plant growth)
- effector.py - KB Section 12 (Effector-based offset animation)
- metaballs.py - KB Section 13 (SDF volume metaballs)
- morphing.py - KB Section 24 (Product morph effect)
- recursive.py - KB Section 11 (Recursive instancing/hand rig)
- crystals.py - KB Section 23 (Procedural crystal creation)
- painterly.py - KB Section 14 (Painterly brush stroke effect)
- lighting.py - KB Sections 17, 25-28 (Cinematic lighting)
- raycast.py - KB Sections 1, 18 (Shader raycast, material layering)
- loop.py - KB Section 2 (Seamless animation loops)
- hardsurface.py - KB Sections 8-9 (Hard surface validation)
- compositing.py - KB Section 22 (Compositor effects)
- dispersion.py - KB Sections 2, 3, 21, 36 (Light dispersion, glass)
- camera.py - KB Sections 3, 10, 16, 21 (Camera utilities, isometric)
- scatter.py - KB Section 5 (Scattering utilities)
- geometry.py - KB Sections 2, 15 (Generative patterns)
- sculpting.py - KB Section 31 (Sculpting effects)

Cross-references are embedded in each module's docstrings.
See: docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md
"""

import sys

# Check if we're in a Blender environment
_IN_BLENDER = 'bpy' in sys.modules or 'bpy' in sys.builtin_module_names

# Always-available modules (no Blender dependency)
# These can be imported for unit testing

__version__ = "0.8.2"
__version_info__ = (0, 8, 2)

__all__ = [
    # Version
    "__version__",
    "__version_info__",
    # Blender-dependent (import lazily or in Blender context)
    "Pipeline",
    "NodeKit",
    "reset_scene",
    "ensure_collection",
    "load_task",
    # Tutorial-codified modules (original)
    "WorldFog",
    "VolumetricProjector",
    "GodRays",
    "SeamlessParticles",
    "FootprintSimulation",
    "TextAnimator",
    "TrailEffect",
    "ShortestPathOptimizer",
    "FernGrower",
    # Tutorial-codified modules (batch 2)
    "EffectorOffset",
    "DistanceMask",
    "DynamicLighting",
    "SDFMetaballs",
    "VoxelSizePresets",
    "MetaballPresets",
    "ProductMorph",
    "MorphTarget",
    "MorphingMaterial",
    "RecursiveInstance",
    "TransformStorage",
    "IntersectionBlending",
    "CrystalGenerator",
    "CrystalScatter",
    "CrystalPresets",
    # Tutorial-codified modules (batch 3)
    "BrushStrokeEffect",
    "PainterlyMaterial",
    "PainterlyPresets",
    "CinematicLighting",
    "LightRig",
    "IESLighting",
    "CinematicChecklist",
    "ShaderRaycast",
    "RaycastPresets",
    "MaterialLayering",
    "SeamlessLoop",
    "LoopUtilities",
    "LoopPresets",
    "EmissionLoop",
    "HardSurfaceValidator",
    "BooleanWorkflow",
    "HardSurfaceTips",
    "HardSurfacePresets",
    "CompositorSetup",
    "BloomEffect",
    "ColorGrading",
    "GlareTypes",
    "CompositorWorkflow",
    # Tutorial-codified modules (batch 4)
    "ChromaticAberration",
    "GlassDispersion",
    "LightSplitter",
    "DispersionPresets",
    "SpectralColors",
    "IsometricCamera",
    "DepthOfField",
    "CameraRig",
    "OrbitCamera",
    "CameraPresets",
    "ScatterSetup",
    "WeightMask",
    "GeometryNodesScatter",
    "ScatterPresets",
    "RadialArray",
    "WaveField",
    "IndexAnimation",
    "PatternPresets",
    "SculptEnhancer",
    "SurfaceNoise",
    "CreatureSculpt",
    "SculptingTools",
    "SculptPresets",
    # HUD classes
    "HardSurfaceHUD",
    "CompositorHUD",
    "LoopHUD",
    # Road/Traffic system (geometry_nodes/road_builder.py)
    "RoadType",
    "LaneType",
    "IntersectionType",
    "LaneSpec",
    "RoadSegment",
    "IntersectionGeometry",
    "RoadNetwork",
    "ROAD_TEMPLATES",
    "SURFACE_MATERIALS",
    "RoadBuilder",
    "RoadNetworkGN",
    "IntersectionBuilder",
    "RoadHUD",
]


def __getattr__(name: str):
    """
    Lazy import of Blender-dependent modules.

    This allows 'from lib import oracle' to work without loading
    Blender-dependent modules like nodekit.
    """
    if name == "Pipeline":
        from .pipeline import Pipeline
        return Pipeline
    elif name == "NodeKit":
        from .nodekit import NodeKit
        return NodeKit
    elif name == "reset_scene":
        from .scene_ops import reset_scene
        return reset_scene
    elif name == "ensure_collection":
        from .scene_ops import ensure_collection
        return ensure_collection
    elif name == "load_task":
        from .gsd_io import load_task
        return load_task
    # Tutorial-codified modules (original)
    elif name in ("WorldFog", "VolumetricProjector", "GodRays"):
        from .volumetric import WorldFog, VolumetricProjector, GodRays
        return locals()[name]
    elif name == "SeamlessParticles":
        from .particles import SeamlessParticles
        return SeamlessParticles
    elif name == "FootprintSimulation":
        from .simulation import FootprintSimulation
        return FootprintSimulation
    elif name in ("TextAnimator", "TrailEffect"):
        from .mograph import TextAnimator, TrailEffect
        return locals()[name]
    elif name == "ShortestPathOptimizer":
        from .paths import ShortestPathOptimizer
        return ShortestPathOptimizer
    elif name == "FernGrower":
        from .growth import FernGrower
        return FernGrower
    # Tutorial-codified modules (new - effector)
    elif name == "EffectorOffset":
        from .effector import EffectorOffset
        return EffectorOffset
    elif name == "DistanceMask":
        from .effector import DistanceMask
        return DistanceMask
    elif name == "DynamicLighting":
        from .effector import DynamicLighting
        return DynamicLighting
    # Tutorial-codified modules (new - metaballs)
    elif name == "SDFMetaballs":
        from .metaballs import SDFMetaballs
        return SDFMetaballs
    elif name == "VoxelSizePresets":
        from .metaballs import VoxelSizePresets
        return VoxelSizePresets
    elif name == "MetaballPresets":
        from .metaballs import MetaballPresets
        return MetaballPresets
    # Tutorial-codified modules (new - morphing)
    elif name == "ProductMorph":
        from .morphing import ProductMorph
        return ProductMorph
    elif name == "MorphTarget":
        from .morphing import MorphTarget
        return MorphTarget
    elif name == "MorphingMaterial":
        from .morphing import MorphingMaterial
        return MorphingMaterial
    # Tutorial-codified modules (new - recursive)
    elif name == "RecursiveInstance":
        from .recursive import RecursiveInstance
        return RecursiveInstance
    elif name == "TransformStorage":
        from .recursive import TransformStorage
        return TransformStorage
    elif name == "IntersectionBlending":
        from .recursive import IntersectionBlending
        return IntersectionBlending
    # Tutorial-codified modules (new - crystals)
    elif name == "CrystalGenerator":
        from .crystals import CrystalGenerator
        return CrystalGenerator
    elif name == "CrystalScatter":
        from .crystals import CrystalScatter
        return CrystalScatter
    elif name == "CrystalPresets":
        from .crystals import CrystalPresets
        return CrystalPresets
    # Tutorial-codified modules (batch 3 - painterly)
    elif name == "BrushStrokeEffect":
        from .painterly import BrushStrokeEffect
        return BrushStrokeEffect
    elif name == "PainterlyMaterial":
        from .painterly import PainterlyMaterial
        return PainterlyMaterial
    elif name == "PainterlyPresets":
        from .painterly import PainterlyPresets
        return PainterlyPresets
    # Tutorial-codified modules (batch 3 - lighting)
    elif name == "CinematicLighting":
        from .lighting import CinematicLighting
        return CinematicLighting
    elif name == "LightRig":
        from .lighting import LightRig
        return LightRig
    elif name == "IESLighting":
        from .lighting import IESLighting
        return IESLighting
    elif name == "CinematicChecklist":
        from .lighting import CinematicChecklist
        return CinematicChecklist
    # Tutorial-codified modules (batch 3 - raycast)
    elif name == "ShaderRaycast":
        from .raycast import ShaderRaycast
        return ShaderRaycast
    elif name == "RaycastPresets":
        from .raycast import RaycastPresets
        return RaycastPresets
    elif name == "MaterialLayering":
        from .raycast import MaterialLayering
        return MaterialLayering
    # Tutorial-codified modules (batch 3 - loop)
    elif name == "SeamlessLoop":
        from .loop import SeamlessLoop
        return SeamlessLoop
    elif name == "LoopUtilities":
        from .loop import LoopUtilities
        return LoopUtilities
    elif name == "LoopPresets":
        from .loop import LoopPresets
        return LoopPresets
    elif name == "EmissionLoop":
        from .loop import EmissionLoop
        return EmissionLoop
    # Tutorial-codified modules (batch 3 - hardsurface)
    elif name == "HardSurfaceValidator":
        from .hardsurface import HardSurfaceValidator
        return HardSurfaceValidator
    elif name == "BooleanWorkflow":
        from .hardsurface import BooleanWorkflow
        return BooleanWorkflow
    elif name == "HardSurfaceTips":
        from .hardsurface import HardSurfaceTips
        return HardSurfaceTips
    elif name == "HardSurfacePresets":
        from .hardsurface import HardSurfacePresets
        return HardSurfacePresets
    # Tutorial-codified modules (batch 3 - compositing)
    elif name == "CompositorSetup":
        from .compositing import CompositorSetup
        return CompositorSetup
    elif name == "BloomEffect":
        from .compositing import BloomEffect
        return BloomEffect
    elif name == "ColorGrading":
        from .compositing import ColorGrading
        return ColorGrading
    elif name == "GlareTypes":
        from .compositing import GlareTypes
        return GlareTypes
    elif name == "CompositorWorkflow":
        from .compositing import CompositorWorkflow
        return CompositorWorkflow
    # Tutorial-codified modules (batch 4 - dispersion)
    elif name == "ChromaticAberration":
        from .dispersion import ChromaticAberration
        return ChromaticAberration
    elif name == "GlassDispersion":
        from .dispersion import GlassDispersion
        return GlassDispersion
    elif name == "LightSplitter":
        from .dispersion import LightSplitter
        return LightSplitter
    elif name == "DispersionPresets":
        from .dispersion import DispersionPresets
        return DispersionPresets
    elif name == "SpectralColors":
        from .dispersion import SpectralColors
        return SpectralColors
    # Tutorial-codified modules (batch 4 - camera)
    elif name == "IsometricCamera":
        from .camera import IsometricCamera
        return IsometricCamera
    elif name == "DepthOfField":
        from .camera import DepthOfField
        return DepthOfField
    elif name == "CameraRig":
        from .camera import CameraRig
        return CameraRig
    elif name == "OrbitCamera":
        from .camera import OrbitCamera
        return OrbitCamera
    elif name == "CameraPresets":
        from .camera import CameraPresets
        return CameraPresets
    # Tutorial-codified modules (batch 4 - scatter)
    elif name == "ScatterSetup":
        from .scatter import ScatterSetup
        return ScatterSetup
    elif name == "WeightMask":
        from .scatter import WeightMask
        return WeightMask
    elif name == "GeometryNodesScatter":
        from .scatter import GeometryNodesScatter
        return GeometryNodesScatter
    elif name == "ScatterPresets":
        from .scatter import ScatterPresets
        return ScatterPresets
    # Tutorial-codified modules (batch 4 - geometry)
    elif name == "RadialArray":
        from .geometry import RadialArray
        return RadialArray
    elif name == "WaveField":
        from .geometry import WaveField
        return WaveField
    elif name == "IndexAnimation":
        from .geometry import IndexAnimation
        return IndexAnimation
    elif name == "PatternPresets":
        from .geometry import PatternPresets
        return PatternPresets
    # Tutorial-codified modules (batch 4 - sculpting)
    elif name == "SculptEnhancer":
        from .sculpting import SculptEnhancer
        return SculptEnhancer
    elif name == "SurfaceNoise":
        from .sculpting import SurfaceNoise
        return SurfaceNoise
    elif name == "CreatureSculpt":
        from .sculpting import CreatureSculpt
        return CreatureSculpt
    elif name == "SculptingTools":
        from .sculpting import SculptingTools
        return SculptingTools
    elif name == "SculptPresets":
        from .sculpting import SculptPresets
        return SculptPresets
    # HUD classes
    elif name == "HardSurfaceHUD":
        from .hardsurface import HardSurfaceHUD
        return HardSurfaceHUD
    elif name == "CompositorHUD":
        from .compositing import CompositorHUD
        return CompositorHUD
    elif name == "LoopHUD":
        from .loop import LoopHUD
        return LoopHUD
    # Road/Traffic system
    elif name in ("RoadType", "LaneType", "IntersectionType"):
        from .geometry_nodes.road_builder import RoadType, LaneType, IntersectionType
        return locals()[name]
    elif name == "LaneSpec":
        from .geometry_nodes.road_builder import LaneSpec
        return LaneSpec
    elif name == "RoadSegment":
        from .geometry_nodes.road_builder import RoadSegment
        return RoadSegment
    elif name == "IntersectionGeometry":
        from .geometry_nodes.road_builder import IntersectionGeometry
        return IntersectionGeometry
    elif name == "RoadNetwork":
        from .geometry_nodes.road_builder import RoadNetwork
        return RoadNetwork
    elif name == "ROAD_TEMPLATES":
        from .geometry_nodes.road_builder import ROAD_TEMPLATES
        return ROAD_TEMPLATES
    elif name == "SURFACE_MATERIALS":
        from .geometry_nodes.road_builder import SURFACE_MATERIALS
        return SURFACE_MATERIALS
    elif name == "RoadBuilder":
        from .geometry_nodes.road_builder import RoadBuilder
        return RoadBuilder
    elif name == "RoadNetworkGN":
        from .geometry_nodes.road_builder import RoadNetworkGN
        return RoadNetworkGN
    elif name == "IntersectionBuilder":
        from .geometry_nodes.road_builder import IntersectionBuilder
        return IntersectionBuilder
    elif name == "RoadHUD":
        from .geometry_nodes.road_builder import RoadHUD
        return RoadHUD

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
