"""
Scene operations - Clean scene management for deterministic builds.

Blender never stores intent. Every build starts from a known state.
"""

import bpy


def reset_scene():
    """
    Reset the scene to a clean state.

    - Deletes all objects
    - Purges orphan data blocks (meshes, materials, node_groups, images)
    - Ensures deterministic starting point
    """
    # Delete all objects
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Purge orphan data blocks
    for datablock in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.node_groups,
        bpy.data.images,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for item in list(datablock):
            if item.users == 0:
                datablock.remove(item)


def ensure_collection(name: str) -> bpy.types.Collection:
    """
    Get or create a collection by name.

    Args:
        name: Collection name

    Returns:
        The collection (linked to scene if newly created)
    """
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def unlink_from_scene(obj: bpy.types.Object) -> None:
    """Remove an object from the scene collection (but keep it in memory)."""
    try:
        bpy.context.scene.collection.objects.unlink(obj)
    except RuntimeError:
        pass  # Object not in scene collection


def select_objects(objs: list[bpy.types.Object]) -> None:
    """Select a list of objects, making the first one active."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    if objs:
        bpy.context.view_layer.objects.active = objs[0]
