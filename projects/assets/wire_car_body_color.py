"""
Wire Body Color input to control car body material color.

This adds a SetMaterial node and connects it to a material that reads
the Body Color attribute from the geometry nodes input.
"""
import bpy
from pathlib import Path
from mathutils import Vector


def fix_car_body_color():
    """Add proper material control to the car node group."""
    car_ng = bpy.data.node_groups.get("car")
    if not car_ng:
        print("ERROR: 'car' node group not found!")
        return False

    print(f"Working on: '{car_ng.name}'")

    # Find the input node
    input_node = None
    for node in car_ng.nodes:
        if node.bl_idname == 'NodeGroupInput':
            input_node = node
            break

    if not input_node:
        print("  ERROR: No Group Input node!")
        return False

    # Find Body Color output
    body_color_socket = None
    for output in input_node.outputs:
        if output.name == "Body Color":
            body_color_socket = output
            break

    if not body_color_socket:
        print("  ERROR: No Body Color input!")
        return False

    print(f"  Found Body Color on input node")

    # Find the output node and what feeds it
    output_node = None
    for node in car_ng.nodes:
        if node.bl_idname == 'NodeGroupOutput':
            output_node = node
            break

    if not output_node:
        print("  ERROR: No Group Output node!")
        return False

    # Find what connects to the output geometry
    current_source = None
    current_source_socket = None
    for inp in output_node.inputs:
        if inp.name == 'Geometry' or inp.type == 'GEOMETRY':
            if inp.links:
                current_source = inp.links[0].from_node
                current_source_socket = inp.links[0].from_socket
                print(f"  Output fed by: {current_source.name}.{current_source_socket.name}")
            break

    # Check if there's already a SetMaterial node in the chain
    set_material_node = None
    for node in car_ng.nodes:
        if 'SetMaterial' in node.bl_idname:
            set_material_node = node
            print(f"  Found existing SetMaterial: {set_material_node.name}")
            break

    if not set_material_node:
        # Create a SetMaterial node
        set_material_node = car_ng.nodes.new('GeometryNodeSetMaterial')
        set_material_node.name = "Set Body Color"
        print(f"  Created SetMaterial node")

        # Position it before the output
        if current_source:
            set_material_node.location = Vector((
                (current_source.location.x + output_node.location.x) / 2,
                (current_source.location.y + output_node.location.y) / 2
            ))
        else:
            set_material_node.location = Vector((-200, 0))

    # Get or create the body color material
    body_mat = bpy.data.materials.get("car_body_procedural")
    if not body_mat:
        body_mat = bpy.data.materials.new("car_body_procedural")
        body_mat.use_nodes = True
        print(f"  Created material: car_body_procedural")

    # Setup material to read from attribute
    tree = body_mat.node_tree

    # Clear existing nodes except output
    nodes_to_remove = [n for n in tree.nodes if n.bl_idname != 'NodeMaterialOutput']
    for n in nodes_to_remove:
        tree.nodes.remove(n)

    # Add Attribute node
    attr_node = tree.nodes.new('ShaderNodeAttribute')
    attr_node.attribute_name = 'body_color'
    attr_node.location = (-400, 0)

    # Add Principled BSDF
    bsdf_node = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf_node.location = (-100, 0)

    # Add Material Output
    output_mat = tree.nodes.get('Material Output')
    if not output_mat:
        output_mat = tree.nodes.new('ShaderNodeOutputMaterial')
    output_mat.location = (200, 0)

    # Connect Attribute -> BSDF Base Color
    tree.links.new(attr_node.outputs['Color'], bsdf_node.inputs['Base Color'])

    # Connect BSDF -> Output
    tree.links.new(bsdf_node.outputs['BSDF'], output_mat.inputs['Surface'])

    print(f"  Setup material to read 'body_color' attribute")

    # Add StoreNamedAttribute node for body_color
    store_color = None
    for node in car_ng.nodes:
        if node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            for inp in node.inputs:
                if inp.name == 'Name' and inp.default_value == 'body_color':
                    store_color = node
                    break

    if not store_color:
        store_color = car_ng.nodes.new('GeometryNodeStoreNamedAttribute')
        store_color.name = "Store Body Color"
        store_color.inputs['Name'].default_value = 'body_color'
        # Domain is set via enum in Blender 5.x, skip if not available
        try:
            store_color.inputs['Domain'].default_value = 'FACE'
        except KeyError:
            pass  # Blender 5.x uses different API
        print(f"  Created StoreNamedAttribute for body_color")

        # Position it near the SetMaterial
        store_color.location = Vector((
            set_material_node.location.x - 300,
            set_material_node.location.y
        ))

    # Connect Body Color input to StoreNamedAttribute Value
    value_input = None
    for inp in store_color.inputs:
        if 'Value' in inp.name and inp.type == 'RGBA':
            value_input = inp
            break

    if value_input:
        # Remove existing links to this input
        for link in list(car_ng.links):
            if link.to_socket == value_input:
                car_ng.links.remove(link)

        # Connect Body Color -> Store Value
        car_ng.links.new(body_color_socket, value_input)
        print(f"  Connected Body Color -> Store Body Color.Value")

    # Now wire up the geometry flow:
    # current_source -> store_color -> set_material -> output

    # Connect current source geometry to store_color
    geo_input = None
    for inp in store_color.inputs:
        if inp.name == 'Geometry' or inp.type == 'GEOMETRY':
            geo_input = inp
            break

    if geo_input and current_source_socket:
        # Remove existing link to output
        for link in list(car_ng.links):
            if link.to_node == output_node and link.to_socket.name == 'Geometry':
                car_ng.links.remove(link)

        # Connect source -> store_color
        car_ng.links.new(current_source_socket, geo_input)

        # Connect store_color -> set_material
        store_geo_output = None
        for out in store_color.outputs:
            if out.name == 'Geometry':
                store_geo_output = out
                break

        set_mat_geo_input = None
        for inp in set_material_node.inputs:
            if inp.name == 'Geometry' or inp.type == 'GEOMETRY':
                set_mat_geo_input = inp
                break

        if store_geo_output and set_mat_geo_input:
            car_ng.links.new(store_geo_output, set_mat_geo_input)

        # Connect set_material -> output
        set_mat_geo_output = None
        for out in set_material_node.outputs:
            if out.name == 'Geometry':
                set_mat_geo_output = out
                break

        output_geo_input = None
        for inp in output_node.inputs:
            if inp.name == 'Geometry' or inp.type == 'GEOMETRY':
                output_geo_input = inp
                break

        if set_mat_geo_output and output_geo_input:
            car_ng.links.new(set_mat_geo_output, output_geo_input)

        print(f"  Wired geometry flow: source -> store_color -> set_material -> output")

    # Set the material on the SetMaterial node
    mat_input = None
    for inp in set_material_node.inputs:
        if 'Material' in inp.name or inp.type == 'MATERIAL':
            mat_input = inp
            break

    if mat_input:
        mat_input.default_value = body_mat
        print(f"  Set material to: {body_mat.name}")

    return True


def main():
    blend_path = Path(__file__).parent.parent.parent / "assets" / "vehicles" / "procedural_car_wired.blend"
    print(f"\n{'='*60}")
    print(f"WIRING BODY COLOR: {blend_path}")
    print(f"{'='*60}\n")

    # Open the blend file
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    # Fix the body color wiring
    success = fix_car_body_color()

    if success:
        # Save
        bpy.ops.wm.save_mainfile()
        print(f"\n{'='*60}")
        print(f"SAVED: {blend_path}")
        print(f"{'='*60}")
    else:
        print(f"\nFailed to update!")


if __name__ == "__main__":
    main()
