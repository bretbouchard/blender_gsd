"""
Asset Vault Loader

Load assets into Blender scenes with format-specific handling.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .enums import AssetFormat
from .search import quick_search
from .security import AuditLogger, SecurityConfig, validate_file_access
from .types import AssetIndex, AssetInfo


@dataclass
class LoadOptions:
    """Options for loading assets."""
    link: bool = False  # Link vs append
    relative_path: bool = True
    scale: Optional[float] = None  # Override scale
    location: Tuple[float, float, float] = (0, 0, 0)
    rotation: Tuple[float, float, float] = (0, 0, 0)
    collection: Optional[str] = None  # Target collection
    replace_existing: bool = False


@dataclass
class LoadResult:
    """Result of asset loading operation."""
    success: bool
    asset: AssetInfo
    imported_objects: List[str] = field(default_factory=list)
    imported_collections: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class AssetLoader:
    """
    Load 3D assets into Blender scenes.

    Supports multiple formats with format-specific handling.
    Note: Most operations require bpy (Blender Python API).
    """

    def __init__(
        self,
        index: AssetIndex,
        config: Optional[SecurityConfig] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        """
        Initialize the loader.

        Args:
            index: Asset index for lookups
            config: Security configuration
            audit_logger: Optional audit logger
        """
        self.index = index
        self.config = config or SecurityConfig()
        self.audit_logger = audit_logger

    def load_asset(
        self,
        asset: AssetInfo | str,
        options: Optional[LoadOptions] = None,
    ) -> LoadResult:
        """
        Load an asset into the current scene.

        Args:
            asset: AssetInfo or path/search query
            options: Load options

        Returns:
            LoadResult with import details
        """
        options = options or LoadOptions()

        # Resolve asset if string
        if isinstance(asset, str):
            resolved = resolve_asset(self.index, asset)
            if resolved is None:
                return LoadResult(
                    success=False,
                    asset=None,
                    errors=[f"Asset not found: {asset}"],
                )
            asset = resolved

        # Validate file access
        is_valid, error = validate_file_access(asset.path, self.config)
        if not is_valid:
            if self.audit_logger:
                self.audit_logger.log_access(asset.path, "load", False)
            return LoadResult(
                success=False,
                asset=asset,
                errors=[error],
            )

        # Dispatch by format
        loaders = {
            AssetFormat.BLEND: self._load_blend,
            AssetFormat.FBX: self._load_fbx,
            AssetFormat.OBJ: self._load_obj,
            AssetFormat.GLB: self._load_glb,
            AssetFormat.GLTF: self._load_glb,  # Same loader
        }

        loader = loaders.get(asset.format)
        if loader is None:
            return LoadResult(
                success=False,
                asset=asset,
                errors=[f"Unsupported format: {asset.format.value}"],
            )

        result = loader(asset, options)

        # Log access
        if self.audit_logger:
            self.audit_logger.log_access(asset.path, "load", result.success)

        return result

    def _load_blend(self, asset: AssetInfo, options: LoadOptions) -> LoadResult:
        """Load Blender file via link/append."""
        result = LoadResult(success=False, asset=asset)

        try:
            import bpy

            path = str(asset.path)
            if options.relative_path:
                path = bpy.path.relpath(path) if bpy.data.is_saved else path

            # Get objects/collections from file
            with bpy.data.libraries.load(path) as (data_from, data_to):
                # Import all collections
                data_to.collections = data_from.collections
                # Import all objects
                data_to.objects = data_from.objects

            if options.link:
                # Link instead of append
                for coll in data_to.collections:
                    bpy.context.scene.collection.children.link(coll)
            else:
                # Append to scene
                for obj in data_to.objects:
                    bpy.context.collection.objects.link(obj)
                    result.imported_objects.append(obj.name)

                for coll in data_to.collections:
                    bpy.context.scene.collection.children.link(coll)
                    result.imported_collections.append(coll.name)

            # Apply transforms
            if options.scale or options.location != (0, 0, 0):
                self._apply_transforms(result.imported_objects, options)

            result.success = True

        except ImportError:
            result.errors.append("bpy not available - requires Blender")
        except Exception as e:
            result.errors.append(str(e))

        return result

    def _load_fbx(self, asset: AssetInfo, options: LoadOptions) -> LoadResult:
        """Load FBX file."""
        result = LoadResult(success=False, asset=asset)

        try:
            import bpy

            # Import FBX
            bpy.ops.import_scene.fbx(
                filepath=str(asset.path),
                use_anim=True,
                ignore_leaf_bones=False,
            )

            # Get imported objects
            for obj in bpy.context.selected_objects:
                result.imported_objects.append(obj.name)

            # Apply transforms
            if options.scale or options.location != (0, 0, 0):
                self._apply_transforms(result.imported_objects, options)

            result.success = True

        except ImportError:
            result.errors.append("bpy not available - requires Blender")
        except Exception as e:
            result.errors.append(str(e))

        return result

    def _load_obj(self, asset: AssetInfo, options: LoadOptions) -> LoadResult:
        """Load OBJ file."""
        result = LoadResult(success=False, asset=asset)

        try:
            import bpy

            # Try new importer (Blender 4.0+)
            try:
                bpy.ops.wm.obj_import(
                    filepath=str(asset.path),
                    forward_axis='Y',
                    up_axis='Z',
                )
            except AttributeError:
                # Fall back to legacy importer
                bpy.ops.import_scene.obj(
                    filepath=str(asset.path),
                    axis_forward='Y',
                    axis_up='Z',
                )

            # Get imported objects
            for obj in bpy.context.selected_objects:
                result.imported_objects.append(obj.name)

            # Apply transforms
            if options.scale or options.location != (0, 0, 0):
                self._apply_transforms(result.imported_objects, options)

            result.success = True

        except ImportError:
            result.errors.append("bpy not available - requires Blender")
        except Exception as e:
            result.errors.append(str(e))

        return result

    def _load_glb(self, asset: AssetInfo, options: LoadOptions) -> LoadResult:
        """Load GLB/GLTF file."""
        result = LoadResult(success=False, asset=asset)

        try:
            import bpy

            bpy.ops.import_scene.gltf(
                filepath=str(asset.path),
            )

            # Get imported objects
            for obj in bpy.context.selected_objects:
                result.imported_objects.append(obj.name)

            # Apply transforms
            if options.scale or options.location != (0, 0, 0):
                self._apply_transforms(result.imported_objects, options)

            result.success = True

        except ImportError:
            result.errors.append("bpy not available - requires Blender")
        except Exception as e:
            result.errors.append(str(e))

        return result

    def _apply_transforms(
        self,
        object_names: List[str],
        options: LoadOptions,
    ) -> None:
        """Apply transforms to imported objects."""
        try:
            import bpy

            scale = options.scale or 1.0
            loc = options.location
            rot = options.rotation

            for name in object_names:
                if name in bpy.data.objects:
                    obj = bpy.data.objects[name]

                    # Apply scale
                    obj.scale = (obj.scale[0] * scale, obj.scale[1] * scale, obj.scale[2] * scale)

                    # Apply location
                    obj.location = (
                        obj.location[0] + loc[0],
                        obj.location[1] + loc[1],
                        obj.location[2] + loc[2],
                    )

        except Exception:
            pass  # Don't fail if transforms can't be applied

    def load_by_requirement(
        self,
        requirement: str,
        options: Optional[LoadOptions] = None,
        max_results: int = 5,
    ) -> List[LoadResult]:
        """
        Load assets by natural language requirement.

        Args:
            requirement: Natural language requirement (e.g., "sci-fi vehicle")
            options: Load options
            max_results: Maximum assets to load

        Returns:
            List of LoadResult
        """
        # Search for matching assets
        results = quick_search(self.index, requirement, max_results=max_results)

        # Load each result
        load_results = []
        for search_result in results:
            load_result = self.load_asset(search_result.asset, options)
            load_results.append(load_result)

        return load_results


def resolve_asset(index: AssetIndex, query: str) -> Optional[AssetInfo]:
    """
    Resolve an asset from query string.

    Tries exact path match first, then falls back to search.

    Args:
        index: Asset index
        query: Path or search query

    Returns:
        AssetInfo if found, None otherwise
    """
    # Try exact path match
    query_path = Path(query)

    for rel_path, asset in index.assets.items():
        if asset.path == query_path or str(asset.path).endswith(query):
            return asset

    # Fall back to search
    results = quick_search(index, query, max_results=1)
    return results[0].asset if results else None
