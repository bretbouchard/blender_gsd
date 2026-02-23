"""
Analyze the procedural car node group structure.
Run this in Blender to understand the node layout.
"""
import bpy

# Get the car node group
car_ng = bpy.data.node_groups.get('car')
if not car_ng:
    print('ERROR: car node group not found')
else:
    print('=== NODE GROUP INFO ===')
    print(f'Name: {car_ng.name}')
    print(f'Type: {car_ng.type}')
    print(f'Nodes: {len(car_ng.nodes)}')
    print(f'Links: {len(car_ng.links)}')

    # Check for interface (Blender 5.x)
    if hasattr(car_ng, 'interface'):
        print('\n=== INTERFACE (Blender 5.x) ===')
        for item in car_ng.interface.items_tree:
            print(f'  {item.item_type}: {item.name}')
    else:
        print('\n=== INPUTS (Old API) ===')
        for inp in car_ng.inputs:
            print(f'  {inp.name}: {inp.type}')
        print('\n=== OUTPUTS (Old API) ===')
        for out in car_ng.outputs:
            print(f'  {out.name}: {out.type}')

    print('\n=== NODE TYPES ===')
    node_types = {}
    for node in car_ng.nodes:
        t = node.bl_idname
        node_types[t] = node_types.get(t, 0) + 1

    for t, count in sorted(node_types.items(), key=lambda x: -x[1]):
        print(f'  {count:3d}x {t}')

    print('\n=== COLLECTION INFO NODES ===')
    for node in car_ng.nodes:
        if node.bl_idname == 'GeometryNodeCollectionInfo':
            # Check what collection it references
            if hasattr(node, 'inputs'):
                for inp in node.inputs:
                    if inp.name == 'Collection' and inp.links:
                        for link in inp.links:
                            print(f'  {node.name} <- {link.from_node.name}')
                    elif inp.name == 'Collection':
                        # Check default value
                        try:
                            coll = inp.default_value
                            if coll:
                                print(f'  {node.name} -> {coll.name}')
                        except:
                            pass

    print('\n=== RANDOM VALUE NODES ===')
    random_nodes = [n for n in car_ng.nodes if n.bl_idname == 'FunctionNodeRandomValue']
    print(f'Total: {len(random_nodes)}')

    # Show first few with connections
    for i, node in enumerate(random_nodes[:5]):
        print(f'\n  Random {i+1}: {node.name}')
        for output in node.outputs:
            if output.links:
                for link in output.links:
                    print(f'    -> {link.to_node.name} ({link.to_socket.name})')
