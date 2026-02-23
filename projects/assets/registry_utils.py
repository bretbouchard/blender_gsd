#!/usr/bin/env python3
"""
Asset Registry Utilities

Reads from config/asset_registry.yaml and provides utilities for:
- Listing all assets and their status
- Generating conversion scripts
- Updating the registry
- Creating Blender asset library catalogs

Usage:
    python projects/assets/registry_utils.py --list
    python projects/assets/registry_utils.py --status
    python projects/assets/registry_utils.py --generate-script kitbash3d
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Try to import yaml, fall back to basic parsing if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

PROJECT_ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / "config" / "asset_registry.yaml"


@dataclass
class AssetSource:
    """Represents an asset source to convert."""
    name: str
    source_path: str
    kit_type: str = "native_blend"
    status: str = "pending"
    author: str = "Unknown"
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    extra: dict = field(default_factory=dict)


def load_registry() -> dict:
    """Load the asset registry YAML file."""
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry not found: {REGISTRY_PATH}")

    with open(REGISTRY_PATH) as f:
        if HAS_YAML:
            return yaml.safe_load(f)
        else:
            # Basic YAML parsing for simple structures
            # This is a fallback - install pyyaml for full support
            return parse_yaml_basic(f.read())


def parse_yaml_basic(content: str) -> dict:
    """Basic YAML parser for when pyyaml is not available."""
    result = {}
    current_section = None
    current_item = None
    indent_stack = [(0, result)]

    for line in content.split('\n'):
        # Skip comments and empty lines
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            continue

        indent = len(line) - len(stripped)

        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()

            if value:
                # Key-value pair
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith('[') and value.endswith(']'):
                    # Simple list parsing
                    value = [v.strip().strip('"') for v in value[1:-1].split(',') if v.strip()]

                # Find the right level
                while indent_stack and indent <= indent_stack[-1][0]:
                    indent_stack.pop()

                if indent_stack:
                    indent_stack[-1][1][key] = value
            else:
                # New section or list item
                if key.startswith('- '):
                    key = key[2:]

                # Pop to correct level
                while indent_stack and indent <= indent_stack[-1][0]:
                    indent_stack.pop()

                new_dict = {}
                if isinstance(indent_stack[-1][1], list):
                    indent_stack[-1][1].append({key: new_dict})
                else:
                    indent_stack[-1][1][key] = new_dict

                indent_stack.append((indent, new_dict))

    return result


def get_all_sources(registry: dict) -> list[AssetSource]:
    """Get all asset sources from the registry."""
    sources = []

    # KitBash3D kits
    for kit in registry.get('kitbash3d', {}).get('kits', []):
        source = AssetSource(
            name=kit['name'],
            source_path=kit.get('source_dir', ''),
            kit_type=kit.get('kit_type', 'native_blend'),
            status=kit.get('status', 'pending'),
            author='KitBash3D',
            tags=kit.get('tags', []),
            notes=kit.get('notes', ''),
            extra={
                'texture_dir': kit.get('texture_dir'),
                'texture_prefix': kit.get('texture_prefix'),
                'obj_file': kit.get('obj_file'),
                'fbx_file': kit.get('fbx_file'),
                'blend_file': kit.get('blend_file'),
            }
        )
        sources.append(source)

    # Plugin sources
    for plugin in registry.get('plugins', {}).get('sources', []):
        source = AssetSource(
            name=plugin['name'],
            source_path=plugin['source'],
            kit_type='plugin',
            status=plugin.get('status', 'pending'),
            author=plugin.get('author', 'Unknown'),
            tags=plugin.get('tags', []),
            extra={
                'recursive': plugin.get('recursive', True),
                'include_node_groups': plugin.get('include_node_groups', False),
            }
        )
        sources.append(source)

    # Storage collections
    for coll in registry.get('storage_collections', {}).get('collections', []):
        source = AssetSource(
            name=coll['name'],
            source_path=coll.get('source_root', ''),
            kit_type='collection',
            status=coll.get('status', 'pending'),
            author=coll['name'],
            tags=coll.get('tags', []),
            notes=coll.get('description', ''),
            extra={
                'recursive': coll.get('recursive', True),
                'blend_files': coll.get('blend_files', []),
            }
        )
        sources.append(source)

    return sources


def list_sources(registry: dict, filter_status: str | None = None):
    """Print all sources with their status."""
    sources = get_all_sources(registry)

    print("=" * 70)
    print("ASSET REGISTRY - All Sources")
    print("=" * 70)

    current_type = None
    for source in sources:
        if filter_status and source.status != filter_status:
            continue

        if source.kit_type != current_type:
            current_type = source.kit_type
            print(f"\n{current_type.upper().replace('_', ' ')}:")
            print("-" * 40)

        status_icon = "✓" if source.status == "completed" else "○"
        print(f"  {status_icon} {source.name:<25} [{source.status}]")
        if source.notes:
            print(f"      → {source.notes}")


def show_status(registry: dict):
    """Show conversion status summary."""
    status = registry.get('status', {})

    print("=" * 50)
    print("CONVERSION STATUS")
    print("=" * 50)

    for category, data in status.items():
        if isinstance(data, dict) and 'total' in data:
            completed = data.get('completed', 0)
            total = data.get('total', 0)
            pending = data.get('pending', 0)
            percent = (completed / total * 100) if total > 0 else 0
            bar_len = int(percent / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)

            print(f"\n{category.upper()}")
            print(f"  [{bar}] {completed}/{total} ({percent:.0f}%)")
            print(f"  Pending: {pending}")

    print()
    if status.get('last_run'):
        print(f"Last run: {status['last_run']}")
    else:
        print("Last run: Never")

    if status.get('next_action'):
        print(f"Next action: {status['next_action']}")


def list_asset_libraries(registry: dict):
    """List Blender asset library paths."""
    print("=" * 50)
    print("BLENDER ASSET LIBRARIES")
    print("=" * 50)

    for lib in registry.get('asset_libraries', []):
        path = Path(lib['path'])
        exists = "✓" if path.exists() else "✗"
        print(f"\n{exists} {lib['name']}")
        print(f"   Path: {lib['path']}")
        print(f"   {lib.get('description', '')}")


def generate_conversion_list(registry: dict, category: str = "all"):
    """Generate a list of items pending conversion."""
    sources = get_all_sources(registry)
    pending = [s for s in sources if s.status == "pending"]

    if category != "all":
        pending = [s for s in pending if category.lower() in s.kit_type.lower()]

    print(f"\nPending conversions ({len(pending)} items):")
    print("-" * 50)
    for source in pending:
        print(f"  - {source.name} ({source.kit_type})")


def main():
    parser = argparse.ArgumentParser(description="Asset Registry Utilities")
    parser.add_argument("--list", action="store_true", help="List all sources")
    parser.add_argument("--status", action="store_true", help="Show conversion status")
    parser.add_argument("--libraries", action="store_true", help="List asset libraries")
    parser.add_argument("--pending", action="store_true", help="List pending conversions")
    parser.add_argument("--filter", choices=["completed", "pending"], help="Filter by status")
    parser.add_argument("--category", default="all", help="Filter by category")

    args = parser.parse_args()

    try:
        registry = load_registry()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.status:
        show_status(registry)
    elif args.libraries:
        list_asset_libraries(registry)
    elif args.pending:
        generate_conversion_list(registry, args.category)
    else:
        list_sources(registry, args.filter)


if __name__ == "__main__":
    main()
