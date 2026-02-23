import bpy

# Find import operators
print("import_scene operators:")
for op_name in dir(bpy.ops.import_scene):
    if not op_name.startswith('_'):
        print(f"  {op_name}")

print("\nAll import operators:")
for op_name in dir(bpy.ops.wm):
    if 'import' in op_name.lower():
        print(f"  wm.{op_name}")
