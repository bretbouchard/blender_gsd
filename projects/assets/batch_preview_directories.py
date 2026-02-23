#!/usr/bin/env python3
"""
Batch Preview Directory Listing Tool

This script generates a categorized list of directories containing .blend files
for use with Blender's built-in Batch Generate Previews feature.

Usage:
    python batch_preview_directories.py [--output FILE] [--json]

Output formats:
    - Default: Human-readable text with statistics
    - --json: JSON format for programmatic use
    - --output FILE: Write to file instead of stdout

How to use with Blender:
    1. Run this script to get directory paths
    2. Open Blender (fresh session, no files open)
    3. Go to File → Data Previews → Batch Generate Previews
    4. Navigate to each directory path and process
"""

import os
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime


# Asset library root
ASSET_ROOT = "/Volumes/Storage/3d/kitbash/converted_assets"


def count_blend_files(directory):
    """Count .blend files in a directory (non-recursive)."""
    try:
        return len([f for f in os.listdir(directory) if f.endswith('.blend')])
    except PermissionError:
        return 0


def scan_asset_directories(root_path):
    """Scan asset directories and return structured data."""
    directories = []
    total_files = 0

    # Scan top-level categories (Kits)
    for item in sorted(os.listdir(root_path)):
        item_path = os.path.join(root_path, item)
        if not os.path.isdir(item_path):
            continue

        # Check if this is a leaf directory (contains .blend files directly)
        direct_blends = count_blend_files(item_path)

        if direct_blends > 0:
            # This directory has blend files directly
            directories.append({
                'path': item_path,
                'name': item,
                'blend_count': direct_blends,
                'category': 'root'
            })
            total_files += direct_blends

        # Check subdirectories
        for subitem in sorted(os.listdir(item_path)):
            subitem_path = os.path.join(item_path, subitem)
            if not os.path.isdir(subitem_path):
                continue

            sub_blends = count_blend_files(subitem_path)
            if sub_blends > 0:
                directories.append({
                    'path': subitem_path,
                    'name': f"{item}/{subitem}",
                    'blend_count': sub_blends,
                    'category': item
                })
                total_files += sub_blends

    return directories, total_files


def format_text_output(directories, total_files):
    """Format output as human-readable text."""
    lines = []
    lines.append("=" * 70)
    lines.append("BLENDER BATCH PREVIEW GENERATION - DIRECTORY LISTING")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Root: {ASSET_ROOT}")
    lines.append(f"Total directories with .blend files: {len(directories)}")
    lines.append(f"Total .blend files: {total_files}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("DIRECTORIES (sorted by category)")
    lines.append("-" * 70)

    # Group by category
    by_category = defaultdict(list)
    for d in directories:
        by_category[d['category']].append(d)

    for category in sorted(by_category.keys()):
        dirs = by_category[category]
        cat_total = sum(d['blend_count'] for d in dirs)
        lines.append("")
        lines.append(f"## {category} ({len(dirs)} dirs, {cat_total} files)")
        lines.append("")

        for d in sorted(dirs, key=lambda x: x['name']):
            lines.append(f"  [{d['blend_count']:4d} files]  {d['path']}")

    lines.append("")
    lines.append("=" * 70)
    lines.append("INSTRUCTIONS FOR BATCH PREVIEW GENERATION")
    lines.append("=" * 70)
    lines.append("""
1. Open Blender (fresh session with NO files open)

2. Go to: File → Data Previews → Batch Generate Previews

3. In the file browser that opens:
   - Navigate to one of the directory paths listed above
   - Click "Batch Generate Previews" button
   - Wait for processing to complete

4. Repeat for each directory (or process in batches)

5. Tips:
   - Process similar-sized directories together
   - Larger directories (100+ files) will take longer
   - Previews are saved automatically to each .blend file

NOTES:
- Do NOT run this on files currently open in Blender
- Processing involves rendering, so it takes time
- You can close Blender and resume anytime - previews are per-file
""")

    return "\n".join(lines)


def format_json_output(directories, total_files):
    """Format output as JSON."""
    return json.dumps({
        'generated': datetime.now().isoformat(),
        'root': ASSET_ROOT,
        'total_directories': len(directories),
        'total_blend_files': total_files,
        'directories': directories
    }, indent=2)


def format_paths_only(directories):
    """Output just the paths, one per line (for scripting)."""
    return "\n".join(d['path'] for d in directories)


def main():
    parser = argparse.ArgumentParser(
        description='Generate directory listing for Blender batch preview generation'
    )
    parser.add_argument(
        '--output', '-o',
        help='Write output to file instead of stdout'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output in JSON format'
    )
    parser.add_argument(
        '--paths-only', '-p',
        action='store_true',
        help='Output just directory paths (one per line)'
    )
    parser.add_argument(
        '--root', '-r',
        default=ASSET_ROOT,
        help=f'Root directory to scan (default: {ASSET_ROOT})'
    )

    args = parser.parse_args()

    print(f"Scanning {args.root}...")
    directories, total_files = scan_asset_directories(args.root)
    print(f"Found {len(directories)} directories with {total_files} .blend files\n")

    # Format output
    if args.json:
        output = format_json_output(directories, total_files)
    elif args.paths_only:
        output = format_paths_only(directories)
    else:
        output = format_text_output(directories, total_files)

    # Write or print
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Output written to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
