"""
Upgrade the procedural car node group to expose all standard inputs.
"""
import bpy
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from assets.node_group_upgrader import NodeGroupUpgrader, STANDARD_INPUTS


def main():
    blend_path = Path(__file__).parent.parent.parent / "assets" / "vehicles" / "procedural_car_wired.blend"
    print(f"\n{'='*60}")
    print(f"UPGRADING: {blend_path}")
    print(f"{'='*60}\n")

    # Open the blend file
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    # Find the car node group
    car_ng = bpy.data.node_groups.get("car")
    if not car_ng:
        print("ERROR: 'car' node group not found!")
        return

    print(f"Found node group: '{car_ng.name}'")
    print(f"  Nodes: {len(car_ng.nodes)}")

    # Get existing inputs using the correct API
    existing = []
    for item in car_ng.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            existing.append(item.name)
    print(f"  Existing inputs: {existing}")

    # Add missing inputs
    added = 0
    for input_name, spec in STANDARD_INPUTS.items():
        if input_name in existing:
            continue

        input_type = spec["type"]

        try:
            if input_type == "INT":
                socket = car_ng.interface.new_socket(
                    name=input_name,
                    in_out='INPUT',
                    socket_type='INT',
                )
                socket.default_value = spec.get("default", 1)

            elif input_type == "FLOAT":
                socket = car_ng.interface.new_socket(
                    name=input_name,
                    in_out='INPUT',
                    socket_type='FLOAT',
                )
                socket.default_value = spec.get("default", 0.5)

            elif input_type == "RGBA":
                socket = car_ng.interface.new_socket(
                    name=input_name,
                    in_out='INPUT',
                    socket_type='RGBA',
                )
                default = spec.get("default", (0.5, 0.5, 0.5, 1.0))
                socket.default_value = default

            elif input_type == "BOOLEAN":
                socket = car_ng.interface.new_socket(
                    name=input_name,
                    in_out='INPUT',
                    socket_type='BOOLEAN',
                )
                socket.default_value = spec.get("default", False)

            print(f"  Added: {input_name} ({input_type})")
            added += 1

        except Exception as e:
            print(f"  ERROR adding '{input_name}': {e}")

    # Save
    if added > 0:
        bpy.ops.wm.save_mainfile()
        print(f"\nSaved! Added {added} new inputs.")
    else:
        print(f"\nNo changes needed.")

    # Show final state
    print(f"\nFinal inputs:")
    for item in car_ng.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            print(f"  - {item.name}")


if __name__ == "__main__":
    main()
