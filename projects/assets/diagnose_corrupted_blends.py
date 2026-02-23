#!/usr/bin/env python3
"""
Diagnose Corrupted .blend Files

Scans converted assets to identify:
1. Valid .blend files (proper header, readable)
2. Corrupted files (wrong size, bad header)
3. Empty stubs (17 bytes or similar)

Generates report with recovery recommendations.
"""

import os
import struct
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
DEFAULT_ROOT = Path("/Volumes/Storage/3d/kitbash/converted_assets")

# Blender 4.x+ uses Zstandard compression for .blend files
# Raw files start with "BLENDER", compressed files start with Zstd magic
BLEND_MAGIC_RAW = b'BLENDER'
ZSTD_MAGIC = b'\x28\xb5\x2f\xfd'  # Zstandard magic number

# Size thresholds
MIN_VALID_BLEND_SIZE = 100  # Real blend files are at least several KB
SUSPICIOUS_SIZES = [17, 0, 1, 32, 64]  # Common corruption sizes


def check_blend_header(filepath: Path) -> tuple[bool, str]:
    """
    Check if file has valid Blender header.

    Blender 4.x+ uses Zstandard compression, so files may start with
    either "BLENDER" (uncompressed) or Zstd magic (compressed).

    Returns: (is_valid, reason)
    """
    try:
        if not filepath.exists():
            return False, "File does not exist"

        size = filepath.stat().st_size

        if size == 0:
            return False, "Empty file (0 bytes)"

        if size in SUSPICIOUS_SIZES:
            return False, f"Suspicious size ({size} bytes) - likely corrupted"

        if size < MIN_VALID_BLEND_SIZE:
            return False, f"Too small ({size} bytes) - not a valid blend"

        # Check magic header
        with open(filepath, 'rb') as f:
            header = f.read(4)  # Read enough for Zstd magic check

        # Check for Zstandard compressed blend (Blender 4.x+)
        if header == ZSTD_MAGIC:
            return True, "Valid blend file (Zstd compressed)"

        # Check for uncompressed blend
        with open(filepath, 'rb') as f:
            full_header = f.read(7)
        if full_header == BLEND_MAGIC_RAW:
            return True, "Valid blend file (uncompressed)"

        # Neither - corrupted or wrong format
        # Try to read as text to see what it contains
        try:
            with open(filepath, 'r', errors='ignore') as f:
                content = f.read(50)
            return False, f"Wrong header - contains: '{content[:30]}...'"
        except:
            return False, f"Unknown format (not blend or zstd)"

    except Exception as e:
        return False, f"Error reading: {e}"


def scan_directory(root: Path) -> dict:
    """
    Scan directory and categorize all .blend files.

    Returns dict with statistics and file lists.
    """
    results = {
        'valid': [],
        'corrupted': [],
        'empty': [],
        'suspicious_size': [],
        'by_size': defaultdict(list),
        'by_directory': defaultdict(lambda: {'valid': 0, 'corrupted': 0}),
    }

    print(f"Scanning: {root}")
    print("-" * 60)

    for blend_file in root.rglob("*.blend"):
        rel_path = blend_file.relative_to(root)
        size = blend_file.stat().st_size

        is_valid, reason = check_blend_header(blend_file)

        file_info = {
            'path': str(rel_path),
            'full_path': str(blend_file),
            'size': size,
            'reason': reason,
        }

        # Track by size
        results['by_size'][size].append(str(rel_path))

        # Track by directory
        parent_dir = str(rel_path.parent)
        if is_valid:
            results['valid'].append(file_info)
            results['by_directory'][parent_dir]['valid'] += 1
        else:
            if size in SUSPICIOUS_SIZES or size < MIN_VALID_BLEND_SIZE:
                if size == 0:
                    results['empty'].append(file_info)
                else:
                    results['suspicious_size'].append(file_info)
            else:
                results['corrupted'].append(file_info)
            results['by_directory'][parent_dir]['corrupted'] += 1

    return results


def generate_report(results: dict, output_path: Path):
    """Generate detailed report."""

    total = len(results['valid']) + len(results['corrupted']) + \
            len(results['empty']) + len(results['suspicious_size'])

    with open(output_path, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("BLENDED FILE CORRUPTION DIAGNOSTIC REPORT\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 70 + "\n\n")

        # Summary
        f.write("## SUMMARY\n\n")
        f.write(f"Total .blend files scanned: {total}\n")
        f.write(f"  Valid files:      {len(results['valid']):5d} ({100*len(results['valid'])/total:.1f}%)\n")
        f.write(f"  Corrupted:        {len(results['corrupted']):5d} ({100*len(results['corrupted'])/total:.1f}%)\n")
        f.write(f"  Suspicious size:  {len(results['suspicious_size']):5d} ({100*len(results['suspicious_size'])/total:.1f}%)\n")
        f.write(f"  Empty (0 bytes):  {len(results['empty']):5d} ({100*len(results['empty'])/total:.1f}%)\n")
        f.write("\n")

        # Size distribution for small files
        f.write("## SIZE DISTRIBUTION (files under 1KB)\n\n")
        small_sizes = [(s, files) for s, files in results['by_size'].items() if s < 1024]
        small_sizes.sort(key=lambda x: x[0])

        for size, files in small_sizes:
            f.write(f"  {size:5d} bytes: {len(files):4d} files\n")
            if size < 100 and len(files) <= 10:
                for fn in files:
                    f.write(f"              - {fn}\n")
        f.write("\n")

        # Directories with most corruption
        f.write("## DIRECTORIES WITH CORRUPTION\n\n")
        corrupted_dirs = [(d, stats) for d, stats in results['by_directory'].items()
                          if stats['corrupted'] > 0]
        corrupted_dirs.sort(key=lambda x: x[1]['corrupted'], reverse=True)

        for dirname, stats in corrupted_dirs[:20]:
            total_in_dir = stats['valid'] + stats['corrupted']
            pct = 100 * stats['corrupted'] / total_in_dir if total_in_dir > 0 else 0
            f.write(f"  {dirname}/\n")
            f.write(f"    Valid: {stats['valid']}, Corrupted: {stats['corrupted']} ({pct:.0f}%)\n")
        f.write("\n")

        # Full list of corrupted files
        f.write("## ALL CORRUPTED/SUSPICIOUS FILES\n\n")

        if results['suspicious_size']:
            f.write(f"### Suspicious Size ({len(results['suspicious_size'])} files)\n\n")
            for info in results['suspicious_size']:
                f.write(f"  [{info['size']:5d}b] {info['path']}\n")
            f.write("\n")

        if results['corrupted']:
            f.write(f"### Other Corruption ({len(results['corrupted'])} files)\n\n")
            for info in results['corrupted'][:100]:  # Limit to first 100
                f.write(f"  [{info['size']:5d}b] {info['path']}\n")
                f.write(f"           Reason: {info['reason']}\n")
            if len(results['corrupted']) > 100:
                f.write(f"  ... and {len(results['corrupted']) - 100} more\n")
        f.write("\n")

        # Recovery recommendations
        f.write("## RECOVERY RECOMMENDATIONS\n\n")
        f.write("1. Files with suspicious sizes (17, 32, 64 bytes) are likely\n")
        f.write("   write failures - check if original source files exist.\n\n")
        f.write("2. Re-run conversion scripts on corrupted directories.\n\n")
        f.write("3. Check external drive health with Disk Utility.\n\n")
        f.write("4. Consider copying source files to internal drive before\n")
        f.write("   conversion to avoid external drive write issues.\n")

    return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Diagnose corrupted .blend files")
    parser.add_argument(
        '--dir',
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Root directory to scan (default: {DEFAULT_ROOT})"
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path("corruption_report.txt"),
        help="Output report file"
    )

    args = parser.parse_args()

    if not args.dir.exists():
        print(f"Error: Directory does not exist: {args.dir}")
        return 1

    # Run scan
    results = scan_directory(args.dir)

    # Generate report
    report_path = generate_report(results, args.output)

    # Print summary
    total = len(results['valid']) + len(results['corrupted']) + \
            len(results['empty']) + len(results['suspicious_size'])

    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"Total files:     {total}")
    print(f"Valid:           {len(results['valid'])} ({100*len(results['valid'])/total:.1f}%)")
    print(f"Corrupted:       {len(results['corrupted'])}")
    print(f"Suspicious size: {len(results['suspicious_size'])}")
    print(f"Empty:           {len(results['empty'])}")
    print(f"\nReport saved to: {report_path}")

    # Show most common corruption sizes
    print("\nMost common corruption sizes:")
    small_sizes = [(s, len(f)) for s, f in results['by_size'].items() if s < 1024]
    small_sizes.sort(key=lambda x: x[1], reverse=True)
    for size, count in small_sizes[:5]:
        print(f"  {size:5d} bytes: {count:4d} files")

    return 0


if __name__ == "__main__":
    exit(main())
