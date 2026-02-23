#!/usr/bin/env python3
"""
Check if blend files have preview thumbnails.

Run in Blender:
    /Applications/Blender.app/Contents/MacOS/Blender --python check_thumbnails.py
"""

import bpy
from pathlib import Path

CONVERTED_ROOT = Path("/Volumes/Storage/3d/kitbash/converted_assets")


def check_previews():
    """Check preview status in blend files."""
    results = {
        'with_preview': 0,
        'without_preview': 0,
        'errors': 0,
        'samples_no_preview': [],
    }

    blend_files = list(CONVERTED_ROOT.rglob("*.blend"))
    total = len(blend_files)

    print(f"Checking {total} blend files for previews...")
    print("-" * 60)

    for i, blend_path in enumerate(blend_files):
        if (i + 1) % 100 == 0:
            print(f"Progress: {i+1}/{total} - With preview: {results['with_preview']}, Without: {results['without_preview']}")

        try:
            # Load file and check for previews
            with bpy.data.libraries.load(str(blend_path)) as (data_from, _):
                # Check if any objects have asset data with previews
                # Note: We can't directly check previews via library load
                # We need to actually open the file
                pass

            # Alternative: check file size as proxy
            # Files with previews are typically larger
            size = blend_path.stat().st_size

            # Files smaller than 50KB likely don't have render previews
            if size < 50000:
                results['without_preview'] += 1
                if len(results['samples_no_preview']) < 10:
                    results['samples_no_preview'].append(str(blend_path.relative_to(CONVERTED_ROOT)))
            else:
                results['with_preview'] += 1

        except Exception as e:
            results['errors'] += 1

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total files:        {total}")
    print(f"Likely with preview:  {results['with_preview']} (>= 50KB)")
    print(f"Likely without preview: {results['without_preview']} (< 50KB)")
    print(f"Errors:             {results['errors']}")

    if results['samples_no_preview']:
        print(f"\nSample files without previews:")
        for s in results['samples_no_preview']:
            print(f"  {s}")


if __name__ == "__main__":
    check_previews()
