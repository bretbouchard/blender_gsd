"""
Geometry Nodes Utilities Package.

Provides programmatic tools for building and manipulating Blender
geometry node trees with support for simulations, instances, fields,
and named attributes.

Core Components:
    NodeTreeBuilder: Programmatic node tree creation
    InstanceController: Instance extraction and control
    SimulationBuilder: Simulation zone helpers
    FieldOperations: Field operations and sampling
    AttributeManager: Named attribute handling

Extended Components (Phase 5):
    CurlNoise: Divergence-free curl noise for particles
    CurlParticleSystem: Build curl-based particle simulations
    EdgeErosion: Edge erosion for weathered mesh look
    FaceErosion: Face erosion with pitting
    ErosionSystem: Combined edge and face erosion
    HairClumpGenerator: Generate procedural hair clumps
    FurSystem: Complete fur/hair system
    HandwritingSystem: Procedural handwriting text system
    BuildingFolder: Doctor Strange-style building folding effect
    InfiniteBackdrop: Create infinite studio backdrops
    StudioSetup: Complete studio lighting setup
    VolumetricTools: Volumetric rendering utilities

Usage:
    from lib.geometry_nodes import NodeTreeBuilder, SimulationBuilder

    # Create a geometry node tree
    builder = NodeTreeBuilder("MyGeometryNodes")

    # Add nodes
    input_node = builder.add_group_input((0, 0))
    transform = builder.add_node("GeometryNodeTransform", (200, 0))

    # Create a simulation
    sim = SimulationBuilder(builder)
    sim_in, sim_out = sim.create_simulation_zone((400, 0))

    # Get the tree
    tree = builder.get_tree()

    # Use curl noise for particles
    from lib.geometry_nodes import CurlNoise, CurlParticleSystem
    curl = CurlNoise.from_noise_texture_gn(builder, position_socket)

    # Create fur system
    from lib.geometry_nodes import FurSystem
    fur = FurSystem(surface_mesh, builder).set_density(1000).build()

Compatibility:
    - Blender 4.x
    - Blender 5.x
"""

from __future__ import annotations

__all__ = [
    # Core builder
    "NodeTreeBuilder",
    # Instance handling
    "InstanceController",
    "InstanceExtractor",
    # Simulation building
    "SimulationBuilder",
    # Field operations
    "FieldOperations",
    # Attribute management
    "AttributeManager",
    # Curl noise (Phase 5)
    "CurlNoise",
    "CurlParticleSystem",
    "CurlLayer",
    # Erosion (Phase 5)
    "EdgeErosion",
    "FaceErosion",
    "ErosionSystem",
    "erode_mesh",
    # Hair/fur (Phase 5)
    "HairClumpGenerator",
    "FurSystem",
    "SIZE_CURVES",
    "create_fur",
    # Handwriting (Phase 5)
    "HandwritingSystem",
    "LetterVariantGenerator",
    "create_handwriting",
    "DEFAULT_ALPHABET",
    # Folding (Phase 5)
    "BuildingFolder",
    "FoldingAnimator",
    "create_folding_effect",
    # Backdrop (Phase 5)
    "InfiniteBackdrop",
    "StudioSetup",
    "StudioLight",
    "create_studio",
    # Volumes (Phase 5)
    "VolumetricTools",
    "VolumePreset",
    "create_quick_fog",
    "create_quick_smoke",
    "create_quick_cloud",
    # Version info
    "__version__",
    "__author__",
]

__version__ = "2.0.0"
__author__ = "Blender GSD Project"


from .attributes import AttributeManager
from .fields import FieldOperations
from .instances import InstanceController, InstanceExtractor
from .node_builder import NodeTreeBuilder
from .simulation import SimulationBuilder

# Phase 5: Extended components
from .curl_noise import CurlNoise, CurlParticleSystem, CurlLayer
from .erosion import EdgeErosion, FaceErosion, ErosionSystem, erode_mesh
from .hair import HairClumpGenerator, FurSystem, SIZE_CURVES, create_fur
from .handwriting import (
    HandwritingSystem,
    LetterVariantGenerator,
    create_handwriting,
    DEFAULT_ALPHABET,
)
from .folding import BuildingFolder, FoldingAnimator, create_folding_effect
from .backdrop import InfiniteBackdrop, StudioSetup, StudioLight, create_studio
from .volumes import (
    VolumetricTools,
    VolumePreset,
    create_quick_fog,
    create_quick_smoke,
    create_quick_cloud,
)


# Convenience function for quick node tree creation
def create_node_tree(
    name: str,
    inputs: list[dict] | None = None,
    outputs: list[dict] | None = None,
) -> NodeTreeBuilder:
    """
    Create a new geometry node tree with optional interface.

    Convenience function that creates a NodeTreeBuilder and optionally
    sets up its input/output interface.

    Args:
        name: Name for the node tree.
        inputs: Optional list of input definitions.
            Each dict should have "name", "type", and optional "default".
        outputs: Optional list of output definitions.
            Each dict should have "name" and "type".

    Returns:
        A configured NodeTreeBuilder instance.

    Example:
        >>> tree = create_node_tree(
        ...     "MyModifier",
        ...     inputs=[
        ...         {"name": "Geometry", "type": "GEOMETRY"},
        ...         {"name": "Scale", "type": "VALUE", "default": 1.0},
        ...     ],
        ...     outputs=[
        ...         {"name": "Geometry", "type": "GEOMETRY"},
        ...     ]
        ... )
    """
    builder = NodeTreeBuilder(name)

    if inputs or outputs:
        builder.wrap_as_group(inputs or [], outputs or [])

    return builder


# Convenience aliases
builder = NodeTreeBuilder
instances = InstanceController
simulation = SimulationBuilder
fields = FieldOperations
attributes = AttributeManager
