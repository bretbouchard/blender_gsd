"""
Motion Tracking Package

Provides tracking types, session management, and import/export for motion tracking.

Usage:
    from lib.cinematic.tracking import TrackData, SolveData, FootageMetadata
"""

from __future__ import annotations

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .types import (
    TrackData,
    SolveData,
    SolveReport,
    FootageMetadata,
    FootageInfo,
    TrackingSession,
)

__all__ = [
    "BLENDER_AVAILABLE",
    "TrackData",
    "SolveData",
    "SolveReport",
    "FootageMetadata",
    "FootageInfo",
    "TrackingSession",
]

__version__ = "0.1.0"
