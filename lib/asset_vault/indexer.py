"""
Asset Vault Indexer

Builds and maintains asset indices for fast search.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .enums import AssetCategory, AssetFormat
from .scanner import scan_directory, detect_format, get_file_info
from .types import AssetInfo, AssetIndex, SecurityConfig


# Index configuration
INDEX_VERSION = "1.0"
INDEX_FILENAME = "asset_index.json"
INDEX_DIR = ".gsd-state"


class AssetIndexer:
    """
    Builds and maintains asset indices.

    The index is stored as JSON for human readability and fast loading.
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        """
        Initialize the indexer.

        Args:
            config: Security configuration for path validation
        """
        self.config = config or SecurityConfig()

    def build_index(
        self,
        library_path: Path,
        force_rebuild: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> AssetIndex:
        """
        Build a complete index of a library.

        Args:
            library_path: Root directory of the asset library
            force_rebuild: If True, rebuild even if index exists
            progress_callback: Optional callback(current, total, path)

        Returns:
            Complete AssetIndex
        """
        start_time = time.time()

        # Check for existing index
        if not force_rebuild:
            existing = self.load_index(library_path)
            if existing:
                return existing

        # Scan for assets
        assets = scan_directory(library_path, recursive=True, config=self.config)
        total = len(assets)

        # Build index
        index = AssetIndex(
            version=INDEX_VERSION,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            root_path=library_path,
        )

        for i, asset_path in enumerate(assets):
            if progress_callback:
                progress_callback(i + 1, total, asset_path)

            # Create AssetInfo
            info = self._create_asset_info(asset_path, library_path)

            # Add to index
            rel_path = str(asset_path.relative_to(library_path))
            index.assets[rel_path] = info

            # Update category mapping
            if info.category:
                cat_name = info.category.value
                if cat_name not in index.categories:
                    index.categories[cat_name] = []
                index.categories[cat_name].append(rel_path)

            # Update tag mappings
            for tag in info.tags:
                if tag not in index.tags:
                    index.tags[tag] = []
                index.tags[tag].append(rel_path)

        # Save index
        self.save_index(index)

        duration_ms = int((time.time() - start_time) * 1000)
        return index

    def _create_asset_info(
        self,
        asset_path: Path,
        library_path: Path,
    ) -> AssetInfo:
        """
        Create AssetInfo for a file.

        Args:
            asset_path: Path to the asset file
            library_path: Root library path

        Returns:
            AssetInfo instance
        """
        file_info = get_file_info(asset_path)

        info = AssetInfo(
            path=asset_path,
            name=asset_path.stem,
            format=AssetFormat(file_info.get("format", "unknown")),
            file_size=file_info.get("size_bytes", 0),
            last_modified=datetime.fromtimestamp(file_info.get("modified_time", 0)),
        )

        return info

    def update_index(
        self,
        index: AssetIndex,
        check_modified: bool = True,
    ) -> AssetIndex:
        """
        Update an existing index with new/modified/removed files.

        Args:
            index: Existing index to update
            check_modified: If True, re-index modified files

        Returns:
            Updated AssetIndex
        """
        if not index.root_path:
            raise ValueError("Index has no root_path")

        # Scan current files
        current_assets = set(scan_directory(index.root_path, recursive=True, config=self.config))
        current_rel_paths = {
            str(p.relative_to(index.root_path)): p
            for p in current_assets
        }

        # Find removed assets
        indexed_paths = set(index.assets.keys())
        removed = indexed_paths - set(current_rel_paths.keys())

        # Remove deleted assets
        for rel_path in removed:
            del index.assets[rel_path]

        # Find new and modified assets
        for rel_path, asset_path in current_rel_paths.items():
            if rel_path not in index.assets:
                # New asset
                info = self._create_asset_info(asset_path, index.root_path)
                index.assets[rel_path] = info
            elif check_modified:
                # Check if modified
                existing = index.assets[rel_path]
                stat = asset_path.stat()
                modified = datetime.fromtimestamp(stat.st_mtime)

                if existing.last_modified and modified > existing.last_modified:
                    # Re-index modified asset
                    info = self._create_asset_info(asset_path, index.root_path)
                    index.assets[rel_path] = info

        # Rebuild category/tag mappings
        index.categories.clear()
        index.tags.clear()

        for rel_path, info in index.assets.items():
            if info.category:
                cat_name = info.category.value
                if cat_name not in index.categories:
                    index.categories[cat_name] = []
                index.categories[cat_name].append(rel_path)

            for tag in info.tags:
                if tag not in index.tags:
                    index.tags[tag] = []
                index.tags[tag].append(rel_path)

        index.updated_at = datetime.now()
        return index

    def save_index(
        self,
        index: AssetIndex,
        path: Optional[Path] = None,
    ) -> Path:
        """
        Save index to JSON file.

        Args:
            index: Index to save
            path: Output path (default: {root_path}/.gsd-state/asset_index.json)

        Returns:
            Path to saved index
        """
        if not index.root_path:
            raise ValueError("Index has no root_path")

        if path is None:
            path = index.root_path / INDEX_DIR / INDEX_FILENAME

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save
        data = index.to_dict()

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return path

    def load_index(self, library_path: Path) -> Optional[AssetIndex]:
        """
        Load index from JSON file.

        Args:
            library_path: Root directory of the library

        Returns:
            AssetIndex if found, None otherwise
        """
        path = library_path / INDEX_DIR / INDEX_FILENAME

        if not path.exists():
            return None

        try:
            with open(path) as f:
                data = json.load(f)

            # Validate version
            if data.get("version") != INDEX_VERSION:
                return None  # Incompatible version, rebuild needed

            return AssetIndex.from_dict(data)

        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def get_index_path(self, library_path: Path) -> Path:
        """
        Get the expected index path for a library.

        Args:
            library_path: Root directory of the library

        Returns:
            Path to index file
        """
        return library_path / INDEX_DIR / INDEX_FILENAME


def quick_index(library_path: Path, force_rebuild: bool = False) -> AssetIndex:
    """
    Convenience function for one-shot indexing.

    Args:
        library_path: Root directory of the library
        force_rebuild: If True, rebuild even if index exists

    Returns:
        AssetIndex
    """
    indexer = AssetIndexer()
    return indexer.build_index(library_path, force_rebuild=force_rebuild)
