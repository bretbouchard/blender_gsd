"""
Generate Eyes - Main Generation Script

Orchestrates eye cluster generation with full parameter control.
Can be run directly in Blender or imported as a module.
"""

import bpy
import yaml
import math
from pathlib import Path
from mathutils import Vector
from typing import Optional, Dict, Any

# Import local modules
from .eye_geometry import create_eye_node_group, create_single_eye
from .eye_distribution import create_distribution_node_group, create_eyes_on_sphere


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration from YAML file.

    Args:
        config_path: Path to config file, defaults to default_eyes.yaml

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "configs" / "default_eyes.yaml"
    else:
        config_path = Path(config_path)

    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        # Return default configuration
        return {
            'geometry': {
                'count': 100,
                'distribution': 'sphere',
                'size_min': 0.1,
                'size_max': 1.0,
                'radius': 10.0,
                'seed': 42,
            },
            'eye_structure': {
                'pupil_ratio': 0.3,
                'iris_ratio': 0.6,
                'subdivisions': 2,
            },
        }


def generate_eyes(
    count: int = 100,
    distribution: str = "sphere",
    size_min: float = 0.1,
    size_max: float = 1.0,
    radius: float = 10.0,
    seed: int = 42,
    pupil_ratio: float = 0.3,
    iris_ratio: float = 0.6,
    subdivisions: int = 2,
    name: str = "EyeCluster",
    config_path: Optional[str] = None,
) -> bpy.types.Object:
    """
    Generates a complete eye cluster with all parameters.

    Args:
        count: Number of eyes (12 to 1,000,000)
        distribution: Distribution type ('sphere', 'random', 'grid')
        size_min: Minimum eye size
        size_max: Maximum eye size
        radius: Distribution sphere radius
        seed: Random seed for reproducibility
        pupil_ratio: Pupil size relative to eye
        iris_ratio: Iris size relative to eye
        subdivisions: Mesh detail level
        name: Object name
        config_path: Optional path to config file (overrides other params)

    Returns:
        The generated eye cluster object
    """
    # Load from config if provided
    if config_path:
        config = load_config(config_path)
        geo = config.get('geometry', {})
        eye_struct = config.get('eye_structure', {})

        count = geo.get('count', count)
        distribution = geo.get('distribution', distribution)
        size_min = geo.get('size_min', size_min)
        size_max = geo.get('size_max', size_max)
        radius = geo.get('radius', radius)
        seed = geo.get('seed', seed)
        pupil_ratio = eye_struct.get('pupil_ratio', pupil_ratio)
        iris_ratio = eye_struct.get('iris_ratio', iris_ratio)
        subdivisions = eye_struct.get('subdivisions', subdivisions)

    # Validate parameters
    count = max(12, min(count, 1_000_000))
    size_min = max(0.001, size_min)
    size_max = max(size_min, size_max)
    radius = max(0.1, radius)
    pupil_ratio = max(0.0, min(pupil_ratio, 1.0))
    iris_ratio = max(pupil_ratio, min(iris_ratio, 1.0))  # Iris must be larger than pupil
    subdivisions = max(0, min(subdivisions, 6))

    # Clean up existing object with same name
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    # Ensure node groups exist
    create_eye_node_group()
    create_distribution_node_group()

    # Create the eye cluster
    if distribution == "sphere":
        obj = create_eyes_on_sphere(
            count=count,
            radius=radius,
            size_min=size_min,
            size_max=size_max,
            seed=seed,
            name=name
        )
    else:
        # Fallback to sphere distribution
        obj = create_eyes_on_sphere(
            count=count,
            radius=radius,
            size_min=size_min,
            size_max=size_max,
            seed=seed,
            name=name
        )

    print(f"Generated eye cluster: {name}")
    print(f"  Count: {count}")
    print(f"  Radius: {radius}")
    print(f"  Size range: {size_min} - {size_max}")
    print(f"  Seed: {seed}")

    return obj


def generate_single_test_eye(
    size: float = 1.0,
    location: Vector = None,
    name: str = "TestEye"
) -> bpy.types.Object:
    """
    Generates a single eye for testing/preview.

    Args:
        size: Eye size
        location: World position
        name: Object name

    Returns:
        The generated eye object
    """
    return create_single_eye(
        size=size,
        pupil_ratio=0.3,
        iris_ratio=0.6,
        subdivisions=2,
        location=location or Vector((0, 0, 0)),
        name=name
    )


def clear_all_eyes():
    """Removes all eye-related objects from the scene."""
    to_remove = []
    for obj in bpy.data.objects:
        if "Eye" in obj.name or "eye" in obj.name:
            to_remove.append(obj)

    for obj in to_remove:
        bpy.data.objects.remove(obj, do_unlink=True)

    print(f"Removed {len(to_remove)} eye objects")


def regenerate_with_seed(seed: int, base_name: str = "EyeCluster") -> bpy.types.Object:
    """
    Regenerates the eye cluster with a new seed.

    Args:
        seed: New random seed
        base_name: Base object name

    Returns:
        The regenerated object
    """
    obj = bpy.data.objects.get(base_name)
    if obj and obj.modifiers:
        for mod in obj.modifiers:
            if mod.type == 'NODES':
                # Find seed input and update it
                for i, item in enumerate(mod.node_group.interface.items_tree):
                    if item.item_type == 'SOCKET' and item.name == 'Seed':
                        mod[i] = seed
                        break
        return obj
    else:
        # Generate new
        return generate_eyes(seed=seed, name=base_name)


class EyeGeneratorProperties(bpy.types.PropertyGroup):
    """Properties for the eye generator panel."""

    eye_count: bpy.props.IntProperty(
        name="Eye Count",
        description="Number of eyes to generate",
        default=100,
        min=12,
        max=1000000,
    )

    distribution_radius: bpy.props.FloatProperty(
        name="Distribution Radius",
        description="Radius of the distribution sphere",
        default=10.0,
        min=0.1,
        max=1000.0,
    )

    size_min: bpy.props.FloatProperty(
        name="Min Size",
        description="Minimum eye size",
        default=0.1,
        min=0.001,
        max=10.0,
    )

    size_max: bpy.props.FloatProperty(
        name="Max Size",
        description="Maximum eye size",
        default=1.0,
        min=0.01,
        max=10.0,
    )

    seed: bpy.props.IntProperty(
        name="Seed",
        description="Random seed for reproducibility",
        default=42,
        min=0,
        max=999999,
    )

    pupil_ratio: bpy.props.FloatProperty(
        name="Pupil Ratio",
        description="Pupil size relative to eye",
        default=0.3,
        min=0.0,
        max=1.0,
    )

    iris_ratio: bpy.props.FloatProperty(
        name="Iris Ratio",
        description="Iris size relative to eye",
        default=0.6,
        min=0.0,
        max=1.0,
    )


class OBJECT_OT_GenerateEyes(bpy.types.Operator):
    """Generate eye cluster operator."""

    bl_idname = "eyes.generate"
    bl_label = "Generate Eyes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.eye_generator

        generate_eyes(
            count=props.eye_count,
            radius=props.distribution_radius,
            size_min=props.size_min,
            size_max=props.size_max,
            seed=props.seed,
            pupil_ratio=props.pupil_ratio,
            iris_ratio=props.iris_ratio,
        )

        self.report({'INFO'}, f"Generated {props.eye_count} eyes")
        return {'FINISHED'}


class OBJECT_OT_ClearEyes(bpy.types.Operator):
    """Clear all eye objects operator."""

    bl_idname = "eyes.clear"
    bl_label = "Clear Eyes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clear_all_eyes()
        self.report({'INFO'}, "Cleared all eyes")
        return {'FINISHED'}


class VIEW3D_PT_EyeGenerator(bpy.types.Panel):
    """Eye Generator panel in the 3D viewport."""

    bl_label = "Eye Generator"
    bl_idname = "VIEW3D_PT_eye_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Eyes'

    def draw(self, context):
        layout = self.layout
        props = context.scene.eye_generator

        # Geometry settings
        box = layout.box()
        box.label(text="Geometry", icon='MESH_UVSPHERE')
        box.prop(props, "eye_count")
        box.prop(props, "distribution_radius")

        # Size settings
        box = layout.box()
        box.label(text="Size", icon='ARROW_LEFTRIGHT')
        box.prop(props, "size_min")
        box.prop(props, "size_max")

        # Eye structure
        box = layout.box()
        box.label(text="Eye Structure", icon='MATSPHERE')
        box.prop(props, "pupil_ratio")
        box.prop(props, "iris_ratio")

        # Random seed
        box = layout.box()
        box.label(text="Random", icon='TIME')
        box.prop(props, "seed")

        # Generate button
        layout.separator()
        row = layout.row()
        row.operator("eyes.generate", icon='MESH_MONKEY')
        row = layout.row()
        row.operator("eyes.clear", icon='X')


# Registration
classes = [
    EyeGeneratorProperties,
    OBJECT_OT_GenerateEyes,
    OBJECT_OT_ClearEyes,
    VIEW3D_PT_EyeGenerator,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.eye_generator = bpy.props.PointerProperty(
        type=EyeGeneratorProperties
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.eye_generator


if __name__ == "__main__":
    register()
