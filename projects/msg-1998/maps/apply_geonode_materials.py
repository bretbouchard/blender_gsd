"""
MSG-1998 Road System - Apply Materials to Geometry Nodes

Adds Set Material nodes to the existing geometry node groups
to assign materials to pavement, curbs, sidewalks, and markings.
"""

import bpy


def get_or_create_material(name, color, roughness=0.8, metallic=0.0):
    """Get existing material or create a new one."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic

    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_road_materials():
    """Create all road materials."""
    materials = {
        'asphalt': get_or_create_material(
            "M_Road_Asphalt",
            (0.08, 0.08, 0.09, 1.0),
            roughness=0.85
        ),
        'concrete': get_or_create_material(
            "M_Road_Concrete",
            (0.5, 0.48, 0.45, 1.0),
            roughness=0.9
        ),
        'curb': get_or_create_material(
            "M_Road_Curb",
            (0.4, 0.38, 0.36, 1.0),
            roughness=0.8
        ),
        'marking': get_or_create_material(
            "M_Road_LaneMarking",
            (0.95, 0.95, 0.95, 1.0),
            roughness=0.5
        ),
    }
    return materials


def add_material_to_node_group(node_group, material, output_socket_name, material_name):
    """
    Add a Set Material node before an output socket.
    """
    if node_group is None:
        return None

    nodes = node_group.nodes
    links = node_group.links

    # Find the output node
    output_node = None
    for node in nodes:
        if node.type == 'GROUP_OUTPUT':
            output_node = node
            break

    if output_node is None:
        print(f"  No output node found in {node_group.name}")
        return None

    # Find the socket
    target_socket = None
    for input_socket in output_node.inputs:
        if input_socket.name == output_socket_name:
            target_socket = input_socket
            break

    if target_socket is None:
        print(f"  No socket '{output_socket_name}' found")
        return None

    # Find what's connected to this socket
    if not target_socket.links:
        print(f"  Nothing connected to '{output_socket_name}'")
        return None

    source_link = target_socket.links[0]
    source_socket = source_link.from_socket

    # Create Set Material node
    set_mat = nodes.new('GeometryNodeSetMaterial')
    set_mat.name = f"SetMaterial_{material_name}"
    set_mat.label = f"Set {material_name}"
    set_mat.inputs['Material'].default_value = material

    # Position it before the output
    set_mat.location = (output_node.location.x - 200, output_node.location.y)

    # Reconnect: source -> Set Material -> Output
    links.new(source_socket, set_mat.inputs['Geometry'])
    links.new(set_mat.outputs['Geometry'], target_socket)

    print(f"  Added material '{material_name}' to output '{output_socket_name}'")
    return set_mat


def add_materials_to_road_builder(materials):
    """Add materials to MSG_Road_Builder node group."""
    ng = bpy.data.node_groups.get("MSG_Road_Builder")
    if not ng:
        print("MSG_Road_Builder not found")
        return

    print("\nAdding materials to MSG_Road_Builder...")

    # Add materials to each output
    add_material_to_node_group(ng, materials['asphalt'], 'Pavement', 'Asphalt')
    add_material_to_node_group(ng, materials['curb'], 'Curbs', 'Curb')
    add_material_to_node_group(ng, materials['concrete'], 'Sidewalks', 'Concrete')


def add_materials_to_lane_markings(materials):
    """Add materials to MSG_Lane_Markings node group."""
    ng = bpy.data.node_groups.get("MSG_Lane_Markings")
    if not ng:
        print("MSG_Lane_Markings not found")
        return

    print("\nAdding materials to MSG_Lane_Markings...")

    add_material_to_node_group(ng, materials['marking'], 'Markings', 'LaneMarking')


def apply_materials_to_geometry_nodes():
    """Main function to apply materials to all geometry node groups."""

    print("\n" + "=" * 50)
    print("Adding Materials to Geometry Nodes")
    print("=" * 50)

    # Create materials
    materials = create_road_materials()
    print(f"Created/verified {len(materials)} materials")

    # Add to node groups
    add_materials_to_road_builder(materials)
    add_materials_to_lane_markings(materials)

    print("\n" + "=" * 50)
    print("Materials Added to Geometry Nodes!")
    print("=" * 50)

    return materials


# Run in Blender
if __name__ == "__main__":
    apply_materials_to_geometry_nodes()
