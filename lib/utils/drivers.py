"""
Safe driver utilities for Blender GSD pipeline.

Provides driver creation with named variables instead of hardcoded object names,
driver repair utilities, and safe expression handling.

Usage:
    from lib.utils.drivers import add_safe_driver, DriverBuilder, repair_drivers

    # Create driver with safe variables
    add_safe_driver(
        obj, "rotation_euler", 1,
        expression="distance / (2 * pi * radius)",
        variables={
            'distance': (vehicle_obj, "location[0]"),
            'radius': (None, "0.35"),  # Constant
        }
    )

    # Repair broken drivers after rename
    repaired = repair_drivers(obj)
"""

import re
import warnings
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Try to import bpy
try:
    import bpy
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    warnings.warn("bpy not available. Driver utilities will not function.")


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DriverVariable:
    """Definition of a driver variable."""
    name: str
    target_object: Optional[str]  # Object name or None for constant
    data_path: str
    transform_space: str = 'WORLD_SPACE'  # For transform properties


@dataclass
class DriverInfo:
    """Information about a driver for inspection/repair."""
    object_name: str
    data_path: str
    array_index: int
    expression: str
    variables: Dict[str, Tuple[Optional[str], str]]  # name -> (object_name, data_path)


# ============================================================================
# SAFE DRIVER CREATION
# ============================================================================

def add_safe_driver(
    obj,
    data_path: str,
    array_index: int = 0,
    expression: str = "0",
    variables: Dict[str, Tuple] = None,
    driver_type: str = 'SCRIPTED'
) -> Optional[Any]:
    """
    Add a driver with named variables instead of hardcoded object names.

    This is the safe way to create drivers - using variable references
    instead of object names in expressions prevents breakage on rename.

    Args:
        obj: Blender object to add driver to
        data_path: Property to drive (e.g., "location", "rotation_euler")
        array_index: Array index for multi-component properties
        expression: Driver expression using variable names
        variables: Dict of {var_name: (target_obj, data_path)}
                   target_obj can be None for constant values
        driver_type: 'SCRIPTED', 'AVERAGE', 'SUM', 'MIN', 'MAX'

    Returns:
        The created driver (FCurve) or None on failure

    Example:
        add_safe_driver(
            wheel, "rotation_euler", 1,
            expression="distance / (2 * pi * radius)",
            variables={
                'distance': (vehicle, "location[0]"),
                'radius': (None, "0.35"),
            }
        )
    """
    if not HAS_BLENDER:
        logger.error("bpy not available, cannot create driver")
        return None

    if obj is None:
        logger.error("Cannot add driver to None object")
        return None

    try:
        # Add driver
        fcurve = obj.driver_add(data_path, array_index)
        driver = fcurve.driver
        driver.type = driver_type

        if driver_type == 'SCRIPTED':
            driver.expression = expression

        # Clear existing variables
        while driver.variables:
            driver.variables.remove(driver.variables[0])

        # Add variables
        if variables:
            for var_name, (target, path) in variables.items():
                var = driver.variables.new()
                var.name = var_name

                if target is not None:
                    # Object reference
                    if isinstance(target, str):
                        # Target is object name
                        target_obj = bpy.data.objects.get(target)
                    else:
                        # Target is object itself
                        target_obj = target

                    if target_obj:
                        var.targets[0].id_type = 'OBJECT'
                        var.targets[0].id = target_obj
                        var.targets[0].data_path = path
                    else:
                        logger.warning(f"Target object not found for variable {var_name}")
                else:
                    # Single property or constant
                    var.targets[0].id_type = 'OBJECT'
                    var.targets[0].id = obj  # Use self
                    var.targets[0].data_path = path

        logger.debug(f"Added driver to {obj.name}.{data_path}[{array_index}]")
        return fcurve

    except Exception as e:
        logger.error(f"Failed to add driver: {e}")
        return None


def remove_driver(obj, data_path: str, array_index: int = -1) -> bool:
    """
    Remove a driver from an object.

    Args:
        obj: Blender object
        data_path: Property path
        array_index: Array index (-1 for all)

    Returns:
        True if driver was removed
    """
    if not HAS_BLENDER or obj is None:
        return False

    try:
        if array_index >= 0:
            obj.driver_remove(data_path, array_index)
        else:
            obj.driver_remove(data_path)
        return True
    except:
        return False


# ============================================================================
# DRIVER BUILDER (FLUENT API)
# ============================================================================

class DriverBuilder:
    """
    Fluent builder for creating drivers.

    Usage:
        driver = (
            DriverBuilder(wheel, "rotation_euler", 1)
            .expression("distance / (2 * pi * radius)")
            .variable("distance", vehicle, "location[0]")
            .variable("radius", None, "0.35")
            .build()
        )
    """

    def __init__(self, obj, data_path: str, array_index: int = 0):
        self.obj = obj
        self.data_path = data_path
        self.array_index = array_index
        self.expression = "0"
        self.variables: Dict[str, Tuple] = {}
        self.driver_type = 'SCRIPTED'

    def expression(self, expr: str) -> 'DriverBuilder':
        """Set the driver expression."""
        self.expression = expr
        return self

    def variable(
        self,
        name: str,
        target_obj,
        data_path: str,
        transform_space: str = 'WORLD_SPACE'
    ) -> 'DriverBuilder':
        """Add a variable to the driver."""
        self.variables[name] = (target_obj, data_path)
        return self

    def single_property(
        self,
        name: str,
        target_obj,
        data_path: str
    ) -> 'DriverBuilder':
        """Add a single property variable."""
        return self.variable(name, target_obj, data_path)

    def transform_channel(
        self,
        name: str,
        target_obj,
        channel: str = 'LOC_X',
        space: str = 'WORLD_SPACE'
    ) -> 'DriverBuilder':
        """Add a transform channel variable."""
        # This is a convenience for common transform lookups
        channel_map = {
            'LOC_X': 'location[0]',
            'LOC_Y': 'location[1]',
            'LOC_Z': 'location[2]',
            'ROT_X': 'rotation_euler[0]',
            'ROT_Y': 'rotation_euler[1]',
            'ROT_Z': 'rotation_euler[2]',
            'SCALE_X': 'scale[0]',
            'SCALE_Y': 'scale[1]',
            'SCALE_Z': 'scale[2]',
        }
        data_path = channel_map.get(channel, channel)
        return self.variable(name, target_obj, data_path)

    def rotation_difference(
        self,
        name: str,
        obj1,
        obj2
    ) -> 'DriverBuilder':
        """Add a rotation difference variable."""
        if not HAS_BLENDER:
            return self

        # This creates a ROTATION_DIFF variable type
        # We'll use the builder pattern differently here
        var = (obj1, obj2)  # Special marker for rotation diff
        self.variables[name] = var
        return self

    def average(self) -> 'DriverBuilder':
        """Set driver type to AVERAGE."""
        self.driver_type = 'AVERAGE'
        return self

    def summation(self) -> 'DriverBuilder':
        """Set driver type to SUM."""
        self.driver_type = 'SUM'
        return self

    def build(self) -> Optional[Any]:
        """Build and return the driver."""
        # Handle special variable types
        processed_vars = {}
        for name, value in self.variables.items():
            if isinstance(value, tuple) and len(value) == 2:
                if isinstance(value[0], str) or value[0] is None or hasattr(value[0], 'name'):
                    # Normal variable
                    processed_vars[name] = value
                else:
                    # Rotation difference - need special handling
                    # For now, convert to standard variable
                    processed_vars[name] = value

        return add_safe_driver(
            self.obj,
            self.data_path,
            self.array_index,
            self.expression,
            processed_vars,
            self.driver_type
        )


# ============================================================================
# DRIVER INSPECTION
# ============================================================================

def get_drivers(obj) -> List[DriverInfo]:
    """
    Get all drivers on an object.

    Args:
        obj: Blender object

    Returns:
        List of DriverInfo objects
    """
    if not HAS_BLENDER or obj is None:
        return []

    drivers = []

    if not obj.animation_data:
        return drivers

    for fcurve in obj.animation_data.drivers:
        driver = fcurve.driver

        variables = {}
        for var in driver.variables:
            if var.targets[0].id:
                variables[var.name] = (var.targets[0].id.name, var.targets[0].data_path)
            else:
                variables[var.name] = (None, var.targets[0].data_path)

        info = DriverInfo(
            object_name=obj.name,
            data_path=fcurve.data_path,
            array_index=fcurve.array_index,
            expression=driver.expression if hasattr(driver, 'expression') else '',
            variables=variables
        )
        drivers.append(info)

    return drivers


def find_drivers_with_object(obj_name: str) -> List[DriverInfo]:
    """
    Find all drivers that reference a specific object.

    Args:
        obj_name: Object name to search for

    Returns:
        List of DriverInfo objects referencing the object
    """
    if not HAS_BLENDER:
        return []

    found = []

    for obj in bpy.data.objects:
        drivers = get_drivers(obj)
        for driver in drivers:
            for var_name, (target, _) in driver.variables.items():
                if target == obj_name:
                    found.append(driver)
                    break

    return found


def find_drivers_with_expression(pattern: str) -> List[DriverInfo]:
    """
    Find all drivers matching an expression pattern.

    Args:
        pattern: Regex pattern to match

    Returns:
        List of matching DriverInfo objects
    """
    if not HAS_BLENDER:
        return []

    regex = re.compile(pattern, re.IGNORECASE)
    found = []

    for obj in bpy.data.objects:
        drivers = get_drivers(obj)
        for driver in drivers:
            if regex.search(driver.expression):
                found.append(driver)

    return found


# ============================================================================
# DRIVER REPAIR
# ============================================================================

def repair_drivers(
    obj,
    rename_map: Dict[str, str] = None,
    auto_detect: bool = True
) -> List[str]:
    """
    Repair drivers after object rename.

    Args:
        obj: Object to repair drivers on
        rename_map: Dict of {old_name: new_name} for manual mapping
        auto_detect: Try to auto-detect renames from expression analysis

    Returns:
        List of repaired variable names
    """
    if not HAS_BLENDER or obj is None or not obj.animation_data:
        return []

    repaired = []
    rename_map = rename_map or {}

    for fcurve in obj.animation_data.drivers:
        driver = fcurve.driver

        for var in driver.variables:
            for target in var.targets:
                if target.id_type == 'OBJECT':
                    old_name = target.id.name if target.id else None

                    # Check if object still exists
                    if old_name and old_name not in bpy.data.objects:
                        # Try to find new name
                        if old_name in rename_map:
                            new_name = rename_map[old_name]
                        elif auto_detect:
                            # Try to find similar object
                            new_name = _find_similar_object(old_name)
                        else:
                            new_name = None

                        if new_name and new_name in bpy.data.objects:
                            target.id = bpy.data.objects[new_name]
                            repaired.append(f"{var.name}: {old_name} -> {new_name}")
                            logger.info(f"Repaired driver variable: {old_name} -> {new_name}")

    return repaired


def _find_similar_object(old_name: str) -> Optional[str]:
    """Find an object with a similar name (for auto-repair)."""
    if not HAS_BLENDER:
        return None

    # Remove common suffixes to find base name
    base_name = old_name
    for suffix in ['_pivot', '_ctrl', '_IK', '_FK', '_target', '_pole']:
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break

    # Look for objects with similar base
    candidates = []
    for obj_name in bpy.data.objects.keys():
        if base_name in obj_name and obj_name != old_name:
            candidates.append(obj_name)

    if candidates:
        # Return shortest match (most similar)
        return min(candidates, key=len)

    return None


def fix_driver_expression(expression: str, rename_map: Dict[str, str]) -> str:
    """
    Fix object names in a driver expression string.

    Args:
        expression: Driver expression
        rename_map: Dict of {old_name: new_name}

    Returns:
        Fixed expression
    """
    if not rename_map:
        return expression

    # This is a simplistic approach - proper parsing would be better
    result = expression
    for old_name, new_name in rename_map.items():
        # Replace object name references (this is fragile)
        result = result.replace(old_name, new_name)

    return result


# ============================================================================
# COMMON DRIVER PATTERNS
# ============================================================================

def create_wheel_rotation_driver(
    wheel_obj,
    vehicle_obj,
    radius: float,
    axis: str = 'Y'
) -> Optional[Any]:
    """
    Create a driver for wheel rotation based on vehicle movement.

    Args:
        wheel_obj: Wheel object to rotate
        vehicle_obj: Vehicle object to track
        radius: Wheel radius in meters
        axis: Rotation axis ('X', 'Y', or 'Z')

    Returns:
        Created driver or None
    """
    axis_index = {'X': 0, 'Y': 1, 'Z': 2}[axis]

    return (
        DriverBuilder(wheel_obj, "rotation_euler", axis_index)
        .expression("distance / (2 * pi * radius)")
        .variable("distance", vehicle_obj, "location[0]")
        .variable("pi", None, "3.14159265359")
        .variable("radius", None, str(radius))
        .build()
    )


def create_ik_influence_driver(
    armature,
    bone_name: str,
    blend_property: str
) -> Optional[Any]:
    """
    Create a driver for IK constraint influence from a custom property.

    Args:
        armature: Armature object
        bone_name: Bone with IK constraint
        blend_property: Custom property name (e.g., "ik_fk_blend_arm_L")

    Returns:
        Created driver or None
    """
    if not HAS_BLENDER:
        return None

    bone = armature.pose.bones.get(bone_name)
    if not bone:
        return None

    # Find IK constraint
    ik_constraint = None
    for con in bone.constraints:
        if con.type == 'IK':
            ik_constraint = con
            break

    if not ik_constraint:
        logger.warning(f"No IK constraint on bone {bone_name}")
        return None

    # Add driver to influence
    return (
        DriverBuilder(ik_constraint, "influence", 0)
        .expression(blend_property)
        .variable(blend_property, armature, f'["{blend_property}"]')
        .build()
    )


def create_visibility_driver(
    obj,
    driver_obj,
    property_path: str,
    threshold: float = 0.5
) -> Optional[Any]:
    """
    Create a driver for object visibility based on a property value.

    Args:
        obj: Object to control visibility of
        driver_obj: Object with driving property
        property_path: Property to drive from
        threshold: Value above which object is visible

    Returns:
        Created driver or None
    """
    return (
        DriverBuilder(obj, "hide_viewport", 0)
        .expression(f"value < {threshold}")
        .variable("value", driver_obj, property_path)
        .build()
    )


# ============================================================================
# VALIDATION
# ============================================================================

def validate_driver_expression(expression: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a driver expression for common issues.

    Args:
        expression: Driver expression to validate

    Returns:
        (is_valid, error_message)
    """
    # Check for empty expression
    if not expression.strip():
        return False, "Empty expression"

    # Check for unbalanced parentheses
    paren_count = 0
    for char in expression:
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
        if paren_count < 0:
            return False, "Unbalanced parentheses"

    if paren_count != 0:
        return False, "Unbalanced parentheses"

    # Check for common typos
    common_functions = ['sin', 'cos', 'tan', 'abs', 'sqrt', 'pow', 'min', 'max', 'pi']
    for func in common_functions:
        # Check for missing parentheses after function
        pattern = rf'\b{func}\s*[^(\s]'
        if re.search(pattern, expression):
            return False, f"Possible missing parentheses after '{func}'"

    # Check for potential division by zero (literal 0)
    if re.search(r'/\s*0(?![.0-9])', expression):
        warnings.warn("Potential division by zero in expression")

    return True, None


def validate_all_drivers() -> Dict[str, List[str]]:
    """
    Validate all drivers in the scene.

    Returns:
        Dict of {object_name: [list of issues]}
    """
    if not HAS_BLENDER:
        return {}

    issues = {}

    for obj in bpy.data.objects:
        obj_issues = []

        for driver_info in get_drivers(obj):
            # Validate expression
            is_valid, error = validate_driver_expression(driver_info.expression)
            if not is_valid:
                obj_issues.append(f"{driver_info.data_path}: {error}")

            # Check for missing targets
            for var_name, (target, _) in driver_info.variables.items():
                if target and target not in bpy.data.objects:
                    obj_issues.append(f"Variable '{var_name}' references missing object '{target}'")

        if obj_issues:
            issues[obj.name] = obj_issues

    return issues
