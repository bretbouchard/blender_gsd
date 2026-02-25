"""
MSG-1998 Road System - Apply Geometry Nodes to Streets

This script applies the MSG geometry node groups to the actual road data
from the Streets_Roads collection.

Run this AFTER running setup_road_geonodes.py
"""

import bpy
import bmesh


def get_roads_collection():
    """Get or find the Streets_Roads collection."""
    # Try common names
    for name in ["Streets_Roads", "Streets", "Roads", "roads"]:
        if name in bpy.data.collections:
            return bpy.data.collections[name]

    # Check scene collection
    for coll in bpy.context.scene.collection.children:
        if "road" in coll.name.lower() or "street" in coll.name.lower():
            return coll

    return None


def convert_mesh_to_curve(mesh_obj):
    """Convert a mesh object to a curve object."""
    # Create a copy of the mesh data
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)

    # Create curve data
    curve_data = bpy.data.curves.new(f"{mesh_obj.name}_curve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2  # Low resolution for roads

    # Build adjacency map
    vert_edges = {v: [] for v in bm.verts}
    for edge in bm.edges:
        vert_edges[edge.verts[0]].append(edge)
        vert_edges[edge.verts[1]].append(edge)

    # Find connected chains (simple approach - find longest chain from each vertex)
    used_edges = set()

    def find_chain_from_edge(start_edge):
        """Find a connected chain starting from an edge."""
        chain = [start_edge.verts[0], start_edge.verts[1]]
        used_edges.add(start_edge)

        # Extend forward
        current = chain[-1]
        while True:
            found = False
            for edge in vert_edges[current]:
                if edge in used_edges:
                    continue
                other = edge.verts[1] if edge.verts[0] == current else edge.verts[0]
                if other not in chain:
                    chain.append(other)
                    used_edges.add(edge)
                    current = other
                    found = True
                    break
            if not found:
                break

        # Extend backward
        current = chain[0]
        while True:
            found = False
            for edge in vert_edges[current]:
                if edge in used_edges:
                    continue
                other = edge.verts[1] if edge.verts[0] == current else edge.verts[0]
                if other not in chain:
                    chain.insert(0, other)
                    used_edges.add(edge)
                    current = other
                    found = True
                    break
            if not found:
                break

        return chain

    # Create splines from edge chains
    for edge in bm.edges:
        if edge not in used_edges:
            chain = find_chain_from_edge(edge)
            if len(chain) >= 2:
                spline = curve_data.splines.new('POLY')
                spline.points.add(len(chain) - 1)  # Already has 1 point

                for i, vert in enumerate(chain):
                    co = mesh_obj.matrix_world @ vert.co
                    spline.points[i].co = (co.x, co.y, co.z, 1)

    bm.free()

    if len(curve_data.splines) == 0:
        bpy.data.curves.remove(curve_data)
        return None

    # Create curve object
    curve_obj = bpy.data.objects.new(f"{mesh_obj.name}_curve", curve_data)
    return curve_obj


def get_road_curves(convert_meshes=True):
    """Get all curve objects from the roads collection."""
    roads_coll = get_roads_collection()

    if not roads_coll:
        print("ERROR: Could not find roads collection")
        print("Available collections:")
        for coll in bpy.data.collections:
            print(f"  - {coll.name}")
        return []

    curves = []
    converted = []

    for obj in roads_coll.all_objects:
        if obj.type == 'CURVE':
            curves.append(obj)
        elif obj.type == 'MESH' and convert_meshes and len(obj.data.vertices) >= 2:
            # Convert mesh to curve
            print(f"  Converting: {obj.name}")
            curve_obj = convert_mesh_to_curve(obj)
            if curve_obj and len(curve_obj.data.splines) > 0:
                curves.append(curve_obj)
                converted.append(curve_obj)

    if converted:
        print(f"  Converted {len(converted)} meshes to curves")
        # Link converted curves to collection
        for curve in converted:
            roads_coll.objects.link(curve)

    print(f"Found {len(curves)} road curves")
    return curves


def join_road_curves(output_name="All_Roads_Curves"):
    """
    Join all road curves into a single object for geometry nodes.
    This is more efficient than processing each separately.
    """
    curves = get_road_curves()

    if not curves:
        print("No curves to join")
        return None

    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    # Select all curves
    for curve in curves:
        curve.select_set(True)

    # Set active object
    bpy.context.view_layer.objects.active = curves[0]

    # Join
    bpy.ops.object.join()

    # Rename
    joined = bpy.context.active_object
    joined.name = output_name

    print(f"Joined {len(curves)} curves into: {joined.name}")
    return joined


def create_road_output_object(name="Roads_GeoNodes"):
    """Create an empty object to hold the geometry nodes output."""
    # Create empty mesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # Link to scene
    bpy.context.collection.objects.link(obj)

    return obj


def apply_master_geonodes(target_obj, source_curves, road_width=10.0, sidewalk_width=2.0):
    """
    Apply the master geometry node setup to an object.

    Args:
        target_obj: Object to add modifier to
        source_curves: Source curve object or collection
        road_width: Width of road surface in meters
        sidewalk_width: Width of sidewalks on each side
    """

    # Check node group exists
    if "MSG_Road_System_Master" not in bpy.data.node_groups:
        print("ERROR: MSG_Road_System_Master not found")
        print("Run setup_road_geonodes.py first")
        return None

    # Add geometry nodes modifier
    mod = target_obj.modifiers.new(name="Road System", type='NODES')
    mod.node_group = bpy.data.node_groups["MSG_Road_System_Master"]

    # Set parameters
    # Input socket indices (0 = Road Curves, 1 = Road Width, etc.)
    # Note: Blender 5.0 uses different socket access

    # Find and set the Road Curves input
    for item in mod.node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Road Width":
                mod[item.identifier] = road_width
            elif item.name == "Sidewalk Width":
                mod[item.identifier] = sidewalk_width
            elif item.name == "Curb Height":
                mod[item.identifier] = 0.15

    # Set the geometry input (Road Curves)
    # This requires using the object as input
    if isinstance(source_curves, bpy.types.Object):
        # Set as input geometry
        for item in mod.node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name == "Road Curves":
                    # For geometry input, we need to use a different approach
                    # We'll use the Object Info node internally
                    pass

    print(f"Applied geometry nodes to: {target_obj.name}")
    return mod


def create_road_system_from_collection():
    """
    Main function: Create complete road system from Streets_Roads collection.
    """

    print("\n" + "=" * 50)
    print("Creating MSG Road System from Collection")
    print("=" * 50)

    # Step 1: Get roads collection
    roads_coll = get_roads_collection()
    if not roads_coll:
        print("ERROR: No roads collection found")
        return

    print(f"Using collection: {roads_coll.name}")

    # Step 2: Get all curves
    curves = get_road_curves()
    if not curves:
        print("ERROR: No curves found in collection")
        return

    # Step 3: Join curves into single object
    print("\nJoining curves...")
    joined = join_road_curves("MSG_Roads_Input")

    if not joined:
        print("ERROR: Failed to join curves")
        return

    # Step 4: Create output object
    print("\nCreating output object...")
    output = create_road_output_object("MSG_Roads_Output")

    # Step 5: Apply geometry nodes
    print("\nApplying geometry nodes...")
    apply_master_geonodes(output, joined)

    # Step 6: Create a collection for outputs
    if "Road_System_Output" not in bpy.data.collections:
        output_coll = bpy.data.collections.new("Road_System_Output")
        bpy.context.scene.collection.children.link(output_coll)
    else:
        output_coll = bpy.data.collections["Road_System_Output"]

    # Move objects to output collection
    for obj in [joined, output]:
        # Unlink from current collections
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        # Link to output collection
        output_coll.objects.link(obj)

    print("\n" + "=" * 50)
    print("Road system created!")
    print(f"  Input curves: {joined.name}")
    print(f"  Output object: {output.name}")
    print(f"  Output collection: {output_coll.name}")
    print("=" * 50)

    return output


def create_separate_road_objects():
    """
    Alternative: Apply geometry nodes to each road individually.
    Better for LOD and individual control, but more objects.
    """

    print("\n" + "=" * 50)
    print("Creating Individual Road Objects")
    print("=" * 50)

    curves = get_road_curves()
    if not curves:
        return

    # Check node group exists
    if "MSG_Road_Builder" not in bpy.data.node_groups:
        print("ERROR: Run setup_road_geonodes.py first")
        return

    # Create output collection
    if "Road_Objects" not in bpy.data.collections:
        output_coll = bpy.data.collections.new("Road_Objects")
        bpy.context.scene.collection.children.link(output_coll)
    else:
        output_coll = bpy.data.collections["Road_Objects"]

    created = 0
    for curve in curves:  # Process all roads
        # Skip if already has the modifier
        if any(m.type == 'NODES' and m.node_group and m.node_group.name == "MSG_Road_Builder" for m in curve.modifiers):
            print(f"  Skipping (already processed): {curve.name}")
            continue

        # Apply geometry nodes directly to the curve
        mod = curve.modifiers.new(name="Road", type='NODES')
        mod.node_group = bpy.data.node_groups["MSG_Road_Builder"]

        # Set road width based on name
        road_width = 10.0
        name_lower = curve.name.lower()
        if "avenue" in name_lower:
            road_width = 20.0
        elif "street" in name_lower:
            road_width = 12.0
        elif "lane" in name_lower:
            road_width = 8.0
        elif "plaza" in name_lower:
            road_width = 25.0
        elif "broadway" in name_lower:
            road_width = 22.0

        # Set parameters using Blender 5.0 interface
        for item in mod.node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name == "Road Width":
                    mod[item.identifier] = road_width
                elif item.name == "Sidewalk Width":
                    mod[item.identifier] = 2.0
                elif item.name == "Curb Height":
                    mod[item.identifier] = 0.15

        # Move to output collection
        for coll in curve.users_collection:
            if coll != output_coll:
                coll.objects.unlink(curve)
        if output_coll not in curve.users_collection:
            output_coll.objects.link(curve)

        created += 1
        print(f"  Created: {curve.name} (width={road_width}m)")

    print(f"\nCreated {created} road objects in: {output_coll.name}")
    return output_coll


# Run in Blender
if __name__ == "__main__":
    # Choose approach:
    # 1. Single object (faster, less control)
    # create_road_system_from_collection()

    # 2. Individual objects (more control, LOD support)
    create_separate_road_objects()
