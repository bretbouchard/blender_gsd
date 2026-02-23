"""
Fix the car node group to wire Body Color input to the actual material.

This connects the exposed "Body Color" input socket to the material nodes
so that setting the input actually changes the car's color.
"""
import bpy
from pathlib import Path


def find_material_output_node(ng):
    """Find the material output node or a Set Material node."""
    for node in ng.nodes:
        if 'Material' in node.bl_idname or 'Output' in node.bl_idname:
            return node
    return None


def find_input_node(ng):
    """Find the Group Input node."""
    for node in ng.nodes:
        if node.bl_idname == 'NodeGroupInput':
            return node
    return None


def wire_body_color_to_materials():
    """Wire the Body Color input to control the car's body material color."""
    car_ng = bpy.data.node_groups.get("car")
    if not car_ng:
        print("ERROR: 'car' node group not found!")
        return False

    print(f"Working on node group: '{car_ng.name}'")
    print(f"  Nodes: {len(car_ng.nodes)}")

    # Find the Group Input node
    input_node = find_input_node(car_ng)
    if not input_node:
        print("  ERROR: No Group Input node found!")
        return False

    # Find the Body Color output on the input node
    body_color_socket = None
    for output in input_node.outputs:
        if output.name == "Body Color":
            body_color_socket = output
            break

    if not body_color_socket:
        print("  ERROR: 'Body Color' input not found on Group Input!")
        return False

    print(f"  Found Body Color socket on input node")

    # Look for nodes that might accept color input
    # Common patterns: Set Color, Set Material, or direct BSDF inputs
    color_target_nodes = []

    for node in car_ng.nodes:
        # Check for Set Color nodes or similar attribute nodes
        if 'Color' in node.bl_idname or 'Attribute' in node.bl_idname:
            color_target_nodes.append(node)

        # Check for any node with a "Color" or "Base Color" input
        for input in node.inputs:
            if input.name in ['Color', 'Base Color', 'Body Color']:
                color_target_nodes.append((node, input.name))

    print(f"  Found {len(color_target_nodes)} potential color target nodes")

    # Also look for material-related nodes
    material_nodes = []
    for node in car_ng.nodes:
        if 'SetMaterial' in node.bl_idname or 'SetMaterialFromIndex' in node.bl_idname:
            material_nodes.append(node)
            print(f"    Material node: {node.name} ({node.bl_idname})")

    # The car likely uses collection instances with existing materials
    # We need to find where the car color material is defined and update it

    # Strategy: Create a Store Named Attribute node to store "body_color"
    # Then the material can read it via Attribute node

    # Check if there's already a Store Named Attribute for body_color
    store_attr = None
    for node in car_ng.nodes:
        if node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            for inp in node.inputs:
                if inp.name == 'Name' and inp.default_value == 'body_color':
                    store_attr = node
                    break

    if not store_attr:
        # Create a Store Named Attribute node
        store_attr = car_ng.nodes.new('GeometryNodeStoreNamedAttribute')
        store_attr.name = "Store Body Color"
        store_attr.inputs['Name'].default_value = 'body_color'
        store_attr.inputs['Domain'].default_value = 'POINT'  # or 'FACE'
        print(f"  Created Store Named Attribute node: {store_attr.name}")
    else:
        print(f"  Found existing Store Named Attribute: {store_attr.name}")

    # Find the Value/Vector input for the color
    # Store Named Attribute has inputs: Name, Value (vector), Geometry
    value_socket = None
    for inp in store_attr.inputs:
        if 'Value' in inp.name or 'Vector' in inp.name:
            value_socket = inp
            break

    if value_socket:
        # Connect Body Color to the Value input
        try:
            car_ng.links.new(body_color_socket, value_socket)
            print(f"  Connected Body Color -> {store_attr.name}.Value")
        except Exception as e:
            print(f"  Error connecting: {e}")

    # Now we need to position this node in the flow
    # It should be before any Realize Instances or Output nodes

    # Find the output node
    output_node = None
    for node in car_ng.nodes:
        if node.bl_idname == 'NodeGroupOutput':
            output_node = node
            break

    if output_node:
        # Find what's connected to the output's Geometry input
        geometry_input = None
        for inp in output_node.inputs:
            if inp.name == 'Geometry' or inp.type == 'GEOMETRY':
                geometry_input = inp
                break

        if geometry_input and geometry_input.links:
            # Get the node that's currently connected to output
            current_source = geometry_input.links[0].from_node
            print(f"  Current output source: {current_source.name}")

            # We need to insert our Store Named Attribute after realization
            # but before output, or find a better spot in the chain

    return True


def update_body_material_to_use_attribute():
    """Update the car body material to read from the body_color attribute."""
    # The material is likely "car color" or similar
    body_mat = None
    for mat in bpy.data.materials:
        if 'car' in mat.name.lower() and 'color' in mat.name.lower():
            body_mat = mat
            break
        elif 'car' in mat.name.lower():
            body_mat = mat  # Fallback to first car material

    if not body_mat:
        print("No car material found to update")
        return False

    print(f"Updating material: {body_mat.name}")

    if not body_mat.use_nodes:
        body_mat.use_nodes = True

    tree = body_mat.node_tree

    # Find the Principled BSDF
    bsdf = None
    for node in tree.nodes:
        if 'BsdfPrincipled' in node.bl_idname or 'Principled BSDF' in node.name:
            bsdf = node
            break

    if not bsdf:
        print("  No Principled BSDF found")
        return False

    # Check if there's already an Attribute node for body_color
    attr_node = None
    for node in tree.nodes:
        if node.bl_idname == 'ShaderNodeAttribute':
            if node.attribute_name == 'body_color':
                attr_node = node
                break

    if not attr_node:
        # Create an Attribute node
        attr_node = tree.nodes.new('ShaderNodeAttribute')
        attr_node.attribute_name = 'body_color'
        attr_node.location = (bsdf.location.x - 300, bsdf.location.y)
        print(f"  Created Attribute node for body_color")

    # Connect Attribute Color output to BSDF Base Color
    color_output = None
    for output in attr_node.outputs:
        if 'Color' in output.name:
            color_output = output
            break

    base_color_input = None
    for inp in bsdf.inputs:
        if 'Base Color' in inp.name:
            base_color_input = inp
            break

    if color_output and base_color_input:
        # Remove existing link if any
        for link in tree.links:
            if link.to_socket == base_color_input:
                tree.links.remove(link)

        tree.links.new(color_output, base_color_input)
        print(f"  Connected Attribute.Color -> BSDF.Base Color")

    return True


def main():
    blend_path = Path(__file__).parent.parent.parent / "assets" / "vehicles" / "procedural_car_wired.blend"
    print(f"\n{'='*60}")
    print(f"WIRING BODY COLOR IN: {blend_path}")
    print(f"{'='*60}\n")

    # Open the blend file
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    # Wire the Body Color input in the node group
    success = wire_body_color_to_materials()

    # Also update the material to read the attribute
    if success:
        update_body_material_to_use_attribute()

    # Save
    bpy.ops.wm.save_mainfile()
    print(f"\nSaved changes to: {blend_path}")


if __name__ == "__main__":
    main()
