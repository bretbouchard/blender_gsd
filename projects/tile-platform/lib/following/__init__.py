"""
Following module for automated platform tracking.

This module provides classes for automated following of targets,
including position tracking, prediction, and tile management.

Classes:
    TargetTracker: Tracks and predicts target positions
    FollowingController: Coordinates automated platform following
"""

from .controller import FollowingController
from .tracker import TargetTracker

__all__ = [
    "TargetTracker",
    "FollowingController",
]
