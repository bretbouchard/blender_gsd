"""
Wire Style Inputs for Deterministic Part Selection

The original node group uses Random Value nodes with seeded inputs.
The original inputs (front, back, wheels, etc.) feed into the SEED of random nodes.

Strategy:
1. The original inputs ALREADY control the random seed
2. We just need to make sure our new inputs (Front Base, Back Base, etc.)
   connect to the same Random Value nodes as the original inputs

The existing wiring:
- "front" -> Random Value.Seed
- "back" -> Random Value.002.Seed
- "wheels" -> Random Value.003.Seed
- etc.

The Random Value output goes to Instance Index.

To add our new inputs as alternatives, we could:
A) Connect new inputs to the same Random Value Seed (same behavior)
B) Replace Random Value output with direct input (no randomness)

Option B gives deterministic control, which is what we want.

Run in Blender with the car file open.
"""
import bpy


def analyze_random_to_instance_connections():
    """Map which Random Value nodes feed which Instance on Points nodes."""
    car_ng = bpy.data.node_groups.get('car')
    if not car_ng:
        return None, None

    # Map: Random Value node name -> Instance on Points node name
    random_to_instance = {}
    # Map: Instance on Points name -> Random Value name
    instance_to_random = {}

    for node in car_ng.nodes:
        if node.bl_idname == 'GeometryNodeInstanceOnPoints':
            idx_input = node.inputs.get('Instance Index')
            if idx_input and idx_input.links:
                for link in idx_input.links:
                    if link.from_node.bl_idname == 'FunctionNodeRandomValue':
                        random_to_instance[link.from_node.name] = node.name
                        instance_to_random[node.name] = link.from_node.name

    return random_to_instance, instance_to_random


def analyze_input_to_random_connections():
    """Map which Group Inputs feed which Random Value nodes."""
    car_ng = bpy.data.node_groups.get('car')
    if not car_ng:
        return None

    # Find Group Input node
    input_node = None
    for node in car_ng.nodes:
        if node.type == 'GROUP_INPUT':
            input_node = node
            break

    if not input_node:
        return None

    # Map: Input name -> [(Random Value node name, socket name)]
    input_to_random = {}

    for i, out in enumerate(input_node.outputs):
        if out.links:
            connections = []
            for link in out.links:
                if 'Random' in link.to_node.name:
                    connections.append((link.to_node.name, link.to_socket.name))
            if connections:
                input_to_random[out.name] = connections

    return input_to_random


def create_direct_wiring():
    """
    Replace Random Value -> Instance Index connections with direct Input -> Instance Index.

    This bypasses the randomness entirely, giving deterministic part selection.
    """
    car_ng = bpy.data.node_groups.get('car')
    if not car_ng:
        return False

    # Find Group Input node
    input_node = None
    for node in car_ng.nodes:
        if node.type == 'GROUP_INPUT':
            input_node = node
            break

    # Build input index map
    input_indices = {}
    for i, out in enumerate(input_node.outputs):
        input_indices[out.name] = i

    # Get the mappings
    random_to_instance, instance_to_random = analyze_random_to_instance_connections()
    input_to_random = analyze_input_to_random_connections()

    print("=== CURRENT WIRING ===")
    print("Input -> Random Value -> Instance on Points:")
    for inp, conns in input_to_random.items():
        for random_name, socket in conns:
            instance_name = random_to_instance.get(random_name, "???")
            print(f"  {inp} -> {random_name}.{socket} -> {instance_name}")

    # Now we'll add parallel connections from our new inputs
    # New input -> same Instance on Points (replacing random output)

    # Mapping of original input -> new input (for same part)
    # Note: wheels chains through Random Value.003 -> Random Value.005 -> Instance on Points.001
    # Note: central maps to Instance on Points.003 (but we don't have Central Style input)
    input_mapping = {
        'front': 'Front Base',
        'back': 'Back Base',
        'front headlights': 'Front Lights',
        'back headlights': 'Back Lights',
        'handles': 'Handle Style',
        'front bumper': 'Front Bumper',
        'back bumper': 'Back Bumper',
        'mirrors': 'Mirror Style',
        'grid': 'Grill Style',
    }

    # Special chain mappings for inputs that don't directly connect to Instance on Points
    # Format: (input_name, random_chain, instance_node)
    # where random_chain is list of Random Value nodes to follow
    chain_mappings = [
        # wheels -> Random Value.003 -> Random Value.005 -> Instance on Points.001
        ('wheels', ['Random Value.003', 'Random Value.005'], 'Instance on Points.001', 'Wheel Style'),
    ]

    changes_made = 0

    print("\n=== ADDING DIRECT WIRING ===")

    for orig_input, new_input in input_mapping.items():
        if orig_input not in input_to_random:
            print(f"  Original input '{orig_input}' has no random connections, skipping")
            continue

        if new_input not in input_indices:
            print(f"  New input '{new_input}' not found, skipping")
            continue

        # Get the Random Value and Instance nodes
        for random_name, socket in input_to_random[orig_input]:
            instance_name = random_to_instance.get(random_name)
            if not instance_name:
                continue

            instance_node = car_ng.nodes.get(instance_name)
            if not instance_node:
                continue

            # Find the Instance Index input
            idx_input = instance_node.inputs.get('Instance Index')
            if not idx_input:
                continue

            # Create a Subtract node (input is 1-indexed, Instance Index is 0-indexed)
            subtract_node = car_ng.nodes.new('ShaderNodeMath')
            subtract_node.name = f"Subtract1_{new_input.replace(' ', '_')}"
            subtract_node.label = f"{new_input} - 1"
            subtract_node.operation = 'SUBTRACT'
            subtract_node.inputs[1].default_value = 1.0
            subtract_node.location = (input_node.location.x + 200, input_node.location.y - changes_made * 80)

            # Connect new input -> Subtract -> Instance Index
            new_input_out = input_node.outputs[input_indices[new_input]]
            car_ng.links.new(new_input_out, subtract_node.inputs[0])
            car_ng.links.new(subtract_node.outputs[0], idx_input)

            print(f"  {new_input} -> Subtract1 -> {instance_name}.Instance Index")
            changes_made += 1

    # Handle chain mappings (wheels goes through 2 Random Values before hitting Instance)
    print("\n=== ADDING CHAIN WIRING ===")
    for orig_input, random_chain, instance_name, new_input in chain_mappings:
        if new_input not in input_indices:
            print(f"  New input '{new_input}' not found, skipping")
            continue

        instance_node = car_ng.nodes.get(instance_name)
        if not instance_node:
            print(f"  Instance node '{instance_name}' not found, skipping")
            continue

        # Find the Instance Index input
        idx_input = instance_node.inputs.get('Instance Index')
        if not idx_input:
            print(f"  Instance Index not found on {instance_name}, skipping")
            continue

        # Create a Subtract node (input is 1-indexed, Instance Index is 0-indexed)
        subtract_node = car_ng.nodes.new('ShaderNodeMath')
        subtract_node.name = f"Subtract1_{new_input.replace(' ', '_')}"
        subtract_node.label = f"{new_input} - 1"
        subtract_node.operation = 'SUBTRACT'
        subtract_node.inputs[1].default_value = 1.0
        subtract_node.location = (input_node.location.x + 200, input_node.location.y - changes_made * 80)

        # Connect new input -> Subtract -> Instance Index
        new_input_out = input_node.outputs[input_indices[new_input]]
        car_ng.links.new(new_input_out, subtract_node.inputs[0])
        car_ng.links.new(subtract_node.outputs[0], idx_input)

        print(f"  {new_input} -> Subtract1 -> {instance_name}.Instance Index (chain: {' -> '.join(random_chain)})")
        changes_made += 1

    print(f"\nTotal direct wiring changes: {changes_made}")
    return changes_made > 0


def verify_wiring():
    """Verify the wiring was successful."""
    car_ng = bpy.data.node_groups.get('car')

    # Find Group Input node
    input_node = None
    for node in car_ng.nodes:
        if node.type == 'GROUP_INPUT':
            input_node = node
            break

    print("\n=== VERIFICATION ===")
    print("New input connections:")

    new_inputs = ['Front Base', 'Back Base', 'Wheel Style', 'Front Lights',
                  'Back Lights', 'Handle Style', 'Front Bumper', 'Back Bumper',
                  'Mirror Style', 'Grill Style']

    for inp_name in new_inputs:
        for i, out in enumerate(input_node.outputs):
            if out.name == inp_name:
                if out.links:
                    for link in out.links:
                        print(f"  {inp_name} -> {link.to_node.name}")
                else:
                    print(f"  {inp_name}: NOT CONNECTED")
                break


def main():
    """Main function."""
    print("=" * 60)
    print("WIRING STYLE INPUTS FOR DETERMINISTIC SELECTION")
    print("=" * 60)

    print("\n1. Creating direct wiring from inputs to Instance Index...")
    create_direct_wiring()

    print("\n2. Verifying wiring...")
    verify_wiring()

    print("\n3. Saving modified file...")
    output_path = "//procedural_car_wired.blend"
    bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath(output_path))
    print(f"  Saved to: {output_path}")

    print("\n" + "=" * 60)
    print("WIRING COMPLETE")
    print("=" * 60)
    print("\nNow you can set Front Base = 5 to always get front style #5")
    print("instead of random selection.")


if __name__ == "__main__":
    main()
