"""
Light Linking Module

Provides selective light linking functionality for Blender 4.0+.
Light linking allows lights to only affect specific objects,
enabling fine-grained control over illumination.

This module wraps Blender's light_linking API for:
- Linking lights to specific collections (receiver)
- Setting up blocker collections
- Include/exclude object lists
- Querying current linking state

Usage:
    from lib.cinematic.light_linking import (
        link_light_to_collection,
        unlink_light_from_collection,
        set_light_include_only,
        set_light_exclude,
        get_light_links,
        clear_light_links,
    )

    # Light only affects specific objects
    set_light_include_only("key_light", ["product", "base"])

    # Light excludes certain objects
    set_light_exclude("rim_light", ["background_plane"])
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Set
from pathlib import Path

# Guarded bpy import
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


# Minimum Blender version for light linking
BLENDER_40_MIN = (4, 0, 0)


def _check_blender_version() -> bool:
    """
    Check if Blender version supports light linking.

    Returns:
        True if Blender 4.0+, False otherwise
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        return bpy.app.version >= BLENDER_40_MIN
    except Exception:
        return False


def _get_or_create_collection(name: str, parent: Any = None) -> Optional[Any]:
    """
    Get or create a collection by name.

    Args:
        name: Collection name
        parent: Parent collection (defaults to scene collection)

    Returns:
        Collection object or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Check if collection exists
        if name in bpy.data.collections:
            return bpy.data.collections[name]

        # Create new collection
        collection = bpy.data.collections.new(name)

        # Link to parent or scene
        if parent is None:
            if hasattr(bpy.context, "scene") and bpy.context.scene is not None:
                bpy.context.scene.collection.children.link(collection)
        else:
            parent.children.link(collection)

        return collection

    except Exception:
        return None


def link_light_to_collection(
    light_name: str,
    collection_name: str,
    link_type: str = "receiver"
) -> bool:
    """
    Link light to only affect objects in a collection.

    Light linking allows selective illumination - only objects in
    the specified collection will receive light from this light.

    Args:
        light_name: Name of the light object
        collection_name: Name of collection to link (created if not exists)
        link_type: "receiver" (objects receive light) or "blocker" (objects block light)

    Returns:
        True if successful, False if failed or Blender < 4.0
    """
    if not _check_blender_version():
        return False

    try:
        # Get light object
        if light_name not in bpy.data.objects:
            return False

        light_obj = bpy.data.objects[light_name]

        # Verify it's a light
        if light_obj.type != "LIGHT":
            return False

        # Check light linking support
        if not hasattr(light_obj, "light_linking"):
            return False

        # Get or create collection
        collection = _get_or_create_collection(collection_name)
        if collection is None:
            return False

        # Set collection based on link type
        if link_type == "receiver":
            light_obj.light_linking.receiver_collection = collection
        elif link_type == "blocker":
            if hasattr(light_obj.light_linking, "blocker_collection"):
                light_obj.light_linking.blocker_collection = collection

        return True

    except Exception:
        return False


def unlink_light_from_collection(
    light_name: str,
    collection_name: str
) -> bool:
    """
    Remove light link from collection.

    Removes the light-to-collection link, restoring default behavior
    where the light affects all objects.

    Args:
        light_name: Name of the light object
        collection_name: Name of linked collection

    Returns:
        True if successful, False if failed
    """
    if not _check_blender_version():
        return False

    try:
        # Get light object
        if light_name not in bpy.data.objects:
            return False

        light_obj = bpy.data.objects[light_name]

        if not hasattr(light_obj, "light_linking"):
            return False

        # Check if this collection is the receiver
        receiver = light_obj.light_linking.receiver_collection
        if receiver is not None and receiver.name == collection_name:
            light_obj.light_linking.receiver_collection = None

        # Check if this collection is the blocker
        if hasattr(light_obj.light_linking, "blocker_collection"):
            blocker = light_obj.light_linking.blocker_collection
            if blocker is not None and blocker.name == collection_name:
                light_obj.light_linking.blocker_collection = None

        return True

    except Exception:
        return False


def set_light_include_only(
    light_name: str,
    object_names: List[str]
) -> bool:
    """
    Set light to only affect specified objects.

    Creates a receiver collection containing only the specified objects.
    All other objects will not be affected by this light.

    Args:
        light_name: Name of the light object
        object_names: List of object names that should receive light

    Returns:
        True if successful, False if failed
    """
    if not _check_blender_version():
        return False

    try:
        # Get light object
        if light_name not in bpy.data.objects:
            return False

        light_obj = bpy.data.objects[light_name]

        if light_obj.type != "LIGHT":
            return False

        if not hasattr(light_obj, "light_linking"):
            return False

        # Create receiver collection
        receiver_name = f"{light_name}_receivers"
        receiver_coll = _get_or_create_collection(receiver_name)

        if receiver_coll is None:
            return False

        # Clear existing objects from collection
        for obj in receiver_coll.objects:
            receiver_coll.objects.unlink(obj)

        # Add specified objects to collection
        for obj_name in object_names:
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                # Only link if not already in collection
                if obj_name not in receiver_coll.objects:
                    receiver_coll.objects.link(obj)

        # Set as receiver collection
        light_obj.light_linking.receiver_collection = receiver_coll

        return True

    except Exception:
        return False


def set_light_exclude(
    light_name: str,
    object_names: List[str]
) -> bool:
    """
    Set light to exclude specified objects.

    Creates a blocker collection containing the specified objects.
    These objects will block light but won't receive it.

    Note: In Blender's implementation, blockers affect shadowing
    but may not exclude illumination. For full exclusion, use
    include-only mode instead.

    Args:
        light_name: Name of the light object
        object_names: List of object names to exclude

    Returns:
        True if successful, False if failed
    """
    if not _check_blender_version():
        return False

    try:
        # Get light object
        if light_name not in bpy.data.objects:
            return False

        light_obj = bpy.data.objects[light_name]

        if light_obj.type != "LIGHT":
            return False

        if not hasattr(light_obj, "light_linking"):
            return False

        # Check for blocker collection support
        if not hasattr(light_obj.light_linking, "blocker_collection"):
            return False

        # Create blocker collection
        blocker_name = f"{light_name}_blockers"
        blocker_coll = _get_or_create_collection(blocker_name)

        if blocker_coll is None:
            return False

        # Clear existing objects from collection
        for obj in list(blocker_coll.objects):
            blocker_coll.objects.unlink(obj)

        # Add specified objects to collection
        for obj_name in object_names:
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                if obj_name not in blocker_coll.objects:
                    blocker_coll.objects.link(obj)

        # Set as blocker collection
        light_obj.light_linking.blocker_collection = blocker_coll

        return True

    except Exception:
        return False


def get_light_links(light_name: str) -> Dict[str, Any]:
    """
    Get light linking configuration for a light.

    Returns information about receiver and blocker collections
    associated with this light.

    Args:
        light_name: Name of the light object

    Returns:
        Dictionary containing:
        - has_linking: True if light has any linking
        - receiver_collection: Name of receiver collection or None
        - blocker_collection: Name of blocker collection or None
        - receiver_objects: List of object names in receiver collection
        - blocker_objects: List of object names in blocker collection
        - supported: True if light linking is supported
    """
    result = {
        "has_linking": False,
        "receiver_collection": None,
        "blocker_collection": None,
        "receiver_objects": [],
        "blocker_objects": [],
        "supported": _check_blender_version(),
    }

    if not _check_blender_version():
        return result

    try:
        # Get light object
        if light_name not in bpy.data.objects:
            return result

        light_obj = bpy.data.objects[light_name]

        if light_obj.type != "LIGHT":
            return result

        if not hasattr(light_obj, "light_linking"):
            return result

        linking = light_obj.light_linking

        # Get receiver collection
        receiver = linking.receiver_collection
        if receiver is not None:
            result["receiver_collection"] = receiver.name
            result["receiver_objects"] = [obj.name for obj in receiver.objects]
            result["has_linking"] = True

        # Get blocker collection
        if hasattr(linking, "blocker_collection"):
            blocker = linking.blocker_collection
            if blocker is not None:
                result["blocker_collection"] = blocker.name
                result["blocker_objects"] = [obj.name for obj in blocker.objects]
                result["has_linking"] = True

        return result

    except Exception:
        return result


def clear_light_links(light_name: str) -> bool:
    """
    Clear all light linking for a light.

    Removes receiver and blocker collections, restoring default
    behavior where the light affects all objects.

    Args:
        light_name: Name of the light object

    Returns:
        True if successful, False if failed
    """
    if not _check_blender_version():
        return False

    try:
        # Get light object
        if light_name not in bpy.data.objects:
            return False

        light_obj = bpy.data.objects[light_name]

        if not hasattr(light_obj, "light_linking"):
            return False

        linking = light_obj.light_linking

        # Clear receiver collection
        if linking.receiver_collection is not None:
            linking.receiver_collection = None

        # Clear blocker collection
        if hasattr(linking, "blocker_collection"):
            if linking.blocker_collection is not None:
                linking.blocker_collection = None

        return True

    except Exception:
        return False


def get_objects_affected_by_light(light_name: str) -> List[str]:
    """
    Get list of objects affected by a light.

    If light has linking, returns only objects in receiver collection.
    Otherwise returns all objects in scene (default behavior).

    Args:
        light_name: Name of the light object

    Returns:
        List of object names affected by this light
    """
    links = get_light_links(light_name)

    if not links["has_linking"]:
        # No linking - return all objects
        if BLENDER_AVAILABLE:
            try:
                return [obj.name for obj in bpy.data.objects if obj.type == "MESH"]
            except Exception:
                pass
        return []

    # Return receiver objects
    return links["receiver_objects"]


def copy_light_linking(
    source_light: str,
    target_light: str
) -> bool:
    """
    Copy light linking configuration from one light to another.

    Useful for creating lights with matching linking behavior.

    Args:
        source_light: Name of light to copy from
        target_light: Name of light to copy to

    Returns:
        True if successful, False if failed
    """
    if not _check_blender_version():
        return False

    try:
        # Get source links
        source_links = get_light_links(source_light)

        if not source_links["has_linking"]:
            # No linking to copy - just clear target
            return clear_light_links(target_light)

        # Apply same linking to target
        if source_links["receiver_objects"]:
            set_light_include_only(target_light, source_links["receiver_objects"])

        if source_links["blocker_objects"]:
            set_light_exclude(target_light, source_links["blocker_objects"])

        return True

    except Exception:
        return False


def is_light_linking_supported() -> bool:
    """
    Check if light linking is supported in current Blender version.

    Returns:
        True if Blender 4.0+ with light linking support
    """
    return _check_blender_version()
