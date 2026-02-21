"""
Modifiers Module for Blender 5.0+.

Provides utilities for the new array modifier, surface distribution,
and instance management.

Example:
    >>> from lib.blender5x.modifiers import NewArrayModifier, SurfaceDistribute
    >>> NewArrayModifier.create_radial(target, count=12)
    >>> SurfaceDistribute.distribute_collection(surface, collection)
"""

from .array_new import (
    NewArrayModifier,
    SurfaceDistribute,
    ArraySettings,
    ArrayFitType,
    ArrayDistribution,
)

from .distribute import (
    SurfaceDistribution,
    InstanceVariation,
    DistributionSettings,
    DistributionMethod,
    AlignmentMode,
)

from .instances import (
    InstanceModifiers,
    InstanceSettings,
    InstanceMode,
    CurveFollowMode,
)

__all__ = [
    # Array
    "NewArrayModifier",
    "SurfaceDistribute",
    "ArraySettings",
    "ArrayFitType",
    "ArrayDistribution",
    # Distribute
    "SurfaceDistribution",
    "InstanceVariation",
    "DistributionSettings",
    "DistributionMethod",
    "AlignmentMode",
    # Instances
    "InstanceModifiers",
    "InstanceSettings",
    "InstanceMode",
    "CurveFollowMode",
]
