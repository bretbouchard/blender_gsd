"""
MSG-1998 Road System - Fix Road Display

The geometry node modifier needs the input geometry connected.
This script ensures the modifiers are properly configured.
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


def fix_road_modifiers():
    """Fix all road curve modifiers to properly use geometry nodes."""

    print("\n" + "=" * 50)
    print("Fixing Road Modifiers")
    print("=" * 50)

    curves = get_road_curves()
    print(f"Found {len(curves)} road curves")

    fixed = 0
    for curve in curves:
        # Check for geometry nodes modifiers
        for mod in curve.modifiers:
            if mod.type == 'NODES':
                ng = mod.node_group
                if ng and "MSG_Road" in ng.name:
                    # The issue is the input socket connection
                    # In Blender 5.0, we need to ensure the geometry input works

                    # Get the input socket identifier
                    for item in ng.interface.items_tree:
                        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                            if item.name == "Road Curves" or "Curve" in item.name or item.socket_type == 'NodeSocketGeometry':
                                # This should be auto-connected to the curve
                                print(f"  {curve.name}: Input '{item.name}' identifier={item.identifier}")
                    fixed += 1

    print(f"\nChecked {fixed} modifiers")

    # The real issue: Geometry nodes on curves use the curve itself as input
    # We need to make sure the node group expects this

    return fixed


def verify_node_groups():
    """Check that node groups exist and have correct structure."""

    print("\n" + "=" * 50)
    print("Verifying Node Groups")
    print("=" * 50)

    for ng_name in ["MSG_Road_Builder", "MSG_Lane_Markings"]:
        if ng_name in bpy.data.node_groups:
            ng = bpy.data.node_groups[ng_name]
            print(f"\n{ng_name}:")
            print(f"  Nodes: {len(ng.nodes)}")

            # Check inputs
            for item in ng.interface.items_tree:
                if item.item_type == 'SOCKET':
                    direction = "INPUT" if item.in_out == 'INPUT' else "OUTPUT"
                    print(f"  {direction}: {item.name} ({item.socket_type})")
        else:
            print(f"\n{ng_name}: NOT FOUND")


def test_single_road():
    """Test a single road to see what's happening."""

    curves = get_road_curves()
    if not curves:
        print("No curves found!")
        return

    curve = curves[0]
    print(f"\nTesting: {curve.name}")
    print(f"  Type: {curve.type}")
    print(f"  Modifiers: {len(curve.modifiers)}")

    for mod in curve.modifiers:
        print(f"  Modifier: {mod.name} ({mod.type})")
        if mod.type == 'NODES':
            print(f"    Node Group: {mod.node_group.name if mod.node_group else 'None'}")

            # Check if modifier is affecting the curve
            # In Blender, geometry nodes on a curve should process the curve


def main():
    verify_node_groups()
    fix_road_modifiers()
    test_single_road()

    print("\n" + "=" * 50)
    print("Debug Info Complete")
    print("=" * 50)


# Run in Blender
if __name__ == "__main__":
    main()
