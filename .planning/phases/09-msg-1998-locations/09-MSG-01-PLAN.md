# PLAN: MSG 1998 Location Building - fSpy Import & Camera Matching

**Phase:** 9.MSG-01
**Created:** 2026-02-22
**Depends On:** FDX GSD Phase 8 (Production Packages)
**Output To:** Phase 9.MSG-02 (Modeling Pipeline)

---

## Goal

Implement fSpy camera matching workflow to import real-world location references into Blender with accurate camera perspective.

---

## Tasks

### Task 1: fSpy Import Module
**File:** `lib/msg1998/fspy_import.py`

```python
@dataclass
class FSpyImportResult:
    """Result of fSpy import operation."""
    camera: bpy.types.Object
    reference_image: bpy.types.Image
    original_fspy_path: Path
    focal_length_mm: float
    sensor_width_mm: float
    rotation_matrix: Matrix

def import_fspy(fspy_path: Path, blend_path: Path) -> FSpyImportResult:
    """Import fSpy file and create matched camera."""
    ...

def validate_fspy_camera(camera: bpy.types.Object) -> list[str]:
    """Validate camera setup matches fSpy data."""
    ...
```

### Task 2: Reference Image Loader
**File:** `lib/msg1998/reference_loader.py`

```python
@dataclass
class ReferenceSet:
    """Set of reference images for a location."""
    location_id: str
    images: list[Path]
    fspy_files: list[Path]
    primary_angle: str  # "north", "south", "east", "west"

def load_references(location_dir: Path) -> ReferenceSet:
    """Load all reference images and fSpy files for location."""
    ...

def setup_reference_plane(image: bpy.types.Image, camera: bpy.types.Object) -> bpy.types.Object:
    """Create image plane aligned with camera for modeling reference."""
    ...
```

### Task 3: Handoff Package Receiver
**File:** `lib/msg1998/handoff_receiver.py`

```python
@dataclass
class FDXHandoffPackage:
    """Received handoff from FDX GSD."""
    scene_id: str
    locations: list[LocationAsset]
    received_at: datetime
    manifest: dict

def receive_handoff(handoff_dir: Path, dest_dir: Path) -> FDXHandoffPackage:
    """Receive and validate handoff package from FDX GSD."""
    ...

def validate_handoff(package: FDXHandoffPackage) -> list[str]:
    """Validate all required files present."""
    ...
```

### Task 4: Period Validation Utilities
**File:** `lib/msg1998/period_validator.py`

```python
@dataclass
class PeriodViolation:
    """Detected period accuracy issue."""
    element: str
    description: str
    severity: str  # "error", "warning", "info"
    suggestion: str

def validate_period_accuracy(blend_path: Path, target_year: int = 1998) -> list[PeriodViolation]:
    """Check blend file for period-accurate elements."""
    ...

# Known period violations for 1998 NYC
PERIOD_VIOLATIONS_1998 = {
    "led_screens": "LED billboards not common until 2000s",
    "smartphone_stations": "Smartphone charging stations post-2010",
    "modern_traffic_signals": "LED traffic signals post-2005",
    "contemporary_signage": "Check signage for modern branding",
}
```

### Task 5: CLI Commands
**File:** `lib/msg1998/cli.py`

```python
# blender-gsd receive-handoff --from-fdx --scene SCN-XXX
@app.command()
def receive_handoff(scene: str, from_fdx: bool = True):
    """Receive handoff package from FDX GSD."""
    ...

# blender-gsd build-location LOC-XXX --from-fspy
@app.command()
def build_location(location_id: str, from_fspy: bool = False):
    """Initialize location build from fSpy."""
    ...

# blender-gsd validate-period LOC-XXX --year 1998
@app.command()
def validate_period(location_id: str, year: int = 1998):
    """Validate period accuracy of location."""
    ...
```

---

## File Structure

```
lib/msg1998/
├── __init__.py
├── fspy_import.py         # Task 1
├── reference_loader.py    # Task 2
├── handoff_receiver.py    # Task 3
├── period_validator.py    # Task 4
├── types.py               # Shared data types
└── cli.py                 # Task 5
```

---

## Validation Criteria

- [ ] fSpy import creates accurate camera
- [ ] Reference images load correctly
- [ ] Handoff packages validate against schema
- [ ] Period validator catches known violations
- [ ] CLI commands work as specified

---

## Estimated Time

**2-3 hours**
