"""
Eyes Project - Script Package

Main entry point for the eye generation system.
"""

from .eye_geometry import create_eye_node_group, create_single_eye
from .eye_distribution import create_distribution_node_group, create_eyes_on_sphere
from .generate_eyes import (
    generate_eyes,
    generate_single_test_eye,
    clear_all_eyes,
    regenerate_with_seed,
    load_config,
    register,
    unregister,
)

__all__ = [
    'create_eye_node_group',
    'create_single_eye',
    'create_distribution_node_group',
    'create_eyes_on_sphere',
    'generate_eyes',
    'generate_single_test_eye',
    'clear_all_eyes',
    'regenerate_with_seed',
    'load_config',
    'register',
    'unregister',
]

__version__ = '0.1.0'
