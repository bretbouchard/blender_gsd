"""
Example: Mask Basics

Demonstrates:
- Creating zone-based masks
- Combining masks with boolean operations
- Applying smooth falloff

Usage:
    blender --python examples/basic/mask_basics.py
"""

from __future__ import annotations


def main():
    """Demonstrate mask creation and combination."""
    print("Mask Basics Example")
    print("=" * 40)

    # Import mask classes
    from lib.masks import Mask, MaskCombiner, FalloffType

    # Create a height-based mask (middle zone)
    height_mask = Mask(
        mask_type="height",
        min_value=0.2,
        max_value=0.8,
        falloff=FalloffType.SMOOTH,
        falloff_distance=0.1,
    )
    print(f"Created height mask: {height_mask.min_value} to {height_mask.max_value}")

    # Create an angle-based mask (front facing)
    angle_mask = Mask(
        mask_type="angle",
        axis="Z",
        angle_start=0,
        angle_end=90,
        falloff=FalloffType.LINEAR,
    )
    print(f"Created angle mask: {angle_mask.angle_start}° to {angle_mask.angle_end}°")

    # Combine masks with AND operation
    combined = MaskCombiner(height_mask).AND(angle_mask)
    print(f"Combined masks with AND operation")

    # Create inverse mask
    inverse = MaskCombiner(combined).NOT()
    print(f"Created inverse mask")

    # Demonstrate mask evaluation
    print("\nMask Evaluation Examples:")
    test_points = [
        (0.5, 45, "Middle height, front facing"),
        (0.1, 45, "Low height, front facing"),
        (0.5, 120, "Middle height, side facing"),
        (0.9, 10, "High height, front facing"),
    ]

    for height, angle, desc in test_points:
        # Evaluate each mask
        height_val = height_mask.evaluate(height=height)
        angle_val = angle_mask.evaluate(angle=angle)
        combined_val = combined.evaluate(height=height, angle=angle)

        print(f"\n  Point: {desc}")
        print(f"    Height mask: {height_val:.2f}")
        print(f"    Angle mask: {angle_val:.2f}")
        print(f"    Combined: {combined_val:.2f}")

    print("\n✓ Example complete!")


if __name__ == "__main__":
    main()
