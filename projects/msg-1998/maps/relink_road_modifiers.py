"""
MSG-1998 Road System - Relink Modifiers

The modifiers lost their node group references when we rebuilt the node groups.
This script re-links them.
"""

import bpy


def get_road_curves():
    """Get all road curves from all collections."""
    curves = []
    for coll in bpy.data.collections:
        for obj in coll.objects:
            if obj.type == 'CURVE' and obj not in curves:
                curves.append(obj)
    return curves


def get_road_width(obj):
    """Get road width from name."""
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


def relink_road_modifiers():
    """Re-link all road curve modifiers to the correct node groups."""

    print("\n" + "=" * 50)
    print("Re-linking Road Modifiers")
    print("=" * 50)

    # Get node groups
    road_builder = bpy.data.node_groups.get("MSG_Road_Builder")
    lane_markings = bpy.data.node_groups.get("MSG_Lane_Markings")

    if not road_builder:
        print("ERROR: MSG_Road_Builder not found!")
        return
    if not lane_markings:
        print("ERROR: MSG_Lane_Markings not found!")
        return

    print(f"Found node groups: {road_builder.name}, {lane_markings.name}")

    curves = get_road_curves()
    print(f"Found {len(curves)} road curves")

    fixed_road = 0
    fixed_markings = 0

    for curve in curves:
        road_width = get_road_width(curve)

        # Find and fix Road modifier
        for mod in curve.modifiers:
            if mod.type == 'NODES':
                if mod.name == "Road" or "Road" in mod.name:
                    if mod.node_group is None:
                        mod.node_group = road_builder
                        print(f"  Fixed Road modifier: {curve.name}")

                        # Set parameters
                        for item in road_builder.interface.items_tree:
                            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                                if item.name == "Road Width":
                                    mod[item.identifier] = road_width
                                elif item.name == "Sidewalk Width":
                                    mod[item.identifier] = 2.0
                                elif item.name == "Curb Height":
                                    mod[item.identifier] = 0.15

                        fixed_road += 1

                elif mod.name == "Lane Markings" or "Marking" in mod.name:
                    if mod.node_group is None:
                        mod.node_group = lane_markings
                        print(f"  Fixed Lane Markings modifier: {curve.name}")

                        # Set parameters
                        for item in lane_markings.interface.items_tree:
                            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                                if item.name == "Road Width":
                                    mod[item.identifier] = road_width
                                elif item.name == "Center Line Width":
                                    mod[item.identifier] = 0.15
                                elif item.name == "Edge Line Width":
                                    mod[item.identifier] = 0.10
                                elif item.name == "Z Offset":
                                    mod[item.identifier] = 0.02

                        fixed_markings += 1

    print(f"\nFixed {fixed_road} Road modifiers")
    print(f"Fixed {fixed_markings} Lane Markings modifiers")

    print("\n" + "=" * 50)
    print("Modifiers Re-linked!")
    print("=" * 50)


# Run in Blender
if __name__ == "__main__":
    relink_road_modifiers()
