"""
Delete subway-related vertex groups from the Ways object
Run this in Blender
"""

import bpy

# Keywords that indicate subway/underground (to DELETE)
subway_keywords = [
    'subway', 'metro', 'mta', 'path', 'ind ', 'bmt ', 'irt ',
    'line', 'rail', 'station', 'terminal', 'tunnel', 'platform',
    'lower level', 'upper level', 'entrance', 'connector',
    'storage track', 'coach passage', 'mail platform',
    'herald square', 'times square', 'bryant park', 'pabt',
    'northeast corridor', 'hudson line', 'moynihan',
    'penn station', '33rd street (path', '34th street - herald',
    '34th street–herald', '42nd street', '42nd-Street',
]

# Get the Ways object
obj = bpy.data.objects.get("Ways")

if not obj:
    print("ERROR: 'Ways' object not found")
else:
    print(f"Processing '{obj.name}' with {len(obj.vertex_groups)} vertex groups")

    # Switch to object mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')

    groups_to_remove = []
    groups_to_keep = []

    for vg in obj.vertex_groups:
        name_lower = vg.name.lower()
        is_subway = False

        for keyword in subway_keywords:
            if keyword in name_lower:
                is_subway = True
                break

        if is_subway:
            groups_to_remove.append(vg.name)
        else:
            groups_to_keep.append(vg.name)

    print(f"\nRemoving {len(groups_to_remove)} subway groups:")
    for name in groups_to_remove[:20]:
        print(f"  - {name}")
    if len(groups_to_remove) > 20:
        print(f"  ... and {len(groups_to_remove) - 20} more")

    print(f"\nKeeping {len(groups_to_keep)} road groups:")
    for name in groups_to_keep[:20]:
        print(f"  + {name}")
    if len(groups_to_keep) > 20:
        print(f"  ... and {len(groups_to_keep) - 20} more")

    # Remove the subway groups
    for name in groups_to_remove:
        vg = obj.vertex_groups.get(name)
        if vg:
            obj.vertex_groups.remove(vg)

    print(f"\nDone! Now have {len(obj.vertex_groups)} vertex groups")
