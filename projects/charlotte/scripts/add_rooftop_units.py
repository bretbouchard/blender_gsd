"""
Charlotte Digital Twin - Apply Rooftop Units to All Buildings

Adds rooftop HVAC units, cooling towers, and mechanical equipment
to all qualifying buildings in the scene.

Features:
- Automatic unit count based on roof size
- Random placement with collision avoidance
- Box HVAC units and cylindrical cooling towers
- Grouped in dedicated collection

Usage:
    blender charlotte.blend --python scripts/add_rooftop_units.py

Options:
    --min-height 30    Minimum building height in meters (default: 30)
    --seed 42          Random seed for reproducibility (default: 42)
    --clear            Clear existing rooftop units first
"""

import bpy
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

# Use the simple Python-based approach (more reliable)
from lib.rooftop_nodes import (
    add_rooftop_units_to_all_buildings,
    clear_rooftop_units,
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Add rooftop units')
    parser.add_argument('--min-height', type=float, default=30.0)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--clear', action='store_true')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CHARLOTTE ROOFTOP UNITS")
    print("=" * 60)

    if args.clear:
        clear_rooftop_units()

    add_rooftop_units_to_all_buildings(
        min_height=args.min_height,
        seed=args.seed,
    )

    print("\n✓ Done!")
    print("\nTip: Units are in the 'Rooftop_Units' collection")
    print("Tip: Run with --clear to remove and regenerate")


if __name__ == '__main__':
    main()
