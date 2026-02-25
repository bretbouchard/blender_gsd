"""
MSG-1998 Road System - Apply Lane Markings

Adds lane marking geometry nodes modifier to all road curves.
Creates center lines, edge lines, and crosswalk markings.

Run this after roads are set up.
"""

import bpy


def get_road_curves():
    """Get all road curves from collections."""
    curves = []
    for coll_name in ["Road_Objects", "Streets_Roads"]:
        if coll_name in bpy.data.collections:
            coll = bpy.data.collections[coll_name]
            for obj in coll.objects:
                if obj.type == 'CURVE':
                    curves.append(obj)
    return curves


def get_road_width(obj):
    """Get road width from existing modifier or name."""
    # Try to get from existing Road modifier
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group and mod.node_group.name == "MSG_Road_Builder":
            for item in mod.node_group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                    if item.name == "Road Width":
                        try:
                            return mod[item.identifier]
                        except:
                            pass

    # Fall back to name-based detection
    name_lower = obj.name.lower()
    if "avenue" in name_lower:
        return 20.0
    elif "broadway" in name_lower:
        return 22.0
    elif "plaza" in name_lower:
        return 25.0
    elif "street" in name_lower:
        return 12.0
    elif "lane" in name_lower:
        return 8.0
    return 10.0


def apply_lane_markings():
    """Apply lane markings geometry nodes to all roads."""

    print("\n" + "=" * 50)
    print("Applying Lane Markings")
    print("=" * 50)

    # Check node group exists
    if "MSG_Lane_Markings" not in bpy.data.node_groups:
        print("ERROR: MSG_Lane_Markings node group not found")
        print("Run setup_road_geonodes.py first")
        return

    curves = get_road_curves()
    print(f"Found {len(curves)} road curves")

    # Create output collection for markings
    if "Lane_Markings" not in bpy.data.collections:
        markings_coll = bpy.data.collections.new("Lane_Markings")
        bpy.context.scene.collection.children.link(markings_coll)
    else:
        markings_coll = bpy.data.collections["Lane_Markings"]

    created = 0
    for curve in curves:
        # Check if already has lane markings modifier
        has_markings = any(
            m.type == 'NODES' and m.node_group and m.node_group.name == "MSG_Lane_Markings"
            for m in curve.modifiers
        )

        if has_markings:
            print(f"  Skipping (has markings): {curve.name}")
            continue

        # Add lane markings modifier
        mod = curve.modifiers.new(name="Lane Markings", type='NODES')
        mod.node_group = bpy.data.node_groups["MSG_Lane_Markings"]

        # Get road width
        road_width = get_road_width(curve)

        # Set parameters
        for item in mod.node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name == "Road Width":
                    mod[item.identifier] = road_width
                elif item.name == "Center Line Width":
                    mod[item.identifier] = 0.15  # 15cm center line
                elif item.name == "Edge Line Width":
                    mod[item.identifier] = 0.10  # 10cm edge lines
                elif item.name == "Z Offset":
                    mod[item.identifier] = 0.02  # 2cm above road surface

        print(f"  Added markings: {curve.name} (width={road_width}m)")
        created += 1

    print(f"\nApplied lane markings to {created} roads")

    print("\n" + "=" * 50)
    print("Lane Markings Complete!")
    print("=" * 50)

    return created


# Run in Blender
if __name__ == "__main__":
    apply_lane_markings()
