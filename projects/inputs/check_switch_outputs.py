"""Check IndexSwitch output socket names."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Switch_Check")

print("="*60)
print("INDEX SWITCH NODE OUTPUTS")
print("="*60)

for node in ng.nodes:
    if node.type == 'INDEX_SWITCH':
        print(f"\n{node.name}:")
        print(f"  Type: {node.bl_idname}")
        print("  Outputs:")
        for out in node.outputs:
            print(f"    - {out.name} (type={out.type})")
        # Check if any outputs are connected
        for out in node.outputs:
            if out.links:
                for link in out.links:
                    print(f"    {out.name} -> {link.to_node.name}")

print("\n" + "="*60)
print("GEOMETRY NODE SWITCH OUTPUTS")
print("="*60)

for node in ng.nodes:
    if node.bl_idname == 'GeometryNodeSwitch':
        print(f"\n{node.name}:")
        print("  Outputs:")
        for out in node.outputs:
            print(f"    - {out.name} (type={out.type})")
