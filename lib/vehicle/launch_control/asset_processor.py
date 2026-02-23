"""
Launch Control Asset Processor

Processes KitBash car assets to add Launch Control compatibility.
Run this script from within Blender.

Usage in Blender:
    1. Open the car asset blend file
    2. Run this script (Alt+P in Text Editor)
    3. Or use from command line:
       blender --background --python asset_processor.py -- /path/to/assets.blend

The script will:
1. Analyze all car objects in the scene
2. Detect wheels, body, and other components
3. Create Launch Control rigs for each car
4. Add suspension systems
5. Add steering systems
6. Create vehicle paths for animation
7. Save as new blend file with "_launch_control" suffix

Command line usage:
    blender -b -P asset_processor.py -- /path/to/cars.blend --output /path/to/output.blend
"""

import bpy
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from math import pi
import re


@dataclass
class CarDetectionResult:
    """Result of car object detection."""
    car_name: str
    body_object: Optional[bpy.types.Object] = None
    wheels: Dict[str, bpy.types.Object] = None
    steering_wheel: Optional[bpy.types.Object] = None
    windows: List[bpy.types.Object] = None
    lights: Dict[str, List[bpy.types.Object]] = None
    exhausts: List[bpy.types.Object] = None
    spoilers: List[bpy.types.Object] = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.wheels is None:
            self.wheels = {}
        if self.windows is None:
            self.windows = []
        if self.lights is None:
            self.lights = {}
        if self.exhausts is None:
            self.exhausts = []
        if self.spoilers is None:
            self.spoilers = []


class CarDetector:
    """Detects and classifies car components in a blend file."""

    # Naming patterns for component detection
    WHEEL_PATTERNS = [
        r'wheel', r'rim', r'tire', r'tyre',
        r'fl$', r'fr$', r'rl$', r'rr$', r'bl$', r'br$',  # Front-left, etc.
        r'front.*left', r'front.*right', r'rear.*left', r'rear.*right',
        r'_fl_', r'_fr_', r'_rl_', r'_rr_',
    ]

    BODY_PATTERNS = [
        r'body', r'chassis', r'frame', r'car_', r'vehicle',
        r'main', r'base', r'shell',
    ]

    STEERING_PATTERNS = [
        r'steering', r'steer.*wheel', r'wheel.*steer',
    ]

    WINDOW_PATTERNS = [
        r'window', r'windshield', r'windscreen', r'glass',
        r'mirror', r'side.*glass',
    ]

    LIGHT_PATTERNS = {
        'headlights': [r'headlight', r'head.*light', r'front.*light', r'main.*beam'],
        'taillights': [r'taillight', r'tail.*light', r'rear.*light', r'brake.*light'],
        'indicators': [r'indicator', r'turn.*signal', r'blinker', r'signal'],
        'fog_lights': [r'fog.*light', r'foglight'],
    }

    EXHAUST_PATTERNS = [
        r'exhaust', r'muffler', r'tailpipe', r'pipe',
    ]

    SPOILER_PATTERNS = [
        r'spoiler', r'wing', r'air.*dam', r'splitter',
    ]

    def __init__(self):
        self.cars_found: List[CarDetectionResult] = []

    def scan_scene(self, verbose: bool = True) -> List[CarDetectionResult]:
        """Scan the current scene for car objects."""
        self.cars_found = []

        # Group objects by their base name
        car_groups = self._group_car_objects(verbose)

        if verbose:
            print(f"Found {len(car_groups)} potential car groups")

        for car_name, objects in car_groups.items():
            if verbose:
                print(f"  Analyzing: {car_name} ({len(objects)} objects)")
            result = self._detect_components(car_name, objects)
            if result.confidence > 0.3:  # Minimum confidence threshold
                self.cars_found.append(result)
                if verbose:
                    print(f"    ✓ Detected car (confidence: {result.confidence:.2f})")
                    print(f"      Wheels: {list(result.wheels.keys())}")
            elif verbose:
                print(f"    ✗ Skipped (confidence: {result.confidence:.2f})")

        return self.cars_found

    def _group_car_objects(self, verbose: bool = False) -> Dict[str, List[bpy.types.Object]]:
        """Group objects by their base car name."""
        groups: Dict[str, List[bpy.types.Object]] = {}

        total = len(bpy.data.objects)
        if verbose:
            print(f"Scanning {total} objects...")

        for i, obj in enumerate(bpy.data.objects):
            if verbose and i % 100 == 0:
                print(f"  Progress: {i}/{total} objects scanned...")

            if obj.type not in ['MESH', 'CURVE', 'EMPTY']:
                continue

            # Extract base name (remove common suffixes)
            base_name = self._extract_base_name(obj.name)

            if base_name:
                if base_name not in groups:
                    groups[base_name] = []
                groups[base_name].append(obj)

        return groups

    def _extract_base_name(self, name: str) -> Optional[str]:
        """Extract the base car name from an object name.

        Supports multiple naming conventions:
        - KitBash: Component_CarID_Material (e.g., Body_A_CarPaint_Orange -> Car_A)
        - Standard: CarName_Component (e.g., Ferrari_body -> Ferrari)
        - Simple: CarName (e.g., CarA001 -> CarA001)
        """
        name_lower = name.lower()

        # Skip if it's a camera, light, or other non-car object
        skip_words = ['camera', 'light', 'lamp', 'empty', 'helper', 'locator']
        if any(skip in name_lower for skip in skip_words):
            return None

        # Split by underscore
        if '_' in name:
            parts = name.split('_')

            # KitBash pattern: Component_CarID_Material (e.g., Body_A_CarPaint_Orange)
            # CarID is typically a single letter (A, B, C, D) or letter+number (A1, B2)
            if len(parts) >= 2:
                component = parts[0].lower()
                car_id = parts[1]

                # Check if second part looks like a car ID (single letter or letter+digit)
                if len(car_id) <= 3 and car_id[0].isalpha():
                    # Check if first part is a known component type
                    component_types = [
                        'body', 'bumper', 'door', 'hood', 'roof', 'trunk',
                        'wheel', 'rim', 'tire', 'seat', 'interior', 'cockpit',
                        'fender', 'grill', 'spoiler', 'mirror', 'glass',
                        'exhaust', 'suspension', 'brake', 'engine', 'mech',
                        'frame', 'chassis', 'door', 'side', 'front', 'rear',
                        'headlight', 'taillight', 'bumperfront', 'bumperrear',
                        'steeringcolumn', 'wiper', 'fuel', 'piping', 'struts',
                        'meshgrille', 'hoodinsert', 'scoop', 'fans', 'fins',
                        'undercarriage', 'object', 'box', 'pcylinder', 'c1', 'c2'
                    ]

                    if component in component_types or component.startswith('car'):
                        # This is KitBash style - group by Car ID
                        return f"Car_{car_id}"

                # Standard pattern: CarName_Component (parts[0] is the car name)
                # Check if first part looks like a car name
                if any(p in parts[0].lower() for p in ['car', 'ferrari', 'lambo', 'porsche', 'audi', 'bmw', 'mercedes']):
                    return parts[0]

                # If second part is a known component, first part is car name
                if any(p in parts[1].lower() for p in ['wheel', 'body', 'door', 'hood', 'bumper']):
                    return parts[0]

        # Single word name - check if it looks like a car
        if any(p in name_lower for p in ['car', 'veh', 'auto']):
            return name

        return None

    def _detect_components(
        self,
        car_name: str,
        objects: List[bpy.types.Object]
    ) -> CarDetectionResult:
        """Detect car components from a group of objects."""
        result = CarDetectionResult(car_name=car_name)
        result.windows = []
        result.exhausts = []
        result.spoilerss = []
        result.lights = {k: [] for k in self.LIGHT_PATTERNS.keys()}

        for obj in objects:
            obj_lower = obj.name.lower()

            # Check for wheels
            for pattern in self.WHEEL_PATTERNS:
                if re.search(pattern, obj_lower):
                    position = self._determine_wheel_position(obj.name, obj)
                    if position:
                        result.wheels[position] = obj
                        result.confidence += 0.15
                    break

            # Check for body
            for pattern in self.BODY_PATTERNS:
                if re.search(pattern, obj_lower):
                    if result.body_object is None:
                        result.body_object = obj
                        result.confidence += 0.2
                    break

            # Check for steering wheel
            for pattern in self.STEERING_PATTERNS:
                if re.search(pattern, obj_lower):
                    result.steering_wheel = obj
                    result.confidence += 0.1
                    break

            # Check for windows
            for pattern in self.WINDOW_PATTERNS:
                if re.search(pattern, obj_lower):
                    result.windows.append(obj)
                    result.confidence += 0.05
                    break

            # Check for lights
            for light_type, patterns in self.LIGHT_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, obj_lower):
                        result.lights[light_type].append(obj)
                        result.confidence += 0.05
                        break

            # Check for exhausts
            for pattern in self.EXHAUST_PATTERNS:
                if re.search(pattern, obj_lower):
                    result.exhausts.append(obj)
                    result.confidence += 0.03
                    break

            # Check for spoilers
            for pattern in self.SPOILER_PATTERNS:
                if re.search(pattern, obj_lower):
                    result.spoilers.append(obj)
                    result.confidence += 0.05
                    break

        # Bonus confidence for having all 4 wheels
        if len(result.wheels) == 4:
            result.confidence += 0.2

        return result

    def _determine_wheel_position(
        self,
        name: str,
        obj: bpy.types.Object
    ) -> Optional[str]:
        """Determine which wheel position this object is."""
        name_lower = name.lower()

        # Check explicit position indicators
        if any(p in name_lower for p in ['fl', 'frontleft', 'front_left', 'lf']):
            return 'front_left'
        if any(p in name_lower for p in ['fr', 'frontright', 'front_right', 'rf']):
            return 'front_right'
        if any(p in name_lower for p in ['rl', 'bl', 'rearleft', 'rear_left', 'lr']):
            return 'rear_left'
        if any(p in name_lower for p in ['rr', 'br', 'rearright', 'rear_right', 'lr']):
            return 'rear_right'

        # Try to determine from object position
        if obj.type == 'MESH':
            # Get approximate position
            x = obj.location.x
            y = obj.location.y

            # X: negative = left, positive = right
            # Y: positive = front, negative = rear (typical Blender orientation)

            is_left = x < 0
            is_front = y > 0

            if is_front:
                return 'front_left' if is_left else 'front_right'
            else:
                return 'rear_left' if is_left else 'rear_right'

        return None


class LaunchControlBuilder:
    """Builds Launch Control rigs for detected cars."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def process_car(self, car: CarDetectionResult) -> Dict[str, Any]:
        """
        Add Launch Control rigging to a detected car.

        Returns processing result with status and any warnings.
        """
        result = {
            'car_name': car.car_name,
            'success': False,
            'warnings': [],
            'created_objects': [],
            'errors': [],
        }

        try:
            # Create car collection
            car_collection = self._get_or_create_collection(f"{car.car_name}_LaunchControl")

            # Create root empty for the rig
            rig_root = self._create_rig_root(car.car_name, car.body_object)
            rig_root.users_collection[0].objects.unlink(rig_root)
            car_collection.objects.link(rig_root)
            result['created_objects'].append(rig_root.name)

            # Add wheel pivots
            if car.wheels:
                pivot_result = self._create_wheel_pivots(car.wheels, rig_root)
                result['created_objects'].extend(pivot_result['objects'])
                result['warnings'].extend(pivot_result['warnings'])

            # Add steering setup
            if 'front_left' in car.wheels and 'front_right' in car.wheels:
                steering_result = self._create_steering_setup(
                    car.wheels['front_left'],
                    car.wheels['front_right'],
                    rig_root
                )
                result['created_objects'].extend(steering_result['objects'])
                result['warnings'].extend(steering_result['warnings'])

            # Add suspension helpers
            suspension_result = self._create_suspension_helpers(car.wheels, rig_root)
            result['created_objects'].extend(suspension_result['objects'])

            # Add body constraints
            if car.body_object:
                self._constrain_body_to_rig(car.body_object, rig_root)

            # Add custom properties for Launch Control
            self._add_launch_control_properties(rig_root, car)

            result['success'] = True

        except Exception as e:
            result['errors'].append(str(e))

        self.results.append(result)
        return result

    def _get_or_create_collection(self, name: str) -> bpy.types.Collection:
        """Get or create a collection by name."""
        if name in bpy.data.collections:
            return bpy.data.collections[name]

        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        return collection

    def _create_rig_root(
        self,
        car_name: str,
        body_object: Optional[bpy.types.Object]
    ) -> bpy.types.Object:
        """Create the root empty for the Launch Control rig."""
        root_name = f"{car_name}_Rig"
        root = bpy.data.objects.new(root_name, None)
        root.empty_display_type = 'CUBE'
        root.empty_display_size = 0.5

        bpy.context.collection.objects.link(root)

        # Position at body center if available
        if body_object:
            root.location = body_object.location.copy()
        else:
            root.location = (0, 0, 0)

        return root

    def _create_wheel_pivots(
        self,
        wheels: Dict[str, bpy.types.Object],
        rig_root: bpy.types.Object
    ) -> Dict[str, Any]:
        """Create pivot points for each wheel."""
        result = {'objects': [], 'warnings': []}

        for position, wheel_obj in wheels.items():
            # Create pivot empty
            pivot_name = f"{rig_root.name}_Wheel_{position}"
            pivot = bpy.data.objects.new(pivot_name, None)
            pivot.empty_display_type = 'ARROWS'
            pivot.empty_display_size = 0.2

            # Position at wheel center
            pivot.location = wheel_obj.location.copy()
            pivot.parent = rig_root

            bpy.context.collection.objects.link(pivot)
            result['objects'].append(pivot.name)

            # Parent wheel to pivot
            wheel_obj.parent = pivot

        return result

    def _create_steering_setup(
        self,
        wheel_fl: bpy.types.Object,
        wheel_fr: bpy.types.Object,
        rig_root: bpy.types.Object
    ) -> Dict[str, Any]:
        """Create steering mechanism for front wheels."""
        result = {'objects': [], 'warnings': []}

        # Create steering controller
        steer_name = f"{rig_root.name}_Steering"
        steer_ctrl = bpy.data.objects.new(steer_name, None)
        steer_ctrl.empty_display_type = 'CIRCLE'
        steer_ctrl.empty_display_size = 0.3

        # Position between front wheels
        mid_x = (wheel_fl.location.x + wheel_fr.location.x) / 2
        mid_y = (wheel_fl.location.y + wheel_fr.location.y) / 2
        mid_z = (wheel_fl.location.z + wheel_fr.location.z) / 2
        steer_ctrl.location = (mid_x, mid_y, mid_z)
        steer_ctrl.rotation_euler = (pi/2, 0, 0)  # Rotate to horizontal
        steer_ctrl.parent = rig_root

        bpy.context.collection.objects.link(steer_ctrl)
        result['objects'].append(steer_ctrl.name)

        # Add steering custom property
        steer_ctrl['max_steering_angle'] = 35.0
        steer_ctrl['ackermann_enabled'] = True

        return result

    def _create_suspension_helpers(
        self,
        wheels: Dict[str, bpy.types.Object],
        rig_root: bpy.types.Object
    ) -> Dict[str, Any]:
        """Create suspension helper objects."""
        result = {'objects': []}

        # Create suspension root
        susp_name = f"{rig_root.name}_Suspension"
        susp_root = bpy.data.objects.new(susp_name, None)
        susp_root.empty_display_type = 'SPHERE'
        susp_root.empty_display_size = 0.1
        susp_root.parent = rig_root

        bpy.context.collection.objects.link(susp_root)
        result['objects'].append(susp_root.name)

        # Add suspension properties
        for position in wheels.keys():
            susp_root[f'{position}_travel'] = 0.15  # meters
            susp_root[f'{position}_stiffness'] = 25000  # N/m
            susp_root[f'{position}_damping'] = 3000  # Ns/m

        return result

    def _constrain_body_to_rig(
        self,
        body: bpy.types.Object,
        rig_root: bpy.types.Object
    ) -> None:
        """Add constraints to keep body with rig."""
        # Add Copy Transforms constraint
        constraint = body.constraints.new('COPY_TRANSFORMS')
        constraint.target = rig_root
        constraint.owner_space = 'LOCAL'
        constraint.target_space = 'LOCAL'

    def _add_launch_control_properties(
        self,
        rig_root: bpy.types.Object,
        car: CarDetectionResult
    ) -> None:
        """Add custom properties for Launch Control system."""
        # Vehicle identification
        rig_root['launch_control_version'] = '1.0'
        rig_root['vehicle_name'] = car.car_name
        rig_root['vehicle_type'] = 'supercar'

        # Physics properties (defaults)
        rig_root['mass_kg'] = 1500.0
        rig_root['engine_power_kw'] = 400.0
        rig_root['max_speed_kmh'] = 320.0
        rig_root['acceleration_0_100'] = 3.5  # seconds

        # Wheel properties
        rig_root['wheelbase'] = self._calculate_wheelbase(car.wheels)
        rig_root['track_width'] = self._calculate_track_width(car.wheels)

        # Steering properties
        rig_root['steering_ratio'] = 15.0  # steering wheel : wheel angle
        rig_root['max_steering_angle'] = 35.0  # degrees

        # Suspension properties
        rig_root['suspension_type'] = 'independent'
        rig_root['suspension_travel'] = 0.15  # meters
        rig_root['spring_stiffness'] = 25000  # N/m
        rig_root['damping_ratio'] = 0.3

        # Animation properties
        rig_root['animation_ready'] = True
        rig_root['path_follow_enabled'] = True

    def _calculate_wheelbase(self, wheels: Dict[str, bpy.types.Object]) -> float:
        """Calculate wheelbase from wheel positions."""
        if 'front_left' in wheels and 'rear_left' in wheels:
            front = wheels['front_left'].location
            rear = wheels['rear_left'].location
            return abs(front.y - rear.y)
        return 2.6  # Default wheelbase

    def _calculate_track_width(self, wheels: Dict[str, bpy.types.Object]) -> float:
        """Calculate track width from wheel positions."""
        if 'front_left' in wheels and 'front_right' in wheels:
            left = wheels['front_left'].location
            right = wheels['front_right'].location
            return abs(right.x - left.x)
        return 1.6  # Default track width


def process_blend_file(
    input_path: str,
    output_path: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Process a blend file to add Launch Control to all cars.

    Args:
        input_path: Path to input blend file
        output_path: Optional output path (defaults to input_launch_control.blend)
        verbose: Print progress messages

    Returns:
        Processing result dictionary
    """
    result = {
        'input_file': input_path,
        'output_file': output_path,
        'cars_processed': 0,
        'cars_successful': 0,
        'cars': [],
        'errors': [],
    }

    try:
        if verbose:
            print(f"\n{'='*50}")
            print("Launch Control Asset Processor")
            print(f"{'='*50}")
            print(f"Input: {input_path}")

        # If we're not in an active Blender session, we need to load the file
        current_file = bpy.data.filepath
        if current_file != input_path:
            if verbose:
                print("Loading blend file...")
            bpy.ops.wm.open_mainfile(filepath=input_path)

        # Detect cars
        if verbose:
            print("\n--- Detecting Cars ---")
        detector = CarDetector()
        cars = detector.scan_scene(verbose=verbose)
        result['cars_processed'] = len(cars)

        if verbose:
            print(f"\n--- Processing {len(cars)} Cars ---")

        # Process each car
        builder = LaunchControlBuilder()
        for i, car in enumerate(cars):
            if verbose:
                print(f"\n[{i+1}/{len(cars)}] Processing: {car.car_name}")
            car_result = builder.process_car(car)
            result['cars'].append(car_result)
            if car_result['success']:
                result['cars_successful'] += 1
                if verbose:
                    print(f"  ✓ Success - Created {len(car_result['created_objects'])} objects")
            else:
                if verbose:
                    print(f"  ✗ Failed")
                    for err in car_result['errors']:
                        print(f"    Error: {err}")

        # Save output
        if output_path is None:
            input_file = Path(input_path)
            output_path = str(input_file.parent / f"{input_file.stem}_launch_control.blend")

        if verbose:
            print(f"\n--- Saving ---")
            print(f"Output: {output_path}")

        bpy.ops.wm.save_as_mainfile(filepath=output_path)
        result['output_file'] = output_path

        if verbose:
            print(f"\n{'='*50}")
            print(f"COMPLETE: {result['cars_successful']}/{result['cars_processed']} cars processed")
            print(f"{'='*50}\n")

    except Exception as e:
        result['errors'].append(str(e))
        if verbose:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()

    return result


def process_current_scene(verbose: bool = True) -> Dict[str, Any]:
    """
    Process the currently open Blender scene.

    Use this when you have a blend file already open in Blender.

    Returns:
        Processing result dictionary
    """
    result = {
        'input_file': bpy.data.filepath,
        'output_file': None,
        'cars_processed': 0,
        'cars_successful': 0,
        'cars': [],
        'errors': [],
    }

    try:
        if verbose:
            print(f"\n{'='*50}")
            print("Launch Control Asset Processor")
            print(f"{'='*50}")
            print(f"Processing current scene: {bpy.path.basename(bpy.data.filepath)}")

        # Detect cars
        if verbose:
            print("\n--- Detecting Cars ---")
        detector = CarDetector()
        cars = detector.scan_scene(verbose=verbose)
        result['cars_processed'] = len(cars)

        if verbose:
            print(f"\n--- Processing {len(cars)} Cars ---")

        # Process each car
        builder = LaunchControlBuilder()
        for i, car in enumerate(cars):
            if verbose:
                print(f"\n[{i+1}/{len(cars)}] Processing: {car.car_name}")
            car_result = builder.process_car(car)
            result['cars'].append(car_result)
            if car_result['success']:
                result['cars_successful'] += 1
                if verbose:
                    print(f"  ✓ Success - Created {len(car_result['created_objects'])} objects")
            else:
                if verbose:
                    print(f"  ✗ Failed")
                    for err in car_result['errors']:
                        print(f"    Error: {err}")

        if verbose:
            print(f"\n{'='*50}")
            print(f"COMPLETE: {result['cars_successful']}/{result['cars_processed']} cars processed")
            print("Save the file manually to keep changes")
            print(f"{'='*50}\n")

    except Exception as e:
        result['errors'].append(str(e))
        if verbose:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()

    return result


def process_supercars_assets(verbose: bool = True):
    """
    Process the KitBash supercar assets.

    Run this function in Blender with the supercars blend file open,
    or call it to open and process the file automatically.
    """
    # Default path to supercar assets
    default_path = "/Volumes/Storage/3d/kitbash/converted_assets/Veh Supercars/Veh Supercars_assets.blend"

    return process_blend_file(default_path, verbose=verbose)


# === COMMAND LINE INTERFACE ===

def main():
    """Command line interface for asset processor."""
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    if not args:
        print("Usage: blender --background --python asset_processor.py -- <input.blend> [output.blend]")
        print("\nOptions:")
        print("  input.blend   - Path to car assets blend file")
        print("  output.blend  - Optional output path (default: input_launch_control.blend)")
        return

    input_path = args[0]
    output_path = args[1] if len(args) > 1 else None

    print(f"Processing: {input_path}")
    result = process_blend_file(input_path, output_path)

    print("\n=== Processing Result ===")
    print(f"Cars found: {result['cars_processed']}")
    print(f"Cars processed successfully: {result['cars_successful']}")
    print(f"Output file: {result['output_file']}")

    if result['errors']:
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")

    for car in result['cars']:
        status = "✓" if car['success'] else "✗"
        print(f"\n{status} {car['car_name']}")
        if car['warnings']:
            for warning in car['warnings']:
                print(f"    ⚠ {warning}")
        if car['errors']:
            for error in car['errors']:
                print(f"    ✗ {error}")


if __name__ == "__main__":
    main()


__all__ = [
    'CarDetector',
    'CarDetectionResult',
    'LaunchControlBuilder',
    'process_blend_file',
    'process_current_scene',
    'process_supercars_assets',
]
