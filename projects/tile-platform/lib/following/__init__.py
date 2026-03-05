"""
Following module for automated platform tracking.

This module provides classes for automated following of targets,
including position tracking, prediction, and tile management.

Classes:
    TargetTracker: Tracks and predicts target positions
    FollowingController: Coordinates automated platform following
    PlacementPredictor: Predicts tile placement needs
"""

from .controller import FollowingController
from .predictor import PlacementPredictor
from .tracker import TargetTracker

__all__ = [
    "TargetTracker",
    "FollowingController",
    "PlacementPredictor",
]
