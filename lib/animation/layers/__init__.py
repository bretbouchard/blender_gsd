"""
Animation Layers Module

Non-destructive animation editing with multiple layers.

Phase 13.7: Animation Layers (REQ-ANIM-09)

Usage:
    from lib.animation.layers import (
        AnimationLayerSystem,
        create_layer_system,
        LayerBlender,
        blend_layers,
        LayerMaskManager,
        apply_mask_to_layer,
    )

    # Create layer system
    system = create_layer_system("hero_rig", bone_names=["root", "spine", "head"])

    # Create layers
    system.create_layer("Base", LayerType.BASE)
    system.create_layer("Detail", LayerType.ADDITIVE)
    system.create_layer("Hand Animation", LayerType.OVERRIDE)

    # Add keyframes
    system.add_keyframe_to_layer("detail", frame=24, bone_name="spine",
                                  rotation=(0, 0, 5))

    # Set opacity
    system.set_layer_opacity("detail", 0.5)

    # Blend layers
    blender = LayerBlender(system)
    result = blender.evaluate(frame=24)
"""

from .layer_system import (
    AnimationLayerSystem,
    create_layer_system,
    get_layer_presets_directory,
    list_layer_presets,
    load_layer_preset,
    apply_layer_preset,
)

from .layer_blend import (
    LayerBlender,
    blend_layers,
    blend_layer_range,
)

from .layer_mask import (
    LayerMaskManager,
    apply_mask_to_layer,
    create_custom_mask,
    list_available_masks,
)


__all__ = [
    # Layer System
    'AnimationLayerSystem',
    'create_layer_system',
    'get_layer_presets_directory',
    'list_layer_presets',
    'load_layer_preset',
    'apply_layer_preset',

    # Layer Blending
    'LayerBlender',
    'blend_layers',
    'blend_layer_range',

    # Layer Masking
    'LayerMaskManager',
    'apply_mask_to_layer',
    'create_custom_mask',
    'list_available_masks',
]
