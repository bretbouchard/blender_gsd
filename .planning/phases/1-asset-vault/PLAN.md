# Phase 1: Asset Vault System

**Status**: Planning
**Created**: 2026-02-21
**Goal**: Complete asset indexing, search, and auto-loading with security hardening

---

## Overview

The Asset Vault System provides a unified interface to discover, index, search, and load 3D assets from external libraries into Blender scenes. It handles multiple file formats (blend, fbx, obj, glb), extracts metadata, generates thumbnails, and provides secure path handling.

### External Asset Libraries
- `/Volumes/Storage/3d/kitbash/` - 23+ KitBash3D packs
- `/Volumes/Storage/3d/animation/` - 200+ VFX assets, Vitaly Bulgarov mechs
- `/Volumes/Storage/3d/my 3d designs/` - 321 .blend files
- `/Volumes/Storage/3d/kitbash/kpacks/` - 70+ kits
- **Total**: ~3,090 .blend files, thousands of FBX/OBJ/GLB assets

---

## Requirements Mapping

| Req ID | Description | Priority | Plan |
|--------|-------------|----------|------|
| REQ-AV-01 | Asset Library Indexer | P0 | 01-01, 01-02 |
| REQ-AV-02 | Metadata Extraction | P0 | 01-02, 01-03 |
| REQ-AV-03 | Scale Normalization | P1 | 01-04 |
| REQ-AV-04 | Category/Tag Management | P1 | 01-05 |
| REQ-AV-05 | Search API | P0 | 01-06 |
| REQ-AV-06 | Auto-Loader | P1 | 01-07 |
| REQ-AV-07 | Thumbnail Generation | P2 | 01-08 |
| REQ-AV-08 | Path Sanitization & Security | P0 | 01-09 |
| REQ-AV-09 | Audit Logging | P1 | 01-09 |

---

## Module Structure

```
lib/asset_vault/
    __init__.py           # Package exports
    types.py              # AssetInfo, AssetIndex, SearchResult, SecurityConfig
    enums.py              # AssetFormat, AssetCategory, SearchMode
    security.py           # sanitize_path, AuditLogger, ALLOWED_PATHS
    scanner.py            # scan_directory, scan_library, detect_format
    indexer.py            # AssetIndexer, build_index, update_index
    metadata.py           # extract_metadata, extract_dimensions, extract_materials
    scale_normalizer.py   # ScaleNormalizer, reference_based_scaling
    categories.py         # CategoryManager, load_categories_yaml, auto_categorize
    search.py             # SearchEngine, text_search, tag_search, visual_similarity
    loader.py             # AssetLoader, load_asset, link_append
    thumbnails.py         # ThumbnailGenerator, generate_thumbnails
```

---

## Wave Structure

### Wave 1: Foundation (Plans 01-01, 01-02)
- Core types and security layer
- Scanner and indexer foundation
- **Parallel**: Yes

### Wave 2: Metadata & Organization (Plans 01-03, 01-04, 01-05)
- Metadata extraction
- Scale normalization
- Category management
- **Parallel**: Yes (depends on Wave 1)

### Wave 3: Core Features (Plans 01-06, 01-07)
- Search API
- Auto-loader
- **Parallel**: Yes (depends on Wave 2)

### Wave 4: Polish (Plans 01-08, 01-09)
- Thumbnail generation
- Security hardening + audit logging
- **Parallel**: Yes (depends on Wave 1)

---

## Plans

### Plan 01-01: Core Types & Security Layer

**Objective**: Establish foundational types and secure path handling

**Files**:
- `lib/asset_vault/__init__.py`
- `lib/asset_vault/types.py`
- `lib/asset_vault/enums.py`
- `lib/asset_vault/security.py`

**Tasks**:

<task type="auto">
  <name>Create types.py with core data structures</name>
  <files>lib/asset_vault/types.py</files>
  <action>
    Create the following dataclasses:

    1. AssetInfo:
       - path: Path (sanitized, absolute)
       - name: str
       - format: AssetFormat enum
       - category: AssetCategory | None
       - tags: list[str]
       - dimensions: tuple[float, float, float] | None (bbox in meters)
       - materials: list[str] (material names)
       - textures: list[Path] (texture file paths)
       - objects: list[str] (object/collection names in file)
       - scale_reference: str | None (e.g., "1_unit = 1_meter")
       - thumbnail_path: Path | None
       - file_size: int (bytes)
       - last_modified: datetime
       - metadata: dict[str, Any] (format-specific extras)

    2. AssetIndex:
       - version: str (schema version)
       - created_at: datetime
       - updated_at: datetime
       - root_path: Path
       - assets: dict[str, AssetInfo] (keyed by relative path)
       - categories: dict[str, list[str]] (category -> asset paths)
       - tags: dict[str, list[str]] (tag -> asset paths)

    3. SearchResult:
       - asset: AssetInfo
       - score: float (0.0 to 1.0)
       - match_type: str ("text", "tag", "visual", "exact")
       - highlights: list[str] (matched text fragments)

    4. SecurityConfig:
       - allowed_paths: list[Path] (whitelist)
       - max_file_size_mb: int (default: 500)
       - allowed_extensions: list[str]
       - audit_log_path: Path | None

    Use dataclasses with field(default_factory=...) for mutable defaults.
  </action>
  <verify>python -c "from lib.asset_vault.types import AssetInfo, AssetIndex, SearchResult, SecurityConfig; print('OK')"</verify>
  <done>All 4 dataclasses defined with proper type hints and docstrings</done>
</task>

<task type="auto">
  <name>Create enums.py with type-safe enumerations</name>
  <files>lib/asset_vault/enums.py</files>
  <action>
    Create the following enums using Python's enum.Enum:

    1. AssetFormat:
       - BLEND = "blend"
       - FBX = "fbx"
       - OBJ = "obj"
       - GLB = "glb"
       - GLTF = "gltf"
       - STL = "stl"
       - ABC = "abc" (Alembic)
       - DAE = "dae" (Collada)
       - UNKNOWN = "unknown"

       Include classmethod from_extension(cls, ext: str) -> AssetFormat

    2. AssetCategory:
       - KITBASH = "kitbash"
       - PROP = "prop"
       - VEHICLE = "vehicle"
       - CHARACTER = "character"
       - ENVIRONMENT = "environment"
       - ARCHITECTURE = "architecture"
       - FURNITURE = "furniture"
       - ELECTRONICS = "electronics"
       - NATURE = "nature"
       - FOOD = "food"
       - CLOTHING = "clothing"
       - WEAPON = "weapon"
       - SCI_FI = "sci_fi"
       - FANTASY = "fantasy"
       - INDUSTRIAL = "industrial"
       - VFX = "vfx"
       - UNKNOWN = "unknown"

    3. SearchMode:
       - TEXT = "text" (keyword search)
       - TAG = "tag" (tag-based filtering)
       - VISUAL = "visual" (image similarity - placeholder)
       - HYBRID = "hybrid" (combined approaches)

    Include EXTENSION_MAP = {ext: format} for fast lookup.
  </action>
  <verify>python -c "from lib.asset_vault.enums import AssetFormat, AssetCategory, SearchMode; assert AssetFormat.from_extension('.fbx') == AssetFormat.FBX"</verify>
  <done>All 3 enums defined with helper methods</done>
</task>

<task type="auto">
  <name>Create security.py with path sanitization</name>
  <files>lib/asset_vault/security.py</files>
  <action>
    Implement security utilities for safe file access:

    1. ALLOWED_PATHS: list[Path] - Default whitelist initialized from config
       - /Volumes/Storage/3d
       - ~/Documents/Blender (expanded)
       - Configurable via set_allowed_paths()

    2. class SecurityError(Exception):
       - Path blocked with reason

    3. def sanitize_path(path: str | Path) -> Path:
       - Resolve to absolute path
       - Resolve all symlinks
       - Block ".." components after resolution (path traversal)
       - Verify path is within ALLOWED_PATHS
       - Raise SecurityError if validation fails
       - Return validated absolute Path

    4. def validate_file_access(path: Path, config: SecurityConfig) -> bool:
       - Check path is sanitized
       - Check file exists
       - Check file size <= max_file_size_mb
       - Check extension in allowed_extensions
       - Return True if all checks pass

    5. class AuditLogger:
       - __init__(self, log_path: Path | None)
       - log_access(self, path: Path, action: str, success: bool, user: str = "system")
       - log_security_event(self, event_type: str, details: dict)
       - get_recent_events(self, count: int = 100) -> list[dict]
       - Uses JSON lines format for audit log
       - Includes timestamp, path, action, success, user_agent

    All functions must be importable without bpy context.
  </action>
  <verify>python -c "from lib.asset_vault.security import sanitize_path, SecurityError, AuditLogger; print('OK')"</verify>
  <done>sanitize_path blocks traversal, AuditLogger records events</done>
</task>

<task type="auto">
  <name>Create __init__.py with package exports</name>
  <files>lib/asset_vault/__init__.py</files>
  <action>
    Export all public symbols from the asset_vault package:

    From types: AssetInfo, AssetIndex, SearchResult, SecurityConfig
    From enums: AssetFormat, AssetCategory, SearchMode
    From security: sanitize_path, SecurityError, AuditLogger, ALLOWED_PATHS

    Define __all__ with all exports.
    Add version constant: __version__ = "0.1.0"
    Add docstring explaining the package purpose.
  </action>
  <verify>python -c "from lib.asset_vault import AssetInfo, sanitize_path, __version__; print(f'v{__version__}')"</verify>
  <done>Package imports work, version 0.1.0</done>
</task>

**Success Criteria**:
- All 4 core modules created
- sanitize_path blocks path traversal attacks
- Unit tests for security functions pass

---

### Plan 01-02: Scanner & Indexer Foundation

**Objective**: Implement directory scanning and asset indexing

**Files**:
- `lib/asset_vault/scanner.py`
- `lib/asset_vault/indexer.py`

**Depends on**: 01-01

**Tasks**:

<task type="auto">
  <name>Create scanner.py for directory scanning</name>
  <files>lib/asset_vault/scanner.py</files>
  <action>
    Implement file system scanning for 3D assets:

    1. SUPPORTED_EXTENSIONS: set[str] = {".blend", ".fbx", ".obj", ".glb", ".gltf", ".stl", ".abc", ".dae"}

    2. def detect_format(file_path: Path) -> AssetFormat:
       - Use extension to determine format
       - Handle case-insensitive extensions
       - Return AssetFormat.UNKNOWN for unsupported

    3. def scan_directory(
         directory: Path,
         recursive: bool = True,
         config: SecurityConfig | None = None
       ) -> list[Path]:
       - Sanitize directory path first
       - Walk directory tree (recursive or single level)
       - Filter by SUPPORTED_EXTENSIONS
       - Validate each file with security config
       - Return list of valid asset paths
       - Raise SecurityError for unauthorized paths

    4. def scan_library(
         library_path: Path,
         config: SecurityConfig | None = None
       ) -> dict[str, list[Path]]:
       - Scan top-level subdirectories as "packs"
       - Return {pack_name: [asset_paths]}
       - Example: {"CyberPunk": [...], "Art Deco": [...]}

    5. def get_file_info(path: Path) -> dict[str, Any]:
       - Return basic file metadata without parsing
       - Include: size, modified_time, extension, is_readable
       - Fast operation (no Blender required)

    Use pathlib exclusively, no os.path.
    Handle permission errors gracefully.
  </action>
  <verify>python -c "from lib.asset_vault.scanner import scan_directory, detect_format; print('OK')"</verify>
  <done>scan_directory returns filtered asset paths</done>
</task>

<task type="auto">
  <name>Create indexer.py for asset indexing</name>
  <files>lib/asset_vault/indexer.py</files>
  <action>
    Implement the asset index system:

    1. INDEX_VERSION = "1.0"
    INDEX_FILENAME = "asset_index.json"

    2. class AssetIndexer:
       def __init__(self, config: SecurityConfig | None = None):

       def build_index(
         self,
         library_path: Path,
         force_rebuild: bool = False
       ) -> AssetIndex:
         - Check for existing index (skip if exists and not forced)
         - Scan directory for all assets
         - Create AssetInfo for each asset (basic info only)
         - Build category and tag dictionaries
         - Set index metadata (version, timestamps, root_path)
         - Return complete AssetIndex

       def update_index(
         self,
         index: AssetIndex,
         check_modified: bool = True
       ) -> AssetIndex:
         - Scan for new/removed files
         - Update modified files if check_modified
         - Rebuild category/tag dictionaries
         - Update timestamps

       def save_index(self, index: AssetIndex, path: Path | None = None) -> Path:
         - Save index to JSON at library_path/.gsd-state/asset_index.json
         - Create directory if needed
         - Use json.dump with indent=2 for readability
         - Convert Path objects to strings for JSON
         - Return path to saved index

       def load_index(self, library_path: Path) -> AssetIndex | None:
         - Load from .gsd-state/asset_index.json
         - Return None if not found
         - Validate index version matches INDEX_VERSION
         - Reconstruct AssetInfo objects from dict

    3. def quick_index(library_path: Path) -> AssetIndex:
       - Convenience function for one-shot indexing
       - Build or load index automatically

    The index should be human-readable JSON for debugging.
  </action>
  <verify>python -c "from lib.asset_vault.indexer import AssetIndexer, quick_index; print('OK')"</verify>
  <done>AssetIndexer builds, saves, loads JSON index</done>
</task>

**Success Criteria**:
- Scanner finds all .blend, .fbx, .obj, .glb files
- Indexer creates valid JSON index
- Index can be saved and loaded

---

### Plan 01-03: Metadata Extraction

**Objective**: Extract detailed metadata from 3D asset files

**Files**:
- `lib/asset_vault/metadata.py`

**Depends on**: 01-02

**Tasks**:

<task type="auto">
  <name>Create metadata.py for asset metadata extraction</name>
  <files>lib/asset_vault/metadata.py</files>
  <action>
    Implement metadata extraction for each format:

    1. def extract_metadata(
         asset_path: Path,
         format: AssetFormat | None = None
       ) -> dict[str, Any]:
       - Detect format if not provided
       - Dispatch to format-specific extractor
       - Return unified metadata dict

    2. def extract_blend_metadata(path: Path) -> dict[str, Any]:
       - Use bpy library to read .blend file (if available)
       - Fallback: Parse blend header for basic info
       - Extract: object names, collection names, material names
       - Extract: scene dimensions if available
       - Extract: embedded previews if present
       - Handle "failed to read" gracefully

    3. def extract_fbx_metadata(path: Path) -> dict[str, Any]:
       - Parse FBX ASCII header if present
       - Extract geometry counts (vertices, faces)
       - Extract embedded texture filenames
       - Fallback: Basic file info only

    4. def extract_obj_metadata(path: Path) -> dict[str, Any]:
       - Parse OBJ file for geometry info
       - Count vertices, faces, groups
       - Extract material library reference (mtllib)
       - Extract group/object names (o, g)
       - Fast: Only parse header lines, not full geometry

    5. def extract_glb_metadata(path: Path) -> dict[str, Any]:
       - Parse GLB binary header (JSON chunk)
       - Extract scene structure from glTF JSON
       - Count meshes, materials, textures
       - Extract node names

    6. def extract_dimensions(path: Path, format: AssetFormat) -> tuple[float, float, float] | None:
       - Calculate bounding box from geometry
       - Return (width, height, depth) in meters
       - Return None if cannot determine

    7. def extract_materials(path: Path, format: AssetFormat) -> list[str]:
       - Return list of material names
       - Include embedded materials for FBX/OBJ
       - Include Blender materials for .blend

    Design for headless operation (no Blender GUI needed for basic extraction).
    Use binary parsing for speed on large files.
  </action>
  <verify>python -c "from lib.asset_vault.metadata import extract_metadata, extract_obj_metadata; print('OK')"</verify>
  <done>All format extractors return metadata dicts</done>
</task>

**Success Criteria**:
- OBJ parser extracts vertex/face counts
- Blend extractor handles missing bpy gracefully
- Metadata extraction works without Blender GUI

---

### Plan 01-04: Scale Normalization

**Objective**: Normalize asset scales to consistent units

**Files**:
- `lib/asset_vault/scale_normalizer.py`

**Depends on**: 01-02

**Tasks**:

<task type="auto">
  <name>Create scale_normalizer.py for reference-based scaling</name>
  <files>lib/asset_vault/scale_normalizer.py</files>
  <action>
    Implement scale normalization system:

    1. REFERENCE_SCALES: dict[str, float] = {
         "1_unit = 1_meter": 1.0,
         "1_unit = 1_centimeter": 0.01,
         "1_unit = 1_inch": 0.0254,
         "1_unit = 1_foot": 0.3048,
         "1_unit = 1_yard": 0.9144,
         "z_up_meters": 1.0,  # Z-up coordinate system
         "y_up_meters": 1.0,  # Y-up coordinate system
       }

    2. @dataclass
       class ScaleInfo:
         detected_scale: float  # Multiplier to convert to meters
         confidence: float  # 0.0 to 1.0
         method: str  # "metadata", "heuristic", "reference"
         reference_object: str | None  # e.g., "human_figure_1.8m"

    3. class ScaleNormalizer:
       def __init__(self, reference_scale: float = 1.0):
         self.reference_scale = reference_scale

       def detect_scale(self, asset: AssetInfo) -> ScaleInfo:
         - Try metadata scale first (if stored)
         - Try heuristic: Check dimensions against known object sizes
         - Return ScaleInfo with confidence rating

       def normalize_scale(
         self,
         asset: AssetInfo,
         target_scale: float = 1.0
       ) -> tuple[float, ScaleInfo]:
         - Detect current scale
         - Calculate scale multiplier
         - Return (multiplier, scale_info)

       def set_reference_object(
         self,
         asset: AssetInfo,
         known_height: float,
         object_name: str | None = None
       ) -> float:
         - Use known object height to calibrate scale
         - Calculate and return scale factor
         - Store in asset.scale_reference

    4. def apply_scale_to_blend(path: Path, scale: float) -> bool:
       - Apply scale transform to all objects in .blend
       - Requires bpy, returns False if unavailable

    5. HEURISTICS for scale detection:
       - Human figure ~1.7-1.9m -> detect 1_unit scale
       - Door ~2.0-2.2m -> detect 1_unit scale
       - Car ~4-5m -> detect 1_unit scale
       - Chair seat ~0.45m -> detect 1_unit scale

    Include fallback for unknown scales (default to 1.0).
  </action>
  <verify>python -c "from lib.asset_vault.scale_normalizer import ScaleNormalizer, REFERENCE_SCALES; print('OK')"</verify>
  <done>ScaleNormalizer detects and applies scale multipliers</done>
</task>

**Success Criteria**:
- Scale detection works for common objects
- Reference object calibration works
- Scale multipliers calculated correctly

---

### Plan 01-05: Category & Tag Management

**Objective**: YAML-driven categorization and tagging system

**Files**:
- `lib/asset_vault/categories.py`
- `config/asset_categories.yaml`

**Depends on**: 01-02

**Tasks**:

<task type="auto">
  <name>Create categories.py for category/tag management</name>
  <files>lib/asset_vault/categories.py</files>
  <action>
    Implement category and tag management:

    1. DEFAULT_CATEGORIES_YAML: str = "config/asset_categories.yaml"

    2. @dataclass
       class CategoryRule:
         patterns: list[str]  # Filename patterns (glob)
         keywords: list[str]  # Keyword matches
         category: AssetCategory
         tags: list[str]
         confidence: float  # Default confidence for this rule

    3. class CategoryManager:
       def __init__(self, config_path: Path | None = None):
         self.rules: list[CategoryRule] = []
         self.load_config(config_path)

       def load_config(self, path: Path | None) -> None:
         - Load YAML config if provided
         - Parse category rules
         - Validate against AssetCategory enum

       def auto_categorize(self, asset: AssetInfo) -> tuple[AssetCategory, list[str], float]:
         - Match filename against patterns
         - Match path against keywords
         - Return (category, tags, confidence)
         - Multiple matches -> highest confidence
         - No match -> (AssetCategory.UNKNOWN, [], 0.0)

       def add_rule(self, rule: CategoryRule) -> None:
         - Add rule to manager
         - Re-sort by specificity

       def get_all_tags(self) -> list[str]:
         - Return all unique tags from rules

    4. def load_categories_yaml(path: Path) -> list[CategoryRule]:
       - Parse YAML file with structure:
         categories:
           - name: "kitbash"
             patterns: ["*kitbash*", "*KB3D*"]
             keywords: ["kitbash", "modular"]
             tags: ["modular", "kit"]
           - name: "vehicle"
             patterns: ["*car*", "*truck*", "*vehicle*"]
             keywords: ["car", "truck", "vehicle", "auto"]
             tags: ["transportation", "wheeled"]
       - Return list of CategoryRule objects

    5. Built-in rules for common patterns:
       - KitBash3D packs: kitbash category
       - My designs: custom tag
       - VFX assets: vfx category
  </action>
  <verify>python -c "from lib.asset_vault.categories import CategoryManager, CategoryRule; print('OK')"</verify>
  <done>CategoryManager auto-categorizes assets by patterns</done>
</task>

<task type="auto">
  <name>Create asset_categories.yaml configuration</name>
  <files>config/asset_categories.yaml</files>
  <action>
    Create comprehensive YAML configuration for categorization:

    Structure:
    ```yaml
    version: "1.0"
    description: "Asset categorization rules for auto-tagging"

    categories:
      # KitBash3D packs
      - name: "kitbash"
        patterns:
          - "*KitBash*"
          - "*KB3D*"
          - "*kitbash*"
        keywords:
          - "kitbash"
          - "modular"
          - "kit"
        tags:
          - "modular"
          - "kit"
          - "assets"

      # Vehicles
      - name: "vehicle"
        patterns:
          - "*car*"
          - "*truck*"
          - "*vehicle*"
          - "*mech*"
          - "*robot*"
        keywords:
          - "car"
          - "truck"
          - "vehicle"
          - "mech"
          - "robot"
          - "vitaly"
        tags:
          - "transportation"
          - "mechanical"

      # Sci-Fi
      - name: "sci_fi"
        patterns:
          - "*cyberpunk*"
          - "*scifi*"
          - "*sci-fi*"
          - "*futuristic*"
        keywords:
          - "cyberpunk"
          - "scifi"
          - "futuristic"
          - "neon"
          - "tech"
        tags:
          - "futuristic"
          - "technology"

      # Architecture
      - name: "architecture"
        patterns:
          - "*building*"
          - "*house*"
          - "*architecture*"
        keywords:
          - "building"
          - "house"
          - "architecture"
        tags:
          - "structure"
          - "environment"

      # VFX elements
      - name: "vfx"
        patterns:
          - "*fx*"
          - "*vfx*"
          - "*particle*"
        keywords:
          - "vfx"
          - "fx"
          - "particle"
          - "simulation"
        tags:
          - "effects"
          - "simulation"

      # Custom designs
      - name: "custom"
        patterns:
          - "*my*design*"
        keywords: []
        tags:
          - "personal"
          - "custom"
    ```

    Include comments explaining each category.
  </action>
  <verify>python -c "import yaml; yaml.safe_load(open('config/asset_categories.yaml'))"</verify>
  <done>YAML config loads with 6+ category rules</done>
</task>

**Success Criteria**:
- Categories loaded from YAML
- Auto-categorization matches KitBash patterns
- Tags applied correctly

---

### Plan 01-06: Search API

**Objective**: Full-text, tag-based, and hybrid search

**Files**:
- `lib/asset_vault/search.py`

**Depends on**: 01-02, 01-05

**Tasks**:

<task type="auto">
  <name>Create search.py for asset search functionality</name>
  <files>lib/asset_vault/search.py</files>
  <action>
    Implement comprehensive search system:

    1. @dataclass
       class SearchQuery:
         text: str | None = None
         tags: list[str] | None = None
         category: AssetCategory | None = None
         formats: list[AssetFormat] | None = None
         min_score: float = 0.0
         max_results: int = 100
         mode: SearchMode = SearchMode.HYBRID

    2. class SearchEngine:
       def __init__(self, index: AssetIndex):
         self.index = index
         self._text_index: dict[str, list[tuple[str, float]]] = {}
         self._build_text_index()

       def _build_text_index(self) -> None:
         - Build inverted index for text search
         - Tokenize asset names, paths, metadata
         - Store (asset_path, relevance_score) per token

       def search(self, query: SearchQuery) -> list[SearchResult]:
         - Dispatch by query.mode
         - text -> text_search()
         - tag -> tag_search()
         - hybrid -> combine text and tag results
         - Sort by score descending
         - Limit to max_results

       def text_search(self, text: str, fuzzy: bool = True) -> list[SearchResult]:
         - Tokenize search text
         - Look up tokens in inverted index
         - Aggregate scores per asset
         - If fuzzy: use substring matching
         - Return sorted results

       def tag_search(self, tags: list[str], match_all: bool = False) -> list[SearchResult]:
         - Look up assets for each tag
         - If match_all: intersection of all sets
         - Else: union with weighted scoring
         - Return sorted results

       def category_search(self, category: AssetCategory) -> list[SearchResult]:
         - Look up assets by category
         - All results have score 1.0

       def filter_by_format(
         self,
         results: list[SearchResult],
         formats: list[AssetFormat]
       ) -> list[SearchResult]:
         - Filter results by asset format

    3. def quick_search(
         index: AssetIndex,
         query: str,
         max_results: int = 20
       ) -> list[SearchResult]:
       - Convenience function for simple searches
       - Uses HYBRID mode by default

    4. Search scoring:
       - Exact match: 1.0
       - Prefix match: 0.9
       - Substring match: 0.7
       - Tag match: 0.8
       - Category match: 0.6
       - Combined (hybrid): weighted average
  </action>
  <verify>python -c "from lib.asset_vault.search import SearchEngine, SearchQuery; print('OK')"</verify>
  <done>SearchEngine returns ranked results for text and tag queries</done>
</task>

**Success Criteria**:
- Text search finds assets by name
- Tag search filters by multiple tags
- Hybrid search combines both

---

### Plan 01-07: Auto-Loader

**Objective**: Context-based asset loading into Blender

**Files**:
- `lib/asset_vault/loader.py`

**Depends on**: 01-03, 01-06

**Tasks**:

<task type="auto">
  <name>Create loader.py for asset loading</name>
  <files>lib/asset_vault/loader.py</files>
  <action>
    Implement asset loading into Blender scenes:

    1. @dataclass
       class LoadOptions:
         link: bool = False  # Link vs append
         relative_path: bool = True
         scale: float | None = None  # Override scale
         location: tuple[float, float, float] = (0, 0, 0)
         rotation: tuple[float, float, float] = (0, 0, 0)
         collection: str | None = None  # Target collection
         replace_existing: bool = False

    2. @dataclass
       class LoadResult:
         success: bool
         asset: AssetInfo
         imported_objects: list[str]  # Object names
         imported_collections: list[str]  # Collection names
         warnings: list[str]
         errors: list[str]

    3. class AssetLoader:
       def __init__(self, index: AssetIndex, config: SecurityConfig | None = None):
         self.index = index
         self.config = config or SecurityConfig()

       def load_asset(
         self,
         asset: AssetInfo | str,
         options: LoadOptions | None = None
       ) -> LoadResult:
         - Resolve asset if string (path or search query)
         - Validate path with security config
         - Dispatch by format
         - Return LoadResult

       def load_blend(
         self,
         path: Path,
         options: LoadOptions
       ) -> LoadResult:
         - Use bpy.ops.wm.link/append for .blend
         - Handle collections and objects
         - Apply scale if specified
         - Set location/rotation

       def load_fbx(
         self,
         path: Path,
         options: LoadOptions
       ) -> LoadResult:
         - Use bpy.ops.import_scene.fbx
         - Apply scale transform
         - Handle armature/mesh imports

       def load_obj(
         self,
         path: Path,
         options: LoadOptions
       ) -> LoadResult:
         - Use bpy.ops.wm.obj_import (4.0+) or legacy
         - Handle MTL files automatically

       def load_glb(
         self,
         path: Path,
         options: LoadOptions
       ) -> LoadResult:
         - Use bpy.ops.wm.gltf_import
         - Handle animations, materials

       def load_by_requirement(
         self,
         requirement: str,
         options: LoadOptions | None = None
       ) -> list[LoadResult]:
         - Parse requirement string (e.g., "sci-fi vehicle", "chair furniture")
         - Search index for matching assets
         - Load best match(es)
         - Return all loaded results

    4. def resolve_asset(
         index: AssetIndex,
         query: str
       ) -> AssetInfo | None:
       - Try exact path match first
       - Fall back to search
       - Return top result or None

    Handle bpy import errors gracefully (return LoadResult with errors).
    Log all load operations via AuditLogger.
  </action>
  <verify>python -c "from lib.asset_vault.loader import AssetLoader, LoadOptions; print('OK')"</verify>
  <done>AssetLoader loads .blend, .fbx, .obj, .glb files</done>
</task>

**Success Criteria**:
- Blend files load via link/append
- FBX/OBJ/GLB import correctly
- load_by_requirement finds and loads assets

---

### Plan 01-08: Thumbnail Generation

**Objective**: Generate preview thumbnails for assets

**Files**:
- `lib/asset_vault/thumbnails.py`

**Depends on**: 01-02

**Tasks**:

<task type="auto">
  <name>Create thumbnails.py for preview generation</name>
  <files>lib/asset_vault/thumbnails.py</files>
  <action>
    Implement thumbnail generation:

    1. THUMBNAIL_SIZE: tuple[int, int] = (256, 256)
    THUMBNAIL_FORMAT: str = "PNG"
    THUMBNAIL_DIR: str = ".gsd-state/thumbnails"

    2. @dataclass
       class ThumbnailConfig:
         size: tuple[int, int] = (256, 256)
         format: str = "PNG"
         background: tuple[float, float, float, float] = (0.1, 0.1, 0.1, 1.0)
         lighting: str = "studio"  # "studio", "flat", "hdri"
         camera_distance: float = 3.0
         auto_frame: bool = True

    3. class ThumbnailGenerator:
       def __init__(self, config: ThumbnailConfig | None = None):
         self.config = config or ThumbnailConfig()

       def generate_thumbnail(
         self,
         asset: AssetInfo,
         output_path: Path | None = None
       ) -> Path | None:
         - Generate thumbnail for asset
         - Save to output_path or default location
         - Return path to thumbnail or None on failure

       def generate_blend_thumbnail(self, path: Path) -> Path | None:
         - Create temporary scene
         - Load first object/collection from .blend
         - Set up camera and lighting
         - Render at thumbnail size
         - Save and cleanup

       def generate_fbx_thumbnail(self, path: Path) -> Path | None:
         - Import FBX to temporary scene
         - Frame all objects
         - Render thumbnail
         - Cleanup scene

       def generate_obj_thumbnail(self, path: Path) -> Path | None:
         - Import OBJ to temporary scene
         - Apply default material
         - Render thumbnail
         - Cleanup scene

       def batch_generate(
         self,
         assets: list[AssetInfo],
         parallel: bool = False
       ) -> dict[str, Path]:
         - Generate thumbnails for multiple assets
         - Return {asset_path: thumbnail_path}
         - Skip if thumbnail already exists

    4. def extract_embedded_thumbnail(path: Path, format: AssetFormat) -> Path | None:
       - Extract embedded preview from .blend files
       - Extract GLB/GLTF preview images
       - Return None if no embedded thumbnail

    5. def get_thumbnail_path(asset: AssetInfo) -> Path:
       - Return expected thumbnail path
       - Pattern: {THUMBNAIL_DIR}/{hash(asset.path)}.png

    Note: Thumbnail generation requires bpy (Blender).
    Return None gracefully if bpy unavailable.
  </action>
  <verify>python -c "from lib.asset_vault.thumbnails import ThumbnailGenerator, ThumbnailConfig; print('OK')"</verify>
  <done>ThumbnailGenerator creates 256x256 previews for assets</done>
</task>

**Success Criteria**:
- Thumbnails generated for .blend, .fbx, .obj
- Embedded thumbnails extracted when available
- Batch generation skips existing thumbnails

---

### Plan 01-09: Security Hardening & Audit Logging

**Objective**: Complete security implementation with comprehensive audit logging

**Files**:
- `lib/asset_vault/security.py` (extended)

**Depends on**: 01-01

**Tasks**:

<task type="auto">
  <name>Extend security.py with comprehensive audit logging</name>
  <files>lib/asset_vault/security.py</files>
  <action>
    Extend the security module with enhanced audit logging:

    1. Extend AuditLogger with:
       - class AuditEvent(TypedDict):
           timestamp: str (ISO 8601)
           event_type: str  # "access", "denied", "scan", "load", "index"
           path: str
           action: str  # "read", "write", "delete", "load", "scan"
           success: bool
           user: str
           details: dict[str, Any]

       - def log_access(self, path: Path, action: str, success: bool, user: str = "system"):
         Log file access attempts

       - def log_security_event(self, event_type: str, details: dict):
         Log security-relevant events (blocked paths, suspicious activity)

       - def log_index_event(self, action: str, count: int, duration_ms: int):
         Log index build/update operations

       - def export_audit_log(self, output_path: Path, format: str = "json") -> Path:
         Export audit log in JSON or CSV format

       - def get_statistics(self) -> dict[str, Any]:
         Return stats: total_events, access_count, denied_count, top_accessed_paths

    2. Add rate limiting for path operations:
       - class RateLimiter:
         - Track operations per path per minute
         - Block if threshold exceeded
         - Log rate limit events

    3. Add path validation cache:
       - _validated_paths: dict[str, tuple[Path, float]] (path, expiry_time)
       - Cache TTL: 60 seconds
       - Speed up repeated validations

    4. Add security configuration validation:
       - def validate_security_config(config: SecurityConfig) -> list[str]:
         Return list of configuration warnings/errors

    5. Add allowed path expansion:
       - Support glob patterns in allowed_paths
       - Support environment variables in paths
       - Expand user home directories

    Update ALLOWED_PATHS to load from config/asset_library.yaml.
  </action>
  <verify>python -c "from lib.asset_vault.security import AuditLogger; a = AuditLogger(None); print('OK')"</verify>
  <done>AuditLogger records all access, generates reports</done>
</task>

<task type="auto">
  <name>Add security configuration to asset_library.yaml</name>
  <files>config/asset_library.yaml</files>
  <action>
    Extend existing config/asset_library.yaml with security settings:

    Add section:
    ```yaml
    security:
      # Whitelisted directories for asset access
      allowed_paths:
        - "/Volumes/Storage/3d"
        - "~/Documents/Blender"

      # Maximum file size in MB
      max_file_size_mb: 500

      # Allowed file extensions
      allowed_extensions:
        - ".blend"
        - ".fbx"
        - ".obj"
        - ".glb"
        - ".gltf"
        - ".stl"
        - ".abc"
        - ".dae"

      # Audit logging
      audit:
        enabled: true
        log_path: ".gsd-state/audit.log"
        # Events to log: "all", "access", "denied", "none"
        log_level: "access"

      # Rate limiting
      rate_limit:
        enabled: true
        max_requests_per_minute: 100
    ```

    Preserve all existing config sections.
  </action>
  <verify>python -c "import yaml; d = yaml.safe_load(open('config/asset_library.yaml')); assert 'security' in d"</verify>
  <done>Security config section added to asset_library.yaml</done>
</task>

**Success Criteria**:
- Audit log records all access attempts
- Rate limiting prevents abuse
- Security config validated on load

---

## Testing Strategy

### Unit Tests

```
tests/unit/asset_vault/
    test_types.py           # Dataclass instantiation, serialization
    test_enums.py           # Enum values, from_extension
    test_security.py        # sanitize_path, SecurityError, AuditLogger
    test_scanner.py         # scan_directory, detect_format
    test_indexer.py         # build_index, save/load
    test_metadata.py        # extract_*_metadata functions
    test_scale.py           # ScaleNormalizer
    test_categories.py      # CategoryManager, auto_categorize
    test_search.py          # SearchEngine, text/tag search
    test_loader.py          # AssetLoader (mocked bpy)
    test_thumbnails.py      # ThumbnailGenerator (mocked bpy)
```

### Integration Tests

```
tests/integration/asset_vault/
    test_full_index.py      # Index real kitbash directory
    test_load_cycle.py      # Full load workflow
```

---

## Success Criteria

### Functional Requirements

- [ ] REQ-AV-01: Asset Library Indexer scans all 4 external libraries
- [ ] REQ-AV-02: Metadata Extraction works for .blend, .fbx, .obj, .glb
- [ ] REQ-AV-03: Scale Normalization detects common object scales
- [ ] REQ-AV-04: Category/Tag Management loads from YAML
- [ ] REQ-AV-05: Search API finds assets by text and tags
- [ ] REQ-AV-06: Auto-Loader loads assets by context requirements
- [ ] REQ-AV-07: Thumbnail Generation creates 256x256 previews
- [ ] REQ-AV-08: Path Sanitization blocks path traversal
- [ ] REQ-AV-09: Audit Logging records all access

### Non-Functional Requirements

- [ ] Indexing completes for 3,000+ files in under 5 minutes
- [ ] Search returns results in under 100ms for 10,000 assets
- [ ] Security layer adds <10ms overhead per operation
- [ ] All modules work without Blender for core functionality

---

## Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| pathlib | Path handling | stdlib |
| dataclasses | Data structures | stdlib |
| typing | Type hints | stdlib |
| yaml | YAML parsing | PyYAML |
| bpy | Blender integration | Blender only |

---

## Output

After completion, create `.planning/phases/1-asset-vault/01-09-SUMMARY.md` summarizing:
- Modules created
- Tests passing
- Known limitations
- Integration points
